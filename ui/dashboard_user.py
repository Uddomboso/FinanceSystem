from PyQt5.QtWidgets import (
    QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,
    QStackedWidget,QFrame,QComboBox,QSizePolicy,QScrollArea,QApplication
)
from PyQt5.QtGui import QPixmap,QFont,QIcon
from PyQt5.QtCore import Qt,QSize
import qtawesome as qta
from datetime import datetime,timedelta
import webbrowser
from flask import Flask,request
import threading
import os
import traceback

from core.ai_suggestions import get_recent_suggestions,generate_suggestions
from ui.transaction_form import TransactionForm
from ui.budget_window import BudgetWindow
from ui.charts_window import ChartsWindow
from ui.settings_window import SettingsWindow,DARK_QSS,LIGHT_QSS
from ui.bank_connect_window import BankConnectWindow
from database.db_manager import fetch_all,fetch_one,execute_query
from core.transactions import get_total_by_type,insert_plaid_transaction
from core.currency import convert
from ui.commitment_form import CommitmentForm
from core.salary_checker import check_salary_reminder
from core.commitment_manager import check_commitments
from PyQt5.QtWidgets import (
    QWidget,QLabel,QVBoxLayout,QHBoxLayout,QScrollArea,QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGridLayout
from core.transfer import get_recent_category_transfers
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from core.plaid_api import create_link_token,exchange_public_token,get_accounts,get_transactions
from ui.category_manager import CategoryManager
from ui.savings_goal_manager import SavingsGoalManager





class UserDashboard(QMainWindow):
    def __init__(self,username,user_id):
        super().__init__()
        self.username = username
        self.user_id = user_id

        self.setWindowTitle("PennyWise")
        self.setMinimumSize(1440,900)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        self.nav_buttons = {}

        self.init_sidebar()
        self.init_pages()
        generate_suggestions(self.user_id)
        self.show_dashboard()

        self.start_flask_thread()

    def is_dark_mode(self):
        result = fetch_one("SELECT dark_mode FROM settings WHERE user_id = ?",(self.user_id,))
        return result and result["dark_mode"]

    def run_flask_server(self):
        app = Flask(__name__)
        dashboard_ref = self

        @app.route("/success")
        def plaid_success():
            try:
                print("✅ Callback received")
                public_token = request.args.get("token")
                print("🔑 Public token received:",public_token)

                if public_token:
                    data = exchange_public_token(public_token)
                    print("🎯 Exchange response:",data)

                    access_token = data.get("access_token")
                    if access_token:
                        accounts = get_accounts(access_token)
                        print("✅ Retrieved accounts:",accounts)

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

                return "<h2>✅ Success! You can now close this tab.</h2>"

            except Exception as e:
                traceback.print_exc()
                return f"<h2>❌ Error:</h2><pre>{e}</pre>",500

        app.run(port=5000)

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
                """)
            webbrowser.open("file://" + os.path.abspath("ui/plaid_link.html"))

    def init_sidebar(self):
        sidebar = QVBoxLayout()
        sidebar.setAlignment(Qt.AlignTop)
        sidebar.setSpacing(20)
        sidebar.setContentsMargins(0,20,0,20)

        logo = QLabel()
        logo_path = "logopng.png" if self.is_dark_mode() else "logopng.png"
        pixmap = QPixmap(logo_path)
        pixmap = pixmap.scaled(150,150,Qt.KeepAspectRatio,Qt.SmoothTransformation)
        logo.setPixmap(pixmap)
        logo.setAlignment(Qt.AlignCenter)
        sidebar.addWidget(logo)

        notif_btn_layout = QHBoxLayout()
        notif_btn_layout.setAlignment(Qt.AlignCenter)

        self.notif_btn = QPushButton()
        self.notif_btn.setIcon(qta.icon("fa5s.bell",color="#ffe22a"))
        self.notif_btn.setIconSize(QSize(24,24))
        self.notif_btn.setFixedSize(40,40)
        self.notif_btn.setFlat(True)
        self.notif_btn.setCursor(Qt.PointingHandCursor)
        self.notif_btn.clicked.connect(self.toggle_notifications)

        notif_btn_layout.addWidget(self.notif_btn)
        sidebar.addLayout(notif_btn_layout)

        self.notif_popup = QFrame(self)

        popup_bg = "#1e1e1e" if self.is_dark_mode() else "white"

        self.notif_popup = QFrame(self)
        self.notif_popup.setStyleSheet(f"""
            background-color: {popup_bg};
            border: 1px solid #ccc;
            border-radius: 10px;
            padding: 10px;
        """)
        self.notif_popup.setVisible(False)
        self.notif_popup.setFixedWidth(280)
        self.notif_popup.setFixedHeight(180)
        self.notif_popup.move(250,120)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(Qt.gray)
        self.notif_popup.setGraphicsEffect(shadow)

        notif_layout = QVBoxLayout(self.notif_popup)
        notif_layout.setSpacing(4)

        notifications = fetch_all("""
            SELECT content, created_at 
            FROM notifications 
            WHERE user_id = ? AND notification_type = 'payment'
            ORDER BY created_at DESC
            LIMIT 5
        """,(self.user_id,))

        if not notifications:
            notif_layout.addWidget(QLabel("No recent payment notifications."))
        else:
            for n in notifications:
                label = QLabel(f"🪙 {n['content']}")
                label.setWordWrap(True)
                label.setStyleSheet("font-size: 13px;")
                notif_layout.addWidget(label)

        nav_items = [
            ("Dashboard","fa5s.tachometer-alt",self.show_dashboard),
            ("Transactions","fa5s.exchange-alt",self.show_transactions),
            ("Budget","fa5s.money-bill-wave",self.show_budget),
            ("Reports","fa5s.chart-bar",self.show_reports),
            ("Settings","fa5s.cog",self.show_settings),
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
        sidebar_bg = "#111111" if self.is_dark_mode() else "#d6733a"
        sidebar_widget.setStyleSheet(f"background-color: {sidebar_bg};")
        self.main_layout.addWidget(sidebar_widget)

    def apply_global_theme(self,dark_mode):
        print("🌙 Applying global theme:","dark" if dark_mode else "light")
        stylesheet = DARK_QSS if dark_mode else LIGHT_QSS
        QApplication.instance().setStyleSheet(stylesheet)

    def init_pages(self):
        self.stack = QStackedWidget()

        self.page_dashboard = self.build_dashboard()
        self.page_transactions = TransactionForm(self.user_id)
        self.page_budget = BudgetWindow(self.user_id)
        self.page_reports = ChartsWindow(self.user_id)
        self.page_bank = BankConnectWindow(self.user_id,self)  # Pass self as parent
        self.page_settings = SettingsWindow(self.user_id,parent=self)

        self.stack.addWidget(self.page_dashboard)
        self.stack.addWidget(self.page_transactions)
        self.stack.addWidget(self.page_budget)
        self.stack.addWidget(self.page_reports)
        self.stack.addWidget(self.page_settings)
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
        layout.setContentsMargins(30,30,30,30)
        layout.setSpacing(30)

        header = QLabel(f"Welcome back, {self.username}!")
        header.setFont(QFont("Segoe UI",32))
        header.setStyleSheet("color: #d6733a;")
        layout.addWidget(header)

        header.setStyleSheet(f"""
            color: #d6733a;
            background-color: transparent;
        """)

        accounts = fetch_all("""
            SELECT a.account_id, a.bank_name, a.account_type,
                   COALESCE(
                       (SELECT SUM(CASE WHEN t.transaction_type = 'income' THEN t.amount ELSE -t.amount END)
                        FROM transactions t 
                        WHERE t.account_id = a.account_id), 0) as balance
            FROM accounts a
            WHERE a.user_id = ?
        """,(self.user_id,))

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

                icon = qta.icon("fa5s.university",color="#704b3b")
                icon_label = QLabel()
                icon_label.setPixmap(icon.pixmap(24,24))
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

        self.add_category_overview(layout)

        self.update_financial_overview(layout)

        self.add_ai_tips(layout)

        self.add_recent_activity(layout)

        container.setLayout(layout)
        scroll.setWidget(container)
        return scroll

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
        overview_frame.setStyleSheet(f"""
            background-color: {'#1e1e1e' if self.is_dark_mode() else 'white'};
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

        # Expenses card
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
        activity_frame.setStyleSheet(f"""
            background-color: {'#1e1e1e' if self.is_dark_mode() else 'white'};
            border-radius: 10px;
            padding: 20px;
            border: none;
            color: {'#FFFDD0' if self.is_dark_mode() else '#333'};
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
        widget.setStyleSheet(f"""
            border-bottom: {'1px solid #e9ecef' if not self.is_dark_mode() else 'none'};
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
        check_commitments(self.user_id)
        check_salary_reminder(self.user_id)

    def show_transactions(self):
        self.stack.setCurrentWidget(self.page_transactions)
        self.highlight_nav("Transactions")

    def add_ai_tips(self,layout):
        print("Fetching AI tips for user:",self.user_id)

        try:
            tips = get_recent_suggestions(self.user_id)
            print(f"Found {len(tips)} tips")

            if not tips:
                no_tips = QLabel("No financial tips available yet.")
                no_tips.setStyleSheet("color: #6c757d; font-style: italic;")
                layout.addWidget(no_tips)
            else:
                # Just show the first tip only
                first_tip = tips[0]

                tip_label = QLabel(first_tip["content"])
                tip_label.setWordWrap(True)
                tip_label.setStyleSheet("""
                    background-color:  {'#1e1e1e' if self.is_dark_mode() else 'white'};
                    padding: 20px;
                    border-radius: 10px;
                    font-size: 15px;
                    border: none;
                    font-family: 'Segoe UI', sans-serif;
                    color:  {'#FFFDD0' if self.is_dark_mode() else '#333'};
                    border-left: 4px solid #d6733a;
                """)

                layout.addWidget(tip_label)

        except Exception as e:
            print(f"Error displaying tips: {e}")
            error_label = QLabel("Could not load financial tips. Please try again later.")
            error_label.setStyleSheet("color: #dc3545; font-size: 14px;")
            layout.addWidget(error_label)

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
        self.launch_plaid_in_browser()

    def refresh_dashboard(self):
        new_dashboard = self.build_dashboard()
        self.stack.removeWidget(self.page_dashboard)
        self.page_dashboard = new_dashboard
        self.stack.insertWidget(0,self.page_dashboard)
        self.stack.setCurrentWidget(self.page_dashboard)

    def open_commitment_form(self,category_name):
        dlg = CommitmentForm(self.user_id,category_name)
        dlg.exec_()

    def start_flask_thread(self):
        def run():
            try:
                print(" Starting Flask server in thread...")
                self.run_flask_server()
            except Exception as e:
                print("Flask thread crashed:")
                traceback.print_exc()

        thread = threading.Thread(target=run,daemon=True)
        thread.start()

    def is_dark_mode(self):
        setting = fetch_one("SELECT dark_mode FROM settings WHERE user_id = ?",(self.user_id,))
        return bool(setting["dark_mode"]) if setting and "dark_mode" in setting.keys() else False

    def show_commitment_form(self):
        self.commitment_form = CommitmentForm(self.user_id)
        self.commitment_form.show()

    def toggle_notifications(self):
        is_visible = self.notif_popup.isVisible()
        self.notif_popup.setVisible(not is_visible)

    def open_category_manager(self):
        dlg = CategoryManager(user_id=self.current_user_id)
        dlg.exec_()

    def open_savings_goal_manager(self):
        dlg = SavingsGoalManager(user_id=self.current_user_id)
        dlg.exec_()

    def add_category_overview(self,layout):
        categories = fetch_all("""
            SELECT category_name, color, budget_amount,
                   COALESCE((
                       SELECT SUM(amount)
                       FROM transactions
                       WHERE category_id = c.category_id
                         AND transaction_type = 'expense'
                   ), 0) AS spent
            FROM categories c
            WHERE user_id = ?
        """,(self.user_id,))

        wrapper = QFrame()
        wrapper.setStyleSheet(f"""
            background-color: {'#1e1e1e' if self.is_dark_mode() else '#ffffff'};
            border-radius: 10px;
            padding: 20px;
        """)
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setAlignment(Qt.AlignLeft)

        title = QLabel("Categories & Budgets")
        title.setFont(QFont("Segoe UI",16,QFont.Bold))
        title.setStyleSheet("color: #d6733a;")
        wrapper_layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(30)

        for i,cat in enumerate(categories):
            cat_name = cat["category_name"]
            color = cat["color"] or "#4caf50"
            spent = cat["spent"] or 0

            circle = QPushButton(f"${spent:.0f}")
            circle.setFixedSize(80,80)
            circle.setStyleSheet(f"""
                background-color: {color};
                border-radius: 40px;
                color: white;
                font-size: 16px;
                font-weight: bold;
            """)
            circle.clicked.connect(lambda _,cat=cat_name: self.open_commitment_form(cat))

            circle_layout = QVBoxLayout(circle)
            amount_lbl = QLabel(f"${spent:.0f}")
            amount_lbl.setAlignment(Qt.AlignCenter)
            amount_lbl.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
            circle_layout.addStretch()
            circle_layout.addWidget(amount_lbl)
            circle_layout.addStretch()

            # Name below circle
            outer_layout = QVBoxLayout()
            outer_layout.setAlignment(Qt.AlignCenter)
            outer_layout.addWidget(circle)

            name_lbl = QLabel(cat_name)
            name_lbl.setAlignment(Qt.AlignCenter)
            name_lbl.setStyleSheet("font-size: 12px; color: #333;")
            outer_layout.addWidget(name_lbl)

            holder = QWidget()
            holder.setLayout(outer_layout)

            grid.addWidget(holder,i // 4,i % 4)

        # Add "+" Button
        add_btn = QPushButton("+")
        add_btn.setFixedSize(80,80)
        add_btn.setStyleSheet("""
            background-color: #007bff;
            border-radius: 40px;
            color: white;
            font-size: 24px;
            font-weight: bold;
        """)

        add_layout = QVBoxLayout()
        add_layout.setAlignment(Qt.AlignCenter)
        add_layout.addWidget(add_btn)
        add_lbl = QLabel("Add")
        add_lbl.setAlignment(Qt.AlignCenter)
        add_lbl.setStyleSheet("font-size: 12px; color: #333;")
        add_layout.addWidget(add_lbl)

        add_holder = QWidget()
        add_holder.setLayout(add_layout)

        grid.addWidget(add_holder,len(categories) // 4,len(categories) % 4)

        wrapper_layout.addLayout(grid)
        layout.addWidget(wrapper)
