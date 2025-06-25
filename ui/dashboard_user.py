from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt
from ui.transaction_form import TransactionForm

self.transactions_btn.clicked.connect(self.open_transaction_form)

def open_transaction_form(self):
    self.trans_window = TransactionForm(user_id=self.user_id)  # You'll need to pass user_id from LoginWindow
    self.trans_window.show()



class UserDashboard(QWidget):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.setWindowTitle("PennyWise - User Dashboard")
        self.setMinimumSize(500, 400)

        # Declare instance attributes here
        self.welcome_label = QLabel()
        self.transactions_btn = QPushButton("Transactions")
        self.budget_btn = QPushButton("Budget")
        self.reports_btn = QPushButton("Reports")
        self.settings_btn = QPushButton("Settings")
        self.ai_btn = QPushButton("AI Suggestions")
        self.logout_btn = QPushButton("Logout")

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.welcome_label.setText(f"Welcome, {self.username} 👋")
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.welcome_label.setStyleSheet("font-size: 20px; margin-bottom: 20px;")

        buttons_layout = QHBoxLayout()
        buttons = [
            self.transactions_btn,
            self.budget_btn,
            self.reports_btn,
            self.settings_btn,
            self.ai_btn,
            self.logout_btn
        ]

        for btn in buttons:
            btn.setFixedHeight(40)
            buttons_layout.addWidget(btn)

        self.logout_btn.clicked.connect(self.logout)

        layout.addWidget(self.welcome_label)
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def logout(self):
        QMessageBox.information(self, "Logout", "You have been logged out.")
        self.close()
