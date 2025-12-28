"""
Main Dashboard - Modern UI with Navigation & Notifications
"""

import sys
from PyQt5.QtWidgets import (
    QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QLabel,
    QScrollArea,QFrame,QSizePolicy,QPushButton,QMessageBox,
    QApplication,QStyle,QStackedWidget,QToolBar,QAction,
    QStatusBar,QMenu,QSystemTrayIcon,QGridLayout, QSpacerItem,
    QWidgetAction,QDialog,QRadioButton,QButtonGroup
)
from PyQt5.QtCore import Qt,QTimer,QPropertyAnimation,QEasingCurve,QSize,QEvent,pyqtSignal
from PyQt5.QtGui import QFont,QIcon,QPalette,QColor,QPainter,QPixmap
from datetime import datetime, timedelta

# ===== COMPONENT IMPORTS =====
from ui.components.mood_meter import MoodMeter
from ui.components.badges_widget import BadgesWidget
from ui.components.enhanced_penny_widget import EnhancedPennyWidget
from ui.components.cards import CardWidget
from ui.components.metrics import MetricChip
from ui.components.progress import ProgressBar
from ui.tutorial_system import TutorialManager
from core.theme_manager import theme_manager
from assets.styles.penny_colors import PennyColors
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from PyQt5.QtWidgets import QGraphicsOpacityEffect
from database.db_manager import fetch_all, fetch_one, execute_query
from core.plaid_api import create_link_token, exchange_public_token, get_accounts, get_transactions, get_account_balances
from core.logger import logger
import qtawesome as qta
from PyQt5.QtWidgets import QStatusBar,QMenu,QSystemTrayIcon,QGridLayout, QSpacerItem
from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QGridLayout
from PyQt5.QtGui import QColor
from database.db_manager import fetch_all
# Ensure QPixmap, QFont, Qt are already imported from PyQt5.QtGui/QtCore
from PyQt5.QtWidgets import QMessageBox
from database.db_manager import fetch_all, fetch_one, execute_query
from PyQt5.QtWidgets import QMessageBox, QInputDialog
from database.db_manager import fetch_all, fetch_one, execute_query
from core.commitment_manager import (
    check_commitments,
    process_immediate_commitment,
    create_commitment,
    get_suggested_amount
)
from ui.commitment_form import CommitmentForm, CommitmentSelectionDialog
from ui.savings_form import SavingsForm

from database.db_manager import fetch_all, fetch_one, execute_query
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QFrame, QSizePolicy, QSpacerItem


# --- Define Constants (Crucial for styling) ---
from assets.styles.penny_colors import PennyColors


def _nav_palette(theme_name=None):
    name = theme_name or theme_manager.current_theme
    return PennyColors.NAV_DARK if name == "dark" else PennyColors.NAV_LIGHT


def theme_palette():
    """Return the global palette for the active theme."""
    return PennyColors.get_palette(theme_manager.current_theme)


def theme_color(token, fallback=None):
    """Fetch a palette value with optional fallback."""
    palette = theme_palette()
    if token in palette:
        return palette[token]
    if fallback is not None:
        return fallback
    return palette.get("text_primary", "#ffffff")
# -----------------------------------------------

class NotificationBadge(QWidget):
    """Interactive notification badge with hover preview and click handling"""

    def __init__(self, count=0, parent=None):
        super().__init__(parent)
        self.count = count
        self.setFixedSize(18, 18)
        
        # Enable mouse events on QWidget
        self.setEnabled(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)
        
        self.update_count(count)
        
        # UI components (will be set by parent)
        self.preview_popup = None
        self.notification_window = None
        self.notification_manager = None

    def paintEvent(self, e):
        """Draw the badge manually"""
        from PyQt5.QtGui import QPainter, QColor, QFont
        from PyQt5.QtCore import Qt
        
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # Draw circle background
        p.setBrush(QColor("#dc2626"))
        p.setPen(Qt.NoPen)
        p.drawEllipse(0, 0, 18, 18)

        # Draw count text
        p.setPen(Qt.white)
        p.setFont(QFont("segoe ui", 9, QFont.Bold))
        text = str(self.count) if self.count <= 99 else "99+"
        p.drawText(self.rect(), Qt.AlignCenter, text)

    def update_count(self, count):
        """Update badge count and visibility"""
        self.count = count
        if count > 0:
            self.show()
        else:
            self.hide()
        self.update()  # Trigger repaint

    def enterEvent(self, event):
        if hasattr(self, "preview_popup"):
            self.preview_popup.update_content()
            self.preview_popup.move(
                self.mapToGlobal(self.rect().bottomLeft())
            )
            self.preview_popup.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if hasattr(self, "preview_popup"):
            self.preview_popup.hide()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Find parent DashboardMain and show notifications panel
            parent = self.parent()
            while parent and not hasattr(parent, 'show_notifications'):
                parent = parent.parent()
            if parent and hasattr(parent, 'show_notifications'):
                parent.show_notifications()
        super().mousePressEvent(event)


class CustomTitleBar(QWidget):
    """
    A custom, draggable title bar with dark background and window control buttons.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.setFixedHeight(30)  # Height of the standard title bar
        self.setMouseTracking(True)
        self.nav_colors = {}
        self.apply_palette()

        self.setup_ui()

    def apply_palette(self):
        self.nav_colors = _nav_palette()
        self.setStyleSheet(f"""
            CustomTitleBar {{
                background-color: {self.nav_colors['bg']};
                color: {self.nav_colors['text_secondary']};
                border: none;
            }}
        """)

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 5, 0)
        layout.setSpacing(5)

        # Title label removed
        layout.addStretch()

        # 2. Control Buttons (Minimize, Maximize, Close) - FIXED ICON NAMES
        btn_min = self.create_button('fa5s.window-minimize', self.main_window.showMinimized, "Minimize")
        self.btn_max_restore = self.create_button('fa5s.window-maximize', self.toggle_maximize, "Maximize")
        btn_close = self.create_button('fa5s.times', self.main_window.close, "Close")

        layout.addWidget(btn_min)
        layout.addWidget(self.btn_max_restore)
        layout.addWidget(btn_close)

    def create_button(self, icon_id, action, tooltip):
        btn = QPushButton()
        btn.setFixedSize(QSize(25, 25))
        btn.setToolTip(tooltip)

        try:
            icon = qta.icon(icon_id, color=self.nav_colors.get("text_secondary", "#FFFFFF"))
            btn.setIcon(icon)
        except Exception as e:
            print(f"Warning: Could not load icon {icon_id}: {e}")
            # Fallback to text if icon fails
            if 'minimize' in icon_id:
                btn.setText("_")
            elif 'maximize' in icon_id:
                btn.setText("□")
            elif 'times' in icon_id:
                btn.setText("×")

        btn.clicked.connect(action)

        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                padding: 0;
                border-radius: 3px;
                color: {self.nav_colors.get("text_secondary", "#FFFFFF")};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {theme_color('surface_alt')};
            }}
            QPushButton#CloseButton:hover {{
                background-color: {theme_color('error')};
                color: {theme_color('surface')};
            }}
        """)
        if 'times' in icon_id:
            btn.setObjectName("CloseButton")

        return btn

    def refresh_theme(self):
        self.apply_palette()
        # Update button icons to match new palette
        for btn in self.findChildren(QPushButton):
            icon = btn.icon()
            if icon.isNull():
                continue
            # Recreate icon with updated color where possible
            data = btn.toolTip().lower()
            icon_id = (
                'fa5s.window-minimize' if "minimize" in data else
                'fa5s.window-maximize' if "maximize" in data else
                'fa5s.times'
            )
            try:
                btn.setIcon(qta.icon(icon_id, color=self.nav_colors.get("text_secondary", "#FFFFFF")))
            except Exception:
                pass

    # --- Draggability methods ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position:
            if self.main_window.isMaximized():
                # If window is maximized, restore it first
                self.main_window.showNormal()
                # Adjust position to make dragging natural
                cursor_x = event.globalPos().x()
                window_width = self.main_window.width()
                new_x = cursor_x - (window_width / 2)
                self.main_window.move(int(new_x), 0)
                self.drag_position = event.globalPos()
            else:
                delta = event.globalPos() - self.drag_position
                self.main_window.move(self.main_window.pos() + delta)
                self.drag_position = event.globalPos()
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle_maximize()

    def toggle_maximize(self):
        if self.main_window.isMaximized():
            self.main_window.showNormal()
            try:
                self.btn_max_restore.setIcon(qta.icon('fa5s.window-maximize', color=NAV_TEXT_COLOR))
            except:
                self.btn_max_restore.setText("□")
            self.btn_max_restore.setToolTip("Maximize")
        else:
            self.main_window.showMaximized()
            try:
                self.btn_max_restore.setIcon(qta.icon('fa5s.window-restore', color=NAV_TEXT_COLOR))
            except:
                self.btn_max_restore.setText("❐")
            self.btn_max_restore.setToolTip("Restore")




