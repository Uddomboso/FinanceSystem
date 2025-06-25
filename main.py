import sys
from PyQt5.QtWidgets import QApplication
from database.db_manager import initialize_db
from ui.login_window import LoginWindow  # ✅ New import


def main():
    # Initialize database
    initialize_db()

    # Start the application
    app = QApplication(sys.argv)
    app.setApplicationName("PennyWise - Personal Finance Manager")

    # ✅ Replace placeholder with actual login window
    window = LoginWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
