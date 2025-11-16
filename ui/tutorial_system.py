"""
Professional Tutorial System for PennyWise - FIXED STACKING ISSUE
Guides new users through the beautiful dashboard without simplifying it
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QGraphicsOpacityEffect)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QPalette, QColor


class TutorialOverlay(QFrame):
    """Professional tutorial overlay that highlights features - FIXED STACKING"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_step = 0
        self.tutorial_steps = []
        self.current_content = None  # Track current content widget
        self.setup_overlay()
        
    def setup_overlay(self):
        """Setup the tutorial overlay"""
        self.setStyleSheet("""
            TutorialOverlay {
                background: rgba(0, 0, 0, 0.7);
                border: none;
            }
        """)
        
        # Make it cover the whole window
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignCenter)
        
    def setup_tutorial_steps(self):
        """Define the tutorial steps for the professional dashboard"""
        self.tutorial_steps = [
            {
                "title": "🎉 Welcome to PennyWise!",
                "message": "I'm Penny, your AI financial companion. Let me show you around your beautiful new dashboard!",
                "highlight": None,
                "position": "center"
            },
            {
                "title": "📊 Your Financial Overview", 
                "message": "Here are your key metrics at a glance. Watch these numbers grow as you save!",
                "highlight": "metrics",
                "position": "top"
            },
            {
                "title": "🦉 Your Financial Guide",
                "message": "This is me! I'll give you personalized tips and insights about your finances.",
                "highlight": "penny",
                "position": "center"
            },
            {
                "title": "📈 Spending & Goals",
                "message": "Track your spending categories and progress toward financial goals.",
                "highlight": "analytics", 
                "position": "center"
            },
            {
                "title": "💫 Smart Insights",
                "message": "Get AI-powered insights about your financial habits and opportunities.",
                "highlight": "story",
                "position": "bottom"
            },
            {
                "title": "⚡ Quick Actions", 
                "message": "Fast access to everything you need. Start by adding a transaction!",
                "highlight": "actions",
                "position": "bottom"
            },
            {
                "title": "🚀 You're All Set!",
                "message": "Ready to take control of your finances? Explore and click around!",
                "highlight": None,
                "position": "center"
            }
        ]
        
    def clear_current_content(self):
        """Clear the current tutorial content"""
        if self.current_content:
            self.current_content.deleteLater()
            self.current_content = None
            
    def show_step(self, step_index):
        """Show a specific tutorial step - FIXED STACKING"""
        if step_index < len(self.tutorial_steps):
            self.current_step = step_index
            step = self.tutorial_steps[step_index]
            
            # Clear previous content FIRST
            self.clear_current_content()
            
            # Create new tutorial content
            self.current_content = QWidget()
            self.current_content.setFixedSize(400, 300)
            self.current_content.setStyleSheet("""
                QWidget {
                    background: white;
                    border-radius: 16px;
                    padding: 0px;
                }
            """)
            
            # Create tutorial step content
            content_layout = QVBoxLayout(self.current_content)
            content_layout.setContentsMargins(25, 25, 25, 20)
            content_layout.setSpacing(15)
            
            # Title
            title = QLabel(step["title"])
            title.setFont(QFont("Segoe UI", 18, QFont.Bold))
            title.setStyleSheet("color: #1F2937; text-align: center;")
            title.setAlignment(Qt.AlignCenter)
            content_layout.addWidget(title)
            
            # Message
            message = QLabel(step["message"])
            message.setFont(QFont("Segoe UI", 13))
            message.setStyleSheet("color: #6B7280; line-height: 1.4;")
            message.setWordWrap(True)
            message.setAlignment(Qt.AlignCenter)
            content_layout.addWidget(message)
            
            # Progress indicator
            progress = QLabel(f"Step {step_index + 1} of {len(self.tutorial_steps)}")
            progress.setStyleSheet("color: #9CA3AF; font-size: 12px;")
            progress.setAlignment(Qt.AlignCenter)
            content_layout.addWidget(progress)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            if step_index > 0:
                back_btn = QPushButton("← Back")
                back_btn.setStyleSheet("""
                    QPushButton {
                        background: rgba(107, 114, 128, 0.1);
                        color: #6B7280;
                        border: none;
                        border-radius: 8px;
                        padding: 10px 20px;
                        font-weight: 500;
                    }
                    QPushButton:hover {
                        background: rgba(107, 114, 128, 0.2);
                    }
                """)
                back_btn.clicked.connect(lambda: self.show_step(step_index - 1))
                button_layout.addWidget(back_btn)
            
            button_layout.addStretch()
            
            skip_btn = QPushButton("Skip Tutorial")
            skip_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #6B7280;
                    border: 1px solid rgba(107, 114, 128, 0.3);
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: rgba(107, 114, 128, 0.1);
                }
            """)
            skip_btn.clicked.connect(self.skip_tutorial)
            button_layout.addWidget(skip_btn)
            
            if step_index < len(self.tutorial_steps) - 1:
                next_btn = QPushButton("Next →")
                next_btn.setStyleSheet("""
                    QPushButton {
                        background: #2563EB;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 10px 20px;
                        font-weight: 600;
                    }
                    QPushButton:hover {
                        background: #1D4ED8;
                    }
                """)
                next_btn.clicked.connect(lambda: self.show_step(step_index + 1))
                button_layout.addWidget(next_btn)
            else:
                finish_btn = QPushButton("Get Started!")
                finish_btn.setStyleSheet("""
                    QPushButton {
                        background: #10B981;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 10px 20px;
                        font-weight: 600;
                    }
                    QPushButton:hover {
                        background: #059669;
                    }
                """)
                finish_btn.clicked.connect(self.complete_tutorial)
                button_layout.addWidget(finish_btn)
            
            content_layout.addLayout(button_layout)
            
            # Add to main layout
            self.main_layout.addWidget(self.current_content)
            
            # Position based on step
            self.position_overlay(step["position"])
            
    def position_overlay(self, position):
        """Position the overlay based on step requirements"""
        parent = self.parent()
        if parent and self.current_content:
            if position == "top":
                self.current_content.move(50, 50)
            elif position == "bottom":
                self.current_content.move(50, parent.height() - 350)
            else:  # center
                self.current_content.move(
                    (parent.width() - 400) // 2, 
                    (parent.height() - 300) // 2
                )
    
    def skip_tutorial(self):
        """Skip the entire tutorial"""
        self.complete_tutorial()
        
    def complete_tutorial(self):
        """Complete the tutorial"""
        self.clear_current_content()
        self.hide()
        if hasattr(self.parent(), 'on_tutorial_complete'):
            self.parent().on_tutorial_complete()
            
    def start_tutorial(self):
        """Start the tutorial"""
        self.setup_tutorial_steps()
        self.show()
        self.show_step(0)


class TutorialManager:
    """Manages the tutorial system"""
    
    def __init__(self, dashboard):
        self.dashboard = dashboard
        self.overlay = TutorialOverlay(dashboard)
        self.overlay.hide()
        
    def should_show_tutorial(self):
        """Check if tutorial should be shown (based on user settings)"""
        # For now, always show for demo. In real app, check user settings
        return True
        
    def start_tutorial(self):
        """Start the tutorial if needed"""
        if self.should_show_tutorial():
            # Resize overlay to cover dashboard
            self.overlay.resize(self.dashboard.size())
            self.overlay.start_tutorial()
            
    def on_tutorial_complete(self):
        """Called when tutorial is completed"""
        print("🎓 Tutorial completed - user can now explore the beautiful dashboard!")
        # In real app: Save to user settings that tutorial is completed