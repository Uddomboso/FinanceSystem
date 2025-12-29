from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QStackedLayout, QMessageBox, QFrame
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
import bcrypt
import os

from database.db_manager import insert_user, fetch_one, execute_query


class LoginWindow(QWidget):
    login_successful = pyqtSignal(int, str, str)  # user_id, username, role
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login or Sign Up")
        self.setMinimumSize(1000, 700)
        self.setStyleSheet("""
            font-family: Segoe UI;
            font-size: 16px;
            background-color: #fffaf5;
        """)
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(40)

        # Left panel - Branding
        left_frame = QFrame()
        left_frame.setFixedWidth(400)
        left_frame.setStyleSheet("""
            QFrame {
                background-color: #fff3e6;
                border-radius: 20px;
                padding: 40px;
            }
        """)

        left_layout = QVBoxLayout(left_frame)
        left_layout.setAlignment(Qt.AlignCenter)
        left_layout.setSpacing(30)

        # Logo
        logo = QLabel()
        logo_path = os.path.join("logopng.png")
        if os.path.exists(logo_path):
            logo.setPixmap(QPixmap(logo_path).scaledToWidth(250, Qt.SmoothTransformation))
        else:
            logo.setText("APP LOGO")
            logo.setStyleSheet("font-size: 24px; font-weight: bold; color: #704b3b;")
        logo.setAlignment(Qt.AlignCenter)

        # Welcome text
        welcome_text = QLabel("Welcome to Our Platform")
        welcome_text.setAlignment(Qt.AlignCenter)
        welcome_text.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #704b3b;
            margin-top: 20px;
        """)

        description = QLabel("Sign in to your account or create a new one to get started with our services.")
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet("color: #8a6d5b; font-size: 15px; margin-top: 10px;")

        left_layout.addWidget(logo)
        left_layout.addWidget(welcome_text)
        left_layout.addWidget(description)
        left_layout.addStretch()

        # Right panel - Login/Signup forms
        right_frame = QFrame()
        right_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 20px;
                padding: 0px;
            }
        """)

        self.stack = QStackedLayout(right_frame)
        self.login_ui = self.make_login_ui()
        self.signup_ui = self.make_signup_ui()
        self.stack.addWidget(self.login_ui)
        self.stack.addWidget(self.signup_ui)

        main_layout.addWidget(left_frame)
        main_layout.addWidget(right_frame, 1)

    def make_login_ui(self):
        container = QVBoxLayout()
        container.setContentsMargins(50, 60, 50, 60)
        container.setSpacing(25)

        # Header
        header = QLabel("Welcome Back")
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #704b3b;")
        header.setAlignment(Qt.AlignCenter)

        subheader = QLabel("Sign in to continue to your account")
        subheader.setStyleSheet("color: #8a6d5b; font-size: 16px;")
        subheader.setAlignment(Qt.AlignCenter)

        # Form
        form_layout = QVBoxLayout()
        form_layout.setSpacing(20)

        email_label = QLabel("Email Address")
        email_label.setStyleSheet("font-weight: bold; color: #704b3b; margin-bottom: 5px;")

        self.email = QLineEdit()
        self.email.setPlaceholderText("Enter your email")
        self.email.setStyleSheet("""
            QLineEdit {
                padding: 12px 15px;
                border: 2px solid #e6d5c8;
                border-radius: 10px;
                font-size: 15px;
            }
            QLineEdit:focus {
                border-color: #d6733a;
            }
        """)

        password_label = QLabel("Password")
        password_label.setStyleSheet("font-weight: bold; color: #704b3b; margin-bottom: 5px;")

        self.password = QLineEdit()
        self.password.setPlaceholderText("Enter your password")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setStyleSheet("""
            QLineEdit {
                padding: 12px 15px;
                border: 2px solid #e6d5c8;
                border-radius: 10px;
                font-size: 15px;
            }
            QLineEdit:focus {
                border-color: #d6733a;
            }
        """)

        form_layout.addWidget(email_label)
        form_layout.addWidget(self.email)
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password)

        # Login button
        login_btn = QPushButton("Sign In")
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #d6733a;
                color: white;
                padding: 14px;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c26634;
            }
            QPushButton:pressed {
                background-color: #a8592d;
            }
        """)
        login_btn.clicked.connect(self.login)

        # Switch to signup
        switch_layout = QHBoxLayout()
        switch_layout.setAlignment(Qt.AlignCenter)

        switch_label = QLabel("Don't have an account?")
        switch_label.setStyleSheet("color: #8a6d5b;")

        switch_btn = QPushButton("Sign Up")
        switch_btn.setFlat(True)
        switch_btn.setStyleSheet("""
            QPushButton {
                color: #d6733a;
                font-weight: bold;
                text-decoration: none;
                border: none;
                padding: 5px 10px;
            }
            QPushButton:hover {
                color: #c26634;
                text-decoration: underline;
            }
        """)
        switch_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        switch_layout.addWidget(switch_label)
        switch_layout.addWidget(switch_btn)

        container.addWidget(header)
        container.addWidget(subheader)
        container.addSpacing(20)
        container.addLayout(form_layout)
        container.addWidget(login_btn)
        container.addSpacing(10)
        container.addLayout(switch_layout)
        container.addStretch()

        wrap = QWidget()
        wrap.setLayout(container)
        return wrap

    def make_signup_ui(self):
        container = QVBoxLayout()
        container.setContentsMargins(50, 60, 50, 60)
        container.setSpacing(25)

        # Header
        header = QLabel("Create Account")
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #704b3b;")
        header.setAlignment(Qt.AlignCenter)

        subheader = QLabel("Sign up to get started with our platform")
        subheader.setStyleSheet("color: #8a6d5b; font-size: 16px;")
        subheader.setAlignment(Qt.AlignCenter)

        # Form
        form_layout = QVBoxLayout()
        form_layout.setSpacing(20)

        email_label = QLabel("Email Address")
        email_label.setStyleSheet("font-weight: bold; color: #704b3b; margin-bottom: 5px;")

        self.new_email = QLineEdit()
        self.new_email.setPlaceholderText("Enter your email")
        self.new_email.setStyleSheet("""
            QLineEdit {
                padding: 12px 15px;
                border: 2px solid #e6d5c8;
                border-radius: 10px;
                font-size: 15px;
            }
            QLineEdit:focus {
                border-color: #d6733a;
            }
        """)

        username_label = QLabel("Username")
        username_label.setStyleSheet("font-weight: bold; color: #704b3b; margin-bottom: 5px;")

        self.new_username = QLineEdit()
        self.new_username.setPlaceholderText("Choose a username")
        self.new_username.setStyleSheet("""
            QLineEdit {
                padding: 12px 15px;
                border: 2px solid #e6d5c8;
                border-radius: 10px;
                font-size: 15px;
            }
            QLineEdit:focus {
                border-color: #d6733a;
            }
        """)

        password_label = QLabel("Password")
        password_label.setStyleSheet("font-weight: bold; color: #704b3b; margin-bottom: 5px;")

        self.new_password = QLineEdit()
        self.new_password.setPlaceholderText("Create a password")
        self.new_password.setEchoMode(QLineEdit.Password)
        self.new_password.setStyleSheet("""
            QLineEdit {
                padding: 12px 15px;
                border: 2px solid #e6d5c8;
                border-radius: 10px;
                font-size: 15px;
            }
            QLineEdit:focus {
                border-color: #d6733a;
            }
        """)

        form_layout.addWidget(email_label)
        form_layout.addWidget(self.new_email)
        form_layout.addWidget(username_label)
        form_layout.addWidget(self.new_username)
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.new_password)

        # Signup button
        signup_btn = QPushButton("Create Account")
        signup_btn.setStyleSheet("""
            QPushButton {
                background-color: #d6733a;
                color: white;
                padding: 14px;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c26634;
            }
            QPushButton:pressed {
                background-color: #a8592d;
            }
        """)
        signup_btn.clicked.connect(self.signup)

        # Switch to login
        switch_layout = QHBoxLayout()
        switch_layout.setAlignment(Qt.AlignCenter)

        switch_label = QLabel("Already have an account?")
        switch_label.setStyleSheet("color: #8a6d5b;")

        switch_btn = QPushButton("Sign In")
        switch_btn.setFlat(True)
        switch_btn.setStyleSheet("""
            QPushButton {
                color: #d6733a;
                font-weight: bold;
                text-decoration: none;
                border: none;
                padding: 5px 10px;
            }
            QPushButton:hover {
                color: #c26634;
                text-decoration: underline;
            }
        """)
        switch_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        switch_layout.addWidget(switch_label)
        switch_layout.addWidget(switch_btn)

        container.addWidget(header)
        container.addWidget(subheader)
        container.addSpacing(20)
        container.addLayout(form_layout)
        container.addWidget(signup_btn)
        container.addSpacing(10)
        container.addLayout(switch_layout)
        container.addStretch()

        wrap = QWidget()
        wrap.setLayout(container)
        return wrap

    def login(self):
        email = self.email.text().strip()
        password = self.password.text().encode()

        if not email or not password:
            QMessageBox.warning(self, "Error", "Please fill in all fields.")
            return

        user = fetch_one("SELECT * FROM users WHERE email = ?", (email,))
        if user:
            if bcrypt.checkpw(password, user["password_hash"].encode()):
                # Update last login
                execute_query(
                    "UPDATE users SET last_login = datetime('now') WHERE user_id = ?",
                    (user["user_id"],),
                    commit=True
                )
                QMessageBox.information(self, "Success", "Login successful!")
                self.hide()
                # Import dashboard only after successful login
                self.open_dashboard(user["user_id"], user["username"], user.get("role", "End User"))
            else:
                QMessageBox.warning(self, "Failed", "Incorrect password. Please try again.")
        else:
            QMessageBox.warning(self, "Failed", "No account found with this email.")

    def signup(self):
        email = self.new_email.text().strip()
        username = self.new_username.text().strip()
        password = self.new_password.text().encode()

        if not email or not username or not password:
            QMessageBox.warning(self, "Error", "Please fill in all fields.")
            return

        # Check if email or username already exists
        existing_email = fetch_one("SELECT user_id FROM users WHERE email = ?", (email,))
        if existing_email:
            QMessageBox.warning(self, "Error", "An account with this email already exists.")
            return

        existing_username = fetch_one("SELECT user_id FROM users WHERE username = ?", (username,))
        if existing_username:
            QMessageBox.warning(self, "Error", "This username is already taken.")
            return

        hashed = bcrypt.hashpw(password, bcrypt.gensalt()).decode()
        try:
            # Create user
            insert_user(email, username, hashed, role="End User")

            # Fetch the newly created user
            user = fetch_one("SELECT user_id, username, role FROM users WHERE email = ?", (email,))
            if not user:
                QMessageBox.critical(self, "Error", "Failed to retrieve user after signup.")
                return

            user_id = user["user_id"]
            username = user["username"]
            role = user.get("role", "End User")

            # Create default categories and settings
            self.create_default_categories(user_id)
            self.create_default_settings(user_id)

            QMessageBox.information(self, "Success", "Account created successfully!")
            self.hide()
            # Import dashboard only after successful signup
            self.open_dashboard(user_id, username, role)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not create account: {str(e)}")

    def create_default_categories(self, user_id):
        """Create default categories for new user with error handling"""
        defaults = [
            ("Savings", "#3cba54"),
            ("Bills", "#db3236"),
            ("Spending", "#4885ed")
        ]
        for name, color in defaults:
            try:
                exists = fetch_one(
                    "SELECT category_id FROM categories WHERE user_id = ? AND category_name = ?",
                    (user_id, name)
                )
                if not exists:
                    execute_query(
                        "INSERT INTO categories (user_id, category_name, color, is_default) VALUES (?, ?, ?, 1)",
                        (user_id, name, color),
                        commit=True
                    )
            except Exception as e:
                print(f"Error creating category {name}: {e}")

    def create_default_settings(self, user_id):
        """Create default settings for new user"""
        try:
            existing = fetch_one("SELECT user_id FROM settings WHERE user_id = ?", (user_id,))
            if not existing:
                execute_query(
                    "INSERT INTO settings (user_id, currency, dark_mode, notifications_enabled) VALUES (?, 'USD', 0, 1)",
                    (user_id,),
                    commit=True
                )
        except Exception as e:
            print(f"Error creating default settings: {e}")

    def open_dashboard(self, user_id, username, role):
        """Open dashboard after successful login/signup - lazy import"""
        try:
            from ui.dashboard_main import DashboardMain
            self.dash = DashboardMain(user_id=user_id, username=username, role=role, show_tutorial=False)
            self.dash.show()
        except ImportError as e:
            QMessageBox.critical(self, "Error", f"Failed to load dashboard: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open dashboard: {e}")
