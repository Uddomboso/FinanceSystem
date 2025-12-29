# app_main.py - Load .env BEFORE any imports that use Config
import sys
import os
from pathlib import Path

# Load .env file FIRST, before any other imports
script_dir = Path(__file__).parent.absolute()
env_path = script_dir / ".env"

if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_path)
    print(f"✅ app_main.py: Loaded .env from {env_path}")
else:
    print(f"⚠️  app_main.py: .env not found at {env_path}, trying current directory")
    from dotenv import load_dotenv
    load_dotenv()

# Verify keys are loaded before importing Config
print("🔍 app_main.py: Checking WorkOS keys before imports:")
print(f"   WORKOS_API_KEY: {'SET' if os.getenv('WORKOS_API_KEY') else 'NOT SET'}")
print(f"   WORKOS_CLIENT_ID: {'SET' if os.getenv('WORKOS_CLIENT_ID') else 'NOT SET'}")
print(f"   WORKOS_REDIRECT_URL: {os.getenv('WORKOS_REDIRECT_URL', 'NOT SET')}")
print()

# NOW import PyQt5 and other modules
from PyQt5.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap

# Set Qt attributes before creating QApplication
QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

# Import Config AFTER dotenv is loaded
from core.config import Config
from core.theme_manager import theme_manager
from core.logger import logger
from core.user_settings import UserSettings

# Verify Config has the values
print("🔍 app_main.py: Config values after import:")
print(f"   Config.WORKOS_API_KEY: {'SET' if Config.WORKOS_API_KEY else 'NOT SET'}")
print(f"   Config.WORKOS_CLIENT_ID: {'SET' if Config.WORKOS_CLIENT_ID else 'NOT SET'}")
print(f"   Config.WORKOS_REDIRECT_URL: {Config.WORKOS_REDIRECT_URL}")
print()


