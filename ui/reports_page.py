# ui/reports_page.py
"""
Enhanced Reports Page with Gamification and Bank Activity Charts
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QPushButton, QButtonGroup
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from database.db_manager import fetch_all
from assets.styles.penny_colors import PennyColors
from core import theme_manager
import qtawesome as qta
from datetime import timedelta, date
import calendar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QComboBox
import sip

class ReportsPage(QWidget):
    """Enhanced Reports Page with charts and gamification"""
    
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.chart_type = 'bar'  # Default: bar chart
        self.range_mode = "30d"
        self._palette = PennyColors.get_palette(theme_manager.current_theme)
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Setup the reports page UI"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        
        # Container widget
        self.container = QWidget()
        content_layout = QVBoxLayout(self.container)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(25)
        
        # Header
        header_layout = QHBoxLayout()
        self.title_main = QLabel("Reports & Analytics")
        self.title_main.setFont(QFont("Segoe UI", 28, QFont.Bold))
        header_layout.addWidget(self.title_main)
        header_layout.addStretch()
        content_layout.addLayout(header_layout)
        
        # Bank Activity Chart Section (flat layout, no cards)
        chart_section = self.create_chart_section()
        content_layout.addWidget(chart_section)
        content_layout.addStretch()
        
        self.container.setLayout(content_layout)
        self.scroll.setWidget(self.container)
        main_layout.addWidget(self.scroll)
        self._apply_styles()
    
    def create_chart_section(self):
        """Create bank activity chart section with chart type selector"""
        section_frame = QWidget()
        section_layout = QVBoxLayout(section_frame)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(12)
        
        # Section header
        header_layout = QHBoxLayout()
        self.chart_title = QLabel("Bank Activity")
        self.chart_title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        header_layout.addWidget(self.chart_title)
        header_layout.addStretch()

        # Chart type selector
        chart_type_group = QButtonGroup()
        chart_type_layout = QHBoxLayout()
        chart_type_layout.setSpacing(8)
        
        self.bar_btn = QPushButton()
        self.bar_btn.setCheckable(True)
        self.bar_btn.setChecked(True)
        self.bar_btn.clicked.connect(lambda: self.change_chart_type('bar'))
        self.bar_btn.setToolTip("Bar Chart")
        
        self.pie_btn = QPushButton()
        self.pie_btn.setCheckable(True)
        self.pie_btn.clicked.connect(lambda: self.change_chart_type('pie'))
        self.pie_btn.setToolTip("Pie Chart")
        
        self.line_btn = QPushButton()
        self.line_btn.setCheckable(True)
        self.line_btn.clicked.connect(lambda: self.change_chart_type('line'))
        self.line_btn.setToolTip("Line Chart")
        
        chart_type_group.addButton(self.bar_btn)
        chart_type_group.addButton(self.pie_btn)
        chart_type_group.addButton(self.line_btn)
        
        chart_type_layout.addWidget(self.bar_btn)
        chart_type_layout.addWidget(self.pie_btn)
        chart_type_layout.addWidget(self.line_btn)
        header_layout.addLayout(chart_type_layout)

        # Range selector (last 30 days, year-to-date, or specific month in last 12)
        self.range_combo = QComboBox()
        self.range_combo.setFont(QFont("Segoe UI", 11))
        self.range_options = self.build_range_options()
        for label, value in self.range_options:
            self.range_combo.addItem(label, value)
        self.range_combo.currentIndexChanged.connect(self.change_range_mode)
        header_layout.addWidget(self.range_combo)
        
        section_layout.addLayout(header_layout)
        
        # Chart container
        self.chart_container = QWidget()
        self.chart_container.setMinimumHeight(400)
        chart_container_layout = QVBoxLayout(self.chart_container)
        chart_container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.chart_canvas = None
        section_layout.addWidget(self.chart_container)
        
        # Apply initial palette styles
        self._apply_button_styles()
        return section_frame

    def change_range_mode(self, index):
        """Handle range selection change and refresh chart."""
        if index < 0:
            return
        value = self.range_combo.itemData(index)
        self.range_mode = value or "30d"
        self.create_chart()

    def build_range_options(self):
        """Build time-range options: last 30d, year-to-date, and past 12 months."""
        options = [("Last 30 days", "30d"), ("Year to date", "year")]
        today = date.today()
        for i in range(12):
            month_date = (today.replace(day=1) - timedelta(days=30 * i))
            year = month_date.year
            month = month_date.month
            label = month_date.strftime("%b %Y")
            value = f"month:{year:04d}-{month:02d}"
            options.append((label, value))
        return options
    
    def change_chart_type(self, chart_type):
        """Change the chart type and update display"""
        self.chart_type = chart_type
        
        # Update button styles
        self.bar_btn.setChecked(chart_type == 'bar')
        self.pie_btn.setChecked(chart_type == 'pie')
        self.line_btn.setChecked(chart_type == 'line')
        self._apply_button_styles()
        
        # Recreate chart
        self.create_chart()
    
    def create_chart(self):
        """Create the bank activity chart based on current chart type"""
        # Clear existing chart
        layout = self.chart_container.layout()
        if layout:
            # Remove any existing widgets safely
            while layout.count():
                item = layout.takeAt(0)
                w = item.widget()
                if w and not sip.isdeleted(w):
                    w.setParent(None)
                    w.deleteLater()
        self.chart_canvas = None
        self._apply_styles()
        p = self._palette
        
        # Resolve date range based on selection
        end_date = date.today()
        if self.range_mode == "year":
            start_date = date(end_date.year, 1, 1)
            title_suffix = f"Year to Date {end_date.year}"
        elif self.range_mode.startswith("month:"):
            _, ym = self.range_mode.split(":")
            year, month = map(int, ym.split("-"))
            start_date = date(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            end_date = date(year, month, last_day)
            title_suffix = start_date.strftime("%B %Y")
        else:  # default 30d
            start_date = end_date - timedelta(days=30)
            title_suffix = "Last 30 Days"
        
        transactions = fetch_all("""
            SELECT 
                date(t.date) as day,
                SUM(CASE WHEN t.amount >= 0 THEN t.amount ELSE 0 END) as income,
                SUM(CASE WHEN t.amount < 0 THEN ABS(t.amount) ELSE 0 END) as expense
            FROM transactions t
            WHERE t.user_id = ? 
              AND date(t.date) BETWEEN ? AND ?
            GROUP BY date(t.date)
            ORDER BY date(t.date)
        """, (self.user_id, start_date.isoformat(), end_date.isoformat()))
        
        if not transactions:
            # Show empty state
            layout = self.chart_container.layout()
            empty_label = QLabel("No transaction data available")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet(f"color: {p['text_secondary']}; font-size: 14px;")
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
        fig = Figure(figsize=(10, 6), facecolor=p["background"])
        ax = fig.add_subplot(111, facecolor=p["surface"])
        income_color = p.get("success", "#10B981")
        expense_color = p.get("error", "#EF4444")
        border_color = p.get("border", "#E5E7EB")
        text_color = p.get("text_primary", "#1F2937")
        secondary_text = p.get("text_secondary", "#6B7280")  # kept for potential future use
        
        if self.chart_type == 'bar':
            # Bar chart
            x = range(len(dates))
            width = 0.35
            ax.bar([i - width/2 for i in x], income_values, width, label='Income', color=income_color, alpha=0.85)
            ax.bar([i + width/2 for i in x], expense_values, width, label='Expenses', color=expense_color, alpha=0.85)
            ax.set_xlabel('Date')
            ax.set_ylabel('Amount ($)')
            ax.set_title(f'Bank Activity - Income vs Expenses ({title_suffix})')
            legend = ax.legend()
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
                    colors.append(income_color)
                
                if total_expense > 0:
                    labels.append('Expenses')
                    sizes.append(total_expense)
                    colors.append(expense_color)
                
                wedges, texts, autotexts = ax.pie(
                    sizes,
                    labels=labels,
                    colors=colors,
                    autopct='%1.1f%%',
                    startangle=90,
                    textprops={'color': text_color}
                )
                for t in autotexts:
                    t.set_color(text_color)
                ax.set_title(f'Bank Activity - Income vs Expenses ({title_suffix})')
            else:
                ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes, color=text_color)
                
        elif self.chart_type == 'line':
            # Line chart
            x = range(len(dates))
            ax.plot(x, income_values, marker='o', label='Income', color=income_color, linewidth=2)
            ax.plot(x, expense_values, marker='s', label='Expenses', color=expense_color, linewidth=2)
            ax.set_xlabel('Date')
            ax.set_ylabel('Amount ($)')
            ax.set_title(f'Bank Activity - Income vs Expenses Trend ({title_suffix})')
            legend = ax.legend()
            ax.grid(True, alpha=0.3, color=border_color)
            ax.set_xticks(x)
            ax.set_xticklabels([d[-5:] if d else '' for d in dates], rotation=45, ha='right')
        
        # Apply palette to axes text and spines
        for spine in ax.spines.values():
            spine.set_color(border_color)
        ax.tick_params(colors=text_color)
        ax.yaxis.label.set_color(text_color)
        ax.xaxis.label.set_color(text_color)
        ax.title.set_color(text_color)
        if 'legend' in locals() and legend:
            for text in legend.get_texts():
                text.set_color(text_color)
            legend.get_frame().set_facecolor(p["surface"])
            legend.get_frame().set_edgecolor(border_color)
        fig.tight_layout()
        
        # Create canvas
        self.chart_canvas = FigureCanvas(fig)
        layout = self.chart_container.layout()
        layout.addWidget(self.chart_canvas)
    
    def load_data(self):
        """Load chart and badge data"""
        self.create_chart()
    
    def refresh(self):
        """Refresh all data"""
        self.load_data()

    # ---- Palette + styling helpers ----
    def _refresh_palette(self):
        theme_name = getattr(theme_manager, "current_theme", "light") or "light"
        self._palette = PennyColors.get_palette(theme_name)

    def _apply_styles(self):
        """Apply palette-driven styles for backgrounds, text, combos, and buttons."""
        self._refresh_palette()
        p = self._palette

        # Backgrounds
        self.setStyleSheet(f"background: {p['background']};")
        self.scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: {p['background']};
            }}
            QScrollArea > QWidget {{
                background: {p['background']};
            }}
        """)
        self.container.setStyleSheet(f"background: {p['background']};")
        self.chart_container.setStyleSheet(f"background: {p['surface']};")

        # Text
        self.title_main.setStyleSheet(f"color: {p['text_primary']};")
        self.chart_title.setStyleSheet(f"color: {p['text_primary']};")

        # Range combo
        self.range_combo.setStyleSheet(f"""
            QComboBox {{
                background: {p['surface']};
                color: {p['text_primary']};
                border: 1px solid {p['border']};
                border-radius: 8px;
                padding: 6px 10px;
            }}
            QComboBox::drop-down {{
                width: 24px;
                border-left: 1px solid {p['border']};
            }}
            QComboBox QAbstractItemView {{
                background: {p['surface']};
                color: {p['text_primary']};
                border: 1px solid {p['border']};
                selection-background-color: {p.get('surface_alt', p['surface'])};
                selection-color: {p['text_primary']};
            }}
        """)

        # Buttons & icons
        self._apply_button_styles()

    def _apply_button_styles(self):
        """Style chart type buttons with palette-driven colors and icons."""
        self._refresh_palette()
        p = self._palette
        active = p.get("primary", "#2563EB")
        inactive_bg = p.get("surface", "#FFFFFF")
        hover_bg = p.get("surface_alt", p.get("surface", "#FFFFFF"))
        border = p.get("border", "#E5E7EB")
        text = p.get("text_primary", "#1F2937")

        # Update icons to follow text color
        self.bar_btn.setIcon(qta.icon('fa5s.chart-bar', color=text))
        self.pie_btn.setIcon(qta.icon('fa5s.chart-pie', color=text))
        self.line_btn.setIcon(qta.icon('fa5s.chart-line', color=text))

        def style(btn, is_active):
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {active if is_active else inactive_bg};
                    color: {p['surface'] if is_active else text};
                    border: 2px solid {active if is_active else border};
                    border-radius: 8px;
                    padding: 8px 12px;
                    min-width: 40px;
                    min-height: 40px;
                }}
                QPushButton:hover {{
                    background: {active if is_active else hover_bg};
                }}
            """)

        style(self.bar_btn, self.chart_type == 'bar')
        style(self.pie_btn, self.chart_type == 'pie')
        style(self.line_btn, self.chart_type == 'line')


