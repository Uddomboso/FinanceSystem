from database.db_manager import execute_query,fetch_all,fetch_one
from core.currency import convert
from datetime import datetime

from database.db_manager import fetch_all, fetch_one, execute_query
from datetime import datetime
import re

# simple merchant → category mapping
MERCHANT_RULES = {
    "netflix": "Netflix",
    "spotify": "Spotify",
    "gym": "Gym",
    "rent": "Rent",
    "apple": "Apple",
    "amazon": "Amazon",
    "ubereats": "Food Delivery"
}

def get_user_currency(user_id):
    row = fetch_one("SELECT currency FROM settings WHERE user_id = ?",(user_id,))
    return row["currency"] if row else "USD"


def add_txn(user_id,acc_id,cat_id,amt,tx_type,note,date,recurring):
    q = '''
    INSERT INTO transactions (
        user_id, account_id, category_id, amount,
        transaction_type, description, date, is_recurring
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    '''
    p = (user_id,acc_id,cat_id,amt,tx_type,note,date,recurring)
    execute_query(q,p,commit=True)


def get_all_txns(user_id):
    q = '''
    SELECT 
        t.*, 
        c.category_name, 
        a.bank_name,
        a.account_type
    FROM transactions t
    LEFT JOIN categories c ON t.category_id = c.category_id
    LEFT JOIN accounts a ON t.account_id = a.account_id
    WHERE t.user_id = ?
    ORDER BY t.date DESC
    '''
    txns = fetch_all(q,(user_id,))


    user_currency = get_user_currency(user_id)
    if user_currency != "USD":
        for txn in txns:
            txn["amount"] = convert(txn["amount"],"USD",user_currency) or txn["amount"]

    return txns


def get_total_by_type(user_id):
    q = '''
    SELECT 
        transaction_type, 
        SUM(amount) as total
    FROM transactions
    WHERE user_id = ?
    GROUP BY transaction_type
    '''
    return fetch_all(q,(user_id,))


def get_txn_summary_by_cat(user_id):
    q = '''
    SELECT 
        c.category_name, 
        SUM(t.amount) as total,
        c.color
    FROM transactions t
    JOIN categories c ON t.category_id = c.category_id
    WHERE t.user_id = ? AND t.transaction_type = 'expense'
    GROUP BY c.category_name
    ORDER BY total DESC
    '''
    return fetch_all(q,(user_id,))

