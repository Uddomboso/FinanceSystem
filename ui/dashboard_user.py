from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt

from ui.transaction_form import TransactionForm
from ui.charts_window import ChartsWindow
from ui.budget_window import BudgetWindow
from ui.settings_window import SettingsWindow
from ui.ai_suggestions_window import AiSuggestionsWindow
from ui.bank_connect_window import BankConnectWindow


class UserDashboard(QWidget):
    def __init__(self, username, user_id):
        super().__init__()
        self.username = username
        self.user_id = user_id

        self.setWindowTitle("pennywise dashboard")
        self.setMinimumSize(500, 400)

        # main buttons
        self.welcome = QLabel()
        self.txn_btn = QPushButton("transactions")
        self.budget_btn = QPushButton("budget")
        self.reports_btn = QPushButton("reports")
        self.settings_btn = QPushButton("settings")
        self.ai_btn = QPushButton("ai stuff")
        self.logout_btn = QPushButton("logout")

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.welcome.setText(f"hey {self.username} 👋")
        self.welcome.setAlignment(Qt.AlignCenter)
        self.welcome.setStyleSheet("font-size: 20px; margin-bottom: 20px;")
        self.bank_btn = QPushButton("link bank")

        # horizontal row for buttons
        row = QHBoxLayout()
        btns = [
            self.txn_btn,
            self.budget_btn,
            self.reports_btn,
            self.settings_btn,
            self.ai_btn,
            self.bank_btn,
            self.logout_btn
        ]

        for b in btns:
            b.setFixedHeight(40)
            row.addWidget(b)

        # hook up clicks
        self.txn_btn.clicked.connect(self.open_txn_form)
        self.budget_btn.clicked.connect(self.open_budget)
        self.reports_btn.clicked.connect(self.open_charts)
        self.settings_btn.clicked.connect(self.open_settings)
        self.ai_btn.clicked.connect(self.open_ai)
        self.logout_btn.clicked.connect(self.logout)
        self.bank_btn.clicked.connect(self.open_bank)

        layout.addWidget(self.welcome)
        layout.addLayout(row)
        self.setLayout(layout)

    def open_txn_form(self):
        self.txn_form = TransactionForm(self.user_id)
        self.txn_form.show()

    def open_budget(self):
        self.budget = BudgetWindow(self.user_id)
        self.budget.show()

    def open_charts(self):
        self.charts = ChartsWindow(self.user_id)
        self.charts.show()

    def open_settings(self):
        self.settings = SettingsWindow(self.user_id)
        self.settings.show()

    def open_ai(self):
        self.ai = AiSuggestionsWindow(self.user_id)
        self.ai.show()

    def logout(self):
        QMessageBox.information(self, "bye", "logged out")
        self.close()

    def open_bank(self):
        self.bank = BankConnectWindow(self.user_id)
        self.bank.show()
