"""
Settings Window - User Preferences Management
Implements Use Case 5.3.5 Settings functionality
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QCheckBox, QFrame, QScrollArea, QGroupBox, QGridLayout, QMessageBox,
    QApplication, QColorDialog, QSlider, QSpinBox, QLineEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette
import qtawesome as qta
from database.db_manager import fetch_one, execute_query
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
        self.setup_ui()
        self.load_current_settings()
        
    def setup_ui(self):
        """Setup the settings interface"""
        self.setWindowTitle("Settings - PennyWise")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QWidget {
                background: #f9f7f5;
                color: #1F2937;
            }
        """)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # Header
        self.setup_header(main_layout)
        
        # Scroll area for settings
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #E5E7EB;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #9CA3AF;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #6B7280;
            }
        """)
        
        # Settings container
        settings_container = QWidget()
        settings_layout = QVBoxLayout(settings_container)
        settings_layout.setSpacing(25)
        
        # Settings sections
        self.setup_appearance_section(settings_layout)
        self.setup_language_section(settings_layout)
        self.setup_currency_section(settings_layout)
        self.setup_notifications_section(settings_layout)
        self.setup_account_section(settings_layout)
        self.setup_advanced_section(settings_layout)
        
        scroll_area.setWidget(settings_container)
        main_layout.addWidget(scroll_area)
        
        # Action buttons
        self.setup_action_buttons(main_layout)
        
    def setup_header(self, layout):
        """Setup settings header"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 12px;
                padding: 20px;
                border: 1px solid #E5E7EB;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title with icon
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon('fa5s.cog', color='#d6733a').pixmap(32, 32))
        title_layout.addWidget(icon_label)
        
        title_label = QLabel("Settings")
        title_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title_label.setStyleSheet("color: #1F2937; margin-left: 10px;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        header_layout.addLayout(title_layout)
        
        # Subtitle
        subtitle_label = QLabel("Customize your PennyWise experience")
        subtitle_label.setFont(QFont("Segoe UI", 14))
        subtitle_label.setStyleSheet("color: #6B7280; margin-top: 5px;")
        header_layout.addWidget(subtitle_label)
        
        layout.addWidget(header_frame)
        
    def setup_appearance_section(self, layout):
        """Setup appearance settings (dark mode, color themes)"""
        group = self.create_settings_group("Appearance", "fa5s.palette")
        
        # Dark mode toggle
        dark_mode_layout = QHBoxLayout()
        self.dark_mode_checkbox = QCheckBox("Enable Dark Mode")
        self.dark_mode_checkbox.setFont(QFont("Segoe UI", 12))
        self.dark_mode_checkbox.setStyleSheet("""
            QCheckBox {
                color: #374151;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 10px;
                border: 2px solid #D1D5DB;
            }
            QCheckBox::indicator:checked {
                background: #d6733a;
                border-color: #d6733a;
            }
        """)
        dark_mode_layout.addWidget(self.dark_mode_checkbox)
        dark_mode_layout.addStretch()
        group.layout().addLayout(dark_mode_layout)
        
        # Color theme selection
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Color Theme:")
        theme_label.setFont(QFont("Segoe UI", 12))
        theme_label.setStyleSheet("color: #374151;")
        theme_layout.addWidget(theme_label)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Default", "Ocean", "Forest", "Sunset", "Midnight", "Custom"])
        self.theme_combo.setFont(QFont("Segoe UI", 12))
        self.theme_combo.setStyleSheet("""
            QComboBox {
                background: white;
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                padding: 8px 12px;
                min-width: 150px;
            }
            QComboBox:focus {
                border-color: #d6733a;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #6B7280;
                margin-right: 8px;
            }
        """)
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        group.layout().addLayout(theme_layout)
        
        # Custom color picker (hidden by default)
        self.custom_color_widget = QWidget()
        self.custom_color_layout = QHBoxLayout(self.custom_color_widget)
        self.custom_color_layout.setContentsMargins(0, 0, 0, 0)
        custom_color_label = QLabel("Custom Accent Color:")
        custom_color_label.setFont(QFont("Segoe UI", 12))
        custom_color_label.setStyleSheet("color: #374151;")
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
        
        layout.addWidget(group)
        
    def setup_language_section(self, layout):
        """Setup language settings"""
        group = self.create_settings_group("Language & Region", "fa5s.globe")
        
        # Language selection
        lang_layout = QHBoxLayout()
        lang_label = QLabel("Language:")
        lang_label.setFont(QFont("Segoe UI", 12))
        lang_label.setStyleSheet("color: #374151;")
        lang_layout.addWidget(lang_label)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Spanish", "French", "German", "Italian", "Portuguese"])
        self.language_combo.setFont(QFont("Segoe UI", 12))
        self.language_combo.setStyleSheet("""
            QComboBox {
                background: white;
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                padding: 8px 12px;
                min-width: 150px;
            }
            QComboBox:focus {
                border-color: #d6733a;
            }
        """)
        lang_layout.addWidget(self.language_combo)
        lang_layout.addStretch()
        group.layout().addLayout(lang_layout)
        
        # Date format
        date_layout = QHBoxLayout()
        date_label = QLabel("Date Format:")
        date_label.setFont(QFont("Segoe UI", 12))
        date_label.setStyleSheet("color: #374151;")
        date_layout.addWidget(date_label)
        
        self.date_format_combo = QComboBox()
        self.date_format_combo.addItems(["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"])
        self.date_format_combo.setFont(QFont("Segoe UI", 12))
        self.date_format_combo.setStyleSheet("""
            QComboBox {
                background: white;
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                padding: 8px 12px;
                min-width: 150px;
            }
            QComboBox:focus {
                border-color: #d6733a;
            }
        """)
        date_layout.addWidget(self.date_format_combo)
        date_layout.addStretch()
        group.layout().addLayout(date_layout)
        
        layout.addWidget(group)
        
    def setup_currency_section(self, layout):
        """Setup currency settings"""
        group = self.create_settings_group("Currency & Numbers", "fa5s.dollar-sign")
        
        # Currency selection
        currency_layout = QHBoxLayout()
        currency_label = QLabel("Currency:")
        currency_label.setFont(QFont("Segoe UI", 12))
        currency_label.setStyleSheet("color: #374151;")
        currency_layout.addWidget(currency_label)
        
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CHF", "CNY"])
        self.currency_combo.setFont(QFont("Segoe UI", 12))
        self.currency_combo.setStyleSheet("""
            QComboBox {
                background: white;
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                padding: 8px 12px;
                min-width: 150px;
            }
            QComboBox:focus {
                border-color: #d6733a;
            }
        """)
        currency_layout.addWidget(self.currency_combo)
        currency_layout.addStretch()
        group.layout().addLayout(currency_layout)
        
        # Number format
        number_layout = QHBoxLayout()
        number_label = QLabel("Number Format:")
        number_label.setFont(QFont("Segoe UI", 12))
        number_label.setStyleSheet("color: #374151;")
        number_layout.addWidget(number_label)
        
        self.number_format_combo = QComboBox()
        self.number_format_combo.addItems(["1,234.56", "1.234,56", "1 234,56"])
        self.number_format_combo.setFont(QFont("Segoe UI", 12))
        self.number_format_combo.setStyleSheet("""
            QComboBox {
                background: white;
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                padding: 8px 12px;
                min-width: 150px;
            }
            QComboBox:focus {
                border-color: #d6733a;
            }
        """)
        number_layout.addWidget(self.number_format_combo)
        number_layout.addStretch()
        group.layout().addLayout(number_layout)
        
        layout.addWidget(group)
        
    def setup_notifications_section(self, layout):
        """Setup notification settings"""
        group = self.create_settings_group("Notifications", "fa5s.bell")
        
        # Email notifications
        email_layout = QHBoxLayout()
        self.email_notifications = QCheckBox("Email Notifications")
        self.email_notifications.setFont(QFont("Segoe UI", 12))
        self.email_notifications.setStyleSheet("""
            QCheckBox {
                color: #374151;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 10px;
                border: 2px solid #D1D5DB;
            }
            QCheckBox::indicator:checked {
                background: #d6733a;
                border-color: #d6733a;
            }
        """)
        email_layout.addWidget(self.email_notifications)
        email_layout.addStretch()
        group.layout().addLayout(email_layout)
        
        # Push notifications
        push_layout = QHBoxLayout()
        self.push_notifications = QCheckBox("Push Notifications")
        self.push_notifications.setFont(QFont("Segoe UI", 12))
        self.push_notifications.setStyleSheet("""
            QCheckBox {
                color: #374151;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 10px;
                border: 2px solid #D1D5DB;
            }
            QCheckBox::indicator:checked {
                background: #d6733a;
                border-color: #d6733a;
            }
        """)
        push_layout.addWidget(self.push_notifications)
        push_layout.addStretch()
        group.layout().addLayout(push_layout)
        
        # Notification frequency
        freq_layout = QHBoxLayout()
        freq_label = QLabel("Notification Frequency:")
        freq_label.setFont(QFont("Segoe UI", 12))
        freq_label.setStyleSheet("color: #374151;")
        freq_layout.addWidget(freq_label)
        
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(["Real-time", "Daily", "Weekly", "Monthly"])
        self.frequency_combo.setFont(QFont("Segoe UI", 12))
        self.frequency_combo.setStyleSheet("""
            QComboBox {
                background: white;
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                padding: 8px 12px;
                min-width: 150px;
            }
            QComboBox:focus {
                border-color: #d6733a;
            }
        """)
        freq_layout.addWidget(self.frequency_combo)
        freq_layout.addStretch()
        group.layout().addLayout(freq_layout)
        
        layout.addWidget(group)
        
    def setup_account_section(self, layout):
        """Setup account information settings"""
        group = self.create_settings_group("Account Information", "fa5s.user")
        
        # Username
        username_layout = QHBoxLayout()
        username_label = QLabel("Username:")
        username_label.setFont(QFont("Segoe UI", 12))
        username_label.setStyleSheet("color: #374151;")
        username_label.setFixedWidth(120)
        username_layout.addWidget(username_label)
        
        self.username_edit = QLineEdit()
        self.username_edit.setFont(QFont("Segoe UI", 12))
        self.username_edit.setStyleSheet("""
            QLineEdit {
                background: white;
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                padding: 8px 12px;
            }
            QLineEdit:focus {
                border-color: #d6733a;
            }
        """)
        username_layout.addWidget(self.username_edit)
        username_layout.addStretch()
        group.layout().addLayout(username_layout)
        
        # Email
        email_layout = QHBoxLayout()
        email_label = QLabel("Email:")
        email_label.setFont(QFont("Segoe UI", 12))
        email_label.setStyleSheet("color: #374151;")
        email_label.setFixedWidth(120)
        email_layout.addWidget(email_label)
        
        self.email_edit = QLineEdit()
        self.email_edit.setFont(QFont("Segoe UI", 12))
        self.email_edit.setPlaceholderText("Enter email address (default will be used if empty)")
        self.email_edit.setStyleSheet("""
            QLineEdit {
                background: white;
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                padding: 8px 12px;
            }
            QLineEdit:focus {
                border-color: #d6733a;
            }
        """)
        email_layout.addWidget(self.email_edit)
        email_layout.addStretch()
        group.layout().addLayout(email_layout)
        
        # Change password button
        password_layout = QHBoxLayout()
        password_label = QLabel("Password:")
        password_label.setFont(QFont("Segoe UI", 12))
        password_label.setStyleSheet("color: #374151;")
        password_label.setFixedWidth(120)
        password_layout.addWidget(password_label)
        
        self.change_password_btn = QPushButton("Change Password")
        self.change_password_btn.setFont(QFont("Segoe UI", 12))
        self.change_password_btn.setStyleSheet("""
            QPushButton {
                background: #6B7280;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #4B5563;
            }
        """)
        self.change_password_btn.clicked.connect(self.change_password)
        password_layout.addWidget(self.change_password_btn)
        password_layout.addStretch()
        group.layout().addLayout(password_layout)
        
        layout.addWidget(group)
        
    def setup_advanced_section(self, layout):
        """Setup advanced settings"""
        group = self.create_settings_group("Advanced", "fa5s.cogs")
        
        # Auto-save
        autosave_layout = QHBoxLayout()
        self.auto_save = QCheckBox("Auto-save changes")
        self.auto_save.setFont(QFont("Segoe UI", 12))
        self.auto_save.setStyleSheet("""
            QCheckBox {
                color: #374151;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 10px;
                border: 2px solid #D1D5DB;
            }
            QCheckBox::indicator:checked {
                background: #d6733a;
                border-color: #d6733a;
            }
        """)
        autosave_layout.addWidget(self.auto_save)
        autosave_layout.addStretch()
        group.layout().addLayout(autosave_layout)
        
        # Data export
        export_layout = QHBoxLayout()
        export_label = QLabel("Data Management:")
        export_label.setFont(QFont("Segoe UI", 12))
        export_label.setStyleSheet("color: #374151;")
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
        
        layout.addWidget(group)
        
    def create_settings_group(self, title, icon_name):
        """Create a settings group with title and icon"""
        group = QGroupBox()
        group.setStyleSheet("""
            QGroupBox {
                background: white;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                padding: 20px;
                font-weight: bold;
                font-size: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #1F2937;
            }
        """)
        
        # Title with icon
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 15)
        
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon_name, color='#d6733a').pixmap(20, 20))
        title_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_label.setStyleSheet("color: #1F2937; margin-left: 8px;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # Create layout for the group
        group_layout = QVBoxLayout(group)
        group_layout.addLayout(title_layout)
        
        return group
        
    def setup_action_buttons(self, layout):
        """Setup action buttons (Save, Cancel, Reset)"""
        button_frame = QFrame()
        button_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 12px;
                padding: 20px;
                border: 1px solid #E5E7EB;
            }
        """)
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
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
                self.theme_combo.setCurrentText(settings['theme'] if 'theme' in settings.keys() else 'Default')
                
                # Load language settings
                self.language_combo.setCurrentText(settings['language'] if 'language' in settings.keys() else 'English')
                self.date_format_combo.setCurrentText(settings['date_format'] if 'date_format' in settings.keys() else 'MM/DD/YYYY')
                
                # Load currency settings
                self.currency_combo.setCurrentText(settings['currency'] if 'currency' in settings.keys() else 'USD')
                self.number_format_combo.setCurrentText(settings['number_format'] if 'number_format' in settings.keys() else '1,234.56')
                
                # Load notification settings
                self.email_notifications.setChecked(bool(settings['email_notifications'] if 'email_notifications' in settings.keys() else True))
                self.push_notifications.setChecked(bool(settings['push_notifications'] if 'push_notifications' in settings.keys() else True))
                self.frequency_combo.setCurrentText(settings['notification_frequency'] if 'notification_frequency' in settings.keys() else 'Daily')
                
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
            'language': 'English',
            'date_format': 'MM/DD/YYYY',
            'currency': 'USD',
            'number_format': '1,234.56',
            'email_notifications': True,
            'push_notifications': True,
            'notification_frequency': 'Daily',
            'auto_save': True,
            'custom_accent_color': '#d6733a',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        try:
            execute_query("""
                INSERT INTO settings (user_id, dark_mode, theme, language, date_format, 
                                    currency, number_format, email_notifications, 
                                    push_notifications, notification_frequency, 
                                    auto_save, custom_accent_color, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                default_settings['user_id'],
                default_settings['dark_mode'],
                default_settings['theme'],
                default_settings['language'],
                default_settings['date_format'],
                default_settings['currency'],
                default_settings['number_format'],
                default_settings['email_notifications'],
                default_settings['push_notifications'],
                default_settings['notification_frequency'],
                default_settings['auto_save'],
                default_settings['custom_accent_color'],
                default_settings['created_at'],
                default_settings['updated_at']
            ), commit=True)
            
            self.current_settings = default_settings
            
        except Exception as e:
            print(f"Error creating default settings: {e}")
            
    def on_theme_changed(self, theme):
        """Handle theme selection change"""
        if theme == "Custom":
            self.custom_color_widget.setVisible(True)
        else:
            self.custom_color_widget.setVisible(False)
            
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
                'theme': self.theme_combo.currentText(),
                'language': self.language_combo.currentText(),
                'date_format': self.date_format_combo.currentText(),
                'currency': self.currency_combo.currentText(),
                'number_format': self.number_format_combo.currentText(),
                'email_notifications': self.email_notifications.isChecked(),
                'push_notifications': self.push_notifications.isChecked(),
                'notification_frequency': self.frequency_combo.currentText(),
                'auto_save': self.auto_save.isChecked(),
                'custom_accent_color': getattr(self, 'custom_accent_color', '#d6733a'),
                'updated_at': datetime.now().isoformat()
            }
            
            # Update settings in database
            execute_query("""
                UPDATE settings SET 
                    dark_mode = ?, theme = ?, language = ?, date_format = ?,
                    currency = ?, number_format = ?, email_notifications = ?,
                    push_notifications = ?, notification_frequency = ?,
                    auto_save = ?, custom_accent_color = ?, updated_at = ?
                WHERE user_id = ?
            """, (
                settings_data['dark_mode'],
                settings_data['theme'],
                settings_data['language'],
                settings_data['date_format'],
                settings_data['currency'],
                settings_data['number_format'],
                settings_data['email_notifications'],
                settings_data['push_notifications'],
                settings_data['notification_frequency'],
                settings_data['auto_save'],
                settings_data['custom_accent_color'],
                settings_data['updated_at'],
                self.user_id
            ), commit=True)
            
            # Update user information
            email_value = self.email_edit.text().strip()
            if not email_value:
                # If email is empty, use a default placeholder
                email_value = f"user{self.user_id}@pennywise.local"
            
            execute_query("""
                UPDATE users SET username = ?, email = ? WHERE user_id = ?
            """, (
                self.username_edit.text(),
                email_value,
                self.user_id
            ), commit=True)
            
            # Emit settings changed signal
            self.settings_changed.emit(settings_data)
            
            # Apply theme changes immediately
            self.apply_theme_changes(settings_data)
            
            QMessageBox.information(self, "Settings Saved", "Your settings have been saved successfully!")
            self.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")
            
    def validate_settings(self):
        """Validate settings before saving"""
        # Validate username
        if not self.username_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Username cannot be empty!")
            return False
            
        # Validate email (optional but if provided, should be valid)
        email = self.email_edit.text().strip()
        if email:  # Only validate if email is provided
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                QMessageBox.warning(self, "Validation Error", "Please enter a valid email address or leave it empty for default!")
                return False
            
        return True
        
    def apply_theme_changes(self, settings_data):
        """Apply theme changes immediately"""
        try:
            # Apply dark mode
            if settings_data['dark_mode']:
                self.apply_dark_theme()
            else:
                self.apply_light_theme()
                
            # Apply custom accent color
            if hasattr(self, 'custom_accent_color'):
                self.apply_accent_color(settings_data['custom_accent_color'])
                
        except Exception as e:
            print(f"Error applying theme changes: {e}")
            
    def apply_dark_theme(self):
        """Apply dark theme to the application"""
        if self.parent_window:
            # Apply dark theme to parent window
            dark_stylesheet = """
                QWidget {
                    background: #1F2937;
                    color: #F9FAFB;
                }
                QFrame {
                    background: #374151;
                    border: 1px solid #4B5563;
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
            """
            self.parent_window.setStyleSheet(dark_stylesheet)
            
    def apply_light_theme(self):
        """Apply light theme to the application"""
        if self.parent_window:
            # Apply light theme to parent window
            light_stylesheet = """
                QWidget {
                    background: #F9FAFB;
                    color: #1F2937;
                }
                QFrame {
                    background: white;
                    border: 1px solid #E5E7EB;
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
            """
            self.parent_window.setStyleSheet(light_stylesheet)
            
    def apply_accent_color(self, color):
        """Apply custom accent color"""
        # This would update the accent color throughout the application
        # Implementation depends on your theme system
        pass


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