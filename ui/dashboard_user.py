from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QStackedWidget, QFrame, QComboBox, QSizePolicy, QScrollArea
)
from PyQt5.QtGui import QPixmap, QFont, QIcon
from PyQt5.QtCore import Qt, QSize
import qtawesome as qta
from datetime import datetime

from ui.transaction_form import TransactionForm
from ui.budget_window import BudgetWindow
from ui.charts_window import ChartsWindow
from ui.settings_window import SettingsWindow
from ui.ai_suggestions_window import AISuggestions
from ui.bank_connect_window import BankConnectWindow
from database.db_manager import fetch_all, fetch_one
from core.transactions import get_total_by_type
from core.currency import convert

class UserDashboard(QMainWindow):
    def __init__(self, username, user_id):
        super().__init__()
        self.username = username
        self.user_id = user_id

        self.setWindowTitle("PennyWise | Dashboard")
        self.setMinimumSize(1440, 900)
        self.setStyleSheet("background-color: #f8f9fa;")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.nav_buttons = {}

        self.init_sidebar()
        self.init_pages()
        self.show_dashboard()

    def init_sidebar(self):
        sidebar = QVBoxLayout()
        sidebar.setAlignment(Qt.AlignTop)
        sidebar.setSpacing(20)
        sidebar.setContentsMargins(0, 20, 0, 20)

        # for pennywise logo
        logo = QLabel()
        pixmap = QPixmap("logopng.png")
        pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo.setPixmap(pixmap)
        logo.setAlignment(Qt.AlignCenter)
        sidebar.addWidget(logo)

        # side bar nabigations
        nav_items = [
            ("Dashboard", "fa5s.tachometer-alt", self.show_dashboard),
            ("Transactions", "fa5s.exchange-alt", self.show_transactions),
            ("Budget", "fa5s.money-bill-wave", self.show_budget),
            ("Reports", "fa5s.chart-bar", self.show_reports),
            ("Settings", "fa5s.cog", self.show_settings),
            ("AI Tips", "fa5s.lightbulb", self.show_ai),
            ("Link Bank", "fa5s.university", self.show_bank)
        ]

        for text, icon_name, func in nav_items:
            icon = qta.icon(icon_name, color="#ffe22a")
            btn = QPushButton(icon, f"  {text}")
            btn.setFont(QFont("Segoe UI", 14))
            btn.setStyleSheet(self.default_btn_style())
            btn.setIconSize(QSize(24, 24))
            btn.clicked.connect(func)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.nav_buttons[text] = btn
            sidebar.addWidget(btn)

        sidebar.addStretch()

        # user
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
        self.page_bank = BankConnectWindow(self.user_id, self)  # Pass self as parent

        self.stack.addWidget(self.page_dashboard)
        self.stack.addWidget(self.page_transactions)
        self.stack.addWidget(self.page_budget)
        self.stack.addWidget(self.page_reports)
        self.stack.addWidget(self.page_settings)
        self.stack.addWidget(self.page_ai)
        self.stack.addWidget(self.page_bank)

        self.main_layout.addWidget(self.stack)

    def build_dashboard(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(30)

        # header
        header = QLabel(f"Welcome back, {self.username} 👋")
        header.setFont(QFont("Segoe UI", 32))
        header.setStyleSheet("color: #d6733a;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # date
        date_label = QLabel(datetime.now().strftime("%A, %B %d, %Y"))
        date_label.setFont(QFont("Segoe UI", 14))
        date_label.setAlignment(Qt.AlignCenter)
        date_label.setStyleSheet("color: #6c757d;")
        layout.addWidget(date_label)

        #finance overview
        self.update_financial_overview(layout)

        # recent activity
        self.add_recent_activity(layout)

        container.setLayout(layout)
        scroll.setWidget(container)
        return scroll

    def update_financial_overview(self, layout):
        # financial data
        totals = get_total_by_type(self.user_id)
        income = next((t["total"] for t in totals if t["transaction_type"] == "income"), 0)
        expense = next((t["total"] for t in totals if t["transaction_type"] == "expense"), 0)
        balance = income - expense

        # user currency
        user_currency = fetch_one("SELECT currency FROM settings WHERE user_id = ?", (self.user_id,))
        currency = user_currency["currency"] if user_currency else "USD"

        # convert amounts 
        if currency != "USD":
            income = convert(income, "USD", currency) or income
            expense = convert(expense, "USD", currency) or expense
            balance = convert(balance, "USD", currency) or balance

        # overview 
        overview_frame = QFrame()
        overview_frame.setStyleSheet("""
            background-color: white;
            border-radius: 10px;
            padding: 20px;
        """)
        overview_layout = QHBoxLayout(overview_frame)

        # balance
        balance_card = self.create_finance_card(
            "Total Balance", 
            f"{currency} {balance:,.2f}", 
            "#4CAF50" if balance >= 0 else "#F44336"
        )
        
        #income
        income_card = self.create_finance_card(
            "Total Income", 
            f"{currency} {income:,.2f}", 
            "#2196F3"
        )
        
        # expense
        expense_card = self.create_finance_card(
            "Total Expenses", 
            f"{currency} {expense:,.2f}", 
            "#FF9800"
        )

        overview_layout.addWidget(balance_card)
        overview_layout.addWidget(income_card)
        overview_layout.addWidget(expense_card)
        layout.addWidget(overview_frame)

    def create_finance_card(self, title, value, color):
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

    def add_recent_activity(self, layout):
        # recent transactions
        transactions = fetch_all("""
            SELECT t.*, c.category_name, a.bank_name 
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.category_id
            LEFT JOIN accounts a ON t.account_id = a.account_id
            WHERE t.user_id = ?
            ORDER BY t.date DESC
            LIMIT 5
        """, (self.user_id,))

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

    def create_transaction_widget(self, txn):
        widget = QFrame()
        widget.setStyleSheet("""
            border-bottom: 1px solid #e9ecef;
            padding: 10px 0;
        """)
        layout = QHBoxLayout(widget)

        # Transaction icon
        icon = qta.icon(
            "fa5s.arrow-up" if txn["transaction_type"] == "expense" else "fa5s.arrow-down",
            color="#dc3545" if txn["transaction_type"] == "expense" else "#28a745"
        )
        icon_label = QLabel()
        icon_label.setPixmap(icon.pixmap(24, 24))
        layout.addWidget(icon_label)

        # transaction details
        details = QVBoxLayout()
        details.setSpacing(5)

        desc = QLabel(txn["description"] or "No description")
        desc.setStyleSheet("font-weight: bold;")

        meta = QLabel(f"{txn['category_name'] or 'Uncategorized'} • {txn['bank_name'] or 'No account'}")
        meta.setStyleSheet("color: #6c757d; font-size: 12px;")

        details.addWidget(desc)
        details.addWidget(meta)
        layout.addLayout(details)

        # amount and date
        right = QVBoxLayout()
        right.setSpacing(5)
        right.setAlignment(Qt.AlignRight)

        amount = QLabel(f"{txn['amount']:.2f}")
        amount.setStyleSheet(f"""
            font-weight: bold;
            color: {'#dc3545' if txn['transaction_type'] == 'expense' else '#28a745'};
        """)

        date = QLabel(txn["date"].split()[0] if isinstance(txn["date"], str) else txn["date"].strftime("%Y-%m-%d"))
        date.setStyleSheet("color: #6c757d; font-size: 12px;")

        right.addWidget(amount)
        right.addWidget(date)
        layout.addLayout(right)

        return widget

    def update_dashboard(self):
        """Refresh dashboard data"""
        self.page_dashboard = self.build_dashboard()
        self.stack.removeWidget(self.stack.widget(0))
        self.stack.insertWidget(0, self.page_dashboard)
        self.stack.setCurrentIndex(0)

    # navigation methods remain the same as before
    def highlight_nav(self, active_text):
        for text, btn in self.nav_buttons.items():
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
