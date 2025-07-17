from datetime import datetime
from database.db_manager import fetch_all, fetch_one, execute_query

def check_commitments(user_id):
    setting = fetch_one("SELECT notifications_enabled FROM settings WHERE user_id = ?", (user_id,))
    if not setting or setting["notifications_enabled"] == 0:
        return  # Global toggle is OFF

    today = datetime.now()
    today_day = today.day

    commitments = fetch_all("""
        SELECT cc.*, c.category_name
        FROM category_commitments cc
        JOIN categories c ON cc.category_id = c.category_id
        WHERE cc.user_id = ?
    """, (user_id,))

    for c in commitments:
        due_day = c["due_day"]
        days_until = due_day - today_day

        if due_day < today_day and not c["is_paid"]:
            msg = f"⚠️ '{c['category_name']}' commitment overdue! Pay {c['amount']}"
        elif due_day == today_day and not c["is_paid"]:
            msg = f"📅 '{c['category_name']}' is due today: {c['amount']}"
        elif 0 < days_until <= 7 and not c["is_paid"]:
            msg = f"🔔 Reminder: '{c['category_name']}' due in {days_until} days"
        else:
            continue

        if not already_notified(user_id, msg):
            add_notification(user_id, msg)

def mark_commitment_paid(commitment_id):
    execute_query("""
        UPDATE category_commitments SET is_paid = 1, last_paid_date = CURRENT_TIMESTAMP
        WHERE commitment_id = ?
    """, (commitment_id,))

def reset_commitments_monthly():
    execute_query("UPDATE category_commitments SET is_paid = 0 WHERE 1=1")

def add_notification(user_id, content):
    execute_query("""
        INSERT INTO ai_suggestions (user_id, content)
        VALUES (?, ?)
    """, (user_id, content))

def already_notified(user_id, message):
    result = fetch_one("""
        SELECT 1 FROM ai_suggestions 
        WHERE user_id = ? AND content = ? AND DATE(created_at) = DATE('now')
    """, (user_id, message))
    return result is not None

def maybe_reset_commitments():
    today = datetime.now()
    if today.day == 1:
        reset_commitments_monthly()
