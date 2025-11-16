from datetime import datetime
from database.db_manager import fetch_all,fetch_one,execute_query


def add_notification(user_id,content,notification_type="reminder"):
    """Add a notification to the database"""
    execute_query("""
        INSERT INTO notifications (user_id, content, notification_type, is_sent, send_date)
        VALUES (?, ?, ?, 0, date('now'))
    """,(user_id,content,notification_type),commit=True)


def check_transaction_against_commitments(user_id,transaction_amount,transaction_description):
    """Check if a transaction matches any unpaid commitments and mark them as paid"""
    try:
        # Get all unpaid commitments
        unpaid_commitments = fetch_all("""
            SELECT cc.*, c.category_name 
            FROM category_commitments cc
            JOIN categories c ON cc.category_id = c.category_id
            WHERE cc.user_id = ? AND cc.is_paid = 0
        """,(user_id,))

        for commitment in unpaid_commitments:
            category_name = commitment['category_name']
            commitment_amount = commitment['amount']

            # Check if transaction matches this commitment
            if (matches_commitment(transaction_description,category_name) and
                    abs(transaction_amount - commitment_amount) <= 1.00):  # Allow $1 difference

                # Mark commitment as paid
                execute_query("""
                    UPDATE category_commitments 
                    SET is_paid = 1, paid_date = ?
                    WHERE commitment_id = ?
                """,(datetime.now().isoformat(),commitment['commitment_id']),commit=True)

                add_notification(user_id,f"✅ {category_name} marked as paid!","payment")
                return True,f"Automatically marked {category_name} as paid"

        return False,"No matching commitments found"

    except Exception as e:
        return False,f"Error checking commitments: {str(e)}"


def matches_commitment(transaction_description,category_name):
    """Check if transaction description matches the category/commitment"""
    desc_lower = transaction_description.lower()
    category_lower = category_name.lower()

    # Simple matching logic - you can enhance this
    return (category_lower in desc_lower or
            any(keyword in desc_lower for keyword in get_category_keywords(category_name)))


def get_category_keywords(category_name):
    """Get search keywords for different categories"""
    keywords = {
        'netflix': ['netflix'],
        'amazon': ['amazon','prime'],
        'spotify': ['spotify'],
        'gym': ['gym','fitness','workout'],
        'electricity': ['electric','power','utility'],
        'internet': ['internet','wifi','broadband'],
        'phone': ['phone','mobile','cellular'],
        'rent': ['rent','lease'],
        'car insurance': ['car insurance','auto insurance'],
        'health insurance': ['health insurance','medical insurance']
    }
    return keywords.get(category_name.lower(),[category_name.lower()])


def mark_commitment_paid_manually(user_id, commitment_id):
    """Mark a commitment as paid manually WITHOUT creating a transaction"""
    try:
        from database.db_manager import fetch_one, execute_query
        
        # Get commitment details
        commitment = fetch_one("""
            SELECT cc.*, c.category_name
            FROM category_commitments cc
            JOIN categories c ON cc.category_id = c.category_id
            WHERE cc.commitment_id = ? AND cc.user_id = ?
        """,(commitment_id,user_id))

        if not commitment:
            return False

        # Extract category name
        try:
            category_name = commitment['category_name'] if 'category_name' in commitment.keys() else 'Payment'
        except (KeyError, TypeError):
            category_name = 'Payment'

        # Mark commitment as paid - NO transaction created
        execute_query("""
            UPDATE category_commitments 
            SET is_paid = 1, last_paid_date = ?
            WHERE commitment_id = ? AND user_id = ?
        """,(datetime.now().isoformat(),commitment_id,user_id),commit=True)

        # Add notification
        add_notification(user_id,f"✅ {category_name} marked as paid!","payment")

        return True

    except Exception as e:
        print(f"Error marking commitment as paid: {e}")
        import traceback
        traceback.print_exc()
        return False

def process_immediate_commitment(user_id,commitment_id):
    """DEPRECATED: Use mark_commitment_paid_manually instead - this creates transactions which we don't want for manual marking"""
    # For backward compatibility, just mark as paid without transaction
    return mark_commitment_paid_manually(user_id, commitment_id)


def create_commitment(user_id,category_id,category_name,amount,due_day=1):
    """Create a new commitment"""
    execute_query("""
        INSERT INTO category_commitments 
        (user_id, category_id, amount, is_paid, due_day, created_at)
        VALUES (?, ?, ?, 0, ?, ?)
    """,(user_id,category_id,amount,due_day,datetime.now().isoformat()),commit=True)


def get_suggested_amount(category_name):
    """Get suggested amounts for different categories"""
    suggestions = {
        'netflix': 15.99,
        'amazon prime': 12.99,
        'spotify': 9.99,
        'gym': 29.99,
        'electricity': 120.00,
        'internet': 79.99,
        'phone': 45.00,
        'rent': 1200.00,
        'car insurance': 89.99,
        'health insurance': 299.99
    }
    return suggestions.get(category_name.lower(),50.00)


def check_commitments(user_id):
    """Check for due commitments and send reminders"""
    setting = fetch_one("SELECT notifications_enabled FROM settings WHERE user_id = ?",(user_id,))
    if not setting or setting["notifications_enabled"] == 0:
        return

    today = datetime.now()
    today_day = today.day

    commitments = fetch_all("""
        SELECT cc.*, c.category_name
        FROM category_commitments cc
        JOIN categories c ON cc.category_id = c.category_id
        WHERE cc.user_id = ? AND cc.is_paid = 0
    """,(user_id,))

    for c in commitments:
        due_day = c["due_day"] if c["due_day"] is not None else 1
        days_until = due_day - today_day

        if due_day == today_day and not c["is_paid"]:
            msg = f"📅 '{c['category_name']}' is due today: ${c['amount']}"
            if not already_notified_today(user_id,msg):
                add_notification(user_id,msg,'reminder')
        elif 0 < days_until <= 3 and not c["is_paid"]:
            msg = f"🔔 Reminder: '{c['category_name']}' due in {days_until} days"
            if not already_notified_today(user_id,msg):
                add_notification(user_id,msg,'reminder')


def already_notified_today(user_id,message):
    result = fetch_one("""
        SELECT 1 FROM notifications
        WHERE user_id = ? AND content = ? AND DATE(created_at) = DATE('now')
    """,(user_id,message))
    return result is not None


def get_category_commitment_status(user_id,category_id):
    """Get the current commitment status for a category"""
    return fetch_one("""
        SELECT * FROM category_commitments 
        WHERE category_id = ? AND user_id = ? AND is_paid = 0
        ORDER BY created_at DESC LIMIT 1
    """,(category_id,user_id))