from PyQt5.QtWidgets import (
    QDialog,QLabel,QLineEdit,QPushButton,QVBoxLayout,
    QComboBox,QMessageBox,QSpinBox,QCheckBox,QHBoxLayout,
    QGraphicsDropShadowEffect,QWidget,QDateEdit,QTextEdit,
    QRadioButton,QButtonGroup,QScrollArea
)
from PyQt5.QtCore import Qt, QDate, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette
from database.db_manager import fetch_all,fetch_one,execute_query
import qtawesome as qta
from core.logger import logger


class ModernDialogHeader(QWidget):
    """Modern dialog header with icon, title, and close button"""
    def __init__(self, parent, title, icon='fa5s.piggy-bank'):
        super().__init__(parent)
        self.dialog = parent
        self.setFixedHeight(60)
        self.drag_position = None
        self.setMouseTracking(True)
        self.setup_ui(title, icon)
    
    def mousePressEvent(self, event):
        """Make header draggable"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos()
    
    def mouseMoveEvent(self, event):
        """Handle dragging"""
        if self.drag_position and event.buttons() == Qt.LeftButton:
            delta = event.globalPos() - self.drag_position
            self.dialog.move(self.dialog.pos() + delta)
            self.drag_position = event.globalPos()
            event.accept()
    
    def setup_ui(self, title, icon):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 10, 10)
        layout.setSpacing(15)
        
        # Icon
        try:
            icon_pixmap = qta.icon(icon, color='#d6733a')
            icon_label = QLabel()
            icon_label.setPixmap(icon_pixmap.pixmap(32, 32))
            layout.addWidget(icon_label)
        except Exception as e:
            print(f"Could not load icon: {e}")
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title_label.setStyleSheet("color: #1F2937;")
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # Close button
        try:
            close_icon = qta.icon('fa5s.times', color='#6B7280')
            close_btn = QPushButton()
            close_btn.setIcon(close_icon)
            close_btn.setFixedSize(32, 32)
            close_btn.clicked.connect(self.dialog.reject)
            close_btn.setToolTip("Close")
            close_btn.setStyleSheet("""
                QPushButton {
                    border: none;
                    background: transparent;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background: #F3F4F6;
                }
                QPushButton:pressed {
                    background: #E5E7EB;
                }
            """)
            layout.addWidget(close_btn)
        except Exception as e:
            print(f"Could not load close icon: {e}")


class CommitmentForm(QDialog):
    commitment_added = pyqtSignal(float)
    commitments_changed = pyqtSignal()
    commitment_created = pyqtSignal()  # New signal for notification manager

    def __init__(self,user_id,category_name=None,parent_dashboard=None):
        super().__init__()
        self.user_id = user_id
        self.category_name = category_name
        self.parent_dashboard = parent_dashboard
        self.setWindowTitle("Add Commitment")
        self.setMinimumSize(550,650)
        
        # Set window flags for a clean modern look
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        self.init_ui()
        
        # Connect inputs to preview
        self.name_input.textChanged.connect(self.update_preview)
        self.amount_input.textChanged.connect(self.update_preview)
        self.day_input.valueChanged.connect(self.update_preview)
        self.detection_group.buttonClicked.connect(self.update_preview)
        
        # Known brands for Smart Detect
        self.known_brands = ['netflix', 'spotify', 'apple music', 'applemusic', 'amazon prime', 
                            'amazon', 'hulu', 'disney', 'youtube', 'google', 'microsoft',
                            'adobe', 'dropbox', 'zoom', 'slack', 'discord', 'twitch']

    def init_ui(self):
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create a background widget that fills the entire dialog
        bg_widget = QWidget()
        bg_widget.setAttribute(Qt.WA_StyledBackground, True)
        bg_widget.setStyleSheet("background-color: #f9f7f5;")
        bg_layout = QVBoxLayout(bg_widget)
        bg_layout.setContentsMargins(20, 20, 20, 20)
        bg_layout.setSpacing(0)
        
        # Style the dialog
        self.setStyleSheet("""
            ModernDialogHeader {
                background-color: white;
                border-radius: 16px 16px 0 0;
                border-bottom: 1px solid #E5E7EB;
            }
            QLabel {
                color: #374151;
                font-size: 14px;
                font-weight: 500;
            }
            QComboBox, QLineEdit {
                border: 2px solid #D1D5DB;
                border-radius: 10px;
                padding: 12px;
                font-size: 14px;
                background-color: white;
            }
            QComboBox:hover, QLineEdit:hover {
                border-color: #d6733a;
            }
            QComboBox:focus, QLineEdit:focus {
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
            QCheckBox {
                font-size: 14px;
                color: #374151;
            }
            QRadioButton {
                font-size: 14px;
                color: #374151;
                padding: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
        """)

        # Container widget to hold everything with white background and shadow
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
        
        # Add drop shadow effect to container
        shadow = QGraphicsDropShadowEffect(container)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 60))
        container.setGraphicsEffect(shadow)

        # Add modern header
        header = ModernDialogHeader(self, "Add Commitment", icon='fa5s.credit-card')
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
        
        # Commitment Details Section
        commitment_header = self.create_section_header("Commitment Details")
        content_layout.addWidget(commitment_header)

        name_label = QLabel("Commitment Name:")
        content_layout.addWidget(name_label)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Netflix, Gym Membership, Rent")
        self.name_input.setFixedHeight(40)
        self.name_input.setToolTip("💡 Tip: For Smart Detect, name it exactly as it appears in your transactions (e.g., 'Netflix', 'Emu Gym', 'Local Cafe'). This helps automatically match payments!")
        content_layout.addWidget(self.name_input)

        amount_label = QLabel("Monthly Amount:")
        content_layout.addWidget(amount_label)
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("e.g., 15.99")
        self.amount_input.setFixedHeight(40)
        content_layout.addWidget(self.amount_input)

        day_label = QLabel("Due Day of Month:")
        content_layout.addWidget(day_label)
        self.day_input = QSpinBox()
        self.day_input.setRange(1, 31)
        self.day_input.setValue(1)
        self.day_input.setFixedHeight(40)
        content_layout.addWidget(self.day_input)

        # Optional Transfer Account
        transfer_header = self.create_section_header("Transfer Account (Optional)")
        content_layout.addWidget(transfer_header)
        
        bank_label = QLabel("Bank Name:")
        content_layout.addWidget(bank_label)
        self.bank_name_input = QLineEdit()
        self.bank_name_input.setPlaceholderText("e.g., Chase, Bank of America")
        self.bank_name_input.setFixedHeight(40)
        content_layout.addWidget(self.bank_name_input)
        
        account_label = QLabel("Account Number:")
        content_layout.addWidget(account_label)
        self.account_number_input = QLineEdit()
        self.account_number_input.setPlaceholderText("Leave empty if not applicable")
        self.account_number_input.setFixedHeight(40)
        content_layout.addWidget(self.account_number_input)

        # Payment Detection Options Section
        detection_header = self.create_section_header("Payment Detection")
        content_layout.addWidget(detection_header)
        
        # Create button group for radio buttons
        self.detection_group = QButtonGroup()
        
        # Manual option
        self.manual_radio = QRadioButton("Mark as Paid Manually")
        self.manual_radio.setChecked(True)  # Default option
        self.manual_radio.setStyleSheet("""
            QRadioButton {
                font-size: 14px;
                color: #374151;
                padding: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        manual_info = QLabel("You'll manually mark this commitment as paid each month.")
        manual_info.setStyleSheet("color: #6B7280; font-size: 12px; padding-left: 30px; margin-top: -5px;")
        content_layout.addWidget(self.manual_radio)
        content_layout.addWidget(manual_info)
        self.detection_group.addButton(self.manual_radio, 0)
        
        # Smart Detect option
        self.smart_radio = QRadioButton("Smart Detect")
        self.smart_radio.setStyleSheet("""
            QRadioButton {
                font-size: 14px;
                color: #374151;
                padding: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        smart_info = QLabel("PennyWise will automatically scan your recent transactions and match them to this commitment. Works best for big name brands (Netflix, Spotify, etc.) or use the commitment name to match - if you name it 'Emu Gym', it will search for 'Emu Gym' in your debit transactions.")
        smart_info.setStyleSheet("color: #6B7280; font-size: 12px; padding-left: 30px; margin-top: -5px;")
        smart_info.setWordWrap(True)
        content_layout.addWidget(self.smart_radio)
        content_layout.addWidget(smart_info)
        self.detection_group.addButton(self.smart_radio, 1)
        
        # Pay as you go option
        self.paynow_radio = QRadioButton("Pay as you go")
        self.paynow_radio.setStyleSheet("""
            QRadioButton {
                font-size: 14px;
                color: #374151;
                padding: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        paynow_info = QLabel("This commitment won't auto-detect payments. Use 'Pay now' from the dashboard menu when you're ready to make a payment.")
        paynow_info.setStyleSheet("color: #6B7280; font-size: 12px; padding-left: 30px; margin-top: -5px;")
        paynow_info.setWordWrap(True)
        content_layout.addWidget(self.paynow_radio)
        content_layout.addWidget(paynow_info)
        self.detection_group.addButton(self.paynow_radio, 2)

        # Total Deduction Preview
        self.preview_label = QLabel("")
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #F0F9FF;
                border: 2px solid #d6733a;
                border-radius: 10px;
                padding: 14px;
                font-size: 14px;
                font-weight: 600;
                color: #1E40AF;
            }
        """)
        self.preview_label.setWordWrap(True)
        content_layout.addWidget(self.preview_label)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        self.save_btn = QPushButton("Save Commitment")
        self.save_btn.clicked.connect(self.save_commitment)
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

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        content_layout.addLayout(btn_layout)

        # Add scroll area to container layout
        container_layout.addWidget(scroll_area)
        
        # Add scroll buttons
        scroll_btn_layout = QHBoxLayout()
        scroll_btn_layout.setContentsMargins(30, 0, 30, 15)
        scroll_btn_layout.addStretch()
        
        up_btn = QPushButton("↑")
        up_btn.setFixedSize(40, 30)
        up_btn.setStyleSheet("""
            QPushButton {
                background-color: #F3F4F6;
                color: #374151;
                border: 1px solid #D1D5DB;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
                border-color: #9CA3AF;
            }
            QPushButton:pressed {
                background-color: #D1D5DB;
            }
        """)
        up_btn.clicked.connect(lambda: scroll_area.verticalScrollBar().setValue(
            scroll_area.verticalScrollBar().value() - 50
        ))
        
        down_btn = QPushButton("↓")
        down_btn.setFixedSize(40, 30)
        down_btn.setStyleSheet("""
            QPushButton {
                background-color: #F3F4F6;
                color: #374151;
                border: 1px solid #D1D5DB;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
                border-color: #9CA3AF;
            }
            QPushButton:pressed {
                background-color: #D1D5DB;
            }
        """)
        down_btn.clicked.connect(lambda: scroll_area.verticalScrollBar().setValue(
            scroll_area.verticalScrollBar().value() + 50
        ))
        
        scroll_btn_layout.addWidget(up_btn)
        scroll_btn_layout.addSpacing(10)
        scroll_btn_layout.addWidget(down_btn)
        scroll_btn_layout.addStretch()
        
        container_layout.addLayout(scroll_btn_layout)
        
        # Add container to background layout
        bg_layout.addWidget(container)
        
        # Add background widget to main layout
        layout.addWidget(bg_widget)
        
        # Initial preview update
        self.update_preview()
    
    def create_section_header(self, title):
        """Create a styled section header"""
        header = QLabel(title)
        header.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header.setStyleSheet("""
            QLabel {
                color: #1F2937;
                font-weight: 700;
                margin-top: 10px;
            }
        """)
        return header
    
    def update_preview(self):
        """Update the commitment preview"""
        try:
            name = self.name_input.text().strip()
            amount = float(self.amount_input.text())
            if amount > 0 and name:
                # Get currency from settings
                currency_row = fetch_one("SELECT currency FROM settings WHERE user_id = ?", (self.user_id,))
                currency = currency_row["currency"] if currency_row else "USD"
                
                method_id = self.detection_group.checkedId()
                method_text = "Smart Detect" if method_id == 1 else "Pay as you go" if method_id == 2 else "Manual"
                
                self.preview_label.setText(
                    f"💳 {name}: ${amount:,.2f} {currency} due on day {self.day_input.value()} of each month\n"
                    f"Payment detection: {method_text}"
                )
            else:
                self.preview_label.setText("")
        except (ValueError, AttributeError):
            self.preview_label.setText("")


    def save_commitment(self):
        """Save commitment based on selected payment detection method"""
        # #region agent log
        import json as _json
        import time as _time
        try:
            with open(r'c:\Users\asus\OneDrive\Desktop\PennyWise\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(_json.dumps({"sessionId":"debug-session","runId":"balances-pre-fix","hypothesisId":"H4","location":"commitment_form.py:save_commitment","message":"save_commitment invoked","data":{"user_id":getattr(self,'user_id',None)}, "timestamp":int(_time.time()*1000)}) + "\n")
        except Exception:
            pass
        # #endregion
        try:
            # Validate inputs
            name = self.name_input.text().strip()
            if not name:
                QMessageBox.warning(self,"Error","Please enter a commitment name")
                return
            
            # Get amount first before using it
            try:
                amount = float(self.amount_input.text())
                if amount <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self,"Error","Please enter a valid amount greater than 0")
                return
            
            due_day = self.day_input.value()
            bank_name = self.bank_name_input.text().strip() or None
            account_number = self.account_number_input.text().strip() or None
            
            # Get selected payment detection method
            detection_method = self.detection_group.checkedId()
            
            # STEP 1: Create category IMMEDIATELY and show in UI (optimistic update)
            # This allows users to see their commitment category right away
            category = fetch_one("""
                SELECT category_id FROM categories WHERE category_name = ? AND user_id = ?
            """, (name, self.user_id))
            
            if not category:
                # Create new category with the commitment name
                execute_query("""
                    INSERT INTO categories (user_id, category_name, color, budget_amount)
                    VALUES (?, ?, ?, ?)
                """, (self.user_id, name, '#6B7280', amount), commit=True)
                
                category = fetch_one("""
                    SELECT category_id FROM categories WHERE category_name = ? AND user_id = ?
                    ORDER BY category_id DESC LIMIT 1
                """, (name, self.user_id))
            
            if not category:
                QMessageBox.critical(self, "Error", "Could not create or find category")
                return
            
            cat_id = category['category_id']
            
            # STEP 2: IMMEDIATELY refresh UI to show the category (non-blocking)
            # This makes the user see their commitment right away
            if self.parent_dashboard and hasattr(self.parent_dashboard, 'commitment_tracker'):
                # Trigger immediate refresh so user sees the category
                QTimer.singleShot(10, lambda: self.parent_dashboard.commitment_tracker.load_commitments())
            
            # STEP 3: Do validation and background work (non-blocking)
            # Check if name matches known brands for Smart Detect
            name_lower = name.lower()
            is_known_brand = any(brand in name_lower for brand in self.known_brands)
            
            # If Smart Detect is selected but not a known brand, show warning
            if detection_method == 1 and not is_known_brand:
                reply = QMessageBox.question(
                    self, "Smart Detect Warning",
                    f"'{name}' may not be recognized as a known brand. Smart Detect works best for brands like Netflix, Spotify, etc.\n\n"
                    "Would you like to continue with Smart Detect anyway?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            # Emit optimistic delta signal for fast UI updates
            self._emit_commitment_delta(amount)

            # STEP 4: Save commitment in background (after UI update)
            # Run table alterations and commitment save asynchronously
            def save_commitment_background():
                try:
                    # Ensure table columns exist (non-blocking)
                    try:
                        execute_query("""
                            ALTER TABLE category_commitments 
                            ADD COLUMN detection_method INTEGER DEFAULT 0
                        """, commit=True)
                    except:
                        pass  # Column might already exist
                    
                    try:
                        execute_query("""
                            ALTER TABLE category_commitments 
                            ADD COLUMN bank_name TEXT
                        """, commit=True)
                    except:
                        pass  # Column might already exist
                        
                    try:
                        execute_query("""
                            ALTER TABLE category_commitments 
                            ADD COLUMN account_number TEXT
                        """, commit=True)
                    except:
                        pass  # Column might already exist
                    
                    # Save commitment
                    execute_query("""
                        INSERT INTO category_commitments 
                        (user_id, category_id, amount, due_day, detection_method, bank_name, account_number, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                    """, (self.user_id, cat_id, amount, due_day, detection_method, bank_name, account_number), commit=True)
                    
                    # Final refresh to sync everything - rebuild balance cards immediately
                    if self.parent_dashboard:
                        if hasattr(self.parent_dashboard, 'commitment_tracker'):
                            self.parent_dashboard.commitment_tracker.load_commitments()
                        # Rebuild balance cards with fresh Plaid data and updated commitments
                        if hasattr(self.parent_dashboard, 'rebuild_overview_cards'):
                            self.parent_dashboard.rebuild_overview_cards()
                        self.parent_dashboard.refresh_dashboard()
                except Exception as e:
                    print(f"Error saving commitment background: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Run background save after a tiny delay (allows UI to update first)
            QTimer.singleShot(100, save_commitment_background)
            
            # Close the dialog immediately so user can see their commitment
            result = self.accept()
            if result == QDialog.Accepted:
                # Reload commitments so the new entry appears immediately
                self.load_commitments()
                self.trigger_dashboard_refresh()
                self.commitments_changed.emit()
                # Emit signal for notification manager
                self.commitment_created.emit()
            
            # Show success dialog (non-blocking)
            self.show_commitment_created_dialog(name, amount, due_day, detection_method)
            
            # Refresh metrics cards after a short delay
            if self.parent_dashboard:
                def refresh_metrics():
                    try:
                        # CRITICAL: Refresh metrics cards to update "Price After Commitments" when new commitment is added
                        if hasattr(self.parent_dashboard, 'refresh_metrics_cards_main'):
                            self.parent_dashboard.refresh_metrics_cards_main()
                        if hasattr(self.parent_dashboard, 'metrics_carousel') and self.parent_dashboard.metrics_carousel:
                            if hasattr(self.parent_dashboard.metrics_carousel, 'refresh_metrics_cards'):
                                self.parent_dashboard.metrics_carousel.refresh_metrics_cards()
                        self.parent_dashboard.refresh_dashboard()
                        # Additional refresh to ensure UI updates
                        QTimer.singleShot(100, lambda: (
                            self.parent_dashboard.refresh_metrics_cards_main() if hasattr(self.parent_dashboard, 'refresh_metrics_cards_main') else None,
                            self.parent_dashboard.metrics_carousel.refresh_metrics_cards() if (hasattr(self.parent_dashboard, 'metrics_carousel') and self.parent_dashboard.metrics_carousel) else None
                        ))
                    except Exception as e:
                        print(f"❌ Error refreshing metrics: {e}")
                
                QTimer.singleShot(300, refresh_metrics)
                
        except Exception as e:
            QMessageBox.critical(self,"Error",f"Could not save commitment: {e}")
            import traceback
            traceback.print_exc()

    def _emit_commitment_delta(self, amount: float):
        """Emit commitment delta signal with logging for easier debugging."""
        try:
            logger.info(f"[CommitmentForm] Emitting commitment_added (+{amount:.2f})")
        except Exception:
            pass
        self.commitment_added.emit(float(amount))
    
    def show_commitment_created_dialog(self, name, amount, due_day, detection_method):
        """Show a beautifully styled commitment created dialog"""
        from assets.styles.penny_colors import PennyColors
        
        msg = QMessageBox(self.parent_dashboard if self.parent_dashboard else self)
        msg.setWindowTitle("✅ Commitment Created")
        msg.setIcon(QMessageBox.Information)
        
        if detection_method == 2:
            method_text = "Pay as you go"
        elif detection_method == 1:
            method_text = "Smart Detect"
        else:
            method_text = "Manual"
        
        # Style the message box with PennyWise theme
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {PennyColors.SURFACE};
                color: {PennyColors.TEXT_PRIMARY};
                font-family: 'Segoe UI', system-ui, sans-serif;
            }}
            QMessageBox QLabel {{
                color: {PennyColors.TEXT_PRIMARY};
                font-family: 'Segoe UI', system-ui, sans-serif;
                font-size: 14px;
            }}
            QMessageBox QPushButton {{
                background-color: {PennyColors.PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-weight: 600;
                font-size: 14px;
                min-width: 100px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: #1D4ED8;
            }}
            QMessageBox QPushButton:pressed {{
                background-color: #1E40AF;
            }}
        """)
        
        # Create styled HTML content
        confirmation_text = f"""
        <div style='font-family: "Segoe UI", system-ui, sans-serif; padding: 10px;'>
        <h3 style='color: {PennyColors.SUCCESS}; font-weight: 600; font-size: 18px; margin-bottom: 12px;'>
            ✅ Commitment '{name}' Created!
        </h3>
        <p style='color: {PennyColors.TEXT_PRIMARY}; font-size: 14px; margin: 8px 0;'>
            <b>Amount:</b> ${amount:,.2f} due on day {due_day} of each month
        </p>
        <p style='color: {PennyColors.TEXT_SECONDARY}; font-size: 13px; margin: 8px 0;'>
            <b>Payment Detection:</b> {method_text}
        </p>
        <p style='color: {PennyColors.TEXT_SECONDARY}; font-size: 12px; margin-top: 15px; font-style: italic;'>
            Hover over the commitment on your dashboard to mark as paid, use Smart Detect, or pay as you go.
        </p>
        </div>
        """
        
        msg.setText(confirmation_text)
        msg.setStandardButtons(QMessageBox.Ok)
        
        # Style the OK button
        ok_button = msg.button(QMessageBox.Ok)
        if ok_button:
            ok_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {PennyColors.PRIMARY};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 24px;
                    font-weight: 600;
                    font-size: 14px;
                    min-width: 100px;
                }}
                QPushButton:hover {{
                    background-color: #1D4ED8;
                }}
                QPushButton:pressed {{
                    background-color: #1E40AF;
                }}
            """)
        
        msg.exec_()

    # In your CommitmentForm, add logic for Savings vs other categories

    def create_commitment(self):
        from database.db_manager import execute_query
        from datetime import datetime

        amount = self.amount_input.value()
        description = self.desc_input.text().strip()
        due_date = self.due_date.date().toString("yyyy-MM-dd")

        if amount <= 0:
            QMessageBox.warning(self,"Error","Please enter a valid amount.")
            return

        # Determine if this is a Savings commitment
        is_savings = self.category_name and self.category_name.lower() == 'savings'

        if is_savings:
            action_type = "savings transfer"
            success_message = f"✅ ${amount} monthly savings transfer created!"
        else:
            action_type = "payment"
            success_message = f"💰 ${amount} monthly payment created for {self.category_name}!"

        try:
            execute_query("""
                INSERT INTO category_commitments 
                (user_id, category_id, amount, description, is_paid, due_date, created_at)
                VALUES (?, ?, ?, ?, 0, ?, ?)
            """,(self.user_id,self.category_id,amount,description,due_date,datetime.now()),commit=True)

            QMessageBox.information(self,"Success",success_message)
            self.accept()

        except Exception as e:
            QMessageBox.critical(self,"Error",f"Failed to create {action_type}: {str(e)}")


class CommitmentSelectionDialog(QDialog):
    """Modern dialog for selecting or creating a commitment"""
    
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.selected_item = None
        self.setWindowTitle("Add Commitment")
        self.setMinimumSize(520, 480)
        
        # Set window flags for modern look
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        self.init_ui()
        self.load_common_commitments()
    
    def init_ui(self):
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Background widget
        bg_widget = QWidget()
        bg_widget.setAttribute(Qt.WA_StyledBackground, True)
        bg_widget.setStyleSheet("background-color: #f9f7f5;")
        bg_layout = QVBoxLayout(bg_widget)
        bg_layout.setContentsMargins(20, 20, 20, 20)
        bg_layout.setSpacing(0)
        
        # Style the dialog
        self.setStyleSheet("""
            QComboBox {
                border: 2px solid #D1D5DB;
                border-radius: 10px;
                padding: 12px;
                font-size: 14px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #d6733a;
            }
            QComboBox:focus {
                border-color: #d6733a;
            }
            QLineEdit, QDateEdit {
                border: 2px solid #D1D5DB;
                border-radius: 10px;
                padding: 12px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:hover, QDateEdit:hover {
                border-color: #d6733a;
            }
            QLineEdit:focus, QDateEdit:focus {
                border-color: #d6733a;
            }
        """)
        
        # Container with shadow
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
        
        # Drop shadow effect
        shadow = QGraphicsDropShadowEffect(container)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 60))
        container.setGraphicsEffect(shadow)
        
        # Modern header
        header = ModernDialogHeader(self, "Add Commitment", icon='fa5s.credit-card')
        container_layout.addWidget(header)
        
        # Content container
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(30, 25, 30, 30)
        content_widget.setStyleSheet("background-color: white; border-radius: 0 0 16px 16px;")
        
        # Instructions label with proper spacing
        instruction_label = QLabel("Select a commitment or create a custom one:")
        instruction_label.setFont(QFont("Segoe UI", 14))
        instruction_label.setStyleSheet("color: #374151; font-weight: 500;")
        content_layout.addWidget(instruction_label)
        
        # Commitment dropdown
        self.commitment_combo = QComboBox()
        self.commitment_combo.setFixedHeight(45)
        self.commitment_combo.currentIndexChanged.connect(self.on_commitment_changed)
        content_layout.addWidget(self.commitment_combo)
        
        # Custom fields container (initially hidden)
        self.custom_widget = QWidget()
        custom_layout = QVBoxLayout(self.custom_widget)
        custom_layout.setContentsMargins(0, 0, 0, 0)
        custom_layout.setSpacing(15)
        
        # Custom Name
        custom_name_label = QLabel("Custom Name:")
        custom_name_label.setFont(QFont("Segoe UI", 12))
        custom_name_label.setStyleSheet("color: #374151;")
        custom_layout.addWidget(custom_name_label)
        
        self.custom_name_input = QLineEdit()
        self.custom_name_input.setPlaceholderText("e.g., Insurance Premium")
        self.custom_name_input.setFixedHeight(45)
        custom_layout.addWidget(self.custom_name_input)
        
        # Amount
        amount_label = QLabel("Amount:")
        amount_label.setFont(QFont("Segoe UI", 12))
        amount_label.setStyleSheet("color: #374151;")
        custom_layout.addWidget(amount_label)
        
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("0.00")
        self.amount_input.setFixedHeight(45)
        custom_layout.addWidget(self.amount_input)
        
        # Due Date
        due_date_label = QLabel("First Due Date:")
        due_date_label.setFont(QFont("Segoe UI", 12))
        due_date_label.setStyleSheet("color: #374151;")
        custom_layout.addWidget(due_date_label)
        
        self.due_date_input = QDateEdit()
        self.due_date_input.setCalendarPopup(True)
        self.due_date_input.setDate(QDate.currentDate().addDays(1))
        self.due_date_input.setFixedHeight(45)
        custom_layout.addWidget(self.due_date_input)
        
        # Frequency
        frequency_label = QLabel("Frequency:")
        frequency_label.setFont(QFont("Segoe UI", 12))
        frequency_label.setStyleSheet("color: #374151;")
        custom_layout.addWidget(frequency_label)
        
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(["Monthly", "Yearly", "Weekly", "Bi-weekly"])
        self.frequency_combo.setFixedHeight(45)
        custom_layout.addWidget(self.frequency_combo)
        
        # Notes/Description
        notes_label = QLabel("Notes (optional):")
        notes_label.setFont(QFont("Segoe UI", 12))
        notes_label.setStyleSheet("color: #374151;")
        custom_layout.addWidget(notes_label)
        
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Add any notes or context...")
        self.notes_input.setFixedHeight(80)
        self.notes_input.setStyleSheet("""
            QTextEdit {
                border: 2px solid #D1D5DB;
                border-radius: 10px;
                padding: 8px;
                font-size: 14px;
                background-color: white;
            }
            QTextEdit:hover {
                border-color: #d6733a;
            }
            QTextEdit:focus {
                border-color: #d6733a;
            }
        """)
        custom_layout.addWidget(self.notes_input)
        
        self.custom_widget.hide()
        content_layout.addWidget(self.custom_widget)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        self.add_btn = QPushButton("Add")
        self.add_btn.clicked.connect(self.accept_dialog)
        self.add_btn.setFixedHeight(50)
        self.add_btn.setStyleSheet("""
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
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setFixedHeight(50)
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
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.add_btn)
        content_layout.addLayout(btn_layout)
        
        # Add content to container
        container_layout.addWidget(content_widget)
        
        # Add container to background layout
        bg_layout.addWidget(container)
        
        # Add background to main layout
        layout.addWidget(bg_widget)
    
    def load_common_commitments(self):
        """Load common commitment templates"""
        common_commitments = [
            ("Netflix", 15.99),
            ("Spotify", 9.99),
            ("Amazon Prime", 12.99),
            ("Gym Membership", 29.99),
            ("Internet", 79.99),
            ("Phone Bill", 45.00),
            ("--- Custom ---", None)
        ]
        
        self.commitment_combo.addItem("Select a commitment...", None)
        for name, amount in common_commitments:
            if amount is not None:
                self.commitment_combo.addItem(f"{name} (${amount:,.2f})", {"name": name, "amount": amount, "is_custom": False})
            else:
                self.commitment_combo.addItem(name, {"name": "Custom", "is_custom": True})
    
    def on_commitment_changed(self, index):
        """Handle commitment selection change"""
        if index == 0:  # "Select a commitment..."
            self.custom_widget.hide()
            self.add_btn.setEnabled(False)
            return
        
        data = self.commitment_combo.currentData()
        if data and data.get("is_custom", False):
            self.custom_widget.show()
            self.add_btn.setEnabled(True)
            self.custom_name_input.setFocus()
        else:
            self.custom_widget.hide()
            self.add_btn.setEnabled(True)
    
    def accept_dialog(self):
        """Validate and accept the dialog"""
        index = self.commitment_combo.currentIndex()
        
        if index == 0:
            QMessageBox.warning(self, "Selection Required", "Please select a commitment.")
            return
        
        data = self.commitment_combo.currentData()
        
        if data and data.get("is_custom", False):
            # Validate custom fields
            custom_name = self.custom_name_input.text().strip()
            if not custom_name:
                QMessageBox.warning(self, "Invalid Input", "Please enter a custom commitment name.")
                self.custom_name_input.setFocus()
                return
            
            try:
                amount = float(self.amount_input.text())
                if amount <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Invalid Amount", "Please enter a valid amount greater than 0.")
                self.amount_input.setFocus()
                return
            
            self.selected_item = {
                "name": custom_name,
                "amount": amount,
                "due_date": self.due_date_input.date().toString("yyyy-MM-dd"),
                "frequency": self.frequency_combo.currentText(),
                "notes": self.notes_input.toPlainText().strip(),
                "is_custom": True
            }
        else:
            # Use common commitment data
            self.selected_item = {
                "name": data.get("name"),
                "amount": data.get("amount"),
                "due_date": None,
                "frequency": "Monthly",
                "notes": "",
                "is_custom": False
            }
        
        self.accept()
    
    def get_selected_item(self):
        """Get the selected commitment data"""
        return self.selected_item