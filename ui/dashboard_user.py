from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt
from ui.transaction_form import TransactionForm
from ui.charts_window import ChartsWindow
from ui.budget_window import BudgetWindow
from ui.settings_window import SettingsWindow

class UserDashboard(QWidget):
    def __init__(self, username, user_id):
        super().__init__()
        self.username = username
        self.user_id = user_id

        self.setWindowTitle("pennywise dashboard")
        self.setMinimumSize(500, 400)

        # buttons
        self.welcome = QLabel()
        self.txn_btn = QPushButton("transactions")
        self.budget_btn = QPushButton("budget")
        self.reports_btn = QPushButton("reports")
        self.settings_btn = QPushButton("settings")
        self.ai_btn = QPushButton("ai stuff")
        self.logout_btn = QPushButton("logout")
        self.settings_btn.clicked.connect(self.open_settings)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.welcome.setText(f"hey {self.username} 👋")
        self.welcome.setAlignment(Qt.AlignCenter)
        self.welcome.setStyleSheet("font-size: 20px; margin-bottom: 20px;")

        row = QHBoxLayout()
        btns = [
            self.txn_btn,
            self.budget_btn,
            self.reports_btn,
            self.settings_btn,
            self.ai_btn,
            self.logout_btn
        ]

        for b in btns:
            b.setFixedHeight(40)
            row.addWidget(b)

        self.txn_btn.clicked.connect(self.open_txn_form)
        self.budget_btn.clicked.connect(self.open_budget)
        self.reports_btn.clicked.connect(self.open_charts)
        self.logout_btn.clicked.connect(self.logout)

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

    def logout(self):
        QMessageBox.information(self, "bye", "logged out")
        self.close()
    def open_settings(self):
        self.settings = SettingsWindow(self.user_id)
        self.settings.show()
