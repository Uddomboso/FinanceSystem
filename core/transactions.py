from database.db_manager import execute_query, fetch_all
from core.currency import convert
from database.db_manager import fetch_one

def get_user_currency(user_id):
    row = fetch_one("select currency from settings where user_id = ?", (user_id,))
    return row["currency"] if row else "USD"


def add_txn(user_id, acc_id, cat_id, amt, tx_type, note, date, recurring):
    q = '''
    insert into transactions (
        user_id, account_id, category_id, amount,
        transaction_type, description, date, is_recurring
    ) values (?, ?, ?, ?, ?, ?, ?, ?)
    '''
    p = (user_id, acc_id, cat_id, amt, tx_type, note, date, recurring)
    execute_query(q, p, commit=True)

def get_all_txns(user_id):
    q = '''
    select t.*, c.category_name, a.bank_name
    from transactions t
    left join categories c on t.category_id = c.category_id
    left join accounts a on t.account_id = a.account_id
    where t.user_id = ?
    order by t.date desc
    '''
    return fetch_all(q, (user_id,))

def get_total_by_type(user_id):
    q = '''
    select transaction_type, sum(amount) as total
    from transactions
    where user_id = ?
    group by transaction_type
    '''
    return fetch_all(q, (user_id,))

def get_txn_summary_by_cat(user_id):
    q = '''
    select c.category_name, sum(t.amount) as total
    from transactions t
    join categories c on t.category_id = c.category_id
    where t.user_id = ?
    group by c.category_name
    order by total desc
    '''
    return fetch_all(q, (user_id,))
