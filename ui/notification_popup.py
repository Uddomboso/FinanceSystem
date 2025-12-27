"""
Notification UI Components for PennyWise
Minimal hover preview and full notification window
"""

from PyQt5.QtWidgets import (
    QFrame, QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QListWidgetItem, QPushButton, QWidget
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
from datetime import datetime


class NotificationPreviewPopup(QFrame):
    """Small hover preview panel for recent notifications"""
    
    def __init__(self, notification_manager, parent=None):
        super().__init__(parent)
        self.notification_manager = notification_manager
        self.setup_ui()
        self.hide()
        
    def setup_ui(self):
        self.setFixedSize(300, 200)
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("Recent Notifications")
        title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        title.setStyleSheet("color: #374151; margin-bottom: 4px;")
        layout.addWidget(title)
        
        # Notifications list
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(4)
        layout.addWidget(self.content_widget)
        
    def update_content(self):
        """Update preview with recent notifications"""
        # Clear existing content
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get recent notifications (max 5)
        notifications = self.notification_manager.get_active_notifications()[:5]
        
        if not notifications:
            no_notifs = QLabel("No notifications")
            no_notifs.setStyleSheet("color: #6b7280; font-style: italic; padding: 8px;")
            self.content_layout.addWidget(no_notifs)
            return
        
        for notif in notifications:
            notif_widget = QWidget()
            notif_layout = QVBoxLayout(notif_widget)
            notif_layout.setContentsMargins(0, 0, 0, 0)
            notif_layout.setSpacing(2)
            
            # Title
            title_label = QLabel(notif.get('title', 'Notification'))
            title_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
            title_label.setStyleSheet("color: #374151;")
            title_label.setWordWrap(True)
            notif_layout.addWidget(title_label)
            
            # Message
            msg_label = QLabel(notif.get('message', ''))
            msg_label.setFont(QFont("Segoe UI", 8))
            msg_label.setStyleSheet("color: #6b7280;")
            msg_label.setWordWrap(True)
            msg_label.setMaximumHeight(40)
            notif_layout.addWidget(msg_label)
            
            self.content_layout.addWidget(notif_widget)


class NotificationWindow(QDialog):
    """Full notifications window showing all active notifications"""
    
    def __init__(self, notification_manager, parent=None):
        super().__init__(parent)
        self.notification_manager = notification_manager
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Notifications")
        self.setFixedSize(400, 500)
        self.setStyleSheet("""
            QDialog {
                background: white;
                border: 1px solid #d1d5db;
                border-radius: 8px;
            }
            QListWidget {
                border: none;
                background: transparent;
            }
            QListWidget::item {
                border-bottom: 1px solid #f3f4f6;
                padding: 8px;
            }
            QListWidget::item:selected {
                background: #f3f4f6;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QLabel("All Notifications")
        header.setFont(QFont("Segoe UI", 12, QFont.Bold))
        header.setStyleSheet("color: #374151; margin-bottom: 8px;")
        layout.addWidget(header)
        
        # Notifications list
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(32)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #374151;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #1f2937;
            }
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.update_content()
        
    def update_content(self):
        """Update window with all notifications"""
        self.list_widget.clear()
        
        notifications = self.notification_manager.get_active_notifications()
        
        if not notifications:
            item = QListWidgetItem("No notifications")
            item.setFont(QFont("Segoe UI", 10))
            self.list_widget.addItem(item)
            return
        
        for notif in notifications:
            title = notif.get('title', 'Notification')
            message = notif.get('message', '')
            severity = notif.get('severity', 'medium')
            
            item_text = f"• {title}\n  {message}"
            item = QListWidgetItem(item_text)
            item.setFont(QFont("Segoe UI", 9))
            
            # Apply severity styling using Qt-supported methods
            if severity == 'high':
                item.setForeground(QColor("#dc2626"))
            elif severity == 'medium':
                item.setForeground(QColor("#f59e0b"))
            else:
                item.setForeground(QColor("#6b7280"))
            
            self.list_widget.addItem(item)
    
    def showEvent(self, event):
        """Refresh content when window is shown"""
        super().showEvent(event)
        self.update_content()
        # Center on parent
        if self.parent():
            parent_rect = self.parent().geometry()
            self.move(
                parent_rect.left() + (parent_rect.width() - self.width()) // 2,
                parent_rect.top() + (parent_rect.height() - self.height()) // 2
            )
