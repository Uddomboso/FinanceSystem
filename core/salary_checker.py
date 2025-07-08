from datetime import datetime, timedelta
from database.db_manager import fetch_one
from core.commitment_manager import add_notification

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
