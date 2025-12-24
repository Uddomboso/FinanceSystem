# app_main.py - FIXED TO PROPERLY USE NEW SYSTEM
import sys
from PyQt5.QtWidgets import QApplication,QSplashScreen,QMessageBox
from PyQt5.QtCore import Qt,QTimer
from PyQt5.QtGui import QPixmap

# SET QT ATTRIBUTES BEFORE CREATING QAPPLICATION
QApplication.setAttribute(Qt.AA_ShareOpenGLContexts,True)
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling,True)

from core.theme_manager import theme_manager
from core.config import Config
from core.logger import logger
from core.user_settings import UserSettings


class PennyWiseApp:
    """Main application class with proper login flow"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        # Prevent app from quitting when the last window closes during transitions (e.g., login -> dashboard)
        self.app.setQuitOnLastWindowClosed(False)
        self.dashboard = None
        self.login_window = None
        self.dashboard_started = False
        self.user_id = None
        self.username = None

    def setup_application(self):
        """Setup application-wide settings"""
        # Apply theme
        theme_manager.load_stylesheets()
        # Load user theme preference if available
        default_theme = "light"
        try:
            # If no user yet, fallback to light; once login succeeds, the dashboard will reapply
            # but we try to respect persisted setting when possible.
            if self.user_id:
                us = UserSettings(self.user_id)
                default_theme = "dark" if us.settings.get("dark_mode") else "light"
        except Exception as e:
            logger.warning(f"Could not load user theme preference, using light: {e}")
        theme_manager.apply_theme(self.app, default_theme)

        # App metadata
        self.app.setApplicationName("PennyWise")
        self.app.setApplicationVersion("2.0.0")
        self.app.setOrganizationName("PennyWise")

        # Initialize database for v2
        self.setup_database()

    def setup_database(self):
        """Ensure database has required tables for v2"""
        try:
            from database.db_manager import fetch_all,execute_query

            # Check if we have the new commitment tables
            tables = fetch_all("SELECT name FROM sqlite_master WHERE type='table'")
            table_names = [table['name'] for table in tables]

            # Create missing tables for v2 features
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
            # Category commitments table
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
            """,commit=True)

            logger.info("V2 database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create v2 tables: {e}")

    def show_splash_screen(self):
        """Show splash screen"""
        try:
            splash_pix = QPixmap(300,200)
            splash_pix.fill(Qt.white)
            splash = QSplashScreen(splash_pix,Qt.WindowStaysOnTopHint)
            splash.showMessage(
                "Loading PennyWise v2...",
                Qt.AlignBottom | Qt.AlignCenter,
                Qt.black,
            )
            splash.show()
            self.app.processEvents()
            QTimer.singleShot(2000,splash.close)
            return splash
        except Exception as e:
            logger.warning(f"Splash failed: {e}")
            return None

    def show_login(self):
        """Show login window - FIXED to properly handle new system"""
        try:
            from ui.loginv2 import LoginWindowV2
            self.login_window = LoginWindowV2()
            self.login_window.login_successful.connect(self.on_login_success)
            self.login_window.show()
            logger.info("LoginWindowV2 displayed")
        except Exception as e:
            logger.error(f"Failed to show LoginWindowV2: {e}")
            # Instead of falling back to demo, show error and try old system
            self.fallback_to_old_login()

    def fallback_to_old_login(self):
        """Fallback to old login system with warning"""
        try:
            from ui.login_window import LoginWindow
            self.login_window = LoginWindow()

            # Monkey-patch the old login to work with new flow
            def old_login_success_wrapper():
                # For old system, we need to extract user info differently
                # This is a hack to make old system work with new flow
                QMessageBox.warning(None,"Compatibility Mode",
                                    "Using old system - some features may be limited")
                self.on_login_success(1,"User")  # Default user

            # Connect the old login success (this is a bit hacky)
            if hasattr(self.login_window,'login_successful'):
                self.login_window.login_successful.connect(self.on_login_success)
            else:
                # If old system doesn't have signals, we'll handle it differently
                QTimer.singleShot(1000,lambda: QMessageBox.information(
                    None,"Info","Please use the old login system normally"))

            self.login_window.show()
            logger.info("Using old LoginWindow as fallback")
        except Exception as e:
            logger.error(f"All login methods failed: {e}")
            QMessageBox.critical(None,"Error",
                                 "Cannot start application. Please check your installation.")
            sys.exit(1)

    def on_login_success(self,user_id,username):
        """Handle successful login"""
        self.user_id = user_id
        self.username = username
        logger.info(f"User {username} (ID: {user_id}) logged in successfully")

        # Close login window if it exists
        if self.login_window:
            self.login_window.close()
            self.login_window = None

        # Start dashboard
        self.start_dashboard()

    def start_dashboard(self):
        """Start the main dashboard - Uses new DashboardMain only"""
        if self.dashboard_started:
            return
        self.dashboard_started = True

        print(f"Starting dashboard for user {self.username} (ID: {self.user_id})")

        # Ensure QApplication is ready
        if not QApplication.instance():
            print("QApplication not initialized!")
            return

        # Re-apply theme using the logged-in user's preference (source of truth)
        try:
            us = UserSettings(self.user_id)
            user_theme = "dark" if us.is_dark_mode_enabled() else "light"
            theme_manager.apply_theme(self.app, user_theme)
        except Exception as e:
            logger.warning(f"Could not apply user theme preference, keeping current theme: {e}")

        try:
            # Import and create the new dashboard
            from ui.dashboard_main import DashboardMain
            self.dashboard = DashboardMain(
                user_id=self.user_id,
                username=self.username,
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

    def create_basic_dashboard(self):
        """Create a basic dashboard as last resort"""
        from PyQt5.QtWidgets import QMainWindow,QLabel,QVBoxLayout,QWidget
        self.dashboard = QMainWindow()
        self.dashboard.setWindowTitle(f"PennyWise v2 - {self.username}")
        central = QWidget()
        layout = QVBoxLayout(central)

        title = QLabel(f"Welcome to PennyWise v2, {self.username}!")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #704b3b; margin: 20px;")

        subtitle = QLabel("Basic Mode - New dashboard failed to load")
        subtitle.setStyleSheet("font-size: 16px; color: #8a6d5b; margin: 10px;")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch()

        self.dashboard.setCentralWidget(central)
        logger.info("Using Basic Dashboard (Fallback)")
        self.dashboard.show()

    def run(self):
        """Run the application"""
        logger.info("Starting PennyWise Application v2.0")

        # Setup app
        self.setup_application()

        # Show splash
        splash = self.show_splash_screen()

        # Show login after splash
        if splash:
            QTimer.singleShot(1500,self.show_login)
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