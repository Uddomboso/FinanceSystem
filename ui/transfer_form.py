from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QComboBox, QMessageBox
)
from core.transfer import transfer_to_category
from database.db_manager import fetch_all

class TransferForm(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("Transfer to Category")
        self.setMinimumSize(400, 300)

        self.amount_input = QLineEdit()
        self.acc_input = QComboBox()
        self.cat_input = QComboBox()
        self.note_input = QLineEdit()
        self.save_btn = QPushButton("Transfer")

        self.load_accs()
        self.load_cats()
        self.init_ui()

    def init_ui(self):
        box = QVBoxLayout()
        box.addWidget(QLabel("Amount"))
        box.addWidget(self.amount_input)

        box.addWidget(QLabel("From Account"))
        box.addWidget(self.acc_input)

        box.addWidget(QLabel("To Category"))
        box.addWidget(self.cat_input)

        box.addWidget(QLabel("Note (optional)"))
        box.addWidget(self.note_input)

        box.addWidget(self.save_btn)
        self.setLayout(box)

        self.save_btn.clicked.connect(self.make_transfer)

    def load_accs(self):
        rows = fetch_all("select account_id, bank_name from accounts where user_id = ?", (self.user_id,))
        for r in rows:
            self.acc_input.addItem(r["bank_name"], r["account_id"])

    def load_cats(self):
        rows = fetch_all("select category_id, category_name from categories where user_id = ?", (self.user_id,))
        for r in rows:
            self.cat_input.addItem(r["category_name"], r["category_id"])

    def make_transfer(self):
        try:
            amount = float(self.amount_input.text())
            acc_id = self.acc_input.currentData()
            cat_id = self.cat_input.currentData()
            note = self.note_input.text()

            transfer_to_category(self.user_id, acc_id, cat_id, amount, note)
            QMessageBox.information(self, "Success", "Transfer recorded successfully!")
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to transfer: {e}")
