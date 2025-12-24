"""
Minimal WorkOS SSO helper server.

Usage:
1) Set .env with:
   WORKOS_API_KEY=sk_...
   WORKOS_CLIENT_ID=client_...
   WORKOS_REDIRECT_URL=http://localhost:8000/callback
   # optionally:
   # WORKOS_CONNECTION_ID=conn_...  or WORKOS_ORGANIZATION_ID=org_...
2) pip install workos flask python-dotenv
3) python auth_server.py
4) In your app, open http://localhost:8000/ in a browser to start SSO.
"""

import os
from flask import Flask, redirect, request
from dotenv import load_dotenv
from workos import client


load_dotenv()

WORKOS_API_KEY = os.environ.get("WORKOS_API_KEY", "")
WORKOS_CLIENT_ID = os.environ.get("WORKOS_CLIENT_ID", "")
WORKOS_REDIRECT_URL = os.environ.get("WORKOS_REDIRECT_URL", "") or os.environ.get("WORKOS_REDIRECT_URI", "")
WORKOS_CONNECTION_ID = os.environ.get("WORKOS_CONNECTION_ID", "")
WORKOS_ORGANIZATION_ID = os.environ.get("WORKOS_ORGANIZATION_ID", "")

workos = client.Client(api_key=WORKOS_API_KEY)
app = Flask(__name__)


def _auth_url():
    # One of connection or organization is required by WorkOS
    kwargs = {}
    if WORKOS_CONNECTION_ID:
        kwargs["connection"] = WORKOS_CONNECTION_ID
    if WORKOS_ORGANIZATION_ID:
        kwargs["organization"] = WORKOS_ORGANIZATION_ID

    return workos.sso.get_authorization_url(
        client_id=WORKOS_CLIENT_ID,
        redirect_uri=WORKOS_REDIRECT_URL,
        **kwargs,
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
    profile = workos.sso.get_profile_and_token(code=code)
    # TODO: persist session, update app state, etc.
    return f"Logged in as {profile.email}"


if __name__ == "__main__":
    app.run(port=8000, debug=False)

