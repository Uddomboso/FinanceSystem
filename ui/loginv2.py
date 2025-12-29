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
        self.setMinimumSize(1200, 750)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        
        # Brand colors
        self.colors = {
            'primary': '#d6733a',
            'accent': '#ffe22a',
            'dark': '#704b3b',
            'dark_alt': '#b45131',
            'neutral': '#b2b3a3',
            'warm': '#fdbd63',
            'bg_light': '#fffaf5',
            'bg_panel': '#fff3e6',
            'text_primary': '#704b3b',
            'text_secondary': '#8a6d5b',
            'white': '#ffffff',
        }
        
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
        """Initialize the modern UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout with no margins for full-width design
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left panel - Branding with gradient background
        left_panel = self.create_left_panel()
        
        # Right panel - Login form
        right_panel = self.create_right_panel()

        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 1)

    def create_left_panel(self):
        """Create the left branding panel"""
        panel = QFrame()
        panel.setFixedWidth(500)
        
        # Gradient background using stylesheet
        panel.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.colors['bg_panel']},
                    stop:1 {self.colors['bg_light']});
                border: none;
            }}
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(60, 80, 60, 80)
        layout.setSpacing(40)
        layout.setAlignment(Qt.AlignCenter)

        # Logo
        logo_container = QFrame()
        logo_container.setFixedSize(200, 200)
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setAlignment(Qt.AlignCenter)

        logo = QLabel()
        logo_path = os.path.join("logopng.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled = pixmap.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo.setPixmap(scaled)
        else:
            logo.setText("PW")
            logo.setStyleSheet(f"""
                font-size: 72px;
                font-weight: 700;
                color: {self.colors['primary']};
                font-family: 'Segoe UI', 'Inter', sans-serif;
            """)
        logo.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(logo)

        layout.addStretch()
        layout.addWidget(logo_container, alignment=Qt.AlignCenter)
        layout.addStretch()

        return panel

    def create_right_panel(self):
        """Create the right login panel"""
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors['bg_light']};
                border: none;
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Stacked layout for different states
        self.stack = QStackedLayout()
        self.workos_ui = self.make_workos_login_ui()
        self.error_ui = self.make_error_ui()
        
        self.stack.addWidget(self.workos_ui)
        self.stack.addWidget(self.error_ui)

        # Show appropriate panel
        if self.workos_available:
            self.stack.setCurrentIndex(0)
        else:
            self.stack.setCurrentIndex(1)

        layout.addLayout(self.stack)

        return panel

    def make_workos_login_ui(self):
        """Create the main login UI"""
        container = QWidget()
        container.setStyleSheet(f"""
            QWidget {{
                background-color: {self.colors['bg_light']};
            }}
        """)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(80, 100, 80, 100)
        layout.setSpacing(0)

        # Header section
        header_layout = QVBoxLayout()
        header_layout.setSpacing(16)
        header_layout.setAlignment(Qt.AlignTop)

        # Welcome title
        title = QLabel("Welcome")
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet(f"""
            QLabel {{
                font-size: 36px;
                font-weight: 700;
                color: {self.colors['text_primary']};
                font-family: 'Segoe UI', 'Inter', sans-serif;
                letter-spacing: -0.5px;
                margin: 0;
                padding: 0;
                background-color: transparent;
            }}
        """)

        # Subtitle
        subtitle = QLabel("Sign in to continue to your account")
        subtitle.setAlignment(Qt.AlignLeft)
        subtitle.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: 400;
                color: {self.colors['text_secondary']};
                font-family: 'Segoe UI', 'Inter', sans-serif;
                margin-top: 8px;
                background-color: transparent;
            }}
        """)

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_layout.addSpacing(60)

        # Google button with modern styling
        google_btn = QPushButton("  Continue with Google")
        google_btn.setMinimumHeight(64)
        google_btn.setCursor(Qt.PointingHandCursor)
        
        # Modern button styling with shadow and hover effects
        google_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['white']};
                color: {self.colors['text_primary']};
                border: 2px solid #e5e7eb;
                border-radius: 12px;
                font-size: 16px;
                font-weight: 600;
                font-family: 'Segoe UI', 'Inter', sans-serif;
                padding: 0px 32px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {self.colors['bg_light']};
                border-color: {self.colors['primary']};
                border-width: 2px;
            }}
            QPushButton:pressed {{
                background-color: {self.colors['bg_panel']};
                border-color: {self.colors['dark_alt']};
            }}
        """)
        google_btn.clicked.connect(self.login_with_workos)

        # Spacing and alignment
        layout.addLayout(header_layout)
        layout.addStretch()
        layout.addWidget(google_btn)
        layout.addStretch()

        return container

    def make_error_ui(self):
        """Create error UI when WorkOS is not configured"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(80, 100, 80, 100)
        layout.setSpacing(0)

        # Header
        title = QLabel("WorkOS Not Configured")
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet(f"""
            font-size: 36px;
            font-weight: 700;
            color: {self.colors['text_primary']};
            font-family: 'Segoe UI', 'Inter', sans-serif;
            letter-spacing: -0.5px;
        """)

        subtitle = QLabel("OAuth authentication is not available")
        subtitle.setAlignment(Qt.AlignLeft)
        subtitle.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 400;
            color: {self.colors['text_secondary']};
            font-family: 'Segoe UI', 'Inter', sans-serif;
            margin-top: 8px;
        """)

        # Error message box
        error_box = QFrame()
        error_box.setStyleSheet("""
            QFrame {
                background-color: #fef2f2;
                border: 1px solid #fecaca;
                border-radius: 12px;
                padding: 24px;
                margin-top: 32px;
            }
        """)
        error_layout = QVBoxLayout(error_box)
        error_layout.setSpacing(12)

        error_text = QLabel(
            "To enable Google OAuth login, add the following to your .env file:\n\n"
            "WORKOS_API_KEY=your_api_key\n"
            "WORKOS_CLIENT_ID=your_client_id\n"
            "WORKOS_REDIRECT_URL=http://localhost:8000/authenticate\n\n"
            "After adding these, restart the application."
        )
        error_text.setWordWrap(True)
        error_text.setStyleSheet("""
            color: #991b1b;
            font-size: 14px;
            font-family: 'Segoe UI', 'Inter', sans-serif;
            line-height: 1.6;
        """)
        error_layout.addWidget(error_text)

        # Retry button
        retry_btn = QPushButton("Check Again")
        retry_btn.setMinimumHeight(56)
        retry_btn.setCursor(Qt.PointingHandCursor)
        retry_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['primary']};
                color: {self.colors['white']};
                border: none;
                border-radius: 12px;
                font-size: 16px;
                font-weight: 600;
                font-family: 'Segoe UI', 'Inter', sans-serif;
                padding: 0px 24px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['dark_alt']};
            }}
            QPushButton:pressed {{
                background-color: #a0402a;
            }}
        """)
        retry_btn.clicked.connect(self.retry_workos_check)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(32)
        layout.addWidget(error_box)
        layout.addStretch()
        layout.addWidget(retry_btn)
        layout.addStretch()

        return container

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
        
        #  Hardcoded admin if .env admin does nit work (fallback)
        hardcoded_admins = [
            "suzanudomboso@gmail.com",
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
