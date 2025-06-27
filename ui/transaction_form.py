from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QComboBox, QTextEdit, QCheckBox, QMessageBox
)
from PyQt5.QtCore import Qt
from database.db_manager import fetch_all, fetch_one
from core.transactions import add_txn
from core.currency import convert
import datetime

class TransactionForm(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("add transaction")
        self.setMinimumSize(400, 400)

        self.amount_input = QLineEdit()
        self.type_input = QComboBox()
        self.cat_input = QComboBox()
        self.acc_input = QComboBox()
        self.note_input = QTextEdit()
        self.recurring = QCheckBox("recurring")
        self.save_btn = QPushButton("save")
        self.convert_lbl = QLabel()

        self.init_ui()
        self.load_cats()
        self.load_accs()

    def init_ui(self):
        box = QVBoxLayout()

        self.amount_input.setPlaceholderText("amount e.g. 150.00")
        self.amount_input.textChanged.connect(self.show_converted)
        self.type_input.addItems(["expense", "income"])
        self.note_input.setPlaceholderText("note or desc (opt)")

        box.addWidget(QLabel("amount"))
        box.addWidget(self.amount_input)
        box.addWidget(self.convert_lbl)

        box.addWidget(QLabel("type"))
        box.addWidget(self.type_input)

        box.addWidget(QLabel("category"))
        box.addWidget(self.cat_input)

        box.addWidget(QLabel("account"))
        box.addWidget(self.acc_input)

        box.addWidget(QLabel("description"))
        box.addWidget(self.note_input)

        box.addWidget(self.recurring)
        box.addWidget(self.save_btn)

        self.save_btn.clicked.connect(self.save_txn)
        self.setLayout(box)

    def get_user_currency(self):
        row = fetch_one("select currency from settings where user_id = ?", (self.user_id,))
        return row["currency"] if row else "USD"

    def show_converted(self):
        try:
            amt = float(self.amount_input.text())
            curr = self.get_user_currency()
            result = convert(amt, "USD", curr)
            if result is not None:
                self.convert_lbl.setText(f"= {result} {curr}")
            else:
                self.convert_lbl.setText("")
        except:
            self.convert_lbl.setText("")

    def load_cats(self):
        rows = fetch_all("select category_id, category_name from categories where user_id = ?", (self.user_id,))
        self.cat_input.clear()
        for r in rows:
            self.cat_input.addItem(r["category_name"], r["category_id"])

    def load_accs(self):
        rows = fetch_all("select account_id, bank_name from accounts where user_id = ?", (self.user_id,))
        self.acc_input.clear()
        for r in rows:
            name = r["bank_name"] or f"acc {r['account_id']}"
            self.acc_input.addItem(name, r["account_id"])

    def save_txn(self):
        try:
            amt = float(self.amount_input.text())
            tx_type = self.type_input.currentText()
            cat_id = self.cat_input.currentData()
            acc_id = self.acc_input.currentData()
            note = self.note_input.toPlainText()
            recur = int(self.recurring.isChecked())
            now = datetime.datetime.now()

            add_txn(self.user_id, acc_id, cat_id, amt, tx_type, note, now, recur)

            QMessageBox.information(self, "done", "transaction saved")
            self.close()

        except ValueError:
            QMessageBox.warning(self, "oops", "enter a valid number")
        except Exception as e:
            QMessageBox.critical(self, "error", f"couldn’t save: {e}")
