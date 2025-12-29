"""
Maintenance View Widget
Full-screen maintenance message for end users when maintenance mode is enabled
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from core.maintenance_mode import get_maintenance_mode


class MaintenanceView(QWidget):
    """Full-screen maintenance view for end users"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.update_message()
    
    def setup_ui(self):
        """Setup the maintenance view UI"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(30)
        
        # Main container
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignCenter)
        container_layout.setSpacing(20)
        
        # Icon/Emoji
        icon_label = QLabel("🔧")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFont(QFont("Segoe UI", 72))
        container_layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel("Maintenance in Progress")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Segoe UI", 32, QFont.Bold))
        title_label.setStyleSheet("color: #333;")
        container_layout.addWidget(title_label)
        
        # Message
        self.message_label = QLabel()
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setFont(QFont("Segoe UI", 16))
        self.message_label.setStyleSheet("color: #666; padding: 20px;")
        self.message_label.setWordWrap(True)
        self.message_label.setMaximumWidth(600)
        container_layout.addWidget(self.message_label)
        
        # Info text
        info_label = QLabel("We'll be back soon. Thank you for your patience.")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setFont(QFont("Segoe UI", 14))
        info_label.setStyleSheet("color: #999; margin-top: 20px;")
        container_layout.addWidget(info_label)
        
        layout.addWidget(container)
        
        # Set background
        self.setStyleSheet("""
            QWidget {
                background: #f8f9fa;
            }
        """)
    
    def update_message(self):
        """Update the maintenance message from the current state"""
        maintenance_mode = get_maintenance_mode()
        message = maintenance_mode.get_message()
        self.message_label.setText(message)

