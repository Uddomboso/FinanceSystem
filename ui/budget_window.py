from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QComboBox, QLineEdit, QPushButton, QMessageBox, QProgressBar
)
from core.budget import set_budget, get_spent, get_budget
from database.db_manager import fetch_all

class BudgetWindow(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("budgets")
        self.setMinimumSize(400, 300)

        self.cat_select = QComboBox()
        self.amount_input = QLineEdit()
        self.save_btn = QPushButton("set budget")
        self.progress = QProgressBar()

        self.status_lbl = QLabel()
        self.amount_lbl = QLabel()
        self.used_lbl = QLabel()

        self.init_ui()
        self.load_cats()

    def init_ui(self):
        box = QVBoxLayout()

        self.cat_select.currentIndexChanged.connect(self.refresh_stats)
        self.amount_input.setPlaceholderText("enter budget amount")

        box.addWidget(QLabel("category"))
        box.addWidget(self.cat_select)

        box.addWidget(QLabel("budget limit"))
        box.addWidget(self.amount_input)

        box.addWidget(self.save_btn)

        box.addWidget(QLabel("usage"))
        box.addWidget(self.progress)
        box.addWidget(self.used_lbl)
        box.addWidget(self.status_lbl)

        self.save_btn.clicked.connect(self.save_budget)

        self.setLayout(box)

    def load_cats(self):
        rows = fetch_all("select category_id, category_name from categories where user_id = ?", (self.user_id,))
        self.cat_select.clear()
        for r in rows:
            self.cat_select.addItem(r["category_name"], r["category_id"])

        if rows:
            self.refresh_stats()

    def refresh_stats(self):
        cat_id = self.cat_select.currentData()
        if not cat_id:
            return

        used = get_spent(self.user_id, cat_id)
        limit = get_budget(self.user_id, cat_id)

        self.used_lbl.setText(f"used: ${used:.2f} / ${limit:.2f}")

        if limit > 0:
            pct = int((used / limit) * 100)
            self.progress.setValue(min(pct, 100))
            if used > limit:
                self.status_lbl.setText("you passed the limit ")
            else:
                self.status_lbl.setText("you're good so far ")
        else:
            self.progress.setValue(0)
            self.status_lbl.setText("no budget set yet")

    def save_budget(self):
        try:
            amt = float(self.amount_input.text())
            cat_id = self.cat_select.currentData()
            set_budget(self.user_id, cat_id, amt)
            QMessageBox.information(self, "done", "budget updated")
            self.refresh_stats()
        except ValueError:
            QMessageBox.warning(self, "error", "enter a valid number")
