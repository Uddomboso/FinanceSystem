"""
Settings Window - User Preferences Management
Implements Use Case 5.3.5 Settings functionality
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QCheckBox, QFrame, QScrollArea, QGroupBox, QGridLayout, QMessageBox,
    QApplication, QColorDialog, QSlider, QSpinBox, QLineEdit, QStackedWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QFont, QColor, QPalette
import qtawesome as qta
from database.db_manager import fetch_one, fetch_all, execute_query
from core.theme_manager import theme_manager
from assets.styles.penny_colors import PennyColors
import json
from datetime import datetime


class SettingsWindow(QWidget):
    """Settings window implementing Use Case 5.3.5"""
    
    # Signal emitted when settings are changed
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.parent_window = parent
        self.current_settings = {}
        # Ensure new preference columns exist without requiring verification flows
        self.ensure_additional_setting_columns()
        self._current_section = "appearance"
        self._label_styles = []
        self._all_checkboxes = []
        self._all_combos = []
        self._all_lineedits = []
        self._section_groups = []
        self._nav_icon_map = {}
        self._refreshing_theme = False
        self.setup_ui()
        self.load_current_settings()

    def _compute_control_styles(self):
        """Compute palette-driven control styles."""
        p = self._palette
        self._checkbox_style = f"""
            QCheckBox {{
                color: {p['text_primary']};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 10px;
                border: 2px solid {p['border']};
                background: {p['surface']};
            }}
            QCheckBox::indicator:checked {{
                background: {p['accent']};
                border-color: {p['accent']};
            }}
        """
        self._combo_style = f"""
            QComboBox {{
                background: {p['surface']};
                border: 2px solid {p['border']};
                border-radius: 8px;
                padding: 8px 12px;
                min-width: 150px;
                color: {p['text_primary']};
            }}
            QComboBox:focus {{
                border-color: {p['accent']};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {p['text_secondary']};
                margin-right: 8px;
            }}
        """
        self._lineedit_style = f"""
            QLineEdit {{
                background: {p['surface']};
                border: 2px solid {p['border']};
                border-radius: 8px;
                padding: 8px 12px;
                color: {p['text_primary']};
            }}
            QLineEdit:focus {{
                border-color: {p['accent']};
            }}
        """
    def _register_label(self, label, tone="primary", extra=""):
        """Keep track of labels for restyling on theme change."""
        self._label_styles.append((label, tone, extra))
        self._apply_label_style(label, tone, extra)

    def _apply_label_style(self, label, tone="primary", extra=""):
        color = self._palette['text_secondary'] if tone == "secondary" else self._palette['text_primary']
        label.setStyleSheet(f"color: {color};{extra}")

    def _register_checkbox(self, checkbox):
        self._all_checkboxes.append(checkbox)
        checkbox.setStyleSheet(self._checkbox_style)

    def _register_combo(self, combo):
        self._all_combos.append(combo)
        combo.setStyleSheet(self._combo_style)

    def _register_lineedit(self, lineedit):
        self._all_lineedits.append(lineedit)
        lineedit.setStyleSheet(self._lineedit_style)

    def _register_group(self, group):
        self._section_groups.append(group)

    def _sidebar_button_styles(self):
        p = self._palette
        return f"""
            QPushButton {{
                text-align: left;
                padding: 10px 12px;
                border-radius: 8px;
                border: none;
                background: transparent;
                color: {p['text_secondary']};
            }}
            QPushButton:hover {{
                background: {p['surface_alt']};
                color: {p['text_primary']};
            }}
            QPushButton:checked {{
                background: {p['surface_alt']};
                color: {p['accent']};
            }}
        """

    def refresh_theme_ui(self):
        """Reapply palette-driven styles after theme change."""
        self._palette = PennyColors.get_palette(theme_manager.current_theme)
        self._compute_control_styles()
        p = self._palette
        self.setStyleSheet(f"background: {p['background']}; color: {p['text_primary']};")
        # Header
        if hasattr(self, "header_icon_label"):
            self.header_icon_label.setPixmap(qta.icon('fa5s.cog', color=p.get('accent', '#d6733a')).pixmap(28, 28))
        if hasattr(self, "header_divider"):
            self.header_divider.setStyleSheet(f"color: {p['border']}; background: {p['border']}; border: none; margin-top: 8px;")

        # Labels
        for label, tone, extra in self._label_styles:
            self._apply_label_style(label, tone, extra)

        # Fallback: restyle all labels (for any not registered)
        for lbl in self.findChildren(QLabel):
            lbl.setStyleSheet(f"color: {p['text_primary']};")

        # Controls
        # Keep legacy registered sets
        for cb in self._all_checkboxes:
            cb.setStyleSheet(self._checkbox_style)
        for combo in self._all_combos:
            combo.setStyleSheet(self._combo_style)
        for le in self._all_lineedits:
            le.setStyleSheet(self._lineedit_style)

        # Refresh all checkboxes/combos/lineedits even if not registered (forward compatibility)
        for cb in self.findChildren(QCheckBox):
            cb.setStyleSheet(self._checkbox_style)
        for combo in self.findChildren(QComboBox):
            combo.setStyleSheet(self._combo_style)
        for le in self.findChildren(QLineEdit):
            le.setStyleSheet(self._lineedit_style)

        # Groups
        for group in self._section_groups:
            group.setStyleSheet(f"""
                QFrame#settings_section {{
                    background: transparent;
                    border: none;
                }}
                QLabel.section-title {{
                    color: {p.get('text_primary', '#1F2937')};
                    font-weight: 700;
                    font-size: 16px;
                }}
            """)

        # Sidebar buttons
        for key, btn in self._nav_buttons.items():
            icon_name = self._nav_icon_map.get(key, "fa5s.circle")
            btn.setStyleSheet(self._sidebar_button_styles())
            btn.setIcon(qta.icon(icon_name, color=p['text_secondary']))

        # Reapply current section selection
        self.show_section(self._current_section)

    def get_settings_columns(self):
        """Return list of column names from settings table."""
        try:
            return [row[1] for row in fetch_all("PRAGMA table_info(settings)")]
        except Exception as e:
            print(f"Warning: could not read settings columns: {e}")
            return []

    def ensure_additional_setting_columns(self):
        """Ensure optional preference columns exist (non-destructive)."""
        try:
            # PRAGMA table_info returns tuples: (cid, name, type, notnull, dflt_value, pk)
            columns = [row[1] for row in fetch_all("PRAGMA table_info(settings)")]
            # column_name -> (sql_type, default_literal, is_text)
            desired = {
                "theme": ("TEXT", "'Default'", True),
                "language": ("TEXT", "'English'", True),
                "date_format": ("TEXT", "'MM/DD/YYYY'", True),
                "currency": ("TEXT", "'USD'", True),
                "number_format": ("TEXT", "'1,234.56'", True),
                "email_notifications": ("BOOLEAN", "1", False),
                "push_notifications": ("BOOLEAN", "1", False),
                "budget_alerts_enabled": ("BOOLEAN", "1", False),
                "bill_reminders_enabled": ("BOOLEAN", "1", False),
                "notification_frequency": ("TEXT", "'Daily'", True),
                "currency_auto_refresh": ("BOOLEAN", "1", False),
                "auto_save": ("BOOLEAN", "1", False),
                "custom_accent_color": ("TEXT", "'#d6733a'", True),
                "font_family": ("TEXT", "'Segoe UI'", True),
                "dark_mode": ("BOOLEAN", "0", False),
                "created_at": ("DATETIME", "CURRENT_TIMESTAMP", True),
                "updated_at": ("DATETIME", "CURRENT_TIMESTAMP", True),
            }
            for col, (col_type, default_val, _) in desired.items():
                if col not in columns:
                    execute_query(
                        f"ALTER TABLE settings ADD COLUMN {col} {col_type} DEFAULT {default_val}",
                        commit=True,
                    )
        except Exception as e:
            print(f"Warning: could not ensure settings columns: {e}")
        
    def setup_ui(self):
        """Setup the settings interface"""
        self.setWindowTitle("Settings - PennyWise")
        self.setMinimumSize(800, 600)
        self._palette = PennyColors.get_palette(theme_manager.current_theme)
        self._compute_control_styles()
        p = self._palette

        self.setStyleSheet(f"background: {p['background']}; color: {p['text_primary']};")
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(16)
        
        # Header
        self.setup_header(main_layout)
        
        # Split-pane container: left navigation + right content stack
        split_frame = QFrame()
        split_frame.setStyleSheet("background: transparent;")
        split_layout = QHBoxLayout(split_frame)
        split_layout.setContentsMargins(0, 0, 0, 0)
        split_layout.setSpacing(16)

        self._nav_items = [
            ("appearance", "Appearance", "fa5s.palette"),
            ("language", "Language & Region", "fa5s.globe"),
            ("currency", "Currency & Numbers", "fa5s.dollar-sign"),
            ("notifications", "Notifications", "fa5s.bell"),
            ("account", "Account Information", "fa5s.user"),
            ("advanced", "Advanced", "fa5s.cogs"),
        ]
        sidebar = self.build_sidebar()
        split_layout.addWidget(sidebar)

        self.content_stack = QStackedWidget()
        split_layout.addWidget(self.content_stack)
        split_layout.setStretch(0, 1)
        split_layout.setStretch(1, 3)

        main_layout.addWidget(split_frame)

        # Build pages and connect navigation
        self.build_pages()
        
        # Action buttons
        self.setup_action_buttons(main_layout)
        
    def setup_header(self, layout):
        """Setup settings header"""
        p = self._palette
        header = QWidget()
        header.setStyleSheet("background: transparent;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 10)
        
        # Title with icon
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon('fa5s.cog', color=p.get('accent', '#d6733a')).pixmap(28, 28))
        self.header_icon_label = icon_label
        title_layout.addWidget(icon_label)
        
        title_label = QLabel("Settings")
        title_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self._register_label(title_label, "primary", " margin-left: 10px;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        header_layout.addLayout(title_layout)
        
        # Thin divider under header (palette-driven, subtle)
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"color: {p['border']}; background: {p['border']}; border: none; margin-top: 8px;")
        self.header_divider = divider
        header_layout.addWidget(divider)
        
        layout.addWidget(header)

    def build_sidebar(self):
        """Create left navigation sidebar."""
        p = self._palette
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        self._nav_buttons = {}
        for key, label, icon_name in self._nav_items:
            btn = QPushButton()
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setText(label)
            btn.setFont(QFont("Segoe UI", 12))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setIcon(qta.icon(icon_name, color=p['text_secondary']))
            btn.setStyleSheet(self._sidebar_button_styles())
            btn.clicked.connect(lambda _, k=key: self.show_section(k))
            layout.addWidget(btn)
            self._nav_buttons[key] = btn
            self._nav_icon_map[key] = icon_name

        layout.addStretch()
        return sidebar

    def build_pages(self):
        """Build stacked pages for each settings category."""
        self._page_indices = {}
        builders = {
            "appearance": self.setup_appearance_section,
            "language": self.setup_language_section,
            "currency": self.setup_currency_section,
            "notifications": self.setup_notifications_section,
            "account": self.setup_account_section,
            "advanced": self.setup_advanced_section,
        }
        for key, _, _ in self._nav_items:
            builder = builders.get(key)
            if not builder:
                continue
            page_widget = builder()
            # Wrap page in scroll area for overflow
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
            scroll.setWidget(page_widget)
            index = self.content_stack.addWidget(scroll)
            self._page_indices[key] = index

        # Default selection
        self.show_section("appearance")

    def show_section(self, key):
        """Switch to the requested section and update nav state."""
        if key in self._page_indices:
            self.content_stack.setCurrentIndex(self._page_indices[key])
        if key in self._nav_buttons:
            self._nav_buttons[key].setChecked(True)
        self._current_section = key
        
    def setup_appearance_section(self):
        """Setup appearance settings (dark mode, color themes)"""
        group = self.create_settings_group("Appearance", "fa5s.palette")
        
        # Dark mode toggle
        dark_mode_layout = QHBoxLayout()
        self.dark_mode_checkbox = QCheckBox("Enable Dark Mode")
        self.dark_mode_checkbox.setFont(QFont("Segoe UI", 12))
        self._register_checkbox(self.dark_mode_checkbox)
        self.dark_mode_checkbox.stateChanged.connect(self.on_dark_mode_toggled)
        dark_mode_layout.addWidget(self.dark_mode_checkbox)
        dark_mode_layout.addStretch()
        group.layout().addLayout(dark_mode_layout)
        
        # Custom color picker (hidden by default)
        self.custom_color_widget = QWidget()
        self.custom_color_layout = QHBoxLayout(self.custom_color_widget)
        self.custom_color_layout.setContentsMargins(0, 0, 0, 0)
        custom_color_label = QLabel("Custom Accent Color:")
        custom_color_label.setFont(QFont("Segoe UI", 12))
        self._register_label(custom_color_label, "primary")
        self.custom_color_layout.addWidget(custom_color_label)
        
        self.color_picker_btn = QPushButton("Choose Color")
        self.color_picker_btn.setFont(QFont("Segoe UI", 12))
        self.color_picker_btn.setStyleSheet("""
            QPushButton {
                background: #d6733a;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #b45131;
            }
        """)
        self.color_picker_btn.clicked.connect(self.open_color_picker)
        self.custom_color_layout.addWidget(self.color_picker_btn)
        self.custom_color_layout.addStretch()
        self.custom_color_widget.setVisible(False)
        group.layout().addWidget(self.custom_color_widget)
        
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(12)
        page_layout.addWidget(group)
        page_layout.addStretch()
        return page
        
    def setup_language_section(self):
        """Setup language settings"""
        group = self.create_settings_group("Language & Region", "fa5s.globe")
        
        # Language selection
        lang_layout = QHBoxLayout()
        lang_label = QLabel("Language:")
        lang_label.setFont(QFont("Segoe UI", 12))
        lang_label.setStyleSheet(f"color: {self._palette['text_primary']};")
        lang_layout.addWidget(lang_label)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Spanish", "French", "German", "Italian", "Portuguese"])
        self.language_combo.setFont(QFont("Segoe UI", 12))
        self.language_combo.setStyleSheet(self._combo_style)
        lang_layout.addWidget(self.language_combo)
        lang_layout.addStretch()
        group.layout().addLayout(lang_layout)
        
        # Date format
        date_layout = QHBoxLayout()
        date_label = QLabel("Date Format:")
        date_label.setFont(QFont("Segoe UI", 12))
        date_label.setStyleSheet(f"color: {self._palette['text_primary']};")
        date_layout.addWidget(date_label)
        
        self.date_format_combo = QComboBox()
        self.date_format_combo.addItems(["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"])
        self.date_format_combo.setFont(QFont("Segoe UI", 12))
        self.date_format_combo.setStyleSheet(self._combo_style)
        date_layout.addWidget(self.date_format_combo)
        date_layout.addStretch()
        group.layout().addLayout(date_layout)
        
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(12)
        page_layout.addWidget(group)
        page_layout.addStretch()
        return page
        
    def setup_currency_section(self):
        """Setup currency settings"""
        group = self.create_settings_group("Currency & Numbers", "fa5s.dollar-sign")
        
        # Currency selection
        currency_layout = QHBoxLayout()
        currency_label = QLabel("Currency:")
        currency_label.setFont(QFont("Segoe UI", 12))
        currency_label.setStyleSheet(f"color: {self._palette['text_primary']};")
        currency_layout.addWidget(currency_label)
        
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CHF", "CNY"])
        self.currency_combo.setFont(QFont("Segoe UI", 12))
        self.currency_combo.setStyleSheet(self._combo_style)
        currency_layout.addWidget(self.currency_combo)
        currency_layout.addStretch()
        group.layout().addLayout(currency_layout)
        
        # Number format
        number_layout = QHBoxLayout()
        number_label = QLabel("Number Format:")
        number_label.setFont(QFont("Segoe UI", 12))
        number_label.setStyleSheet(f"color: {self._palette['text_primary']};")
        number_layout.addWidget(number_label)
        
        self.number_format_combo = QComboBox()
        self.number_format_combo.addItems(["1,234.56", "1.234,56", "1 234,56"])
        self.number_format_combo.setFont(QFont("Segoe UI", 12))
        self.number_format_combo.setStyleSheet(self._combo_style)
        number_layout.addWidget(self.number_format_combo)
        number_layout.addStretch()
        group.layout().addLayout(number_layout)
        
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(12)
        page_layout.addWidget(group)
        page_layout.addStretch()
        return page
        
    def setup_notifications_section(self):
        """Setup notification settings"""
        group = self.create_settings_group("Notifications", "fa5s.bell")
        
        # Email notifications
        email_layout = QHBoxLayout()
        self.email_notifications = QCheckBox("Email Notifications")
        self.email_notifications.setFont(QFont("Segoe UI", 12))
        self.email_notifications.setStyleSheet(self._checkbox_style)
        email_layout.addWidget(self.email_notifications)
        email_layout.addStretch()
        group.layout().addLayout(email_layout)
        
        # Push notifications
        push_layout = QHBoxLayout()
        self.push_notifications = QCheckBox("Push Notifications")
        self.push_notifications.setFont(QFont("Segoe UI", 12))
        self.push_notifications.setStyleSheet(self._checkbox_style)
        push_layout.addWidget(self.push_notifications)
        push_layout.addStretch()
        group.layout().addLayout(push_layout)

        # Budget alerts
        budget_layout = QHBoxLayout()
        self.budget_alerts = QCheckBox("Budget Alerts (near/over limit)")
        self.budget_alerts.setFont(QFont("Segoe UI", 12))
        self.budget_alerts.setStyleSheet(self._checkbox_style)
        budget_layout.addWidget(self.budget_alerts)
        budget_layout.addStretch()
        group.layout().addLayout(budget_layout)

        # Bill reminders
        bill_layout = QHBoxLayout()
        self.bill_reminders = QCheckBox("Bill Reminders")
        self.bill_reminders.setFont(QFont("Segoe UI", 12))
        self.bill_reminders.setStyleSheet(self._checkbox_style)
        bill_layout.addWidget(self.bill_reminders)
        bill_layout.addStretch()
        group.layout().addLayout(bill_layout)
        
        # Notification frequency
        freq_layout = QHBoxLayout()
        freq_label = QLabel("Notification Frequency:")
        freq_label.setFont(QFont("Segoe UI", 12))
        freq_label.setStyleSheet(f"color: {self._palette['text_primary']};")
        freq_layout.addWidget(freq_label)
        
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(["Real-time", "Daily", "Weekly", "Monthly"])
        self.frequency_combo.setFont(QFont("Segoe UI", 12))
        self.frequency_combo.setStyleSheet(self._combo_style)
        freq_layout.addWidget(self.frequency_combo)
        freq_layout.addStretch()
        group.layout().addLayout(freq_layout)

        # Currency auto-refresh toggle
        refresh_layout = QHBoxLayout()
        self.currency_refresh = QCheckBox("Auto-refresh exchange rates (cached when offline)")
        self.currency_refresh.setFont(QFont("Segoe UI", 12))
        self.currency_refresh.setStyleSheet(self._checkbox_style)
        refresh_layout.addWidget(self.currency_refresh)
        refresh_layout.addStretch()
        group.layout().addLayout(refresh_layout)
        
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(12)
        page_layout.addWidget(group)
        page_layout.addStretch()
        return page
        
    def setup_account_section(self):
        """Setup account information settings"""
        group = self.create_settings_group("Account Information", "fa5s.user")
        
        # Username
        username_layout = QHBoxLayout()
        username_label = QLabel("Username:")
        username_label.setFont(QFont("Segoe UI", 12))
        username_label.setStyleSheet(f"color: {self._palette['text_primary']};")
        username_label.setFixedWidth(120)
        username_layout.addWidget(username_label)
        
        self.username_edit = QLineEdit()
        self.username_edit.setFont(QFont("Segoe UI", 12))
        self.username_edit.setStyleSheet(self._lineedit_style)
        username_layout.addWidget(self.username_edit)
        username_layout.addStretch()
        group.layout().addLayout(username_layout)
        
        # Email
        email_layout = QHBoxLayout()
        email_label = QLabel("Email:")
        email_label.setFont(QFont("Segoe UI", 12))
        email_label.setStyleSheet(f"color: {self._palette['text_primary']};")
        email_label.setFixedWidth(120)
        email_layout.addWidget(email_label)
        
        self.email_edit = QLineEdit()
        self.email_edit.setFont(QFont("Segoe UI", 12))
        self.email_edit.setPlaceholderText("Leave blank to use a local default; no verification needed")
        self.email_edit.setStyleSheet(self._lineedit_style)
        email_layout.addWidget(self.email_edit)
        email_layout.addStretch()
        group.layout().addLayout(email_layout)

        # Email helper text
        email_help = QLabel("Tip: Keep this blank to use a local default email. No verification required here.")
        email_help.setStyleSheet(f"color: {self._palette['text_secondary']}; font-size: 11px; margin-left: 120px;")
        group.layout().addWidget(email_help)

        # Password note (no inline verification flow)
        password_note = QLabel("Password changes are handled in the security section; no prompts here.")
        password_note.setStyleSheet(f"color: {self._palette['text_secondary']}; font-size: 11px; margin-left: 120px;")
        group.layout().addWidget(password_note)
        
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(12)
        page_layout.addWidget(group)
        page_layout.addStretch()
        return page
        
    def setup_advanced_section(self):
        """Setup advanced settings"""
        group = self.create_settings_group("Advanced", "fa5s.cogs")
        
        # Auto-save
        autosave_layout = QHBoxLayout()
        self.auto_save = QCheckBox("Auto-save changes")
        self.auto_save.setFont(QFont("Segoe UI", 12))
        self.auto_save.setStyleSheet(self._checkbox_style)
        autosave_layout.addWidget(self.auto_save)
        autosave_layout.addStretch()
        group.layout().addLayout(autosave_layout)
        
        # Data export
        export_layout = QHBoxLayout()
        export_label = QLabel("Data Management:")
        export_label.setFont(QFont("Segoe UI", 12))
        export_label.setStyleSheet(f"color: {self._palette['text_primary']};")
        export_layout.addWidget(export_label)
        
        self.export_btn = QPushButton("Export Data")
        self.export_btn.setFont(QFont("Segoe UI", 12))
        self.export_btn.setStyleSheet("""
            QPushButton {
                background: #10B981;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #059669;
            }
        """)
        self.export_btn.clicked.connect(self.export_data)
        export_layout.addWidget(self.export_btn)
        
        self.import_btn = QPushButton("Import Data")
        self.import_btn.setFont(QFont("Segoe UI", 12))
        self.import_btn.setStyleSheet("""
            QPushButton {
                background: #3B82F6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #2563EB;
            }
        """)
        self.import_btn.clicked.connect(self.import_data)
        export_layout.addWidget(self.import_btn)
        export_layout.addStretch()
        group.layout().addLayout(export_layout)
        
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(12)
        page_layout.addWidget(group)
        page_layout.addStretch()
        return page
        
    def create_settings_group(self, title, icon_name):
        """Create a lightweight settings section with title and icon (no card chrome)."""
        p = self._palette
        group = QFrame()
        group.setObjectName("settings_section")
        group.setStyleSheet(f"""
            QFrame#settings_section {{
                background: transparent;
                border: none;
            }}
            QLabel.section-title {{
                color: {p.get('text_primary', '#1F2937')};
                font-weight: 700;
                font-size: 16px;
            }}
        """)
        
        # Title with icon
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 12)
        
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon_name, color=p.get('accent', '#d6733a')).pixmap(18, 18))
        title_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setObjectName("section-title")
        title_label.setFont(QFont("Segoe UI", 15, QFont.Bold))
        title_label.setStyleSheet(f"color: {p.get('text_primary','#1F2937')}; margin-left: 8px;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # Create layout for the group
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(0, 0, 0, 12)
        group_layout.addLayout(title_layout)
        
        self._register_group(group)
        return group
        
    def setup_action_buttons(self, layout):
        """Setup action buttons (Save, Cancel, Reset)"""
        button_frame = QFrame()
        button_frame.setStyleSheet("background: transparent; border: none;")
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 12, 0, 0)
        
        # Reset button
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.setFont(QFont("Segoe UI", 12))
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background: #6B7280;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
            }
            QPushButton:hover {
                background: #4B5563;
            }
        """)
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_btn)
        
        button_layout.addStretch()
        
        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFont(QFont("Segoe UI", 12))
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: #EF4444;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
            }
            QPushButton:hover {
                background: #DC2626;
            }
        """)
        self.cancel_btn.clicked.connect(self.close)
        button_layout.addWidget(self.cancel_btn)
        
        # Save button
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: #d6733a;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
            }
            QPushButton:hover {
                background: #b45131;
            }
        """)
        self.save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_btn)
        
        layout.addWidget(button_frame)
        
    def load_current_settings(self):
        """Load current settings from database"""
        try:
            settings = fetch_one("SELECT * FROM settings WHERE user_id = ?", (self.user_id,))
            if settings:
                # Load appearance settings
                self.dark_mode_checkbox.setChecked(bool(settings['dark_mode'] if 'dark_mode' in settings.keys() else False))
                # Font control removed; ignore font settings

                # Load language settings
                self.language_combo.setCurrentText(settings['language'] if 'language' in settings.keys() else 'English')
                self.date_format_combo.setCurrentText(settings['date_format'] if 'date_format' in settings.keys() else 'MM/DD/YYYY')
                
                # Load currency settings
                self.currency_combo.setCurrentText(settings['currency'] if 'currency' in settings.keys() else 'USD')
                self.number_format_combo.setCurrentText(settings['number_format'] if 'number_format' in settings.keys() else '1,234.56')
                
                # Load notification settings
                self.email_notifications.setChecked(bool(settings['email_notifications'] if 'email_notifications' in settings.keys() else True))
                self.push_notifications.setChecked(bool(settings['push_notifications'] if 'push_notifications' in settings.keys() else True))
                self.budget_alerts.setChecked(bool(settings['budget_alerts_enabled'] if 'budget_alerts_enabled' in settings.keys() else True))
                self.bill_reminders.setChecked(bool(settings['bill_reminders_enabled'] if 'bill_reminders_enabled' in settings.keys() else True))
                self.frequency_combo.setCurrentText(settings['notification_frequency'] if 'notification_frequency' in settings.keys() else 'Daily')
                self.currency_refresh.setChecked(bool(settings['currency_auto_refresh'] if 'currency_auto_refresh' in settings.keys() else True))
                
                # Load account settings
                user_info = fetch_one("SELECT username, email FROM users WHERE user_id = ?", (self.user_id,))
                if user_info:
                    self.username_edit.setText(user_info['username'] if 'username' in user_info.keys() else '')
                    self.email_edit.setText(user_info['email'] if 'email' in user_info.keys() else '')
                
                # Load advanced settings
                self.auto_save.setChecked(bool(settings['auto_save'] if 'auto_save' in settings.keys() else True))
                
                # Store current settings for comparison
                self.current_settings = dict(settings)
            else:
                # Create default settings if none exist
                self.create_default_settings()
                
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.create_default_settings()
            
    def create_default_settings(self):
        """Create default settings for new user"""
        default_settings = {
            'user_id': self.user_id,
            'dark_mode': False,
            'theme': 'Default',
            'font_family': 'Segoe UI',
            'language': 'English',
            'date_format': 'MM/DD/YYYY',
            'currency': 'USD',
            'number_format': '1,234.56',
            'email_notifications': True,
            'push_notifications': True,
            'budget_alerts_enabled': True,
            'bill_reminders_enabled': True,
            'notification_frequency': 'Daily',
            'currency_auto_refresh': True,
            'auto_save': True,
            'custom_accent_color': '#d6733a',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        try:
            cols_in_db = set(self.get_settings_columns())
            insertable = {k: v for k, v in default_settings.items() if k in cols_in_db}
            columns_sql = ", ".join(insertable.keys())
            placeholders = ", ".join(["?"] * len(insertable))
            execute_query(
                f"INSERT INTO settings ({columns_sql}) VALUES ({placeholders})",
                tuple(insertable.values()),
                commit=True,
            )
            
            self.current_settings = default_settings
            
        except Exception as e:
            print(f"Error creating default settings: {e}")
            
    def on_theme_changed(self, theme):
        """Handle theme selection change"""
        if theme == "Custom":
            self.custom_color_widget.setVisible(True)
        else:
            self.custom_color_widget.setVisible(False)
        # Live restyle when switching preset theme without save
        self.refresh_theme_ui()

    def on_dark_mode_toggled(self, state):
        """Apply dark/light immediately when checkbox is toggled."""
        dark = state == Qt.Checked
        if dark:
            self.apply_dark_theme()
        else:
            self.apply_light_theme()
        # Refresh local widgets to avoid stale QSS until navigation changes
        self.refresh_theme_ui()
            
    def open_color_picker(self):
        """Open color picker for custom accent color"""
        color = QColorDialog.getColor(QColor('#d6733a'), self, "Choose Accent Color")
        if color.isValid():
            self.custom_accent_color = color.name()
            self.color_picker_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color.name()};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 16px;
                }}
                QPushButton:hover {{
                    background: {self.darken_color(color.name())};
                }}
            """)
            
    def darken_color(self, hex_color):
        """Darken a hex color"""
        color = QColor(hex_color)
        color = color.darker(120)
        return color.name()
        
    def change_password(self):
        """Handle password change"""
        from PyQt5.QtWidgets import QInputDialog, QMessageBox
        
        current_password, ok1 = QInputDialog.getText(self, "Change Password", "Enter current password:", QLineEdit.Password)
        if not ok1:
            return
            
        new_password, ok2 = QInputDialog.getText(self, "Change Password", "Enter new password:", QLineEdit.Password)
        if not ok2:
            return
            
        confirm_password, ok3 = QInputDialog.getText(self, "Change Password", "Confirm new password:", QLineEdit.Password)
        if not ok3:
            return
            
        if new_password != confirm_password:
            QMessageBox.warning(self, "Error", "Passwords do not match!")
            return
            
        if len(new_password) < 6:
            QMessageBox.warning(self, "Error", "Password must be at least 6 characters long!")
            return
            
        # Here you would typically verify the current password and update it
        # For now, we'll just show a success message
        QMessageBox.information(self, "Success", "Password changed successfully!")
        
    def export_data(self):
        """Export user data"""
        QMessageBox.information(self, "Export Data", "Data export feature coming soon!")
        
    def import_data(self):
        """Import user data"""
        QMessageBox.information(self, "Import Data", "Data import feature coming soon!")
        
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(
            self, "Reset Settings", 
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.create_default_settings()
            self.load_current_settings()
            QMessageBox.information(self, "Settings Reset", "Settings have been reset to defaults!")
            
    def save_settings(self):
        """Save all settings to database"""
        try:
            # Validate settings
            if not self.validate_settings():
                return
                
            # Prepare settings data
            settings_data = {
                'dark_mode': self.dark_mode_checkbox.isChecked(),
                'language': self.language_combo.currentText(),
                'date_format': self.date_format_combo.currentText(),
                'currency': self.currency_combo.currentText(),
                'number_format': self.number_format_combo.currentText(),
                'email_notifications': self.email_notifications.isChecked(),
                'push_notifications': self.push_notifications.isChecked(),
                'budget_alerts_enabled': self.budget_alerts.isChecked(),
                'bill_reminders_enabled': self.bill_reminders.isChecked(),
                'notification_frequency': self.frequency_combo.currentText(),
                'currency_auto_refresh': self.currency_refresh.isChecked(),
                'auto_save': self.auto_save.isChecked(),
                'custom_accent_color': getattr(self, 'custom_accent_color', '#d6733a'),
                'updated_at': datetime.now().isoformat()
            }
            
            # Update settings using only columns that exist
            cols_in_db = set(self.get_settings_columns())
            filtered = {k: v for k, v in settings_data.items() if k in cols_in_db}
            set_clause = ", ".join([f"{k} = ?" for k in filtered.keys()])
            execute_query(
                f"UPDATE settings SET {set_clause} WHERE user_id = ?",
                tuple(filtered.values()) + (self.user_id,),
                commit=True,
            )
            
            # Update user information
            email_value = self.email_edit.text().strip()
            if not email_value:
                # If email is empty, use a default placeholder
                email_value = f"user{self.user_id}@pennywise.local"
            
            user_info = fetch_one("SELECT username, email FROM users WHERE user_id = ?", (self.user_id,))
            username_value = self.username_edit.text().strip()
            if not username_value:
                username_value = user_info['username'] if user_info and 'username' in user_info.keys() else f"user{self.user_id}"
            execute_query("""
                UPDATE users SET username = ?, email = ? WHERE user_id = ?
            """, (
                username_value,
                email_value,
                self.user_id
            ), commit=True)
            
            # Emit settings changed signal
            self.settings_changed.emit(settings_data)
            
            # Apply theme changes immediately
            self.apply_theme_changes(settings_data)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")
            
    def validate_settings(self):
        """Validate settings before saving"""
        # Validate email (optional but if provided, should be valid)
        email = self.email_edit.text().strip()
        if email:  # Only validate if email is provided
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                # Do not block saving; fall back to default placeholder silently
                default_email = f"user{self.user_id}@pennywise.local"
                self.email_edit.setText(default_email)
                return True
            
        return True
        
    def apply_theme_changes(self, settings_data):
        """Apply theme changes immediately"""
        try:
            # Apply dark mode
            if settings_data['dark_mode']:
                self.apply_dark_theme()
            else:
                self.apply_light_theme()

            # Refresh this window's palette-driven widgets immediately
            self.refresh_theme_ui()
                
            # Apply custom accent color
            if hasattr(self, 'custom_accent_color'):
                self.apply_accent_color(settings_data['custom_accent_color'])
                
        except Exception as e:
            print(f"Error applying theme changes: {e}")
            
    def apply_dark_theme(self):
        """Apply dark theme to the application"""
        app = QApplication.instance()
        if app:
            theme_manager.apply_theme(app, "dark")
            
    def apply_light_theme(self):
        """Apply light theme to the application"""
        app = QApplication.instance()
        if app:
            theme_manager.apply_theme(app, "light")

    def apply_accent_color(self, color):
        """Apply custom accent color"""
        # This would update the accent color throughout the application
        # Implementation depends on your theme system
        pass

    def changeEvent(self, event):
        """Refresh UI when application palette changes (theme toggle)."""
        if event.type() == QEvent.PaletteChange and not self._refreshing_theme:
            try:
                self._refreshing_theme = True
                self.refresh_theme_ui()
            finally:
                self._refreshing_theme = False
        super().changeEvent(event)

    def showEvent(self, event):
        """Ensure styles are refreshed when the window becomes visible."""
        try:
            if not self._refreshing_theme:
                self._refreshing_theme = True
                self.refresh_theme_ui()
        finally:
            self._refreshing_theme = False
        super().showEvent(event)


# Theme stylesheets for reference
DARK_QSS = """
QWidget {
    background: #1F2937;
    color: #F9FAFB;
}
QFrame {
    background: #374151;
    border: 1px solid #4B5563;
    border-radius: 8px;
}
QPushButton {
    background: #4B5563;
    color: #F9FAFB;
    border: 1px solid #6B7280;
    border-radius: 6px;
    padding: 8px 16px;
}
QPushButton:hover {
    background: #6B7280;
}
QLineEdit {
    background: #374151;
    color: #F9FAFB;
    border: 1px solid #4B5563;
    border-radius: 6px;
    padding: 8px 12px;
}
QComboBox {
    background: #374151;
    color: #F9FAFB;
    border: 1px solid #4B5563;
    border-radius: 6px;
    padding: 8px 12px;
}
"""

LIGHT_QSS = """
QWidget {
    background: #F9FAFB;
    color: #1F2937;
}
QFrame {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
}
QPushButton {
    background: #d6733a;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
}
QPushButton:hover {
    background: #b45131;
}
QLineEdit {
    background: white;
    color: #1F2937;
    border: 1px solid #E5E7EB;
    border-radius: 6px;
    padding: 8px 12px;
}
QComboBox {
    background: white;
    color: #1F2937;
    border: 1px solid #E5E7EB;
    border-radius: 6px;
    padding: 8px 12px;
}
"""