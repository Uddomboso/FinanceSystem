from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QCheckBox, QComboBox,
    QPushButton, QMessageBox, QGroupBox
)
from PyQt5.QtGui import QFont
from database.db_manager import fetch_one, execute_query


class SettingsWindow(QWidget):
    def __init__(self, user_id):
        super().__init__()
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
        self.language.addItems(["en", "tr"])
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
        s = fetch_one("SELECT * FROM settings WHERE user_id = ?", (self.user_id,))
        if s:
            self.dark_mode.setChecked(bool(s["dark_mode"]))
            self.notif_box.setChecked(bool(s["notifications_enabled"]))

            currency_index = self.currency.findText(s["currency"])
            if currency_index >= 0:
                self.currency.setCurrentIndex(currency_index)

            lang_code = s.get("language", "en")
            lang_index = self.language.findText(lang_code)
            if lang_index >= 0:
                self.language.setCurrentIndex(lang_index)

            # Apply theme on load
            if s["dark_mode"]:
                self.apply_dark_theme()
            else:
                self.apply_light_theme()

    def save_settings(self):
        dark = int(self.dark_mode.isChecked())
        notif = int(self.notif_box.isChecked())
        curr = self.currency.currentText()
        lang = self.language.currentText()

        query = '''
        INSERT INTO settings (user_id, dark_mode, currency, language, notifications_enabled)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            dark_mode = excluded.dark_mode,
            currency = excluded.currency,
            language = excluded.language,
            notifications_enabled = excluded.notifications_enabled
        '''
        execute_query(query, (self.user_id, dark, curr, lang, notif), commit=True)

        # Apply theme instantly
        if dark:
            self.apply_dark_theme()
        else:
            self.apply_light_theme()

        # Language switch (for this window only)
        self.save_btn.setText("Ayarları Kaydet" if lang == "tr" else "Save Settings")

        # Refresh dashboard if parent exists
        parent = self.parent()
        if parent and hasattr(parent, "refresh_dashboard"):
            parent.refresh_dashboard()

        QMessageBox.information(self, "Settings Saved", "Your preferences have been updated successfully.")

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #2e2e2e;
                color: white;
            }
            QGroupBox {
                border: 1px solid #444;
                margin-top: 20px;
            }
            QLabel, QCheckBox, QComboBox {
                font-size: 14px;
            }
        """)

    def apply_light_theme(self):
        self.setStyleSheet("")
