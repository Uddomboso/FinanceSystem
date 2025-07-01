from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QComboBox, QLineEdit, QPushButton, QMessageBox, QProgressBar
)
from core.budget import set_budget, get_spent, get_budget
from database.db_manager import fetch_all, fetch_one
from core.currency import convert

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

    def get_user_currency(self):
        row = fetch_one("select currency from settings where user_id = ?", (self.user_id,))
        return row["currency"] if row else "USD"

    def load_cats(self):
        rows = fetch_all("select category_id, category_name from categories where user_id = ?", (self.user_id,))
        self.cat_select.clear()
        for r in rows:
            self.cat_select.addItem(r["category_name"], r["category_id"])
        if rows:
            self.refresh_stats()

    def get_used_and_limit(self):
        cat_id = self.cat_select.currentData()
        if not cat_id:
            return None,None,None

        # Get spent amount for this category (converted to user currency if needed)
        spent = get_spent(self.user_id,cat_id)  # from core.budget

        # Get budget limit for this category
        budget = get_budget(self.user_id,cat_id)  # from core.budget

        # Get user currency from settings
        curr = self.get_user_currency()

        # Convert spent and budget to user currency if needed
        spent_c = convert(spent,"USD",curr) if spent is not None else 0.0
        budget_c = convert(budget,"USD",curr) if budget is not None else 0.0

        return spent_c,budget_c,curr

    def refresh_stats(self):
        used_c,limit_c,curr = self.get_used_and_limit()

        if used_c is None or limit_c is None:
            self.used_lbl.setText("No budget set")
            self.progress.setValue(0)
            self.status_lbl.setText("no budget set yet")
            return

        curr = curr or "USD"
        self.used_lbl.setText(f"used: {used_c:.2f} / {limit_c:.2f} {curr}")

        if limit_c > 0:
            pct = int((used_c / limit_c) * 100)
            self.progress.setValue(min(pct,100))
            if used_c > limit_c:
                self.status_lbl.setText("you passed the limit")
            else:
                self.status_lbl.setText("you're good so far")
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
