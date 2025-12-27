"""
Payment Action Sheet for PennyWise
Simple modal for payment actions on a specific commitment
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from ui.dashboard_main import theme_palette


class PaymentActionSheet(QDialog):
    """
    Payment action sheet modal
    Shows payment options for a specific commitment
    """
    # Signals for actions
    pay_now_requested = pyqtSignal(int)  # commitment_id
    mark_paid_requested = pyqtSignal(int)  # commitment_id
    smart_detect_requested = pyqtSignal(int)  # commitment_id
    
    def __init__(self, commitment_id, category_name, status_text, parent=None):
        super().__init__(parent)
        self.commitment_id = commitment_id
        self.setWindowTitle("Payment Options")
        self.setFixedSize(380, 240)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setup_ui(category_name, status_text)
    
    def setup_ui(self, category_name, status_text):
        """Setup the action sheet UI"""
        p = theme_palette()
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Title section
        title_label = QLabel(category_name)
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_label.setStyleSheet(f"color: {p['text_primary']};")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Status subtitle
        status_label = QLabel(status_text)
        status_label.setFont(QFont("Segoe UI", 11))
        status_label.setStyleSheet(f"color: {p['text_secondary']};")
        status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(status_label)
        
        layout.addSpacing(8)
        
        # Action buttons container
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(10)
        
        # Pay Now button
        pay_now_btn = QPushButton("Pay Now")
        pay_now_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        pay_now_btn.setFixedHeight(40)
        pay_now_btn.setStyleSheet(f"""
            QPushButton {{
                background: {p.get('primary', '#2596be')};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
            }}
            QPushButton:hover {{
                background: {p.get('accent', '#2596be')};
            }}
        """)
        pay_now_btn.clicked.connect(lambda: self._handle_pay_now())
        actions_layout.addWidget(pay_now_btn)
        
        # Mark as Paid button
        mark_paid_btn = QPushButton("Mark as Paid (Manual)")
        mark_paid_btn.setFont(QFont("Segoe UI", 10))
        mark_paid_btn.setFixedHeight(40)
        mark_paid_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {p['text_primary']};
                border: 2px solid {p['border']};
                border-radius: 8px;
                padding: 10px;
            }}
            QPushButton:hover {{
                background: {p.get('row_hover', 'rgba(37,150,190,0.08)')};
                border-color: {p.get('primary', '#2596be')};
            }}
        """)
        mark_paid_btn.clicked.connect(lambda: self._handle_mark_paid())
        actions_layout.addWidget(mark_paid_btn)
        
        # Smart Detect button
        smart_detect_btn = QPushButton("Smart Detect")
        smart_detect_btn.setFont(QFont("Segoe UI", 10))
        smart_detect_btn.setFixedHeight(40)
        smart_detect_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {p['text_primary']};
                border: 2px solid {p['border']};
                border-radius: 8px;
                padding: 10px;
            }}
            QPushButton:hover {{
                background: {p.get('row_hover', 'rgba(37,150,190,0.08)')};
                border-color: {p.get('primary', '#2596be')};
            }}
        """)
        smart_detect_btn.clicked.connect(lambda: self._handle_smart_detect())
        actions_layout.addWidget(smart_detect_btn)
        
        layout.addLayout(actions_layout)
        
        # Dialog styling
        self.setStyleSheet(f"""
            QDialog {{
                background: {p['surface']};
                border: 1px solid {p['border']};
                border-radius: 12px;
            }}
        """)
    
    def _handle_pay_now(self):
        """Handle Pay Now action - emit signal and close"""
        self.pay_now_requested.emit(self.commitment_id)
        self.accept()
    
    def _handle_mark_paid(self):
        """Handle Mark as Paid action - emit signal and close"""
        self.mark_paid_requested.emit(self.commitment_id)
        self.accept()
    
    def _handle_smart_detect(self):
        """Handle Smart Detect action - emit signal and close"""
        self.smart_detect_requested.emit(self.commitment_id)
        self.accept()