class PennyWiseApp:
    """Main application class with proper login flow"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.dashboard = None
        self.login_window = None
        self.dashboard_started = False
        self.user_id = None
        self.username = None

    def setup_application(self):
        """Setup application-wide settings"""
        theme_manager.load_stylesheets()
        default_theme = "light"
        try:
            if self.user_id:
                us = UserSettings(self.user_id)
                default_theme = "dark" if us.settings.get("dark_mode") else "light"
        except Exception as e:
            logger.warning(f"Could not load user theme preference, using light: {e}")
        theme_manager.apply_theme(self.app, default_theme)

        self.app.setApplicationName("PennyWise")
        self.app.setApplicationVersion("2.0.0")
        self.app.setOrganizationName("PennyWise")

        self.setup_database()

    def setup_database(self):
        """Ensure database has required tables for v2"""
        try:
            from database.db_manager import fetch_all, execute_query

            tables = fetch_all("SELECT name FROM sqlite_master WHERE type='table'")
            table_names = [table['name'] for table in tables]

            if 'category_commitments' not in table_names:
                logger.info("Creating v2 database tables...")
                self.create_v2_tables()

            print(f"Database connected. Found {len(tables)} tables")
        except Exception as e:
            logger.error(f"Database setup failed: {e}")

    def create_v2_tables(self):
        """Create tables required for v2 features"""
        from database.db_manager import execute_query

        try:
            execute_query("""
                CREATE TABLE IF NOT EXISTS category_commitments (
                    commitment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    category_id INTEGER NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    due_day INTEGER DEFAULT 1,
                    is_paid BOOLEAN DEFAULT 0,
                    paid_date TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (category_id) REFERENCES categories (category_id)
                )
            """, commit=True)

            logger.info("V2 database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create v2 tables: {e}")

    def show_splash_screen(self):
        """Show splash screen"""
        try:
            splash_pix = QPixmap(300, 200)
            splash_pix.fill(Qt.white)
            splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
            splash.showMessage(
                "Loading PennyWise v2...",
                Qt.AlignBottom | Qt.AlignCenter,
                Qt.black,
            )
            splash.show()
            self.app.processEvents()
            QTimer.singleShot(2000, splash.close)
            return splash
        except Exception as e:
            logger.warning(f"Splash failed: {e}")
            return None

    def show_login(self):
        """Show login window"""
        try:
            from ui.loginv2 import LoginWindowV2
            self.login_window = LoginWindowV2()
            self.login_window.login_successful.connect(self.on_login_success)
            self.login_window.show()
            logger.info("LoginWindowV2 displayed")
        except Exception as e:
            logger.error(f"Failed to show LoginWindowV2: {e}")
            self.fallback_to_old_login()

    def fallback_to_old_login(self):
        """Fallback to old login system with warning"""
        try:
            from ui.login_window import LoginWindow
            self.login_window = LoginWindow()

            if hasattr(self.login_window, 'login_successful'):
                def wrapped_login(user_id, username):
                    from database.db_manager import fetch_one
                    user = fetch_one("SELECT role FROM users WHERE user_id = ?", (user_id,))
                    role = user.get("role", "End User") if user else "End User"
                    self.on_login_success(user_id, username, role)
                self.login_window.login_successful.connect(wrapped_login)
            else:
                QTimer.singleShot(1000, lambda: QMessageBox.information(
                    None, "Info", "Please use the old login system normally"))

            self.login_window.show()
            logger.info("Using old LoginWindow as fallback")
        except Exception as e:
            logger.error(f"All login methods failed: {e}")
            QMessageBox.critical(None, "Error",
                                 "Cannot start application. Please check your installation.")
            sys.exit(1)

    def on_login_success(self, user_id, username, role):
        """Handle successful login"""
        self.user_id = user_id
        self.username = username
        self.user_role = role
        logger.info(f"User {username} (ID: {user_id}, Role: {role}) logged in successfully")

        if self.login_window:
            self.login_window.close()
            self.login_window = None

        self.start_dashboard()

    def start_dashboard(self):
        """Start the main dashboard"""
        if self.dashboard_started:
            return
        self.dashboard_started = True

        print(f"Starting dashboard for user {self.username} (ID: {self.user_id})")

        if not QApplication.instance():
            print("QApplication not initialized!")
            return

        try:
            us = UserSettings(self.user_id)
            user_theme = "dark" if us.is_dark_mode_enabled() else "light"
            theme_manager.apply_theme(self.app, user_theme)
        except Exception as e:
            logger.warning(f"Could not apply user theme preference, keeping current theme: {e}")

        try:
            from core.font_manager import apply_font_size
            from database.db_manager import fetch_one
            settings = fetch_one("SELECT font_family FROM settings WHERE user_id = ?", (self.user_id,))
            if settings and 'font_family' in settings.keys():
                font_size = settings['font_family']
                if font_size in ["Small", "Medium", "Large"]:
                    apply_font_size(font_size)
                else:
                    apply_font_size("Medium")
            else:
                apply_font_size("Medium")
        except Exception as e:
            logger.warning(f"Could not apply font size preference: {e}")

        try:
            from ui.dashboard_main import DashboardMain
            self.dashboard = DashboardMain(
                user_id=self.user_id,
                username=self.username,
                role=self.user_role,
                show_tutorial=False
            )
            logger.info("Modern Dashboard Loaded Successfully")
            self.dashboard.show()
            print("New dashboard is now active!")
            return

        except ImportError as e:
            logger.error(f"Failed to import DashboardMain: {e}")
            print(f"Import error details: {e}")
            self.create_error_dashboard(f"Import Error: {e}")
        except Exception as e:
            logger.error(f"Failed to load modern dashboard: {e}")
            print(f"Dashboard error details: {e}")
            self.create_error_dashboard(f"Dashboard Error: {e}")

    def create_error_dashboard(self, error_message):
        """Create an error dashboard when new dashboard fails"""
        from PyQt5.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton
        from PyQt5.QtCore import Qt

        self.dashboard = QMainWindow()
        self.dashboard.setWindowTitle(f"PennyWise v2 - {self.username} (Error)")
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        title = QLabel(f"Welcome to PennyWise v2, {self.username}!")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #704b3b; margin: 20px;")
        title.setAlignment(Qt.AlignCenter)

        error_label = QLabel(f"New Dashboard Error:\n{error_message}")
        error_label.setStyleSheet("font-size: 14px; color: #dc3545; background: #f8d7da; padding: 15px; border-radius: 8px; border: 1px solid #f5c6cb;")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setWordWrap(True)

        note_label = QLabel("Note: Old dashboard is kept as reference only.\nPlease check the error and fix the new dashboard.")
        note_label.setStyleSheet("font-size: 12px; color: #6c757d; font-style: italic;")
        note_label.setAlignment(Qt.AlignCenter)
        note_label.setWordWrap(True)

        retry_btn = QPushButton("Retry Dashboard")
        retry_btn.setStyleSheet("""
            QPushButton {
                background-color: #e89574;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d4886b;
            }
        """)
        retry_btn.clicked.connect(self.retry_dashboard)

        layout.addWidget(title)
        layout.addWidget(error_label)
        layout.addWidget(note_label)
        layout.addWidget(retry_btn)
        layout.addStretch()

        self.dashboard.setCentralWidget(central)
        logger.info("Using Error Dashboard")
        self.dashboard.show()

    def retry_dashboard(self):
        """Retry loading the new dashboard"""
        self.dashboard_started = False
        if self.dashboard:
            self.dashboard.close()
        self.start_dashboard()

    def run(self):
        """Run the application"""
        logger.info("Starting PennyWise Application v2.0")

        self.setup_application()

        splash = self.show_splash_screen()

        if splash:
            QTimer.singleShot(1500, self.show_login)
        else:
            self.show_login()

        logger.info("PennyWise Application Started")
        return self.app.exec_()


def main():
    """Main entry point"""
    print("PennyWise v2.0 - Starting...")
    print("=======================================")

    try:
        Config.validate_config()
    except Exception as e:
        print(f"Config validation issue: {e}")
        print("Running with default configuration")

    app = PennyWiseApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
