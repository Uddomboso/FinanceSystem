
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QComboBox, QTextEdit, QCheckBox, QMessageBox, QDateEdit
)
from PyQt5.QtCore import Qt, QDate
from database.db_manager import fetch_all, fetch_one
from core.transactions import add_txn
from core.currency import convert
import datetime

class TransactionForm(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("Add Transaction")
        self.setMinimumSize(400, 500)
   
        self.amount_input = QLineEdit()
        self.type_input = QComboBox()
        self.cat_input = QComboBox()
        self.acc_input = QComboBox()
        self.note_input = QTextEdit()
        self.date_input = QDateEdit(QDate.currentDate())
        self.recurring = QCheckBox("Recurring Transaction")
        self.save_btn = QPushButton("Save Transaction")
        self.convert_lbl = QLabel()

        self.init_ui()
        self.load_cats()
        self.load_accs()

    def init_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Amount"))
        self.amount_input.setPlaceholderText("e.g. 150.00")
        self.amount_input.textChanged.connect(self.show_converted)
        layout.addWidget(self.amount_input)
        layout.addWidget(self.convert_lbl)

        layout.addWidget(QLabel("Type"))
        self.type_input.addItems(["Expense", "Income", "Transfer"])
        layout.addWidget(self.type_input)

        layout.addWidget(QLabel("Category"))
        layout.addWidget(self.cat_input)

        layout.addWidget(QLabel("Account"))
        layout.addWidget(self.acc_input)

        layout.addWidget(QLabel("Date"))
        self.date_input.setCalendarPopup(True)
        layout.addWidget(self.date_input)

        layout.addWidget(QLabel("Description"))
        self.note_input.setPlaceholderText("Optional description")
        self.note_input.setMaximumHeight(100)
        layout.addWidget(self.note_input)

        layout.addWidget(self.recurring)

        self.save_btn.clicked.connect(self.save_txn)
        layout.addWidget(self.save_btn)

        self.setLayout(layout)

    def get_user_currency(self):
        row = fetch_one("SELECT currency FROM settings WHERE user_id = ?", (self.user_id,))
        return row["currency"] if row else "USD"

    def show_converted(self):
        try:
            amt = float(self.amount_input.text())
            curr = self.get_user_currency()
            result = convert(amt, "USD", curr)
            if result is not None:
                self.convert_lbl.setText(f"≈ {result:.2f} {curr}")
            else:
                self.convert_lbl.setText("")
        except ValueError:
            self.convert_lbl.setText("")

    def load_cats(self):
        rows = fetch_all(
            "SELECT category_id, category_name FROM categories WHERE user_id = ?", 
            (self.user_id,)
        )
        self.cat_input.clear()
        self.cat_input.addItem("Select Category", None)
        for r in rows:
            self.cat_input.addItem(r["category_name"], r["category_id"])

    def load_accs(self):
        rows = fetch_all(
            "SELECT account_id, bank_name FROM accounts WHERE user_id = ?", 
            (self.user_id,)
        )
        self.acc_input.clear()
        self.acc_input.addItem("Select Account", None)
        for r in rows:
            name = r["bank_name"] or f"Account {r['account_id']}"
            self.acc_input.addItem(name, r["account_id"])

    def save_txn(self):
        try:

            amount = float(self.amount_input.text())
            tx_type = self.type_input.currentText().lower()
            cat_id = self.cat_input.currentData()
            acc_id = self.acc_input.currentData()
            note = self.note_input.toPlainText()
            recur = int(self.recurring.isChecked())
            date = self.date_input.date().toString(Qt.ISODate)
            
            if not acc_id:
                raise ValueError("Please select an account")
            if not cat_id and tx_type != "transfer":
                raise ValueError("Please select a category")

            add_txn(
                user_id=self.user_id,
                acc_id=acc_id,
                cat_id=cat_id,
                amt=amount,
                tx_type=tx_type,
                note=note,
                date=date,
                recurring=recur
            )

            QMessageBox.information(self, "Success", "Transaction saved successfully")
            self.close()

        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save transaction: {str(e)}")