def insert_plaid_transaction(user_id, account_id, txn):
    # extract fields
    amount = float(txn.get("amount", 0))
    name = txn.get("name", "Unknown")
    date_str = txn.get("date", datetime.now().date().isoformat())

    # check if txn already exists (avoid duplicates)
    existing = fetch_one("""
        SELECT transaction_id FROM transactions
        WHERE user_id = ? AND account_id = ? AND amount = ? AND description = ? AND date = ?
    """, (user_id, account_id, amount, name, date_str))
    if existing:
        return existing["transaction_id"]

    # try to auto-match merchant to category
    category_id = auto_match_category(user_id, name)

    # if still no category, leave NULL (or you can fallback to "Miscellaneous")
    if not category_id:
        category_id = None

    # insert transaction
    txn_type = "expense" if amount > 0 else "income"
    execute_query("""
        INSERT INTO transactions (
            user_id, account_id, category_id, amount,
            description, date, transaction_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, account_id, category_id, amount, name, date_str, txn_type), commit=True)

    # fetch inserted id
    inserted = fetch_one("""
        SELECT transaction_id FROM transactions
        WHERE user_id = ? AND account_id = ? AND amount = ? AND description = ? AND date = ?
        ORDER BY transaction_id DESC LIMIT 1
    """, (user_id, account_id, amount, name, date_str))

    # after insert, try to mark related commitment
    try:
        matched = False
        # First try matching by category_id if we have one
        if category_id:
            matched = try_mark_commitment_for_txn(user_id, account_id, category_id, amount, name, date_str)
        
        # If no match by category_id, try Smart Detect by transaction name
        if not matched:
            matched = smart_detect_commitment_by_name(user_id, name, amount)
        
        if matched:
            print(f"✅ Commitment matched for {name}")
    except Exception as e:
        print("commitment match error:", e)

    return inserted["transaction_id"] if inserted else None



def get_account_balance(user_id,account_type="salary"):
    q = '''
    SELECT 
        SUM(CASE WHEN t.transaction_type = 'income' THEN t.amount ELSE 0 END) as total_income,
        SUM(CASE WHEN t.transaction_type = 'expense' THEN t.amount ELSE 0 END) as total_expenses
    FROM transactions t
    JOIN accounts a ON t.account_id = a.account_id
    WHERE t.user_id = ? AND a.account_type = ?
    '''
    result = fetch_one(q,(user_id,account_type))

    if result:
        balance = (result["total_income"] or 0) - (result["total_expenses"] or 0)

        # Convert to user's currency if needed
        user_currency = get_user_currency(user_id)
        if user_currency != "USD":
            balance = convert(balance,"USD",user_currency) or balance

        return balance

    return 0

def mark_related_commitment_paid(user_id, category_id, amount):
    execute_query("""
        UPDATE category_commitments
        SET is_paid = 1, last_paid_date = CURRENT_TIMESTAMP
        WHERE user_id = ? AND category_id = ? AND is_paid = 0 AND amount <= ?
    """, (user_id, category_id, amount))


# core/transactions.py

# existing helpers assumed already present
# if not, you can add your own salary_checker, transfer_to_savings etc here

def find_unpaid_commitments_for_user(user_id):
    q = """
    SELECT commitment_id, category_id, amount, due_day
    FROM category_commitments
    WHERE user_id = ? AND is_paid = 0
    """
    return fetch_all(q, (user_id,))

def merchant_matches_category(merchant_name, category_name):
    if not merchant_name or not category_name:
        return False
    return category_name.lower() in merchant_name.lower() or merchant_name.lower() in category_name.lower()

def try_mark_commitment_for_txn(user_id, account_id, category_id, amount, name, date_str):
    """Try to match transaction to a commitment using Smart Detect or amount matching"""
    # Get unpaid commitments - check both Smart Detect (detection_method=1) and Manual (detection_method=0 or NULL)
    # Use COALESCE to handle cases where detection_method column doesn't exist yet
    try:
        commitments = fetch_all("""
            SELECT cc.commitment_id, cc.amount, COALESCE(cc.detection_method, 0) as detection_method, c.category_name
            FROM category_commitments cc
            JOIN categories c ON cc.category_id = c.category_id
            WHERE cc.user_id = ? AND COALESCE(cc.is_paid, 0) = 0 AND cc.category_id = ?
        """, (user_id, category_id))
    except:
        # Fallback if detection_method column doesn't exist
        commitments = fetch_all("""
            SELECT cc.commitment_id, cc.amount, 0 as detection_method, c.category_name
            FROM category_commitments cc
            JOIN categories c ON cc.category_id = c.category_id
            WHERE cc.user_id = ? AND COALESCE(cc.is_paid, 0) = 0 AND cc.category_id = ?
        """, (user_id, category_id))

    tol = 1.0  # tolerance 1 USD
    name_lower = name.lower() if name else ""

    # Known brands for Smart Detect
    known_brands = ['netflix', 'spotify', 'apple music', 'applemusic', 'amazon prime', 
                   'amazon', 'hulu', 'disney', 'youtube', 'google', 'microsoft',
                   'adobe', 'dropbox', 'zoom', 'slack', 'discord', 'twitch']

    for c in commitments:
        expected = float(c['amount'] or 0)
        # Handle sqlite3.Row object - use bracket notation
        try:
            detection_method = c['detection_method'] if c['detection_method'] is not None else 0
        except (KeyError, TypeError):
            detection_method = 0
        try:
            category_name = (c['category_name'] or '').lower()
        except (KeyError, TypeError):
            category_name = ''
        amount_matches = abs(expected - amount) <= tol
        
        # Smart Detect: Match by keyword in transaction name
        if detection_method == 1:
            # Check if category name or transaction name contains known brand keywords
            matches_brand = any(brand in name_lower or brand in category_name for brand in known_brands)
            
            # Also check if transaction name contains category name
            matches_category = category_name and category_name in name_lower
            
            if (matches_brand or matches_category) and amount_matches:
                # Mark as paid
                execute_query("""
                    UPDATE category_commitments
                    SET is_paid = 1,
                        last_paid_date = CURRENT_TIMESTAMP
                    WHERE commitment_id = ?
                """, (c['commitment_id'],), commit=True)

                # Add notification
                execute_query("""
                    INSERT INTO notifications (user_id, content, notification_type, created_at)
                    VALUES (?, ?, 'payment', CURRENT_TIMESTAMP)
                """, (user_id, f"✅ Smart Detect: {c['category_name']} payment of ${amount:.2f} automatically matched!"), commit=True)
                return True
        
        # Manual: Match by amount only (detection_method=0)
        # Pay as you go: Match by amount (detection_method=2) - user manually pays
        # For "Pay as you go", always match by amount if category matches
        elif detection_method == 0 or detection_method == 2 or detection_method is None:
            # For detection_method=2 (Pay as you go), match by amount only (category_id already matches)
            # For detection_method=0 (Manual), also match by amount only
            if amount_matches:
                # Mark as paid
                execute_query("""
                    UPDATE category_commitments
                    SET is_paid = 1,
                        last_paid_date = CURRENT_TIMESTAMP
                    WHERE commitment_id = ?
                """, (c['commitment_id'],), commit=True)

                # Add notification
                execute_query("""
                    INSERT INTO notifications (user_id, content, notification_type, created_at)
                    VALUES (?, ?, 'payment', CURRENT_TIMESTAMP)
                """, (user_id, f"✅ {c['category_name']} payment of ${amount:.2f} matched commitment!"), commit=True)
                return True
    
    return False


def smart_detect_commitment_by_name(user_id, transaction_name, amount):
    """
    Smart Detect: Match transaction to commitment by name similarity.
    This is called when category_id matching fails.
    Matches transaction name (e.g., "Netflix - REF-ABC123") to commitment category name (e.g., "Netflix")
    """
    if not transaction_name:
        return False
    
    name_lower = transaction_name.lower()
    tol = 1.0  # tolerance 1 USD
    
    # Get all unpaid commitments for user
    try:
        commitments = fetch_all("""
            SELECT cc.commitment_id, cc.amount, c.category_name
            FROM category_commitments cc
            JOIN categories c ON cc.category_id = c.category_id
            WHERE cc.user_id = ? AND COALESCE(cc.is_paid, 0) = 0
        """, (user_id,))
    except Exception as e:
        print(f"Error fetching commitments: {e}")
        return False
    
    for c in commitments:
        try:
            category_name = (c['category_name'] or '').lower()
            expected_amount = float(c['amount'] or 0)
        except (KeyError, TypeError):
            continue
        
        if not category_name:
            continue
        
        # Check if category name appears in transaction name
        # e.g., "netflix" in "netflix - ref-abc123"
        if category_name in name_lower:
            # Also check amount is within tolerance
            if abs(expected_amount - amount) <= tol:
                # Mark as paid
                execute_query("""
                    UPDATE category_commitments
                    SET is_paid = 1,
                        last_paid_date = CURRENT_TIMESTAMP
                    WHERE commitment_id = ?
                """, (c['commitment_id'],), commit=True)
                
                # Add notification
                execute_query("""
                    INSERT INTO notifications (user_id, content, notification_type, created_at)
                    VALUES (?, ?, 'payment', CURRENT_TIMESTAMP)
                """, (user_id, f"✅ Smart Detect: {c['category_name']} payment of ${amount:.2f} automatically matched!"), commit=True)
                
                print(f"✅ Smart Detect matched '{transaction_name}' to commitment '{c['category_name']}'")
                return True
    
    return False


def get_or_create_category(user_id, category_name):
    """Find category_id by name, or create if it doesn't exist"""
    cat = fetch_one(
        "SELECT category_id FROM categories WHERE user_id = ? AND category_name = ?",
        (user_id, category_name)
    )
    if cat:
        return cat["category_id"]

    execute_query(
        "INSERT INTO categories (user_id, category_name) VALUES (?, ?)",
        (user_id, category_name),
        commit=True
    )
    new_id = fetch_one("SELECT last_insert_rowid() as id")["id"]
    return new_id


def auto_match_category(user_id, merchant_name):
    """Return category_id if merchant matches known rules"""
    if not merchant_name:
        return None
    name = merchant_name.lower()
    for keyword, category_name in MERCHANT_RULES.items():
        if keyword in name:
            return get_or_create_category(user_id, category_name)
    return None

def insert_simulated_transaction(user_id, merchant_name, amount, date_str=None):
    """
    Insert a simulated transaction without requiring an account.
    For demo/developer use only.
    
    Args:
        user_id: User ID
        merchant_name: Transaction description/merchant name
        amount: Transaction amount (positive for expenses)
        date_str: Optional date string (defaults to today)
    
    Returns:
        transaction_id if successful, None otherwise
    """
    if date_str is None:
        date_str = datetime.now().date().isoformat()
    
    amount = float(amount)
    
    # Check if transaction already exists (avoid duplicates)
    existing = fetch_one("""
        SELECT transaction_id FROM transactions
        WHERE user_id = ? AND account_id IS NULL AND amount = ? AND description = ? AND date = ?
    """, (user_id, amount, merchant_name, date_str))
    if existing:
        return existing["transaction_id"]
    
    # Try to auto-match merchant to category
    category_id = auto_match_category(user_id, merchant_name)
    
    # Determine transaction type (expense if positive amount)
    txn_type = "expense" if amount > 0 else "income"
    
    # Insert transaction with NULL account_id (simulated transactions don't need accounts)
    execute_query("""
        INSERT INTO transactions (
            user_id, account_id, category_id, amount,
            description, date, transaction_type
        ) VALUES (?, NULL, ?, ?, ?, ?, ?)
    """, (user_id, category_id, amount, merchant_name, date_str, txn_type), commit=True)
    
    # Fetch inserted id
    inserted = fetch_one("""
        SELECT transaction_id FROM transactions
        WHERE user_id = ? AND account_id IS NULL AND amount = ? AND description = ? AND date = ?
        ORDER BY transaction_id DESC LIMIT 1
    """, (user_id, amount, merchant_name, date_str))
    
    # Try to mark related commitment (commitment matching doesn't require account_id)
    try:
        matched = False
        # First try matching by category_id if we have one
        if category_id:
            # Use NULL for account_id in commitment matching
            matched = try_mark_commitment_for_txn(user_id, None, category_id, amount, merchant_name, date_str)
        
        # If no match by category_id, try Smart Detect by transaction name
        if not matched:
            matched = smart_detect_commitment_by_name(user_id, merchant_name, amount)
        
        if matched:
            print(f"✅ Commitment matched for {merchant_name}")
    except Exception as e:
        print(f"Commitment match error: {e}")
    
    return inserted["transaction_id"] if inserted else None

