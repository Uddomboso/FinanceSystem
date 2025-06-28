from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, pyqtSlot
from core.plaid_api import create_link_token, exchange_public_token, get_accounts
from core.plaid_api import get_transactions
from core.transactions import insert_plaid_transaction
import datetime


class BankConnectWindow(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("Link Bank Account (Sandbox)")
        self.setMinimumSize(800, 600)

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
        self.instructions.setStyleSheet("background: #fff3cd; padding: 12px; border-radius: 8px; color: #856404;")
        self.instructions.setWordWrap(True)
        self.layout.addWidget(self.instructions)

        self.web_view = QWebEngineView()
        self.layout.addWidget(self.web_view)

        self.web_view.urlChanged.connect(self.handle_redirect)

        self.init_plaid()

    def init_plaid(self):
        response = create_link_token(self.user_id)

        if "error" in response:
            self.status_label.setText("❌ Error creating link token.")
            QMessageBox.critical(self, "Plaid Error", response["error"])
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
        <script>
        var handler = Plaid.create({{
            token: '{token}',
            onSuccess: function(public_token, metadata) {{
                window.location.href = 'plaid-success://' + public_token;
            }},
            onExit: function(err, metadata) {{
                alert('Plaid exited.');
            }}
        }});
        handler.open();
        </script>
        </body></html>
        """
        self.web_view.setHtml(html, QUrl("https://localhost/"))

    @pyqtSlot(QUrl)
    def handle_redirect(self, url):
        if url.scheme() != "plaid-success":
            return

        public_token = url.toString().split("://")[1]
        token_response = exchange_public_token(public_token)

        if "error" in token_response or "access_token" not in token_response:
            self.status_label.setText("❌ Failed to exchange token.")
            QMessageBox.critical(self, "Error", token_response.get("error", "Unknown error"))
            return

        access_token = token_response["access_token"]
        accounts = get_accounts(access_token)

        start = (datetime.datetime.now() - datetime.timedelta(days=30)).date().isoformat()
        end = datetime.datetime.now().date().isoformat()
        txns_data = get_transactions(access_token,start,end)

        for txn in txns_data.get("transactions",[]):
            insert_plaid_transaction(self.user_id,None,txn)

        if "error" in accounts:
            QMessageBox.critical(self, "Error", accounts["error"])
            return

        self.display_accounts(accounts)

    def display_accounts(self, accounts_data):
        self.status_label.setText("✅ Accounts linked successfully")
        self.web_view.hide()

        for acc in accounts_data.get("accounts", []):
            name = acc.get("name", "Unknown Bank")
            subtype = acc.get("subtype", "account")
            balance = acc.get("balances", {}).get("available", "N/A")
            currency = acc.get("balances", {}).get("iso_currency_code", "USD")

            label = QLabel(f"{name} ({subtype}) — {currency} {balance}")
            label.setStyleSheet("padding: 8px; font-weight: bold;")
            self.layout.addWidget(label)
