from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QComboBox, QTextEdit, QCheckBox, QMessageBox, QHBoxLayout,
    QScrollArea, QFrame
)
from PyQt5.QtCore import Qt
from database.db_manager import fetch_all, fetch_one
from core.transactions import add_txn
from core.currency import convert
import datetime
from ui.transfer_form import TransferForm


class TransactionForm(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("Transactions & Categories")
        self.setMinimumSize(500, 500)

        self.transactions_view = QWidget()
        self.categories_view = QWidget()
        self.stack_layout = QVBoxLayout()
        self.container = QVBoxLayout()

        self.init_toggle_buttons()
        self.init_transaction_form()
        self.init_categories_view()

        self.stack_layout.addWidget(self.transactions_view)
        self.setLayout(self.container)
        self.container.addLayout(self.toggle_btn_layout)
        self.container.addLayout(self.stack_layout)

    def init_toggle_buttons(self):
        self.toggle_btn_layout = QHBoxLayout()
        self.txn_btn = QPushButton("Transactions View")
        self.cat_btn = QPushButton("Categories View")
        self.txn_btn.clicked.connect(self.show_transaction_form)
        self.cat_btn.clicked.connect(self.show_category_view)

        self.toggle_btn_layout.addWidget(self.txn_btn)
        self.toggle_btn_layout.addWidget(self.cat_btn)

    # View 1: Transactions
    def init_transaction_form(self):
        layout = QVBoxLayout()
        self.amount_input = QLineEdit()
        self.type_input = QComboBox()
        self.cat_input = QComboBox()
        self.acc_input = QComboBox()
        self.note_input = QTextEdit()
        self.recurring = QCheckBox("Recurring")
        self.save_btn = QPushButton("Save")
        self.convert_lbl = QLabel()

        self.amount_input.setPlaceholderText("amount e.g. 150.00")
        self.amount_input.textChanged.connect(self.show_converted)
        self.type_input.addItems(["expense", "income"])
        self.note_input.setPlaceholderText("note or desc (opt)")

        layout.addWidget(QLabel("Amount"))
        layout.addWidget(self.amount_input)
        layout.addWidget(self.convert_lbl)

        layout.addWidget(QLabel("Type"))
        layout.addWidget(self.type_input)

        layout.addWidget(QLabel("Category"))
        layout.addWidget(self.cat_input)

        layout.addWidget(QLabel("Account"))
        layout.addWidget(self.acc_input)

        layout.addWidget(QLabel("Description"))
        layout.addWidget(self.note_input)

        layout.addWidget(self.recurring)
        layout.addWidget(self.save_btn)

        self.save_btn.clicked.connect(self.save_txn)

        self.transactions_view.setLayout(layout)
        self.load_cats()
        self.load_accs()

    def show_transaction_form(self):
        self.stack_layout.removeWidget(self.categories_view)
        self.categories_view.setVisible(False)
        self.stack_layout.addWidget(self.transactions_view)
        self.transactions_view.setVisible(True)

    def show_category_view(self):
        self.stack_layout.removeWidget(self.transactions_view)
        self.transactions_view.setVisible(False)
        self.stack_layout.addWidget(self.categories_view)
        self.categories_view.setVisible(True)

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

            QMessageBox.information(self, "Done", "Transaction saved")
            self.close()
        except ValueError:
            QMessageBox.warning(self, "Oops", "Enter a valid number")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Couldn’t save: {e}")

    # View 2: Categories Grid
    def init_categories_view(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        vbox = QVBoxLayout()
        categories = fetch_all("SELECT * FROM categories WHERE user_id = ?", (self.user_id,))

        for cat in categories:
            frame = QFrame()
            frame.setStyleSheet("border: 1px solid #ccc; padding: 10px; margin-bottom: 10px;")
            layout = QHBoxLayout()

            name = QLabel(cat["category_name"])
            name.setStyleSheet("font-weight: bold; font-size: 14px;")
            layout.addWidget(name)

            if cat["budget_amount"]:
                budget = QLabel(f"Budget: {cat['budget_amount']:.2f}")
                layout.addWidget(budget)

            transfer_btn = QPushButton("Transfer")
            transfer_btn.clicked.connect(lambda _, cid=cat["category_id"]: self.open_transfer(cid))
            layout.addWidget(transfer_btn)

            frame.setLayout(layout)
            vbox.addWidget(frame)

        content.setLayout(vbox)
        scroll.setWidget(content)
        self.categories_view = scroll

    def open_transfer(self, category_id):
        form = TransferForm(self.user_id)
        # You could pre-select the category here if you want
        form.cat_input.setCurrentIndex(
            next((i for i in range(form.cat_input.count()) if form.cat_input.itemData(i) == category_id), 0)
        )
        form.show()
