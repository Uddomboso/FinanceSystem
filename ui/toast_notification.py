"""
Toast Notification System for PennyWise
Standalone, non-blocking toast notifications for desktop app
"""

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtGui import QScreen


class ToastNotification(QWidget):
    """
    Simple toast notification popup that appears at bottom-right of screen
    Auto-closes after 4 seconds. Non-blocking and safe to use.
    """
    
    def __init__(self, title="Notification", message="", parent=None):
        super().__init__(parent)
        self.title = title
        self.message = message
        
        # Window flags - tool window, frameless, stays on top
        self.setWindowFlags(
            Qt.Tool | 
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint
        )
        
        # Show without activating (doesn't steal focus)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        self.setup_ui()
        self.position_on_screen()
        
    def setup_ui(self):
        """Setup the toast UI layout and styling"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)
        
        # Title label
        self.title_label = QLabel(self.title)
        self.title_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.title_label.setStyleSheet("color: #ffffff;")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)
        
        # Message label
        self.message_label = QLabel(self.message)
        self.message_label.setFont(QFont("Segoe UI", 9))
        self.message_label.setStyleSheet("color: #f3f4f6;")
        self.message_label.setWordWrap(True)
        self.message_label.setMaximumWidth(300)
        layout.addWidget(self.message_label)
        
        # Main container styling
        self.setStyleSheet("""
            QWidget {
                background: #1f2937;
                border: 1px solid #374151;
                border-radius: 8px;
            }
        """)
        
        # Set fixed size for consistency
        self.setFixedSize(320, 80)
        
    def position_on_screen(self):
        """Position toast at bottom-right of primary screen"""
        # Get primary screen geometry
        screen = self.screen() if hasattr(self, 'screen') else None
        if not screen:
            # Fallback for older PyQt5 versions
            from PyQt5.QtWidgets import QApplication
            screen = QApplication.primaryScreen()
        
        if screen:
            screen_geometry = screen.availableGeometry()
            
            # Calculate bottom-right position with margin
            margin = 20
            x = screen_geometry.right() - self.width() - margin
            y = screen_geometry.bottom() - self.height() - margin
            
            self.move(x, y)
        else:
            # Fallback positioning if screen detection fails
            self.move(1000, 600)
    
    def show_toast(self):
        """Show the toast and schedule auto-close"""
        self.show()
        
        # Auto-close after 4 seconds (4000ms)
        QTimer.singleShot(4000, self.close)
    
    @staticmethod
    def show(title, message):
        """
        Static method to create and show a toast notification
        
        Args:
            title (str): Toast title
            message (str): Toast message
        """
        toast = ToastNotification(title, message)
        toast.show_toast()
        return toast


# Example usage (commented - for reference only):
#
# In DashboardMain or any other class:
#
# def show_success_toast(self):
#     """Example: Show a success toast notification"""
#     # This would be called when needed - safe and non-blocking
#     ToastNotification.show("Success", "Operation completed successfully")
#
# def show_error_toast(self):
#     """Example: Show an error toast notification"""
#     ToastNotification.show("Error", "Something went wrong")
#
# def show_commitment_toast(self):
#     """Example: Show a commitment-related toast"""
#     ToastNotification.show("Commitment Added", "New monthly commitment has been created")
#
# Note: These are commented examples only. No actual integration needed.
# The ToastNotification class is completely standalone and safe to import
# without any dependencies on DashboardMain or other app components.
