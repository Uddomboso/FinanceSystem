# ui/reports_page.py
"""
Enhanced Reports Page with Gamification and Bank Activity Charts
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea,
    QPushButton, QButtonGroup, QGridLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from database.db_manager import fetch_all, fetch_one
from core.badges_manager import BadgesManager
from assets.styles.penny_colors import PennyColors
import qtawesome as qta
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class ReportsPage(QWidget):
    """Enhanced Reports Page with charts and gamification"""
    
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.badges_manager = BadgesManager(user_id)
        self.chart_type = 'bar'  # Default: bar chart
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Setup the reports page UI"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {PennyColors.BACKGROUND}; }}")
        
        # Container widget
        container = QWidget()
        container.setStyleSheet(f"background: {PennyColors.BACKGROUND};")
        content_layout = QVBoxLayout(container)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(25)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Reports & Analytics")
        title.setFont(QFont("Segoe UI", 28, QFont.Bold))
        title.setStyleSheet(f"color: {PennyColors.TEXT_PRIMARY};")
        header_layout.addWidget(title)
        header_layout.addStretch()
        content_layout.addLayout(header_layout)
        
        # Bank Activity Chart Section
        chart_section = self.create_chart_section()
        content_layout.addWidget(chart_section)
        
        # Gamification Section
        gamification_section = self.create_gamification_section()
        content_layout.addWidget(gamification_section)
        
        content_layout.addStretch()
        
        container.setLayout(content_layout)
        scroll.setWidget(container)
        main_layout.addWidget(scroll)
    
    def create_chart_section(self):
        """Create bank activity chart section with chart type selector"""
        section_frame = QFrame()
        section_frame.setStyleSheet(f"""
            QFrame {{
                background: {PennyColors.SURFACE};
                border-radius: 16px;
                border: 1px solid #E5E7EB;
            }}
        """)
        
        section_layout = QVBoxLayout(section_frame)
        section_layout.setContentsMargins(24, 24, 24, 24)
        section_layout.setSpacing(16)
        
        # Section header
        header_layout = QHBoxLayout()
        title = QLabel("Bank Activity")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet(f"color: {PennyColors.TEXT_PRIMARY};")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Chart type selector
        chart_type_group = QButtonGroup()
        chart_type_layout = QHBoxLayout()
        chart_type_layout.setSpacing(8)
        
        self.bar_btn = QPushButton()
        self.bar_btn.setCheckable(True)
        self.bar_btn.setChecked(True)
        self.bar_btn.clicked.connect(lambda: self.change_chart_type('bar'))
        bar_icon = qta.icon('fa5s.chart-bar', color=PennyColors.TEXT_PRIMARY)
        self.bar_btn.setIcon(bar_icon)
        self.bar_btn.setToolTip("Bar Chart")
        self.bar_btn.setStyleSheet(f"""
            QPushButton {{
                background: {'#d6733a' if self.chart_type == 'bar' else PennyColors.SURFACE};
                color: {'white' if self.chart_type == 'bar' else PennyColors.TEXT_PRIMARY};
                border: 2px solid {'#d6733a' if self.chart_type == 'bar' else '#E5E7EB'};
                border-radius: 8px;
                padding: 8px 12px;
                min-width: 40px;
                min-height: 40px;
            }}
            QPushButton:hover {{
                background: {'#c56230' if self.chart_type == 'bar' else '#F3F4F6'};
            }}
        """)
        
        self.pie_btn = QPushButton()
        self.pie_btn.setCheckable(True)
        self.pie_btn.clicked.connect(lambda: self.change_chart_type('pie'))
        pie_icon = qta.icon('fa5s.chart-pie', color=PennyColors.TEXT_PRIMARY)
        self.pie_btn.setIcon(pie_icon)
        self.pie_btn.setToolTip("Pie Chart")
        self.pie_btn.setStyleSheet(f"""
            QPushButton {{
                background: {PennyColors.SURFACE};
                color: {PennyColors.TEXT_PRIMARY};
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                padding: 8px 12px;
                min-width: 40px;
                min-height: 40px;
            }}
            QPushButton:hover {{
                background: #F3F4F6;
            }}
        """)
        
        self.line_btn = QPushButton()
        self.line_btn.setCheckable(True)
        self.line_btn.clicked.connect(lambda: self.change_chart_type('line'))
        line_icon = qta.icon('fa5s.chart-line', color=PennyColors.TEXT_PRIMARY)
        self.line_btn.setIcon(line_icon)
        self.line_btn.setToolTip("Line Chart")
        self.line_btn.setStyleSheet(f"""
            QPushButton {{
                background: {PennyColors.SURFACE};
                color: {PennyColors.TEXT_PRIMARY};
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                padding: 8px 12px;
                min-width: 40px;
                min-height: 40px;
            }}
            QPushButton:hover {{
                background: #F3F4F6;
            }}
        """)
        
        chart_type_group.addButton(self.bar_btn)
        chart_type_group.addButton(self.pie_btn)
        chart_type_group.addButton(self.line_btn)
        
        chart_type_layout.addWidget(self.bar_btn)
        chart_type_layout.addWidget(self.pie_btn)
        chart_type_layout.addWidget(self.line_btn)
        header_layout.addLayout(chart_type_layout)
        
        section_layout.addLayout(header_layout)
        
        # Chart container
        self.chart_container = QFrame()
        self.chart_container.setStyleSheet(f"background: white; border-radius: 12px;")
        self.chart_container.setMinimumHeight(400)
        chart_container_layout = QVBoxLayout(self.chart_container)
        chart_container_layout.setContentsMargins(16, 16, 16, 16)
        
        self.chart_canvas = None
        section_layout.addWidget(self.chart_container)
        
        return section_frame
    
    def change_chart_type(self, chart_type):
        """Change the chart type and update display"""
        self.chart_type = chart_type
        
        # Update button styles
        self.bar_btn.setChecked(chart_type == 'bar')
        self.pie_btn.setChecked(chart_type == 'pie')
        self.line_btn.setChecked(chart_type == 'line')
        
        self.bar_btn.setStyleSheet(f"""
            QPushButton {{
                background: {'#d6733a' if chart_type == 'bar' else PennyColors.SURFACE};
                color: {'white' if chart_type == 'bar' else PennyColors.TEXT_PRIMARY};
                border: 2px solid {'#d6733a' if chart_type == 'bar' else '#E5E7EB'};
                border-radius: 8px;
                padding: 8px 12px;
                min-width: 40px;
                min-height: 40px;
            }}
            QPushButton:hover {{
                background: {'#c56230' if chart_type == 'bar' else '#F3F4F6'};
            }}
        """)
        
        self.pie_btn.setStyleSheet(f"""
            QPushButton {{
                background: {'#d6733a' if chart_type == 'pie' else PennyColors.SURFACE};
                color: {'white' if chart_type == 'pie' else PennyColors.TEXT_PRIMARY};
                border: 2px solid {'#d6733a' if chart_type == 'pie' else '#E5E7EB'};
                border-radius: 8px;
                padding: 8px 12px;
                min-width: 40px;
                min-height: 40px;
            }}
            QPushButton:hover {{
                background: {'#c56230' if chart_type == 'pie' else '#F3F4F6'};
            }}
        """)
        
        self.line_btn.setStyleSheet(f"""
            QPushButton {{
                background: {'#d6733a' if chart_type == 'line' else PennyColors.SURFACE};
                color: {'white' if chart_type == 'line' else PennyColors.TEXT_PRIMARY};
                border: 2px solid {'#d6733a' if chart_type == 'line' else '#E5E7EB'};
                border-radius: 8px;
                padding: 8px 12px;
                min-width: 40px;
                min-height: 40px;
            }}
            QPushButton:hover {{
                background: {'#c56230' if chart_type == 'line' else '#F3F4F6'};
            }}
        """)
        
        # Recreate chart
        self.create_chart()
    
    def create_chart(self):
        """Create the bank activity chart based on current chart type"""
        # Clear existing chart
        if self.chart_canvas:
            self.chart_canvas.deleteLater()
        
        # Get transaction data for last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        transactions = fetch_all("""
            SELECT 
                date(t.date) as day,
                SUM(CASE WHEN t.transaction_type = 'income' THEN t.amount ELSE 0 END) as income,
                SUM(CASE WHEN t.transaction_type = 'expense' THEN t.amount ELSE 0 END) as expense
            FROM transactions t
            WHERE t.user_id = ? 
            AND date(t.date) >= date('now', '-30 days')
            GROUP BY date(t.date)
            ORDER BY date(t.date)
        """, (self.user_id,))
        
        if not transactions:
            # Show empty state
            layout = self.chart_container.layout()
            empty_label = QLabel("No transaction data available")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet(f"color: {PennyColors.TEXT_SECONDARY}; font-size: 14px;")
            layout.addWidget(empty_label)
            return
        
        # Prepare data
        dates = []
        income_values = []
        expense_values = []
        
        for txn in transactions:
            dates.append(txn['day'])
            income_values.append(float(txn['income'] or 0))
            expense_values.append(float(txn['expense'] or 0))
        
        # Create matplotlib figure
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        if self.chart_type == 'bar':
            # Bar chart
            x = range(len(dates))
            width = 0.35
            ax.bar([i - width/2 for i in x], income_values, width, label='Income', color='#10B981', alpha=0.8)
            ax.bar([i + width/2 for i in x], expense_values, width, label='Expenses', color='#EF4444', alpha=0.8)
            ax.set_xlabel('Date')
            ax.set_ylabel('Amount ($)')
            ax.set_title('Bank Activity - Income vs Expenses (Last 30 Days)')
            ax.legend()
            ax.set_xticks(x)
            ax.set_xticklabels([d[-5:] if d else '' for d in dates], rotation=45, ha='right')
            
        elif self.chart_type == 'pie':
            # Pie chart - total income vs total expenses
            total_income = sum(income_values)
            total_expense = sum(expense_values)
            
            if total_income > 0 or total_expense > 0:
                labels = []
                sizes = []
                colors = []
                
                if total_income > 0:
                    labels.append('Income')
                    sizes.append(total_income)
                    colors.append('#10B981')
                
                if total_expense > 0:
                    labels.append('Expenses')
                    sizes.append(total_expense)
                    colors.append('#EF4444')
                
                ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
                ax.set_title('Bank Activity - Income vs Expenses (Last 30 Days)')
            else:
                ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)
                
        elif self.chart_type == 'line':
            # Line chart
            x = range(len(dates))
            ax.plot(x, income_values, marker='o', label='Income', color='#10B981', linewidth=2)
            ax.plot(x, expense_values, marker='s', label='Expenses', color='#EF4444', linewidth=2)
            ax.set_xlabel('Date')
            ax.set_ylabel('Amount ($)')
            ax.set_title('Bank Activity - Income vs Expenses Trend (Last 30 Days)')
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.set_xticks(x)
            ax.set_xticklabels([d[-5:] if d else '' for d in dates], rotation=45, ha='right')
        
        fig.tight_layout()
        
        # Create canvas
        self.chart_canvas = FigureCanvas(fig)
        layout = self.chart_container.layout()
        layout.addWidget(self.chart_canvas)
    
    def create_gamification_section(self):
        """Create gamification section with badges"""
        section_frame = QFrame()
        section_frame.setStyleSheet(f"""
            QFrame {{
                background: {PennyColors.SURFACE};
                border-radius: 16px;
                border: 1px solid #E5E7EB;
            }}
        """)
        
        section_layout = QVBoxLayout(section_frame)
        section_layout.setContentsMargins(24, 24, 24, 24)
        section_layout.setSpacing(16)
        
        # Section header
        header_layout = QHBoxLayout()
        title = QLabel("Achievements")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet(f"color: {PennyColors.TEXT_PRIMARY};")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Badge count
        earned_badges = self.badges_manager.get_earned_badges()
        total_badges = len(self.badges_manager.badge_definitions)
        badge_count_label = QLabel(f"{len(earned_badges)}/{total_badges}")
        badge_count_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        badge_count_label.setStyleSheet(f"""
            background: #d6733a;
            color: white;
            padding: 6px 16px;
            border-radius: 12px;
        """)
        header_layout.addWidget(badge_count_label)
        section_layout.addLayout(header_layout)
        
        # Badges grid
        badges_data = self.badges_manager.get_badges_with_progress()
        badges_grid = QGridLayout()
        badges_grid.setSpacing(16)
        
        for i, badge in enumerate(badges_data):
            row = i // 4
            col = i % 4
            badge_widget = self.create_badge_card(badge)
            badges_grid.addWidget(badge_widget, row, col)
        
        section_layout.addLayout(badges_grid)
        
        return section_frame
    
    def create_badge_card(self, badge_data):
        """Create a badge card with FontAwesome icons"""
        card = QFrame()
        card.setFixedSize(150, 180)
        card.setStyleSheet(f"""
            QFrame {{
                background: {'rgba(214, 115, 58, 0.1)' if badge_data['earned'] else 'white'};
                border: 2px solid {'#d6733a' if badge_data['earned'] else '#E5E7EB'};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)
        
        # Badge icon (using FontAwesome)
        icon_name = self.get_badge_icon(badge_data['id'])
        icon_widget = QLabel()
        icon_widget.setAlignment(Qt.AlignCenter)
        
        if badge_data['earned']:
            icon = qta.icon(icon_name, color=badge_data['color'])
            pixmap = icon.pixmap(64, 64)
            icon_widget.setPixmap(pixmap)
        else:
            icon = qta.icon(icon_name, color='#9CA3AF')
            pixmap = icon.pixmap(64, 64)
            icon_widget.setPixmap(pixmap)
        
        layout.addWidget(icon_widget)
        
        # Badge name (remove emoji if present)
        name_text = badge_data['name']
        # Remove emoji characters
        name_text = ''.join(char for char in name_text if ord(char) < 128).strip()
        name_label = QLabel(name_text)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        name_label.setStyleSheet(f"""
            color: {PennyColors.TEXT_PRIMARY if badge_data['earned'] else PennyColors.TEXT_SECONDARY};
        """)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        
        # Description
        desc_label = QLabel(badge_data['description'])
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setFont(QFont("Segoe UI", 9))
        desc_label.setStyleSheet(f"color: {PennyColors.TEXT_SECONDARY};")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Progress bar for unearned badges
        if not badge_data['earned']:
            progress_bar = QPushButton()  # Using button as progress bar for styling
            progress_bar.setFixedHeight(4)
            progress_bar.setEnabled(False)
            progress_bar.setStyleSheet(f"""
                QPushButton {{
                    background: #E5E7EB;
                    border: none;
                    border-radius: 2px;
                }}
            """)
            layout.addWidget(progress_bar)
        
        return card
    
    def get_badge_icon(self, badge_id):
        """Get FontAwesome icon name for badge"""
        icon_map = {
            'steady_planner': 'fa5s.leaf',
            'smart_saver': 'fa5s.coins',
            'quick_optimizer': 'fa5s.bolt',
            'goal_crusher': 'fa5s.bullseye',
            'balance_master': 'fa5s.star',
            'early_riser': 'fa5s.sun',
            'budget_ninja': 'fa5s.user-secret'
        }
        return icon_map.get(badge_id, 'fa5s.trophy')
    
    def load_data(self):
        """Load chart and badge data"""
        self.create_chart()
    
    def refresh(self):
        """Refresh all data"""
        self.load_data()


