from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QComboBox, QMessageBox, QSpinBox, QCheckBox
)
from PyQt5.QtCore import Qt
from database.db_manager import fetch_all, execute_query

class CommitmentForm(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("Add Monthly Commitment")
        self.setMinimumSize(400, 300)
        self.init_ui()
        self.load_categories()

    def init_ui(self):
        layout = QVBoxLayout()

        self.category_input = QComboBox()
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Enter amount e.g. 100.00")

        self.day_input = QSpinBox()
        self.day_input.setRange(1, 31)
        self.day_input.setPrefix("Day of Month: ")
        self.day_input.setValue(1)

        self.notify_checkbox = QCheckBox("Enable monthly reminders")
        self.notify_checkbox.setChecked(True)

        self.save_btn = QPushButton("Save Commitment")
        self.save_btn.clicked.connect(self.save_commitment)

        layout.addWidget(QLabel("Category"))
        layout.addWidget(self.category_input)
        layout.addWidget(QLabel("Amount"))
        layout.addWidget(self.amount_input)
        layout.addWidget(self.day_input)
        layout.addWidget(self.notify_checkbox)
        layout.addWidget(self.save_btn)

        self.setLayout(layout)

    def load_categories(self):
        rows = fetch_all("SELECT category_id, category_name FROM categories WHERE user_id = ?", (self.user_id,))
        self.category_input.clear()
        for row in rows:
            self.category_input.addItem(row["category_name"], row["category_id"])

    def save_commitment(self):
        try:
            cat_id = self.category_input.currentData()
            amount = float(self.amount_input.text())
            due_day = self.day_input.value()
            notify = 1 if self.notify_checkbox.isChecked() else 0

            execute_query("""
                INSERT INTO category_commitments (user_id, category_id, amount, due_day, notifications_enabled)
                VALUES (?, ?, ?, ?, ?)
            """, (self.user_id, cat_id, amount, due_day, notify))

            QMessageBox.information(self, "Saved", "Commitment saved successfully.")
            self.close()

        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid amount.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save commitment: {e}")
