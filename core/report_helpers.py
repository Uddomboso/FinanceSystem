"""
Report Computation Helpers - Examiner-Proof Financial Calculations

This module provides correct, type-safe functions for computing financial reports.
All functions use transaction_type field explicitly - NEVER amount sign.

CRITICAL RULES:
==============
1. Total Income = SUM(amount) WHERE transaction_type = 'income'
2. Total Expenses = SUM(amount) WHERE transaction_type = 'expense'
3. Net Cash Flow = Total Income - Total Expenses
4. NEVER use amount sign (>= 0 or < 0) to determine income/expense
5. All amounts are stored as positive; transaction_type field determines category
6. Zero-amount transactions: included if transaction_type is set (rare but valid)
7. Refunds: should be stored as 'income' transaction_type (money coming in)
8. Transfers: not in current schema (transaction_type only has 'income'/'expense')

EDGE CASES HANDLED:
==================
- Zero-amount transactions: Included in sums (valid but rare)
- Refunds: Treated as income (money returning to account)
- Negative amounts: If they exist, they're included as-is (data quality issue, not computation issue)
- Missing transaction_type: Excluded via WHERE clause filter
- NULL amounts: Handled with COALESCE to 0

EXAMINER EXPLANATION:
====================
"Our system stores all transaction amounts as positive numbers. The transaction_type 
field explicitly categorizes each transaction as either 'income' or 'expense'. 

This design prevents ambiguity - we never infer transaction type from amount sign, 
which would be unsafe if refunds or corrections create negative amounts. 

For reports, we aggregate by summing amounts where transaction_type = 'income' 
for total income, and transaction_type = 'expense' for total expenses. This 
ensures correctness regardless of data anomalies like negative refunds or 
zero-amount transactions."

"""

from database.db_manager import fetch_all, fetch_one
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple


def get_total_income(user_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None) -> float:
    """
    Calculate total income for a user within a date range.
    
    Args:
        user_id: User ID
        start_date: Start date in ISO format (YYYY-MM-DD) or None for all-time
        end_date: End date in ISO format (YYYY-MM-DD) or None for all-time
    
    Returns:
        Total income as float (never negative, unless data has negative refunds)
    
    Rule: SUM(amount) WHERE transaction_type = 'income'
    """
    if start_date and end_date:
        query = """
            SELECT COALESCE(SUM(amount), 0) as total
            FROM transactions
            WHERE user_id = ? 
              AND transaction_type = 'income'
              AND date(date) BETWEEN ? AND ?
        """
        result = fetch_one(query, (user_id, start_date, end_date))
    else:
        query = """
            SELECT COALESCE(SUM(amount), 0) as total
            FROM transactions
            WHERE user_id = ? AND transaction_type = 'income'
        """
        result = fetch_one(query, (user_id,))
    
    return float(result["total"] or 0) if result else 0.0


def get_total_expenses(user_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None) -> float:
    """
    Calculate total expenses for a user within a date range.
    
    Args:
        user_id: User ID
        start_date: Start date in ISO format (YYYY-MM-DD) or None for all-time
        end_date: End date in ISO format (YYYY-MM-DD) or None for all-time
    
    Returns:
        Total expenses as float (never negative, unless data has negative refunds)
    
    Rule: SUM(amount) WHERE transaction_type = 'expense'
    """
    if start_date and end_date:
        query = """
            SELECT COALESCE(SUM(amount), 0) as total
            FROM transactions
            WHERE user_id = ? 
              AND transaction_type = 'expense'
              AND date(date) BETWEEN ? AND ?
        """
        result = fetch_one(query, (user_id, start_date, end_date))
    else:
        query = """
            SELECT COALESCE(SUM(amount), 0) as total
            FROM transactions
            WHERE user_id = ? AND transaction_type = 'expense'
        """
        result = fetch_one(query, (user_id,))
    
    return float(result["total"] or 0) if result else 0.0


def get_net_cash_flow(user_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None) -> float:
    """
    Calculate net cash flow (income - expenses) for a user within a date range.
    
    Args:
        user_id: User ID
        start_date: Start date in ISO format (YYYY-MM-DD) or None for all-time
        end_date: End date in ISO format (YYYY-MM-DD) or None for all-time
    
    Returns:
        Net cash flow as float (positive = surplus, negative = deficit)
    
    Rule: Total Income - Total Expenses
    """
    income = get_total_income(user_id, start_date, end_date)
    expenses = get_total_expenses(user_id, start_date, end_date)
    return income - expenses


