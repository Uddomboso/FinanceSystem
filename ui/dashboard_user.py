from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QStackedWidget, QFrame, QComboBox, QSizePolicy, QScrollArea
)
from PyQt5.QtGui import QPixmap, QFont, QIcon
from PyQt5.QtCore import Qt, QSize
import qtawesome as qta
from datetime import datetime, timedelta
import webbrowser
from flask import Flask, request
import threading
import os
import traceback

from ui.transaction_form import TransactionForm
from ui.budget_window import BudgetWindow
from ui.charts_window import ChartsWindow
from ui.settings_window import SettingsWindow
from ui.ai_suggestions_window import AISuggestions
from ui.bank_connect_window import BankConnectWindow
from database.db_manager import fetch_all, fetch_one, execute_query
from core.transactions import get_total_by_type, insert_plaid_transaction
from core.currency import convert
from core.plaid_api import create_link_token, exchange_public_token, get_accounts, get_transactions

class UserDashboard(QMainWindow):
    def __init__(self, username, user_id):
        super().__init__()
        self.username = username
        self.user_id = user_id

        self.setWindowTitle("PennyWise | Dashboard")
        self.setMinimumSize(1440, 900)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        self.nav_buttons = {}

        self.init_sidebar()
        self.init_pages()
        self.show_dashboard()

        threading.Thread(target=self.run_flask_server, daemon=True).start()
        self.launch_plaid_in_browser()


    # test if flask is running 
    print("🚀 Starting Flask server...")
    # remove later

    def run_flask_server(self):
        app = Flask(__name__)
        dashboard_ref = self

        @app.route("/success")
        def plaid_success():
            try:
                print(" Callback received")
                public_token = request.args.get("token")
                print("Public token received:",public_token)

                if public_token:
                    data = exchange_public_token(public_token)
                    print("🎯 Exchange response:",data)

                    access_token = data.get("access_token")
                    if access_token:
                        accounts = get_accounts(access_token)
                        print(" Retrieved accounts:",accounts)

                        for acc in accounts.get("accounts",[]):
                            account_type = "salary" if "checking" in acc.get("subtype","").lower() else "savings"
                            execute_query("""
                                INSERT OR REPLACE INTO accounts (
                                    account_id, user_id, bank_name, account_type,
                                    currency, plaid_token, last_sync
                                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,(
                                acc["account_id"],
                                dashboard_ref.user_id,
                                acc.get("name","Unknown"),
                                account_type,
                                acc.get("balances",{}).get("iso_currency_code","USD"),
                                access_token,
                                datetime.now().isoformat()
                            ),commit=True)

                        start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                        end = datetime.now().strftime("%Y-%m-%d")
                        txns = get_transactions(access_token,start,end)

                        for txn in txns.get("transactions",[]):
                            insert_plaid_transaction(dashboard_ref.user_id,txn["account_id"],txn)

                        dashboard_ref.refresh_dashboard()

                return "<h2>Success You can now close this tab.</h2>"

            except Exception as e:
                import traceback
                traceback.print_exc()
                return f"<h2>Error:</h2><pre>{e}</pre>",500

    def launch_plaid_in_browser(self):
        res = create_link_token(self.user_id)
        token = res.get("link_token")
        if token:
            with open("ui/plaid_link.html","w") as f:
                f.write(f"""
    <!DOCTYPE html>
    <html>
      <head>
        <title>Link Bank</title>
        <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
      </head>
      <body>
        <h2>Linking Your Bank Account...</h2>
        <script>
          var linkHandler = Plaid.create({{
            token: "{token}",
            onSuccess: function(public_token, metadata) {{
              window.location.href = "http://127.0.0.1:5000/success?token=" + public_token;
            }},
            onExit: function(err, metadata) {{
              console.log("Exited Plaid Link", err, metadata);
            }}
          }});
          linkHandler.open();
        </script>
      </body>
    </html>
                )
            webbrowser.open("file://" + os.path.abspath("ui/plaid_link.html"))

    def init_sidebar(self):
        sidebar = QVBoxLayout()
        sidebar.setAlignment(Qt.AlignTop)
        sidebar.setSpacing(20)
        sidebar.setContentsMargins(0,20,0,20)

        logo = QLabel()
        pixmap = QPixmap("logopng.png")
        pixmap = pixmap.scaled(150,150,Qt.KeepAspectRatio,Qt.SmoothTransformation)
        logo.setPixmap(pixmap)
        logo.setAlignment(Qt.AlignCenter)
        sidebar.addWidget(logo)

        nav_items = [
            ("Dashboard","fa5s.tachometer-alt",self.show_dashboard),
            ("Transactions","fa5s.exchange-alt",self.show_transactions),
            ("Budget","fa5s.money-bill-wave",self.show_budget),
            ("Reports","fa5s.chart-bar",self.show_reports),
            ("Settings","fa5s.cog",self.show_settings),
            ("AI Tips","fa5s.lightbulb",self.show_ai),
            ("Link Bank","fa5s.university",self.show_bank)
        ]

        for text,icon_name,func in nav_items:
            icon = qta.icon(icon_name,color="#ffe22a")
            btn = QPushButton(icon,f"  {text}")
            btn.setFont(QFont("Segoe UI",14))
            btn.setStyleSheet(self.default_btn_style())
            btn.setIconSize(QSize(24,24))
            btn.clicked.connect(func)
            btn.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed)
            self.nav_buttons[text] = btn
            sidebar.addWidget(btn)

        sidebar.addStretch()

        user_label = QLabel(f"Logged in as:\n{self.username}")
        user_label.setAlignment(Qt.AlignCenter)
        user_label.setStyleSheet("color: white; font-size: 12px;")
        sidebar.addWidget(user_label)

        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar)
        sidebar_widget.setFixedWidth(240)
        sidebar_widget.setStyleSheet("background-color: #d6733a;")
        self.main_layout.addWidget(sidebar_widget)

    def init_pages(self):
        self.stack = QStackedWidget()

        self.page_dashboard = self.build_dashboard()
        self.page_transactions = TransactionForm(self.user_id)
        self.page_budget = BudgetWindow(self.user_id)
        self.page_reports = ChartsWindow(self.user_id)
        self.page_settings = SettingsWindow(self.user_id)
        self.page_ai = AISuggestions(self.user_id)
        self.page_bank = BankConnectWindow(self.user_id,self)

        self.stack.addWidget(self.page_dashboard)
        self.stack.addWidget(self.page_transactions)
        self.stack.addWidget(self.page_budget)
        self.stack.addWidget(self.page_reports)
        self.stack.addWidget(self.page_settings)
        self.stack.addWidget(self.page_ai)
        self.stack.addWidget(self.page_bank)

        self.main_layout.addWidget(self.stack)

    def show_bank(self):
        """Show bank connection page and launch Plaid link"""
        self.stack.setCurrentWidget(self.page_bank)
        self.highlight_nav("Link Bank")
        self.launch_plaid_link()

    
    def build_dashboard(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(30)

        header = QLabel(f"Welcome back, {self.username}!")
        header.setFont(QFont("Segoe UI", 32))
        header.setStyleSheet("color: #d6733a;")
        layout.addWidget(header)

        accounts = fetch_all("""
            SELECT a.account_id, a.bank_name, a.account_type,
                   COALESCE(
                       (SELECT SUM(CASE WHEN t.transaction_type = 'income' THEN t.amount ELSE -t.amount END)
                        FROM transactions t 
                        WHERE t.account_id = a.account_id), 0) as balance
            FROM accounts a
            WHERE a.user_id = ?
        """, (self.user_id,))

        if accounts:
            accounts_section = QFrame()
            accounts_section.setStyleSheet("""
                background-color: white;
                border-radius: 10px;
                padding: 20px;
            """)
            accounts_layout = QVBoxLayout(accounts_section)

            title = QLabel("Your Bank Accounts")
            title.setStyleSheet("font-size: 18px; font-weight: bold;")
            accounts_layout.addWidget(title)

            for account in accounts:
                account_widget = QFrame()
                account_widget.setStyleSheet("""
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 15px;
                    margin-bottom: 10px;
                """)
                account_layout = QHBoxLayout(account_widget)

                icon = qta.icon("fa5s.university", color="#704b3b")
                icon_label = QLabel()
                icon_label.setPixmap(icon.pixmap(24, 24))
                account_layout.addWidget(icon_label)

                details = QVBoxLayout()
                name_label = QLabel(account["bank_name"])
                name_label.setStyleSheet("font-weight: bold;")
                type_label = QLabel(account["account_type"].capitalize())
                type_label.setStyleSheet("color: #6c757d; font-size: 12px;")
                details.addWidget(name_label)
                details.addWidget(type_label)
                account_layout.addLayout(details)

                balance = account["balance"] or 0
                balance_label = QLabel(f"${balance:,.2f}")
                balance_label.setStyleSheet("""
                    font-size: 18px;
                    font-weight: bold;
                    color: #28a745;
                """)
                account_layout.addWidget(balance_label)

                accounts_layout.addWidget(account_widget)

            layout.addWidget(accounts_section)

        self.update_financial_overview(layout)

        self.add_recent_activity(layout)

        container.setLayout(layout)
        scroll.setWidget(container)
        return scroll


    def add_bank_accounts_section(self,layout):

        accounts = fetch_all("""
                SELECT account_id, bank_name, account_type 
                FROM accounts 
                WHERE user_id = ?
            """,(self.user_id,))

        if not accounts:
            return

        section = QFrame()
        section.setStyleSheet("""
                background-color: white;
                border-radius: 10px;
                padding: 20px;
            """)
        section_layout = QVBoxLayout(section)

        title = QLabel("Your Bank Accounts")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        section_layout.addWidget(title)

        for account in accounts:
 
            balance = self.calculate_account_balance(account["account_id"])

            account_widget = self.create_account_widget(
                account["bank_name"],
                account["account_type"],
                balance
            )
            section_layout.addWidget(account_widget)

        layout.addWidget(section)

    def calculate_account_balance(self,account_id):

        transactions = fetch_all("""
                SELECT amount, transaction_type 
                FROM transactions 
                WHERE account_id = ?
            """,(account_id,))

        balance = 0
        for txn in transactions:
            if txn["transaction_type"] == "income":
                balance += txn["amount"]
            else:
                balance -= txn["amount"]

        return balance

    def create_account_widget(self,bank_name,account_type,balance):
        widget = QFrame()
        widget.setStyleSheet("""
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            """)
        layout = QHBoxLayout(widget)

        icon = qta.icon("fa5s.university",color="#704b3b")
        icon_label = QLabel()
        icon_label.setPixmap(icon.pixmap(24,24))
        layout.addWidget(icon_label)

        details = QVBoxLayout()
        details.setSpacing(5)

        name_label = QLabel(bank_name)
        name_label.setStyleSheet("font-weight: bold;")

        type_label = QLabel(account_type.capitalize())
        type_label.setStyleSheet("color: #6c757d; font-size: 12px;")

        details.addWidget(name_label)
        details.addWidget(type_label)
        layout.addLayout(details)

        balance_label = QLabel(f"${balance:,.2f}")
        balance_label.setStyleSheet("""
                font-size: 18px; 
                font-weight: bold;
                color: #28a745;
            """)
        layout.addWidget(balance_label)

        return widget
        self.update_financial_overview(layout)

        self.add_recent_activity(layout)

        container.setLayout(layout)
        scroll.setWidget(container)
        return scroll

    def update_financial_overview(self,layout):

        totals = get_total_by_type(self.user_id)
        income = next((t["total"] for t in totals if t["transaction_type"] == "income"),0)
        expense = next((t["total"] for t in totals if t["transaction_type"] == "expense"),0)
        balance = income - expense

        user_currency = fetch_one("SELECT currency FROM settings WHERE user_id = ?",(self.user_id,))
        currency = user_currency["currency"] if user_currency else "USD"

        if currency != "USD":
            income = convert(income,"USD",currency) or income
            expense = convert(expense,"USD",currency) or expense
            balance = convert(balance,"USD",currency) or balance

        overview_frame = QFrame()
        overview_frame.setStyleSheet("""
            background-color: white;
            border-radius: 10px;
            padding: 20px;
        """)
        overview_layout = QHBoxLayout(overview_frame)

        balance_card = self.create_finance_card(
            "Total Balance",
            f"{currency} {balance:,.2f}",
            "#4CAF50" if balance >= 0 else "#F44336"
        )

        income_card = self.create_finance_card(
            "Total Income",
            f"{currency} {income:,.2f}",
            "#2196F3"
        )

        expense_card = self.create_finance_card(
            "Total Expenses",
            f"{currency} {expense:,.2f}",
            "#FF9800"
        )

        overview_layout.addWidget(balance_card)
        overview_layout.addWidget(income_card)
        overview_layout.addWidget(expense_card)
        layout.addWidget(overview_frame)

    def create_finance_card(self,title,value,color):
        card = QFrame()
        card.setStyleSheet(f"""
            background-color: {color};
            border-radius: 8px;
            padding: 15px;
        """)
        card_layout = QVBoxLayout(card)

        title_label = QLabel(title)
        title_label.setStyleSheet("""
            color: white;
            font-size: 16px;
            font-weight: bold;
        """)

        value_label = QLabel(value)
        value_label.setStyleSheet("""
            color: white;
            font-size: 24px;
            font-weight: bold;
        """)

        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)
        return card

    def add_recent_activity(self,layout):

        transactions = fetch_all("""
            SELECT t.*, c.category_name, a.bank_name 
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.category_id
            LEFT JOIN accounts a ON t.account_id = a.account_id
            WHERE t.user_id = ?
            ORDER BY t.date DESC
            LIMIT 5
        """,(self.user_id,))

        activity_frame = QFrame()
        activity_frame.setStyleSheet("""
            background-color: white;
            border-radius: 10px;
            padding: 20px;
        """)
        activity_layout = QVBoxLayout(activity_frame)

        title = QLabel("Recent Activity")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #343a40;")
        activity_layout.addWidget(title)

        if not transactions:
            no_data = QLabel("No recent transactions found")
            no_data.setStyleSheet("color: #6c757d; font-size: 14px;")
            activity_layout.addWidget(no_data)
        else:
            for txn in transactions:
                txn_widget = self.create_transaction_widget(txn)
                activity_layout.addWidget(txn_widget)

        layout.addWidget(activity_frame)

    def create_transaction_widget(self,txn):
        widget = QFrame()
        widget.setStyleSheet("""
            border-bottom: 1px solid #e9ecef;
            padding: 10px 0;
        """)
        layout = QHBoxLayout(widget)

        icon = qta.icon(
            "fa5s.arrow-up" if txn["transaction_type"] == "expense" else "fa5s.arrow-down",
            color="#dc3545" if txn["transaction_type"] == "expense" else "#28a745"
        )
        icon_label = QLabel()
        icon_label.setPixmap(icon.pixmap(24,24))
        layout.addWidget(icon_label)

        # Transaction details
        details = QVBoxLayout()
        details.setSpacing(5)

        desc = QLabel(txn["description"] or "No description")
        desc.setStyleSheet("font-weight: bold;")

        meta = QLabel(f"{txn['category_name'] or 'Uncategorized'} • {txn['bank_name'] or 'No account'}")
        meta.setStyleSheet("color: #6c757d; font-size: 12px;")

        details.addWidget(desc)
        details.addWidget(meta)
        layout.addLayout(details)

        right = QVBoxLayout()
        right.setSpacing(5)
        right.setAlignment(Qt.AlignRight)

        amount = QLabel(f"{txn['amount']:.2f}")
        amount.setStyleSheet(f"""
            font-weight: bold;
            color: {'#dc3545' if txn['transaction_type'] == 'expense' else '#28a745'};
        """)

        date = QLabel(txn["date"].split()[0] if isinstance(txn["date"],str) else txn["date"].strftime("%Y-%m-%d"))
        date.setStyleSheet("color: #6c757d; font-size: 12px;")

        right.addWidget(amount)
        right.addWidget(date)
        layout.addLayout(right)

        return widget

    def update_dashboard(self):
        """Refresh dashboard data"""
        self.page_dashboard = self.build_dashboard()
        self.stack.removeWidget(self.stack.widget(0))
        self.stack.insertWidget(0,self.page_dashboard)
        self.stack.setCurrentIndex(0)

    def highlight_nav(self,active_text):
        for text,btn in self.nav_buttons.items():
            if text == active_text:
                btn.setStyleSheet(self.active_btn_style())
            else:
                btn.setStyleSheet(self.default_btn_style())

    def default_btn_style(self):
        return """
            QPushButton {
                background-color: #704b3b;
                color: white;
                padding: 12px;
                border: none;
                border-bottom: 4px solid transparent;
                border-radius: 0px;
                text-align: left;
            }
            QPushButton:hover {
                border-bottom: 4px solid #ffe22a;
            }
        """

    def active_btn_style(self):
        return """
            QPushButton {
                background-color: #704b3b;
                color: #ffe22a;
                padding: 12px;
                border: none;
                border-bottom: 4px solid #ffe22a;
                font-weight: bold;
                text-align: left;
            }
        """

    def show_dashboard(self):
        self.stack.setCurrentWidget(self.page_dashboard)
        self.highlight_nav("Dashboard")

    def show_transactions(self):
        self.stack.setCurrentWidget(self.page_transactions)
        self.highlight_nav("Transactions")

    def show_budget(self):
        self.stack.setCurrentWidget(self.page_budget)
        self.highlight_nav("Budget")

    def show_reports(self):
        self.stack.setCurrentWidget(self.page_reports)
        self.highlight_nav("Reports")

    def show_settings(self):
        self.stack.setCurrentWidget(self.page_settings)
        self.highlight_nav("Settings")

    def show_ai(self):
        self.stack.setCurrentWidget(self.page_ai)
        self.highlight_nav("AI Tips")

    def show_bank(self):
        self.stack.setCurrentWidget(self.page_bank)
        self.highlight_nav("Link Bank")

    def refresh_dashboard(self):
        new_dashboard = self.build_dashboard()
        self.stack.removeWidget(self.page_dashboard)
        self.page_dashboard = new_dashboard
        self.stack.insertWidget(0,self.page_dashboard)
        self.stack.setCurrentWidget(self.page_dashboard)





