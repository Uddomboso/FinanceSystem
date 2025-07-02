from database.db_manager import fetch_all, fetch_one, execute_query
import requests
import os

#gorq api key
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or "useYourKey"

def generate_openai_tip(summary):
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "llama3-70b-8192",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an expert financial advisor. You analyze budget usage patterns "
                        "and give sharp, personalized tips — not generic ones. Your tone is confident, "
                        "action-oriented, and always specific. Tips should include clear actions with numbers where possible."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Here's the user's situation:\n\n{summary}\n\n"
                        "Give a short, useful financial tip based on this. Be specific and action-focused, e.g., "
                        "'reduce dining out to ₺500/month' or 'cancel unused streaming services this week'."
                    )
                }
            ],
            "temperature": 0.8,
            "max_tokens": 120
        }

        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()

        return response.json()["choices"][0]["message"]["content"].strip()

    except Exception as e:
        return f"⚠️ AI error: {e}"

def get_recent_suggestions(user_id):
    q = '''
    select * from ai_suggestions
    where user_id = ? order by generated_at desc
    '''
    return fetch_all(q, (user_id,))


def generate_suggestions(user_id):
    tips = []

  
    q = '''
    select c.category_name, c.budget_amount,
    (select sum(t.amount) from transactions t
     where t.user_id = ? and t.category_id = c.category_id
     and t.transaction_type = 'expense') as used
    from categories c
    where c.user_id = ? and c.budget_amount > 0
    '''
    rows = fetch_all(q, (user_id, user_id))
    for r in rows:
        used = r["used"] or 0
        budget = r["budget_amount"]
        category = r["category_name"]

        if used > budget:
            over = used - budget
            summary = (
                f"The user set a ₺{budget:.2f} budget for {category} but has already spent ₺{used:.2f}, "
                f"exceeding it by ₺{over:.2f}. Income is currently less than expenses."
            )
            tip = generate_openai_tip(summary)
            tips.append(tip)
        elif used > 0.8 * budget:
            percent = (used / budget) * 100
            summary = (
                f"Spending in {category} is at ₺{used:.2f} out of a ₺{budget:.2f} budget "
                f"({percent:.0f}% used). Suggest a way to cut back before reaching the limit."
            )
            tip = generate_openai_tip(summary)
            tips.append(tip)

    
    q2 = '''
    select c.category_name, count(*) as freq
    from transactions t
    join categories c on t.category_id = c.category_id
    where t.user_id = ? and t.is_recurring = 1
    group by t.category_id
    order by freq desc limit 1
    '''
    top = fetch_one(q2, (user_id,))
    if top:
        summary = (
            f"The user has frequent recurring transactions in the {top['category_name']} category. "
            "Some of these may not be essential."
        )
        tip = generate_openai_tip(summary)
        tips.append(tip)

   
    q3 = '''
    select transaction_type, sum(amount) as total
    from transactions
    where user_id = ?
    group by transaction_type
    '''
    stats = fetch_all(q3, (user_id,))
    totals = {r["transaction_type"]: r["total"] for r in stats}
    inc = totals.get("income", 0)
    exp = totals.get("expense", 0)
    if inc < exp:
        summary = (
            f"The user's total income is ₺{inc:.2f} while total expenses are ₺{exp:.2f}. "
            "They are spending more than they earn this month."
        )
        tip = generate_openai_tip(summary)
        tips.append(tip)

    # save to db
    for t in tips:
        print("SAVING SUGGESTION:",t,"| USER_ID:",user_id)  # Debug print
        if "⚠️ AI error" not in t and "more than your income" not in t.lower():
            insert_tip(user_id,t)

    return tips


def insert_tip(user_id, content):
    q = '''
    insert into ai_suggestions (user_id, content, is_read)
    values (?, ?, 0)
    '''
    execute_query(q, (user_id, content), commit=True)
