from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QCheckBox, QComboBox,
    QPushButton, QMessageBox, QGroupBox
)
from PyQt5.QtGui import QFont
from database.db_manager import fetch_one, execute_query


class SettingsWindow(QWidget):
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle("Settings")
        self.setMinimumSize(400, 300)

        # UI Elements
        self.dark_mode = QCheckBox("Enable Dark Mode")
        self.notif_box = QCheckBox("Enable Alerts")
        self.currency = QComboBox()
        self.language = QComboBox()
        self.save_btn = QPushButton("Save Settings")

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        label_font = QFont("Segoe UI", 12)
        title_font = QFont("Segoe UI", 14, QFont.Bold)

        # Theme Section
        theme_box = QGroupBox("Theme")
        theme_layout = QVBoxLayout()
        self.dark_mode.setFont(label_font)
        theme_layout.addWidget(self.dark_mode)
        theme_box.setLayout(theme_layout)

        # Currency Section
        currency_box = QGroupBox("Preferred Currency")
        currency_layout = QVBoxLayout()
        self.currency.addItems(["USD", "EUR", "GBP", "NGN", "TRY"])
        self.currency.setFont(label_font)
        currency_layout.addWidget(self.currency)
        currency_box.setLayout(currency_layout)

        # Language Section
        language_box = QGroupBox("Language")
        language_layout = QVBoxLayout()
        self.language.addItems(["English", "Türkçe"])
        self.language.setFont(label_font)
        language_layout.addWidget(self.language)
        language_box.setLayout(language_layout)

        # Alerts
        self.notif_box.setFont(label_font)

        # Save Button
        self.save_btn.setFont(title_font)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #d6733a;
                color: white;
                padding: 10px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #b45131;
            }
        """)
        self.save_btn.clicked.connect(self.save_settings)

        # Assemble layout
        main_layout.addWidget(theme_box)
        main_layout.addWidget(currency_box)
        main_layout.addWidget(language_box)
        main_layout.addWidget(self.notif_box)
        main_layout.addStretch()
        main_layout.addWidget(self.save_btn)

        self.setLayout(main_layout)

    def load_settings(self):
        s = fetch_one("SELECT * FROM settings WHERE user_id = ?",(self.user_id,))
        if s:
            self.dark_mode.setChecked(bool(s["dark_mode"]) if "dark_mode" in s.keys() else False)
            self.notif_box.setChecked(
                bool(s["notifications_enabled"]) if "notifications_enabled" in s.keys() else False)

            currency = s["currency"] if "currency" in s.keys() else "USD"
            currency_index = self.currency.findText(currency)
            if currency_index >= 0:
                self.currency.setCurrentIndex(currency_index)

            lang_code = s["language"] if "language" in s.keys() else "en"
            lang_display = "English" if lang_code == "en" else "Türkçe"
            lang_index = self.language.findText(lang_display)
            if lang_index >= 0:
                self.language.setCurrentIndex(lang_index)

            # Apply theme on load
            self.apply_theme(self.dark_mode.isChecked())

            # Notify parent to apply global theme on load
            parent = self.parent()
            if parent and hasattr(parent,"apply_global_theme"):
                parent.apply_global_theme(self.dark_mode.isChecked())

    def save_settings(self):
        dark = int(self.dark_mode.isChecked())
        notif = int(self.notif_box.isChecked())
        curr = self.currency.currentText()
        lang_display = self.language.currentText()
        lang_code = "en" if lang_display == "English" else "tr"

        query = '''
        INSERT INTO settings (user_id, dark_mode, currency, language, notifications_enabled)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            dark_mode = excluded.dark_mode,
            currency = excluded.currency,
            language = excluded.language,
            notifications_enabled = excluded.notifications_enabled
        '''
        execute_query(query, (self.user_id, dark, curr, lang_code, notif), commit=True)

        # Apply theme instantly
        self.apply_theme(dark)

        # Update button text based on language
        self.save_btn.setText("Ayarları Kaydet" if lang_code == "tr" else "Save Settings")

        # Show confirmation message
        msg = "Ayarlar kaydedildi!" if lang_code == "tr" else "Settings saved successfully!"
        QMessageBox.information(self, "Success", msg)

        # Notify parent to update theme globally
        parent = self.parent()
        if parent and hasattr(parent, "apply_global_theme"):
            parent.apply_global_theme(dark)
        if parent and hasattr(parent, "refresh_dashboard"):
            parent.refresh_dashboard()

    def apply_theme(self, dark):
        """Apply theme to this window only"""
        stylesheet = DARK_QSS if dark else LIGHT_QSS
        self.setStyleSheet(stylesheet)


DARK_QSS = """
    QWidget {
        background-color: #2c2c2c;
        color: #ffffff;
    }
    QScrollArea {
        background-color: #2c2c2c;
    }
    QFrame {
        background-color: #1e1e1e;
        border-radius: 10px;
    }
    QLabel {
        color: #f1f1f1;
    }
    QGroupBox {
        border: 1px solid #444;
        border-radius: 8px;
        margin-top: 10px;
        background-color: #333;
        padding: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px;
        font-weight: bold;
    }
    QComboBox {
        background-color: #444;
        color: #fff;
        border: 1px solid #666;
        padding: 4px;
        border-radius: 4px;
    }
    QCheckBox {
        spacing: 8px;
    }
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
    }
    QPushButton {
        background-color: #d6733a;
        color: white;
        padding: 10px;
        border-radius: 6px;
    }
    QPushButton:hover {
        background-color: #b45131;
    }
"""


LIGHT_QSS = """
    QWidget {
        background-color: #f3f3f3;
        color: #000;
    }
    QGroupBox {
        border: 1px solid #ccc;
        border-radius: 8px;
        margin-top: 10px;
        background-color: #fff;
        padding: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px;
        font-weight: bold;
    }
    QComboBox {
        background-color: #fff;
        color: #000;
        border: 1px solid #aaa;
        padding: 4px;
        border-radius: 4px;
    }
    QCheckBox {
        spacing: 8px;
    }
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
    }
    QPushButton {
        background-color: #d6733a;
        color: white;
        padding: 10px;
        border-radius: 6px;
    }
    QPushButton:hover {
        background-color: #b45131;
    }
"""
