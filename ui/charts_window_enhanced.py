# ui/charts_window_enhanced.py
from PyQt5.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QFrame,QScrollArea
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from database.db_manager import fetch_all
from core.logger import logger

try:
    from PyQt5.QtChart import QChart,QChartView,QPieSeries,QBarSeries,QBarSet,QBarCategoryAxis,QValueAxis
    from PyQt5.QtGui import QPainter

    QT_CHARTS_AVAILABLE = True
except ImportError:
    QT_CHARTS_AVAILABLE = False
    logger.warning("QtCharts not available, using fallback charts")


class AnimatedPieChart(QChartView if QT_CHARTS_AVAILABLE else QFrame):
    """Animated pie chart with smooth transitions"""

    def __init__(self,title="",parent=None):
        if QT_CHARTS_AVAILABLE:
            super().__init__(parent)
            self.chart = QChart()
            self.chart.setTitle(title)
            self.chart.setAnimationOptions(QChart.SeriesAnimations)
            self.chart.legend().setVisible(True)
            self.chart.legend().setAlignment(Qt.AlignBottom)
            self.chart.setBackgroundBrush(Qt.transparent)

            self.setChart(self.chart)
            self.setRenderHint(QPainter.Antialiasing)
            self.setStyleSheet("background: transparent; border: none;")
        else:
            super().__init__(parent)
            self.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #60A5FA, stop:0.2 #34D399, stop:0.4 #FBBF24,
                        stop:0.6 #F87171, stop:0.8 #A78BFA, stop:1 #2DD4BF);
                    border-radius: 12px;
                }
            """)
            layout = QVBoxLayout(self)
            label = QLabel("📊 Enhanced Charts\n(Install PyQtChart for animations)")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
            layout.addWidget(label)

    def update_data(self,data):
        """Update chart data with animation"""
        if not QT_CHARTS_AVAILABLE:
            return

        series = QPieSeries()
        series.setHoleSize(0.35)  # Donut style

        # Penny's chart colors
        colors = ["#60A5FA","#34D399","#FBBF24","#F87171","#A78BFA","#2DD4BF"]

        for i,(label,value) in enumerate(data):
            slice = series.append(label,value)
            if i < len(colors):
                slice.setColor(colors[i])
            slice.setLabelVisible(True)
            slice.setLabel(f"{label}: ${value:.0f}")

        self.chart.removeAllSeries()
        self.chart.addSeries(series)


class EnhancedChartsWindow(QWidget):
    """Modern charts window with animations - REPLACES your current charts_window.py"""

    def __init__(self,user_id):
        super().__init__()
        self.user_id = user_id
        self.setup_ui()
        self.load_chart_data()

    def setup_ui(self):
        """Setup the enhanced charts interface"""
        self.setWindowTitle("📊 Financial Analytics")
        self.setMinimumSize(1000,700)

        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30,30,30,30)
        layout.setSpacing(25)

        # Header
        header = QLabel("Financial Analytics Dashboard")
        header.setFont(QFont("Segoe UI",24,QFont.Bold))
        header.setStyleSheet("color: #1F2937; margin-bottom: 10px;")
        layout.addWidget(header)

        if not QT_CHARTS_AVAILABLE:
            warning_msg = QLabel("⚠️ For enhanced animated charts, install: pip install PyQtChart")
            warning_msg.setStyleSheet("""
                background: #FEF3C7; 
                color: #92400E; 
                padding: 12px; 
                border-radius: 8px; 
                border-left: 4px solid #F59E0B;
            """)
            warning_msg.setWordWrap(True)
            layout.addWidget(warning_msg)

        # Charts grid
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(20)

        # Left: Spending by Category (Pie)
        self.spending_pie = AnimatedPieChart("Spending by Category")
        spending_card = self.create_chart_card("🍔 Spending Distribution",self.spending_pie)
        charts_layout.addWidget(spending_card)

        # Right: Income vs Expenses (Pie)
        self.income_expense_pie = AnimatedPieChart("Income vs Expenses")
        income_card = self.create_chart_card("💰 Income vs Expenses",self.income_expense_pie)
        charts_layout.addWidget(income_card)

        layout.addLayout(charts_layout)

        # Bottom: Quick Metrics Row
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(15)

        self.top_category_metric = self.create_metric_card("🏆 Top Category","Loading...","#2563EB")
        self.avg_spending_metric = self.create_metric_card("💸 Average Spend","Loading...","#10B981")
        self.savings_rate_metric = self.create_metric_card("💰 Savings Rate","Loading...","#F59E0B")

        metrics_layout.addWidget(self.top_category_metric)
        metrics_layout.addWidget(self.avg_spending_metric)
        metrics_layout.addWidget(self.savings_rate_metric)

        layout.addLayout(metrics_layout)

        container.setLayout(layout)
        scroll.setWidget(container)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)

    def create_chart_card(self,title,chart_widget):
        """Create a styled card for charts"""
        card = QFrame()
        card.setProperty("class","card")
        card.setStyleSheet("""
            QFrame[class="card"] {
                background: #FFFFFF;
                border: 1px solid rgba(0, 0, 0, 0.06);
                border-radius: 16px;
                padding: 20px;
            }
        """)

        layout = QVBoxLayout(card)

        # Card header
        header = QLabel(title)
        header.setFont(QFont("Segoe UI",16,QFont.Bold))
        header.setStyleSheet("color: #1F2937; margin-bottom: 15px;")
        layout.addWidget(header)

        # Chart
        chart_widget.setMinimumHeight(300)
        layout.addWidget(chart_widget)

        return card

    def create_metric_card(self,title,value,color):
        """Create animated metric cards"""
        card = QFrame()
        card.setProperty("class","metric-chip")
        card.setFixedHeight(100)
        card.setStyleSheet(f"""
            QFrame[class="metric-chip"] {{
                background: #FFFFFF;
                border: 1px solid rgba(0, 0, 0, 0.08);
                border-radius: 16px;
                padding: 20px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(
            "color: #6B7280; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)

        return card

    def load_chart_data(self):
        """Load and animate chart data"""
        try:
            # Get spending by category
            category_data = fetch_all("""
                SELECT c.category_name, SUM(t.amount) as total
                FROM transactions t
                JOIN categories c ON t.category_id = c.category_id
                WHERE t.user_id = ? AND t.transaction_type = 'expense'
                GROUP BY c.category_name
                HAVING total > 0
                ORDER BY total DESC
                LIMIT 6
            """,(self.user_id,))

            if category_data:
                # Prepare pie chart data
                pie_data = [(cat['category_name'],cat['total']) for cat in category_data]
                self.spending_pie.update_data(pie_data)

                # Update top category metric
                top_cat = category_data[0]
                self.top_category_metric.layout().itemAt(1).widget().setText(
                    f"{top_cat['category_name']}\n${top_cat['total']:,.0f}"
                )

            # Get income vs expense data
            income_data = fetch_all("""
                SELECT SUM(amount) as total_income
                FROM transactions 
                WHERE user_id = ? AND transaction_type = 'income'
            """,(self.user_id,))

            expense_data = fetch_all("""
                SELECT SUM(amount) as total_expense
                FROM transactions 
                WHERE user_id = ? AND transaction_type = 'expense'
            """,(self.user_id,))

            if income_data and expense_data:
                total_income = income_data[0]['total_income'] or 0
                total_expense = expense_data[0]['total_expense'] or 0

                # Only show if we have meaningful data
                if total_income > 0 or total_expense > 0:
                    income_expense_data = [
                        ("Income",total_income),
                        ("Expenses",total_expense)
                    ]
                    self.income_expense_pie.update_data(income_expense_data)

                # Calculate savings rate
                if total_income > 0:
                    savings_rate = ((total_income - total_expense) / total_income) * 100
                    self.savings_rate_metric.layout().itemAt(1).widget().setText(
                        f"{savings_rate:.1f}%"
                    )

                # Calculate average monthly spending
                monthly_data = fetch_all("""
                    SELECT SUM(amount) as monthly_total
                    FROM transactions 
                    WHERE user_id = ? AND transaction_type = 'expense'
                    AND date >= date('now', '-30 days')
                """,(self.user_id,))

                if monthly_data:
                    avg_spend = monthly_data[0]['monthly_total'] or 0
                    self.avg_spending_metric.layout().itemAt(1).widget().setText(
                        f"${avg_spend:,.0f}"
                    )

        except Exception as e:
            logger.error(f"Error loading chart data: {e}")
            # Set fallback values
            self.top_category_metric.layout().itemAt(1).widget().setText("No data")
            self.avg_spending_metric.layout().itemAt(1).widget().setText("$0")
            self.savings_rate_metric.layout().itemAt(1).widget().setText("0%")