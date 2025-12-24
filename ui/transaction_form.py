from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QComboBox, QTextEdit, QCheckBox, QMessageBox, QHBoxLayout,
    QScrollArea, QFrame, QProgressBar, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
from database.db_manager import fetch_all, fetch_one, execute_query
from core.transactions import add_txn
from core.currency import convert
from core.plaid_api import create_transfer, simulate_transfer_webhook
from ui.pin_verification_dialog import PinVerificationDialog
from assets.styles.penny_colors import PennyColors
import datetime
import uuid
from ui.transfer_form import TransferForm


class TransactionForm(QWidget):
    # Signal emitted when transaction is saved
    transaction_saved = pyqtSignal()
    
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.parent_dashboard = parent
        self.pending_commitment_id = None  # Store commitment_id when "Pay Now" is used
        self.setWindowTitle("Transactions & Categories")
        self.setMinimumSize(500, 500)

        self.transactions_view = QWidget()
        self.categories_view = QWidget()
        self.stack_layout = QVBoxLayout()
        self.container = QVBoxLayout()

        self.init_toggle_buttons()
        self.init_transaction_form()
        self.init_categories_view()

        self.stack_layout.addWidget(self.transactions_view)
        self.setLayout(self.container)
        self.container.addLayout(self.toggle_btn_layout)
        self.container.addLayout(self.stack_layout)

    def init_toggle_buttons(self):
        self.toggle_btn_layout = QHBoxLayout()
        self.txn_btn = QPushButton("Transactions View")
        self.cat_btn = QPushButton("Simulate Transactions")
        self.txn_btn.clicked.connect(self.show_transaction_form)
        self.cat_btn.clicked.connect(self.show_category_view)

        self.toggle_btn_layout.addWidget(self.txn_btn)
        self.toggle_btn_layout.addWidget(self.cat_btn)

    # View 1: Transactions
    def init_transaction_form(self):
        layout = QVBoxLayout()
        self.amount_input = QLineEdit()
        self.type_input = QComboBox()
        self.cat_input = QComboBox()
        self.acc_input = QComboBox()
        self.to_account_name_input = QLineEdit()
        self.to_account_input = QLineEdit()
        self.note_input = QTextEdit()
        self.recurring = QCheckBox("Recurring")
        self.save_btn = QPushButton("Transfer")
        self.convert_lbl = QLabel()

        self.amount_input.setPlaceholderText("amount e.g. 150.00")
        self.amount_input.textChanged.connect(self.show_converted)
        self.type_input.addItems(["expense", "income"])
        self.to_account_name_input.setPlaceholderText("recipient name or bank name")
        self.to_account_input.setPlaceholderText("account number")
        self.note_input.setPlaceholderText("note or desc (opt)")
        
        # Make description box smaller
        self.note_input.setFixedHeight(60)

        layout.addWidget(QLabel("Amount"))
        layout.addWidget(self.amount_input)
        layout.addWidget(self.convert_lbl)

        layout.addWidget(QLabel("Type"))
        layout.addWidget(self.type_input)

        layout.addWidget(QLabel("Category"))
        layout.addWidget(self.cat_input)

        layout.addWidget(QLabel("From Account"))
        layout.addWidget(self.acc_input)
        
        layout.addWidget(QLabel("To Account Name"))
        layout.addWidget(self.to_account_name_input)
        
        layout.addWidget(QLabel("To Account Number"))
        layout.addWidget(self.to_account_input)

        layout.addWidget(QLabel("Description"))
        layout.addWidget(self.note_input)

        layout.addWidget(self.recurring)
        layout.addWidget(self.save_btn)

        self.save_btn.clicked.connect(self.save_txn)

        self.transactions_view.setLayout(layout)
        self.load_cats()
        self.load_accs()

    def show_transaction_form(self):
        self.stack_layout.removeWidget(self.categories_view)
        self.categories_view.setVisible(False)
        self.stack_layout.addWidget(self.transactions_view)
        self.transactions_view.setVisible(True)

    def show_category_view(self):
        self.stack_layout.removeWidget(self.transactions_view)
        self.transactions_view.setVisible(False)
        self.stack_layout.addWidget(self.categories_view)
        self.categories_view.setVisible(True)

    def load_cats(self):
        rows = fetch_all("select category_id, category_name from categories where user_id = ?", (self.user_id,))
        self.cat_input.clear()
        for r in rows:
            self.cat_input.addItem(r["category_name"], r["category_id"])
        
        # Connect category change to auto-fill savings accounts when Savings is selected
        self.cat_input.currentIndexChanged.connect(self.on_category_changed)

    def load_accs(self):
        # Use 'id' (INTEGER) instead of 'account_id' (TEXT) for foreign key reference
        rows = fetch_all("select id, account_id, bank_name, account_type from accounts where user_id = ?", (self.user_id,))
        self.acc_input.clear()
        for r in rows:
            bank_name = r["bank_name"] or "Unknown Bank"
            account_type = r["account_type"] or "account"
            # Display format: "Bank Name (Account Type)"
            display_name = f"{bank_name} ({account_type})"
            # Store the database 'id' (INTEGER) for foreign key, not Plaid 'account_id' (TEXT)
            self.acc_input.addItem(display_name, r["id"])
    
    def prefill_savings_transaction(self, amount, from_account_id, to_account_number, category_id, to_account_name=None):
        """Pre-fill the transaction form for a savings payment"""
        try:
            # Set amount
            self.amount_input.setText(str(amount))
            
            # Set transaction type to expense
            self.type_input.setCurrentText("expense")
            
            # Set category to Savings
            category_index = self.cat_input.findData(category_id)
            if category_index >= 0:
                self.cat_input.setCurrentIndex(category_index)
            
            # Auto-fill From Account: Find checking account (salary or checking type)
            if from_account_id:
                from_account_index = self.acc_input.findData(from_account_id)
                if from_account_index >= 0:
                    self.acc_input.setCurrentIndex(from_account_index)
                else:
                    # If not found, try to reload accounts and find again
                    self.load_accs()
                    from_account_index = self.acc_input.findData(from_account_id)
                    if from_account_index >= 0:
                        self.acc_input.setCurrentIndex(from_account_index)
            else:
                # Auto-find checking account if not provided
                self.auto_fill_savings_accounts()
            
            # Auto-fill To Account: Get savings account details
            if not to_account_number or not to_account_name:
                self.auto_fill_savings_accounts()
            else:
                # Set To Account Name if provided
                if to_account_name:
                    self.to_account_name_input.setText(str(to_account_name))
                
                # Set To Account Number
                self.to_account_input.setText(str(to_account_number))
            
            # Set note/description for savings transfer (will be formatted in save_txn)
            self.note_input.setPlainText("Savings transfer")
            
            # Show the transaction form view (not categories view)
            self.show_transaction_form()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to pre-fill form: {str(e)}")
    
    def auto_fill_savings_accounts(self):
        """Auto-fill From Account (checking) and To Account (savings) when Savings category is selected"""
        try:
            # Get checking account (salary or checking type) for "From Account"
            checking_account = fetch_one("""
                SELECT id, bank_name, account_type 
                FROM accounts 
                WHERE user_id = ? AND (account_type = 'salary' OR account_type = 'checking')
                ORDER BY id LIMIT 1
            """, (self.user_id,))
            
            if checking_account:
                checking_id = checking_account['id'] if 'id' in checking_account.keys() else None
                if checking_id:
                    checking_index = self.acc_input.findData(checking_id)
                    if checking_index >= 0:
                        self.acc_input.setCurrentIndex(checking_index)
            
            # Get savings account for "To Account"
            savings_account = fetch_one("""
                SELECT account_id, bank_name, account_type 
                FROM accounts 
                WHERE user_id = ? AND account_type = 'savings'
                LIMIT 1
            """, (self.user_id,))
            
            if savings_account:
                # Set To Account Name (bank name)
                bank_name = savings_account['bank_name'] if 'bank_name' in savings_account.keys() else None
                if bank_name:
                    self.to_account_name_input.setText(str(bank_name))
                
                # Set To Account Number (last 4 digits of account_id for display)
                account_id = savings_account['account_id'] if 'account_id' in savings_account.keys() else ''
                if account_id:
                    if len(str(account_id)) > 4:
                        account_display = f"****{str(account_id)[-4:]}"
                    else:
                        account_display = str(account_id)
                    self.to_account_input.setText(account_display)
        except Exception as e:
            print(f"Error auto-filling savings accounts: {e}")
    
    def on_category_changed(self, index):
        """Called when category selection changes - auto-fill savings accounts if Savings is selected"""
        try:
            if index >= 0:
                category_id = self.cat_input.currentData()
                if category_id:
                    # Get category name to check if it's Savings
                    category_row = fetch_one("SELECT category_name FROM categories WHERE category_id = ?", (category_id,))
                    if category_row:
                        category_name = category_row['category_name']
                        if category_name and category_name.lower() == 'savings':
                            # Auto-fill checking account (from) and savings account (to)
                            self.auto_fill_savings_accounts()
                            # Also set transaction type to expense for savings transfers
                            if self.type_input.currentText() != 'expense':
                                self.type_input.setCurrentText("expense")
        except Exception as e:
            print(f"Error handling category change: {e}")

    def get_user_currency(self):
        row = fetch_one("select currency from settings where user_id = ?", (self.user_id,))
        return row["currency"] if row else "USD"

    def show_converted(self):
        try:
            amt = float(self.amount_input.text())
            curr = self.get_user_currency()
            result = convert(amt, "USD", curr)
            if result is not None:
                self.convert_lbl.setText(f"= {result} {curr}")
            else:
                self.convert_lbl.setText("")
        except:
            self.convert_lbl.setText("")

    def save_txn(self):
        """Process transaction with banking-style verification and Plaid integration"""
        try:
            # Validate inputs
            amt = float(self.amount_input.text())
            if amt <= 0:
                QMessageBox.warning(self, "Invalid Amount", "Amount must be greater than zero")
                return
            
            tx_type = self.type_input.currentText()
            cat_id = self.cat_input.currentData()
            acc_id = self.acc_input.currentData()
            
            if not acc_id:
                QMessageBox.warning(self, "Missing Account", "Please select a from account")
                return
            
            # Get account details for Plaid transfer
            account_row = fetch_one("""
                SELECT account_id, plaid_token, bank_name, account_type
                FROM accounts WHERE id = ?
            """, (acc_id,))
            
            if not account_row:
                QMessageBox.warning(self, "Error", "Account not found")
                return
            
            # Show PIN verification dialog (banking-style security)
            pin_dialog = PinVerificationDialog(self.user_id, self)
            if pin_dialog.exec_() != QDialog.Accepted:
                QMessageBox.information(self, "Cancelled", "Transaction cancelled - PIN not verified")
                return
            
            # Show processing screen
            self.show_processing_screen(amt)
            
            # Get Plaid access token (using dictionary access for sqlite3.Row)
            plaid_token = account_row['plaid_token'] if 'plaid_token' in account_row.keys() else None
            plaid_account_id = account_row['account_id']  # Plaid account ID (TEXT)
            
            # For savings transfers, create Plaid transfer
            cat_name = None
            if cat_id:
                cat_row = fetch_one("SELECT category_name FROM categories WHERE category_id = ?", (cat_id,))
                if cat_row:
                    cat_name = cat_row['category_name']
            
            is_savings = cat_name and cat_name.lower() == 'savings'
            to_account_name = self.to_account_name_input.text().strip()
            to_account = self.to_account_input.text().strip()
            note = self.note_input.toPlainText()
            
            # Generate transaction reference
            transaction_ref = f"TXN{uuid.uuid4().hex[:8].upper()}"
            
            # Build description
            if is_savings:
                description = f"PennyWise: Savings Transfer - Ref: {transaction_ref}"
                if to_account_name:
                    description += f" - To {to_account_name}"
                if to_account:
                    description += f" (Acct: {to_account})"
            else:
                if to_account_name or to_account:
                    to_part = ""
                    if to_account_name:
                        to_part = f"To {to_account_name}"
                    if to_account:
                        if to_part:
                            to_part += f" (Acct: {to_account})"
                        else:
                            to_part = f"To Account {to_account}"
                    description = f"PennyWise: Transfer - Ref: {transaction_ref} - {to_part}"
                elif note:
                    description = f"PennyWise: {note} - Ref: {transaction_ref}"
                else:
                    description = f"PennyWise: Transaction - Ref: {transaction_ref}"
            
            # Create Plaid transfer if we have access token and it's a transfer
            transfer_id = None
            if plaid_token and is_savings:
                # Get destination savings account
                savings_account = fetch_one("""
                    SELECT account_id, plaid_token FROM accounts
                    WHERE user_id = ? AND account_type = 'savings' LIMIT 1
                """, (self.user_id,))
                
                # Use dictionary access for sqlite3.Row
                savings_plaid_token = savings_account['plaid_token'] if 'plaid_token' in savings_account.keys() else None
                savings_account_id = savings_account['account_id'] if 'account_id' in savings_account.keys() else None
                
                if savings_account and savings_plaid_token:
                    transfer_result = create_transfer(
                        savings_plaid_token,
                        plaid_account_id,
                        savings_account_id,
                        str(amt),
                        description
                    )
                    
                    if "error" not in transfer_result and isinstance(transfer_result, dict):
                        transfer_data = transfer_result.get("transfer", {})
                        if isinstance(transfer_data, dict):
                            transfer_id = transfer_data.get("id")
                        # Simulate webhook for sandbox
                        if transfer_id:
                            simulate_transfer_webhook(transfer_id, "TRANSFER_SENT")
            
            # Save transaction to database (description already includes transaction reference)
            now = datetime.datetime.now()
            recur = int(self.recurring.isChecked())
            add_txn(self.user_id, acc_id, cat_id, amt, tx_type, description, now, recur)
            
            # Update simulated_balance for developer testing
            # In production, Stripe/Plaid handles real balance changes
            if tx_type == "expense":
                execute_query("""
                    UPDATE accounts SET simulated_balance = simulated_balance - ?
                    WHERE id = ? AND simulated_balance IS NOT NULL
                """, (amt, acc_id), commit=True)
            elif tx_type == "income":
                execute_query("""
                    UPDATE accounts SET simulated_balance = simulated_balance + ?
                    WHERE id = ? AND simulated_balance IS NOT NULL
                """, (amt, acc_id), commit=True)
            
            # Mark commitment as paid - Priority 1: If "Pay Now" was used (pending_commitment_id exists)
            # Priority 2: Try automatic matching
            commitment_matched = False
            try:
                # Priority 1: Explicitly mark commitment if "Pay Now" was used
                if self.pending_commitment_id:
                    from database.db_manager import execute_query
                    execute_query("""
                        UPDATE category_commitments
                        SET is_paid = 1,
                            last_paid_date = CURRENT_TIMESTAMP,
                            paid_date = ?
                        WHERE commitment_id = ? AND user_id = ?
                    """, (now.isoformat(), self.pending_commitment_id, self.user_id), commit=True)
                    commitment_matched = True
                    print(f"✅ Commitment {self.pending_commitment_id} explicitly marked as paid from 'Pay Now'")
                    
                    # Clear the pending commitment_id
                    self.pending_commitment_id = None
                    
                    # Refresh commitment tracker and dashboard
                    if self.parent_dashboard and hasattr(self.parent_dashboard, 'commitment_tracker'):
                        self.parent_dashboard.commitment_tracker.load_commitments()
                    # Also refresh dashboard metrics so Balance After Commitments updates
                    if self.parent_dashboard:
                        if hasattr(self.parent_dashboard, 'refresh_metrics_cards_main'):
                            self.parent_dashboard.refresh_metrics_cards_main()
                        if hasattr(self.parent_dashboard, 'metrics_carousel'):
                            self.parent_dashboard.metrics_carousel.refresh_metrics_cards()
                # Priority 2: Try automatic matching if no explicit commitment
                elif cat_id:
                    from core.transactions import try_mark_commitment_for_txn
                    # Get account_id for matching (use database id, not Plaid account_id)
                    # Match by category_id and amount (within $1 tolerance)
                    matched = try_mark_commitment_for_txn(self.user_id, acc_id, cat_id, amt, description, now.date().isoformat())
                    if matched:
                        commitment_matched = True
                        print(f"✅ Commitment matched and marked as paid for {description}")
                        # Refresh commitment tracker
                        if self.parent_dashboard and hasattr(self.parent_dashboard, 'commitment_tracker'):
                            self.parent_dashboard.commitment_tracker.load_commitments()
                        # Also refresh dashboard metrics when an automatic match occurs
                        if self.parent_dashboard:
                            if hasattr(self.parent_dashboard, 'refresh_metrics_cards_main'):
                                self.parent_dashboard.refresh_metrics_cards_main()
                            if hasattr(self.parent_dashboard, 'metrics_carousel'):
                                self.parent_dashboard.metrics_carousel.refresh_metrics_cards()
                    else:
                        print(f"⚠️ No commitment matched for category_id={cat_id}, amount={amt}, description={description}")
            except Exception as e:
                print(f"Commitment match error: {e}")
                import traceback
                traceback.print_exc()
            
            # CRITICAL: IMMEDIATELY refresh dashboard to update:
            # 1. Available balance (updated based on transaction type and account) - ESPECIALLY FOR SIMULATED TRANSACTIONS
            # 2. Savings balance (updated if savings transfer - expense decreases, income increases)
            # 3. Price after commitments (decreased because commitment marked as paid)
            # 4. Commitment status (shows checkmark if matched)
            if self.parent_dashboard:
                # Force refresh of all components - this recalculates balances IMMEDIATELY
                # This is critical for simulated transactions to update available balance
                self.parent_dashboard.refresh_dashboard()
                
                # CRITICAL: Refresh metrics cards main to update:
                # - Available Balance (checking balance, decreases when expense from checking) - MUST UPDATE FOR ALL TRANSACTIONS
                # - Savings Balance (increases when income to savings, decreases when expense from savings)
                # - Price After Commitments (decreases when commitment marked as paid)
                if hasattr(self.parent_dashboard, 'refresh_metrics_cards_main'):
                    self.parent_dashboard.refresh_metrics_cards_main()
                
                # Also refresh metrics carousel (includes savings balance)
                if hasattr(self.parent_dashboard, 'metrics_carousel'):
                    self.parent_dashboard.metrics_carousel.refresh_metrics_cards()
                
                # CRITICAL: Refresh recent transactions IMMEDIATELY to show new transaction
                # This is especially important for "Pay Now" transactions
                if hasattr(self.parent_dashboard, 'refresh_recent_transactions'):
                    self.parent_dashboard.refresh_recent_transactions()
                # Also refresh after a short delay to ensure it shows up
                QTimer.singleShot(50, lambda: (
                    self.parent_dashboard.refresh_recent_transactions() if (hasattr(self.parent_dashboard, 'refresh_recent_transactions')) else None
                ))
                
                # Also refresh commitments specifically if a commitment was matched
                if commitment_matched and hasattr(self.parent_dashboard, 'commitment_tracker'):
                    self.parent_dashboard.commitment_tracker.refresh_commitments()
                    # Refresh metrics again after commitment update
                    QTimer.singleShot(50, lambda: (
                        self.parent_dashboard.refresh_metrics_cards_main() if hasattr(self.parent_dashboard, 'refresh_metrics_cards_main') else None,
                        self.parent_dashboard.metrics_carousel.refresh_metrics_cards() if hasattr(self.parent_dashboard, 'metrics_carousel') else None
                    ))
                    
                # Force another refresh after transaction to ensure UI syncs
                # This is especially important for simulated transactions to update available balance
                QTimer.singleShot(100, lambda: (
                    self.parent_dashboard.refresh_metrics_cards_main() if hasattr(self.parent_dashboard, 'refresh_metrics_cards_main') else None,
                    self.parent_dashboard.metrics_carousel.refresh_metrics_cards() if hasattr(self.parent_dashboard, 'metrics_carousel') else None
                ))
                
                # Additional refresh for savings transfers to ensure savings balance updates
                if is_savings:
                    QTimer.singleShot(200, lambda: (
                        self.parent_dashboard.refresh_metrics_cards_main() if hasattr(self.parent_dashboard, 'refresh_metrics_cards_main') else None,
                        self.parent_dashboard.metrics_carousel.refresh_metrics_cards() if hasattr(self.parent_dashboard, 'metrics_carousel') else None
                    ))
                
                # CRITICAL: One more refresh specifically for simulated transactions
                # This ensures available balance updates even for simulated transactions
                QTimer.singleShot(300, lambda: (
                    self.parent_dashboard.refresh_metrics_cards_main() if hasattr(self.parent_dashboard, 'refresh_metrics_cards_main') else None,
                    self.parent_dashboard.metrics_carousel.refresh_metrics_cards() if hasattr(self.parent_dashboard, 'metrics_carousel') else None
                ))
            
            # Emit signal
            self.transaction_saved.emit()
            
            # Wait 3 seconds to simulate real transaction wait time, then hide processing screen and show confirmation
            bank_name = account_row['bank_name'] if 'bank_name' in account_row.keys() and account_row['bank_name'] else 'Account'
            QTimer.singleShot(3000, lambda: (
                self.hide_processing_screen(),
                self.show_confirmation(transaction_ref, amt, bank_name, transfer_id)
            ))
            
            # Navigate back to dashboard after delay (Test Case 3 requirement)
            # This ensures user returns to dashboard and sees updated balances AND recent transactions
            QTimer.singleShot(2000, lambda: (
                self.parent_dashboard.show_dashboard() if self.parent_dashboard else None,
                self.parent_dashboard.refresh_dashboard() if self.parent_dashboard else None,
                # Explicitly refresh metrics cards to update price after commitments and available balance
                self.parent_dashboard.refresh_metrics_cards_main() if (self.parent_dashboard and hasattr(self.parent_dashboard, 'refresh_metrics_cards_main')) else None,
                self.parent_dashboard.metrics_carousel.refresh_metrics_cards() if (self.parent_dashboard and hasattr(self.parent_dashboard, 'metrics_carousel')) else None,
                # CRITICAL: Refresh recent transactions to show the new transaction
                self.parent_dashboard.refresh_recent_transactions() if (self.parent_dashboard and hasattr(self.parent_dashboard, 'refresh_recent_transactions')) else None
            ))
            
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid amount")
        except Exception as e:
            self.hide_processing_screen()
            QMessageBox.critical(self, "Transaction Failed", f"Error processing transaction: {str(e)}")
    
    def show_processing_screen(self, amount):
        """Show banking-style processing screen"""
        if not hasattr(self, 'processing_widget'):
            self.processing_widget = QFrame(self)
            self.processing_widget.setStyleSheet("""
                QFrame {
                    background: rgba(0, 0, 0, 200);
                    border-radius: 16px;
                }
            """)
            processing_layout = QVBoxLayout(self.processing_widget)
            processing_layout.setAlignment(Qt.AlignCenter)
            
            # Processing label
            processing_label = QLabel("Processing Transaction...")
            processing_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
            processing_label.setStyleSheet("color: white; margin-bottom: 20px;")
            processing_label.setAlignment(Qt.AlignCenter)
            processing_layout.addWidget(processing_label)
            
            # Progress bar
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 0)  # Indeterminate
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 2px solid white;
                    border-radius: 8px;
                    height: 30px;
                    background: rgba(255, 255, 255, 0.2);
                }
                QProgressBar::chunk {
                    background: %s;
                    border-radius: 6px;
                }
            """ % PennyColors.ACCENT)
            processing_layout.addWidget(self.progress_bar)
            
            # Amount label
            amount_label = QLabel(f"${amount:,.2f}")
            amount_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
            amount_label.setStyleSheet("color: white; margin-top: 20px;")
            amount_label.setAlignment(Qt.AlignCenter)
            processing_layout.addWidget(amount_label)
        
        self.processing_widget.setGeometry(self.rect())
        self.processing_widget.show()
    
    def hide_processing_screen(self):
        """Hide processing screen"""
        if hasattr(self, 'processing_widget'):
            self.processing_widget.hide()
    
    def show_confirmation(self, ref, amount, bank_name, transfer_id=None):
        """Show banking-style transaction confirmation with app color scheme"""
        msg = QMessageBox(self)
        msg.setWindowTitle("✅ Transaction Successful")
        msg.setIcon(QMessageBox.Information)
        
        # Apply app color scheme styling to the message box
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {PennyColors.SURFACE};
                color: {PennyColors.TEXT_PRIMARY};
                font-family: 'Segoe UI', system-ui, sans-serif;
            }}
            QMessageBox QLabel {{
                color: {PennyColors.TEXT_PRIMARY};
                font-family: 'Segoe UI', system-ui, sans-serif;
            }}
            QMessageBox QPushButton {{
                background-color: {PennyColors.PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 24px;
                font-weight: 600;
                font-size: 14px;
                min-width: 80px;
            }}
            QMessageBox QPushButton:hover {{
                    background-color: {PennyColors.PRIMARY};
            }}
            QMessageBox QPushButton:pressed {{
                    background-color: {PennyColors.PRIMARY};
            }}
        """)
        
        # Use app color scheme in HTML content
        confirmation_text = f"""
        <div style='font-family: "Segoe UI", system-ui, sans-serif;'>
        <h3 style='color: {PennyColors.SUCCESS}; font-weight: 600; margin-bottom: 12px;'>Transaction Confirmed</h3>
        <p style='color: {PennyColors.TEXT_PRIMARY}; margin: 6px 0;'><b>Reference:</b> <span style='color: {PennyColors.TEXT_PRIMARY};'>{ref}</span></p>
        <p style='color: {PennyColors.TEXT_PRIMARY}; margin: 6px 0;'><b>Amount:</b> <span style='color: {PennyColors.TEXT_PRIMARY};'>${amount:,.2f}</span></p>
        <p style='color: {PennyColors.TEXT_PRIMARY}; margin: 6px 0;'><b>From:</b> <span style='color: {PennyColors.TEXT_PRIMARY};'>{bank_name}</span></p>
        """
        
        if transfer_id:
            confirmation_text += f"<p style='color: {PennyColors.TEXT_PRIMARY}; margin: 6px 0;'><b>Transfer ID:</b> <span style='color: {PennyColors.TEXT_PRIMARY};'>{transfer_id}</span></p>"
            confirmation_text += f"<p style='color: {PennyColors.TEXT_PRIMARY}; margin: 6px 0;'><b>Status:</b> <span style='color: {PennyColors.SUCCESS};'>Processing</span></p>"
        
        confirmation_text += f"""
        <p style='margin-top: 15px; font-size: 11px; color: {PennyColors.TEXT_SECONDARY};'>
        You will receive a confirmation email shortly.
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
                    padding: 8px 24px;
                    font-weight: 600;
                    font-size: 14px;
                    min-width: 80px;
                }}
                QPushButton:hover {{
                        background-color: {PennyColors.PRIMARY};
                }}
                QPushButton:pressed {{
                        background-color: {PennyColors.PRIMARY};
                }}
            """)
        
        msg.exec_()

    # View 2: Transaction Simulator
    def init_categories_view(self):
        """Initialize transaction simulator view (replaces old categories view)"""
        import random
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel(" Developer: Transaction Simulator")
        header.setFont(QFont("Segoe UI", 18, QFont.Bold))
        header.setStyleSheet(f"color: {PennyColors.TEXT_PRIMARY}; margin-bottom: 10px;")
        layout.addWidget(header)
        
        info_label = QLabel(
            "<b>For Developers Only:</b> Simulate how companies (like Apple, Netflix, Spotify) debit from accounts. "
            "This helps test how PennyWise will respond when real transactions occur. "
            "Transactions will appear in the history and trigger Smart Detect and commitment matching."
        )
        info_label.setStyleSheet(
            f"color: {PennyColors.TEXT_SECONDARY}; font-size: 12px; margin-bottom: 15px; "
            f"background-color: {PennyColors.PENNY_VOICE}; padding: 12px; border-radius: 8px; "
            f"border-left: 4px solid {PennyColors.WARNING};"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Account selection
        account_label = QLabel("Select Account:")
        account_label.setStyleSheet(f"color: {PennyColors.TEXT_PRIMARY}; font-weight: 600; margin-top: 10px;")
        layout.addWidget(account_label)
        
        self.sim_account_input = QComboBox()
        self.sim_account_input.setFixedHeight(40)
        layout.addWidget(self.sim_account_input)
        
        # Load accounts
        self.load_sim_accounts()
        
        # Custom transaction section
        custom_label = QLabel("Simulate Transaction:")
        custom_label.setStyleSheet(f"color: {PennyColors.TEXT_PRIMARY}; font-weight: 600; margin-top: 15px;")
        layout.addWidget(custom_label)
        
        # Custom merchant name
        merchant_name_layout = QHBoxLayout()
        merchant_name_label = QLabel("Merchant Name:")
        merchant_name_label.setFixedWidth(120)
        merchant_name_layout.addWidget(merchant_name_label)
        self.sim_merchant_input = QLineEdit()
        self.sim_merchant_input.setPlaceholderText("e.g., Local Cafe, Emu Gym, etc.")
        merchant_name_layout.addWidget(self.sim_merchant_input)
        layout.addLayout(merchant_name_layout)
        
        # Custom amount
        amount_layout = QHBoxLayout()
        amount_label = QLabel("Amount:")
        amount_label.setFixedWidth(120)
        amount_layout.addWidget(amount_label)
        self.sim_amount_input = QLineEdit()
        self.sim_amount_input.setPlaceholderText("e.g., 25.50")
        amount_layout.addWidget(self.sim_amount_input)
        layout.addLayout(amount_layout)
        
        # Simulate custom button
        simulate_custom_btn = QPushButton("Simulate Custom Transaction")
        simulate_custom_btn.setFixedHeight(45)
        simulate_custom_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PennyColors.PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                margin-top: 10px;
            }}
            QPushButton:hover {{
                background-color: {PennyColors.PRIMARY};
            }}
        """)
        simulate_custom_btn.clicked.connect(self.simulate_custom_transaction)
        layout.addWidget(simulate_custom_btn)
        
        layout.addStretch()
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        content = QWidget()
        content.setLayout(layout)
        scroll.setWidget(content)
        
        self.categories_view = scroll
    
    def load_sim_accounts(self):
        """Load accounts for simulation"""
        rows = fetch_all("SELECT id, account_id, bank_name, account_type, plaid_token FROM accounts WHERE user_id = ?", (self.user_id,))
        self.sim_account_input.clear()
        for r in rows:
            # Handle sqlite3.Row object - use bracket notation
            try:
                bank_name = r["bank_name"] if r["bank_name"] else "Unknown Bank"
            except (KeyError, TypeError):
                bank_name = "Unknown Bank"
            
            try:
                account_type = r["account_type"] if r["account_type"] else "account"
            except (KeyError, TypeError):
                account_type = "account"
            
            display_name = f"{bank_name} ({account_type})"
            # Store tuple: (id, plaid_token, account_id)
            try:
                plaid_token = r["plaid_token"] if "plaid_token" in r.keys() else None
            except:
                plaid_token = None
            
            try:
                account_id_val = r["account_id"] if "account_id" in r.keys() else None
            except:
                account_id_val = None
            
            self.sim_account_input.addItem(display_name, (r["id"], plaid_token, account_id_val))
    
    def generate_reference_number(self):
        """Generate a random reference number"""
        import random
        import string
        # Generate random alphanumeric reference: e.g., "REF-AB3X9K2M"
        chars = string.ascii_uppercase + string.digits
        ref = ''.join(random.choice(chars) for _ in range(8))
        return f"REF-{ref}"
    
    
    def simulate_custom_transaction(self):
        """Simulate a custom transaction"""
        merchant_name = self.sim_merchant_input.text().strip()
        if not merchant_name:
            QMessageBox.warning(self, "Missing Name", "Please enter a merchant name")
            return
        
        try:
            amount = float(self.sim_amount_input.text())
            if amount <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Invalid Amount", "Please enter a valid amount greater than 0")
            return
        
        # Get selected account
        account_data = self.sim_account_input.currentData()
        if not account_data:
            QMessageBox.warning(self, "No Account", "Please select an account first")
            return
        
        account_id, plaid_token, plaid_account_id = account_data
        
        # Generate reference number
        ref_number = self.generate_reference_number()
        
        # Create transaction name with reference
        transaction_name = f"{merchant_name} - {ref_number}"
        
        self.process_simulation(account_id, plaid_account_id, transaction_name, amount, ref_number)
        
        # Clear inputs
        self.sim_merchant_input.clear()
        self.sim_amount_input.clear()
    
    def process_simulation(self, account_id, plaid_account_id, transaction_name, amount, ref_number):
        """Process the transaction simulation using Plaid"""
        try:
            from core.transactions import insert_plaid_transaction
            from datetime import datetime
            
            # Create transaction object (mimicking Plaid transaction format)
            txn = {
                "account_id": plaid_account_id or str(account_id),  # Use Plaid account_id if available
                "amount": float(amount),
                "date": datetime.now().date().isoformat(),
                "name": transaction_name,
                "merchant_name": transaction_name.split(" - ")[0]  # Extract merchant name
            }
            
            # Insert transaction using Plaid transaction insertion (which handles Smart Detect)
            inserted_id = insert_plaid_transaction(self.user_id, account_id, txn)
            
            if inserted_id:
                # Show success message
                QMessageBox.information(
                    self, "Transaction Simulated",
                    f"✅ Transaction simulated successfully!\n\n"
                    f"Merchant: {transaction_name.split(' - ')[0]}\n"
                    f"Amount: ${amount:.2f}\n"
                    f"Reference: {ref_number}\n\n"
                    f"The transaction will appear in your recent activity."
                )
                
                # IMMEDIATELY refresh dashboard to update balance, transactions, and commitments
                if self.parent_dashboard:
                    self.parent_dashboard.refresh_dashboard()
                    # Explicitly refresh recent transactions to ensure simulated transaction appears
                    if hasattr(self.parent_dashboard, 'refresh_recent_transactions'):
                        self.parent_dashboard.refresh_recent_transactions()
                    # Force refresh metrics cards to update balance immediately
                    if hasattr(self.parent_dashboard, 'metrics_carousel'):
                        self.parent_dashboard.metrics_carousel.refresh_metrics_cards()
                
                # Emit signal
                self.transaction_saved.emit()
            else:
                QMessageBox.warning(self, "Error", "Failed to simulate transaction")
                # Still refresh dashboard even on error
                if self.parent_dashboard:
                    self.parent_dashboard.refresh_dashboard()
                
        except Exception as e:
            QMessageBox.critical(self, "Simulation Error", f"Error simulating transaction: {str(e)}")
            import traceback
            traceback.print_exc()
