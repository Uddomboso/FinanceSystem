import sys
from PyQt5.QtWidgets import QApplication
from database.db_manager import initialize_db
from ui.login_window import LoginWindow


def main():
    # database
    initialize_db()

    # start
    app = QApplication(sys.argv)
    app.setApplicationName("PennyWise - Personal Finance Manager")

    window = LoginWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
