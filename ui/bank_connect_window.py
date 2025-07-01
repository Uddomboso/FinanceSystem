from PyQt5.QtWidgets import QWidget,QVBoxLayout,QLabel,QMessageBox,QPushButton
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl,pyqtSlot
from core.plaid_api import create_link_token,exchange_public_token,get_accounts,get_transactions
from core.transactions import insert_plaid_transaction
from database.db_manager import execute_query,fetch_all
import datetime
import webbrowser


class BankConnectWindow(QWidget):
    def __init__(self,user_id,parent=None):
        super().__init__()
        self.user_id = user_id
        self.parent_dashboard = parent
        self.setWindowTitle("Link Bank Account")
        self.setMinimumSize(800,600)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.status_label = QLabel("Initializing secure Plaid sandbox session...")
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

        self.init_plaid()

    def init_plaid(self):
        response = create_link_token(self.user_id)

        if "error" in response:
            self.status_label.setText(" Error creating link token.")
            QMessageBox.critical(self,"Plaid Error",response["error"])
            return

        token = response.get("link_token")
        if not token:
            self.status_label.setText("No link token received.")
            return

        html = f"""
        <html><head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
        </head><body>
        <script>
        var handler = Plaid.create({{
            token: '{token}',
            onSuccess: function(public_token, metadata) {{
                window.location.href = 'plaid-success://' + public_token;
            }},
            onExit: function(err, metadata) {{
                window.location.href = 'plaid-exit://';
            }}
        }});
        handler.open();
        </script>
        </body></html>
        """
        self.web_view.setHtml(html,QUrl("https://localhost/"))

    @pyqtSlot(QUrl)
    def handle_redirect(self,url):
        if url.scheme() == "plaid-exit":
            self.status_label.setText("Plaid connection closed.")
            return

        if url.scheme() != "plaid-success":
            return

        public_token = url.toString().split("://")[1]
        token_response = exchange_public_token(public_token)

        if "error" in token_response or "access_token" not in token_response:
            self.status_label.setText("Failed to exchange token.")
            QMessageBox.critical(self,"Error",token_response.get("error","Unknown error"))
            return

        access_token = token_response["access_token"]
        self.process_accounts(access_token)

    def process_accounts(self,access_token):
        accounts_data = get_accounts(access_token)

        if "error" in accounts_data:
            QMessageBox.critical(self,"Error",accounts_data["error"])
            return

        for acc in accounts_data.get("accounts",[]):
            q = """
            INSERT OR REPLACE INTO accounts (
                account_id, user_id, bank_name, account_type, 
                currency, plaid_token, last_sync
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            account_type = "salary" if "checking" in acc.get("subtype","").lower() else "savings"
            execute_query(q,(
                acc["account_id"],
                self.user_id,
                acc.get("name","Unknown Bank"),
                account_type,
                acc.get("balances",{}).get("iso_currency_code","USD"),
                access_token,
                datetime.datetime.now().isoformat()
            ),commit=True)

        start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = datetime.datetime.now().strftime("%Y-%m-%d")
        txns_data = get_transactions(access_token,start_date,end_date)

        if "transactions" in txns_data:
            for txn in txns_data["transactions"]:
                account_id = txn.get("account_id")
                insert_plaid_transaction(self.user_id,account_id,txn)

        if self.parent_dashboard:
            self.parent_dashboard.refresh_dashboard()

        self.display_accounts(accounts_data)
        if self.parent_dashboard:
            self.parent_dashboard.update_dashboard()

    def display_accounts(self,accounts_data):
        self.status_label.setText("Accounts linked successfully")
        self.web_view.hide()
        self.refresh_btn.show()

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
            balance = acc.get("balances",{}).get("available",0)
            currency = acc.get("balances",{}).get("iso_currency_code","USD")

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

            balance_label = QLabel(f"Balance: <b>{currency} {balance:,.2f}</b>")
            balance_label.setStyleSheet("font-size: 14px; color: #28a745;")

            account_layout.addWidget(name_label)
            account_layout.addWidget(balance_label)
            self.layout.addWidget(account_frame)

    def refresh_accounts(self):

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



            def init_plaid(self):
                response = create_link_token(self.user_id)
                token = response.get("link_token")

                if not token:
                    QMessageBox.critical(self,"Plaid Error","Failed to create link token.")
                    return

                url = f"https://cdn.plaid.com/link/v2/stable/link.html?token={token}"
                webbrowser.open(url)
