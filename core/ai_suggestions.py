from database.db_manager import fetch_all, fetch_one, execute_query
import openai

openai.api_key = ""

def generate_openai_tip(summary):
    try:
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a friendly financial assistant helping users improve their habits."},
                {"role": "user", "content": f"Turn this into a helpful tip for the user:\n\n{summary}"}
            ],
            max_tokens=100
        )
        return res['choices'][0]['message']['content'].strip()
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
        if used > r["budget_amount"]:
            summary = f"user exceeded their {r['category_name']} budget by ${used - r['budget_amount']:.2f}"
            tip = generate_openai_tip(summary)
            tips.append(tip)
        elif used > 0.8 * r["budget_amount"]:
            tips.append(f"you're close to the limit on {r['category_name']} — careful spending")

    # check most common recurring
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
        tips.append(f"you have frequent recurring txns in {top['category_name']}")

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
        tips.append("your spending is more than your income right now")

    # save to db
    for t in tips:
        insert_tip(user_id, t)

    return tips

def insert_tip(user_id, content):
    q = '''
    insert into ai_suggestions (user_id, content, is_read)
    values (?, ?, 0)
    '''
    execute_query(q, (user_id, content), commit=True)
