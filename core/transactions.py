from database.db_manager import execute_query,fetch_all,fetch_one
from core.currency import convert
from datetime import datetime


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


def insert_plaid_transaction(user_id,account_id,txn):
    #  if transaction already exists
    existing = fetch_one('''
        SELECT transaction_id FROM transactions 
        WHERE user_id = ? AND amount = ? AND date = ? AND description = ?
    ''',(user_id,abs(txn["amount"]),txn["date"],txn.get("name","")))

    if existing:
        return False  #  duplicates

    # transaction type (Plaid uses positive for expenses)
    amount = abs(txn["amount"])
    txn_type = "expense" if txn["amount"] > 0 else "income"

    #  create category
    category_id = None
    if "category" in txn:
        category_path = " > ".join(txn["category"]) if isinstance(txn.get("category"), list) else "Uncategorized"
        category = fetch_one('''
            SELECT category_id FROM categories 
            WHERE user_id = ? AND category_name = ?
        ''',(user_id,category_path))

        if not category:
            execute_query('''
                INSERT INTO categories (user_id, category_name)
                VALUES (?, ?)
            ''',(user_id,category_path),commit=True)
            category_id = execute_query("SELECT last_insert_rowid()").fetchone()[0]
        else:
            category_id = category["category_id"]

    #  transaction
    q = '''
    INSERT INTO transactions (
        user_id, account_id, category_id, amount,
        transaction_type, description, date, is_recurring
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    '''
    execute_query(q,(
        user_id,
        account_id,
        category_id,
        amount,
        txn_type,
        txn.get("name","Plaid Transaction"),
        txn.get("date",datetime.now().date().isoformat()),
        0  # is_recurring
    ),commit=True)

    return True


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

        # convert to user's currency if needed
        user_currency = get_user_currency(user_id)
        if user_currency != "USD":
            balance = convert(balance,"USD",user_currency) or balance

        return balance

    return 0
