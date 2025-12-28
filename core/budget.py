"""
Budget Management Module - Time-Bounded Budgeting

This module provides budget management with support for monthly and yearly periods.
The original get_spent() function calculated lifetime totals - this has been
replaced with time-bounded functions.

For time-bounded budgeting, use functions from core.budget_time_bounded:
- get_spent_monthly() - expenses for a specific month
- get_spent_yearly() - expenses for a specific year
- get_budget_remaining_monthly() - budget status for a month
- get_budget_remaining_yearly() - budget status for a year

DEPRECATED: get_spent() - use get_spent_monthly() or get_spent_yearly() instead
"""
from database.db_manager import fetch_one, fetch_all, execute_query
from datetime import date

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
    """
    DEPRECATED: This function returns LIFETIME totals, not time-bounded.
    
    Use get_spent_monthly() or get_spent_yearly() from core.budget_time_bounded
    for correct time-bounded budgeting.
    
    Kept for backward compatibility only.
    """
    # get how much the user already spent in a category (LIFETIME - no date filter)
    q = '''
    select sum(amount) as total_spent from transactions
    where user_id = ? and category_id = ? and transaction_type = 'expense'
    '''
    row = fetch_one(q, (user_id, cat_id))
    return row["total_spent"] if row and row["total_spent"] else 0

def get_spent_current_month(user_id, cat_id):
    """
    Get spending for current month (time-bounded).
    
    This is the CORRECT way to calculate monthly budget spending.
    """
    from core.budget_time_bounded import get_spent_current_month as _get_spent
    return _get_spent(user_id, cat_id)

def get_all_budgets(user_id):
    """
    DEPRECATED: Returns lifetime totals, not time-bounded.
    
    Use get_all_budgets_with_periods() from core.budget_time_bounded instead.
    """
    # return all categories with budget and how much was used (LIFETIME - no date filter)
    q = '''
    select c.category_id, c.category_name, c.budget_amount,
    (select sum(t.amount)
     from transactions t
     where t.category_id = c.category_id and t.user_id = ? and t.transaction_type = 'expense') as used
    from categories c
    where c.user_id = ?
    '''
    return fetch_all(q, (user_id, user_id))
