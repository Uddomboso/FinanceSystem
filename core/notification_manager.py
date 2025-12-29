"""
Smart Alerts & Notifications Manager for PennyWise
Centralized commitment-related notifications without UI dependencies
"""

from PyQt5.QtCore import QObject, pyqtSignal
from datetime import datetime, date, timedelta
from database.db_manager import fetch_all, fetch_one, execute_query
from core.logger import logger


class NotificationManager(QObject):
    """
    Centralized notification manager for commitment-related alerts.
    
    Responsibilities:
    - Compute notification count only
    - Return plain Python data, no UI widgets
    - Detect commitment events (created, due soon, overdue, recurring, overspending)
    - No caching bugs - always recompute from DB state
    """
    
    # Optional signal for future real-time updates (not used in current implementation)
    notifications_changed = pyqtSignal(int)
    
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self._notifications = []
        self._unread_count = 0
    
    def recompute(self):
        """
        Recompute all notifications from current database state.
        This is the main entry point that should be called when:
        - A commitment is saved
        - A commitment is marked as paid
        - Dashboard loads data
        """
        try:
            self._notifications = self._compute_all_notifications()
            self._unread_count = len(self._notifications)
            logger.info(f"[NotificationManager] Recomputed {self._unread_count} notifications for user {self.user_id}")
            # Emit signal for potential future real-time updates
            self.notifications_changed.emit(self._unread_count)
        except Exception as e:
            logger.error(f"[NotificationManager] Error recomputing notifications: {e}")
            self._notifications = []
            self._unread_count = 0
            self.notifications_changed.emit(0)
    
    def get_unread_count(self):
        """Return the number of active notifications"""
        return self._unread_count
    
    def get_active_notifications(self):
        """Return list of all active notification dictionaries"""
        return self._notifications.copy()
    
    def _compute_all_notifications(self):
        """Compute all notifications from database state"""
        notifications = []
        today = date.today()
        
        # Get all commitments with their details
        commitments = fetch_all("""
            SELECT cc.*, c.category_name, c.color,
                   COALESCE(cc.is_paid, 0) as is_paid
            FROM category_commitments cc
            LEFT JOIN categories c ON cc.category_id = c.category_id
            WHERE cc.user_id = ?
            ORDER BY COALESCE(cc.is_paid, 0) ASC, cc.amount DESC
        """, (self.user_id,))
        
        # Get current balance for overspending risk calculation
        price_after_commitments = self._get_price_after_commitments()
        
        for commitment in commitments:
            # Convert sqlite3.Row to dictionary
            commitment_dict = dict(commitment)
            is_paid = bool(commitment_dict.get('is_paid', 0))
            
            # Skip paid commitments - they should not have active notifications
            if is_paid:
                continue
            
            # Only one notification per commitment - priority: overdue > due_soon > recurring_reminder
            commitment_notification = None
            
            # 1. Check if overdue (highest priority)
            overdue_notification = self._check_overdue(commitment_dict, today)
            if overdue_notification:
                commitment_notification = overdue_notification
            else:
                # 2. Check if due soon (only if not overdue)
                due_soon_notification = self._check_due_soon(commitment_dict, today)
                if due_soon_notification:
                    commitment_notification = due_soon_notification
                else:
                    # 3. Recurring commitment reminder (lowest priority, only if not overdue or due soon)
                    recurring_notification = self._check_recurring_reminder(commitment_dict, today)
                    if recurring_notification:
                        commitment_notification = recurring_notification
            
            # Add only one notification per commitment
            if commitment_notification:
                notifications.append(commitment_notification)
        
        # 4. Overspending risk (price_after_commitments < 0)
        if price_after_commitments < 0:
            notifications.append({
                'type': 'overspending_risk',
                'title': 'Overspending Risk',
                'message': f'Balance after commitments is negative: ${price_after_commitments:.2f}',
                'severity': 'high',
                'commitment_id': None,
                'category_name': None
            })
        
        return notifications
    
    def _get_price_after_commitments(self):
        """Calculate price_after_commitments = total_balance - unpaid_commitments"""
        try:
            # Get checking balance (from Plaid or fallback)
            checking_balance = 0
            has_plaid_checking = False
            
            # Try Plaid first
            plaid_accounts = fetch_all("""
                SELECT account_id, plaid_token
                FROM accounts 
                WHERE user_id = ? 
                AND account_type = 'salary'
                AND is_primary = 1
                AND plaid_token IS NOT NULL
            """, (self.user_id,))
            
            if plaid_accounts:
                from core.plaid_api import get_account_balances
                has_plaid_checking = True
                for account in plaid_accounts:
                    try:
                        balances_data = get_account_balances(account["plaid_token"])
                        if "error" not in balances_data:
                            for acc_balance in balances_data.get("accounts", []):
                                if acc_balance["account_id"] == account["account_id"]:
                                    balance = acc_balance["balances"].get("available", 0) or 0
                                    checking_balance += balance
                    except Exception as e:
                        logger.error(f"Error fetching balance for account {account['account_id']}: {e}")
            
            # Fallback to transaction-based calculation
            if not has_plaid_checking or checking_balance == 0:
                balance_row = fetch_one("""
                    SELECT SUM(
                        CASE 
                            WHEN transaction_type = 'income' THEN amount 
                            WHEN transaction_type = 'expense' THEN -amount 
                            ELSE 0 
                        END
                    ) as balance
                    FROM transactions
                    WHERE user_id = ?
                """, (self.user_id,))
                checking_balance = balance_row["balance"] if balance_row and balance_row["balance"] is not None else 0
            
            # Get unpaid commitments
            unpaid_row = fetch_one("""
                SELECT COALESCE(SUM(amount), 0) AS total
                FROM category_commitments
                WHERE user_id = ? AND COALESCE(is_paid, 0) = 0
            """, (self.user_id,))
            unpaid_commitments = unpaid_row["total"] if unpaid_row and unpaid_row["total"] is not None else 0
            
            # Calculate price after commitments
            price_after_commitments = checking_balance - unpaid_commitments
            return price_after_commitments
            
        except Exception as e:
            logger.error(f"[NotificationManager] Error calculating price_after_commitments: {e}")
            return 0
    
    def _check_due_soon(self, commitment, today):
        """Check if commitment is due within 7 days"""
        try:
            due_day = commitment.get('due_day', 1)
            if not due_day or due_day < 1 or due_day > 31:
                return None
            
            # Calculate next due date
            current_month = today.month
            current_year = today.year
            
            # Handle case where due day is past current month's day
            if due_day < today.day:
                # Due next month
                if current_month == 12:
                    next_month = 1
                    next_year = current_year + 1
                else:
                    next_month = current_month + 1
                    next_year = current_year
            else:
                # Due this month
                next_month = current_month
                next_year = current_year
            
            # Create due date (handle months with fewer days)
            try:
                due_date = date(next_year, next_month, due_day)
            except ValueError:
                # Handle invalid dates (e.g., February 30)
                # Use last day of the month
                if next_month == 12:
                    next_month = 1
                    next_year += 1
                # Find last day of month
                import calendar
                last_day = calendar.monthrange(next_year, next_month)[1]
                due_date = date(next_year, next_month, last_day)
            
            # Check if due within 7 days
            days_until_due = (due_date - today).days
            if 0 <= days_until_due <= 7:
                return {
                    'type': 'due_soon',
                    'title': 'Payment Due Soon',
                    'message': f"{commitment.get('category_name', 'Commitment')} due in {days_until_due} days",
                    'severity': 'medium' if days_until_due > 3 else 'high',
                    'commitment_id': commitment.get('commitment_id'),
                    'category_name': commitment.get('category_name'),
                    'due_date': due_date.isoformat(),
                    'days_until_due': days_until_due
                }
            
            return None
            
        except Exception as e:
            logger.error(f"[NotificationManager] Error checking due soon: {e}")
            return None
    
    def _check_overdue(self, commitment, today):
        """Check if commitment is overdue"""
        try:
            due_day = commitment.get('due_day', 1)
            if not due_day or due_day < 1 or due_day > 31:
                return None
            
            # Calculate most recent due date (could be this month or last month)
            current_month = today.month
            current_year = today.year
            
            # If today's day is past the due day, the commitment was due this month
            if today.day > due_day:
                due_month = current_month
                due_year = current_year
            else:
                # Due last month
                if current_month == 1:
                    due_month = 12
                    due_year = current_year - 1
                else:
                    due_month = current_month - 1
                    due_year = current_year
            
            # Create due date (handle months with fewer days)
            try:
                due_date = date(due_year, due_month, due_day)
            except ValueError:
                # Handle invalid dates
                import calendar
                last_day = calendar.monthrange(due_year, due_month)[1]
                due_date = date(due_year, due_month, min(due_day, last_day))
            
            # Check if overdue (due date is before today and commitment is unpaid)
            if due_date < today:
                days_overdue = (today - due_date).days
                return {
                    'type': 'overdue',
                    'title': 'Payment Overdue',
                    'message': f"{commitment.get('category_name', 'Commitment')} was due {days_overdue} days ago",
                    'severity': 'high',
                    'commitment_id': commitment.get('commitment_id'),
                    'category_name': commitment.get('category_name'),
                    'due_date': due_date.isoformat(),
                    'days_overdue': days_overdue
                }
            
            return None
            
        except Exception as e:
            logger.error(f"[NotificationManager] Error checking overdue: {e}")
            return None
    
    def _check_recurring_reminder(self, commitment, today):
        """Check if recurring commitment needs reminder (monthly cycle boundary)"""
        try:
            # For monthly commitments, remind on the 1st of each month if not paid
            if today.day == 1:
                return {
                    'type': 'recurring_reminder',
                    'title': 'Monthly Payment Reminder',
                    'message': f"{commitment.get('category_name', 'Commitment')} payment due this month",
                    'severity': 'medium',
                    'commitment_id': commitment.get('commitment_id'),
                    'category_name': commitment.get('category_name'),
                    'due_day': commitment.get('due_day')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"[NotificationManager] Error checking recurring reminder: {e}")
            return None
    
    def handle_signup_success(self, user_id, username):
        """
        Handle signup success notification.
        Inserts notification into database and shows toast.
        
        Args:
            user_id (int): The newly created user's ID
            username (str): The newly created user's username
        """
        try:
            # Update user_id if different (in case NotificationManager was created before user_id was known)
            self.user_id = user_id
            
            # Insert notification into database
            content = f"🎉 Welcome to PennyWise, {username}! Your account has been created successfully."
            execute_query("""
                INSERT INTO notifications (user_id, content, notification_type, is_sent, send_date)
                VALUES (?, ?, 'reminder', 0, date('now'))
            """, (user_id, content), commit=True)
            
            # Show toast notification
            from ui.toast_notification import ToastNotification
            ToastNotification.show("Account Created", f"Welcome {username}! Your account has been created successfully.")
            
            logger.info(f"[NotificationManager] Signup success notification handled for user {user_id}")
            
        except Exception as e:
            logger.error(f"[NotificationManager] Error handling signup success: {e}")