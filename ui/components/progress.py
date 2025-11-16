"""
Custom Progress Bar Component
"""

from PyQt5.QtWidgets import QProgressBar, QHBoxLayout, QLabel, QWidget
from PyQt5.QtCore import Qt

class ProgressBar(QWidget):
    """Enhanced progress bar with label and styling"""
    
    def __init__(self, value=0, maximum=100, label="", show_percentage=True, variant="default", parent=None):
        super().__init__(parent)
        self.value = value
        self.maximum = maximum
        self.label = label
        self.show_percentage = show_percentage
        self.variant = variant  # "default", "success", "warning", "danger"
        
        self.setup_ui()
        self.apply_styling()
    
    def setup_ui(self):
        """Setup progress bar layout"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Label
        if self.label:
            self.label_widget = QLabel(self.label)
            self.label_widget.setFixedWidth(120)
            self.label_widget.setStyleSheet("color: #6B7280; font-size: 12px;")
            layout.addWidget(self.label_widget)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(self.value)
        self.progress_bar.setMaximum(self.maximum)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        layout.addWidget(self.progress_bar)
        
        # Percentage label
        if self.show_percentage:
            self.percentage_label = QLabel()
            self.percentage_label.setFixedWidth(40)
            self.percentage_label.setAlignment(Qt.AlignRight)
            self.percentage_label.setStyleSheet("color: #6B7280; font-size: 12px; font-weight: 600;")
            layout.addWidget(self.percentage_label)
            
            self.update_percentage()
    
    def apply_styling(self):
        """Apply progress bar styling based on variant"""
        colors = {
            "default": ("#10B981", "#34D399"),
            "success": ("#10B981", "#34D399"),
            "warning": ("#F59E0B", "#F59E0B"),
            "danger": ("#EF4444", "#DC2626")
        }
        
        start_color, end_color = colors.get(self.variant, colors["default"])
        
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background: #E5E7EB;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                           stop:0 {start_color}, stop:1 {end_color});
                border-radius: 4px;
            }}
        """)
    
    def update_percentage(self):
        """Update percentage label"""
        if hasattr(self, 'percentage_label'):
            percentage = (self.value / self.maximum) * 100 if self.maximum > 0 else 0
            self.percentage_label.setText(f"{percentage:.0f}%")
    
    def set_value(self, value):
        """Set progress value"""
        self.value = value
        self.progress_bar.setValue(value)
        self.update_percentage()
    
    def set_variant(self, variant):
        """Change progress bar variant"""
        self.variant = variant
        self.apply_styling()