from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QStackedLayout, QFrame, QMainWindow, QMessageBox, QLineEdit
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal, QThread
import os

from database.db_manager import fetch_one, execute_query
from core.workos_auth import get_workos_authenticator
from core.session_manager import get_session_manager
from core.logger import logger


class LoginWindowV2(QMainWindow):
    login_successful = pyqtSignal(int, str, str)  # user_id, username, role

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PennyWise - Login")
        self.setMinimumSize(1000, 700)
        self.setStyleSheet("""
            font-family: Segoe UI;
            font-size: 16px;
            background-color: #fffaf5;
        """)
        self.workos_available = self.check_workos_config()
        self.init_ui()

    def check_workos_config(self):
        """Check if WorkOS is properly configured"""
        try:
            from core.config import Config
            print("\n🔍 loginv2.py: Checking WorkOS configuration:")
            print(f"   Config.WORKOS_API_KEY: {'SET' if Config.WORKOS_API_KEY else 'NOT SET'}")
            print(f"   Config.WORKOS_CLIENT_ID: {'SET' if Config.WORKOS_CLIENT_ID else 'NOT SET'}")
            print(f"   Config.WORKOS_REDIRECT_URL: {Config.WORKOS_REDIRECT_URL}")
            
            authenticator = get_workos_authenticator()
            is_configured = authenticator.is_configured()
            print(f"   authenticator.is_configured(): {is_configured}")
            print(f"   authenticator.api_key: {'SET' if authenticator.api_key else 'NOT SET'}")
            print(f"   authenticator.client_id: {'SET' if authenticator.client_id else 'NOT SET'}")
            print()
            return is_configured
        except Exception as e:
            logger.warning(f"WorkOS check failed: {e}")
            print(f"   ❌ Error checking WorkOS: {e}\n")
            return False

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(40)

        # Left branding panel
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

        logo = QLabel()
        logo_path = os.path.join("logopng.png")
        if os.path.exists(logo_path):
            logo.setPixmap(QPixmap(logo_path).scaledToWidth(250, Qt.SmoothTransformation))
        else:
            logo.setText("PENNYWISE")
            logo.setStyleSheet("font-size: 24px; font-weight: bold; color: #704b3b;")
        logo.setAlignment(Qt.AlignCenter)

        welcome = QLabel("Welcome to PennyWise")
        welcome.setAlignment(Qt.AlignCenter)
        welcome.setStyleSheet("font-size: 22px; font-weight: bold; color: #704b3b; margin-top: 20px;")

        desc = QLabel("Sign in with Google to manage your finances.")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #8a6d5b; font-size: 15px; margin-top: 10px;")

        left_layout.addWidget(logo)
        left_layout.addWidget(welcome)
        left_layout.addWidget(desc)
        left_layout.addStretch()

        # Right login panel with stacked layout
        right_frame = QFrame()
        right_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 20px;
                padding: 0px;
            }
        """)
        right_frame_layout = QVBoxLayout(right_frame)
        right_frame_layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedLayout()
        self.workos_ui = self.make_workos_login_ui()
        self.error_ui = self.make_error_ui()
        self.stack.addWidget(self.workos_ui)
        self.stack.addWidget(self.error_ui)

        # Show appropriate panel based on WorkOS availability
        if self.workos_available:
            self.stack.setCurrentIndex(0)
        else:
            self.stack.setCurrentIndex(1)

        right_frame_layout.addLayout(self.stack)
        main_layout.addWidget(left_frame)
        main_layout.addWidget(right_frame, 1)

    def make_workos_login_ui(self):
        container = QVBoxLayout()
        container.setContentsMargins(50, 60, 50, 60)
        container.setSpacing(30)

        header = QLabel("Welcome Back")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #704b3b;")

        subheader = QLabel("Sign in with Google to continue")
        subheader.setAlignment(Qt.AlignCenter)
        subheader.setStyleSheet("color: #8a6d5b; font-size: 16px;")

        container.addWidget(header)
        container.addWidget(subheader)
        container.addSpacing(40)

        # Google OAuth login button
        workos_btn = QPushButton("Continue with Google")
        workos_btn.setMinimumHeight(60)
        workos_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                padding: 18px;
                border: none;
                border-radius: 10px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
            QPushButton:pressed {
                background-color: #4338ca;
            }
        """)
        workos_btn.clicked.connect(self.login_with_workos)
        container.addWidget(workos_btn)

        container.addStretch()
        wrap = QWidget()
        wrap.setLayout(container)
        return wrap

    def make_error_ui(self):
        container = QVBoxLayout()
        container.setContentsMargins(50, 60, 50, 60)
        container.setSpacing(30)

        header = QLabel("WorkOS Not Configured")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #704b3b;")

        error_msg = QLabel(
            "WorkOS authentication is not available.\n\n"
            "To enable WorkOS login, add the following to your .env file:\n\n"
            "WORKOS_API_KEY=your_api_key\n"
            "WORKOS_CLIENT_ID=your_client_id\n"
            "WORKOS_REDIRECT_URL=http://localhost:8000/authenticate\n\n"
            "After adding these, restart the application."
        )
        error_msg.setWordWrap(True)
        error_msg.setAlignment(Qt.AlignCenter)
        error_msg.setStyleSheet("""
            color: #dc3545;
            font-size: 14px;
            padding: 20px;
            background-color: #f8d7da;
            border-radius: 10px;
            border: 1px solid #f5c6cb;
        """)

        retry_btn = QPushButton("Check Again")
        retry_btn.setMinimumHeight(50)
        retry_btn.setStyleSheet("""
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
        retry_btn.clicked.connect(self.retry_workos_check)

        container.addWidget(header)
        container.addWidget(error_msg)
        container.addWidget(retry_btn)
        container.addStretch()

        wrap = QWidget()
        wrap.setLayout(container)
        return wrap

    def retry_workos_check(self):
        """Retry checking WorkOS configuration"""
        self.workos_available = self.check_workos_config()
        if self.workos_available:
            self.stack.setCurrentIndex(0)
            QMessageBox.information(self, "Success", "WorkOS is now configured!")
        else:
            QMessageBox.warning(self, "Still Not Configured", "WorkOS keys are still missing. Please check your .env file.")

    def login_with_workos(self):
        """Handle WorkOS authentication"""
        authenticator = get_workos_authenticator()
        if not authenticator.is_configured():
            QMessageBox.warning(
                self,
                "WorkOS Not Configured",
                "WorkOS authentication is not available.\n\n"
                "Please add WORKOS_API_KEY, WORKOS_CLIENT_ID, and WORKOS_REDIRECT_URL to your .env file."
            )
            self.stack.setCurrentIndex(1)
            return

        QMessageBox.information(self, "WorkOS Login", "Opening browser for authentication...")

        class AuthWorker(QThread):
            finished = pyqtSignal(dict)
            error = pyqtSignal(str)

            def run(self):
                try:
                    user_info = authenticator.authenticate()
                    if user_info:
                        self.finished.emit(user_info)
                    else:
                        self.error.emit("Authentication failed")
                except Exception as e:
                    self.error.emit(str(e))

        self.auth_worker = AuthWorker()
        self.auth_worker.finished.connect(self._on_auth_success)
        self.auth_worker.error.connect(self._on_auth_error)
        self.auth_worker.start()

    def _on_auth_success(self, user_info):
        """Handle successful authentication on main thread"""
        email = user_info.get("email")
        token = user_info.get("token")
        username = user_info.get("username") or email.split("@")[0]
        
        # Determine role: check database first, then email whitelist
        role = self._determine_user_role(email)

        # Check if user exists in database
        user = fetch_one("SELECT * FROM users WHERE email = ?", (email,))
        if user:
            user_id = user["user_id"]
            # Update role if it changed (e.g., admin email added to whitelist)
            execute_query(
                "UPDATE users SET role = ?, last_login = datetime('now') WHERE user_id = ?",
                (role, user_id),
                commit=True
            )
        else:
            execute_query(
                "INSERT INTO users (email, username, password_hash, role, last_login) VALUES (?, ?, ?, ?, datetime('now'))",
                (email, username, "", role),
                commit=True
            )
            user = fetch_one("SELECT * FROM users WHERE email = ?", (email,))
            if not user:
                QMessageBox.critical(self, "Error", "Failed to create user account.")
                return
            user_id = user["user_id"]
            self.create_default_categories(user_id)
            self.create_default_settings(user_id)

        session_manager = get_session_manager()
        session_manager.create_session(user_id=user_id, token=token, user_info=user_info, role=role)

        self.login_successful.emit(user_id, username, role)
        self.hide()
        logger.info(f"WorkOS login successful: {user_id}, role: {role}")

    def _on_auth_error(self, error_msg):
        """Handle authentication error on main thread"""
        logger.error(f"WorkOS login error: {error_msg}")
        QMessageBox.warning(self, "Authentication Failed", f"WorkOS login failed: {error_msg}")

    def create_default_categories(self, user_id):
        """Create default categories for new user with error handling"""
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
            try:
                exists = fetch_one(
                    "SELECT category_id FROM categories WHERE user_id = ? AND category_name = ?",
                    (user_id, name)
                )
                if not exists:
                    execute_query(
                        "INSERT INTO categories (user_id, category_name, color, budget_amount, is_default) VALUES (?, ?, ?, ?, 1)",
                        (user_id, name, color, budget),
                        commit=True
                    )
            except Exception as e:
                logger.error(f"Error creating category {name}: {e}")

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
            logger.error(f"Error creating default settings: {e}")
    
    def _determine_user_role(self, email):
        """
        Determine user role after successful OAuth login.
        Priority: Database role > Email whitelist > Default 'End User'
        """
        # Option 1: Check database role first (if user exists)
        user = fetch_one("SELECT role FROM users WHERE email = ?", (email,))
        if user:
            db_role = user["role"]
            # Only accept valid admin roles from database
            if db_role and db_role in ["Admin", "Technical Manager", "General Manager"]:
                return db_role
        
        # Option 2: Check email whitelist (from config or hardcoded)
        admin_emails = self._get_admin_email_whitelist()
        if email.lower() in admin_emails:
            return "Admin"
        
        # Default: End User
        return "End User"
    
    def _get_admin_email_whitelist(self):
        """Get list of admin emails (from config or hardcoded)"""
        # Option A: From config (add ADMIN_EMAILS to .env as comma-separated)
        from core.config import Config
        admin_emails_env = os.getenv("ADMIN_EMAILS", "")
        if admin_emails_env:
            return [e.strip().lower() for e in admin_emails_env.split(",") if e.strip()]
        
        # Option B: Hardcoded whitelist (fallback)
        hardcoded_admins = [
            # Add admin emails here, e.g.:
            # "admin@example.com",
            # "manager@example.com",
        ]
        return [e.lower() for e in hardcoded_admins]

    def open_dashboard(self, user_id, username, role):
        """Open dashboard after successful login - lazy import"""
        try:
            from ui.dashboard_main import DashboardMain
            self.dash = DashboardMain(user_id=user_id, username=username, role=role, show_tutorial=False)
            self.dash.show()
        except ImportError as e:
            QMessageBox.critical(self, "Error", f"Failed to import dashboard: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open dashboard: {e}")