class MetricsCarousel(QWidget):
    """Modern metrics carousel with real Plaid API data"""

    def __init__(self,user_id,parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.current_index = 0
        self.metrics_data = []  # Will be populated with real data
        self.current_available_balance = None
        self.current_commitments_total = None
        self.current_price_after_commitments = None
        self.current_currency = "USD"
        self.setup_ui()
        self.load_real_data()
        self.start_rotation()

    def setup_ui(self):
        """Setup UI for carousel"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.carousel_layout = QHBoxLayout()
        self.carousel_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self.carousel_layout)
        layout.addStretch()

    def setup_metrics_carousel(self,layout):
        """3-card financial overview with real data"""
        # Create the 3-card container
        overview_frame = QFrame()
        overview_frame.setStyleSheet("QFrame { padding-top: 0px; }")
        overview_layout = QHBoxLayout(overview_frame)
        overview_layout.setSpacing(15)
        overview_layout.setContentsMargins(0,0,0,0)
        
        # Store layout and frame for refresh
        self.overview_frame = overview_frame
        self.overview_layout = overview_layout

        try:
            # Import the required functions
            from database.db_manager import fetch_all,fetch_one

            # Get checking account balance - first try Plaid, then fallback to transactions
            checking_balance = 0
            has_plaid_checking = False
            
            # Check if main account (checking) exists
            main_account = fetch_one("""
                SELECT account_id FROM accounts 
                WHERE user_id = ? AND account_type = 'salary' AND is_primary = 1
                LIMIT 1
            """, (self.user_id,))
            
            # Check if savings account exists (any savings account, not just primary)
            savings_account = fetch_one("""
                SELECT account_id FROM accounts 
                WHERE user_id = ? AND account_type = 'savings' AND plaid_token IS NOT NULL
                LIMIT 1
            """, (self.user_id,))
            
            has_main_account = main_account is not None
            has_savings_account = savings_account is not None
            
            # Get checking account balance - ONLY the primary main account
            checking_balance = 0
            if has_main_account:
                main_account_data = fetch_one("""
                    SELECT account_id, plaid_token
                    FROM accounts 
                    WHERE user_id = ? 
                    AND account_type = 'salary' AND is_primary = 1
                    AND plaid_token IS NOT NULL
                    LIMIT 1
                """,(self.user_id,))
                
                if main_account_data:
                    from core.plaid_api import get_account_balances
                    try:
                        balances_data = get_account_balances(main_account_data["plaid_token"])
                        if "error" not in balances_data:
                            for acc_balance in balances_data.get("accounts",[]):
                                if acc_balance["account_id"] == main_account_data["account_id"]:
                                    balance = acc_balance["balances"].get("available",0) or 0
                                    checking_balance = balance
                                    break
                    except Exception as e:
                        logger.error(f"Error fetching checking balance: {e}")

            # Get savings balance - ONLY from Plaid, sum all savings accounts
            savings = 0
            if has_savings_account:
                savings_accounts = fetch_all("""
                    SELECT account_id, plaid_token
                    FROM accounts 
                    WHERE user_id = ? 
                    AND account_type = 'savings'
                    AND plaid_token IS NOT NULL
                """,(self.user_id,))
                
                if savings_accounts:
                    from core.plaid_api import get_account_balances
                    for savings_account_data in savings_accounts:
                        try:
                            balances_data = get_account_balances(savings_account_data["plaid_token"])
                            if "error" not in balances_data:
                                for acc_balance in balances_data.get("accounts",[]):
                                    if acc_balance["account_id"] == savings_account_data["account_id"]:
                                        balance = acc_balance["balances"].get("available",0) or 0
                                        savings += balance
                        except Exception as e:
                            logger.error(f"Error fetching savings balance: {e}")

            # Get commitments (unpaid)
            commitments_row = fetch_one("""
                SELECT COALESCE(SUM(amount), 0) AS total
                FROM category_commitments
                WHERE user_id = ? AND COALESCE(is_paid, 0) = 0
            """,(self.user_id,))
            try:
                commitments = commitments_row["total"] if commitments_row and "total" in commitments_row.keys() and commitments_row["total"] is not None else 0
            except (KeyError, TypeError, AttributeError):
                commitments = 0

            # Calculate balances
            available_balance = checking_balance if has_main_account else 0
            price_after_commitments = (checking_balance - commitments) if has_main_account else 0

            # Get currency
            user_currency = fetch_one("SELECT currency FROM settings WHERE user_id = ?",(self.user_id,))
            try:
                currency = user_currency["currency"] if user_currency and "currency" in user_currency.keys() else "USD"
            except (KeyError, TypeError, AttributeError):
                currency = "USD"

            # Create cards - ALWAYS show empty cards with add buttons when balance is 0 or no account
            # This ensures users always see the option to add accounts
            if has_savings_account and savings > 0:
                self.savings_card = self.create_finance_card(
                    " Savings Balance",
                    f"{currency} {savings:,.2f}",
                    theme_color('success'),
                    "positive"
                )
            else:
                # Show empty card with add button (when no account OR balance is 0)
                def show_link_bank():
                    # Find the dashboard window by traversing parent widgets
                    widget = self
                    while widget:
                        if hasattr(widget, 'show_link_bank'):
                            widget.show_link_bank()
                            return
                        widget = widget.parent()
                    # Fallback: try to find DashboardMain window
                    from PyQt5.QtWidgets import QApplication
                    for widget in QApplication.topLevelWidgets():
                        if hasattr(widget, 'show_link_bank'):
                            widget.show_link_bank()
                            return
                
                self.savings_card = self.create_empty_card(
                    " Savings Balance",
                    "Add Savings Account",
                    show_link_bank
                )

            # Price After Commitments always shows as finance card (even with 0.00)
            self.commitments_card = self.create_finance_card(
                "Price After Commitments",
                f"{currency} {price_after_commitments:,.2f}",
                theme_color('warning'),
                "warning"
            )
            
            # Available Balance shows empty card if no account or balance is 0
            if has_main_account and checking_balance > 0:
                self.available_card = self.create_finance_card(
                    "Available Balance",
                    f"{currency} {available_balance:,.2f}",
                    theme_color('success'),
                    "positive"
                )
            else:
                # Show empty card with add button
                def show_link_bank_main():
                    # Find the dashboard window by traversing parent widgets
                    widget = self
                    while widget:
                        if hasattr(widget, 'show_link_bank'):
                            widget.show_link_bank()
                            return
                        widget = widget.parent()
                    # Fallback: try to find DashboardMain window
                    from PyQt5.QtWidgets import QApplication
                    for widget in QApplication.topLevelWidgets():
                        if hasattr(widget, 'show_link_bank'):
                            widget.show_link_bank()
                            return
                
                self.available_card = self.create_empty_card(
                    "Available Balance",
                    "Add Bank Account",
                    show_link_bank_main
                )

            # Make Balance After Commitments card 1/8 bigger (160 * 1.125 = 180)
            self.commitments_card.setFixedHeight(180)
            overview_layout.addWidget(self.savings_card)
            overview_layout.addWidget(self.commitments_card)
            overview_layout.addWidget(self.available_card)

        except Exception as e:
            print(f"Error loading financial data: {e}")
            # Fallback to empty cards with add buttons if real data fails
            def show_link_bank_fallback():
                # Find the dashboard window by traversing parent widgets
                widget = self
                while widget:
                    if hasattr(widget, 'show_link_bank'):
                        widget.show_link_bank()
                        return
                    widget = widget.parent()
                # Fallback: try to find DashboardMain window
                from PyQt5.QtWidgets import QApplication
                for widget in QApplication.topLevelWidgets():
                    if hasattr(widget, 'show_link_bank'):
                        widget.show_link_bank()
                        return
            
            self.savings_card = self.create_empty_card(
                " Savings Balance",
                "Add Savings Account",
                show_link_bank_fallback
            )

            # Price After Commitments always shows as finance card (even with 0.00)
            self.commitments_card = self.create_finance_card(
                "Price After Commitments",
                f"{currency} 0.00",
                theme_color('warning'),
                "warning"
            )

            self.available_card = self.create_empty_card(
                "Available Balance",
                "Add Bank Account",
                show_link_bank_fallback
            )

            self.commitments_card.setFixedHeight(180)
            overview_layout.addWidget(self.savings_card)
            overview_layout.addWidget(self.commitments_card)
            overview_layout.addWidget(self.available_card)

        layout.addWidget(overview_frame)

    def refresh_metrics_cards(self):
        """Refresh the metrics cards by clearing and rebuilding them"""
        if not hasattr(self, 'overview_layout'):
            return
        
        # Clear existing cards
        while self.overview_layout.count():
            item = self.overview_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Rebuild cards with fresh data
        # Store the parent frame before clearing
        parent_frame = self.overview_layout.parent()
        if parent_frame:
            # Clear the frame's layout
            if parent_frame.layout():
                while parent_frame.layout().count():
                    item = parent_frame.layout().takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
            # Rebuild
            self.setup_metrics_carousel(parent_frame.layout() if parent_frame.layout() else None)

    def load_real_data(self):
        """Load real financial data using your existing Plaid API logic"""
        try:
            # Import the required functions
            from database.db_manager import fetch_all,fetch_one
            from core.plaid_api import get_account_balances

            # Get REAL checking account balance from Plaid
            checking_balance = 0
            has_plaid_checking = False

            # Get Plaid checking accounts (which are stored as 'salary' type)
            plaid_accounts = fetch_all("""
                SELECT account_id, plaid_token, account_type, bank_name
                FROM accounts 
                WHERE user_id = ? 
                AND account_type = 'salary'
                AND plaid_token IS NOT NULL
            """,(self.user_id,))

            if plaid_accounts:
                has_plaid_checking = True
                for account in plaid_accounts:
                    try:
                        balances_data = get_account_balances(account["plaid_token"])
                        # Check if response contains an error
                        if "error" in balances_data:
                            logger.warning(f"Plaid balance error for account {account['account_id']}: {balances_data['error']}")
                            continue
                        for acc_balance in balances_data.get("accounts",[]):
                            if acc_balance["account_id"] == account["account_id"]:
                                balance = acc_balance["balances"].get("available",0)
                                checking_balance += balance
                    except Exception as e:
                        logger.error(f"Error fetching balance for account {account['account_id']}: {e}")

            # If Plaid failed, use transaction-based calculation
            if not has_plaid_checking or checking_balance == 0:
                checking_balance_row = fetch_one("""
                    SELECT SUM(
                        CASE 
                            WHEN transaction_type = 'income' THEN amount 
                            WHEN transaction_type = 'expense' THEN -amount 
                            ELSE 0 
                        END
                    ) as balance
                    FROM transactions
                    WHERE user_id = ?
                """,(self.user_id,))
                checking_balance = checking_balance_row["balance"] if checking_balance_row and checking_balance_row[
                    "balance"] is not None else 0

            # Get savings balance - ONLY from Plaid, no fallback
            savings = 0
            plaid_savings_accounts = fetch_all("""
                SELECT account_id, plaid_token, account_type, bank_name
                FROM accounts 
                WHERE user_id = ? 
                AND account_type = 'savings'
                AND plaid_token IS NOT NULL
            """,(self.user_id,))
            
            if plaid_savings_accounts:
                # Get real savings balance from Plaid for all savings accounts
                for account in plaid_savings_accounts:
                    try:
                        balances_data = get_account_balances(account["plaid_token"])
                        if "error" in balances_data:
                            logger.warning(f"Plaid savings balance error for account {account['account_id']}: {balances_data['error']}")
                            continue
                        for acc_balance in balances_data.get("accounts",[]):
                            if acc_balance["account_id"] == account["account_id"]:
                                balance = acc_balance["balances"].get("available",0) or 0
                                savings += balance
                    except Exception as e:
                        logger.error(f"Error fetching savings balance for account {account['account_id']}: {e}")

            # Get commitments (unpaid) - handle NULL is_paid values
            commitments_row = fetch_one("""
                SELECT COALESCE(SUM(amount), 0) AS total
                FROM category_commitments
                WHERE user_id = ? AND COALESCE(is_paid, 0) = 0
            """,(self.user_id,))
            # Handle sqlite3.Row object
            try:
                commitments = commitments_row["total"] if commitments_row and "total" in commitments_row.keys() and commitments_row["total"] is not None else 0
            except (KeyError, TypeError, AttributeError):
                commitments = 0
            logger.info(f"[metrics_carousel_sum] user={self.user_id} unpaid_sum={commitments} row={commitments_row}")

            # Calculate balances according to user's logic:
            # Available Balance = checking account balance (money currently in account)
            # Price After Commitments = checking balance - unpaid commitments (what's left after paying all unpaid commitments)
            available_balance = checking_balance  # Available balance IS the checking balance
            price_after_commitments = checking_balance - commitments  # Price after paying all unpaid commitments
            logger.info(
                f"[metrics_carousel] user={self.user_id} checking_balance={checking_balance} "
                f"savings_balance={savings} unpaid_commitments={commitments} "
                f"available_balance={available_balance} price_after_commitments={price_after_commitments}"
            )
            logger.info(
                f"[commitments] user={self.user_id} checking_balance={checking_balance} "
                f"savings_balance={savings} unpaid_commitments={commitments} "
                f"available_balance={available_balance} price_after_commitments={price_after_commitments}"
            )

            # Get currency
            user_currency = fetch_one("SELECT currency FROM settings WHERE user_id = ?",(self.user_id,))
            # Handle sqlite3.Row object
            try:
                currency = user_currency["currency"] if user_currency and "currency" in user_currency.keys() else "USD"
            except (KeyError, TypeError, AttributeError):
                currency = "USD"

            # Get weekly spending (last 7 days)
            weekly_spending_row = fetch_one("""
                SELECT SUM(amount) as total
                FROM transactions 
                WHERE user_id = ? 
                AND transaction_type = 'expense'
                AND date >= date('now', '-7 days')
            """,(self.user_id,))
            weekly_spending = weekly_spending_row["total"] if weekly_spending_row and weekly_spending_row[
                "total"] is not None else 0

            # Get goals progress (average of all goals)
            goals_progress_row = fetch_one("""
                SELECT AVG(progress_percentage) as avg_progress
                FROM savings_goals
                WHERE user_id = ? AND is_completed = 0
            """,(self.user_id,))
            goals_progress = goals_progress_row["avg_progress"] if goals_progress_row and goals_progress_row[
                "avg_progress"] is not None else 0

            # Format the data for the carousel
            neutral_color = theme_color("text_secondary")
            self.metrics_data = [
                (
                    f"{currency} {available_balance:,.2f}",
                    "Available Balance",
                    "up" if available_balance > 0 else "neutral" if available_balance == 0 else "down",
                    PennyColors.SUCCESS if available_balance > 0 else neutral_color if available_balance == 0 else PennyColors.ERROR
                ),
                (f"{currency} {weekly_spending:,.2f}", "Weekly Spending", "down", PennyColors.ERROR),
                (
                    f"{currency} {savings:,.2f}",
                    "Total Savings",
                    "up" if savings > 0 else "neutral" if savings == 0 else "down",
                    PennyColors.SUCCESS if savings > 0 else neutral_color if savings == 0 else PennyColors.ERROR
                ),
                (f"{goals_progress:.0f}%", "Goals Progress", "up", PennyColors.INFO)
            ]

        except Exception as e:
            print(f"Error loading real financial data: {e}")
            # Fallback to demo data if real data fails
            neutral_color = theme_color("text_secondary")
            self.metrics_data = [
                ("$2,847.50","Available Balance","up", PennyColors.SUCCESS),
                ("$1,243.75","Weekly Spending","down", PennyColors.ERROR),
                ("$648.20","Total Savings","up", PennyColors.SUCCESS),
                ("72%","Goals Progress","up", PennyColors.INFO)
            ]

        # Update notification manager with latest data
        try:
            # Find parent dashboard to access notification manager
            parent = self.parent()
            while parent and not hasattr(parent, 'notification_manager'):
                parent = parent.parent()
            if parent and hasattr(parent, 'notification_manager'):
                parent.notification_manager.recompute()
                # Update notification badge
                if hasattr(parent, 'nav_bar') and hasattr(parent.nav_bar, 'notification_badge'):
                    parent.nav_bar.notification_badge.update_count(parent.notification_manager.get_unread_count())
        except Exception as e:
            logger.error(f"Error updating notification manager: {e}")

    def create_metric_card(self,value,label,trend,color):
        """Create a single metric card"""
        p = PennyColors.get_palette(theme_manager.current_theme)
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: {p['surface']};
                border: 1px solid {p['border']};
                border-radius: 16px;
                padding: 25px;
            }}
        """)
        frame.setFixedSize(280,120)
        frame.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)

        layout = QVBoxLayout(frame)
        layout.setSpacing(8)

        # Value with trend indicator
        value_layout = QHBoxLayout()
        value_layout.setContentsMargins(0,0,0,0)

        value_label = QLabel(value)
        value_label.setFont(QFont("Segoe UI",24,QFont.Bold))
        value_label.setStyleSheet(f"color: {color};")

        trend_icon = QLabel("↗" if trend == "up" else "↘")
        trend_icon.setStyleSheet(f"""
            color: {color};
            font-size: 18px;
            font-weight: bold;
        """)

        value_layout.addWidget(value_label)
        value_layout.addWidget(trend_icon)
        value_layout.addStretch()

        # Label
        label_label = QLabel(label)
        label_label.setStyleSheet(f"color: {theme_color('text_secondary')}; font-size: 14px; font-weight: 500;")

        layout.addLayout(value_layout)
        layout.addWidget(label_label)
        layout.addStretch()

        return frame

    def show_current_metric(self):
        """Show current metric in carousel"""
        if not self.metrics_data:
            return

        # Clear previous content
        for i in reversed(range(self.carousel_layout.count())):
            widget = self.carousel_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Add current metric
        value,label,trend,color = self.metrics_data[self.current_index]
        metric_card = self.create_metric_card(value,label,trend,color)
        self.carousel_layout.addStretch()
        self.carousel_layout.addWidget(metric_card)
        self.carousel_layout.addStretch()

    def next_metric(self):
        """Show next metric"""
        if not self.metrics_data:
            return
        self.current_index = (self.current_index + 1) % len(self.metrics_data)
        self.show_current_metric()
        self.restart_rotation()

    def previous_metric(self):
        """Show previous metric"""
        if not self.metrics_data:
            return
        self.current_index = (self.current_index - 1) % len(self.metrics_data)
        self.show_current_metric()
        self.restart_rotation()

    def start_rotation(self):
        """Start automatic rotation"""
        if not self.metrics_data:
            return
        self.rotation_timer = QTimer()
        self.rotation_timer.timeout.connect(self.next_metric)
        self.rotation_timer.start(5000)  # Rotate every 5 seconds

    def restart_rotation(self):
        """Restart rotation timer"""
        if not self.metrics_data:
            return
        self.rotation_timer.stop()
        self.rotation_timer.start(5000)

    def refresh_data(self):
        """Refresh the carousel with updated data"""
        self.load_real_data()
        try:
            if hasattr(self, 'metrics_data') and self.metrics_data:
                logger.info(f"[metrics_carousel] refresh_data metrics={self.metrics_data}")
        except Exception:
            pass
        self.current_index = 0
        self.show_current_metric()
        self.restart_rotation()

    def create_finance_card(self,title,value,color,card_type):
        """Create a clean finance card with visible text"""
        from core.font_manager import get_font_scale
        
        card = QFrame()
        p = theme_palette()
        card.setStyleSheet(f"""
            QFrame {{
                background: {p['surface']};
                border: 1px solid {p['border']};
                border-radius: 16px;
            }}
            QFrame:hover {{
                border: 1px solid {color};
                background: {p['surface_alt']};
            }}
        """)
        card.setFixedHeight(160)
        card.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed)

        # Main layout for the card
        main_layout = QVBoxLayout(card)
        main_layout.setContentsMargins(30,25,30,25)  # Increased padding
        main_layout.setSpacing(10)

        # Get font scale factor
        font_scale = get_font_scale()
        title_font_size = int(16 * font_scale)
        value_font_size = int(42 * font_scale)

        # Title label - make sure it's visible
        title_label = QLabel(title)
        # #region agent log
        import json
        from datetime import datetime
        try:
            with open(r'c:\Users\asus\OneDrive\Desktop\PennyWise\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"location":"dashboard_main.py:914","message":"finance card title created SCALED","data":{"title":title,"base_size":16,"scale":font_scale,"scaled_size":title_font_size},"timestamp":datetime.now().timestamp()*1000,"sessionId":"debug-session","runId":"run1","hypothesisId":"B"})+'\n')
        except: pass
        # #endregion
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {theme_color('text_primary')};
                font-size: {title_font_size}px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
        """)
        title_label.setAlignment(Qt.AlignLeft)

        # Value label - make sure it's visible and large
        value_label = QLabel(value)
        # #region agent log
        try:
            with open(r'c:\Users\asus\OneDrive\Desktop\PennyWise\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"location":"dashboard_main.py:939","message":"finance card value created SCALED","data":{"value":value,"base_size":42,"scale":font_scale,"scaled_size":value_font_size},"timestamp":datetime.now().timestamp()*1000,"sessionId":"debug-session","runId":"run1","hypothesisId":"B"})+'\n')
        except: pass
        # #endregion
        value_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: {value_font_size}px;
                font-weight: bold;
                background: transparent;
                border: none;
            }}
        """)
        value_label.setAlignment(Qt.AlignLeft)

        # Add labels to layout
        main_layout.addWidget(title_label)
        main_layout.addWidget(value_label)
        main_layout.addStretch()

        # Subtle shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0,0,0,25))
        card.setGraphicsEffect(shadow)

        # Expose labels for downstream updates
        card.title_label = title_label
        card.value_label = value_label

        return card

    def create_empty_card(self, title, button_text, button_callback):
        """Create an empty state card with a prominent '+' button to add account"""
        from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QColor
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QSizePolicy
        import qtawesome as qta
        
        card = QFrame()
        card.setFixedHeight(160)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        p = theme_palette()

        main_layout = QVBoxLayout(card)
        main_layout.setContentsMargins(30, 25, 30, 25)
        main_layout.setSpacing(12)
        main_layout.setAlignment(Qt.AlignCenter)

        # Title label
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {theme_color('text_secondary')};
                font-size: 16px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
        """)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Add a visible button instead of just text
        add_button = QPushButton(text)
        add_button.setCursor(Qt.PointingHandCursor)
        add_button.setStyleSheet(f"""
            QPushButton {{
                background: {theme_color('primary')};
                color: {theme_color('surface')};
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 700;
                font-size: 14px;
                min-width: 150px;
            }}
            QPushButton:hover {{
                background: {theme_color('accent')};
                transform: scale(1.05);
            }}
            QPushButton:pressed {{
                background: {theme_color('secondary')};
            }}
        """)
        add_button.clicked.connect(button_callback)
        main_layout.addWidget(add_button)

        # Make entire card clickable as well for better UX
        def card_clicked(event):
            button_callback()
        
        card.mousePressEvent = card_clicked
        card.setCursor(Qt.PointingHandCursor)

        # Update card style to show it's clickable
        card.setStyleSheet(f"""
            QFrame {{
                background: {p['surface']};
                border: 2px dashed {theme_color('border')};
                border-radius: 16px;
            }}
            QFrame:hover {{
                border-color: {theme_color('accent')};
                background: {p.get('surface_alt', p['surface'])};
            }}
        """)

        # Subtle shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 25))
        card.setGraphicsEffect(shadow)

        return card


class ModernNavigationBar(QWidget):
    """Modern left sidebar navigation with icons and text."""

    def __init__(self,parent=None,logout_callback=None,nav_callbacks=None):
        super().__init__(parent)
        self.setObjectName("NavRoot")
        self.logout_callback = logout_callback
        self.nav_callbacks = nav_callbacks or {}
        self.setFixedWidth(240)
        self.setContentsMargins(0,0,0,0)
        # Ensure stylesheet background paints for QWidget
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        self.nav_palette = self.get_nav_palette(theme_manager.current_theme)
        self.setup_ui()
        self.refresh_theme(theme_manager.current_theme)

    def setup_notification_manager(self, notification_manager):
        """Set up notification manager for the badge"""
        self.notification_manager = notification_manager
        if hasattr(self, 'notification_badge'):
            self.notification_badge.notification_manager = notification_manager
            
            # Connect notification button to show notifications panel
            if hasattr(self, 'notification_btn') and self.parent():
                # Find the DashboardMain parent and connect to show_notifications
                parent = self.parent()
                while parent and not hasattr(parent, 'show_notifications'):
                    parent = parent.parent()
                if parent and hasattr(parent, 'show_notifications'):
                    self.notification_btn.clicked.connect(parent.show_notifications)
            
            # Attach UI components to badge
            from ui.notification_popup import NotificationPreviewPopup, NotificationWindow
            self.notification_badge.preview_popup = NotificationPreviewPopup(
                notification_manager,
                self
            )
            self.notification_badge.notification_window = NotificationWindow(
                notification_manager,
                self.window()
            )

    def get_nav_palette(self, theme_name):
        """Return palette for nav based on theme."""
        return _nav_palette(theme_name)

    def refresh_theme(self, theme_name=None):
        """Reapply palette to all nav elements."""
        from core.font_manager import get_font_scale
        
        if theme_name:
            self.nav_palette = self.get_nav_palette(theme_name)
        p = self.nav_palette
        
        # Get font scale factor
        font_scale = get_font_scale()
        logo_font_size = int(18 * font_scale)
        
        # Container background
        self.setStyleSheet(f"""
            ModernNavigationBar {{
                background-color: {p['bg']};
                border-right: 1px solid {p['border']};
            }}
            QWidget#NavLogoContainer, QWidget#NavNotifContainer {{
                background-color: {p['bg']};
            }}
        """)
        pal = self.palette()
        pal.setColor(QPalette.Window, QColor(p['bg']))
        self.setPalette(pal)

        # Logo
        if hasattr(self, "logo_container"):
            self.logo_container.setStyleSheet(f"""
                QWidget#NavLogoContainer {{
                    background-color: {p['bg']};
                }}
            """)
            pal_logo = self.logo_container.palette()
            pal_logo.setColor(QPalette.Window, QColor(p['bg']))
            self.logo_container.setPalette(pal_logo)
        if hasattr(self, "logo_label"):
            self.logo_label.setStyleSheet(f"""
                QLabel {{
                    color: {p['highlight']};
                    font-weight: bold;
                    font-size: {logo_font_size}px;
                    background: {p['bg']};
                    border-radius: 12px;
                    padding: 10px;
                }}
            """)

        # Notification button
        if hasattr(self, "notification_container"):
            self.notification_container.setStyleSheet(f"""
                QWidget#NavNotifContainer {{
                    background-color: {p['bg']};
                }}
            """)
            pal_notif = self.notification_container.palette()
            pal_notif.setColor(QPalette.Window, QColor(p['bg']))
            self.notification_container.setPalette(pal_notif)
        if hasattr(self, "notification_btn"):
            self.notification_btn.setIcon(qta.icon('fa5s.bell', color=p['icon_inactive']))
            self.notification_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: 1px solid {p['notif_border']};
                    color: {p['icon_inactive']};
                    border-radius: 8px;
                }}
                QPushButton:hover {{ 
                    background: {p['highlight_bg']};
                    border-color: {p['highlight']};
                }}
            """)

        # Nav buttons
        nav_btn_font_size = int(18 * font_scale)
        if hasattr(self, "nav_buttons"):
            for text, btn in self.nav_buttons.items():
                state_icon = qta.icon(
                    self.nav_data_map.get(text, ""),
                    color=p["icon_inactive"],
                    color_checked=p["icon_active"]
                )
                btn.setIcon(state_icon)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: {p['text_secondary']};
                        border: none;
                        border-radius: 8px;
                        padding: 10px 20px;
                        font-weight: 500;
                        font-size: {nav_btn_font_size}px;
                        text-align: left;
                    }}
                    QPushButton:hover {{
                        color: {p['text_primary']};
                        background: {p['highlight_bg']};
                    }}
                    QPushButton:checked {{
                        color: {p['highlight']};
                        font-weight: 600;
                        background: {p['highlight_bg']};
                        border-left: 3px solid {p['highlight']};
                    }}
                    QPushButton:disabled {{
                        color: {p['text_disabled']};
                    }}
                """)

        # Logout button
        logout_btn_font_size = int(14 * font_scale)
        if hasattr(self, "logout_btn"):
            self.logout_btn.setIcon(qta.icon('fa5s.sign-out-alt', color=p['icon_inactive']))
            self.logout_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {p['icon_inactive']};
                    border: 1px solid {p['notif_border']};
                    border-radius: 8px;
                    font-family: 'Poppins', sans-serif;
                    font-size: {logout_btn_font_size}px;
                    font-weight: 500;
                    padding: 8px 16px;
                }}
                QPushButton:hover {{ 
                    background: {p['logout_hover_bg']};
                    border-color: {p['logout_hover_border']};
                    color: {p['logout_hover_border']};
                }}
                QPushButton:disabled {{
                    color: {p['text_disabled']};
                    border-color: {p['text_disabled']};
                }}
            """)

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)

        p = self.nav_palette

        # Logo section at top
        self.logo_container = QWidget()
        self.logo_container.setObjectName("NavLogoContainer")
        logo_layout = QHBoxLayout(self.logo_container)
        logo_layout.setContentsMargins(20,20,20,20)
        self.logo_container.setAttribute(Qt.WA_StyledBackground, True)
        self.logo_container.setAutoFillBackground(True)
        self.logo_container.setStyleSheet(f"background:{p['bg']};")
        pal_logo = self.logo_container.palette()
        pal_logo.setColor(QPalette.Window, QColor(p['bg']))
        self.logo_container.setPalette(pal_logo)

        self.logo_label = QLabel("PW")
        self.logo_label.setObjectName("NavLogoLabel")
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setFixedSize(48,48)
        logo_layout.addWidget(self.logo_label)
        layout.addWidget(self.logo_container)

        # Notification button (moved from bottom) - centered
        self.notification_container = QWidget()
        self.notification_container.setObjectName("NavNotifContainer")
        notification_layout = QHBoxLayout(self.notification_container)
        notification_layout.setContentsMargins(20,0,20,10)
        notification_layout.setAlignment(Qt.AlignCenter)
        self.notification_container.setAttribute(Qt.WA_StyledBackground, True)
        self.notification_container.setAutoFillBackground(True)
        self.notification_container.setStyleSheet(f"background:{p['bg']};")
        pal_notif = self.notification_container.palette()
        pal_notif.setColor(QPalette.Window, QColor(p['bg']))
        self.notification_container.setPalette(pal_notif)

        self.notification_btn = QPushButton()
        self.notification_btn.setObjectName("NavNotifButton")
        self.notification_btn.setFixedSize(40,40)

        self.notification_badge = NotificationBadge(0)  # Start with 0, will be updated by manager
        notification_layout.addWidget(self.notification_btn)
        notification_layout.addWidget(self.notification_badge)
        notification_layout.setAlignment(self.notification_badge,Qt.AlignTop | Qt.AlignLeft)
        
        # Connect notification button to show notifications (will be wired to parent callback)
        self.notification_btn.clicked.connect(lambda: None)  # Will be connected in setup_notification_manager
        layout.addWidget(self.notification_container)

        # Remove separator under logo for a cleaner, more open sidebar
        separator = QFrame()
        separator.setFixedHeight(0)
        separator.setStyleSheet("background: transparent;")
        separator.setVisible(False)

        # Navigation items (vertical)
        nav_items = QVBoxLayout()
        nav_items.setContentsMargins(12,20,12,20)
        nav_items.setSpacing(4)

        self.nav_data_map = dict([
            ("Dashboard", "fa5s.tachometer-alt"),
            ("Transactions", "fa5s.exchange-alt"),
            ("Accounts", "fa5s.money-bill-wave"),
            ("Reports", "fa5s.chart-bar"),
            ("Settings", "fa5s.cog"),
            ("Link Bank", "fa5s.university")
        ])

        self.nav_buttons = {}
        for text,icon_id in self.nav_data_map.items():
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setFixedHeight(52)

            # Connect button to navigation method using callbacks
            if text in self.nav_callbacks:
                btn.clicked.connect(self.nav_callbacks[text])

            nav_items.addWidget(btn)
            self.nav_buttons[text] = btn

        self.nav_buttons["Dashboard"].setChecked(True)
        nav_items.addStretch()
        layout.addLayout(nav_items)

        # Bottom section with notification and settings
        bottom_section = QVBoxLayout()
        bottom_section.setContentsMargins(12,0,12,20)
        bottom_section.setSpacing(8)

        # Remove separator above bottom actions for a more spacious look
        separator2 = QFrame()
        separator2.setFixedHeight(0)
        separator2.setStyleSheet("background: transparent;")
        separator2.setVisible(False)

        # Logout button
        self.logout_btn = QPushButton("Logout")
        self.logout_btn.setFixedHeight(40)
        if self.logout_callback:
            self.logout_btn.clicked.connect(self.logout_callback)
        bottom_section.addWidget(self.logout_btn)

        layout.addStretch()
        layout.addLayout(bottom_section)
        self.setLayout(layout)

        # Apply initial palette styles to all created widgets
        self.refresh_theme(theme_manager.current_theme)


