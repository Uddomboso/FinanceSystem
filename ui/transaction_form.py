from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QComboBox, QHBoxLayout, QTextEdit, QCheckBox, QMessageBox
)
from PyQt5.QtCore import Qt
from database.db_manager import fetch_all, execute_query
import datetime


class TransactionForm(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("Add Transaction")
        self.setMinimumSize(400, 400)

        self.amount_input = QLineEdit()
        self.type_input = QComboBox()
        self.category_input = QComboBox()
        self.account_input = QComboBox()
        self.description_input = QTextEdit()
        self.recurring_input = QCheckBox("Recurring")

        self.submit_button = QPushButton("Save Transaction")

        self.setup_ui()
        self.load_categories()
        self.load_accounts()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.amount_input.setPlaceholderText("Amount (e.g., 120.00)")
        self.type_input.addItems(["expense", "income"])
        self.description_input.setPlaceholderText("Description (optional)")

        layout.addWidget(QLabel("Amount"))
        layout.addWidget(self.amount_input)

        layout.addWidget(QLabel("Type"))
        layout.addWidget(self.type_input)

        layout.addWidget(QLabel("Category"))
        layout.addWidget(self.category_input)

        layout.addWidget(QLabel("Account"))
        layout.addWidget(self.account_input)

        layout.addWidget(QLabel("Description"))
        layout.addWidget(self.description_input)

        layout.addWidget(self.recurring_input)
        layout.addWidget(self.submit_button)

        self.submit_button.clicked.connect(self.save_transaction)
        self.setLayout(layout)

    def load_categories(self):
        rows = fetch_all("SELECT category_id, category_name FROM categories WHERE user_id = ?", (self.user_id,))
        self.category_input.clear()
        for row in rows:
            self.category_input.addItem(row["category_name"], row["category_id"])

    def load_accounts(self):
        rows = fetch_all("SELECT account_id, bank_name FROM accounts WHERE user_id = ?", (self.user_id,))
        self.account_input.clear()
        for row in rows:
            display_name = row["bank_name"] or f"Account {row['account_id']}"
            self.account_input.addItem(display_name, row["account_id"])

    def save_transaction(self):
        try:
            amount = float(self.amount_input.text())
            trans_type = self.type_input.currentText()
            category_id = self.category_input.currentData()
            account_id = self.account_input.currentData()
            description = self.description_input.toPlainText()
            is_recurring = int(self.recurring_input.isChecked())
            date = datetime.datetime.now()

            query = '''
                INSERT INTO transactions (
                    user_id, account_id, category_id, amount,
                    transaction_type, description, date, is_recurring
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                self.user_id, account_id, category_id,
                amount, trans_type, description, date, is_recurring
            )
            execute_query(query, params, commit=True)

            QMessageBox.information(self, "Success", "Transaction saved.")
            self.close()

        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid amount.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save transaction: {e}")
