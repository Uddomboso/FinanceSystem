from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QStackedLayout, QMessageBox, QFrame
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt
import bcrypt
import os

from database.db_manager import insert_user, fetch_one
from ui.dashboard_user import UserDashboard

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PennyWise - Login or Sign Up")
        self.setMinimumSize(1204, 1204)
        self.setStyleSheet("font-family: Segoe UI; font-size: 20px;")
        self.init_ui()

    def init_ui(self):
        main = QHBoxLayout(self)

        # left panel
        left = QVBoxLayout()
        logo = QLabel()
        logo_path = os.path.join("logopng.png")
        logo.setPixmap(QPixmap(logo_path).scaledToWidth(200, Qt.SmoothTransformation))
        logo.setAlignment(Qt.AlignCenter)

        brand = QLabel("PennyWise")
        brand.setAlignment(Qt.AlignCenter)
        brand.setStyleSheet("font-size: 28px; font-weight: bold; color: #d6733a;")

        tagline = QLabel("because every coin counts")
        tagline.setAlignment(Qt.AlignCenter)
        tagline.setStyleSheet("font-size: 14px; color: gray;")

        left.addStretch()
        left.addWidget(logo)
        left.addWidget(brand)
        left.addWidget(tagline)
        left.addStretch()

        frame = QFrame()
        frame.setLayout(left)
        frame.setStyleSheet("background-color: #fff3e6; border-radius: 12px; padding: 20px;")
        frame.setFixedWidth(300)

        # right panel
        self.stack = QStackedLayout()
        self.login_ui = self.make_login_ui()
        self.signup_ui = self.make_signup_ui()
        self.stack.addWidget(self.login_ui)
        self.stack.addWidget(self.signup_ui)

        main.addWidget(frame)
        main.addLayout(self.stack)

    def make_login_ui(self):
        box = QVBoxLayout()
        title = QLabel("Login")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")

        self.email = QLineEdit()
        self.email.setPlaceholderText("email")

        self.password = QLineEdit()
        self.password.setPlaceholderText("password")
        self.password.setEchoMode(QLineEdit.Password)

        login_btn = QPushButton("login")
        login_btn.setStyleSheet("background-color: #d6733a; color: white;")
        login_btn.clicked.connect(self.login)

        switch = QPushButton("no account? sign up")
        switch.setFlat(True)
        switch.setStyleSheet("color: #704b3b; text-decoration: underline;")
        switch.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        for w in [title, self.email, self.password, login_btn, switch]:
            box.addWidget(w)

        box.addStretch()
        wrap = QWidget()
        wrap.setLayout(box)
        return wrap

    def make_signup_ui(self):
        box = QVBoxLayout()
        title = QLabel("Sign Up")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")

        self.new_email = QLineEdit()
        self.new_email.setPlaceholderText("email")

        self.new_username = QLineEdit()
        self.new_username.setPlaceholderText("username")

        self.new_password = QLineEdit()
        self.new_password.setPlaceholderText("password")
        self.new_password.setEchoMode(QLineEdit.Password)

        signup_btn = QPushButton("create account")
        signup_btn.setStyleSheet("background-color: #d6733a; color: white;")
        signup_btn.clicked.connect(self.signup)

        switch = QPushButton("already signed up? login")
        switch.setFlat(True)
        switch.setStyleSheet("color: #704b3b; text-decoration: underline;")
        switch.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        for w in [title, self.new_email, self.new_username, self.new_password, signup_btn, switch]:
            box.addWidget(w)

        box.addStretch()
        wrap = QWidget()
        wrap.setLayout(box)
        return wrap

    def login(self):
        email = self.email.text().strip()
        password = self.password.text().encode()

        user = fetch_one("select * from users where email = ?", (email,))
        if user:
            if bcrypt.checkpw(password, user["password_hash"].encode()):
                QMessageBox.information(self, "ok", "login success")
                self.hide()
                self.dash = UserDashboard(user["username"], user["user_id"])
                self.dash.show()
            else:
                QMessageBox.warning(self, "fail", "wrong password")
        else:
            QMessageBox.warning(self, "fail", "no account found")

    def signup(self):
        email = self.new_email.text().strip()
        username = self.new_username.text().strip()
        password = self.new_password.text().encode()

        if not email or not username or not password:
            QMessageBox.warning(self, "error", "fill all fields")
            return

        hashed = bcrypt.hashpw(password, bcrypt.gensalt()).decode()
        try:
            insert_user(email, username, hashed, role="End User")
            QMessageBox.information(self, "done", "account created")
            self.stack.setCurrentIndex(0)
        except Exception as e:
            QMessageBox.critical(self, "fail", f"error: {e}")