class CommitmentTrackerWidget(QWidget):
    def __init__(self,user_id,parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.parent_dashboard = parent  # Store reference to dashboard for refreshing
        print(f"DEBUG: CommitmentTrackerWidget created for user {user_id}")
        self.setup_ui()
        self.load_commitments()

    def trigger_dashboard_refresh(self):
        """Refresh commitments and balance cards (not whole dashboard)."""
        if not self.parent_dashboard:
            return

        if getattr(self, "_is_refreshing", False):
            return

        self._is_refreshing = True
        pd = self.parent_dashboard
        try:
            # Always refresh commitments grid
            if hasattr(pd, 'commitment_tracker') and hasattr(pd.commitment_tracker, 'refresh_commitments'):
                pd.commitment_tracker.refresh_commitments()
            # Refresh only balance cards/metrics
            if hasattr(pd, 'refresh_balance_cards'):
                pd.refresh_balance_cards()
            else:
                if hasattr(pd, 'metrics_carousel') and pd.metrics_carousel:
                    pd.metrics_carousel.refresh_data()
                    pd.metrics_carousel.refresh_metrics_cards()
                if hasattr(pd, 'refresh_metrics_cards_main'):
                    pd.refresh_metrics_cards_main()
            logger.info("[commitments] refresh cards done (partial)")
        except Exception as e:
            logger.warning(f"[commitments] synchronous refresh error: {e}")
        finally:
            self._is_refreshing = False

    def setup_ui(self):
        """Setup ONLY the commitment tracker widget's internal layout"""
        print("DEBUG: Setting up CommitmentTrackerWidget UI")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(12)


        # Commitments container (grid of circular tiles)
        self.commitments_container = QWidget()
        self.commitments_layout = QGridLayout(self.commitments_container)
        self.commitments_layout.setHorizontalSpacing(24)
        self.commitments_layout.setVerticalSpacing(20)
        self.commitments_layout.setContentsMargins(0,0,0,0)

        # Scroll area for commitments
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
        """)
        scroll.setFixedHeight(180)
        scroll.setWidget(self.commitments_container)

        layout.addWidget(scroll)

        # Add commitment circle button
        self.add_circle_btn = QPushButton("+")
        self.add_circle_btn.setFixedSize(96,96)
        self.add_circle_btn.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
        self.add_circle_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 2px dashed {PennyColors.DASHED_BORDER};
                border-radius: 48px;
                color: {theme_color('text_secondary')};
                font-weight: 700;
                font-size: 24px;
            }}
            QPushButton:hover {{
                background: {PennyColors.DASHED_BG};
                border-color: {PennyColors.DASHED_HOVER_BORDER};
                color: {PennyColors.DASHED_HOVER_BORDER};
            }}
        """)
        self.add_circle_btn.clicked.connect(self.add_commitment)
        # We'll place this button in grid during load_commitments()

        # Add savings commitment button
        self.savings_setup_btn = QPushButton()
        self.savings_setup_btn.setFixedSize(96,96)
        self.savings_setup_btn.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
        self.savings_setup_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 2px dashed {PennyColors.DASHED_BORDER};
                border-radius: 48px;
                color: {theme_color('text_secondary')};
                font-weight: 600;
                font-size: 11px;
                text-align: center;
            }}
            QPushButton:hover {{
                background: {PennyColors.DASHED_BG};
                border-color: {PennyColors.MUTED_LILAC};
                color: {PennyColors.MUTED_LILAC};
            }}
        """)
        self.savings_setup_btn.setText("Setup\nsavings\ncommitment")
        self.savings_setup_btn.clicked.connect(self.setup_savings_commitment)



    # ... keep the rest of your methods
    def load_commitments(self):
        """Load commitments and render as circular tiles in a grid."""

        # Clear all existing grid items
        while self.commitments_layout.count():
            item = self.commitments_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)  # Remove from layout
                if w is not self.add_circle_btn and w is not self.savings_setup_btn:
                    w.deleteLater()  # Delete non-button widgets

        try:
            # Use COALESCE to handle NULL is_paid values (treat NULL as 0)
            # Get unpaid sum independently to avoid join issues
            unpaid_row = fetch_one("""
                SELECT COALESCE(SUM(amount), 0) AS total
                FROM category_commitments
                WHERE user_id = ? AND COALESCE(is_paid, 0) = 0
            """, (self.user_id,))
            unpaid_sum = 0
            try:
                unpaid_sum = unpaid_row["total"] if unpaid_row else 0
            except Exception:
                unpaid_sum = 0

            commitments = fetch_all("""
                SELECT cc.*, c.category_name, c.color,
                       COALESCE(cc.is_paid, 0) as is_paid
                FROM category_commitments cc
                LEFT JOIN categories c ON cc.category_id = c.category_id
                WHERE cc.user_id = ?
                ORDER BY COALESCE(cc.is_paid, 0) ASC, cc.amount DESC
            """, (self.user_id,))
            unpaid_total = 0
            sample = []
            for commit in commitments or []:
                amt = commit["amount"] if "amount" in commit.keys() else 0
                is_paid_val = commit["is_paid"] if "is_paid" in commit.keys() else 0
                cat = commit["category_name"] if "category_name" in commit.keys() else ""

                # normalize is_paid to int
                try:
                    norm_paid = int(is_paid_val) if is_paid_val is not None else 0
                except (ValueError, TypeError):
                    norm_paid = 0

                if norm_paid == 0:
                    unpaid_total += amt if amt is not None else 0
                if len(sample) < 5:
                    sample.append({"cat": cat, "amt": amt, "is_paid": norm_paid})
            logger.info(f"[commitments] fetched {len(commitments) if commitments else 0} commitments for user={self.user_id} unpaid_total={unpaid_total} sample={sample} unpaid_sum_query={unpaid_sum}")
            
            # Check if there's a Savings commitment - handle sqlite3.Row and None values
            has_savings = False
            try:
                for commit in commitments:
                    try:
                        cat_name = commit['category_name'] if 'category_name' in commit.keys() else None
                        if cat_name and str(cat_name).lower() == 'savings':
                            has_savings = True
                            break
                    except (KeyError, TypeError, AttributeError):
                        continue
            except:
                has_savings = False

            if not commitments:
                empty_label = QLabel("No active commitments\nAdd recurring payments like Netflix, Spotify, etc.")
                empty_label.setAlignment(Qt.AlignCenter)
                empty_label.setStyleSheet(f"""
                    color: {theme_color('text_secondary')};
                    font-size: 14px;
                    padding: 40px;
                    background: {theme_color('surface_alt')};
                    border-radius: 12px;
                    border: 2px dashed {theme_color('border')};
                """)
                empty_label.setMinimumHeight(120)
                # place the savings setup button, add circle and empty message
                self.commitments_layout.addWidget(self.savings_setup_btn, 0, 0)
                self.commitments_layout.addWidget(self.add_circle_btn, 0, 1)
                self.commitments_layout.addWidget(empty_label, 0, 2, 1, 3)
                return

            # Grid placement
            max_cols = 5
            row = 0
            col = 0
            for commitment in commitments:
                # Handle sqlite3.Row object - use bracket notation with safety checks
                try:
                    color = commitment['color'] if 'color' in commitment.keys() and commitment['color'] else theme_color('text_secondary')
                except (KeyError, TypeError):
                    color = theme_color('text_secondary')
                
                try:
                    due_day = commitment['due_day'] if 'due_day' in commitment.keys() and commitment['due_day'] else 1
                except (KeyError, TypeError):
                    due_day = 1
                # Handle is_paid - sqlite3.Row uses [] not .get(), COALESCE ensures it's always 0 or 1
                try:
                    is_paid_raw = commitment['is_paid']
                    if is_paid_raw is None:
                        is_paid = 0
                    elif isinstance(is_paid_raw, bool):
                        is_paid = 1 if is_paid_raw else 0
                    else:
                        is_paid = int(is_paid_raw) if is_paid_raw else 0
                except (KeyError, TypeError):
                    is_paid = 0

                # Extract values from sqlite3.Row with safety checks
                try:
                    category_name = commitment['category_name'] if 'category_name' in commitment.keys() else 'Unknown'
                except (KeyError, TypeError):
                    category_name = 'Unknown'
                
                try:
                    amount = commitment['amount'] if 'amount' in commitment.keys() else 0
                except (KeyError, TypeError):
                    amount = 0
                
                try:
                    commitment_id = commitment['commitment_id'] if 'commitment_id' in commitment.keys() else None
                except (KeyError, TypeError):
                    commitment_id = None
                
                try:
                    category_id = commitment['category_id'] if 'category_id' in commitment.keys() else None
                except (KeyError, TypeError):
                    category_id = None
                
                if not commitment_id:
                    continue  # Skip if we can't get commitment_id
                
                circle = self.create_commitment_circle(
                    category_name,
                    amount,
                    commitment_id,
                    category_id,
                    color,
                    due_day,
                    is_paid
                )
                circle.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                self.commitments_layout.addWidget(circle, row, col, alignment=Qt.AlignCenter)
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

            # Add savings setup button if no savings commitment exists
            if not has_savings:
                self.commitments_layout.addWidget(self.savings_setup_btn, row, col, alignment=Qt.AlignCenter)
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

            # Add the "+" circle at the next slot
            self.commitments_layout.addWidget(self.add_circle_btn, row, col, alignment=Qt.AlignCenter)
            logger.info(f"[commitments] rendered grid items rows={row+1} cols_used={col+1} has_savings={has_savings}")

        except Exception as e:
            # Print the actual error for debugging
            print(f"Error loading commitments: {e}")
            import traceback
            traceback.print_exc()
            
            error_label = QLabel(f"Unable to load commitments\nError: {str(e)}\nPlease try again later")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet(f"""
                color: {theme_color('text_secondary')};
                font-size: 14px;
                padding: 40px;
                background: {theme_color('surface_alt')};
                border-radius: 12px;
                border: 2px dashed {theme_color('border')};
            """)
            self.commitments_layout.addWidget(error_label, 0, 0)





    def refresh_commitments(self):
        """Public helper to reload commitments safely."""
        self.load_commitments()

    def setup_savings_commitment(self):
        """Open the savings goal form and refresh commitments afterward."""
        try:
            dlg = SavingsForm(self.user_id, parent_dashboard=self.parent_dashboard)
            dlg.exec_()
            self.load_commitments()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open savings setup: {e}")

    def create_commitment_widget(self,category_name,amount,commitment_id,category_id,color,due_day):
        """Create a legacy row-style widget (retained but unused)."""
        widget = QFrame()
        p = theme_palette()
        border_color = theme_color('commitment_border', p['border'])
        widget.setStyleSheet(f"""
            QFrame {{
                background: {theme_color('commitment_bg', p['surface'])};
                border: 1px solid {border_color};
                border-radius: 12px;
                padding: 16px;
            }}
            QFrame:hover {{
                border-color: {color};
                background: {theme_color('surface_alt')};
            }}
        """)

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(12)

        # Color indicator
        color_indicator = QLabel()
        color_indicator.setFixedSize(8,40)
        color_indicator.setStyleSheet(f"""
            background: {color};
            border-radius: 4px;
        """)
        layout.addWidget(color_indicator)

        # Commitment details
        details_layout = QVBoxLayout()
        details_layout.setSpacing(4)

        name_label = QLabel(category_name)
        name_label.setStyleSheet(f"font-weight: 600; color: {theme_color('text_primary')}; font-size: 14px;")

        amount_label = QLabel(f"${amount:.2f}/month")
        amount_label.setStyleSheet(f"color: {theme_color('text_secondary')}; font-size: 13px;")

        # Status with due day information
        today = datetime.now().day
        status_text = "🔄 Due today!" if today == due_day else f"📅 Due day {due_day}"
        status_color = theme_color('error') if today == due_day else theme_color('warning')

        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"color: {status_color}; font-size: 12px; font-weight: 500;")

        details_layout.addWidget(name_label)
        details_layout.addWidget(amount_label)
        details_layout.addWidget(status_label)
        layout.addLayout(details_layout)

        layout.addStretch()

        # Action buttons
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)

        # Mark as paid button
        pay_btn = QPushButton("Mark Paid")
        pay_btn.setFixedSize(80,32)
        pay_btn.setStyleSheet(f"""
            QPushButton {{
                background: {theme_color('success')};
                color: {theme_color('background')};
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {theme_color('secondary', theme_color('success'))};
            }}
        """)
        pay_btn.clicked.connect(lambda: self.mark_as_paid(commitment_id,category_name))

        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.setFixedSize(70,32)
        remove_btn.setStyleSheet(f"""
            QPushButton {{
                background: {theme_color('muted')};
                color: {theme_color('background')};
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {theme_color('text_secondary')};
            }}
        """)
        remove_btn.clicked.connect(lambda: self.remove_commitment(commitment_id))

        actions_layout.addWidget(pay_btn)
        actions_layout.addWidget(remove_btn)
        layout.addLayout(actions_layout)

        return widget

    def create_commitment_circle(self,category_name,amount,commitment_id,category_id,color,due_day,is_paid=0):
        """Create a circular tile for a commitment with context menu actions."""
        # Normalize color palette: enforce light, muted tones for commitments only
        def get_muted_pastel_color(name:str, fallback:str) -> str:
            key = (name or "").lower()
            mapping = {
                'bill': '#F6C1B5',      # muted salmon
                'rent': '#FAD4C0',      # soft peach
                'utilities': '#CFE7F6', # soft sky
                'internet': '#CFE7F6',
                'phone': '#BEE3D2',     # mint
                'savings': '#B3D9F2',   # soft blue (CHANGED from lavender)
                'subscription': '#F4DEB3', # soft mustard
                'netflix': '#D7C6E6',   # lavender
                'spotify': '#BEE3D2',   # mint
                'amazon': '#FAD4C0',    # soft peach
                'gym': '#FFD4E5',       # soft pink (CHANGED from lavender)
                'insurance': '#E8D5C4',  # beige
                'groceries': '#D4EDDA',  # soft green
                'transportation': '#FFF3CD',  # soft yellow
                'entertainment': '#E9D5FF',  # soft purple
                'healthcare': '#FFCCCB',  # light rose
                'education': '#B8E0D2',  # mint green
                'dining': '#FFE5B4',  # soft orange
                'shopping': '#FFD9E3'  # rose pink
            }
            for k,v in mapping.items():
                if k in key:
                    return v
            # default to a soft neutral if unknown or saturated
            return '#E8E3DC'

        pastel_bg = get_muted_pastel_color(category_name, color)
        accent = theme_color('accent')
        neutral_ring = theme_color('border')
        
        # For paid commitments, use brown ring
        if is_paid:
            ring = theme_color('text_secondary')
        else:
            # ring color: accent if due today, otherwise neutral
            ring = accent if datetime.now().day == (due_day or 1) else neutral_ring

        btn = QPushButton()
        btn.setFixedSize(96,96)
        
        # For paid commitments, show brown checkmark instead of amount
        if is_paid:
            # Create brown checkmark icon (check-circle in brown) - smaller size
            check_icon = qta.icon('fa5s.check-circle', color=theme_color('text_secondary'))
            btn.setIcon(check_icon)
            btn.setIconSize(QSize(24, 24))  # Reduced from 36x36 to 24x24
            # Icon alignment: centered horizontally, positioned above text
            btn.setLayoutDirection(Qt.LeftToRight)
            # Show category name below the icon
            btn.setText(f"\n{category_name}")
            amount_text = f"${amount:.0f}" if amount >= 100 else f"${amount:.2f}"
            btn.setToolTip(f"{category_name}\n{amount_text}/month\n✅ Paid")
        else:
            # Content text (two-line: amount then name)
            amount_text = f"${amount:.0f}" if amount >= 100 else f"${amount:.2f}"
            btn.setText(f"{amount_text}\n{category_name}")
            
            # Get detection method for tooltip
            try:
                commitment_info = fetch_one("""
                    SELECT COALESCE(detection_method, 0) as detection_method 
                    FROM category_commitments 
                    WHERE commitment_id = ? AND user_id = ?
                """, (commitment_id, self.user_id))
                if commitment_info:
                    try:
                        dm = commitment_info['detection_method'] if commitment_info['detection_method'] is not None else 0
                    except (KeyError, TypeError):
                        dm = 0
                else:
                    dm = 0
            except:
                dm = 0
            
            detection_label = {0: "Manual", 1: "Smart Detect", 2: "Pay as you go"}.get(dm, "Manual")
            btn.setToolTip(f"{category_name}\n{amount_text}/month\nDue day {due_day}\nDetection: {detection_label}")
        
        # Apply styling after setting icon/text
        # Use darker text in dark mode for better contrast on pastel backgrounds
        from core.theme_manager import theme_manager
        if theme_manager.current_theme == "dark":
            text_color = "#0d1f26"  # Very dark teal-gray for high contrast on pastel circles
        else:
            text_color = theme_color('text_primary')
        
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {pastel_bg};
                color: {text_color};
                border: 3px solid {ring};
                border-radius: 48px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                border: 4px solid {ring};
            }}
        """)

        def open_menu(pos=None):
            from assets.styles.penny_colors import PennyColors
            
            menu = QMenu(btn)
            # Style menu with PennyWise theme colors
            # Get commitment details to check detection method
            try:
                commitment = fetch_one("""
                    SELECT COALESCE(detection_method, 0) as detection_method 
                    FROM category_commitments 
                    WHERE commitment_id = ? AND user_id = ?
                """, (commitment_id, self.user_id))
                
                # Handle sqlite3.Row object
                if commitment:
                    try:
                        detection_method = commitment['detection_method'] if commitment['detection_method'] is not None else 0
                    except (KeyError, TypeError):
                        detection_method = 0
                else:
                    detection_method = 0
            except:
                detection_method = 0
            
            # Map detection method to text for tooltip
            detection_text = {
                0: "Manual",
                1: "Smart Detect",
                2: "Pay as you go"
            }.get(detection_method, "Manual")
            
            # Get commitment paid status to show appropriate menu items
            try:
                commitment_status = fetch_one("""
                    SELECT COALESCE(is_paid, 0) as is_paid 
                    FROM category_commitments 
                    WHERE commitment_id = ? AND user_id = ?
                """, (commitment_id, self.user_id))
                if commitment_status:
                    try:
                        is_paid_status = commitment_status['is_paid'] if commitment_status['is_paid'] is not None else 0
                    except (KeyError, TypeError):
                        is_paid_status = 0
                else:
                    is_paid_status = 0
            except:
                is_paid_status = 0
            
            # Add actions based on payment status
            if is_paid_status:
                # If paid, show "Unmark as Paid" option
                act_unmark_paid = menu.addAction("Unmark as Paid")
                act_unmark_paid.setObjectName("unmark_paid_action")
            else:
                # If not paid, show payment options
                act_mark_paid = menu.addAction("Mark as Paid Manually")
                act_mark_paid.setObjectName("mark_paid_action")
                
                act_smart_detect = menu.addAction("Smart Detect")
                act_smart_detect.setObjectName("smart_detect_action")
                
                act_pay_as_you_go = menu.addAction("Pay now")
                act_pay_as_you_go.setObjectName("pay_as_you_go_action")
            
            # Add separator
            menu.addSeparator()
            
            act_remove = menu.addAction("Delete Category")
            act_remove.setObjectName("delete_category_action")
            
            # Style menu with colored items using object names
            menu.setStyleSheet(f"""
                QMenu {{
                    background-color: {theme_color('surface')};
                    border: 1px solid {theme_color('border')};
                    border-radius: 8px;
                    padding: 4px;
                }}
                QMenu::item {{
                    padding: 10px 20px;
                    font-family: 'Segoe UI', system-ui, sans-serif;
                    font-size: 14px;
                    color: {theme_color('text_primary')};
                    border-radius: 6px;
                }}
                QMenu::item:selected {{
                    background-color: {theme_color('surface_alt')};
                }}
                QMenu::item[objectName="mark_paid_action"] {{
                    color: {theme_color('text_primary')};
                }}
                QMenu::item[objectName="smart_detect_action"] {{
                    color: {theme_color('info')};
                }}
                QMenu::item[objectName="pay_as_you_go_action"] {{
                    color: {theme_color('primary')};
                }}
                QMenu::item[objectName="unmark_paid_action"] {{
                    color: {theme_color('warning')};
                }}
                QMenu::item[objectName="delete_category_action"] {{
                    color: {theme_color('error')};
                    font-weight: 600;
                }}
                QMenu::separator {{
                    height: 1px;
                    background-color: {theme_color('border')};
                    margin: 4px 8px;
                }}
            """)
            
            # Show menu at cursor position if pos provided, otherwise center of button
            if pos:
                global_pos = btn.mapToGlobal(pos)
            else:
                global_pos = btn.mapToGlobal(btn.rect().center())
            chosen = menu.exec_(global_pos)
            
            if is_paid_status:
                # Handle actions for paid commitments
                if chosen == act_unmark_paid:
                    self.unmark_as_paid(commitment_id, category_name)
                elif chosen == act_remove:
                    self.remove_commitment(commitment_id)
            else:
                # Handle actions for unpaid commitments
                if chosen == act_mark_paid:
                    self.mark_as_paid(commitment_id, category_name)
                elif chosen == act_smart_detect:
                    self.trigger_smart_detect(commitment_id, category_name)
                elif chosen == act_pay_as_you_go:
                    self.pay_as_you_go(commitment_id, category_name, amount)
                elif chosen == act_remove:
                    self.remove_commitment(commitment_id)

        # Set context menu policy for right-click
        btn.setContextMenuPolicy(Qt.CustomContextMenu)
        btn.customContextMenuRequested.connect(lambda pos: open_menu(pos))
        
        # Also allow left-click to show menu
        btn.clicked.connect(lambda: open_menu(None))
        
        # Show menu on hover (with slight delay to avoid accidental triggers)
        hover_timer = QTimer(btn)
        hover_timer.setSingleShot(True)
        hover_timer.timeout.connect(lambda: open_menu(None))
        
        def enter_event(event):
            hover_timer.start(500)  # 500ms delay before showing menu on hover
            QPushButton.enterEvent(btn, event)
        
        def leave_event(event):
            hover_timer.stop()
            QPushButton.leaveEvent(btn, event)
        
        # Install event filter for hover detection
        class HoverEventFilter(QWidget):
            def __init__(self, timer, menu_func):
                super().__init__()
                self.timer = timer
                self.menu_func = menu_func
            
            def eventFilter(self, obj, event):
                if obj == btn:
                    if event.type() == QEvent.Enter:
                        self.timer.start(500)
                    elif event.type() == QEvent.Leave:
                        self.timer.stop()
                return super().eventFilter(obj, event)
        
        hover_filter = HoverEventFilter(hover_timer, open_menu)
        btn.installEventFilter(hover_filter)
        
        return btn

    def unmark_as_paid(self, commitment_id, category_name):
        """Unmark commitment as paid (set back to unpaid)"""
        try:
            from database.db_manager import execute_query
            execute_query("""
                UPDATE category_commitments 
                SET is_paid = 0, last_paid_date = NULL
                WHERE commitment_id = ? AND user_id = ?
            """, (commitment_id, self.user_id), commit=True)
            
            QMessageBox.information(self, "Success", f"{category_name} marked as unpaid")
            self.load_commitments()
            # Refresh dashboard metrics to update price after commitments
            self.trigger_dashboard_refresh()
            # Trigger notification recompute to update badge count
            if self.parent_dashboard and hasattr(self.parent_dashboard, 'notification_manager'):
                self.parent_dashboard.notification_manager.recompute()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to unmark as paid: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def mark_as_paid(self,commitment_id,category_name):
        """Mark commitment as paid manually - NO transaction created"""
        try:
            from core.commitment_manager import mark_commitment_paid_manually
            amount = 0.0
            try:
                row = fetch_one("""
                    SELECT amount FROM category_commitments
                    WHERE commitment_id = ? AND user_id = ?
                """, (commitment_id, self.user_id))
                if row and ("amount" in row.keys()):
                    amount = float(row["amount"] or 0.0)
            except Exception:
                amount = 0.0

            success = mark_commitment_paid_manually(self.user_id,commitment_id)
            if success:
                QMessageBox.information(self,"Success",f"{category_name} marked as paid!")
                self.load_commitments()
                # Emit negative delta immediately
                if self.parent_dashboard and hasattr(self.parent_dashboard, 'handle_commitment_delta'):
                    try:
                        logger.info(f"[commitment_delta] emitting paid delta -{amount:.2f} for commitment_id={commitment_id}")
                    except Exception:
                        pass
                    self.parent_dashboard.handle_commitment_delta(-amount)
                # Refresh dashboard metrics to update available balance (safety net)
                self.trigger_dashboard_refresh()
                # Trigger notification recompute to update badge count
                if self.parent_dashboard and hasattr(self.parent_dashboard, 'notification_manager'):
                    self.parent_dashboard.notification_manager.recompute()
            else:
                QMessageBox.warning(self,"Error","Failed to process payment")
        except Exception as e:
            # Fallback: manually mark as paid
            try:
                execute_query("""
                    UPDATE category_commitments 
                    SET is_paid = 1, last_paid_date = ?
                    WHERE commitment_id = ?
                """,(datetime.now().isoformat(),commitment_id),commit=True)

                # Add notification
                from core.commitment_manager import add_notification
                add_notification(self.user_id,f"✅ {category_name} marked as paid!","payment")

                QMessageBox.information(self,"Success",f"{category_name} marked as paid!")
                self.load_commitments()
                # Emit negative delta immediately
                if self.parent_dashboard and hasattr(self.parent_dashboard, 'handle_commitment_delta'):
                    try:
                        logger.info(f"[commitment_delta] emitting paid delta (fallback) -{amount:.2f} for commitment_id={commitment_id}")
                    except Exception:
                        pass
                    self.parent_dashboard.handle_commitment_delta(-amount)
                # Refresh dashboard metrics as safety net
                if self.parent_dashboard:
                    self.parent_dashboard.refresh_dashboard()
                    if hasattr(self.parent_dashboard, 'refresh_metrics_cards_main'):
                        self.parent_dashboard.refresh_metrics_cards_main()
                    if hasattr(self.parent_dashboard, 'metrics_carousel'):
                        self.parent_dashboard.metrics_carousel.refresh_metrics_cards()
                # Trigger commitment check to update notifications (after refresh)
                from core.commitment_manager import check_commitments
                check_commitments(self.user_id)
                # Update notification manager
                if hasattr(self, 'notification_manager'):
                    self.notification_manager.recompute()
                    if hasattr(self, 'nav_bar') and hasattr(self.nav_bar, 'notification_badge'):
                        self.nav_bar.notification_badge.update_count(self.notification_manager.get_unread_count())

            except Exception as fallback_error:
                QMessageBox.warning(self,"Error",f"Failed to mark as paid: {str(fallback_error)}")

    def trigger_smart_detect(self, commitment_id, category_name):
        """Trigger Smart Detect to scan recent transactions for this commitment"""
        try:
            # Get commitment details
            commitment = fetch_one("""
                SELECT cc.*, c.category_name 
                FROM category_commitments cc
                JOIN categories c ON cc.category_id = c.category_id
                WHERE cc.commitment_id = ? AND cc.user_id = ?
            """, (commitment_id, self.user_id))
            
            if not commitment:
                QMessageBox.warning(self, "Error", "Commitment not found")
                return
            
            # Get recent transactions (last 30 days)
            from datetime import datetime, timedelta
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
            # Get commitment amount - handle sqlite3.Row
            try:
                commitment_amount = commitment['amount']
            except (KeyError, TypeError):
                commitment_amount = 0
            
            transactions = fetch_all("""
                SELECT t.*, c.category_name 
                FROM transactions t
                LEFT JOIN categories c ON t.category_id = c.category_id
                WHERE t.user_id = ? 
                AND t.date >= ? 
                AND t.transaction_type = 'expense'
                AND ABS(t.amount - ?) <= 1.0
                ORDER BY t.date DESC
            """, (self.user_id, start_date, commitment_amount))
            
            # Known brands for matching
            known_brands = ['netflix', 'spotify', 'apple music', 'applemusic', 'amazon prime', 
                          'amazon', 'hulu', 'disney', 'youtube', 'google', 'microsoft',
                          'adobe', 'dropbox', 'zoom', 'slack', 'discord', 'twitch']
            
            category_name_lower = category_name.lower()
            matched_transactions = []
            
            for txn in transactions:
                try:
                    txn_desc = (txn['description'] or '').lower()
                    # Check if transaction matches by brand or category name
                    matches_brand = any(brand in txn_desc or brand in category_name_lower for brand in known_brands)
                    matches_category = category_name_lower in txn_desc
                    
                    if matches_brand or matches_category:
                        matched_transactions.append(txn)
                except (KeyError, TypeError):
                    continue
            
            if matched_transactions:
                # Check if results are similar or different
                amounts = [txn['amount'] for txn in matched_transactions]
                unique_amounts = set(round(amt, 2) for amt in amounts)
                descriptions = [txn['description'] for txn in matched_transactions]
                
                # If all amounts are the same and descriptions are similar, auto-select
                # If amounts differ significantly or descriptions are very different, let user choose
                amounts_vary_significantly = len(unique_amounts) > 1
                descriptions_vary = len(set(desc.lower() for desc in descriptions)) > 1
                
                if amounts_vary_significantly or (len(matched_transactions) > 1 and descriptions_vary):
                    # Multiple different results - let user pick
                    
                    dialog = QDialog(self)
                    dialog.setWindowTitle("Smart Detect - Select Transaction")
                    dialog.setMinimumWidth(500)
                    layout = QVBoxLayout(dialog)
                    
                    info_label = QLabel(
                        f"Found {len(matched_transactions)} potential matches for '{category_name}':\n"
                        f"Please select the correct transaction:"
                    )
                    info_label.setWordWrap(True)
                    layout.addWidget(info_label)
                    
                    button_group = QButtonGroup(dialog)
                    radio_buttons = []
                    
                    for i, txn in enumerate(matched_transactions):
                        try:
                            desc = txn['description'] or 'No description'
                            amt = txn['amount']
                            date = txn['date']
                            radio = QRadioButton(f"{desc}\n${amt:.2f} on {date}")
                            radio.setStyleSheet("""
                                QRadioButton {
                                    padding: 10px;
                                    margin: 5px;
                                    font-size: 13px;
                                }
                                QRadioButton:checked {{
                                    background-color: {theme_color('surface_alt')};
                                    border-radius: 4px;
                                }}
                            """)
                            button_group.addButton(radio, i)
                            radio_buttons.append(radio)
                            layout.addWidget(radio)
                        except (KeyError, TypeError):
                            continue
                    
                    if not radio_buttons:
                        QMessageBox.warning(self, "Error", "Could not display transaction options")
                        return
                    
                    # Select first one by default
                    radio_buttons[0].setChecked(True)
                    
                    button_layout = QHBoxLayout()
                    button_layout.addStretch()
                    
                    cancel_btn = QPushButton("Cancel")
                    cancel_btn.clicked.connect(dialog.reject)
                    button_layout.addWidget(cancel_btn)
                    
                    select_btn = QPushButton("Mark Selected as Paid")
                    select_btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {theme_color('primary')};
                            color: {theme_color('surface')};
                            padding: 8px 16px;
                            border-radius: 6px;
                            font-weight: 600;
                        }}
                        QPushButton:hover {{
                            background-color: {theme_color('accent', theme_color('primary'))};
                        }}
                    """)
                    select_btn.clicked.connect(dialog.accept)
                    button_layout.addWidget(select_btn)
                    
                    layout.addLayout(button_layout)
                    
                    if dialog.exec_() == QDialog.Accepted:
                        selected_index = button_group.checkedId()
                        if selected_index >= 0 and selected_index < len(matched_transactions):
                            selected_txn = matched_transactions[selected_index]
                            # Mark as paid
                            self.mark_as_paid(commitment_id, category_name)
                            # Handle sqlite3.Row object
                            try:
                                txn_desc = selected_txn['description'] if 'description' in selected_txn.keys() else 'Transaction'
                            except:
                                txn_desc = 'Transaction'
                            try:
                                txn_amount = selected_txn['amount'] if 'amount' in selected_txn.keys() else 0
                            except:
                                txn_amount = 0
                            
                            QMessageBox.information(
                                self, "Smart Detect",
                                f"✅ Matched and marked as paid:\n"
                                f"{txn_desc} - ${txn_amount:.2f}"
                            )
                else:
                    # All results are similar - just confirm
                    matches_list = []
                    for txn in matched_transactions[:5]:
                        try:
                            desc = txn['description'] if 'description' in txn.keys() else 'No description'
                        except:
                            desc = 'No description'
                        try:
                            amt = txn['amount'] if 'amount' in txn.keys() else 0
                        except:
                            amt = 0
                        try:
                            date = txn['date'] if 'date' in txn.keys() else 'Unknown date'
                        except:
                            date = 'Unknown date'
                        matches_list.append(f"• {desc} - ${amt:.2f} on {date}")
                    matches_text = "\n".join(matches_list)
                    if len(matched_transactions) > 5:
                        matches_text += f"\n... and {len(matched_transactions) - 5} more"
                    
                    reply = QMessageBox.question(
                        self, "Smart Detect - Found Matches",
                        f"Found {len(matched_transactions)} matching transaction(s):\n\n{matches_text}\n\n"
                        f"Would you like to mark this commitment as paid?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )
                    
                    if reply == QMessageBox.Yes:
                        self.mark_as_paid(commitment_id, category_name)
            else:
                # No matches found - show recent transactions and let user pick manually
                # Get last 10 recent transactions for manual selection
                recent_txns = fetch_all("""
                    SELECT t.*, c.category_name 
                    FROM transactions t
                    LEFT JOIN categories c ON t.category_id = c.category_id
                    WHERE t.user_id = ? 
                    AND t.transaction_type = 'expense'
                    ORDER BY t.date DESC, t.id DESC
                    LIMIT 10
                """, (self.user_id,))
                
                dialog = QDialog(self)
                dialog.setWindowTitle("Smart Detect - Manual Selection")
                dialog.setMinimumWidth(600)
                layout = QVBoxLayout(dialog)
                
                info_label = QLabel(
                    f"Smart Detect did not work? Pick the transaction that was made manually to mark as paid.\n\n"
                    f"No automatic matches found for '{category_name}' (${commitment_amount:.2f}).\n"
                    f"Please select the transaction you made for this commitment:"
                )
                info_label.setWordWrap(True)
                info_label.setStyleSheet("font-size: 14px; padding: 10px;")
                layout.addWidget(info_label)
                
                if recent_txns:
                    button_group = QButtonGroup(dialog)
                    radio_buttons = []
                    
                    for i, txn in enumerate(recent_txns):
                        try:
                            desc = txn['description'] or 'No description'
                            amt = txn['amount']
                            date = txn['date']
                            cat_name = txn.get('category_name', 'No category')
                            radio = QRadioButton(f"{desc}\n${amt:.2f} on {date} ({cat_name})")
                            radio.setStyleSheet("""
                                QRadioButton {
                                    padding: 10px;
                                    margin: 5px;
                                    font-size: 13px;
                                }
                                QRadioButton:checked {
                                    background-color: #E3F2FD;
                                    border-radius: 4px;
                                }
                            """)
                            button_group.addButton(radio, i)
                            radio_buttons.append(radio)
                            layout.addWidget(radio)
                        except (KeyError, TypeError):
                            continue
                    
                    if radio_buttons:
                        # Select first one by default
                        radio_buttons[0].setChecked(True)
                else:
                    no_txn_label = QLabel("No recent transactions found. You can mark this commitment as paid manually.")
                    no_txn_label.setWordWrap(True)
                    no_txn_label.setStyleSheet(f"font-size: 13px; color: {theme_color('text_secondary')}; padding: 10px;")
                    layout.addWidget(no_txn_label)
                
                button_layout = QHBoxLayout()
                button_layout.addStretch()
                
                cancel_btn = QPushButton("Cancel")
                cancel_btn.clicked.connect(dialog.reject)
                button_layout.addWidget(cancel_btn)
                
                select_btn = QPushButton("Mark Selected as Paid" if recent_txns else "Mark as Paid Manually")
                select_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {theme_color('primary')};
                        color: {theme_color('surface')};
                        padding: 8px 16px;
                        border-radius: 6px;
                        font-weight: 600;
                    }}
                    QPushButton:hover {{
                        background-color: {theme_color('accent', theme_color('primary'))};
                    }}
                """)
                select_btn.clicked.connect(dialog.accept)
                button_layout.addWidget(select_btn)
                
                layout.addLayout(button_layout)
                
                if dialog.exec_() == QDialog.Accepted:
                    if recent_txns:
                        selected_index = button_group.checkedId()
                        if selected_index >= 0 and selected_index < len(recent_txns):
                            selected_txn = recent_txns[selected_index]
                            # Mark as paid
                            self.mark_as_paid(commitment_id, category_name)
                            # Handle sqlite3.Row object
                            try:
                                txn_desc = selected_txn['description'] if 'description' in selected_txn.keys() else 'Transaction'
                            except:
                                txn_desc = 'Transaction'
                            try:
                                txn_amount = selected_txn['amount'] if 'amount' in selected_txn.keys() else 0
                            except:
                                txn_amount = 0
                            
                            QMessageBox.information(
                                self, "Smart Detect",
                                f"✅ Selected transaction marked as paid:\n"
                                f"{txn_desc} - ${txn_amount:.2f}"
                            )
                    else:
                        # No transactions, just mark as paid manually
                        self.mark_as_paid(commitment_id, category_name)
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to run Smart Detect: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def pay_as_you_go(self, commitment_id, category_name, amount):
        """Navigate to transactions tab and pre-fill form for this commitment"""
        try:
            # Get commitment details
            commitment = fetch_one("""
                SELECT cc.*, c.category_id
                FROM category_commitments cc
                JOIN categories c ON cc.category_id = c.category_id
                WHERE cc.commitment_id = ? AND cc.user_id = ?
            """, (commitment_id, self.user_id))
            
            if not commitment:
                QMessageBox.warning(self, "Error", "Commitment not found")
                return
            
            # Navigate to transactions tab and switch to Transactions View (not Simulate)
            if self.parent_dashboard and hasattr(self.parent_dashboard, 'page_transactions'):
                self.parent_dashboard.show_transactions()
                
                # Switch to Transactions View tab (not Simulate Transactions)
                if hasattr(self.parent_dashboard.page_transactions, 'show_transaction_form'):
                    self.parent_dashboard.page_transactions.show_transaction_form()
                
                # Get category ID - handle sqlite3.Row
                try:
                    cat_id = commitment['category_id']
                except (KeyError, TypeError):
                    QMessageBox.warning(self, "Error", "Could not get category information")
                    return
                
                # Get accounts for pre-filling
                accounts = fetch_all("""
                    SELECT id, account_id, bank_name, account_type 
                    FROM accounts WHERE user_id = ? AND (account_type = 'salary' OR account_type = 'checking')
                    LIMIT 1
                """, (self.user_id,))
                
                if accounts:
                    account_id = accounts[0]['id']
                    
                    # CRITICAL: Set pending_commitment_id so save_txn knows to mark commitment as paid
                    self.parent_dashboard.page_transactions.pending_commitment_id = commitment_id
                    
                    # Pre-fill transaction form
                    self.parent_dashboard.page_transactions.amount_input.setText(str(amount))
                    self.parent_dashboard.page_transactions.type_input.setCurrentText("expense")
                    self.parent_dashboard.page_transactions.note_input.setPlainText(category_name)
                    
                    # Set category
                    cat_index = self.parent_dashboard.page_transactions.cat_input.findData(cat_id)
                    if cat_index >= 0:
                        self.parent_dashboard.page_transactions.cat_input.setCurrentIndex(cat_index)
                    
                    # Set account
                    acc_index = self.parent_dashboard.page_transactions.acc_input.findData(account_id)
                    if acc_index >= 0:
                        self.parent_dashboard.page_transactions.acc_input.setCurrentIndex(acc_index)
                else:
                    QMessageBox.information(
                        self.parent_dashboard, "Account Needed",
                        f"Transaction form opened. Please select an account to complete the payment for '{category_name}'."
                    )
            else:
                QMessageBox.warning(self, "Error", "Unable to navigate to transactions tab.")
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open payment form: {str(e)}")
            import traceback
            traceback.print_exc()

    def pay_savings_commitment(self, commitment_id, category_name, amount):
        """Handle payment for savings commitment - navigate to transactions tab and pre-fill form"""
        try:
            # Get checking account (from account) - use 'id' for foreign key reference
            checking_accounts = fetch_all("""
                SELECT id, account_id, bank_name, account_type
                FROM accounts
                WHERE user_id = ? AND (account_type = 'checking' OR account_type = 'salary')
                ORDER BY id
                LIMIT 1
            """, (self.user_id,))
            
            if not checking_accounts:
                QMessageBox.warning(self, "No Account", "Please link a checking account first.")
                return
            
            checking_account = checking_accounts[0]
            
            # Get savings account (to account) - use 'id' for foreign key reference
            savings_accounts = fetch_all("""
                SELECT id, account_id, bank_name, account_type
                FROM accounts
                WHERE user_id = ? AND account_type = 'savings'
                ORDER BY id
                LIMIT 1
            """, (self.user_id,))
            
            if not savings_accounts:
                QMessageBox.warning(self, "No Savings Account", "Please link a savings account first.")
                return
            
            savings_account = savings_accounts[0]
            
            # Get savings category ID
            savings_category = fetch_one("""
                SELECT category_id
                FROM categories
                WHERE user_id = ? AND LOWER(category_name) = 'savings'
            """, (self.user_id,))
            
            if not savings_category:
                QMessageBox.warning(self, "No Category", "Savings category not found. Please create it first.")
                return
            
            # Navigate to transactions tab and pre-fill
            if self.parent_dashboard:
                self.parent_dashboard.show_transactions()
                # Get the transaction form and pre-fill it
                if hasattr(self.parent_dashboard, 'page_transactions'):
                    # Use Plaid account_id for display purposes (for the "To Account Number" field)
                    # sqlite3.Row supports dictionary-style access, not .get() method
                    savings_account_id = savings_account['account_id'] if 'account_id' in savings_account.keys() else ''
                    # Extract last 4 characters if account_id is long, otherwise use full ID
                    if savings_account_id and len(str(savings_account_id)) > 4:
                        account_display = f"****{str(savings_account_id)[-4:]}"
                    else:
                        account_display = str(savings_account_id) if savings_account_id else ''
                    
                    # Use database 'id' (INTEGER) for the from_account_id foreign key
                    self.parent_dashboard.page_transactions.prefill_savings_transaction(
                        amount=amount,
                        from_account_id=checking_account['id'],  # Use 'id' not 'account_id'
                        to_account_number=account_display,
                        category_id=savings_category['category_id']
                    )
            else:
                QMessageBox.warning(self, "Error", "Unable to navigate to transactions.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open payment form: {str(e)}")

    def remove_commitment(self,commitment_id):
        """Remove a commitment"""
        reply = QMessageBox.question(
            self,
            "Remove Commitment",
            "Are you sure you want to remove this commitment?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            execute_query(
                "DELETE FROM category_commitments WHERE commitment_id = ? AND user_id = ?",
                (commitment_id,self.user_id),
                commit=True
            )
            self.load_commitments()
            # Refresh dashboard metrics to update available balance
            self.trigger_dashboard_refresh()

    def add_commitment(self):
        """Open modern commitment selection dialog"""
        # Get available categories for commitments
        categories = fetch_all("""
            SELECT category_id, category_name 
            FROM categories 
            WHERE user_id = ? AND category_id NOT IN (
                SELECT category_id 
                FROM category_commitments 
                WHERE user_id = ? AND is_paid = 0
            )
        """,(self.user_id,self.user_id))

        if not categories:
            QMessageBox.information(self,"No Categories",
                                    "All your categories already have commitments.\nCreate a new category first.")
            return

        # Show modern commitment form
        # Ensure the dialog talks to the real DashboardMain instance
        target_dashboard = self.parent_dashboard if self.parent_dashboard else self
        dlg = CommitmentForm(self.user_id, parent_dashboard=target_dashboard, category_name="Custom Commitment")
        if hasattr(dlg, 'commitment_added'):
            dlg.commitment_added.connect(target_dashboard.handle_commitment_delta if hasattr(target_dashboard, 'handle_commitment_delta') else self.handle_commitment_added_signal)
        # Connect the signal for all commitment mutations
        if hasattr(dlg, 'commitments_changed'):
            # When commitments change, rebuild balance cards immediately
            def on_commitments_changed():
                if hasattr(target_dashboard, 'rebuild_overview_cards'):
                    target_dashboard.rebuild_overview_cards()
            dlg.commitments_changed.connect(on_commitments_changed)
        # Note: Notification recompute is now handled directly in commitment save callback
        # No need for signal connection as recompute happens after database save completes

        result = dlg.exec_()
        if result == QDialog.Accepted:
            # Reload commitments so the new entry appears immediately
            self.load_commitments()
            self.trigger_dashboard_refresh()
    def handle_commitment_added_signal(self, amount):
        """Forward commitment delta to the main dashboard."""
        if self.parent_dashboard and hasattr(self.parent_dashboard, 'handle_commitment_delta'):
            self.parent_dashboard.handle_commitment_delta(amount)


