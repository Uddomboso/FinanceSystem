from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QComboBox, QMessageBox, QSpinBox, QCheckBox
)
from PyQt5.QtCore import Qt
from database.db_manager import fetch_all, fetch_one, execute_query

class CommitmentForm(QDialog):  # hanged from QWidget
    def __init__(self, user_id, category_name=None):
        super().__init__()
        self.user_id = user_id
        self.category_name = category_name
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

        self.notify_checkbox = QCheckBox("Enable monthly reminders (global)")
        self.notify_checkbox.setChecked(self.get_notification_setting())

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

    def get_notification_setting(self):
        setting = fetch_one("SELECT notifications_enabled FROM settings WHERE user_id = ?", (self.user_id,))
        return setting and setting["notifications_enabled"] == 1

    def load_categories(self):
        rows = fetch_all("SELECT category_id, category_name FROM categories WHERE user_id = ?", (self.user_id,))
        self.category_input.clear()
        for row in rows:
            self.category_input.addItem(row["category_name"], row["category_id"])

        if self.category_name:
            index = self.category_input.findText(self.category_name, Qt.MatchFixedString)
            if index >= 0:
                self.category_input.setCurrentIndex(index)
                self.category_input.setEnabled(False)

    def save_commitment(self):
        try:
            cat_id = self.category_input.currentData()
            amount = float(self.amount_input.text())
            due_day = self.day_input.value()
            notify = 1 if self.notify_checkbox.isChecked() else 0

            execute_query("""
                INSERT INTO category_commitments (user_id, category_id, amount, due_day)
                VALUES (?, ?, ?, ?)
            """, (self.user_id, cat_id, amount, due_day))

            execute_query("""
                UPDATE settings SET notifications_enabled = ? WHERE user_id = ?
            """, (notify, self.user_id))

            QMessageBox.information(self, "Saved", "Commitment saved successfully.")
            self.accept()  # ✅ instead of self.close() for QDialog
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid amount.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save commitment: {e}")
