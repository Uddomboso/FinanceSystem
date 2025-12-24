from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QComboBox, QMessageBox
)
from assets.styles.penny_colors import PennyColors
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
        p = PennyColors.get_palette("light")
        label_style = f"color: {p['text_primary']}; font-size: 13px;"
        input_style = f"""
            QLineEdit, QComboBox {{
                background: {p['surface']};
                color: {p['text_primary']};
                border: 1px solid {p['border']};
                border-radius: 8px;
                padding: 8px 10px;
                selection-background-color: {p['primary']};
            }}
            QLineEdit:focus, QComboBox:focus {{
                border: 1px solid {p['accent']};
            }}
        """
        btn_style = f"""
            QPushButton {{
                background: {p['accent']};
                color: {p['surface']};
                border: none;
                border-radius: 10px;
                padding: 10px 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {PennyColors.GRADIENTS['accent'].split('stop:1 ')[1].rstrip(')')};
            }}
        """

        box = QVBoxLayout()

        amt_label = QLabel("Amount")
        amt_label.setStyleSheet(label_style)
        box.addWidget(amt_label)
        self.amount_input.setStyleSheet(input_style)
        box.addWidget(self.amount_input)

        from_label = QLabel("From Account")
        from_label.setStyleSheet(label_style)
        box.addWidget(from_label)
        self.acc_input.setStyleSheet(input_style)
        box.addWidget(self.acc_input)

        to_label = QLabel("To Category")
        to_label.setStyleSheet(label_style)
        box.addWidget(to_label)
        self.cat_input.setStyleSheet(input_style)
        box.addWidget(self.cat_input)

        note_label = QLabel("Note (optional)")
        note_label.setStyleSheet(label_style)
        box.addWidget(note_label)
        self.note_input.setStyleSheet(input_style)
        box.addWidget(self.note_input)

        self.save_btn.setStyleSheet(btn_style)
        box.addWidget(self.save_btn)
        self.setLayout(box)

        self.save_btn.clicked.connect(self.make_transfer)

    def load_accs(self):
        rows = fetch_all("select account_id, bank_name, account_type from accounts where user_id = ?", (self.user_id,))
        for r in rows:
            bank_name = r["bank_name"] or "Unknown Bank"
            account_type = r["account_type"] or "account"
            # Display format: "Bank Name (Account Type)"
            display_name = f"{bank_name} ({account_type})"
            self.acc_input.addItem(display_name, r["account_id"])

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
