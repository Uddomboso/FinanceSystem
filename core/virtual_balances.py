"""In-memory demo balances for sandbox users.

After the initial Plaid sync (which always reports USD 100.00 in sandbox), we keep
track of balances locally so that UI updates reflect transactions immediately
without re-querying Plaid.
"""
from threading import Lock
from typing import Dict
from core.logger import logger

BASE_MAIN_BALANCE = 100.0
BASE_SAVINGS_BALANCE = 100.0

# Structure: {user_id: {"main": float, "savings": float}}
_BALANCES: Dict[int, Dict[str, float]] = {}
_LOCK = Lock()


def _normalize_account_type(account_type: str) -> str:
    if not account_type:
        return "main"
    account_type = account_type.lower()
    if account_type in {"salary", "checking", "main"}:
        return "main"
    if account_type in {"savings", "save"}:
        return "savings"
    return "main"


def _ensure_user(user_id: int) -> Dict[str, float]:
    user_id = int(user_id)
    if user_id not in _BALANCES:
        _BALANCES[user_id] = {
            "main": BASE_MAIN_BALANCE,
            "savings": BASE_SAVINGS_BALANCE,
        }
    return _BALANCES[user_id]


def has_balances(user_id: int) -> bool:
    """Return True if the user already has an initialized virtual balance."""
    with _LOCK:
        return int(user_id) in _BALANCES


def initialize_balances(user_id: int, *, main: float | None = None, savings: float | None = None) -> Dict[str, float]:
    """Explicitly set starting balances for a user (used after the first Plaid fetch)."""
    return reset_balances(user_id, main=main, savings=savings)


def get_balance(user_id: int, account_type: str = "main") -> float:
    with _LOCK:
        balances = _ensure_user(user_id)
        normalized = _normalize_account_type(account_type)
        value = balances.get(normalized, BASE_MAIN_BALANCE if normalized == "main" else BASE_SAVINGS_BALANCE)
        logger.info(f"[virtual_balances] get_balance user={user_id} type={normalized} value={value}")
        return value


def set_balance(user_id: int, value: float, account_type: str = "main") -> float:
    with _LOCK:
        balances = _ensure_user(user_id)
        normalized = _normalize_account_type(account_type)
        balances[normalized] = float(value)
        logger.info(f"[virtual_balances] set_balance user={user_id} type={normalized} value={balances[normalized]}")
        return balances[normalized]


def adjust_balance(user_id: int, delta: float, account_type: str = "main") -> float:
    with _LOCK:
        balances = _ensure_user(user_id)
        normalized = _normalize_account_type(account_type)
        before = balances.get(normalized, 0.0)
        balances[normalized] = round(before + float(delta), 2)
        logger.info(f"[virtual_balances] adjust_balance user={user_id} type={normalized} delta={delta} before={before} after={balances[normalized]}")
        return balances[normalized]


def reset_balances(user_id: int, *, main: float | None = None, savings: float | None = None) -> Dict[str, float]:
    with _LOCK:
        _BALANCES[int(user_id)] = {
            "main": BASE_MAIN_BALANCE if main is None else float(main),
            "savings": BASE_SAVINGS_BALANCE if savings is None else float(savings),
        }
        logger.info(f"[virtual_balances] reset_balances user={user_id} main={_BALANCES[int(user_id)]['main']} savings={_BALANCES[int(user_id)]['savings']}")
        return dict(_BALANCES[int(user_id)])
