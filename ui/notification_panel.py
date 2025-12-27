"""
Notification Panel for PennyWise
Standalone window panel like commitment form
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, 
    QListWidgetItem, QPushButton, QScrollArea, QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from ui.dashboard_main import theme_palette, theme_color


class NotificationPanel(QDialog):
    """
    Standalone notification panel window
    Like commitment form - takes portion of screen
    """
    # Signals for actions
    mark_paid_requested = pyqtSignal(int)  # commitment_id
    manage_payment_requested = pyqtSignal(int, int)  # commitment_id, category_id
    notification_dismissed = pyqtSignal()
    notification_deleted = pyqtSignal(int)  # commitment_id
    
    def __init__(self, notification_manager, parent=None):
        super().__init__(parent)
        self.notification_manager = notification_manager
        self._current_active_item_id = None  # Track which item shows actions
        self.setup_window()
        self.setup_ui()
        
    def setup_window(self):
        """Setup window properties like commitment form"""
        self.setWindowTitle("Notifications")
        self.setFixedSize(400, 600)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        
    def setup_ui(self):
        """Setup the panel UI layout and styling"""
        # Get theme palette
        p = theme_palette()
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header section
        header = QWidget()
        header.setFixedHeight(44)
        header.setStyleSheet(f"""
            QWidget {{
                background: {p['surface']};
                border-bottom: 1px solid {p['border']};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 10, 12, 10)
        
        # Title
        title = QLabel("Notifications")
        title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        title.setStyleSheet(f"color: {p['text_primary']};")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.setFont(QFont("Segoe UI", 14, QFont.Bold))
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {p['text_secondary']};
                border: none;
                border-radius: 12px;
            }}
            QPushButton:hover {{
                background: {p.get('row_hover', 'rgba(37,150,190,0.08)')};
                color: {p['text_primary']};
            }}
        """)
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        
        layout.addWidget(header)
        
        # Notifications list with scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background: {p['background']};
                border: none;
            }}
            QScrollBar:vertical {{
                background: {p['surface']};
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {p['border']};
                border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {p['text_secondary']};
            }}
        """)
        
        # List widget for notifications
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                background: transparent;
                border-bottom: 1px solid {p.get('border', '#e5e7eb')};
                padding: 0;
                color: {p['text_primary']};
            }}
            QListWidget::item:selected {{
                background: {p.get('row_hover', 'rgba(37,150,190,0.08)')};
            }}
            QListWidget::item:hover {{
                background: {p.get('row_hover', 'rgba(37,150,190,0.08)')};
            }}
        """)
        
        # Connect item click to show/hide actions
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        
        self.scroll_area.setWidget(self.list_widget)
        layout.addWidget(self.scroll_area)
        
        # Main window styling
        self.setStyleSheet(f"""
            QDialog {{
                background: {p['background']};
                border: 1px solid {p['border']};
            }}
        """)
        
        # Initial content load
        self.refresh_notifications()
    
    def refresh_notifications(self):
        """Refresh the notifications list from notification manager"""
        # Disable updates during refresh for better performance
        self.list_widget.setUpdatesEnabled(False)
        self.list_widget.clear()
        # Reset active item tracking
        self._current_active_item_id = None
        
        # Get theme palette for consistent styling
        p = theme_palette()
        
        if not self.notification_manager:
            item = QListWidgetItem("No notification manager available")
            item.setFont(QFont("Segoe UI", 9))
            self.list_widget.addItem(item)
            self.list_widget.setUpdatesEnabled(True)
            return
        
        notifications = self.notification_manager.get_active_notifications()
        
        # Sort notifications by urgency and time relevance
        def notification_sort_key(notif):
            """Sort key: (priority, time_value) where lower priority = higher urgency"""
            notif_type = notif.get('type', '')
            
            if notif_type == 'overdue':
                # Overdue: most overdue first (highest days_overdue first)
                days_overdue = notif.get('days_overdue', 0)
                return (0, -days_overdue)  # Negative for descending order
            elif notif_type == 'due_soon':
                days_until_due = notif.get('days_until_due', 999)
                if days_until_due == 0:
                    # Due today: priority 1
                    return (1, 0)
                else:
                    # Due soon: nearest first (priority 2, sort by days_until_due ascending)
                    return (2, days_until_due)
            elif notif_type == 'recurring_reminder':
                # Recurring reminders: priority 3
                return (3, 0)
            elif notif_type == 'overspending_risk':
                # Overspending risk: priority 4
                return (4, 0)
            else:
                # Unknown types: last
                return (5, 0)
        
        notifications = sorted(notifications, key=notification_sort_key)
        
        if not notifications:
            item = QListWidgetItem("No notifications")
            item.setFont(QFont("Segoe UI", 9))
            item.setForeground(QColor(p['text_secondary']))
            self.list_widget.addItem(item)
            self.list_widget.setUpdatesEnabled(True)
            return
        
        for notif in notifications:
            notif_type = notif.get('type', '')
            category_name = notif.get('category_name', '')
            severity = notif.get('severity', 'medium')
            
            # Extract primary text (category name) and secondary text (status)
            if notif_type == 'overspending_risk':
                # Special case: overspending has no category
                primary_text = notif.get('title', 'Overspending Risk')
                secondary_text = notif.get('message', '')
            else:
                # Use category name as primary text
                primary_text = category_name or 'Commitment'
                
                # Extract status from notification data
                if notif_type == 'overdue':
                    days_overdue = notif.get('days_overdue', 0)
                    secondary_text = f"Overdue by {days_overdue} day{'s' if days_overdue != 1 else ''}"
                elif notif_type == 'due_soon':
                    days_until_due = notif.get('days_until_due', 0)
                    if days_until_due == 0:
                        secondary_text = "Due today"
                    else:
                        secondary_text = f"Due in {days_until_due} day{'s' if days_until_due != 1 else ''}"
                elif notif_type == 'recurring_reminder':
                    secondary_text = "Payment due this month"
                else:
                    secondary_text = notif.get('message', '')
            
            # Create custom item widget
            item_widget = QWidget()
            item_layout = QVBoxLayout(item_widget)
            item_layout.setContentsMargins(12, 8, 12, 8)
            item_layout.setSpacing(4)
            
            # Content container (always visible)
            content_layout = QVBoxLayout()
            content_layout.setContentsMargins(0, 0, 0, 0)
            content_layout.setSpacing(2)
            
            # Primary text - category name (bold, readable contrast)
            primary_label = QLabel(primary_text)
            primary_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
            primary_label.setContentsMargins(0, 0, 0, 0)
            primary_label.setStyleSheet(f"color: {p['text_primary']};")
            
            # Secondary text - status (improved contrast with theme-aware urgency colors)
            secondary_label = QLabel(secondary_text)
            secondary_label.setFont(QFont("Segoe UI", 8))
            secondary_label.setWordWrap(True)
            secondary_label.setContentsMargins(0, 0, 0, 0)
            
            # Apply theme-aware severity colors to secondary text only
            if severity == 'high':
                secondary_label.setStyleSheet(f"color: {p.get('error', '#DC2626')};")
            elif severity == 'medium':
                secondary_label.setStyleSheet(f"color: {p.get('warning', '#F59E0B')};")
            else:
                secondary_label.setStyleSheet(f"color: {p['text_secondary']};")
            
            content_layout.addWidget(primary_label)
            content_layout.addWidget(secondary_label)
            item_layout.addLayout(content_layout)
            
            # Add action buttons for commitment-related notifications (hidden by default)
            actions_widget = None
            if notif_type in ('overdue', 'due_soon', 'recurring_reminder'):
                commitment_id = notif.get('commitment_id')
                if commitment_id:
                    actions_widget = QWidget()
                    actions_widget.setVisible(False)
                    actions_layout = QVBoxLayout(actions_widget)
                    actions_layout.setContentsMargins(0, 6, 0, 0)
                    actions_layout.setSpacing(4)
                    
                    # Resolve Payment button
                    resolve_payment_btn = QPushButton("Resolve Payment")
                    resolve_payment_btn.setFont(QFont("Segoe UI", 8))
                    resolve_payment_btn.setFixedHeight(24)
                    resolve_payment_btn.setStyleSheet(f"""
                        QPushButton {{
                            background: {p.get('primary', '#2596be')};
                            color: white;
                            border: none;
                            border-radius: 4px;
                            padding: 4px 12px;
                        }}
                        QPushButton:hover {{
                            background: {p.get('accent', '#2596be')};
                        }}
                    """)
                    resolve_payment_btn.clicked.connect(lambda checked, cid=commitment_id: self._handle_manage_payment(cid, 0))
                    actions_layout.addWidget(resolve_payment_btn)
                    
                    # Dismiss button
                    dismiss_btn = QPushButton("Dismiss")
                    dismiss_btn.setFont(QFont("Segoe UI", 8))
                    dismiss_btn.setFixedHeight(24)
                    dismiss_btn.setStyleSheet(f"""
                        QPushButton {{
                            background: transparent;
                            color: {p['text_secondary']};
                            border: 1px solid {p['border']};
                            border-radius: 4px;
                            padding: 4px 12px;
                        }}
                        QPushButton:hover {{
                            background: {p.get('row_hover', 'rgba(37,150,190,0.08)')};
                            color: {p['text_primary']};
                        }}
                    """)
                    dismiss_btn.clicked.connect(lambda checked, cid=commitment_id: self._handle_dismiss(cid))
                    actions_layout.addWidget(dismiss_btn)
                    
                    # Delete button
                    delete_btn = QPushButton("Delete")
                    delete_btn.setFont(QFont("Segoe UI", 8))
                    delete_btn.setFixedHeight(24)
                    delete_btn.setStyleSheet(f"""
                        QPushButton {{
                            background: transparent;
                            color: {p.get('error', '#DC2626')};
                            border: 1px solid {p.get('error', '#DC2626')};
                            border-radius: 4px;
                            padding: 4px 12px;
                        }}
                        QPushButton:hover {{
                            background: {p.get('error', '#DC2626')};
                            color: white;
                        }}
                    """)
                    delete_btn.clicked.connect(lambda checked, cid=commitment_id: self._handle_delete(cid))
                    actions_layout.addWidget(delete_btn)
                    
                    item_layout.addWidget(actions_widget)
            
            # Add to list with proper size hint
            item = QListWidgetItem()
            item_id = id(item_widget)
            item.setData(Qt.UserRole, item_id)
            if actions_widget:
                item_widget.actions_widget = actions_widget
            # Set initial size hint (collapsed state - actions hidden)
            item_widget.updateGeometry()
            item.setSizeHint(item_widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, item_widget)
        
        # Re-enable updates after refresh
        self.list_widget.setUpdatesEnabled(True)
    
    def update_theme(self):
        """Update panel styling when theme changes"""
        self.setup_ui()
        self.refresh_notifications()
    
    def _on_item_clicked(self, item):
        """Handle item click - show/hide actions for clicked item only"""
        item_id = item.data(Qt.UserRole)
        if item_id is None:
            return
        
        item_widget = self.list_widget.itemWidget(item)
        if not item_widget or not hasattr(item_widget, 'actions_widget'):
            return
        
        actions_widget = item_widget.actions_widget
        previous_active_id = self._current_active_item_id
        
        # Toggle actions for clicked item
        if self._current_active_item_id == item_id:
            # Same item clicked again - hide actions
            actions_widget.setVisible(False)
            self._current_active_item_id = None
        else:
            # Hide actions on previously active item
            if self._current_active_item_id is not None:
                for i in range(self.list_widget.count()):
                    other_item = self.list_widget.item(i)
                    if other_item and other_item.data(Qt.UserRole) == self._current_active_item_id:
                        other_widget = self.list_widget.itemWidget(other_item)
                        if other_widget and hasattr(other_widget, 'actions_widget'):
                            other_widget.actions_widget.setVisible(False)
                            other_widget.updateGeometry()
                            other_item.setSizeHint(other_widget.sizeHint())
                        break
            
            # Show actions for clicked item
            actions_widget.setVisible(True)
            self._current_active_item_id = item_id
        
        # Update clicked item geometry and size hint
        item_widget.updateGeometry()
        item.setSizeHint(item_widget.sizeHint())
    
    def _handle_manage_payment(self, commitment_id, category_id):
        """Handle resolve payment action - emit signal for dashboard to handle navigation"""
        self.manage_payment_requested.emit(commitment_id, category_id or 0)
    
    def _handle_dismiss(self, commitment_id):
        """Handle dismiss action - emit signal and refresh"""
        self.notification_dismissed.emit()
        # Refresh to update list (notifications are computed, so resolved ones will disappear)
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, self.refresh_notifications)
    
    def _handle_delete(self, commitment_id):
        """Handle delete action - emit signal and refresh"""
        self.notification_deleted.emit(commitment_id)
        # Refresh after a short delay to allow backend to process
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(300, self.refresh_notifications)
    
    def showEvent(self, event):
        """Refresh notifications when panel is shown"""
        super().showEvent(event)
        self.refresh_notifications()
        # Center on parent
        if self.parent():
            parent_rect = self.parent().geometry()
            self.move(
                parent_rect.left() + (parent_rect.width() - self.width()) // 2,
                parent_rect.top() + (parent_rect.height() - self.height()) // 2
            )
