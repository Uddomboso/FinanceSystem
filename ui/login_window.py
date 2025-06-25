from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt
import bcrypt
from database.db_manager import insert_user, fetch_one
from ui.dashboard_user import UserDashboard


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PennyWise - Login")
        self.setFixedSize(300, 300)

        # Define instance attributes up front
        self.label = QLabel("Login or Sign Up")
        self.email_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.login_button = QPushButton("Login")
        self.signup_button = QPushButton("Sign Up")

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.label.setAlignment(Qt.AlignCenter)

        self.email_input.setPlaceholderText("Email")
        self.username_input.setPlaceholderText("Username")
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)

        self.login_button.clicked.connect(self.login)
        self.signup_button.clicked.connect(self.signup)

        layout.addWidget(self.label)
        layout.addWidget(self.email_input)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        layout.addWidget(self.signup_button)

        self.setLayout(layout)

    def login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().encode()

        user = fetch_one("SELECT * FROM users WHERE email = ?", (email,))
        if user:
            stored_hash = user["password_hash"]
            if bcrypt.checkpw(password, stored_hash.encode()):
                QMessageBox.information(self, "Login Successful", f"Welcome {user['username']}!")
                self.hide()
                self.dashboard = UserDashboard(user["username"])
                self.dashboard.show()
            else:
                QMessageBox.warning(self, "Error", "Invalid password.")
        else:
            QMessageBox.warning(self, "Error", "User not found.")

    def signup(self):
        email = self.email_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text().encode()

        if not email or not username or not password:
            QMessageBox.warning(self, "Error", "Please fill all fields.")
            return

        hashed = bcrypt.hashpw(password, bcrypt.gensalt()).decode()
        try:
            insert_user(email, username, hashed, role="End User")
            QMessageBox.information(self, "Account Created", "You can now log in.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create account: {e}")
