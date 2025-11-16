# ui/loginv2.py - NEW FILE
from PyQt5.QtWidgets import (
    QWidget,QLabel,QLineEdit,QPushButton,QVBoxLayout,QHBoxLayout,
    QStackedLayout,QMessageBox,QFrame,QMainWindow
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt,pyqtSignal
import bcrypt
import os

from database.db_manager import insert_user,fetch_one,execute_query


class LoginWindowV2(QMainWindow):
    login_successful = pyqtSignal(int,str)  # user_id, username

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PennyWise - Login")
        self.setMinimumSize(1000,700)
        self.setStyleSheet("""
            font-family: Segoe UI;
            font-size: 16px;
            background-color: #fffaf5; /* Light Beige Background */
        """)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(40,40,40,40)
        main_layout.setSpacing(40)

        # Left panel - Branding
        left_frame = QFrame()
        left_frame.setFixedWidth(400)
        left_frame.setStyleSheet("""
            QFrame {
                background-color: #fff3e6; /* Light Cream Background */
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
            logo.setPixmap(QPixmap(logo_path).scaledToWidth(250,Qt.SmoothTransformation))
        else:
            logo.setText("PENNYWISE")
            logo.setStyleSheet("font-size: 24px; font-weight: bold; color: #704b3b;")
        logo.setAlignment(Qt.AlignCenter)

        # Welcome text
        welcome_text = QLabel("Welcome to PennyWise")
        welcome_text.setAlignment(Qt.AlignCenter)
        welcome_text.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #704b3b;
            margin-top: 20px;
        """)

        description = QLabel("Sign in to your account or create a new one to manage your finances.")
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
        main_layout.addWidget(right_frame,1)

    def make_login_ui(self):
        container = QVBoxLayout()
        container.setContentsMargins(50,60,50,60)
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
                border: 2px solid #f0e8e4; /* Muted Input Border */
                border-radius: 10px;
                font-size: 15px;
            }
            QLineEdit:focus {
                border-color: #e89574; /* Primary Accent Focus */
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
                border: 2px solid #f0e8e4; /* Muted Input Border */
                border-radius: 10px;
                font-size: 15px;
            }
            QLineEdit:focus {
                border-color: #e89574; /* Primary Accent Focus */
            }
        """)

        # Add widgets to form
        form_layout.addWidget(email_label)
        form_layout.addWidget(self.email)
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password)

        # Login button
        login_btn = QPushButton("Sign In")
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #e89574; /* Soft Terracotta Button */
                color: white;
                padding: 14px;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d4886b; /* Darker Hover */
            }
            QPushButton:pressed {
                background-color: #c27d61;
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
                color: #e89574; /* Soft Terracotta Link */
                font-weight: bold;
                text-decoration: none;
                border: none;
                padding: 5px 10px;
            }
            QPushButton:hover {
                color: #d4886b;
                text-decoration: underline;
            }
        """)
        switch_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        switch_layout.addWidget(switch_label)
        switch_layout.addWidget(switch_btn)

        # Add all to main container
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
        container.setContentsMargins(50,60,50,60)
        container.setSpacing(25)

        # Header
        header = QLabel("Create Account")
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #704b3b;")
        header.setAlignment(Qt.AlignCenter)

        subheader = QLabel("Sign up to get started with PennyWise")
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
                border: 2px solid #f0e8e4; /* Muted Input Border */
                border-radius: 10px;
                font-size: 15px;
            }
            QLineEdit:focus {
                border-color: #e89574; /* Primary Accent Focus */
            }
        """)

        username_label = QLabel("Username")
        username_label.setStyleSheet("font-weight: bold; color: #704b3b; margin-bottom: 5px;")

        self.new_username = QLineEdit()
        self.new_username.setPlaceholderText("Choose a username")
        self.new_username.setStyleSheet("""
            QLineEdit {
                padding: 12px 15px;
                border: 2px solid #f0e8e4; /* Muted Input Border */
                border-radius: 10px;
                font-size: 15px;
            }
            QLineEdit:focus {
                border-color: #e89574; /* Primary Accent Focus */
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
                border: 2px solid #f0e8e4; /* Muted Input Border */
                border-radius: 10px;
                font-size: 15px;
            }
            QLineEdit:focus {
                border-color: #e89574; /* Primary Accent Focus */
            }
        """)

        # Add widgets to form
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
                background-color: #e89574; /* Soft Terracotta Button */
                color: white;
                padding: 14px;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d4886b; /* Darker Hover */
            }
            QPushButton:pressed {
                background-color: #c27d61;
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
                color: #e89574; /* Soft Terracotta Link */
                font-weight: bold;
                text-decoration: none;
                border: none;
                padding: 5px 10px;
            }
            QPushButton:hover {
                color: #d4886b;
                text-decoration: underline;
            }
        """)
        switch_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        switch_layout.addWidget(switch_label)
        switch_layout.addWidget(switch_btn)

        # Add all to main container
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

    # ... (rest of the class methods: login, signup, create_default_categories, initialize_user_data remain unchanged)

    def login(self):
        email = self.email.text().strip()
        password = self.password.text().encode()

        user = fetch_one("SELECT * FROM users WHERE email = ?", (email,))
        if user:
            if bcrypt.checkpw(password, user["password_hash"].encode()):
                QMessageBox.information(self, "Success", "Login successful!")
                
                # Initialize user data and emit signal
                self.initialize_user_data(user["user_id"], user["username"])
                self.login_successful.emit(user["user_id"], user["username"])
                self.hide()
                
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

        hashed = bcrypt.hashpw(password, bcrypt.gensalt()).decode()
        try:
            # Create user
            insert_user(email, username, hashed, role="End User")

            # Fetch the newly created user's ID
            user = fetch_one("SELECT user_id FROM users WHERE email = ?", (email,))
            if not user:
                QMessageBox.critical(self, "Error", "Failed to retrieve user after signup.")
                return

            user_id = user["user_id"]

            # Create default categories for the new user
            self.create_default_categories(user_id)
            
            # Initialize user settings
            self.initialize_user_data(user_id, username)

            QMessageBox.information(self, "Success", "Account created successfully!")

            # Emit signal for auto-login
            self.login_successful.emit(user_id, username)
            self.hide()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not create account: {e}")

    def create_default_categories(self, user_id):
        """Automatically create default categories for a new user."""
        try:
            defaults = [
                ("Bills", "#EF4444", 0),
                ("Groceries", "#10B981", 0),
                ("Entertainment", "#8B5CF6", 0),
                ("Transportation", "#3B82F6", 0),
                ("Dining Out", "#F59E0B", 0),
                ("Shopping", "#EC4899", 0),
                ("Healthcare", "#DC2626", 0),
                ("Income", "#059669", 0),
                ("Savings", "#06B6D4", 0)
            ]
            for name, color, budget in defaults:
                exists = fetch_one(
                    "SELECT category_id FROM categories WHERE user_id = ? AND category_name = ?",
                    (user_id, name),
                )
                if not exists:
                    execute_query(
                        "INSERT INTO categories (user_id, category_name, color, budget_amount, is_default) VALUES (?, ?, ?, ?, 1)",
                        (user_id, name, color, budget),
                        commit=True,
                    )
        except Exception as e:
            print("⚠️ Error creating default categories:", e)

    def initialize_user_data(self, user_id, username):
        """Initialize user data after login/signup"""
        try:
            # Setup default settings if they don't exist
            existing_settings = fetch_one("SELECT user_id FROM settings WHERE user_id = ?", (user_id,))
            if not existing_settings:
                execute_query("""
                    INSERT INTO settings (user_id, currency, dark_mode, notifications_enabled)
                    VALUES (?, 'USD', 0, 1)
                """, (user_id,), commit=True)
                print(f"✅ Created default settings for {username}")
        except Exception as e:
            print(f"⚠️ Error initializing user data: {e}")