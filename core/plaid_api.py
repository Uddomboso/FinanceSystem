

import uuid
import random
import datetime
import requests

# sandbox keys (from your plaid dashboard)
client_id = "insertyourid"
secret = "insertyoursecret"
base_url = "https://sandbox.plaid.com"

# this part is to toggle between real sanbox plaid api and a fake demo
use_mock = True  # set to false for test


def mock_create_link_token(user_id):
    return f"mock-link-token-{uuid.uuid4()}"

def mock_get_accounts(user_id):
    return [
        {
            "account_id": f"acc_{uuid.uuid4().hex[:6]}",
            "name": "GTBank Checking",
            "type": "salary",
            "balance": round(random.uniform(1500, 5000), 2),
            "currency": "NGN",
            "last_sync": datetime.datetime.now().isoformat(),
            "plaid_token": "mock-access-token"
        },
        {
            "account_id": f"acc_{uuid.uuid4().hex[:6]}",
            "name": "PiggyVest Savings",
            "type": "savings",
            "balance": round(random.uniform(3000, 10000), 2),
            "currency": "NGN",
            "last_sync": datetime.datetime.now().isoformat(),
            "plaid_token": "mock-access-token"
        }
    ]

# -------- REAL SANDBOX PLAID ----------

def real_create_link_token(user_id):
    url = f"{base_url}/link/token/create"
    headers = {"Content-Type": "application/json"}
    body = {
        "client_id": client_id,
        "secret": secret,
        "client_name": "pennywise demo",
        "user": {"client_user_id": str(user_id)},
        "products": ["transactions"],
        "country_codes": ["US"],
        "language": "en"
    }
    res = requests.post(url, headers=headers, json=body)
    return res.json()

def exchange_public_token(public_token):
    url = f"{base_url}/item/public_token/exchange"
    data = {
        "client_id": client_id,
        "secret": secret,
        "public_token": public_token
    }
    res = requests.post(url, json=data)
    return res.json()

def real_get_accounts(access_token):
    url = f"{base_url}/accounts/get"
    data = {
        "client_id": client_id,
        "secret": secret,
        "access_token": access_token
    }
    res = requests.post(url, json=data)
    return res.json()

# -------- PUBLIC INTERFACE ----------

def create_link_token(user_id):
    if use_mock:
        return mock_create_link_token(user_id)
    return real_create_link_token(user_id)

def get_mock_accounts(user_id):
    return mock_get_accounts(user_id)

def get_accounts(access_token):
    if use_mock:
        return {"accounts": mock_get_accounts("demo")}  # wrapped to match plaid's format
    return real_get_accounts(access_token)
