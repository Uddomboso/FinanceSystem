from database.db_manager import execute_query
from datetime import datetime
from core.commitment_manager import add_notification
from database.db_manager import fetch_one


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

def check_salary_reminder(user_id):
    today = datetime.now().day

    row = fetch_one("SELECT expected_amount, expected_day FROM salary_expectations WHERE user_id = ?", (user_id,))
    if not row:
        return

    expected_day = row["expected_day"]
    days_until = expected_day - today

    if 0 < days_until <= 7:
        add_notification(user_id, f"💼 Your salary is expected in {days_until} day(s). Don't forget your commitments.")
    elif expected_day == today:
        add_notification(user_id, "💸 It's salary day today! Review your commitments and savings goals.")
