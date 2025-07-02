import uuid
import random
import datetime
import requests

# plad sandbox credentials
client_id = "."
secret = "."
base_url = "https://sandbox.plaid.com"

# toggle mock mode (True = use fake data, False = use real Plaid API)
use_mock = False


# ========== MOCK MODE [TESTING]==========
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
        "client_id": client_id,
        "secret": secret,
        "client_name": "PennyWise Demo",
        "user": {"client_user_id": str(user_id)},
        "products": ["transactions"],
        "country_codes": ["US"],
        "language": "en"
    }
    try:
        res = requests.post(url, headers=headers, json=body)
        return res.json()
    except Exception as e:
        return {"error": str(e)}

def exchange_public_token(public_token):
    url = f"{base_url}/item/public_token/exchange"
    data = {
        "client_id": client_id,
        "secret": secret,
        "public_token": public_token
    }
    try:
        res = requests.post(url, json=data)
        return res.json()
    except Exception as e:
        return {"error": str(e)}

def real_get_accounts(access_token):
    url = f"{base_url}/accounts/get"
    data = {
        "client_id": client_id,
        "secret": secret,
        "access_token": access_token
    }
    try:
        res = requests.post(url, json=data)
        return res.json()
    except Exception as e:
        return {"accounts": [], "error": str(e)}


# ========== UNIFIED INTERFACE ==========
def create_link_token(user_id):
    return mock_create_link_token(user_id) if use_mock else real_create_link_token(user_id)

def get_accounts(access_token):
    return mock_get_accounts("demo") if use_mock else real_get_accounts(access_token)

def get_transactions(access_token, start_date, end_date):
    url = f"{base_url}/transactions/get"
    data = {
        "client_id": client_id,
        "secret": secret,
        "access_token": access_token,
        "start_date": start_date,
        "end_date": end_date
    }
    res = requests.post(url, json=data)
    return res.json()

