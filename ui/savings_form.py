# ui/savings_form.py
"""
Savings Form - Separate form for adding savings goals (different from commitments)
"""
from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QComboBox, QMessageBox, QSpinBox, QHBoxLayout,
    QGraphicsDropShadowEffect, QWidget, QTextEdit,
    QScrollArea
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from database.db_manager import fetch_all, fetch_one, execute_query
from ui.commitment_form import ModernDialogHeader
import qtawesome as qta
from datetime import datetime

class SavingsForm(QDialog):
    """Form for adding savings goals - separate from commitments"""
    
    def __init__(self, user_id, parent_dashboard=None):
        super().__init__()
        self.user_id = user_id
        self.parent_dashboard = parent_dashboard
        self.setWindowTitle("Add Savings Goal")
        self.setMinimumSize(550, 600)
        
        # Set window flags for a clean modern look
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Style the dialog
        self.setStyleSheet("""
            QLabel {
                color: #374151;
                font-size: 14px;
                font-weight: 500;
            }
            QComboBox, QLineEdit, QTextEdit {
                border: 2px solid #D1D5DB;
                border-radius: 10px;
                padding: 12px;
                font-size: 14px;
                background-color: white;
            }
            QComboBox:hover, QLineEdit:hover, QTextEdit:hover {
                border-color: #d6733a;
            }
            QComboBox:focus, QLineEdit:focus, QTextEdit:focus {
                border-color: #d6733a;
            }
            QSpinBox {
                border: 2px solid #D1D5DB;
                border-radius: 10px;
                padding: 12px;
                font-size: 14px;
                background-color: white;
            }
            QSpinBox:hover {
                border-color: #d6733a;
            }
        """)
        
        # Container widget
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 16px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Add drop shadow effect
        shadow = QGraphicsDropShadowEffect(container)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 60))
        container.setGraphicsEffect(shadow)
        
        # Add modern header
        header = ModernDialogHeader(self, "Add Savings Goal", icon='fa5s.piggy-bank')
        container_layout.addWidget(header)
        
        # Content container with scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #F3F4F6;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #D1D5DB;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #9CA3AF;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(30, 25, 30, 30)
        content_widget.setStyleSheet("background-color: white; border-radius: 0 0 16px 16px;")
        
        scroll_area.setWidget(content_widget)
        
        # Savings Goal Details Section
        goal_header = self.create_section_header("Savings Goal Details")
        content_layout.addWidget(goal_header)
        
        target_amount_label = QLabel("Target Amount:")
        content_layout.addWidget(target_amount_label)
        self.target_amount_input = QLineEdit()
        self.target_amount_input.setPlaceholderText("e.g., 5000.00")
        self.target_amount_input.setFixedHeight(40)
        content_layout.addWidget(self.target_amount_input)
        
        # Monthly Contribution Section
        contribution_header = self.create_section_header("Monthly Contribution")
        content_layout.addWidget(contribution_header)
        
        monthly_amount_label = QLabel("Monthly Contribution Amount:")
        content_layout.addWidget(monthly_amount_label)
        self.monthly_amount_input = QLineEdit()
        self.monthly_amount_input.setPlaceholderText("e.g., 200.00")
        self.monthly_amount_input.setFixedHeight(40)
        content_layout.addWidget(self.monthly_amount_input)
        
        # Target Date Section
        target_date_header = self.create_section_header("Target Date (Optional)")
        content_layout.addWidget(target_date_header)
        
        target_year_label = QLabel("Target Year:")
        content_layout.addWidget(target_year_label)
        self.target_year_input = QSpinBox()
        self.target_year_input.setRange(datetime.now().year, datetime.now().year + 20)
        self.target_year_input.setValue(datetime.now().year + 1)
        self.target_year_input.setFixedHeight(40)
        content_layout.addWidget(self.target_year_input)
        
        target_month_label = QLabel("Target Month:")
        content_layout.addWidget(target_month_label)
        self.target_month_input = QSpinBox()
        self.target_month_input.setRange(1, 12)
        self.target_month_input.setValue(12)
        self.target_month_input.setFixedHeight(40)
        content_layout.addWidget(self.target_month_input)
        
        # Notes Section
        notes_label = QLabel("Notes (Optional):")
        content_layout.addWidget(notes_label)
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Add any notes about this savings goal...")
        self.notes_input.setFixedHeight(80)
        content_layout.addWidget(self.notes_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setFixedHeight(45)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #374151;
                border: 2px solid #D1D5DB;
                border-radius: 10px;
                font-size: 15px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #F9FAFB;
                border-color: #9CA3AF;
            }
            QPushButton:pressed {
                background-color: #F3F4F6;
            }
        """)
        
        self.save_btn = QPushButton("Save Savings Goal")
        self.save_btn.clicked.connect(self.save_savings_goal)
        self.save_btn.setFixedHeight(45)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #d6733a;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 15px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #b45131;
            }
            QPushButton:pressed {
                background-color: #9a4a28;
            }
        """)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        content_layout.addLayout(button_layout)
        
        content_layout.addStretch()
        
        container_layout.addWidget(scroll_area)
        layout.addWidget(container)
    
    def create_section_header(self, title):
        """Create a section header"""
        header = QLabel(title)
        header.setFont(QFont("Segoe UI", 14, QFont.Bold))
        header.setStyleSheet("color: #1F2937; margin-top: 10px; margin-bottom: 5px;")
        return header
    
    def save_savings_goal(self):
        """Save the savings goal"""
        try:
            # Savings is always just "Savings" - no custom name needed
            goal_name = "Savings"
            
            target_amount_str = self.target_amount_input.text().strip()
            if not target_amount_str:
                QMessageBox.warning(self, "Validation Error", "Please enter a target amount.")
                return
            
            try:
                target_amount = float(target_amount_str)
                if target_amount <= 0:
                    raise ValueError("Target amount must be greater than 0")
            except ValueError:
                QMessageBox.warning(self, "Validation Error", "Please enter a valid target amount.")
                return
            
            monthly_amount_str = self.monthly_amount_input.text().strip()
            if not monthly_amount_str:
                QMessageBox.warning(self, "Validation Error", "Please enter a monthly contribution amount.")
                return
            
            try:
                monthly_amount = float(monthly_amount_str)
                if monthly_amount <= 0:
                    raise ValueError("Monthly amount must be greater than 0")
            except ValueError:
                QMessageBox.warning(self, "Validation Error", "Please enter a valid monthly contribution amount.")
                return
            
            target_year = self.target_year_input.value()
            target_month = self.target_month_input.value()
            notes = self.notes_input.toPlainText().strip()
            
            # Calculate target date
            target_date = f"{target_year}-{target_month:02d}-01"
            
            # Create or update savings category - just "Savings"
            category_name = "Savings"
            
            # Check if category already exists
            existing_category = fetch_one("""
                SELECT category_id FROM categories 
                WHERE user_id = ? AND category_name = ?
            """, (self.user_id, category_name))
            
            if existing_category:
                category_id = existing_category['category_id']
                # Update existing category
                execute_query("""
                    UPDATE categories 
                    SET budget_amount = ?, notes = ?
                    WHERE category_id = ?
                """, (target_amount, notes, category_id), commit=True)
            else:
                # Create new category
                execute_query("""
                    INSERT INTO categories (user_id, category_name, budget_amount, notes, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (self.user_id, category_name, target_amount, notes, datetime.now().isoformat()), commit=True)
                
                # Get the new category_id
                new_category = fetch_one("""
                    SELECT category_id FROM categories 
                    WHERE user_id = ? AND category_name = ?
                    ORDER BY category_id DESC LIMIT 1
                """, (self.user_id, category_name))
                category_id = new_category['category_id']
            
            # Create or update the commitment entry in category_commitments
            # This is what makes it show up in the Monthly Commitments section
            existing_commitment = fetch_one("""
                SELECT commitment_id FROM category_commitments 
                WHERE user_id = ? AND category_id = ?
            """, (self.user_id, category_id))
            
            if existing_commitment:
                # Update existing commitment
                execute_query("""
                    UPDATE category_commitments 
                    SET amount = ?, is_paid = 0
                    WHERE commitment_id = ?
                """, (monthly_amount, existing_commitment['commitment_id']), commit=True)
            else:
                # Create new commitment with monthly contribution amount
                execute_query("""
                    INSERT INTO category_commitments (user_id, category_id, amount, due_day, is_paid, created_at)
                    VALUES (?, ?, ?, 1, 0, ?)
                """, (self.user_id, category_id, monthly_amount, datetime.now().isoformat()), commit=True)
            
            QMessageBox.information(self, "Success", "Savings goal saved successfully!")
            
            # Refresh dashboard if parent exists
            if self.parent_dashboard:
                if hasattr(self.parent_dashboard, 'refresh_dashboard'):
                    self.parent_dashboard.refresh_dashboard()
            
            self.accept()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save savings goal: {str(e)}")
            import traceback
            traceback.print_exc()


