"""
Minimal WorkOS AuthKit helper server.

Usage:
1) Set .env with:
   WORKOS_API_KEY=sk_...
   WORKOS_CLIENT_ID=client_...
   WORKOS_REDIRECT_URL=http://localhost:8000/callback
2) pip install workos flask python-dotenv
3) python auth_server.py
4) In your app, open http://localhost:8000/ in a browser to start Google OAuth.
"""

import os
from flask import Flask, redirect, request
from dotenv import load_dotenv

# Try to import WorkOS with latest SDK
try:
    from workos import WorkOSClient
    WORKOS_AVAILABLE = True
except ImportError:
    print("Error: WorkOS package not installed. Install with: pip install workos")
    WORKOS_AVAILABLE = False
    WorkOSClient = None


load_dotenv()

WORKOS_API_KEY = os.environ.get("WORKOS_API_KEY", "")
WORKOS_CLIENT_ID = os.environ.get("WORKOS_CLIENT_ID", "")
WORKOS_REDIRECT_URL = os.environ.get("WORKOS_REDIRECT_URL", "") or os.environ.get("WORKOS_REDIRECT_URI", "")

if WORKOS_AVAILABLE and WORKOS_API_KEY and WORKOS_CLIENT_ID:
    workos = WorkOSClient(api_key=WORKOS_API_KEY, client_id=WORKOS_CLIENT_ID)
else:
    workos = None
app = Flask(__name__)


def _auth_url():
    return workos.user_management.get_authorization_url(
        redirect_uri=WORKOS_REDIRECT_URL,
        provider="GoogleOAuth"
    )


@app.route("/")
def login():
    if not WORKOS_API_KEY or not WORKOS_CLIENT_ID or not WORKOS_REDIRECT_URL:
        return "Missing WORKOS_API_KEY / WORKOS_CLIENT_ID / WORKOS_REDIRECT_URL", 500
    url = _auth_url()
    return redirect(url)


@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Missing code", 400
    auth_response = workos.user_management.authenticate_with_code(code=code)
    user = getattr(auth_response, 'user', None)
    email = getattr(user, 'email', 'Unknown') if user else 'Unknown'
    return f"Logged in as {email}"


if __name__ == "__main__":
    app.run(port=8000, debug=False)

