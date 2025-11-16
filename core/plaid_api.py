import uuid
import random
import os
import requests
import datetime

# Import Config first, then logger separately to avoid circular imports
from core.config import Config

# Import logger after Config is imported
from core.logger import logger, log_demo_event

# Use configuration from config.py
PLAID_CLIENT_ID = Config.PLAID_CLIENT_ID
PLAID_SECRET = Config.PLAID_SECRET
base_url = Config.PLAID_BASE_URL

# Use mock mode based on configuration
use_mock = Config.DEMO_MODE

# ... rest of your plaid_api.py code remains the same ...

def get_account_balances(access_token):
    """Get account balances from Plaid"""
    if Config.DEMO_MODE:
        log_demo_event("BALANCES", "Using mock balances")
        return mock_get_account_balances(access_token)

    url = f"{base_url}/accounts/balance/get"
    headers = {"Content-Type": "application/json"}
    data = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": access_token
    }

    try:
        res = requests.post(url, json=data, headers=headers, timeout=10)
        res.raise_for_status()
        logger.info("Successfully fetched account balances from Plaid")
        return res.json()
    except requests.exceptions.HTTPError as e:
        # Get more detailed error information from Plaid API
        error_detail = ""
        try:
            error_response = e.response.json()
            error_detail = error_response.get("error_message", str(e))
        except:
            error_detail = str(e)
        logger.error(f"Error fetching Plaid balances: {e.response.status_code} - {error_detail}")
        return {"error": error_detail}
    except Exception as e:
        logger.error(f"Error fetching Plaid balances: {e}")
        return {"error": str(e)}

def mock_get_account_balances(access_token):
    """Mock implementation for demo mode"""
    return {
        "accounts": [
            {
                "account_id": "mock_acc_001",
                "balances": {
                    "available": 2500.00,
                    "current": 2500.00,
                    "iso_currency_code": "USD"
                },
                "name": "Demo Checking",
                "official_name": "Demo Checking Account",
                "type": "depository",
                "subtype": "checking"
            }
        ]
    }

def mock_generate_transaction(user_id, account_id, name="Netflix", amount=8.00, date=None, category=None):
    if date is None:
        date = datetime.datetime.now().date().isoformat()
    txn = {
        "account_id": account_id,
        "amount": amount,
        "date": date,
        "name": name,
        "category_id": category if category else None
    }
    return txn

def mock_post_and_insert(user_id, account_id, name="Netflix", amount=8.0, date=None, category=None):
    txn = mock_generate_transaction(user_id, account_id, name, amount, date, category)
    from core.transactions import insert_plaid_transaction
    inserted = insert_plaid_transaction(user_id, account_id, txn)
    return inserted

# ========== MOCK MODE [TESTING] ==========
def mock_create_link_token(user_id):
    return {"link_token": f"mock-link-token-{uuid.uuid4()}"}

def mock_get_accounts(user_id):
    return {
        "accounts": [
            {
                "account_id": f"acc_{uuid.uuid4().hex[:6]}",
                "name": "GTBank Checking",
                "subtype": "checking",
                "balances": {"available": round(random.uniform(1500, 5000), 2)},
                "currency": "NGN",
                "last_sync": datetime.datetime.now().isoformat(),
                "plaid_token": "mock-access-token"
            },
            {
                "account_id": f"acc_{uuid.uuid4().hex[:6]}",
                "name": "PiggyVest Savings",
                "subtype": "savings",
                "balances": {"available": round(random.uniform(3000, 10000), 2)},
                "currency": "NGN",
                "last_sync": datetime.datetime.now().isoformat(),
                "plaid_token": "mock-access-token"
            }
        ]
    }

# ========== REAL PLAID MODE ==========
def real_create_link_token(user_id):
    url = f"{base_url}/link/token/create"
    headers = {"Content-Type": "application/json"}
    body = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "client_name": "PennyWise Demo",
        "user": {"client_user_id": str(user_id)},
        "products": ["transactions"],
        "country_codes": ["US"],
        "language": "en"
    }
    try:
        res = requests.post(url, headers=headers, json=body, timeout=10)
        res.raise_for_status()
        logger.info("Successfully created Plaid link token")
        return res.json()
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        try:
            error_response = e.response.json()
            error_detail = error_response.get("error_message", str(e))
        except:
            error_detail = str(e)
        logger.error(f"Error creating Plaid link token: {e.response.status_code} - {error_detail}")
        return {"error": error_detail}
    except Exception as e:
        logger.error(f"Error creating Plaid link token: {e}")
        return {"error": str(e)}

def exchange_public_token(public_token):
    url = f"{base_url}/item/public_token/exchange"
    data = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "public_token": public_token
    }
    try:
        res = requests.post(url, json=data, timeout=10)
        res.raise_for_status()
        logger.info("Successfully exchanged public token")
        return res.json()
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        try:
            error_response = e.response.json()
            error_detail = error_response.get("error_message", str(e))
        except:
            error_detail = str(e)
        logger.error(f"Error exchanging public token: {e.response.status_code} - {error_detail}")
        return {"error": error_detail}
    except Exception as e:
        logger.error(f"Error exchanging public token: {e}")
        return {"error": str(e)}

