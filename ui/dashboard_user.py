from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QStackedWidget, QFrame, QComboBox, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QFont, QIcon
from PyQt5.QtCore import Qt, QSize
import qtawesome as qta

from ui.transaction_form import TransactionForm
from ui.budget_window import BudgetWindow
from ui.charts_window import ChartsWindow
from ui.settings_window import SettingsWindow
from ui.ai_suggestions_window import AISuggestions
from ui.bank_connect_window import BankConnectWindow

class UserDashboard(QMainWindow):
    def __init__(self, username, user_id):
        super().__init__()
        self.username = username
        self.user_id = user_id

        self.setWindowTitle("PennyWise | Dashboard")
        self.setMinimumSize(1440, 900)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        self.nav_buttons = {}  # keep track of nav buttons for styling

        self.init_sidebar()
        self.init_pages()
        self.show_dashboard()

    def init_sidebar(self):
        sidebar = QVBoxLayout()
        sidebar.setAlignment(Qt.AlignTop)
        sidebar.setSpacing(20)

        # logo on top
        logo = QLabel()
        pixmap = QPixmap("logopng.png")
        pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo.setPixmap(pixmap)
        logo.setAlignment(Qt.AlignCenter)
        sidebar.addWidget(logo)

        # nav buttons
        nav_items = [
            ("Dashboard", "fa5s.tachometer-alt", self.show_dashboard),
            ("Transactions", "fa5s.exchange-alt", self.show_transactions),
            ("Budget", "fa5s.money-bill-wave", self.show_budget),
            ("Reports", "fa5s.chart-bar", self.show_reports),
            ("Settings", "fa5s.cog", self.show_settings),
            ("AI Tips", "fa5s.lightbulb", self.show_ai),
            ("Link Bank","fa5s.university",self.show_bank)

        ]

        for text, icon_name, func in nav_items:
            icon = qta.icon(icon_name, color="#ffe22a")
            btn = QPushButton(icon, f"  {text}")
            btn.setFont(QFont("Segoe UI", 14))
            btn.setStyleSheet(self.default_btn_style())
            btn.setIconSize(QSize(24, 24))
            btn.clicked.connect(func)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.nav_buttons[text] = btn
            sidebar.addWidget(btn)

        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar)
        sidebar_widget.setFixedWidth(240)
        sidebar_widget.setStyleSheet("background-color: #d6733a;")
        self.main_layout.addWidget(sidebar_widget)

    def init_pages(self):
        self.stack = QStackedWidget()

        self.page_dashboard = self.build_dashboard()
        self.page_transactions = TransactionForm(self.user_id)
        self.page_budget = BudgetWindow(self.user_id)
        self.page_reports = ChartsWindow(self.user_id)
        self.page_settings = SettingsWindow(self.user_id)
        self.page_ai = AISuggestions(self.user_id)
        self.page_bank = BankConnectWindow(self.user_id)

        self.stack.addWidget(self.page_bank)
        self.stack.addWidget(self.page_dashboard)
        self.stack.addWidget(self.page_transactions)
        self.stack.addWidget(self.page_budget)
        self.stack.addWidget(self.page_reports)
        self.stack.addWidget(self.page_settings)
        self.stack.addWidget(self.page_ai)

        self.main_layout.addWidget(self.stack)

    def highlight_nav(self, active_text):
        for text, btn in self.nav_buttons.items():
            if text == active_text:
                btn.setStyleSheet(self.active_btn_style())
            else:
                btn.setStyleSheet(self.default_btn_style())

    def default_btn_style(self):
        return """
            QPushButton {
                background-color: #704b3b;
                color: white;
                padding: 12px;
                border: none;
                border-bottom: 4px solid transparent;
                border-radius: 0px;
                text-align: left;
            }
            QPushButton:hover {
                border-bottom: 4px solid #ffe22a;
            }
        """

    def active_btn_style(self):
        return """
            QPushButton {
                background-color: #704b3b;
                color: #ffe22a;
                padding: 12px;
                border: none;
                border-bottom: 4px solid #ffe22a;
                font-weight: bold;
                text-align: left;
            }
        """

    def build_dashboard(self):
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(30)

        header = QLabel(f"hey {self.username} 👋")
        header.setFont(QFont("Segoe UI", 32))
        header.setStyleSheet("color: #d6733a")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        ai_box = QLabel("\"you exceeded your food budget again. maybe review groceries or eating out?\"")
        ai_box.setWordWrap(True)
        ai_box.setFont(QFont("Segoe UI", 16))
        ai_box.setStyleSheet("""
            background-color: #e0f7fa;
            border-left: 6px solid #007bff;
            padding: 20px;
            border-radius: 8px;
            color: #333;
        """)
        layout.addWidget(ai_box)

        # categories
        cat_row = QHBoxLayout()
        for name, amt, color in [
            ("savings", "$540", "#3498db"),
            ("bills", "$290", "#b45131"),
            ("child support", "$0", "#c0392b")
        ]:
            box = QLabel(f"{name}\n{amt}")
            box.setFont(QFont("Segoe UI", 14))
            box.setAlignment(Qt.AlignCenter)
            box.setStyleSheet(f"""
                background-color: {color};
                color: white;
                border-radius: 80px;
                padding: 40px;
            """)
            cat_row.addWidget(box)
        layout.addLayout(cat_row)

        # chart slider (static demo)
        slider_label = QLabel("choose chart type")
        slider_label.setFont(QFont("Segoe UI", 14))
        slider_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(slider_label)

        chart_placeholder = QFrame()
        chart_placeholder.setStyleSheet("""
            background-color: #fdbd63;
            min-height: 200px;
            border-radius: 10px;
        """)
        layout.addWidget(chart_placeholder)

        # currency dropdown
        currency_label = QLabel("select currency")
        currency_label.setFont(QFont("Segoe UI", 14))
        currency_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(currency_label)

        dropdown = QComboBox()
        dropdown.addItems(["USD", "NGN", "EUR", "TRY"])
        dropdown.setFixedWidth(200)
        dropdown.setFont(QFont("Segoe UI", 12))
        dropdown.setStyleSheet("padding: 8px; background-color: white; border: 1px solid #ccc; border-radius: 6px;")
        layout.addWidget(dropdown, alignment=Qt.AlignCenter)

        page.setLayout(layout)
        return page

    def show_dashboard(self):
        self.stack.setCurrentWidget(self.page_dashboard)
        self.highlight_nav("Dashboard")

    def show_transactions(self):
        self.stack.setCurrentWidget(self.page_transactions)
        self.highlight_nav("Transactions")

    def show_budget(self):
        self.stack.setCurrentWidget(self.page_budget)
        self.highlight_nav("Budget")

    def show_reports(self):
        self.stack.setCurrentWidget(self.page_reports)
        self.highlight_nav("Reports")

    def show_settings(self):
        self.stack.setCurrentWidget(self.page_settings)
        self.highlight_nav("Settings")

    def show_ai(self):
        self.stack.setCurrentWidget(self.page_ai)
        self.highlight_nav("AI Tips")

    def show_bank(self):
        self.stack.setCurrentWidget(self.page_bank)
        self.highlight_nav("Link Bank")
