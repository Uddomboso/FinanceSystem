"""
Balance Helper - Provides balance calculation with simulated_balance support for developer testing
"""
from database.db_manager import fetch_one, fetch_all
from core.plaid_api import get_account_balances
import logging

logger = logging.getLogger(__name__)


def get_checking_balance(user_id):
    """
    Get checking balance with priority:
    1. simulated_balance (for developer testing)
    2. Plaid API balance
    3. Transaction-based calculation
    """
    checking_balance = 0
    
    # Get primary checking account
    primary_account = fetch_one("""
        SELECT account_id, plaid_token, bank_name, simulated_balance
        FROM accounts 
        WHERE user_id = ? AND account_type = 'salary' AND is_primary = 1
    """, (user_id,))
    
    if primary_account:
        # Priority 1: Use simulated_balance if set (for developer testing)
        try:
            sim_balance = primary_account["simulated_balance"] if "simulated_balance" in primary_account.keys() else None
            if sim_balance is not None:
                return sim_balance
        except:
            pass
        
        # Priority 2: Try Plaid API
        try:
            plaid_token = primary_account["plaid_token"] if "plaid_token" in primary_account.keys() else None
            if plaid_token:
                balances_data = get_account_balances(plaid_token)
                if "error" not in balances_data:
                    for acc_balance in balances_data.get("accounts", []):
                        if acc_balance["account_id"] == primary_account["account_id"]:
                            return acc_balance["balances"].get("available", 0)
        except Exception as e:
            logger.error(f"Error fetching Plaid balance: {e}")
    
    # Priority 3: Transaction-based calculation
    checking_balance_row = fetch_one("""
        SELECT SUM(
            CASE 
                WHEN transaction_type = 'income' THEN amount 
                WHEN transaction_type = 'expense' THEN -amount 
                ELSE 0 
            END
        ) as balance
        FROM transactions
        WHERE user_id = ?
    """, (user_id,))
    
    if checking_balance_row and checking_balance_row["balance"] is not None:
        return checking_balance_row["balance"]
    
    return 0


def get_unpaid_commitments_total(user_id):
    """Get total of unpaid commitments"""
    commitments_row = fetch_one("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM category_commitments
        WHERE user_id = ? AND COALESCE(is_paid, 0) = 0
    """, (user_id,))
    
    try:
        if commitments_row and "total" in commitments_row.keys():
            return commitments_row["total"] or 0
    except:
        pass
    return 0
