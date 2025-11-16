from PyQt5.QtWidgets import QWidget,QVBoxLayout,QLabel,QMessageBox,QPushButton
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl,pyqtSlot,QTimer
import socket
from core.plaid_api import create_link_token,exchange_public_token,get_accounts,get_transactions
from core.transactions import insert_plaid_transaction
from database.db_manager import execute_query,fetch_all
import datetime
import webbrowser
from flask import Flask, request
import threading
import time
import sys


class BankConnectWindow(QWidget):
    def __init__(self,user_id,parent=None):
        super().__init__()
        self.user_id = user_id
        self.parent_dashboard = parent
        self.setWindowTitle("Link Bank Account")
        self.setMinimumSize(800,600)
        self.flask_server = None
        self.flask_thread = None
        self.flask_running = False
        self.flask_port = None

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.status_label = QLabel("🔐 Initializing secure Plaid sandbox session...")
        self.layout.addWidget(self.status_label)

        self.instructions = QLabel("""
        <b>Use these test credentials:</b><br>
        • Username: <code>user_good</code><br>
        • Password: <code>pass_good</code><br>
        <i>No phone number required. If prompted, click "Continue as guest".</i>
        """)
        self.instructions.setStyleSheet("""
            background: #fff3cd; 
            padding: 12px; 
            border-radius: 8px; 
            color: #856404;
        """)
        self.instructions.setWordWrap(True)
        self.layout.addWidget(self.instructions)

        self.web_view = QWebEngineView()
        self.layout.addWidget(self.web_view)

        self.web_view.urlChanged.connect(self.handle_redirect)

        self.refresh_btn = QPushButton("Refresh Accounts")
        self.refresh_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        self.refresh_btn.clicked.connect(self.refresh_accounts)
        self.refresh_btn.hide()
        self.layout.addWidget(self.refresh_btn)

        self.start_flask_server()
        self.init_plaid()

    def start_flask_server(self):
        try:
            app = Flask(__name__)
            widget_ref = self

            @app.route("/success")
            def plaid_success():
                try:
                    print(f"[DEBUG] Flask /success route called!")
                    print(f"[DEBUG] Request args: {request.args}")
                    public_token = request.args.get("token")
                    if public_token:
                        print(f"[DEBUG] Flask received public_token: {public_token[:20]}...")
                        print(f"[DEBUG] About to call process_public_token for user {widget_ref.user_id}")
                        QTimer.singleShot(0, lambda: widget_ref.process_public_token(public_token))
                        return "<h2>✅ Success! Your bank account is being linked...</h2><p>You can close this window.</p>"
                    print(f"[DEBUG] ERROR: No token received in Flask callback")
                    return "<h2>Error: No token received</h2>"
                except Exception as e:
                    import traceback
                    print(f"[ERROR] Flask callback error: {e}")
                    traceback.print_exc()
                    return f"<h2>Error:</h2><pre>{e}</pre>", 500

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('127.0.0.1', 0))
            self.flask_port = s.getsockname()[1]
            s.close()

            try:
                self.flask_thread = threading.Thread(target=lambda: app.run(port=self.flask_port, debug=False, use_reloader=False), daemon=True)
                self.flask_thread.start()
                self.flask_running = True
                time.sleep(1.0)
                print(f"[DEBUG] Flask server started on port {self.flask_port} for BankConnectWindow")
            except Exception as thread_error:
                print(f"[ERROR] Failed to start Flask thread: {thread_error}")
        except Exception as e:
            print(f"Failed to start Flask server: {e}")

    def process_public_token(self, public_token):
        """Process the public token from Flask callback"""
        print(f"[DEBUG] process_public_token called for user_id: {self.user_id}")
        print(f"[DEBUG] Public token (first 20 chars): {public_token[:20]}...")
        try:
            print(f"[DEBUG] Exchanging public token...")
            token_response = exchange_public_token(public_token)
            print(f"[DEBUG] Token exchange response: {token_response}")

            if "error" in token_response or "access_token" not in token_response:
                error_msg = token_response.get("error","Unknown error")
                print(f"[ERROR] Token exchange failed: {error_msg}")
                self.status_label.setText("❌ Failed to exchange token.")
                QMessageBox.critical(self,"Error",error_msg)
                return

            access_token = token_response["access_token"]
            print(f"[DEBUG] Got access_token, calling process_accounts for user {self.user_id}")
            self.process_accounts(access_token)
            print(f"[DEBUG] process_accounts completed")
        except Exception as e:
            print(f"[ERROR] Error processing public token: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self,"Error",f"Failed to process token: {str(e)}")

    def init_plaid(self):
        response = create_link_token(self.user_id)

        if "error" in response:
            self.status_label.setText("❌ Error creating link token.")
            QMessageBox.critical(self,"Plaid Error",response["error"])
            return

        token = response.get("link_token")
        if not token:
            self.status_label.setText("❌ No link token received.")
            return

        html = f"""
        <html><head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
        </head><body>
        <div id="status" style="padding: 20px; font-family: Arial;">
            <h3>Waiting for Plaid Link...</h3>
        </div>
        <script>
        var handler = Plaid.create({{
            token: '{token}',
            onSuccess: function(public_token, metadata) {{
                document.getElementById('status').innerHTML = '<h3 style="color: green;">✅ Linking successful! Processing...</h3>';
                window.location.href = 'http://127.0.0.1:{self.flask_port}/success?token=' + public_token;
            }},
            onExit: function(err, metadata) {{
                if (err) {{
                    document.getElementById('status').innerHTML = '<h3 style="color: red;">❌ Error: ' + err.error_message + '</h3>';
                }} else {{
                    document.getElementById('status').innerHTML = '<h3 style="color: orange;">⚠️ Connection closed</h3>';
                }}
            }}
        }});
        handler.open();
        </script>
        </body></html>
        """
        self.web_view.setHtml(html,QUrl("https://localhost/"))

    @pyqtSlot(QUrl)
    def handle_redirect(self,url):
        # Check if this is the success URL from Plaid
        url_str = url.toString()
        print(f"[DEBUG] URL changed to: {url_str}")
        if "/success" in url_str and "token=" in url_str:
            # Extract token from URL as fallback
            try:
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(url_str)
                params = parse_qs(parsed.query)
                if 'token' in params:
                    public_token = params['token'][0]
                    print(f"[DEBUG] Extracted token from URL redirect: {public_token[:20]}...")
                    print(f"[DEBUG] Processing token directly from URL redirect")
                    self.process_public_token(public_token)
            except Exception as e:
                print(f"[ERROR] Failed to extract token from URL: {e}")

    def process_accounts(self,access_token):
        accounts_data = get_accounts(access_token)

        if "error" in accounts_data:
            QMessageBox.critical(self,"Error",accounts_data["error"])
            return

        print(f"[DEBUG] Processing accounts for user_id: {self.user_id}")
        print(f"[DEBUG] Found {len(accounts_data.get('accounts', []))} accounts to process")
        
        # Extract institution information from Plaid response
        # The response includes an 'item' object with institution_id
        institution_id = None
        institution_name = None
        institution_logo = None
        
        if "item" in accounts_data:
            institution_id = accounts_data["item"].get("institution_id")
        
        # Fetch institution details from Plaid API to get real name and logo
        if institution_id:
            from core.plaid_api import get_institution_by_id
            institution_data = get_institution_by_id(institution_id)
            
            if "institution" in institution_data and "error" not in institution_data:
                institution = institution_data["institution"]
                institution_name = institution.get("name", None)
                institution_logo = institution.get("logo", None) or institution.get("icon", None)
        
        # Fallback: extract from account name if API call failed
        if not institution_name and accounts_data.get("accounts"):
            first_acc_name = accounts_data["accounts"][0].get("name", "")
            if first_acc_name:
                # For Plaid sandbox, accounts are named like "Plaid Checking", "Tartan Bank Checking", etc.
                # Extract bank name (remove "Plaid" prefix and account type)
                parts = first_acc_name.replace("Plaid", "").strip().split()
                if len(parts) > 0:
                    # Remove account type words (Checking, Savings, etc.)
                    account_types = ["checking", "savings", "credit", "card", "loan"]
                    filtered_parts = [p for p in parts if p.lower() not in account_types]
                    if filtered_parts:
                        institution_name = " ".join(filtered_parts)
                    else:
                        institution_name = parts[0] if parts else "Bank"
        
        # Final fallback
        if not institution_name:
            institution_name = "Connected Bank"
        
        print(f"[DEBUG] Institution: {institution_name} (ID: {institution_id}, Logo: {institution_logo})")

        # Save accounts to database
        saved_count = 0
        from database.db_manager import fetch_one
        
        from database.migrations.add_institution_migration import apply_institution_migration
        apply_institution_migration()
        
        # Filter accounts: save main checking account, exclude business/cd accounts
        # We only save the main checking account (not business, savings sub-accounts, cd, etc.)
        main_checking = None
        for acc in accounts_data.get("accounts",[]):
            subtype = acc.get("subtype","").lower()
            
            # Only include checking accounts (not business, cd, etc.)
            # We want the main plaid checking account only
            if "checking" in subtype and "business" not in subtype:
                if main_checking is None:
                    main_checking = acc
                    break
        
        # If no checking account found, look for any non-business account as fallback
        if main_checking is None:
            for acc in accounts_data.get("accounts",[]):
                subtype = acc.get("subtype","").lower()
                if "business" not in subtype and "cd" not in subtype:
                    main_checking = acc
                    break
        
        # Save only the main checking account
        def save_account(acc, acc_type):
            nonlocal saved_count
            # Check if account already exists for this user
            existing = fetch_one("""
                SELECT id FROM accounts 
                WHERE account_id = ? AND user_id = ?
            """, (acc["account_id"], self.user_id))
            
            try:
                if existing:
                    # Update existing account
                    print(f"[DEBUG] Updating existing account: {acc.get('name', 'Unknown')} (ID: {acc['account_id']})")
                    q = """
                    UPDATE accounts SET
                        bank_name = ?, account_type = ?, 
                        currency = ?, plaid_token = ?, last_sync = ?,
                        institution_id = ?, institution_name = ?, institution_logo = ?
                    WHERE account_id = ? AND user_id = ?
                    """
                    execute_query(q,(
                        acc.get("name","Unknown Bank"),
                        acc_type,
                        acc.get("balances",{}).get("iso_currency_code","USD"),
                        access_token,
                        datetime.datetime.now().isoformat(),
                        institution_id,
                        institution_name,
                        institution_logo,
                        acc["account_id"],
                        self.user_id
                    ),commit=True)
                    saved_count += 1
                else:
                    # Insert new account
                    print(f"[DEBUG] Inserting new account: {acc.get('name', 'Unknown')} (ID: {acc['account_id']}) for user {self.user_id}")
                    q = """
                    INSERT INTO accounts (
                        account_id, user_id, bank_name, account_type, 
                        currency, plaid_token, last_sync, institution_id, institution_name, institution_logo
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    execute_query(q,(
                        acc["account_id"],
                        self.user_id,
                        acc.get("name","Unknown Bank"),
                        acc_type,
                        acc.get("balances",{}).get("iso_currency_code","USD"),
                        access_token,
                        datetime.datetime.now().isoformat(),
                        institution_id,
                        institution_name,
                        institution_logo
                    ),commit=True)
                    saved_count += 1
            except Exception as e:
                print(f"[ERROR] Failed to save account {acc.get('name', 'Unknown')}: {e}")
                import traceback
                traceback.print_exc()
        
        if main_checking:
            # Save as salary type (checking/main account)
            save_account(main_checking, "salary")
        else:
            print(f"[WARNING] No main checking account found in Plaid response")
        
        print(f"[DEBUG] Successfully saved {saved_count} accounts for user {self.user_id}")

        # Fetch recent transactions
        start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = datetime.datetime.now().strftime("%Y-%m-%d")
        txns_data = get_transactions(access_token,start_date,end_date)

        if "transactions" in txns_data:
            for txn in txns_data["transactions"]:
                account_id = txn.get("account_id")
                insert_plaid_transaction(self.user_id,account_id,txn)

        print(f"[DEBUG] About to refresh dashboard. Parent dashboard: {self.parent_dashboard}")
        print(f"[DEBUG] Parent dashboard type: {type(self.parent_dashboard)}")
        
        if self.parent_dashboard:
            print(f"[DEBUG] Calling refresh_dashboard()")
            self.parent_dashboard.refresh_dashboard()
            print(f"[DEBUG] Calling update_dashboard()")
            self.parent_dashboard.update_dashboard()
            print(f"[DEBUG] Dashboard refresh calls complete")

        self.display_accounts(accounts_data)
        
        # Force accounts page refresh immediately
        if self.parent_dashboard:
            print(f"[DEBUG] Force refreshing accounts page immediately")
            if hasattr(self.parent_dashboard, 'refresh_accounts_page'):
                self.parent_dashboard.refresh_accounts_page()
            # Also try navigating to accounts page to force refresh
            if hasattr(self.parent_dashboard, 'show_accounts'):
                QTimer.singleShot(500, lambda: self.parent_dashboard.show_accounts())
                QTimer.singleShot(1000, lambda: self.parent_dashboard.refresh_accounts_page())

    def display_accounts(self,accounts_data):
        self.status_label.setText("✅ Accounts linked successfully")
        self.web_view.hide()
        self.refresh_btn.show()

        # Clear previous account displays
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget and widget not in [self.status_label,self.instructions,self.web_view,self.refresh_btn]:
                widget.deleteLater()

        if not accounts_data.get("accounts"):
            self.layout.addWidget(QLabel("No accounts found"))
            return

        for acc in accounts_data["accounts"]:
            name = acc.get("name","Unknown Bank")
            subtype = acc.get("subtype","account")
            balance = acc.get("balances",{}).get("available",0) or 0
            currency = acc.get("balances",{}).get("iso_currency_code","USD") or "USD"

            account_frame = QWidget()
            account_frame.setStyleSheet("""
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 12px;
                border: 1px solid #dee2e6;
            """)
            account_layout = QVBoxLayout(account_frame)

            name_label = QLabel(f"<b>{name}</b> ({subtype})")
            name_label.setStyleSheet("font-size: 16px;")

            balance_value = balance if balance is not None else 0
            balance_label = QLabel(f"Balance: <b>{currency} {balance_value:,.2f}</b>")
            balance_label.setStyleSheet("font-size: 14px; color: #28a745;")

            account_layout.addWidget(name_label)
            account_layout.addWidget(balance_label)
            self.layout.addWidget(account_frame)

    def refresh_accounts(self):
        # Get all access tokens for this user
        accounts = fetch_all("""
            SELECT DISTINCT plaid_token FROM accounts 
            WHERE user_id = ? AND plaid_token IS NOT NULL
        """,(self.user_id,))

        if not accounts:
            QMessageBox.warning(self,"Error","No linked accounts found")
            return

        for account in accounts:
            self.process_accounts(account["plaid_token"])

        QMessageBox.information(self,"Success","Accounts refreshed")
        if self.parent_dashboard:
            self.parent_dashboard.update_dashboard()
