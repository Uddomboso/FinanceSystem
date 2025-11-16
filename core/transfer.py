from database.db_manager import execute_query
from core.commitment_manager import add_notification
from datetime import datetime
from database.db_manager import fetch_all

def get_recent_category_transfers(user_id, limit=5):
    query = """
        SELECT ct.transfer_id, c.category_name, ct.amount, ct.note, ct.transfer_date
        FROM category_transfers ct
        JOIN categories c ON ct.category_id = c.category_id
        WHERE ct.user_id = ?
        ORDER BY ct.transfer_date DESC
        LIMIT ?
    """
    return fetch_all(query, (user_id, limit))


def transfer_to_category(user_id, account_id, category_id, amount, note=""):
    # log as expense in transactions
    execute_query("""
        INSERT INTO transactions (
            user_id, account_id, category_id, amount, transaction_type, description, date
        ) VALUES (?, ?, ?, ?, 'expense', ?, ?)
    """, (user_id, account_id, category_id, amount, note or "Transfer to category", datetime.now()))

    add_notification(user_id, f"✅ You paid {amount} into category (ID: {category_id})")
