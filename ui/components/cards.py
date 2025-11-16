"""
Card Widget Component
"""

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtProperty
from PyQt5.QtGui import QFont

class CardWidget(QFrame):
    """Reusable card component with consistent styling"""
    
    def __init__(self, title="", subtitle="", parent=None):
        super().__init__(parent)
        self.title = title
        self.subtitle = subtitle
        
        self.setup_ui()
        self.apply_styling()
    
    def setup_ui(self):
        """Setup card layout and content"""
        self.setProperty("class", "card")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Header
        if self.title or self.subtitle:
            header_layout = QVBoxLayout()
            header_layout.setSpacing(4)
            
            if self.title:
                self.title_label = QLabel(self.title)
                self.title_label.setProperty("class", "card-title")
                self.title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
                header_layout.addWidget(self.title_label)
            
            if self.subtitle:
                self.subtitle_label = QLabel(self.subtitle)
                self.subtitle_label.setProperty("class", "card-subtitle")
                self.subtitle_label.setFont(QFont("Segoe UI", 12))
                self.subtitle_label.setStyleSheet("color: #6B7280;")
                header_layout.addWidget(self.subtitle_label)
            
            layout.addLayout(header_layout)
        
        # Content area
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(8)
        layout.addLayout(self.content_layout)
        
        layout.addStretch()
    
    def apply_styling(self):
        """Apply card styling"""
        self.setStyleSheet("""
            QFrame[class="card"] {
                background: #FFFFFF;
                border: 1px solid rgba(0, 0, 0, 0.06);
                border-radius: 16px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            }
            QFrame[class="card"]:hover {
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
                border-color: rgba(37, 99, 235, 0.2);
            }
        """)
    
    def add_widget(self, widget):
        """Add widget to card content"""
        self.content_layout.addWidget(widget)
    
    def add_layout(self, layout):
        """Add layout to card content"""
        self.content_layout.addLayout(layout)
    
    def set_title(self, title):
        """Update card title"""
        if hasattr(self, 'title_label'):
            self.title_label.setText(title)
    
    def set_subtitle(self, subtitle):
        """Update card subtitle"""
        if hasattr(self, 'subtitle_label'):
            self.subtitle_label.setText(subtitle)