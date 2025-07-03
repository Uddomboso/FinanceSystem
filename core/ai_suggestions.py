from database.db_manager import fetch_all, fetch_one, execute_query
import requests
import os

# Set this as an env var or paste your key directly
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or "."


def generate_openai_tip(summary):
    try:
        if not GROQ_API_KEY:
            return "⚠️ API key not configured"

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "llama3-70b-8192",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a top-tier financial advisor. Be brief, impactful, and specific."
                },
                {
                    "role": "user",
                    "content": f"User issue:\n{summary}\n\nGive **1 short financial tip** (1-2 sentences max). Make the intro sentence strong, avoid fluff."
                }
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=10
        )

        if response.status_code == 429:
            return "⚠️ API quota exceeded - upgrade your plan"
        elif response.status_code == 401:
            return "⚠️ Invalid API key"

        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()

    except requests.exceptions.RequestException as e:
        return f"⚠️ API error: {str(e)}"
    except Exception as e:
        return f"⚠️ Error generating tip: {str(e)}"

def get_recent_suggestions(user_id):
    try:
        # Verify table exists first
        table_exists = fetch_one("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='ai_suggestions'
        """)

        if not table_exists:
            print("⚠️ ai_suggestions table doesn't exist")
            return []

        q = '''
        SELECT * FROM ai_suggestions
        WHERE user_id = ? 
        ORDER BY generated_at DESC
        LIMIT 3
        '''
        return fetch_all(q,(user_id,))

    except Exception as e:
        print(f"❌ Error fetching suggestions: {e}")
        traceback.print_exc()
        return []


def generate_suggestions(user_id):
    tips = []

    # check budget usage
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

    # most common recurring transaction
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

    # income vs expense check
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
    saved = 0
    for t in tips[:2]:  # get only first 2
        if "⚠️ AI error" not in t and "more than your income" not in t.lower():
            insert_tip(user_id,t)

    return tips


def insert_tip(user_id, content):
    q = '''
    insert into ai_suggestions (user_id, content, is_read)
    values (?, ?, 0)
    '''
    execute_query(q, (user_id, content), commit=True)