def real_get_accounts(access_token):
    url = f"{base_url}/accounts/get"
    data = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": access_token
    }
    try:
        res = requests.post(url, json=data, timeout=10)
        res.raise_for_status()
        logger.info("Successfully fetched accounts from Plaid")
        return res.json()
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        try:
            error_response = e.response.json()
            error_detail = error_response.get("error_message", str(e))
        except:
            error_detail = str(e)
        logger.error(f"Error fetching accounts from Plaid: {e.response.status_code} - {error_detail}")
        return {"accounts": [], "error": error_detail}
    except Exception as e:
        logger.error(f"Error fetching accounts from Plaid: {e}")
        return {"accounts": [], "error": str(e)}

def get_transactions(access_token, start_date, end_date):
    url = f"{base_url}/transactions/get"
    data = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": access_token,
        "start_date": start_date,
        "end_date": end_date
    }
    try:
        res = requests.post(url, json=data, timeout=10)
        res.raise_for_status()
        logger.info("Successfully fetched transactions from Plaid")
        return res.json()
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        try:
            error_response = e.response.json()
            error_detail = error_response.get("error_message", str(e))
        except:
            error_detail = str(e)
        logger.error(f"Error fetching transactions from Plaid: {e.response.status_code} - {error_detail}")
        return {"transactions": [], "error": error_detail}
    except Exception as e:
        logger.error(f"Error fetching transactions from Plaid: {e}")
        return {"transactions": [], "error": str(e)}

def get_institution_by_id(institution_id):
    """Get institution details including name and logo from Plaid"""
    if Config.DEMO_MODE:
        # Return mock institution data
        return {
            "institution": {
                "institution_id": institution_id,
                "name": "Demo Bank",
                "logo": None,
                "icon": None
            }
        }
    
    url = f"{base_url}/institutions/get_by_id"
    headers = {"Content-Type": "application/json"}
    data = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "institution_id": institution_id,
        "country_codes": ["US"],
        "options": {
            "include_optional_metadata": True,
            "include_status": False
        }
    }
    
    try:
        res = requests.post(url, headers=headers, json=data, timeout=10)
        res.raise_for_status()
        logger.info(f"Successfully fetched institution details for {institution_id}")
        return res.json()
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        try:
            error_response = e.response.json()
            error_detail = error_response.get("error_message", str(e))
        except:
            error_detail = str(e)
        logger.error(f"Error fetching institution details: {e.response.status_code} - {error_detail}")
        return {"error": error_detail}
    except Exception as e:
        logger.error(f"Error fetching institution details: {e}")
        return {"error": str(e)}

# ========== TRANSFER API ==========
def create_transfer(access_token, from_account_id, to_account_id, amount, description="Transfer"):
    """Create a bank transfer using Plaid Transfer API"""
    if Config.DEMO_MODE:
        log_demo_event("TRANSFER", f"Mock transfer: ${amount}")
        return mock_create_transfer(from_account_id, to_account_id, amount)
    
    url = f"{base_url}/transfer/create"
    headers = {"Content-Type": "application/json"}
    data = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": access_token,
        "account_id": from_account_id,
        "type": "ach",
        "network": "ach",
        "amount": str(amount),
        "description": description,
        "ach_class": "ppd",
        "user": {
            "legal_name": "User"
        }
    }
    
    try:
        res = requests.post(url, headers=headers, json=data, timeout=30)
        res.raise_for_status()
        logger.info(f"Successfully created transfer: {amount}")
        return res.json()
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        try:
            error_response = e.response.json()
            error_detail = error_response.get("error_message", str(e))
        except:
            error_detail = str(e)
        logger.error(f"Error creating transfer: {e.response.status_code} - {error_detail}")
        return {"error": error_detail}
    except Exception as e:
        logger.error(f"Error creating transfer: {e}")
        return {"error": str(e)}

def mock_create_transfer(from_account_id, to_account_id, amount):
    """Mock transfer for demo mode"""
    import uuid
    return {
        "transfer": {
            "id": f"transfer_{uuid.uuid4().hex[:12]}",
            "account_id": from_account_id,
            "amount": str(amount),
            "status": "pending",
            "created": datetime.datetime.now().isoformat()
        }
    }

def simulate_transfer_webhook(transfer_id, webhook_code="TRANSFER_SENT"):
    """Simulate a transfer webhook event in sandbox"""
    if Config.DEMO_MODE:
        return {"message": "Mock webhook fired"}
    
    url = f"{base_url}{Config.PLAID_SANDBOX_TRANSFER_WEBHOOK_ENDPOINT}"
    headers = {"Content-Type": "application/json"}
    data = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "webhook_code": webhook_code,
        "transfer_id": transfer_id
    }
    
    try:
        res = requests.post(url, headers=headers, json=data, timeout=10)
        res.raise_for_status()
        logger.info(f"Successfully fired transfer webhook: {webhook_code}")
        return res.json()
    except Exception as e:
        logger.error(f"Error firing webhook: {e}")
        return {"error": str(e)}

# ========== UNIFIED INTERFACE ==========
def create_link_token(user_id):
    """Unified interface for creating link tokens"""
    if Config.DEMO_MODE:
        log_demo_event("LINK_TOKEN", "Using mock link token")
        return mock_create_link_token(user_id)
    else:
        return real_create_link_token(user_id)

def get_accounts(access_token):
    """Unified interface for getting accounts"""
    if Config.DEMO_MODE:
        log_demo_event("ACCOUNTS", "Using mock accounts")
        return mock_get_accounts("demo")
    else:
        return real_get_accounts(access_token)