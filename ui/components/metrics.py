"""
Metric Chip Component for displaying key metrics
"""

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class MetricChip(QFrame):
    """Metric chip for displaying key financial metrics"""
    
    def __init__(self, value="0", label="Metric", trend=None, parent=None):
        super().__init__(parent)
        self.value = value
        self.label = label
        self.trend = trend  # "up", "down", or None
        
        self.setup_ui()
        self.apply_styling()
    
    def setup_ui(self):
        """Setup metric chip layout"""
        self.setProperty("class", "metric-chip")
        self.setFixedSize(140, 100)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignCenter)
        
        # Value
        self.value_label = QLabel(self.value)
        self.value_label.setProperty("class", "metric-value")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        
        # Label with optional trend indicator
        label_text = self.label
        if self.trend == "up":
            label_text = f"📈 {self.label}"
        elif self.trend == "down":
            label_text = f"📉 {self.label}"
        
        self.label_label = QLabel(label_text)
        self.label_label.setProperty("class", "metric-label")
        self.label_label.setAlignment(Qt.AlignCenter)
        self.label_label.setFont(QFont("Segoe UI", 10))
        
        layout.addWidget(self.value_label)
        layout.addWidget(self.label_label)
    
    def apply_styling(self):
        """Apply metric chip styling"""
        # Color based on trend
        color = "#2563EB"  # Default blue
        if self.trend == "up":
            color = "#10B981"  # Green for positive
        elif self.trend == "down":
            color = "#EF4444"  # Red for negative
        
        self.setStyleSheet(f"""
            QFrame[class="metric-chip"] {{
                background: #FFFFFF;
                border: 1px solid rgba(0, 0, 0, 0.08);
                border-radius: 16px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            }}
            QLabel[class="metric-value"] {{
                color: {color};
                font-size: 20px;
                font-weight: bold;
            }}
            QLabel[class="metric-label"] {{
                color: #6B7280;
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
        """)
    
    def update_value(self, value, trend=None):
        """Update metric value and trend"""
        self.value = value
        self.trend = trend
        
        self.value_label.setText(str(value))
        
        # Update label with trend indicator
        label_text = self.label
        if trend == "up":
            label_text = f"📈 {self.label}"
        elif trend == "down":
            label_text = f"📉 {self.label}"
        
        self.label_label.setText(label_text)
        self.apply_styling()