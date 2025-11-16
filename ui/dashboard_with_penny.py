"""
Dashboard template with Penny integration
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.components.penny_widget import PennyWidget
from ui.components.cards import CardWidget
from ui.components.metrics import MetricChip


class DashboardWithPenny(QWidget):
    """Main dashboard with Penny companion integration"""
    
    def __init__(self, user_id, username):
        super().__init__()
        self.user_id = user_id
        self.username = username
        
        self.setup_ui()
        self.setup_penny_connection()
        
    def setup_ui(self):
        """Setup the main dashboard layout"""
        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)
        
        # Header
        header = QLabel(f"Welcome back, {self.username}! 👋")
        header.setFont(QFont("Segoe UI", 28, QFont.Bold))
        header.setStyleSheet("color: #1F2937; background: transparent;")
        layout.addWidget(header)
        
        # Row 1: Quick Metrics
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(20)
        
        self.balance_metric = MetricChip("₦0", "Balance", "up")
        self.spending_metric = MetricChip("₦0", "Spending", "down") 
        self.savings_metric = MetricChip("₦0", "Savings", "up")
        self.goals_metric = MetricChip("0%", "Goals", "up")
        
        metrics_row.addWidget(self.balance_metric)
        metrics_row.addWidget(self.spending_metric)
        metrics_row.addWidget(self.savings_metric)
        metrics_row.addWidget(self.goals_metric)
        
        layout.addLayout(metrics_row)
        
        # Row 2: Penny's Corner
        penny_section = QLabel("🦉 Penny's Corner")
        penny_section.setFont(QFont("Segoe UI", 18, QFont.Bold))
        penny_section.setStyleSheet("color: #1F2937; margin-top: 10px;")
        layout.addWidget(penny_section)
        
        self.penny_widget = PennyWidget()
        layout.addWidget(self.penny_widget)
        
        # Row 3: Content Cards
        content_row = QHBoxLayout()
        content_row.setSpacing(20)
        
        # Left: Recent Activity
        self.activity_card = CardWidget("Recent Activity", "Your latest transactions")
        content_row.addWidget(self.activity_card, 1)  # stretch factor 1
        
        # Right: Quick Actions  
        self.actions_card = CardWidget("Quick Actions", "Manage your finances")
        content_row.addWidget(self.actions_card, 1)  # stretch factor 1
        
        layout.addLayout(content_row)
        
        container.setLayout(layout)
        scroll.setWidget(container)
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
        
    def setup_penny_connection(self):
        """Connect Penny to dashboard data"""
        # Connect Penny's signals to dashboard updates
        self.penny_widget.message_updated.connect(self.on_penny_message)
        
        # Initial Penny message
        self.penny_widget.update_message(
            f"💫 Hello {self.username}! I'm analyzing your finances...", 
            "friendly"
        )
        
    def on_penny_message(self, message, tone):
        """Handle new messages from Penny"""
        print(f"📢 Penny says ({tone}): {message}")
        
        # Update metrics based on Penny's tone
        if tone == "positive":
            self._animate_positive_metrics()
        elif tone == "warning":
            self._animate_warning_metrics()
            
    def _animate_positive_metrics(self):
        """Animate metrics for positive tone"""
        # This would update with real data in full implementation
        self.savings_metric.update_value("₦12.5K", "up")
        
    def _animate_warning_metrics(self):
        """Animate metrics for warning tone"""
        # This would update with real data in full implementation
        self.spending_metric.update_value("₦8.2K", "down")
        
    def update_dashboard_data(self, financial_data):
        """Update dashboard with real financial data"""
        # This would be called when new data is available
        balance = financial_data.get('balance', 0)
        spending = financial_data.get('spending', 0)
        savings = financial_data.get('savings', 0)
        
        self.balance_metric.update_value(f"₦{balance:,.0f}")
        self.spending_metric.update_value(f"₦{spending:,.0f}")
        self.savings_metric.update_value(f"₦{savings:,.0f}")
        
        # Update Penny with relevant insights
        if spending > balance * 0.7:
            self.penny_widget.update_message(
                "💡 Your spending is quite high this month. Let's review your budget!",
                "warning"
            )
        elif savings > balance * 0.2:
            self.penny_widget.update_message(
                "🎉 Excellent savings rate! You're building great habits!",
                "positive"
            )