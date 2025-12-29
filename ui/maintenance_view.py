"""
Maintenance View Widget
Full-screen maintenance message for end users when maintenance mode is enabled
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPalette
from core.maintenance_mode import get_maintenance_mode
from assets.styles.penny_colors import PennyColors
from core.theme_manager import theme_manager


class MaintenanceView(QWidget):
    """Full-screen maintenance view for end users"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._palette = PennyColors.get_palette(theme_manager.current_theme)
        self.setup_ui()
        self.update_message()
    
    def setup_ui(self):
        """Setup the maintenance view UI with PennyWise theme"""
        p = self._palette
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(0)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Main container card
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background: {p['surface']};
                border: 2px solid #d6733a;
                border-radius: 16px;
                padding: 48px;
                max-width: 700px;
            }}
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignCenter)
        container_layout.setSpacing(24)
        
        # Title
        title_label = QLabel("Maintenance in Progress")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Segoe UI", 28, QFont.Bold))
        title_label.setStyleSheet(f"color: {p['text_primary']}; margin-bottom: 8px;")
        container_layout.addWidget(title_label)
        
        # Divider line
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"color: #d6733a; background: #d6733a; max-height: 2px;")
        container_layout.addWidget(divider)
        
        # Message
        self.message_label = QLabel()
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setFont(QFont("Segoe UI", 15))
        self.message_label.setStyleSheet(f"color: {p['text_secondary']}; padding: 16px 0; line-height: 1.6;")
        self.message_label.setWordWrap(True)
        container_layout.addWidget(self.message_label)
        
        # Info text
        info_label = QLabel("We'll be back soon. Thank you for your patience.")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setFont(QFont("Segoe UI", 13))
        info_label.setStyleSheet(f"color: {p['text_secondary']}; margin-top: 8px; font-style: italic;")
        container_layout.addWidget(info_label)
        
        layout.addWidget(container)
        
        # Set background with PennyWise theme
        self.setStyleSheet(f"""
            QWidget {{
                background: {p['background']};
            }}
        """)
        
        # Apply palette to widget
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QPalette.Window, QColor(p['background']))
        self.setPalette(pal)
    
    def update_message(self):
        """Update the maintenance message from the current state"""
        maintenance_mode = get_maintenance_mode()
        message = maintenance_mode.get_message()
        self.message_label.setText(message)

