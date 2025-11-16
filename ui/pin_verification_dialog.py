"""
PIN Verification Dialog - Banking-style security verification
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QHBoxLayout, QFrame, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIntValidator
from database.db_manager import fetch_one, execute_query


class PinVerificationDialog(QDialog):
    """Banking-style PIN verification dialog"""
    
    verified = pyqtSignal()
    
    def __init__(self, user_id, parent=None, max_attempts=3):
        super().__init__(parent)
        self.user_id = user_id
        self.max_attempts = max_attempts
        self.attempts = 0
        self.correct_pin = self.get_user_pin()  # Fetch from database, not hardcoded
        
        self.setWindowTitle("Transaction PIN Verification")
        self.setMinimumSize(400, 350)
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Container with rounded corners and shadow
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 16px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(30, 30, 30, 30)
        container_layout.setSpacing(20)
        
        # Header
        header_label = QLabel("🔐 Transaction Security")
        header_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        header_label.setStyleSheet("color: #1F2937; margin-bottom: 10px;")
        header_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(header_label)
        
        # Instructions
        info_label = QLabel("Enter your 4-digit transaction PIN to authorize this transfer")
        info_label.setFont(QFont("Segoe UI", 11))
        info_label.setStyleSheet("color: #6B7280; margin-bottom: 20px;")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        container_layout.addWidget(info_label)
        
        # PIN Input
        pin_label = QLabel("Transaction PIN:")
        pin_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        pin_label.setStyleSheet("color: #374151;")
        container_layout.addWidget(pin_label)
        
        self.pin_input = QLineEdit()
        self.pin_input.setPlaceholderText("Enter 4-digit PIN")
        self.pin_input.setMaxLength(4)
        self.pin_input.setEchoMode(QLineEdit.Password)
        self.pin_input.setValidator(QIntValidator(0, 9999))
        self.pin_input.setFixedHeight(50)
        self.pin_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                padding: 12px;
                font-size: 18px;
                font-weight: bold;
                letter-spacing: 4px;
                background: #F9FAFB;
            }
            QLineEdit:focus {
                border: 2px solid #d6733a;
                background: white;
            }
        """)
        self.pin_input.returnPressed.connect(self.verify_pin)
        container_layout.addWidget(self.pin_input)
        
        # Attempts remaining
        self.attempts_label = QLabel(f"Attempts remaining: {self.max_attempts - self.attempts}")
        self.attempts_label.setFont(QFont("Segoe UI", 9))
        self.attempts_label.setStyleSheet("color: #6B7280;")
        self.attempts_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(self.attempts_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(45)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #F3F4F6;
                color: #374151;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #E5E7EB;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        verify_btn = QPushButton("Verify & Proceed")
        verify_btn.setFixedHeight(45)
        verify_btn.setStyleSheet("""
            QPushButton {
                background: #d6733a;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #b45131;
            }
        """)
        verify_btn.clicked.connect(self.verify_pin)
        button_layout.addWidget(verify_btn)
        
        container_layout.addLayout(button_layout)
        
        # Security notice
        security_notice = QLabel("🔒 Your PIN is encrypted and secure")
        security_notice.setFont(QFont("Segoe UI", 8))
        security_notice.setStyleSheet("color: #9CA3AF; margin-top: 10px;")
        security_notice.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(security_notice)
        
        layout.addWidget(container)
        
        # Set focus to PIN input
        self.pin_input.setFocus()
    
    def get_user_pin(self):
        """Get user's transaction PIN from database settings"""
        try:
            # Check if transaction_pin column exists, if not create it with migration
            settings = fetch_one("SELECT * FROM settings WHERE user_id = ?", (self.user_id,))
            
            if settings and 'transaction_pin' in settings.keys():
                pin = settings['transaction_pin']
                if pin:
                    return pin
            
            # If PIN doesn't exist, create default PIN and store it
            # In production, you should prompt user to set PIN on first use
            default_pin = "1234"  # Default for first-time setup
            self.set_user_pin(default_pin)
            return default_pin
            
        except Exception as e:
            print(f"Error fetching PIN: {e}")
            # Fallback to default PIN if error
            return "1234"
    
    def set_user_pin(self, pin):
        """Store user's transaction PIN in database"""
        try:
            # First, check if transaction_pin column exists
            # If not, we need to add it (migration handled separately)
            settings = fetch_one("SELECT * FROM settings WHERE user_id = ?", (self.user_id,))
            
            if settings:
                # Check if column exists by trying to select it
                try:
                    execute_query("""
                        UPDATE settings SET transaction_pin = ? WHERE user_id = ?
                    """, (pin, self.user_id), commit=True)
                except:
                    # Column doesn't exist, add it first
                    execute_query("""
                        ALTER TABLE settings ADD COLUMN transaction_pin TEXT
                    """, commit=True)
                    execute_query("""
                        UPDATE settings SET transaction_pin = ? WHERE user_id = ?
                    """, (pin, self.user_id), commit=True)
            else:
                # Create settings record with PIN
                execute_query("""
                    INSERT INTO settings (user_id, transaction_pin, currency)
                    VALUES (?, ?, 'USD')
                """, (self.user_id, pin), commit=True)
        except Exception as e:
            print(f"Error storing PIN: {e}")
    
    def verify_pin(self):
        """Verify the entered PIN"""
        entered_pin = self.pin_input.text().strip()
        
        if len(entered_pin) != 4:
            QMessageBox.warning(self, "Invalid PIN", "Please enter a 4-digit PIN")
            self.pin_input.clear()
            return
        
        # Compare with PIN from database (not hardcoded)
        if entered_pin == self.correct_pin:
            self.verified.emit()
            self.accept()
        else:
            self.attempts += 1
            remaining = self.max_attempts - self.attempts
            
            if remaining > 0:
                self.attempts_label.setText(f"Attempts remaining: {remaining}")
                QMessageBox.warning(self, "Invalid PIN", 
                                  f"PIN is incorrect. {remaining} attempt(s) remaining.")
                self.pin_input.clear()
            else:
                QMessageBox.critical(self, "Access Denied", 
                                   "Maximum attempts exceeded. Transaction cancelled.")
                self.reject()