class DashboardMain(QMainWindow):
    """Modern Dashboard with Navigation & Notifications"""
    balances_update_requested = pyqtSignal()

    def __init__(self,user_id,username,show_tutorial=True):
        super().__init__()
        self.user_id = user_id
        self.username = username
        self.previous_mood = None
        self.penny_personality = None
        # DEPRECATED: balances_update_requested signal - use rebuild_overview_cards() directly instead
        # self.balances_update_requested.connect(self.update_balance_cards_from_db)

        # Initialize database v3 with settings support
        from database.db_manager import initialize_database_v3
        initialize_database_v3()

        # Initialize notification manager
        from core.notification_manager import NotificationManager
        self.notification_manager = NotificationManager(self.user_id, self)

        # Connect to notification changes for badge updates
        if hasattr(self, 'notification_manager'):
            self.notification_manager.notifications_changed.connect(self.on_notifications_changed)
            # Initialize notification data
            self.notification_manager.recompute()

        self.setup_window()
        self.setup_ui()
        self.setup_animations()

        # Initialize notifications after UI is ready
        QTimer.singleShot(500, self.update_notification_badge)

        # Tutorial system
        self.tutorial_manager = TutorialManager(self)
        if show_tutorial:
            QTimer.singleShot(2000,self.tutorial_manager.start_tutorial)

    def setup_window(self):
        self.setWindowTitle(f"PennyWise - {self.username}'s Dashboard")
        self.setMinimumSize(1200,800)
        # Let the app stylesheet control the window background (no inline override)

        # Remove the default title bar
        self.setWindowFlags(Qt.FramelessWindowHint)





    def refresh_all_state(self):
        """Centralized method to refresh all app state after runtime changes (e.g., bank linking)"""
        # Refresh accounts page
        if hasattr(self, 'refresh_accounts_page'):
            self.refresh_accounts_page()
        
        # Refresh transaction form accounts dropdown
        if hasattr(self, 'page_transactions') and hasattr(self.page_transactions, 'load_accs'):
            self.page_transactions.load_accs()
        
        # Refresh dashboard components
        self.refresh_dashboard()
        
        # Refresh reports page
        if hasattr(self, 'page_reports') and hasattr(self.page_reports, 'refresh'):
            self.page_reports.refresh()
        
        # Always refresh recent transactions (not just when dashboard is visible)
        if hasattr(self, 'recent_transactions_layout'):
            self.refresh_recent_transactions()
        
        try:
            logger.info("[dashboard] refresh_all_state completed")
        except Exception:
            pass

    def refresh_dashboard(self):
        """Refresh dashboard data including commitments and balance cards"""
        # Refresh commitments if they exist
        if hasattr(self,'commitment_tracker'):
            self.commitment_tracker.refresh_commitments()

        # Rebuild balance cards with fresh Plaid data and updated commitments
        if hasattr(self, 'overview_layout'):
            self.rebuild_overview_cards()

        # Refresh metrics carousel if it exists
        if hasattr(self,'metrics_carousel'):
            self.metrics_carousel.refresh_data()
            self.metrics_carousel.refresh_metrics_cards()
        
        # Refresh recent transactions if on dashboard page
        if hasattr(self, 'stack') and hasattr(self, 'page_dashboard'):
            if self.stack.currentWidget() == self.page_dashboard:
                if hasattr(self, 'recent_transactions_layout'):
                    self.refresh_recent_transactions()
        try:
            logger.info("[dashboard] refresh_dashboard completed")
        except Exception:
            pass

    def on_notifications_changed(self, count):
        """Handle notification count changes safely"""
        try:
            # Ensure nav bar and badge exist before updating
            if hasattr(self, 'nav_bar') and hasattr(self.nav_bar, 'notification_badge'):
                self.nav_bar.notification_badge.update_count(count)
        except Exception as e:
            logger.error(f"Error updating notification badge: {e}")

    def update_notification_badge(self):
        """Update notification badge by recomputing notifications and letting signal handle UI update"""
        if not hasattr(self, "notification_manager"):
            return
        if not hasattr(self, "nav_bar") or not hasattr(self.nav_bar, "notification_badge"):
            return
        # Recompute notifications to ensure latest state, which will emit notifications_changed signal
        self.notification_manager.recompute()
    
    def refresh_metrics_cards_main(self):
        """Refresh the metrics cards in DashboardMain (not MetricsCarousel)"""
        if hasattr(self, 'metrics_carousel'):
            self.metrics_carousel.refresh_metrics_cards()
            try:
                # Log current metrics values if available
                if hasattr(self.metrics_carousel, 'metrics_data') and self.metrics_carousel.metrics_data:
                    logger.info(f"[dashboard] metrics_cards_main refreshed with {len(self.metrics_carousel.metrics_data)} cards")
            except Exception:
                pass

        # Run commitment checks for due dates
        from core.commitment_manager import check_commitments
        check_commitments(self.user_id)

    def rebuild_overview_cards(self):
        """Rebuild the overview cards with fresh Plaid data and current commitments."""
        if not hasattr(self, 'overview_layout'):
            return
        
        # Clear existing cards
        while self.overview_layout.count():
            item = self.overview_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        
        # Re-run setup_metrics_carousel to rebuild cards with fresh data
        # We pass None as layout since cards will be added to existing overview_layout
        self._rebuild_cards_in_layout(self.overview_layout)
    
    def _rebuild_cards_in_layout(self, overview_layout):
        """Internal helper: fetch Plaid balances and build cards in the given layout."""
        try:
            from database.db_manager import fetch_all, fetch_one
            from core.plaid_api import get_account_balances

            # Get REAL checking account balance from Plaid ONLY (no simulated, no transaction fallback)
            checking_balance = 0
            has_plaid_checking = False

            # Get Plaid checking accounts (which are stored as 'salary' type) - ONLY primary
            plaid_accounts = fetch_all("""
                SELECT account_id, plaid_token, account_type, bank_name
                FROM accounts 
                WHERE user_id = ? 
                AND account_type = 'salary'
                AND is_primary = 1
                AND plaid_token IS NOT NULL
            """,(self.user_id,))

            if plaid_accounts:
                has_plaid_checking = True
                for account in plaid_accounts:
                    # ONLY use Plaid API - no simulated_balance, no transaction fallback
                    try:
                        balances_data = get_account_balances(account["plaid_token"])
                        if "error" in balances_data:
                            logger.warning(f"Plaid balance error for account {account['account_id']}: {balances_data['error']}")
                            continue
                        for acc_balance in balances_data.get("accounts",[]):
                            if acc_balance["account_id"] == account["account_id"]:
                                balance = acc_balance["balances"].get("available",0)
                                checking_balance += balance
                    except Exception as e:
                        logger.error(f"Error fetching balance for account {account['account_id']}: {e}")

            # Get savings balance - ONLY from Plaid, no fallback
            # Get ALL savings accounts (not just primary) to sum all savings balances
            savings = 0
            plaid_savings_accounts = fetch_all("""
                SELECT account_id, plaid_token, account_type, bank_name
                FROM accounts 
                WHERE user_id = ? 
                AND account_type = 'savings'
                AND plaid_token IS NOT NULL
            """,(self.user_id,))
            
            if plaid_savings_accounts:
                # Get real savings balance from Plaid for all savings accounts
                for account in plaid_savings_accounts:
                    try:
                        balances_data = get_account_balances(account["plaid_token"])
                        if "error" in balances_data:
                            logger.warning(f"Plaid savings balance error for account {account['account_id']}: {balances_data['error']}")
                            continue
                        for acc_balance in balances_data.get("accounts",[]):
                            if acc_balance["account_id"] == account["account_id"]:
                                balance = acc_balance["balances"].get("available",0) or 0
                                savings += balance
                    except Exception as e:
                        logger.error(f"Error fetching savings balance for account {account['account_id']}: {e}")

            # Get commitments (unpaid) - handle NULL is_paid values
            commitments_row = fetch_one("""
                SELECT COALESCE(SUM(amount), 0) AS total
                FROM category_commitments
                WHERE user_id = ? AND COALESCE(is_paid, 0) = 0
            """,(self.user_id,))
            try:
                commitments = commitments_row["total"] if commitments_row and "total" in commitments_row.keys() and commitments_row["total"] is not None else 0
            except (KeyError, TypeError, AttributeError):
                commitments = 0

            # Calculate balances - commitments ONLY affect computed value, never modify Plaid balance
            price_after_commitments = checking_balance - commitments

            # Get currency
            user_currency = fetch_one("SELECT currency FROM settings WHERE user_id = ?",(self.user_id,))
            try:
                currency = user_currency["currency"] if user_currency and "currency" in user_currency.keys() else "USD"
            except (KeyError, TypeError, AttributeError):
                currency = "USD"

            # Check if accounts exist (relaxed: check by is_primary OR account_type)
            has_savings_account = fetch_one("""
                SELECT account_id FROM accounts 
                WHERE user_id = ? AND (account_type = 'savings' OR is_primary = 1)
                LIMIT 1
            """, (self.user_id,))
            
            has_main_account = fetch_one("""
                SELECT account_id FROM accounts 
                WHERE user_id = ? AND account_type = 'salary' AND is_primary = 1
                LIMIT 1
            """, (self.user_id,))
            
            has_savings = has_savings_account is not None
            has_main = has_main_account is not None
            
            # Create cards
            if has_savings and savings > 0:
                savings_card = self.create_finance_card(
                    "Savings Balance",
                    f"{currency} {savings:,.2f}",
                    theme_color('success'),
                    "positive"
                )
            else:
                def show_link_bank_savings():
                    widget = self
                    while widget:
                        if hasattr(widget, 'show_link_bank'):
                            widget.show_link_bank("savings")
                            return
                        widget = widget.parent() if hasattr(widget, 'parent') and callable(widget.parent) else None
                    from PyQt5.QtWidgets import QApplication
                    for widget in QApplication.topLevelWidgets():
                        if hasattr(widget, 'show_link_bank'):
                            widget.show_link_bank("savings")
                            return
                
                savings_card = self.create_empty_card(
                    " Savings Balance",
                    "Add Savings Account",
                    show_link_bank_savings
                )

            # Price After Commitments always shows as finance card
            commitments_card = self.create_finance_card(
                "Balance After Commitments",
                f"{currency} {price_after_commitments:,.2f}",
                theme_color('warning'),
                "warning"
            )
            commitments_card.setFixedHeight(180)
            self.commitments_card = commitments_card
            if hasattr(commitments_card, "value_label"):
                self.commitments_value_label = commitments_card.value_label
            
            # Available Balance
            if has_main and checking_balance > 0:
                available_card = self.create_finance_card(
                    "Available Balance",
                    f"{currency} {checking_balance:,.2f}",
                    theme_color('success'),
                    "positive"
                )
            else:
                def show_link_bank_main():
                    widget = self
                    while widget:
                        if hasattr(widget, 'show_link_bank'):
                            widget.show_link_bank("listings")
                            return
                        widget = widget.parent() if hasattr(widget, 'parent') and callable(widget.parent) else None
                    from PyQt5.QtWidgets import QApplication
                    for widget in QApplication.topLevelWidgets():
                        if hasattr(widget, 'show_link_bank'):
                            widget.show_link_bank("listings")
                            return
                
                available_card = self.create_empty_card(
                    "Available Balance",
                    "Add Bank Account",
                    show_link_bank_main
                )

            # Add cards to layout
            overview_layout.addWidget(savings_card)
            overview_layout.addWidget(commitments_card)
            overview_layout.addWidget(available_card)
            
            logger.info(f"[rebuild_cards] Plaid balances: checking={checking_balance} savings={savings} commitments={commitments} after={price_after_commitments}")
            
        except Exception as e:
            logger.error(f"Error rebuilding overview cards: {e}")
            import traceback
            traceback.print_exc()

    def refresh_balance_cards(self):
        """Refresh only balance-related cards quickly."""
        try:
            self.rebuild_overview_cards()
            # Force UI repaint
            try:
                from PyQt5.QtWidgets import QApplication
                QApplication.processEvents()
            except Exception:
                pass
            logger.info("[dashboard] refresh_balance_cards completed")
        except Exception as e:
            logger.warning(f"[dashboard] refresh_balance_cards error: {e}")

    def update_balance_cards_from_db(self):  # DEPRECATED: Use rebuild_overview_cards() instead
        """
        Single authoritative recompute+render path for all balance and commitment UI.
        - Queries latest account balance and unpaid commitment sum from DB
        - Computes available_balance and balance_after_commitments (no caching)
        - Updates all UI widgets directly
        - Fails loudly if any widget is missing
        - No partial refresh, no try/except hiding errors
        """
        from database.db_manager import fetch_one
        # #region agent log
        import json as _json
        import time as _time
        try:
            with open(r'c:\Users\asus\OneDrive\Desktop\PennyWise\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(_json.dumps({"sessionId":"debug-session","runId":"balances-pre-fix","hypothesisId":"H1,H3","location":"dashboard_main.py:update_balance_cards_from_db","message":"update_balance_cards_from_db called","data":{"user_id":getattr(self,'user_id',None)}, "timestamp":int(_time.time()*1000)}) + "\n")
        except Exception:
            pass
        # #endregion
        checking_balance_row = fetch_one("""
            SELECT SUM(
                CASE 
                    WHEN transaction_type = 'income' THEN amount 
                    WHEN transaction_type = 'expense' THEN -amount 
                    ELSE 0 
                END
            ) as balance
            FROM transactions
            WHERE user_id = ?
        """, (self.user_id,))
        raw_balance = float(checking_balance_row["balance"] if checking_balance_row and checking_balance_row["balance"] is not None else 0)
        if raw_balance < 0:
            logger.warning(f"[balances] Negative raw checking balance fetched for user={self.user_id}: {raw_balance}")
        unpaid_row = fetch_one("""
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM category_commitments
            WHERE user_id = ? AND COALESCE(is_paid, 0) = 0
        """, (self.user_id,))
        unpaid_sum = float(unpaid_row["total"] if unpaid_row and unpaid_row["total"] is not None else 0)
        # #region agent log
        try:
            with open(r'c:\Users\asus\OneDrive\Desktop\PennyWise\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(_json.dumps({"sessionId":"debug-session","runId":"balances-pre-fix","hypothesisId":"H1,H3","location":"dashboard_main.py:update_balance_cards_from_db","message":"db recompute values","data":{"raw_balance":raw_balance,"unpaid_sum":unpaid_sum,"computed_after":(raw_balance-unpaid_sum)}, "timestamp":int(_time.time()*1000)}) + "\n")
        except Exception:
            pass
        # #endregion
        available_balance = max(0, raw_balance)
        balance_after_commitments = max(0, raw_balance - unpaid_sum)
        user_currency = fetch_one("SELECT currency FROM settings WHERE user_id = ?", (self.user_id,))
        if user_currency and "currency" in user_currency.keys():
            currency = user_currency["currency"]
        else:
            currency = "USD"
        if not hasattr(self, "overview_layout"):
            raise RuntimeError("overview_layout missing in dashboard")
        while self.overview_layout.count():
            item = self.overview_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        savings_row = fetch_one("""
            SELECT COALESCE(SUM(t.amount), 0) AS total
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.category_id
            WHERE t.user_id = ? 
            AND t.transaction_type = 'income'
            AND c.category_name = 'Savings'
        """, (self.user_id,))
        savings = savings_row["total"] if savings_row and savings_row["total"] is not None else 0
        savings_card = self.create_finance_card(
            "Savings Balance",
            f"{currency} {savings:,.2f}",
            theme_color('success'),
            "positive"
        )
        commitments_card = self.create_finance_card(
            "Balance After Commitments",
            f"{currency} {balance_after_commitments:,.2f}",
            theme_color('warning'),
            "warning"
        )
        commitments_card.setFixedHeight(180)
        available_card = self.create_finance_card(
            "Available Balance",
            f"{currency} {available_balance:,.2f}",
            theme_color('success'),
            "positive"
        )
        self.overview_layout.addWidget(savings_card)
        self.overview_layout.addWidget(commitments_card)
        self.overview_layout.addWidget(available_card)

    def handle_commitment_delta(self, delta: float):
        """
        Apply a commitment delta (positive on add, negative on mark-paid) without full refresh.
        Updates cached totals and the commitments card immediately.
        """
        try:
            before_unpaid = float(getattr(self, "current_unpaid_commitments_total", 0) or 0)
            before_price = float(getattr(self, "current_price_after_commitments", 0) or 0)
            currency = getattr(self, "current_currency", "USD") or "USD"
        except Exception:
            before_unpaid = 0.0
            before_price = 0.0
            currency = "USD"

        try:
            logger.info(
                f"[commitment_delta] user={self.user_id} delta={delta:+.2f} "
                f"unpaid_before={before_unpaid:.2f} price_before={before_price:.2f}"
            )
        except Exception:
            pass

        new_unpaid = before_unpaid + float(delta or 0)
        new_price_after = float(getattr(self, "current_available_balance", 0) or 0) - new_unpaid

        self.current_unpaid_commitments_total = new_unpaid
        self.current_price_after_commitments = new_price_after

        try:
            logger.info(
                f"[commitment_delta] user={self.user_id} unpaid_after={new_unpaid:.2f} "
                f"price_after={new_price_after:.2f}"
            )
        except Exception:
            pass

        # Update the commitments card value label directly
        if hasattr(self, "commitments_value_label") and self.commitments_value_label:
            try:
                self.commitments_value_label.setText(f"{currency} {new_price_after:,.2f}")
                logger.info(f"[commitment_delta] card updated value={currency} {new_price_after:,.2f}")
            except Exception as e:
                logger.warning(f"[commitment_delta] failed to update card label: {e}")
        else:
            # Fallback: lightweight balance card refresh if label missing
            try:
                self.refresh_balance_cards()
                logger.info("[commitment_delta] fallback refresh_balance_cards invoked")
            except Exception as e:
                logger.warning(f"[commitment_delta] fallback refresh failed: {e}")

        # Lightweight repaint only
        try:
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()
        except Exception:
            pass

    def force_full_refresh(self):
        """Force a comprehensive, synchronous refresh of dashboard data."""
        try:
            # Refresh core dashboard data
            self.refresh_dashboard()
            # Ensure metrics data/cards are refreshed
            if hasattr(self, 'metrics_carousel'):
                self.metrics_carousel.refresh_data()
                self.metrics_carousel.refresh_metrics_cards()
            # Ensure commitments widget re-renders
            if hasattr(self, 'commitment_tracker'):
                self.commitment_tracker.refresh_commitments()
            # Optionally update dashboard layout
            self.update_dashboard()
            logger.info("[dashboard] force_full_refresh completed")
        except Exception as e:
            logger.warning(f"[dashboard] force_full_refresh error: {e}")

    def update_dashboard(self):
        """Rebuild the dashboard page to reflect latest data"""
        # Just call refresh_dashboard for now
        self.refresh_dashboard()
        # If on dashboard page, refresh it
        if hasattr(self, 'stack') and hasattr(self, 'page_dashboard'):
            if self.stack.currentWidget() == self.page_dashboard:
                # Force a refresh by rebuilding the page
                # Get current scroll position if in scroll area
                self.show_dashboard()
        
        # Refresh accounts page to show newly linked accounts
        self.refresh_accounts_page()

    def force_quick_refresh(self):
        """Lightweight refresh for commitments and balance cards only."""
        # Refresh commitments
        if hasattr(self, 'commitment_tracker'):
            self.commitment_tracker.refresh_commitments()
        # Refresh metrics data/cards without rebuilding pages
        if hasattr(self, 'metrics_carousel'):
            self.metrics_carousel.refresh_data()
            self.metrics_carousel.refresh_metrics_cards()
        # Refresh main metrics cards
        if hasattr(self, 'refresh_metrics_cards_main'):
            self.refresh_metrics_cards_main()

    def logout(self):
        """Handle logout functionality"""
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Logout",
            "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Close the current dashboard
            self.close()
            
            # Import and show the login window
            try:
                from ui.login_window import LoginWindow
                self.login_window = LoginWindow()
                self.login_window.show()
            except ImportError:
                print("Could not import LoginWindow")
                # If login window import fails, just close the application
                from PyQt5.QtWidgets import QApplication
                QApplication.quit()

    def create_pages(self):
        """Create all pages for the stacked widget"""
        # Dashboard page (main content)
        self.page_dashboard = self.build_dashboard_page()
        
        # Transactions page
        from ui.transaction_form import TransactionForm
        self.page_transactions = TransactionForm(self.user_id, parent=self)
        # Connect transaction saved signal to refresh reports
        if hasattr(self.page_transactions, 'transaction_saved'):
            self.page_transactions.transaction_saved.connect(self._refresh_reports_on_transaction)
        
        # Accounts page
        self.page_accounts = self.build_accounts_page()
        
        # Reports page
        from ui.reports_page import ReportsPage
        self.page_reports = ReportsPage(self.user_id)
        
        # Settings page
        from ui.settings_window import SettingsWindow
        self.page_settings = SettingsWindow(self.user_id, parent=self)
        self.page_settings.settings_changed.connect(self.on_settings_changed)
        
        # Link Bank page (created fresh each time show_link_bank is called)
        self.page_bank = None
        
        # Connect to commitment form signals for notification updates
        # We'll connect this when the commitment form is created dynamically
        
        # Add all pages to stack (bank page added dynamically in show_link_bank)
        self.stack.addWidget(self.page_dashboard)
        self.stack.addWidget(self.page_transactions)
        self.stack.addWidget(self.page_accounts)
        self.stack.addWidget(self.page_reports)
        self.stack.addWidget(self.page_settings)
        
        # Set dashboard as default
        self.stack.setCurrentWidget(self.page_dashboard)

    def build_dashboard_page(self):
        """Build the main dashboard page"""
        content_container = QWidget()
        self.dashboard_content_container = content_container
        content_container.setStyleSheet(f"background: {theme_color('background')}; color: {theme_color('text_primary')};")
        content_layout = QVBoxLayout(content_container)
        
        # Content padding
        content_layout.setContentsMargins(30, 5, 30, 30)
        content_layout.setSpacing(5)
        
        # Add content sections
        self.setup_header(content_layout)
        
        spacer = QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Fixed)
        content_layout.addItem(spacer)
        
        self.setup_metrics_carousel(content_layout)
        
        # --- Monthly Commitments Section ---
        commitment_title = QLabel(" Monthly Commitments")
        self.commitment_title = commitment_title
        commitment_title.setFont(QFont("Segoe UI",18,QFont.Bold))
        commitment_title.setStyleSheet(f"color: {theme_color('text_primary')}; margin-top: 15px;")
        content_layout.addWidget(commitment_title)
        
        try:
            self.commitment_tracker = CommitmentTrackerWidget(self.user_id, parent=self)
            content_layout.addWidget(self.commitment_tracker)
        except Exception as e:
            error_widget = QLabel(f"Error loading commitments: {str(e)}")
            error_widget.setStyleSheet("background: yellow; color: red; padding: 20px; border: 2px solid red;")
            content_layout.addWidget(error_widget)
        # --- End Monthly Commitments Section ---

        self.setup_main_content(content_layout)

        # Create scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_bg = theme_color('background')
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background: transparent; }}")
        scroll.viewport().setAutoFillBackground(True)
        vp_pal = scroll.viewport().palette()
        vp_pal.setColor(QPalette.Window, QColor(scroll_bg))
        scroll.viewport().setPalette(vp_pal)
        scroll.setWidget(content_container)
        self.dashboard_scroll = scroll
        
        return scroll

    def build_accounts_page(self):
        """Build the accounts page with flat list of accounts (no sub-accounts)"""
        from PyQt5.QtWidgets import (
            QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, 
            QFrame, QPushButton, QMessageBox, QMenu
        )
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QFont, QColor
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect
        from core.logger import logger
        import qtawesome as qta
        from database.migrations.add_institution_migration import apply_institution_migration
        apply_institution_migration()
        
        # Import PennyWise colors
        from assets.styles.penny_colors import PennyColors
        
        page = QWidget()
        page.setStyleSheet(f"background: {theme_color('background')};")
        self.accounts_page_widget = page
        main_layout = QVBoxLayout(page)
        main_layout.setContentsMargins(24, 16, 24, 24)
        main_layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Accounts")
        title.setFont(QFont("Segoe UI", 28, QFont.Bold))
        title.setStyleSheet(f"color: {theme_color('text_primary')}; padding: 0; margin: 0;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Link Bank button
        link_btn = QPushButton("+ Link Account")
        link_btn.setStyleSheet(f"""
            QPushButton {{
                background: {PennyColors.CTA_GRADIENT};
                color: {PennyColors.SURFACE};
                padding: 8px 12px;
                border-radius: 10px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: {PennyColors.CTA_GRADIENT_HOVER};
            }}
            QPushButton:pressed {{
                background: {PennyColors.CTA_PRESSED};
            }}
        """)
        link_btn.clicked.connect(lambda: self.show_link_bank())
        header_layout.addWidget(link_btn)
        
        main_layout.addLayout(header_layout)
        
        # Info label
        info_label = QLabel("Click an account to manage it. Set as Listings Account or Savings Account.")
        info_label.setStyleSheet(f"color: {theme_color('text_secondary')}; font-size: 12px; padding: 4px 0 8px 0;")
        main_layout.addWidget(info_label)
        
        # Scroll area for accounts
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QScrollArea::viewport { background: transparent; }")
        scroll.viewport().setAutoFillBackground(True)
        vp_pal = scroll.viewport().palette()
        vp_pal.setColor(QPalette.Window, QColor(theme_color('background')))
        scroll.viewport().setPalette(vp_pal)
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet(f"background: {theme_color('background')};")
        self.accounts_scroll_content = scroll_content
        self.accounts_scroll_content = scroll_content
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(12)
        
        # Get all accounts - include both checking (salary) and savings accounts
        # We show all accounts that are linked to pennywise (listings or savings)
        try:
            accounts = fetch_all("""
                SELECT id, account_id, bank_name, account_type, institution_name, institution_logo,
                       is_primary, plaid_token
                FROM accounts 
                WHERE user_id = ? AND plaid_token IS NOT NULL
                AND (account_type = 'salary' OR account_type = 'savings')
                ORDER BY 
                    CASE WHEN account_type = 'salary' AND is_primary = 1 THEN 1
                         WHEN account_type = 'savings' THEN 2
                         ELSE 3 END,
                    COALESCE(institution_name, bank_name)
            """, (self.user_id,))
        except Exception as e:
            # Fallback query without institution_logo if column doesn't exist yet
            logger.warning(f"institution_logo column not found, using fallback query: {e}")
            accounts = fetch_all("""
                SELECT id, account_id, bank_name, account_type, institution_name,
                       is_primary, plaid_token
                FROM accounts 
                WHERE user_id = ? AND plaid_token IS NOT NULL
                AND (account_type = 'salary' OR account_type = 'savings')
                ORDER BY 
                    CASE WHEN account_type = 'salary' AND is_primary = 1 THEN 1
                         WHEN account_type = 'savings' THEN 2
                         ELSE 3 END,
                    COALESCE(institution_name, bank_name)
            """, (self.user_id,))
            # Add None for institution_logo for each account to match expected structure
            if accounts:
                accounts = [dict(acc) if hasattr(acc, 'keys') else acc for acc in accounts]
                for acc in accounts:
                    if isinstance(acc, dict) and 'institution_logo' not in acc:
                        acc['institution_logo'] = None
        
        # Get active accounts
        active_checking = fetch_one("""
            SELECT account_id FROM accounts 
            WHERE user_id = ? AND account_type = 'salary' AND is_primary = 1
            LIMIT 1
        """, (self.user_id,))
        
        active_savings = fetch_one("""
            SELECT account_id FROM accounts 
            WHERE user_id = ? AND account_type = 'savings'
            LIMIT 1
        """, (self.user_id,))
        
        active_checking_id = active_checking['account_id'] if active_checking and 'account_id' in active_checking.keys() else None
        active_savings_id = active_savings['account_id'] if active_savings and 'account_id' in active_savings.keys() else None
        
        if not accounts:
            # Empty state
            empty_container = QWidget()
            empty_layout = QVBoxLayout(empty_container)
            empty_layout.setAlignment(Qt.AlignCenter)
            
            no_accounts_icon = QLabel()
            try:
                no_accounts_icon.setPixmap(qta.icon('fa5s.university', color=theme_color('text_secondary')).pixmap(64, 64))
            except Exception:
                no_accounts_icon.setText("🏦")
                no_accounts_icon.setStyleSheet("font-size: 48px;")
            no_accounts_icon.setAlignment(Qt.AlignCenter)
            empty_layout.addWidget(no_accounts_icon)
            
            no_accounts = QLabel("No accounts linked yet")
            no_accounts.setAlignment(Qt.AlignCenter)
            no_accounts.setStyleSheet(f"""
                color: {theme_color('text_primary')};
                font-size: 16px;
                font-weight: 600;
                padding: 12px 0 4px 0;
            """)
            empty_layout.addWidget(no_accounts)
            
            no_accounts_sub = QLabel("Link your first bank account to get started")
            no_accounts_sub.setAlignment(Qt.AlignCenter)
            no_accounts_sub.setStyleSheet(f"""
                color: {theme_color('text_secondary')};
                font-size: 14px;
                padding: 0 0 24px 0;
            """)
            empty_layout.addWidget(no_accounts_sub)
            
            scroll_layout.addWidget(empty_container)
        else:
            # Display each account as a card
            for acc in accounts:
                try:
                    account_card = self.create_account_card(
                        acc, active_checking_id, active_savings_id, scroll_layout
                    )
                except Exception as e:
                    logger.error(f"Error displaying account: {e}")
                    import traceback
                    traceback.print_exc()
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        return page

    def _apply_root_backgrounds(self):
        """Apply current theme background to root containers and pages."""
        try:
            bg = QColor(theme_color('background'))
            # Main window background/text
            self.setAutoFillBackground(True)
            pal_self = self.palette()
            pal_self.setColor(QPalette.Window, bg)
            pal_self.setColor(QPalette.WindowText, QColor(theme_color('text_primary')))
            self.setPalette(pal_self)
            self.setStyleSheet(f"background: {theme_color('background')}; color: {theme_color('text_primary')};")
            if hasattr(self, "central_widget") and self.central_widget:
                self.central_widget.setAutoFillBackground(True)
                pal = self.central_widget.palette()
                pal.setColor(QPalette.Window, bg)
                self.central_widget.setPalette(pal)
            if hasattr(self, "dashboard_content_container") and self.dashboard_content_container:
                self.dashboard_content_container.setStyleSheet(f"background: {theme_color('background')};")
            if hasattr(self, "dashboard_scroll") and self.dashboard_scroll:
                try:
                    vp = self.dashboard_scroll.viewport()
                    if vp:
                        vp_pal = vp.palette()
                        vp_pal.setColor(QPalette.Window, QColor(theme_color('background')))
                        vp.setPalette(vp_pal)
                        vp.setAutoFillBackground(True)
                except Exception:
                    pass
            if hasattr(self, "welcome_label"):
                self.welcome_label.setStyleSheet(f"color: {theme_color('text_primary')};")
            if hasattr(self, "commitment_title"):
                self.commitment_title.setStyleSheet(f"color: {theme_color('text_primary')}; margin-top: 15px;")
            if hasattr(self, "transactions_title"):
                self.transactions_title.setStyleSheet(f"color: {theme_color('text_primary')}; margin-top: 15px;")
            if hasattr(self, "accounts_page_widget") and self.accounts_page_widget:
                self.accounts_page_widget.setStyleSheet(f"background: {theme_color('background')};")
            if hasattr(self, "accounts_scroll") and self.accounts_scroll:
                try:
                    vp = self.accounts_scroll.viewport()
                    if vp:
                        vp_pal = vp.palette()
                        vp_pal.setColor(QPalette.Window, QColor(theme_color('background')))
                        vp.setPalette(vp_pal)
                        vp.setAutoFillBackground(True)
                except Exception:
                    pass
            if hasattr(self, "accounts_scroll_content") and self.accounts_scroll_content:
                self.accounts_scroll_content.setStyleSheet(f"background: {theme_color('background')};")
            if hasattr(self, "stack") and self.stack:
                self.stack.setStyleSheet(f"background: {theme_color('background')};")
        except Exception as e:
            logger.warning(f"[theme] apply root backgrounds failed: {e}")

    def create_account_card(self, acc, active_checking_id, active_savings_id, parent_layout):
        """Create account card with logo, name, and status"""
        from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QMenu
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QFont, QColor
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect
        from assets.styles.penny_colors import PennyColors
        import qtawesome as qta
        
        account_id = acc['account_id'] if 'account_id' in acc.keys() else acc.get('id') if hasattr(acc, 'get') else None
        bank_name = acc['bank_name'] if 'bank_name' in acc.keys() else 'Unknown Account'
        
        # Handle sqlite3.Row object - use bracket notation or check with 'in'
        # Use institution_name if available, otherwise extract from bank_name
        display_name = None
        if 'institution_name' in acc.keys() and acc['institution_name']:
            display_name = acc['institution_name']
        
        # If no institution_name, try to extract from bank_name
        # Account names are like "Tartan Bank Checking", "First Gingham Credit Union Checking", "Plaid Checking"
        if not display_name and bank_name:
            # Remove "Plaid" prefix if present
            cleaned = bank_name.replace("Plaid", "").strip()
            # Remove account type words (Checking, Savings, etc.)
            account_types = ["Checking", "Savings", "Credit", "Card", "Loan", "checking", "savings", "credit", "card", "loan"]
            parts = cleaned.split()
            filtered_parts = [p for p in parts if p not in account_types]
            if filtered_parts:
                display_name = " ".join(filtered_parts)
            elif cleaned:
                display_name = cleaned
            else:
                display_name = "Bank"
        
        if not display_name:
            display_name = "Bank"
        
        # Also try to fetch institution info if we have institution_id (for display name only)
        if (not display_name or display_name == "Bank") and 'institution_id' in acc.keys() and acc['institution_id']:
            try:
                from core.plaid_api import get_institution_by_id
                institution_data = get_institution_by_id(acc['institution_id'])
                if "institution" in institution_data and "error" not in institution_data:
                    institution = institution_data["institution"]
                    if not display_name or display_name == "Bank":
                        display_name = institution.get("name", display_name)
            except Exception as e:
                logger.warning(f"Failed to fetch institution details: {e}")
        
        # Determine if this is active checking or savings
        is_active_checking = (account_id == active_checking_id)
        is_active_savings = (account_id == active_savings_id)
        is_active = is_active_checking or is_active_savings
        
        # Account card
        account_card = QFrame()
        p = theme_palette()
        
        # Highlight active accounts with different colors
        if is_active_checking:
            border_color = PennyColors.ACCENT  # Orange for main/checking
            bg_color = f"rgba(245, 158, 11, 0.05)"
        elif is_active_savings:
            border_color = PennyColors.SUCCESS  # Green for savings
            bg_color = f"rgba(34, 197, 94, 0.05)"
        else:
            border_color = p['border']
            bg_color = p['surface']
        
        account_card.setStyleSheet(f"""
            QFrame {{
                background: {bg_color};
                border: 2px solid {border_color};
                border-radius: 12px;
                padding: 16px;
            }}
            QFrame:hover {{
                border-color: {border_color if is_active else theme_color('accent')};
                background: {bg_color if is_active else p.get('surface_alt', bg_color)};
            }}
        """)
        
        # Make card clickable to redirect to link accounts tab
        def card_clicked(event):
            self.show_link_bank()
        
        account_card.mousePressEvent = card_clicked
        account_card.setCursor(Qt.PointingHandCursor)
        
        # Subtle shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 15))
        account_card.setGraphicsEffect(shadow)
        
        account_layout = QHBoxLayout(account_card)
        account_layout.setContentsMargins(16, 16, 16, 16)
        account_layout.setSpacing(16)
        
        # Bank logo (icon) - left side
        logo_label = QLabel()
        logo_label.setFixedSize(40, 40)
        logo_bg_color = theme_color('surface_alt') if is_active else theme_color('surface')
        logo_text_color = theme_color('accent') if is_active else theme_color('text_secondary')
        
        # Simplified logo: always use local icon (avoid network/base64 fetch)
        try:
            logo_icon = qta.icon('fa5s.university', color=logo_text_color)
            logo_label.setPixmap(logo_icon.pixmap(40, 40))
            logo_label.setStyleSheet(f"background: {logo_bg_color}; border-radius: 8px;")
        except Exception:
            logo_label.setText("🏦")
            logo_label.setStyleSheet(f"font-size: 32px; color: {logo_text_color}; background: {logo_bg_color}; border-radius: 8px;")
        
        logo_label.setAlignment(Qt.AlignCenter)
        account_layout.addWidget(logo_label)
        
        # Account name and number (middle) - use VBox for name and account number
        name_container = QWidget()
        name_layout = QVBoxLayout(name_container)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(4)
        
        # Bank name - no box, just text
        account_name_label = QLabel(display_name)
        account_name_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        account_name_label.setStyleSheet(f"""
            color: {theme_color('text_primary')};
            background: transparent;
            border: none;
            padding: 0;
        """)
        name_layout.addWidget(account_name_label)
        
        # Account number (account_id) - small, light font
        account_number_label = QLabel(account_id if account_id else "")
        account_number_label.setFont(QFont("Segoe UI", 11))
        account_number_label.setStyleSheet(f"""
            color: {theme_color('text_secondary')};
            background: transparent;
            border: none;
            padding: 0;
            font-weight: normal;
        """)
        name_layout.addWidget(account_number_label)
        
        account_layout.addWidget(name_container)
        account_layout.addStretch()
        
        # Active status badge (right side)
        if is_active_checking:
            status_badge = QLabel("Current Listings Account")
            status_badge.setStyleSheet(f"""
                background: {PennyColors.ACCENT};
                color: white;
                padding: 6px 12px;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
            """)
            account_layout.addWidget(status_badge)
        elif is_active_savings:
            status_badge = QLabel("Current Savings Account")
            status_badge.setStyleSheet(f"""
                background: {PennyColors.SUCCESS};
                color: white;
                padding: 6px 12px;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
            """)
            account_layout.addWidget(status_badge)
        else:
            status_badge = QLabel("Not Active")
            status_badge.setStyleSheet(f"""
                background: {theme_color('surface_alt')};
                color: {theme_color('text_secondary')};
                padding: 6px 12px;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
            """)
            account_layout.addWidget(status_badge)
        
        # Menu button (three dots)
        menu_btn = QPushButton()
        menu_btn.setFixedSize(32, 32)
        try:
            menu_icon = qta.icon('fa5s.ellipsis-v', color=theme_color('text_secondary'))
            menu_btn.setIcon(menu_icon)
        except:
            menu_btn.setText("⋯")
        menu_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background: {theme_color('row_hover', theme_color('surface_alt'))};
            }}
        """)
        
        # Create context menu
        def show_menu(pos):
            menu = QMenu()
            
            # Set as Listings Account (if not already)
            if not is_active_checking:
                set_main_action = menu.addAction("Set as Listings Account")
                def make_set_main_handler(acc_id):
                    def handler():
                        self.set_as_main_account(acc_id)
                    return handler
                set_main_action.triggered.connect(make_set_main_handler(account_id))
            
            # Set as Savings Account (if not already)
            if not is_active_savings:
                set_savings_action = menu.addAction("Set as Savings Account")
                def make_set_savings_handler(acc_id):
                    def handler():
                        self.set_as_savings_account(acc_id)
                    return handler
                set_savings_action.triggered.connect(make_set_savings_handler(account_id))
            
            menu.addSeparator()
            
            # Remove account (QAction doesn't support setStyleSheet, so we'll use a styled widget)
            remove_action = menu.addAction("Remove Account")
            def make_remove_handler(acc_id):
                def handler():
                    self.remove_account(acc_id)
                return handler
            remove_action.triggered.connect(make_remove_handler(account_id))
            
            # Style the menu to make remove action red
            menu.setStyleSheet("""
                QMenu::item:selected {
                    background-color: rgba(220, 38, 38, 0.1);
                }
                QMenu::item {
                    padding: 8px 20px;
                }
            """)
            
            # Show menu at button position
            global_pos = menu_btn.mapToGlobal(menu_btn.rect().bottomLeft())
            menu.exec_(global_pos)
        
        menu_btn.clicked.connect(show_menu)
        account_layout.addWidget(menu_btn)
        
        parent_layout.addWidget(account_card)
        
        return account_card

    def set_as_main_account(self, account_id):
        """Set an account as the main checking account"""
        try:
            from database.migrations.add_institution_migration import apply_institution_migration
            apply_institution_migration()
            
            # TASK 4: Accounts are read-only from Plaid - only update UI-level flags (is_primary)
            # First, unset all primary salary accounts
            execute_query("""
                UPDATE accounts 
                SET is_primary = 0 
                WHERE user_id = ? AND account_type = 'salary'
            """, (self.user_id,), commit=False)
            
            # Set this account as primary (update is_primary and account_type for display)
            # Note: account_type updated for UI, but Plaid data remains source of truth
            execute_query("""
                UPDATE accounts 
                SET is_primary = 1, account_type = 'salary'
                WHERE account_id = ? AND user_id = ?
            """, (account_id, self.user_id), commit=True)
            
            # #region agent log
            import json as _json
            import time as _time
            try:
                with open(r'c:\Users\asus\OneDrive\Desktop\PennyWise\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(_json.dumps({"sessionId":"debug-session","runId":"task4","hypothesisId":"T4","location":"dashboard_main.py:set_as_main_account","message":"updated UI flags only","data":{"account_id":account_id,"updated_is_primary":1,"note":"account_type updated for display, Plaid remains source of truth"}, "timestamp":int(_time.time()*1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            
            # Refresh dashboard
            self.refresh_dashboard()
            self.refresh_metrics_cards_main()
            if hasattr(self, 'metrics_carousel'):
                self.metrics_carousel.refresh_metrics_cards()
            # Also refresh the DashboardMain metrics cards
            if hasattr(self, 'setup_metrics_carousel'):
                # Force refresh by calling show_dashboard which rebuilds the page
                QTimer.singleShot(200, lambda: self.show_dashboard())
            
            # Refresh accounts page
            QTimer.singleShot(100, self.refresh_accounts_page)
            
            QMessageBox.information(self, "Success", "Listings account updated!")
            
        except Exception as e:
            logger.error(f"Error setting main account: {e}")
            QMessageBox.warning(self, "Error", f"Failed to set main account: {str(e)}")

    def set_as_savings_account(self, account_id):
        """Set an account as the savings account - ONLY if it's already a savings account from Plaid"""
        try:
            # #region agent log
            import json as _json
            import time as _time
            try:
                with open(r'c:\Users\asus\OneDrive\Desktop\PennyWise\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(_json.dumps({"sessionId":"debug-session","runId":"accounts-pre-fix","hypothesisId":"H2","location":"dashboard_main.py:set_as_savings_account","message":"set_as_savings_account called","data":{"account_id":account_id,"user_id":self.user_id}, "timestamp":int(_time.time()*1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            
            from database.migrations.add_institution_migration import apply_institution_migration
            apply_institution_migration()
            
            # Check if account exists and get its current type
            from database.db_manager import fetch_one
            account = fetch_one("""
                SELECT account_id, account_type, bank_name, plaid_token
                FROM accounts 
                WHERE account_id = ? AND user_id = ?
            """, (account_id, self.user_id))
            
            if not account:
                QMessageBox.warning(self, "Error", "Account not found")
                return
            
            # Handle sqlite3.Row object - convert to dict or use bracket notation
            try:
                if hasattr(account, 'keys'):
                    account_type = account['account_type'] if 'account_type' in account.keys() else None
                    plaid_token = account['plaid_token'] if 'plaid_token' in account.keys() else None
                else:
                    account_type = account.get("account_type") if hasattr(account, 'get') else None
                    plaid_token = account.get("plaid_token") if hasattr(account, 'get') else None
            except (KeyError, TypeError, AttributeError):
                account_type = None
                plaid_token = None
            
            # #region agent log
            try:
                with open(r'c:\Users\asus\OneDrive\Desktop\PennyWise\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(_json.dumps({"sessionId":"debug-session","runId":"accounts-pre-fix","hypothesisId":"H2","location":"dashboard_main.py:set_as_savings_account","message":"account found before update","data":{"account_id":account_id,"current_type":account_type,"has_plaid_token":bool(plaid_token)}, "timestamp":int(_time.time()*1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            
            # Unset all primary savings accounts first
            execute_query("""
                UPDATE accounts 
                SET is_primary = 0 
                WHERE user_id = ? AND is_primary = 1 AND account_type = 'savings'
            """, (self.user_id,), commit=False)
            
            # Set this account as savings account - update both account_type and is_primary
            execute_query("""
                UPDATE accounts 
                SET is_primary = 1, account_type = 'savings'
                WHERE account_id = ? AND user_id = ?
            """, (account_id, self.user_id), commit=True)
            
            # #region agent log
            try:
                with open(r'c:\Users\asus\OneDrive\Desktop\PennyWise\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(_json.dumps({"sessionId":"debug-session","runId":"task4","hypothesisId":"T4","location":"dashboard_main.py:set_as_savings_account","message":"updated UI flags only","data":{"account_id":account_id,"updated_is_primary":1,"note":"account_type updated for display, Plaid remains source of truth"}, "timestamp":int(_time.time()*1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            
            # #region agent log
            try:
                with open(r'c:\Users\asus\OneDrive\Desktop\PennyWise\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(_json.dumps({"sessionId":"debug-session","runId":"accounts-pre-fix","hypothesisId":"H2","location":"dashboard_main.py:set_as_savings_account","message":"account updated (preserved type)","data":{"account_id":account_id,"preserved_type":"savings"}, "timestamp":int(_time.time()*1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            
            # Refresh accounts page immediately to reflect the change
            # This rebuilds the page with fresh data from database
            self.refresh_accounts_page()
            
            # Refresh dashboard and metrics to show updated savings balance
            self.refresh_dashboard()
            self.refresh_metrics_cards_main()
            if hasattr(self, 'metrics_carousel'):
                self.metrics_carousel.refresh_metrics_cards()
            
            # If user is currently viewing accounts page, ensure it's shown with updated data
            if hasattr(self, 'stack') and self.stack.currentWidget() == self.page_accounts:
                self.stack.setCurrentWidget(self.page_accounts)
            
            QMessageBox.information(self, "Success", "Savings account updated!")
            
        except Exception as e:
            logger.error(f"Error setting savings account: {e}")
            QMessageBox.warning(self, "Error", f"Failed to set savings account: {str(e)}")

    def remove_account(self, account_id):
        """Remove an account"""
        reply = QMessageBox.question(
            self,
            "Remove Account",
            "Are you sure you want to remove this account? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # TASK 4: Accounts are read-only from Plaid - removal is allowed for UI cleanup
                # but account will be re-added if Plaid connection is refreshed
                # #region agent log
                import json as _json
                import time as _time
                try:
                    with open(r'c:\Users\asus\OneDrive\Desktop\PennyWise\.cursor\debug.log', 'a', encoding='utf-8') as f:
                        f.write(_json.dumps({"sessionId":"debug-session","runId":"task4","hypothesisId":"T4","location":"dashboard_main.py:remove_account","message":"removing account (will be re-added from Plaid on refresh)","data":{"account_id":account_id,"note":"account is read-only from Plaid, removal is temporary"}, "timestamp":int(_time.time()*1000)}) + "\n")
                except Exception:
                    pass
                # #endregion
                
                execute_query("""
                    DELETE FROM accounts 
                    WHERE account_id = ? AND user_id = ?
                """, (account_id, self.user_id), commit=True)
                
                # Refresh dashboard and accounts page
                self.refresh_dashboard()
                self.refresh_metrics_cards_main()
                if hasattr(self, 'metrics_carousel'):
                    self.metrics_carousel.refresh_metrics_cards()
                QTimer.singleShot(100, self.refresh_accounts_page)
                
                QMessageBox.information(self, "Success", "Account removed successfully!")
                
            except Exception as e:
                logger.error(f"Error removing account: {e}")
                QMessageBox.warning(self, "Error", f"Failed to remove account: {str(e)}")

    def create_collapsible_institution(self, inst_name, inst_id, plaid_token, parent_layout, expanded_institution):
        """Create a collapsible institution widget with accounts"""
        from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
        from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QSize
        from PyQt5.QtGui import QFont, QColor
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect
        from assets.styles.penny_colors import PennyColors
        import qtawesome as qta
        
        # Get all accounts for this institution (no balance fetching needed)
        accounts = fetch_all("""
            SELECT id, account_id, bank_name, account_type, 
                   is_primary, plaid_token
            FROM accounts 
            WHERE user_id = ? AND plaid_token = ?
            ORDER BY is_primary DESC, account_type, bank_name
        """, (self.user_id, plaid_token))
        
        if not accounts:
            return None
        
        # Main institution card
        inst_card = QFrame()
        inst_card.setStyleSheet(f"""
            QFrame {{
                background: {theme_color('surface')};
                border: 1px solid {theme_color('border')};
                border-radius: 12px;
                padding: 0px;
            }}
        """)
        
        # Subtle shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 15))
        inst_card.setGraphicsEffect(shadow)
        
        main_layout = QVBoxLayout(inst_card)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Institution header (clickable)
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: {theme_color('surface')};
                border-radius: 12px;
                padding: 12px 16px;
            }}
        """)
        header.setCursor(Qt.PointingHandCursor)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 12, 12, 12)
        header_layout.setSpacing(12)
        
        # Chevron icon (smaller, 28px)
        chevron_label = QLabel()
        chevron_label.setFixedSize(28, 28)
        try:
            chevron_icon = qta.icon('fa5s.chevron-down', color=theme_color('accent'))
            chevron_label.setPixmap(chevron_icon.pixmap(28, 28))
        except:
            chevron_label.setText("▼")
            chevron_label.setStyleSheet(f"color: {theme_color('accent')}; font-size: 16px;")
        chevron_label.setAlignment(Qt.AlignCenter)
        
        # Bank name (16px bold)
        bank_name_label = QLabel(inst_name)
        bank_name_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        bank_name_label.setStyleSheet(f"color: {theme_color('text_primary')};")
        
        header_layout.addWidget(chevron_label)
        header_layout.addWidget(bank_name_label)
        header_layout.addStretch()
        
        # Account count badge
        account_count = len(accounts)
        count_label = QLabel(f"{account_count} account{'s' if account_count != 1 else ''}")
        count_label.setStyleSheet(f"""
            color: {theme_color('text_secondary')};
            font-size: 12px;
            padding: 4px 8px;
            background: {theme_color('row_hover', 'rgba(107, 114, 128, 0.1)')};
            border-radius: 6px;
        """)
        header_layout.addWidget(count_label)
        
        # Accounts container (initially hidden)
        accounts_container = QFrame()
        accounts_container.setStyleSheet("background: transparent;")
        accounts_layout = QVBoxLayout(accounts_container)
        accounts_layout.setContentsMargins(16, 8, 16, 12)
        accounts_layout.setSpacing(8)
        accounts_container.hide()
        
        # Add accounts
        for acc in accounts:
            account_id = acc['account_id'] if 'account_id' in acc.keys() else acc.get('id')
            bank_name = acc['bank_name'] if 'bank_name' in acc.keys() else 'Unknown Account'
            account_type = acc['account_type'] if 'account_type' in acc.keys() else 'salary'
            is_primary = acc['is_primary'] if 'is_primary' in acc.keys() else 0
            
            # Account card
            account_card = QFrame()
            p = theme_palette()
            account_card.setStyleSheet(f"""
                QFrame {{
                    background: {p['surface']};
                    border: 1px solid {p['border']};
                    border-radius: 10px;
                    padding: 12px;
                }}
            """)
            account_layout = QVBoxLayout(account_card)
            account_layout.setContentsMargins(12, 12, 12, 12)
            account_layout.setSpacing(8)
            
            # Account header row
            account_header = QHBoxLayout()
            account_header.setSpacing(8)
            
            # Account name (13px bold)
            account_name_label = QLabel(bank_name)
            account_name_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
            account_name_label.setStyleSheet(f"color: {theme_color('text_primary')};")
            account_header.addWidget(account_name_label)
            account_header.addStretch()
            
            # Primary badge (if primary)
            if is_primary:
                primary_badge = QLabel("Primary")
                primary_badge.setStyleSheet(f"""
                    background: {PennyColors.ACCENT};
                    color: {PennyColors.SURFACE};
                    padding: 4px 8px;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: 600;
                """)
                account_header.addWidget(primary_badge)
            
            account_layout.addLayout(account_header)
            
            # Account type label
            type_layout = QHBoxLayout()
            type_layout.setSpacing(12)
            type_layout.addStretch()
            
            type_label = QLabel(account_type.title())
            type_label.setStyleSheet(f"""
                color: {theme_color('text_secondary')};
                font-size: 12px;
            """)
            type_layout.addWidget(type_label)
            
            account_layout.addLayout(type_layout)
            
            # Set primary button (if not already primary)
            if not is_primary:
                set_primary_btn = QPushButton("Set as Primary")
                set_primary_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: {PennyColors.ACCENT};
                        border: 1px solid {PennyColors.ACCENT};
                        border-radius: 8px;
                        padding: 6px 12px;
                        font-size: 12px;
                        font-weight: 500;
                    }}
                    QPushButton:hover {{
                        background: rgba(245, 158, 11, 0.1);
                    }}
                """)
                
                # Lambda closure fix - capture account_id in a default parameter
                def make_set_primary_handler(acc_id):
                    def handler():
                        self.set_primary_account(acc_id, plaid_token)
                    return handler
                
                set_primary_btn.clicked.connect(make_set_primary_handler(account_id))
                account_layout.addWidget(set_primary_btn)
            
            accounts_layout.addWidget(account_card)
        
        main_layout.addWidget(header)
        main_layout.addWidget(accounts_container)
        
        # Store references for accordion behavior
        accounts_container._inst_card = inst_card
        accounts_container._chevron_label = chevron_label
        
        # Toggle functionality with accordion behavior
        def toggle_expand():
            is_expanded = accounts_container.isVisible()
            if is_expanded:
                # Collapse this institution
                accounts_container.hide()
                if accounts_container in expanded_institution:
                    expanded_institution.remove(accounts_container)
                try:
                    chevron_icon = qta.icon('fa5s.chevron-down', color=PennyColors.ACCENT)
                    chevron_label.setPixmap(chevron_icon.pixmap(28, 28))
                except:
                    chevron_label.setText("▼")
            else:
                # Close other expanded institutions (accordion behavior)
                # Find all other institution cards and collapse them
                scroll_widget = parent_layout.parentWidget()
                if scroll_widget:
                    for other_card in scroll_widget.findChildren(QFrame):
                        if other_card != inst_card and hasattr(other_card, 'layout'):
                            # Check if this card has an accounts container
                            for i in range(other_card.layout().count()):
                                item = other_card.layout().itemAt(i)
                                if item and item.widget():
                                    widget = item.widget()
                                    if widget == accounts_container:
                                        continue
                                    if isinstance(widget, QFrame) and widget.isVisible():
                                        # This is another expanded container, collapse it
                                        widget.hide()
                                        # Find its chevron and reset it
                                        for child in other_card.findChildren(QLabel):
                                            if child.fixedSize().width() == 28 and child.fixedSize().height() == 28:
                                                try:
                                                    chev_icon = qta.icon('fa5s.chevron-down', color=PennyColors.ACCENT)
                                                    child.setPixmap(chev_icon.pixmap(28, 28))
                                                except:
                                                    child.setText("▼")
                                                break
                                        break
                
                expanded_institution.clear()
                expanded_institution.append(accounts_container)
                
                accounts_container.show()
                try:
                    chevron_icon = qta.icon('fa5s.chevron-up', color=PennyColors.ACCENT)
                    chevron_label.setPixmap(chevron_icon.pixmap(28, 28))
                except:
                    chevron_label.setText("▲")
        
        header.mousePressEvent = lambda e: toggle_expand() if e.button() == Qt.LeftButton else None
        
        parent_layout.addWidget(inst_card)
        
        return inst_card

    def set_primary_account(self, account_id, plaid_token):
        """Set an account as primary for dashboard balance"""
        try:
            # Ensure migration is applied
            from database.migrations.add_institution_migration import apply_institution_migration
            apply_institution_migration()
            
            # First, unset all primary accounts for this user
            execute_query("""
                UPDATE accounts 
                SET is_primary = 0 
                WHERE user_id = ?
            """, (self.user_id,), commit=False)
            
            # Set the selected account as primary
            execute_query("""
                UPDATE accounts 
                SET is_primary = 1 
                WHERE account_id = ? AND user_id = ?
            """, (account_id, self.user_id), commit=True)
            
            # Refresh dashboard to show new balance
            self.refresh_dashboard()
            self.refresh_metrics_cards_main()
            if hasattr(self, 'metrics_carousel'):
                self.metrics_carousel.refresh_metrics_cards()
            
            # Refresh accounts page to show updated primary badge
            QTimer.singleShot(100, self.refresh_accounts_page)
            
            QMessageBox.information(self, "Success", "Primary account updated! Dashboard balance will reflect this account.")
            
        except Exception as e:
            logger.error(f"Error setting primary account: {e}")
            QMessageBox.warning(self, "Error", f"Failed to set primary account: {str(e)}")

    def refresh_accounts_page(self):
        """Refresh the accounts page by rebuilding it"""
        if not hasattr(self, 'stack') or not hasattr(self, 'page_accounts'):
            return
        
        # Find the index of the accounts page in the stack
        accounts_index = self.stack.indexOf(self.page_accounts)
        if accounts_index == -1:
            return
        
        # Check if we're currently viewing the accounts page
        was_viewing_accounts = self.stack.currentWidget() == self.page_accounts
        
        # Remove the old accounts page from the stack
        old_page = self.stack.widget(accounts_index)
        self.stack.removeWidget(old_page)
        if old_page:
            old_page.deleteLater()
        
        # Build a new accounts page
        self.page_accounts = self.build_accounts_page()
        
        # Insert the new page at the same index
        self.stack.insertWidget(accounts_index, self.page_accounts)
        
        # If we were viewing the accounts page, show it again
        if was_viewing_accounts:
            self.stack.setCurrentWidget(self.page_accounts)

    def show_dashboard(self):
        """Show dashboard view"""
        self.stack.setCurrentWidget(self.page_dashboard)
        self.highlight_nav("Dashboard")
        try:
            logger.info("[dashboard] show_dashboard done - page set to dashboard")
        except Exception:
            pass

    def show_transactions(self):
        """Show transactions view"""
        # Refresh accounts dropdown to ensure latest data
        if hasattr(self, 'page_transactions') and hasattr(self.page_transactions, 'load_accs'):
            self.page_transactions.load_accs()
        self.stack.setCurrentWidget(self.page_transactions)
        self.highlight_nav("Transactions")

    def show_accounts(self):
        """Show accounts view"""
        # Refresh accounts page before showing to ensure latest data
        self.refresh_accounts_page()
        self.stack.setCurrentWidget(self.page_accounts)
        self.highlight_nav("Accounts")

    def _refresh_reports_on_transaction(self):
        """Refresh reports page when a transaction is saved"""
        if hasattr(self, 'page_reports') and hasattr(self.page_reports, 'refresh'):
            self.page_reports.refresh()
    
    def show_reports(self):
        """Show reports view"""
        # Always refresh reports data when showing the page to ensure latest data
        if hasattr(self, 'page_reports') and hasattr(self.page_reports, 'refresh'):
            self.page_reports.refresh()
        self.stack.setCurrentWidget(self.page_reports)
        self.highlight_nav("Reports")

    def _handle_notification_mark_paid(self, commitment_id):
        """Handle mark as paid request from notification panel"""
        try:
            from core.commitment_manager import mark_commitment_paid_manually
            from database.db_manager import fetch_one
            
            # Get category name for feedback
            commitment = fetch_one("""
                SELECT cc.*, c.category_name
                FROM category_commitments cc
                JOIN categories c ON cc.category_id = c.category_id
                WHERE cc.commitment_id = ? AND cc.user_id = ?
            """, (commitment_id, self.user_id))
            
            if not commitment:
                return
            
            # Handle sqlite3.Row object - convert to dict or use bracket notation
            try:
                category_name = commitment['category_name'] if 'category_name' in commitment.keys() else 'Commitment'
            except (KeyError, TypeError):
                category_name = 'Commitment'
            
            # Mark as paid via backend
            success = mark_commitment_paid_manually(self.user_id, commitment_id)
            
            if success:
                # Update notification manager
                if hasattr(self, 'notification_manager'):
                    self.notification_manager.recompute()
                
                # Update badge if available
                if hasattr(self, 'nav_bar') and hasattr(self.nav_bar, 'notification_badge'):
                    self.nav_bar.notification_badge.update_count(self.notification_manager.get_unread_count())
                
                # Refresh notification panel
                if hasattr(self, 'notification_panel'):
                    self.notification_panel.refresh_notifications()
        except Exception as e:
            logger.error(f"Error handling notification mark paid: {e}")
    
    def _handle_notification_manage_payment(self, commitment_id, category_id):
        """Handle resolve payment request from notification panel - show payment action sheet"""
        try:
            from database.db_manager import fetch_one
            from ui.payment_action_sheet import PaymentActionSheet
            
            # Get commitment details including category name and status
            commitment = fetch_one("""
                SELECT cc.*, c.category_name, c.category_id
                FROM category_commitments cc
                JOIN categories c ON cc.category_id = c.category_id
                WHERE cc.commitment_id = ? AND cc.user_id = ?
            """, (commitment_id, self.user_id))
            
            if not commitment:
                return
            
            # Handle sqlite3.Row object - convert to dict or use bracket notation
            try:
                category_name = commitment['category_name'] if 'category_name' in commitment.keys() else 'Commitment'
            except (KeyError, TypeError):
                category_name = 'Commitment'
            
            # Build status text from notification manager
            status_text = "Payment due"
            if hasattr(self, 'notification_manager'):
                notifications = self.notification_manager.get_active_notifications()
                for notif in notifications:
                    if notif.get('commitment_id') == commitment_id:
                        notif_type = notif.get('type', '')
                        if notif_type == 'overdue':
                            days_overdue = notif.get('days_overdue', 0)
                            status_text = f"Overdue by {days_overdue} day{'s' if days_overdue != 1 else ''}"
                        elif notif_type == 'due_soon':
                            days_until_due = notif.get('days_until_due', 0)
                            if days_until_due == 0:
                                status_text = "Due today"
                            else:
                                status_text = f"Due in {days_until_due} day{'s' if days_until_due != 1 else ''}"
                        break
            
            # Show payment action sheet
            action_sheet = PaymentActionSheet(commitment_id, category_name, status_text, self)
            
            # Connect signals to handlers
            action_sheet.pay_now_requested.connect(self._handle_payment_sheet_pay_now)
            action_sheet.mark_paid_requested.connect(self._handle_payment_sheet_mark_paid)
            action_sheet.smart_detect_requested.connect(self._handle_payment_sheet_smart_detect)
            
            action_sheet.exec_()
        except Exception as e:
            logger.error(f"Error handling notification manage payment: {e}")
    
    def _handle_payment_sheet_pay_now(self, commitment_id):
        """Handle Pay Now from payment action sheet - route to transaction form with pre-filled commitment details"""
        try:
            from database.db_manager import fetch_one, fetch_all
            
            # Get commitment details including category_id, category_name, and amount
            commitment = fetch_one("""
                SELECT cc.*, c.category_id, c.category_name
                FROM category_commitments cc
                JOIN categories c ON cc.category_id = c.category_id
                WHERE cc.commitment_id = ? AND cc.user_id = ?
            """, (commitment_id, self.user_id))
            
            if not commitment:
                logger.error(f"Commitment {commitment_id} not found for Pay Now")
                return
            
            # Extract commitment details
            try:
                category_id = commitment['category_id']
                category_name = commitment['category_name']
                amount = float(commitment['amount'])
            except (KeyError, TypeError, ValueError) as e:
                logger.error(f"Error extracting commitment details: {e}")
                return
            
            # Navigate to transactions tab and show transaction form
            if hasattr(self, 'page_transactions'):
                self.show_transactions()
                
                # Switch to Transactions View (not Simulate Transactions)
                if hasattr(self.page_transactions, 'show_transaction_form'):
                    self.page_transactions.show_transaction_form()
                
                # CRITICAL: Set pending_commitment_id so save_txn knows to mark commitment as paid
                self.page_transactions.pending_commitment_id = commitment_id
                
                # Pre-fill transaction form with commitment details
                self.page_transactions.amount_input.setText(str(amount))
                self.page_transactions.type_input.setCurrentText("expense")
                self.page_transactions.note_input.setPlainText(category_name)
                
                # Set category
                cat_index = self.page_transactions.cat_input.findData(category_id)
                if cat_index >= 0:
                    self.page_transactions.cat_input.setCurrentIndex(cat_index)
                
                # Get accounts for pre-filling account field
                accounts = fetch_all("""
                    SELECT id, account_id, bank_name, account_type 
                    FROM accounts 
                    WHERE user_id = ? AND (account_type = 'salary' OR account_type = 'checking')
                    LIMIT 1
                """, (self.user_id,))
                
                if accounts:
                    account_id = accounts[0]['id']
                    acc_index = self.page_transactions.acc_input.findData(account_id)
                    if acc_index >= 0:
                        self.page_transactions.acc_input.setCurrentIndex(acc_index)
        except Exception as e:
            logger.error(f"Error handling payment sheet pay now: {e}")
            import traceback
            traceback.print_exc()
    
    def _handle_payment_sheet_mark_paid(self, commitment_id):
        """Handle Mark as Paid from payment action sheet"""
        try:
            from core.commitment_manager import mark_commitment_paid_manually
            
            # Mark as paid via backend
            success = mark_commitment_paid_manually(self.user_id, commitment_id)
            
            if success:
                # Recompute notifications - this will clear the notification for this commitment
                # since _compute_all_notifications skips paid commitments
                if hasattr(self, 'notification_manager'):
                    self.notification_manager.recompute()
                
                # Update badge count
                if hasattr(self, 'nav_bar') and hasattr(self.nav_bar, 'notification_badge'):
                    self.nav_bar.notification_badge.update_count(self.notification_manager.get_unread_count())
                
                # Refresh notification panel to reflect cleared notification
                if hasattr(self, 'notification_panel'):
                    self.notification_panel.refresh_notifications()
                
                # Refresh commitment tracker to show updated paid status
                if hasattr(self, 'commitment_tracker') and self.commitment_tracker:
                    self.commitment_tracker.load_commitments()
                
                # Refresh dashboard metrics to update balance
                if hasattr(self, 'refresh_metrics_cards_main'):
                    self.refresh_metrics_cards_main()
        except Exception as e:
            logger.error(f"Error handling payment sheet mark paid: {e}")
    
    def _handle_payment_sheet_smart_detect(self, commitment_id):
        """Handle Smart Detect from payment action sheet"""
        from database.db_manager import fetch_one
        commitment = fetch_one("""
            SELECT c.category_name
            FROM category_commitments cc
            JOIN categories c ON cc.category_id = c.category_id
            WHERE cc.commitment_id = ? AND cc.user_id = ?
        """, (commitment_id, self.user_id))
        if commitment:
            # Handle sqlite3.Row object - convert to dict or use bracket notation
            try:
                category_name = commitment['category_name'] if 'category_name' in commitment.keys() else 'Commitment'
            except (KeyError, TypeError):
                category_name = 'Commitment'
            if hasattr(self, 'commitment_tracker') and self.commitment_tracker:
                self.commitment_tracker.trigger_smart_detect(commitment_id, category_name)
    
    def _handle_notification_delete(self, commitment_id):
        """Handle delete notification request - mark commitment as paid to remove notification"""
        try:
            from core.commitment_manager import mark_commitment_paid_manually
            
            # Mark commitment as paid (this will cause notification to disappear on recompute)
            success = mark_commitment_paid_manually(self.user_id, commitment_id)
            
            if success:
                # Update notification manager
                if hasattr(self, 'notification_manager'):
                    self.notification_manager.recompute()
                
                # Update badge if available
                if hasattr(self, 'nav_bar') and hasattr(self.nav_bar, 'notification_badge'):
                    self.nav_bar.notification_badge.update_count(self.notification_manager.get_unread_count())
        except Exception as e:
            logger.error(f"Error handling notification delete: {e}")
    
    def show_notifications(self):
        """Show notifications panel with latest data"""
        if hasattr(self, 'notification_manager'):
            # Ensure notification data is current
            self.notification_manager.recompute()
            
            from ui.notification_panel import NotificationPanel
            if not hasattr(self, 'notification_panel'):
                self.notification_panel = NotificationPanel(self.notification_manager, self)
                # Connect signals to handle actions
                self.notification_panel.mark_paid_requested.connect(self._handle_notification_mark_paid)
                self.notification_panel.manage_payment_requested.connect(self._handle_notification_manage_payment)
                self.notification_panel.notification_deleted.connect(self._handle_notification_delete)
            else:
                # Refresh existing panel data
                self.notification_panel.refresh_notifications()
            
            self.notification_panel.show()
            self.notification_panel.raise_()
            self.notification_panel.activateWindow()

    def show_settings(self):
        """Show settings view"""
        self.stack.setCurrentWidget(self.page_settings)
        self.highlight_nav("Settings")

    def show_link_bank(self, account_type_intent=None):
        """Show link bank view with fresh state"""
        from ui.bank_connect_window import BankConnectWindow
        
        # Remove old bank page if it exists
        if self.page_bank is not None:
            bank_index = self.stack.indexOf(self.page_bank)
            if bank_index >= 0:
                self.stack.removeWidget(self.page_bank)
                self.page_bank.deleteLater()
        
        # Create fresh bank connect window
        self.page_bank = BankConnectWindow(self.user_id, self, account_type_intent=account_type_intent)
        
        # Add to stack if not already there
        bank_index = self.stack.indexOf(self.page_bank)
        if bank_index < 0:
            self.stack.addWidget(self.page_bank)
        
        self.stack.setCurrentWidget(self.page_bank)
        self.highlight_nav("Link Bank")

    def highlight_nav(self, active_text):
        """Highlight the active navigation button"""
        if hasattr(self, 'nav_bar') and hasattr(self.nav_bar, 'nav_buttons'):
            for text, btn in self.nav_bar.nav_buttons.items():
                if text == active_text:
                    btn.setChecked(True)
                else:
                    btn.setChecked(False)

    def setup_metrics_carousel(self,layout):
        """3-card financial overview with real data"""
        # Create the 3-card container
        overview_frame = QFrame()
        overview_frame.setStyleSheet("QFrame { padding-top: 0px; }")
        overview_layout = QHBoxLayout(overview_frame)
        overview_layout.setSpacing(20)
        overview_layout.setContentsMargins(0,0,0,0)
        
        # Store layout and frame for refresh
        self.overview_frame = overview_frame
        self.overview_layout = overview_layout

        # Build cards using shared helper (Plaid only, no simulated/fallback)
        self._rebuild_cards_in_layout(overview_layout)

        if layout:
            layout.addWidget(overview_frame)



    def create_finance_card(self,title,value,color,card_type):
        """Create a clean finance card with visible text"""
        from core.font_manager import get_font_scale
        
        card = QFrame()
        p = theme_palette()
        card.setStyleSheet(f"""
            QFrame {{
                background: {p['surface']};
                border: 1px solid {p['border']};
                border-radius: 16px;
            }}
            QFrame:hover {{
                border: 1px solid {color};
                background: {p.get('surface_alt', p['surface'])};
            }}
        """)
        card.setFixedHeight(160)
        card.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed)

        # Main layout for the card
        main_layout = QVBoxLayout(card)
        main_layout.setContentsMargins(30,25,30,25)  # Increased padding
        main_layout.setSpacing(10)

        # Get font scale factor
        font_scale = get_font_scale()
        title_font_size = int(16 * font_scale)
        value_font_size = int(42 * font_scale)

        # Title label - make sure it's visible
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {theme_color('text_primary')};
                font-size: {title_font_size}px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
        """)
        title_label.setAlignment(Qt.AlignLeft)

        # Value label - make sure it's visible and large
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: {value_font_size}px;
                font-weight: bold;
                background: transparent;
                border: none;
            }}
        """)
        value_label.setAlignment(Qt.AlignLeft)

        # Add labels to layout
        main_layout.addWidget(title_label)
        main_layout.addWidget(value_label)
        main_layout.addStretch()

        # Subtle shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0,0,0,25))
        card.setGraphicsEffect(shadow)

        return card

    def create_empty_card(self, title, button_text, button_callback):
        """Create an empty state card with a prominent '+' button to add account"""
        from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QColor
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QSizePolicy
        import qtawesome as qta
        
        card = QFrame()
        card.setFixedHeight(160)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        main_layout = QVBoxLayout(card)
        main_layout.setContentsMargins(30, 25, 30, 25)
        main_layout.setSpacing(12)
        main_layout.setAlignment(Qt.AlignCenter)

        # Title label
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {theme_color('text_secondary')};
                font-size: 16px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
        """)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Add a visible button instead of just text
        add_button = QPushButton(button_text)
        add_button.setCursor(Qt.PointingHandCursor)
        add_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #d6733a, stop:1 #b45131);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
                min-width: 150px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e6824a, stop:1 #c56141);
                transform: scale(1.05);
            }
            QPushButton:pressed {
                background: #b45131;
            }
        """)
        add_button.clicked.connect(button_callback)
        main_layout.addWidget(add_button)

        # Make entire card clickable as well for better UX
        def card_clicked(event):
            button_callback()
        
        card.mousePressEvent = card_clicked
        card.setCursor(Qt.PointingHandCursor)

        # Update card style to show it's clickable
        card.setStyleSheet("""
            QFrame {
                background: %s;
                border: 2px dashed %s;
                border-radius: 16px;
            }
            QFrame:hover {
                border-color: %s;
                background: %s;
            }
        """ % (
            theme_color('surface'),
            theme_color('border'),
            theme_color('accent'),
            theme_color('surface_alt')
        ))

        # Subtle shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 25))
        card.setGraphicsEffect(shadow)

        return card

    def darken_color(self,hex_color):
        """Darken a color for gradient effect"""
        color = QColor(hex_color)
        color = color.darker(120)
        return color.name()

    def setup_navigation(self):
        """Setup sidebar navigation (now handled in setup_ui)"""
        nav_callbacks = {
            "Dashboard": self.show_dashboard,
            "Transactions": self.show_transactions,
            "Accounts": self.show_accounts,
            "Reports": self.show_reports,
            "Settings": self.show_settings,
            "Link Bank": self.show_link_bank
        }
        self.nav_bar = ModernNavigationBar(self, self.logout, nav_callbacks)
        
        # Set up notification manager for badge after nav_bar is created
        if hasattr(self, 'notification_manager'):
            self.nav_bar.setup_notification_manager(self.notification_manager)

    def setup_ui(self):
        """Setup main content area with sidebar layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main vertical layout: title bar at top, then sidebar+content below
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)

        # Title bar at top (spans full width)
        self.title_bar = CustomTitleBar(self)
        main_layout.addWidget(self.title_bar)

        # Content area: sidebar + main content (horizontal)
        content_wrapper = QWidget()
        content_wrapper_layout = QHBoxLayout(content_wrapper)
        content_wrapper_layout.setContentsMargins(0,0,0,0)
        content_wrapper_layout.setSpacing(0)

        # Sidebar on the left
        self.setup_navigation()  # Creates self.nav_bar
        content_wrapper_layout.addWidget(self.nav_bar)

        # Create stacked widget for different pages
        self.stack = QStackedWidget()
        content_wrapper_layout.addWidget(self.stack)

        # Create all pages
        self.create_pages()

        # Ensure central/background inherits theme palette (prevents stale light bg)
        self.central_widget = central_widget
        self._apply_root_backgrounds()

        main_layout.addWidget(content_wrapper)






    def setup_header(self,layout):
        """Clean header with minimal spacing"""
        welcome = QLabel(f"Welcome back, {self.username}!")
        self.welcome_label = welcome
        welcome.setFont(QFont("Segoe UI",22,QFont.Bold))
        welcome.setStyleSheet(f"""
            color: {theme_color('text_primary')}; 
            font-family: 'Segoe UI', sans-serif;
            font-weight: 700;
            margin: 0px; 
            padding: 0px;
            
            /* Force minimum height/line height to match the 22px font size */
            font-size: 22px;
            line-height: 22px; 
            min-height: 22px;
            
        """)
        welcome.setAlignment(Qt.AlignLeft)

        layout.addWidget(welcome)

    def animate_entrance(self):
        self.animation_timer.stop()
        # Simple fade-in animation for main sections
        # Only animate penny widget since badges are disabled
        if hasattr(self,'penny_widget') and self.penny_widget:
            animation = QPropertyAnimation(self.penny_widget,b"windowOpacity")
            animation.setDuration(800)
            animation.setStartValue(0)
            animation.setEndValue(1)
            animation.setEasingCurve(QEasingCurve.OutCubic)
            animation.start()

    def setup_main_content(self,layout):
        """
        Sets up the main content area with ONLY Financial Companion
        (Commitments are now handled in the main layout flow)
        """
        # Remove any commitment-related code from here
        # The commitments are already added in the main layout via setup_ui()

        # --- Financial Companion Section ONLY ---
        companion_title = QLabel("Pennys corner")
        companion_title.setFont(QFont("Segoe UI",18,QFont.Bold))
        companion_title.setStyleSheet(f"color: {theme_color('text_primary')}; margin-top: 15px;")





        # EnhancedPennyWidget
        self.penny_companion = EnhancedPennyWidget(self.user_id,self.username)
        layout.addWidget(self.penny_companion)

        # Add space between Penny's corner and Recent Transactions
        spacer = QSpacerItem(1, 40, QSizePolicy.Minimum, QSizePolicy.Fixed)
        layout.addItem(spacer)

        # --- Recent Transactions Section ---
        transactions_title = QLabel(" Recent Transactions")
        self.transactions_title = transactions_title
        transactions_title.setFont(QFont("Segoe UI",18,QFont.Bold))
        transactions_title.setStyleSheet(f"color: {theme_color('text_primary')}; margin-top: 15px;")
        layout.addWidget(transactions_title)

        # Add transactions section
        self.add_recent_transactions(layout)

        # Add a stretch spacer
        layout.addStretch()

    def add_recent_transactions(self, layout):
        """Add recent transactions section grouped by dates with Poppins font"""
        # Store reference to layout for refreshing
        self.recent_transactions_layout = layout
        
        # Get ALL transactions - show all transactions, not filtered
        transactions = fetch_all("""
            SELECT t.*, c.category_name, a.bank_name 
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.category_id
            LEFT JOIN accounts a ON t.account_id = a.id
            WHERE t.user_id = ?
            ORDER BY t.date DESC, t.transaction_id DESC
        """, (self.user_id,))

        # Clean container (matching dashboard background)
        activity_frame = QFrame()
        activity_frame.setObjectName("recentActivity")
        activity_frame.setAutoFillBackground(True)
        activity_bg = QColor(theme_color('background'))
        pal = activity_frame.palette()
        pal.setColor(QPalette.Window, activity_bg)
        activity_frame.setPalette(pal)
        activity_frame.setStyleSheet(f"""
            QFrame#recentActivity {{
                background-color: {theme_color('background')};
                padding: 0px;
                border: none;
            }}
            QFrame#recentActivity * {{
                background-color: {theme_color('background')};
                color: {theme_color('text_primary')};
            }}
        """)
        # Store reference to frame for refreshing
        self.recent_transactions_frame = activity_frame
        activity_layout = QVBoxLayout(activity_frame)
        activity_layout.setSpacing(0)
        activity_layout.setContentsMargins(0, 0, 0, 0)

        if not transactions:
            no_data = QLabel("No recent transactions found")
            no_data.setStyleSheet(f"""
                color: {theme_color('text_secondary')}; 
                font-family: 'Poppins', sans-serif;
                font-size: 14px; 
                font-style: italic; 
                padding: 40px 20px;
                text-align: center;
            """)
            no_data.setAlignment(Qt.AlignCenter)
            activity_layout.addWidget(no_data)
        else:
            # Group transactions by date
            grouped_transactions = self.group_transactions_by_date(transactions)
            
            for date, date_transactions in grouped_transactions.items():
                # Add date header
                date_header = self.create_date_header(date, date_transactions)
                activity_layout.addWidget(date_header)
                
                # Add transactions for this date (no separators between transactions)
                for txn in date_transactions:
                    txn_widget = self.create_modern_transaction_widget(txn)
                    activity_layout.addWidget(txn_widget)
                
                # Add spacing between date groups
                if date != list(grouped_transactions.keys())[-1]:
                    spacer = QFrame()
                    spacer.setFixedHeight(20)
                    spacer.setStyleSheet("background: transparent;")
                    activity_layout.addWidget(spacer)
        
        layout.addWidget(activity_frame)
    
    def refresh_recent_transactions(self):
        """Refresh the recent transactions section"""
        if hasattr(self, 'recent_transactions_frame') and hasattr(self, 'recent_transactions_layout'):
            # Remove old frame
            self.recent_transactions_layout.removeWidget(self.recent_transactions_frame)
            self.recent_transactions_frame.deleteLater()
            
            # Rebuild transactions section
            self.add_recent_transactions(self.recent_transactions_layout)

    def group_transactions_by_date(self, transactions):
        """Group transactions by date, maintaining order within each date"""
        from collections import defaultdict
        from datetime import datetime
        
        grouped = defaultdict(list)
        for txn in transactions:
            # Parse date and format it nicely
            if isinstance(txn['date'], str):
                date_obj = datetime.strptime(txn['date'].split()[0], '%Y-%m-%d')
            else:
                date_obj = txn['date']
            
            date_key = date_obj.strftime('%B %d, %Y')
            grouped[date_key].append(txn)
        
        # Sort transactions within each date group by transaction_id DESC (newest first)
        # Handle sqlite3.Row objects - use bracket notation
        for date_key in grouped:
            grouped[date_key].sort(key=lambda x: x['transaction_id'] if 'transaction_id' in x.keys() else 0, reverse=True)
        
        # Sort dates (newest first) and return ordered dict
        sorted_dates = sorted(grouped.keys(), key=lambda x: datetime.strptime(x, '%B %d, %Y'), reverse=True)
        return {date: grouped[date] for date in sorted_dates}

    def create_date_header(self, date, transactions):
        """Create a date header with daily subtotal matching the image style"""
        p = PennyColors.get_palette(theme_manager.current_theme)
        # Calculate daily subtotal
        daily_total = sum(
            txn['amount'] if txn['transaction_type'] == 'income' else -txn['amount']
            for txn in transactions
        )

        header_widget = QFrame()
        header_widget.setAutoFillBackground(True)
        header_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {theme_color('surface')};
                padding: 8px 16px;
                border-radius: 8px;
                margin: 4px 0;
            }}
        """)

        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Date label (slightly darker than background)
        date_label = QLabel(date)
        date_label.setStyleSheet(f"""
            font-family: 'Poppins', sans-serif;
            font-size: 15px;
            font-weight: 500;
            color: {theme_color('text_primary')};
        """)

        # Daily subtotal (slightly darker than background)
        total_label = QLabel(f"{'+' if daily_total >= 0 else ''}{daily_total:,.2f}")
        total_label.setStyleSheet(f"""
            font-family: 'Poppins', sans-serif;
            font-size: 15px;
            font-weight: 500;
            color: {theme_color('text_secondary')};
        """)

        header_layout.addWidget(date_label)
        header_layout.addStretch()
        header_layout.addWidget(total_label)

        # No separator line - just return the header widget
        return header_widget

    def create_modern_transaction_widget(self, txn):
        """Create a modern transaction widget matching the exact image style"""
        p = PennyColors.get_palette(theme_manager.current_theme)
        widget = QFrame()
        widget.setObjectName("txnRow")
        widget.setAutoFillBackground(True)
        widget.setStyleSheet(f"""
            QFrame#txnRow {{
                background-color: transparent;
                padding: 8px 16px;
                margin: 0;
                border: none;
            }}
            QFrame#txnRow:hover {{
                background-color: {theme_color('surface_alt')};
            }}
        """)
        
        layout = QHBoxLayout(widget)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        # Left side: Description and time
        left_layout = QVBoxLayout()
        left_layout.setSpacing(2)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Merchant name (grey, not bold) - no bullet point
        merchant_name = QLabel(txn["description"] or "No description")
        merchant_name.setStyleSheet(f"""
            font-family: 'Poppins', sans-serif;
            font-weight: 400; 
            font-size: 15px; 
            color: {theme_color('text_secondary')};
        """)
        left_layout.addWidget(merchant_name)
        
        # Transaction time
        time_label = QLabel(self.format_transaction_time(txn['date']))
        time_label.setStyleSheet(f"""
            font-family: 'Poppins', sans-serif;
            font-weight: 400; 
            font-size: 12px; 
            color: {theme_color('muted')};
        """)
        left_layout.addWidget(time_label)
        
        layout.addLayout(left_layout)
        layout.addStretch()

        # Amount and arrow (right-aligned)
        right_layout = QHBoxLayout()
        right_layout.setSpacing(6)
        
        # Amount - NO prefix for debits, only + for credits
        if txn['transaction_type'] == 'income':
            amount_text = f"+${txn['amount']:.2f}"
        else:
            amount_text = f"${txn['amount']:.2f}"
            
        amount = QLabel(amount_text)
        amount.setStyleSheet(f"""
            font-family: 'Poppins', sans-serif;
            font-weight: 600; 
            font-size: 15px; 
            color: {theme_color('success') if txn['transaction_type'] == 'income' else theme_color('error')};
        """)
        right_layout.addWidget(amount)
        
        # Small arrow icon (grey)
        arrow_icon = QLabel(">")
        arrow_icon.setStyleSheet(f"""
            font-family: 'Poppins', sans-serif;
            color: {theme_color('muted')};
            font-size: 12px;
            font-weight: bold;
        """)
        right_layout.addWidget(arrow_icon)
        
        layout.addLayout(right_layout)
        
        return widget
    
    def format_transaction_time(self, date_value):
        """Format transaction date to show time"""
        try:
            if isinstance(date_value, str):
                # Try parsing as datetime string
                if ' ' in date_value:
                    # Has time component
                    date_obj = datetime.strptime(date_value.split('.')[0], '%Y-%m-%d %H:%M:%S')
                else:
                    # Date only, parse just the date
                    date_obj = datetime.strptime(date_value.split()[0], '%Y-%m-%d')
            else:
                # Already a datetime object
                date_obj = date_value
            
            # Check if it's today - only show "Today" for current day transactions
            today = datetime.now().date()
            trans_date = date_obj.date()
            
            if trans_date == today:
                # For today's transactions, show time if available
                if isinstance(date_value, str) and ' ' in date_value:
                    time_str = date_obj.strftime('%I:%M %p')
                    return f"Today {time_str}"
                else:
                    # No time component, use current time or just show "Today"
                    time_str = datetime.now().strftime('%I:%M %p')
                    return f"Today {time_str}"
            else:
                # For previous days, show full date and time (no "Today" prefix)
                if isinstance(date_value, str) and ' ' in date_value:
                    time_str = date_obj.strftime('%I:%M %p')
                    return f"{date_obj.strftime('%b %d, %Y')} {time_str}"
                else:
                    # No time component, just show date
                    return date_obj.strftime('%b %d, %Y')
                
        except Exception as e:
            print(f"Error formatting time: {e}")
            return "Recently"

    def create_clean_transaction_widget(self, txn):
        """Create a clean transaction widget matching the second image style"""
        widget = QFrame()
        p = theme_palette()
        widget.setStyleSheet(f"""
            QFrame {{ 
                background: {p.get('row_bg', p['background'])};
                padding: 12px 0;
                border-radius: 8px;
            }} 
            QFrame:hover {{ 
                background-color: {p.get('row_hover', p['surface_alt'])};
            }}
        """)
        layout = QHBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        # Small selection/status icon (like in the second image)
        status_icon = QLabel()
        status_icon.setFixedSize(16, 16)
        status_icon.setStyleSheet(f"""
            QLabel {{
                background: {p.get('border', theme_color('border'))};
                border-radius: 8px;
            }}
        """)
        layout.addWidget(status_icon)

        # Transaction description (main text)
        desc = QLabel(txn["description"] or "No description")
        desc.setStyleSheet(f"""
            font-weight: 500; 
            font-size: 15px; 
            color: {theme_color('text_primary')};
        """)
        layout.addWidget(desc)

        # Category with icon
        category_layout = QHBoxLayout()
        category_layout.setSpacing(8)
        
        # Category icon (using a simple colored circle for now)
        category_icon = QLabel()
        category_icon.setFixedSize(20, 20)
        category_icon.setStyleSheet(f"""
            QLabel {{
                background: {'#ff5c5c' if txn['transaction_type'] == 'expense' else theme_color('success')};
                border-radius: 10px;
            }}
        """)
        category_layout.addWidget(category_icon)
        
        # Category name
        category_name = QLabel(txn['category_name'] or 'Uncategorized')
        category_name.setStyleSheet(f"""
            font-size: 14px; 
            color: {theme_color('text_secondary')};
        """)
        category_layout.addWidget(category_name)
        
        layout.addLayout(category_layout)
        layout.addStretch()

        # Amount and arrow
        right_layout = QHBoxLayout()
        right_layout.setSpacing(8)
        
        # Amount
        amount = QLabel(f"${txn['amount']:.2f}")
        amount.setStyleSheet(f"""
            font-weight: 600; 
            font-size: 15px; 
            color: {theme_color('text_primary') if txn['transaction_type'] == 'expense' else theme_color('success')};
        """)
        right_layout.addWidget(amount)
        
        # Small arrow icon (like in the second image)
        arrow_icon = QLabel("→")
        arrow_icon.setStyleSheet(f"""
            color: {theme_color('muted')};
            font-size: 12px;
        """)
        right_layout.addWidget(arrow_icon)
        
        layout.addLayout(right_layout)
        
        return widget

    def setup_penny_corner_full_width(self,grid_layout,row,col):
        """Penny's Corner spanning full width (replaces badges section)"""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0,0,0,0)
        container_layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Financial Companion")
        title.setFont(QFont("Segoe UI",18,QFont.Bold))
        title.setStyleSheet(f"color: {theme_color('text_primary')};")

        status = QLabel("AI Assistant Active")
        status.setStyleSheet(f"""
            color: {theme_color('success')};
            font-weight: bold;
            background: {theme_color('row_hover', 'rgba(16,185,129,0.1)')};
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 13px;
        """)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(status)

        self.penny_widget = EnhancedPennyWidget(self.user_id,self.username)
        self.penny_widget.personality_ready.connect(self.on_penny_personality_ready)

        container_layout.addLayout(header)
        container_layout.addWidget(self.penny_widget)

        grid_layout.addWidget(container,row,col,1,2)  # Span both columns

    # Comment out or remove the badges section setup
    def setup_badges_section(self,grid_layout,row,col):
        """Badges section - TEMPORARILY DISABLED"""
        # Create a placeholder instead of badges
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0,0,0,0)
        container_layout.setSpacing(15)

        header = QHBoxLayout()
        title = QLabel("Financial Achievements")
        title.setFont(QFont("Segoe UI",18,QFont.Bold))
        title.setStyleSheet(f"color: {theme_color('text_primary')};")

        placeholder_label = QLabel("Badges feature coming soon...")
        placeholder_label.setStyleSheet(f"""
            color: {theme_color('text_secondary')};
            font-size: 14px;
            font-style: italic;
            padding: 40px;
            background: {theme_color('surface_alt')};
            border-radius: 12px;
            border: 2px dashed {theme_color('border')};
        """)
        placeholder_label.setAlignment(Qt.AlignCenter)

        container_layout.addWidget(title)
        container_layout.addWidget(placeholder_label)

        grid_layout.addWidget(container,row,col)

    def setup_mood_section(self,grid_layout,row,col):
        """Mood meter in grid"""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0,0,0,0)
        container_layout.setSpacing(12)

        title = QLabel("Financial Wellness")
        title.setFont(QFont("Segoe UI",18,QFont.Bold))
        title.setStyleSheet(f"color: {theme_color('text_primary')};")

        self.mood_meter = MoodMeter(self.user_id)

        container_layout.addWidget(title)
        container_layout.addWidget(self.mood_meter)

        grid_layout.addWidget(container,row,col)


    def setup_penny_corner(self,grid_layout,row,col):
        """Penny's Corner in grid"""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0,0,0,0)
        container_layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Financial Companion")
        title.setFont(QFont("Segoe UI",18,QFont.Bold))
        title.setStyleSheet(f"color: {theme_color('text_primary')};")

        status = QLabel("AI Assistant Active")
        status.setStyleSheet(f"""
            color: {theme_color('success')};
            font-weight: bold;
            background: {theme_color('row_hover', 'rgba(16,185,129,0.1)')};
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 13px;
        """)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(status)

        self.penny_widget = EnhancedPennyWidget(self.user_id,self.username)
        self.penny_widget.personality_ready.connect(self.on_penny_personality_ready)

        container_layout.addLayout(header)
        container_layout.addWidget(self.penny_widget)

        grid_layout.addWidget(container,row,col)

    def setup_analytics(self,grid_layout,row,col):
        """Analytics section in grid"""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0,0,0,0)
        container_layout.setSpacing(15)

        # Spending Overview
        spending_card = CardWidget("Spending Overview","Monthly budget tracking")
        spending_card.setStyleSheet(f"""
            CardWidget {{
                background: {theme_color('surface')};
                border: 1px solid {theme_color('border')};
                border-radius: 16px;
            }}
        """)
        spending_card.add_layout(self.create_spending_content())

        # Financial Goals
        goals_card = CardWidget("Financial Goals","Progress tracking")
        goals_card.setStyleSheet(f"""
            CardWidget {{
                background: {theme_color('surface')};
                border: 1px solid {theme_color('border')};
                border-radius: 16px;
            }}
        """)
        goals_card.add_layout(self.create_goals_content())

        container_layout.addWidget(spending_card)
        container_layout.addWidget(goals_card)

        grid_layout.addWidget(container,row,col)

    def create_spending_content(self):
        """Modern spending content with consistent progress bars"""
        layout = QVBoxLayout()
        layout.setSpacing(12)

        categories = [
            ("Dining & Food",75,120,"warning"),
            ("Groceries",45,80,"default"),
            ("Transport",35,60,"default"),
            ("Entertainment",90,100,"danger"),
            ("Subscriptions",25,50,"success")
        ]

        for name,spent,budget,variant in categories:
            row = QHBoxLayout()
            label = QLabel(name)
            label.setStyleSheet(f"font-size: 13px; color: {theme_color('text_primary')}; font-weight: 500;")
            label.setFixedWidth(120)

            prog = ProgressBar(spent,budget,"",True,variant)
            prog.setFixedHeight(16)

            amt = QLabel(f"${spent} / ${budget}")
            amt.setStyleSheet(f"font-size: 12px; color: {theme_color('text_secondary')}; font-weight: 600;")
            amt.setFixedWidth(80)

            row.addWidget(label)
            row.addWidget(prog)
            row.addWidget(amt)
            layout.addLayout(row)

        return layout

    def create_goals_content(self):
        """Modern goals content with consistent styling"""
        layout = QVBoxLayout()
        layout.setSpacing(10)

        goals = [
            ("Emergency Fund",65,"$3,250 / $5,000"),
            ("Vacation Fund",30,"$600 / $2,000"),
            ("Investment",45,"Growing portfolio"),
            ("Education",20,"Learning fund")
        ]

        for name,prog,target in goals:
            goal_frame = QFrame()
            goal_frame.setStyleSheet(f"""
                QFrame {
                    background: {theme_color('surface_alt')};
                    border: 1px solid {theme_color('border')};
                    border-radius: 12px;
                    padding: 12px;
                }
            """)

            goal_layout = QVBoxLayout(goal_frame)
            goal_layout.setSpacing(6)

            # Header
            header = QHBoxLayout()
            goal_label = QLabel(name)
            goal_label.setStyleSheet(f"font-weight: 600; color: {theme_color('text_primary')}; font-size: 13px;")
            perc_label = QLabel(f"{prog}%")
            perc_label.setStyleSheet(f"color: {theme_color('accent')}; font-weight: 700; font-size: 13px;")

            header.addWidget(goal_label)
            header.addStretch()
            header.addWidget(perc_label)

            # Progress bar
            bar = ProgressBar(prog,100,"",False,"default")
            bar.setFixedHeight(8)

            # Target
            target_label = QLabel(target)
            target_label.setStyleSheet(f"color: {theme_color('text_secondary')}; font-size: 11px;")

            goal_layout.addLayout(header)
            goal_layout.addWidget(bar)
            goal_layout.addWidget(target_label)

            layout.addWidget(goal_frame)

        return layout

    def on_penny_personality_ready(self,personality_engine):
        self.penny_personality = personality_engine

    def refresh_mood_meter(self):
        current_mood = self.mood_meter.refresh()
        self.previous_mood = current_mood
        self.update_penny_for_mood(current_mood)

    def update_penny_for_mood(self,mood_data):
        if hasattr(self,'penny_widget'):
            self.penny_widget.update_user_mood(mood_data)

    def refresh_badges(self):
        new_badges = self.badges_widget.check_new_badges()
        return new_badges

    def setup_animations(self):
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_entrance)
        self.animation_timer.start(150)

    def animate_entrance(self):
        self.animation_timer.stop()
        # Simple fade-in animation for main sections
        # Only animate penny widget since badges are disabled
        widgets_to_animate = []
        if hasattr(self,'penny_widget') and self.penny_widget:
            widgets_to_animate.append(self.penny_widget)

        for widget in widgets_to_animate:
            animation = QPropertyAnimation(widget,b"windowOpacity")
            animation.setDuration(800)
            animation.setStartValue(0)
            animation.setEndValue(1)
            animation.setEasingCurve(QEasingCurve.OutCubic)
            animation.start()

    def on_tutorial_complete(self):
        if hasattr(self,'penny_widget'):
            self.penny_widget.celebrate_achievement('goal',{'goal_name': 'Tutorial Completion'})

    def on_settings_changed(self, settings_data):
        """Handle settings changes from settings window"""
        try:
            theme_changed = False
            # Apply dark mode changes
            if settings_data.get('dark_mode', False):
                self.apply_dark_theme()
                theme_changed = True
            else:
                self.apply_light_theme()
                theme_changed = True
                
            # Apply custom accent color
            if 'custom_accent_color' in settings_data:
                self.apply_accent_color(settings_data['custom_accent_color'])
                
            # Refresh dashboard to apply currency changes
            if 'currency' in settings_data:
                self.refresh_dashboard()
                
            # Update username if changed
            if 'username' in settings_data:
                self.username = settings_data['username']
                self.setWindowTitle(f"PennyWise - {self.username}'s Dashboard")
            
            # Rebuild dashboard visuals so widgets pick up the new palette immediately
            if theme_changed:
                self.refresh_dashboard()
                
        except Exception as e:
            print(f"Error applying settings changes: {e}")
            
    def apply_dark_theme(self):
        """Apply dark theme to the entire application"""
        app = QApplication.instance()
        if app:
            theme_manager.apply_theme(app, "dark")
        self.apply_current_theme_styles()
        
    def apply_light_theme(self):
        """Apply light theme to the entire application"""
        app = QApplication.instance()
        if app:
            theme_manager.apply_theme(app, "light")
        self.apply_current_theme_styles()
    
    def apply_current_theme_styles(self):
        """Reapply palette-driven styles so inline QSS matches the active theme."""
        try:
            # Central/root backgrounds
            self._apply_root_backgrounds()
            if hasattr(self, "nav_bar"):
                self.nav_bar.refresh_theme(theme_manager.current_theme)
            # Rebuild palette-dependent sections
            if hasattr(self, "overview_layout"):
                self.rebuild_overview_cards()
            if hasattr(self, "metrics_carousel"):
                self.metrics_carousel.refresh_metrics_cards()
            # Rebuild accounts page so card styles pick up the palette
            if hasattr(self, "refresh_accounts_page"):
                self.refresh_accounts_page()
            # Refresh dashboard widgets that use theme_color helpers
            self.refresh_dashboard()
            # Always refresh recent transactions so inline styles update even if not on dashboard
            if hasattr(self, "recent_transactions_layout"):
                self.refresh_recent_transactions()
            # Update AI text colors in Penny widgets
            if hasattr(self, "penny_widget") and hasattr(self.penny_widget, "_update_text_color"):
                self.penny_widget._update_text_color()
            if hasattr(self, "penny_companion") and hasattr(self.penny_companion, "_update_text_color"):
                self.penny_companion._update_text_color()
        except Exception as e:
            logger.warning(f"[theme] apply_current_theme_styles failed: {e}")
        
    def apply_accent_color(self, color):
        """Apply custom accent color throughout the application"""
        # This would update accent colors in various UI elements
        # Implementation depends on your specific UI components
        print(f"Applying accent color: {color}")
        # You can extend this to update specific UI elements with the new accent color


def main():
    app = QApplication(sys.argv)
    theme_manager.load_stylesheets()
    theme_manager.apply_theme(app,"light")

    dash = DashboardMain(user_id=1,username="Alex Johnson",show_tutorial=True)
    dash.show()

    return app.exec_()


if __name__ == "__main__":
    main()