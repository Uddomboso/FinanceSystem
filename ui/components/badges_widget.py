# ui/components/badges_widget.py - ENHANCED VERSION

"""
Enhanced Badges Widget with Celebration Support
"""

from PyQt5.QtWidgets import (QFrame,QVBoxLayout,QHBoxLayout,QLabel,
                             QScrollArea,QWidget,QGridLayout,QProgressBar,QPushButton)
from PyQt5.QtCore import Qt,QPropertyAnimation,QEasingCurve,QTimer
from PyQt5.QtGui import QFont,QColor,QPainter,QPen
from core.badges_manager import BadgesManager
from PyQt5.QtWidgets import QGraphicsOpacityEffect
import qtawesome as qta



class BadgesWidget(QFrame):
    """Widget that displays earned badges and progress toward new ones"""

    def __init__(self,user_id,parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.badges_manager = BadgesManager(user_id)
        self.celebration_callback = None

        self.setup_ui()
        self.apply_styling()
        self.load_badges()

        # Check for new badges periodically
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_new_badges)
        self.check_timer.start(30000)  # Check every 30 seconds

    def setup_ui(self):
        """Setup badges widget layout"""
        self.setProperty("class","badges_widget")
        self.setFixedHeight(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20,15,20,15)
        layout.setSpacing(12)

        # Header
        header_layout = QHBoxLayout()

        # Title with icon
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        trophy_icon = qta.icon('fa5s.trophy', color='#F59E0B')
        icon_label = QLabel()
        icon_label.setPixmap(trophy_icon.pixmap(20, 20))
        title = QLabel("Your Achievements")
        title.setFont(QFont("Segoe UI",16,QFont.Bold))
        title.setStyleSheet("color: #1F2937;")
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title)
        title_layout.addStretch()

        self.badge_count = QLabel("0/7")
        self.badge_count.setStyleSheet("""
            background: #2563EB;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
        """)

        header_widget = QWidget()
        header_widget.setLayout(title_layout)
        header_layout.addWidget(header_widget)
        header_layout.addStretch()
        header_layout.addWidget(self.badge_count)
        layout.addLayout(header_layout)

        # New badges indicator with icon
        new_indicator_layout = QHBoxLayout()
        new_indicator_layout.setSpacing(4)
        new_icon = qta.icon('fa5s.sparkles', color='white')
        new_icon_label = QLabel()
        new_icon_label.setPixmap(new_icon.pixmap(12, 12))
        new_text = QLabel("New!")
        new_text.setStyleSheet("color: white; font-size: 10px; font-weight: bold;")
        new_indicator_layout.addWidget(new_icon_label)
        new_indicator_layout.addWidget(new_text)
        
        self.new_badges_indicator = QWidget()
        self.new_badges_indicator.setLayout(new_indicator_layout)
        self.new_badges_indicator.setStyleSheet("""
            background: #10B981;
            padding: 4px 8px;
            border-radius: 8px;
        """)
        self.new_badges_indicator.setVisible(False)
        header_layout.insertWidget(2,self.new_badges_indicator)

        # Scroll area for badges
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedHeight(140)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #F3F4F6;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #D1D5DB;
                border-radius: 3px;
            }
        """)

        self.badges_container = QWidget()
        self.badges_layout = QHBoxLayout(self.badges_container)
        self.badges_layout.setSpacing(15)
        self.badges_layout.setContentsMargins(5,5,5,5)

        self.scroll_area.setWidget(self.badges_container)
        layout.addWidget(self.scroll_area)

    def set_celebration_callback(self,callback):
        """Set callback for celebration events"""
        self.celebration_callback = callback

    def apply_styling(self):
        """Apply badges widget styling"""
        self.setStyleSheet("""
            QFrame[class="badges_widget"] {
                background: #FFFFFF;
                border: 1px solid rgba(0, 0, 0, 0.06);
                border-radius: 16px;
            }
        """)

    def load_badges(self):
        """Load and display badges"""
        badges_data = self.badges_manager.get_badges_with_progress()

        # Clear existing badges
        for i in reversed(range(self.badges_layout.count())):
            self.badges_layout.itemAt(i).widget().setParent(None)

        # Add badge items
        earned_count = 0
        for badge in badges_data:
            badge_widget = self.create_badge_item(badge)
            self.badges_layout.addWidget(badge_widget)
            if badge['earned']:
                earned_count += 1

        # Update badge count
        self.badge_count.setText(f"{earned_count}/{len(badges_data)}")

        # Add stretch to push badges to the left
        self.badges_layout.addStretch()

    def create_badge_item(self,badge_data):
        """Create individual badge display item"""
        badge_frame = QFrame()
        badge_frame.setFixedSize(100,110)
        badge_frame.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
            }
        """)

        badge_layout = QVBoxLayout(badge_frame)
        badge_layout.setSpacing(6)
        badge_layout.setAlignment(Qt.AlignCenter)

        # Badge icon/status - using FontAwesome icons
        status_circle = QLabel()
        status_circle.setAlignment(Qt.AlignCenter)
        status_circle.setFixedSize(50, 50)
        
        if badge_data['earned']:
            # Earned badge - show with color
            icon = qta.icon(badge_data['icon'], color='white')
            status_circle.setPixmap(icon.pixmap(30, 30))
            status_circle.setStyleSheet(f"""
                background: {badge_data['color']};
                border-radius: 25px;
                border: 2px solid {badge_data['color']};
            """)
        else:
            # Not earned - show grayed out
            icon = qta.icon(badge_data['icon'], color='#9CA3AF')
            status_circle.setPixmap(icon.pixmap(30, 30))
            status_circle.setStyleSheet("""
                background: #E5E7EB;
                border-radius: 25px;
                border: 2px solid #E5E7EB;
            """)

        # Badge name
        name_label = QLabel(badge_data['name'])
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("""
            color: #1F2937;
            font-size: 11px;
            font-weight: 600;
            background: transparent;
        """)
        name_label.setWordWrap(True)

        # Progress bar for unearned badges
        if not badge_data['earned']:
            progress_bar = QProgressBar()
            progress_bar.setValue(badge_data['progress'])
            progress_bar.setFixedHeight(4)
            progress_bar.setTextVisible(False)
            progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    background: #E5E7EB;
                    border: none;
                    border-radius: 2px;
                }}
                QProgressBar::chunk {{
                    background: {badge_data['color']};
                    border-radius: 2px;
                }}
            """)
            badge_layout.addWidget(progress_bar)

        badge_layout.addWidget(status_circle)
        badge_layout.addWidget(name_label)

        # Tooltip with description
        badge_frame.setToolTip(f"{badge_data['description']}\nRarity: {badge_data['rarity'].title()}")

        return badge_frame

    def check_new_badges(self):
        """Check for and display newly earned badges"""
        new_badges = self.badges_manager.check_new_badges()

        if new_badges:
            self.show_new_badges_indicator()
            self.load_badges()  # Refresh display

            # Trigger celebration
            if self.celebration_callback:
                self.celebration_callback(new_badges)

        return new_badges

    def show_new_badges_indicator(self):
        """Show and animate new badges indicator"""
        self.new_badges_indicator.setVisible(True)

        # Pulse animation for indicator
        effect = QGraphicsOpacityEffect(self.new_badges_indicator)
        self.new_badges_indicator.setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect,b"opacity")
        anim.setDuration(1000)
        anim.setKeyValueAt(0,1.0)
        anim.setKeyValueAt(0.5,0.3)
        anim.setKeyValueAt(1.0,1.0)
        anim.setLoopCount(3)  # Pulse 3 times
        anim.start()

        # Hide after 5 seconds
        QTimer.singleShot(5000,self.hide_new_badges_indicator)

    def hide_new_badges_indicator(self):
        """Hide new badges indicator"""
        self.new_badges_indicator.setVisible(False)