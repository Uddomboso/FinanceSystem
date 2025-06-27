from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QMessageBox, QListWidget
)
from core.plaid_api import create_link_token, get_mock_accounts
from database.db_manager import execute_query

class BankConnectWindow(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("connect bank")
        self.setMinimumSize(400, 300)

        self.status = QLabel("click below to simulate linking a bank acc")
        self.connect_btn = QPushButton("link sandbox acc")
        self.account_list = QListWidget()

        self.connect_btn.clicked.connect(self.mock_link)

        box = QVBoxLayout()
        box.addWidget(self.status)
        box.addWidget(self.connect_btn)
        box.addWidget(QLabel("linked accounts"))
        box.addWidget(self.account_list)

        self.setLayout(box)

    def mock_link(self):
        # fake the linking by showing demo accounts
        self.status.setText("getting sandbox accs...")
        data = get_mock_accounts(self.user_id)

        if not data:
            QMessageBox.warning(self, "fail", "couldn't get accounts")
            return

        self.account_list.clear()
        for acc in data:
            display = f"{acc['bank_name']} - {acc['account_type']} (${acc['balance']})"
            self.account_list.addItem(display)

        self.status.setText("mock accs linked successfully ✅")

        for acc in data:
            display = f"{acc['bank_name']} - {acc['account_type']} (${acc['balance']})"
            self.account_list.addItem(display)

            # save to db
            q = '''
            insert into accounts (user_id, account_type, bank_name, currency, plaid_token, last_sync)
            values (?, ?, ?, ?, ?, ?)
            '''
            p = (
                self.user_id,
                acc["type"],
                acc["name"],
                acc["currency"],
                acc["plaid_token"],
                acc["last_sync"]
            )
            execute_query(q,p,commit=True)
