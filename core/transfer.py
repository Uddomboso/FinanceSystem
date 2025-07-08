from database.db_manager import execute_query
from core.commitment_manager import add_notification
from datetime import datetime

def transfer_to_category(user_id, account_id, category_id, amount, note=""):
    # log as expense in transactions
    execute_query("""
        INSERT INTO transactions (
            user_id, account_id, category_id, amount, transaction_type, description, date
        ) VALUES (?, ?, ?, ?, 'expense', ?, ?)
    """, (user_id, account_id, category_id, amount, note or "Transfer to category", datetime.now()))

    add_notification(user_id, f" You paid {amount} into category (ID: {category_id})")

def transfer_to_savings(user_id, from_account_id, to_savings_account_id, amount, note="Transfer to savings"):
    from database.db_manager import execute_query
    from datetime import datetime

    execute_query("""
        INSERT INTO transactions (user_id, account_id, amount, transaction_type, description, date)
        VALUES (?, ?, ?, 'expense', ?, ?)
    """, (user_id, from_account_id, amount, note, datetime.now()))

    execute_query("""
        INSERT INTO transactions (user_id, account_id, amount, transaction_type, description, date)
        VALUES (?, ?, ?, 'income', ?, ?)
    """, (user_id, to_savings_account_id, amount, note, datetime.now()))

