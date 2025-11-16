"""
Penny Companion Widget - The heart and soul of PennyWise
"""

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import QRect, QSize

from .penny_avatar import PennyAvatar
from assets.styles.penny_colors import PennyColors


class PennyWidget(QFrame):
    """Main Penny companion widget with avatar and speech bubble"""
    
    # Signal emitted when Penny has a new message
    message_updated = pyqtSignal(str, str)  # message, tone
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_tone = "friendly"
        self.message_history = []
        self.is_expanded = False
        
        self.setup_ui()
        self.apply_styling()
        self.setup_animations()
        
    def setup_ui(self):
        """Setup Penny's main layout"""
        self.setProperty("class", "penny_widget")
        self.setFixedHeight(120)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(20)
        
        # Left: Penny's Avatar
        self.avatar = PennyAvatar(size=80)
        main_layout.addWidget(self.avatar)
        
        # Right: Speech bubble and controls
        right_layout = QVBoxLayout()
        right_layout.setSpacing(8)
        
        # Speech bubble
        self.bubble_frame = QFrame()
        self.bubble_frame.setProperty("class", "penny_bubble")
        self.bubble_frame.setFixedHeight(80)
        
        bubble_layout = QHBoxLayout(self.bubble_frame)
        bubble_layout.setContentsMargins(16, 12, 16, 12)
        
        self.message_label = QLabel("💭 Penny is thinking...")
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("color: #1F2937; font-size: 14px; line-height: 1.4;")
        self.message_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        bubble_layout.addWidget(self.message_label)
        
        right_layout.addWidget(self.bubble_frame)
        
        # Controls row
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)
        
        self.history_btn = QPushButton("📜 History")
        self.history_btn.setFixedHeight(28)
        self.history_btn.clicked.connect(self.toggle_history)
        
        self.refresh_btn = QPushButton("🔄 New Tip")
        self.refresh_btn.setFixedHeight(28)
        self.refresh_btn.clicked.connect(self.request_new_tip)
        
        controls_layout.addWidget(self.history_btn)
        controls_layout.addWidget(self.refresh_btn)
        controls_layout.addStretch()
        
        right_layout.addLayout(controls_layout)
        main_layout.addLayout(right_layout)
        
        # Apply styling to buttons
        self.style_buttons()
        
    def style_buttons(self):
        """Apply consistent styling to buttons"""
        button_style = """
            QPushButton {
                background: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 12px;
                color: #6B7280;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.9);
                border-color: rgba(37, 99, 235, 0.3);
                color: #2563EB;
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 1);
            }
        """
        self.history_btn.setStyleSheet(button_style)
        self.refresh_btn.setStyleSheet(button_style)
        
    def apply_styling(self):
        """Apply Penny's special styling"""
        self.setStyleSheet("""
            QFrame[class="penny_widget"] {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(254, 243, 199, 0.3), 
                    stop:1 rgba(253, 230, 138, 0.3));
                border: 1px solid rgba(245, 158, 11, 0.2);
                border-radius: 20px;
            }
            QFrame[class="penny_bubble"] {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FEF3C7, stop:1 #FDE68A);
                border-left: 4px solid #F59E0B;
                border-radius: 12px;
            }
        """)
        
    def setup_animations(self):
        """Setup entrance and interaction animations"""
        # Bubble pulse animation
        self.bubble_animation = QPropertyAnimation(self.bubble_frame, b"geometry")
        self.bubble_animation.setDuration(800)
        self.bubble_animation.setEasingCurve(QEasingCurve.OutElastic)
        
        # Message fade animation
        self.message_animation = QPropertyAnimation(self.message_label, b"windowOpacity")
        self.message_animation.setDuration(400)
        self.message_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
    def update_message(self, message, tone="friendly"):
        """Update Penny's message with tone-based styling"""
        self.current_tone = tone
        self.message_history.append((message, tone))
        
        # Keep only last 10 messages
        if len(self.message_history) > 10:
            self.message_history.pop(0)
            
        # Animate message change
        self.message_animation.setStartValue(0.3)
        self.message_animation.setEndValue(1.0)
        self.message_animation.start()
        
        self.message_label.setText(message)
        self.apply_tone_styling(tone)
        
        # Emit signal for other components
        self.message_updated.emit(message, tone)
        
        # Trigger bubble animation
        self.animate_bubble()
        
    def apply_tone_styling(self, tone):
        """Apply tone-specific styling to the bubble"""
        tone_colors = {
            "friendly": ("#FEF3C7", "#FDE68A", "#F59E0B"),
            "positive": ("#D1FAE5", "#A7F3D0", "#10B981"),
            "encouraging": ("#DBEAFE", "#93C5FD", "#2563EB"),
            "warning": ("#FEF3C7", "#FDE68A", "#F59E0B"),
            "alert": ("#FEE2E2", "#FCA5A5", "#DC2626")
        }
        
        start_color, end_color, border_color = tone_colors.get(
            tone, tone_colors["friendly"]
        )
        
        self.bubble_frame.setStyleSheet(f"""
            QFrame[class="penny_bubble"] {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {start_color}, stop:1 {end_color});
                border-left: 4px solid {border_color};
                border-radius: 12px;
            }}
        """)
        
    def animate_bubble(self):
        """Animate the speech bubble for emphasis"""
        original_geometry = self.bubble_frame.geometry()
        
        # Create a gentle bounce effect
        self.bubble_animation.setStartValue(
            QRect(original_geometry.x() - 2, original_geometry.y() - 1,
                  original_geometry.width() + 4, original_geometry.height() + 2)
        )
        self.bubble_animation.setEndValue(original_geometry)
        self.bubble_animation.start()
        
    def toggle_history(self):
        """Toggle message history view"""
        # This would open a history dialog in a full implementation
        print("📜 History button clicked - would show message history")
        # For now, cycle through last messages
        if self.message_history and len(self.message_history) > 1:
            # Show previous message
            prev_message, prev_tone = self.message_history[-2]
            self.update_message(prev_message, prev_tone)
            
    def request_new_tip(self):
        """Request a new AI tip"""
        print("🔄 New tip requested - would trigger AI service")
        # This would connect to the AI service in the full implementation
        # For now, show a placeholder
        self.update_message("💡 Let me think of something fresh for you...", "friendly")
        
        # Simulate AI thinking delay
        QTimer.singleShot(1500, self._simulate_new_tip)
        
    def _simulate_new_tip(self):
        """Simulate getting a new AI tip"""
        import random
        demo_tips = [
            ("I suggest reviewing your weekly spending to find saving opportunities!", "friendly"),
            ("Great job staying within budget this week! 🎉", "positive"),
            ("Let's set up automatic savings for your next paycheck!", "encouraging"),
            ("Watch out for dining out expenses this month.", "warning"),
            ("Your savings are growing steadily! Keep it up! 📈", "positive")
        ]
        
        tip, tone = random.choice(demo_tips)
        self.update_message(tip, tone)
        
    def get_current_message(self):
        """Get Penny's current message"""
        return self.message_label.text(), self.current_tone
        
    def clear_history(self):
        """Clear message history"""
        self.message_history.clear()
        self.update_message("💭 Hello! I'm Penny, your financial companion.", "friendly")