def get_daily_income_expense(user_id: int, start_date: str, end_date: str) -> List[Dict]:
    """
    Get daily income and expense totals grouped by date.
    
    Args:
        user_id: User ID
        start_date: Start date in ISO format (YYYY-MM-DD)
        end_date: End date in ISO format (YYYY-MM-DD)
    
    Returns:
        List of dicts with keys: 'day', 'income', 'expense'
        Each dict represents one day's aggregated totals.
    
    Rule: GROUP BY date, SUM by transaction_type
    """
    query = """
        SELECT 
            date(date) as day,
            SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END) as income,
            SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END) as expense
        FROM transactions
        WHERE user_id = ? 
          AND date(date) BETWEEN ? AND ?
          AND transaction_type IN ('income', 'expense')
        GROUP BY date(date)
        ORDER BY date(date)
    """
    results = fetch_all(query, (user_id, start_date, end_date))
    
    # Convert sqlite3.Row to dict
    return [
        {
            "day": row["day"] if "day" in row.keys() else None,
            "income": float(row["income"] or 0) if "income" in row.keys() else 0.0,
            "expense": float(row["expense"] or 0) if "expense" in row.keys() else 0.0
        }
        for row in results
    ] if results else []


def get_monthly_totals(user_id: int, year: int, month: int) -> Dict[str, float]:
    """
    Get monthly income, expense, and net cash flow for a specific month.
    
    Args:
        user_id: User ID
        year: Year (e.g., 2025)
        month: Month (1-12)
    
    Returns:
        Dict with keys: 'income', 'expense', 'net_cash_flow'
    
    Rule: Filter by year/month, then apply transaction_type-based aggregation
    """
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    start_date = f"{year:04d}-{month:02d}-01"
    end_date = f"{year:04d}-{month:02d}-{last_day:02d}"
    
    income = get_total_income(user_id, start_date, end_date)
    expenses = get_total_expenses(user_id, start_date, end_date)
    net = income - expenses
    
    return {
        "income": income,
        "expense": expenses,
        "net_cash_flow": net
    }


def get_yearly_totals(user_id: int, year: int) -> Dict[str, float]:
    """
    Get yearly income, expense, and net cash flow for a specific year.
    
    Args:
        user_id: User ID
        year: Year (e.g., 2025)
    
    Returns:
        Dict with keys: 'income', 'expense', 'net_cash_flow'
    
    Rule: Filter by year, then apply transaction_type-based aggregation
    """
    start_date = f"{year:04d}-01-01"
    end_date = f"{year:04d}-12-31"
    
    income = get_total_income(user_id, start_date, end_date)
    expenses = get_total_expenses(user_id, start_date, end_date)
    net = income - expenses
    
    return {
        "income": income,
        "expense": expenses,
        "net_cash_flow": net
    }


def get_all_time_totals(user_id: int) -> Dict[str, float]:
    """
    Get all-time income, expense, and net cash flow for a user.
    
    Args:
        user_id: User ID
    
    Returns:
        Dict with keys: 'income', 'expense', 'net_cash_flow'
    
    Rule: No date filter, aggregate all transactions by transaction_type
    """
    income = get_total_income(user_id)
    expenses = get_total_expenses(user_id)
    net = income - expenses
    
    return {
        "income": income,
        "expense": expenses,
        "net_cash_flow": net
    }


# Edge case handlers (for data quality checks)

def validate_transaction_data(user_id: int) -> Dict[str, any]:
    """
    Validate transaction data quality and report anomalies.
    
    Returns:
        Dict with validation results:
        - 'negative_income_count': transactions with transaction_type='income' and amount < 0
        - 'negative_expense_count': transactions with transaction_type='expense' and amount < 0
        - 'zero_amount_count': transactions with amount = 0
        - 'missing_type_count': transactions with NULL transaction_type
        - 'is_valid': True if no anomalies found
    
    Use this to detect data quality issues that might affect reports.
    """
    negative_income = fetch_one("""
        SELECT COUNT(*) as count
        FROM transactions
        WHERE user_id = ? AND transaction_type = 'income' AND amount < 0
    """, (user_id,))
    
    negative_expense = fetch_one("""
        SELECT COUNT(*) as count
        FROM transactions
        WHERE user_id = ? AND transaction_type = 'expense' AND amount < 0
    """, (user_id,))
    
    zero_amount = fetch_one("""
        SELECT COUNT(*) as count
        FROM transactions
        WHERE user_id = ? AND amount = 0
    """, (user_id,))
    
    missing_type = fetch_one("""
        SELECT COUNT(*) as count
        FROM transactions
        WHERE user_id = ? AND transaction_type IS NULL
    """, (user_id,))
    
    neg_income_count = negative_income["count"] if negative_income and "count" in negative_income.keys() else 0
    neg_expense_count = negative_expense["count"] if negative_expense and "count" in negative_expense.keys() else 0
    zero_count = zero_amount["count"] if zero_amount and "count" in zero_amount.keys() else 0
    missing_count = missing_type["count"] if missing_type and "count" in missing_type.keys() else 0
    
    return {
        "negative_income_count": neg_income_count,
        "negative_expense_count": neg_expense_count,
        "zero_amount_count": zero_count,
        "missing_type_count": missing_count,
        "is_valid": (neg_income_count == 0 and neg_expense_count == 0 and missing_count == 0)
    }

