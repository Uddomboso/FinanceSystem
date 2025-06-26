from database.db_manager import fetch_one, fetch_all, execute_query

def set_budget(user_id, cat_id, amount):
    # update or set budget amount for a category
    q = '''
    update categories set budget_amount = ?
    where user_id = ? and category_id = ?
    '''
    execute_query(q, (amount, user_id, cat_id), commit=True)

def get_budget(user_id, cat_id):
    # get the budget limit for a category
    q = '''
    select budget_amount from categories
    where user_id = ? and category_id = ?
    '''
    row = fetch_one(q, (user_id, cat_id))
    return row["budget_amount"] if row else 0

def get_spent(user_id, cat_id):
    # get how much the user already spent in a category
    q = '''
    select sum(amount) as total_spent from transactions
    where user_id = ? and category_id = ? and transaction_type = 'expense'
    '''
    row = fetch_one(q, (user_id, cat_id))
    return row["total_spent"] if row and row["total_spent"] else 0

def get_all_budgets(user_id):
    # return all categories with budget and how much was used
    q = '''
    select c.category_id, c.category_name, c.budget_amount,
    (select sum(t.amount)
     from transactions t
     where t.category_id = c.category_id and t.user_id = ? and t.transaction_type = 'expense') as used
    from categories c
    where c.user_id = ?
    '''
    return fetch_all(q, (user_id, user_id))
