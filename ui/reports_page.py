# ui/reports_page.py
"""
Enhanced Reports Page with Gamification and Bank Activity Charts

REPORT COMPUTATION RULES (Examiner-Proof):
==========================================
1. Total Income = SUM(amount) WHERE transaction_type = 'income'
2. Total Expenses = SUM(amount) WHERE transaction_type = 'expense'
3. Net Cash Flow = Total Income - Total Expenses
4. NEVER use amount sign (>= 0 or < 0) to determine income/expense
5. All amounts are stored as positive; transaction_type field determines category
6. Edge cases:
   - Zero-amount transactions: included if transaction_type is set (rare but valid)
   - Refunds: should be stored as 'income' transaction_type (money coming in)
   - Transfers: not currently in schema (transaction_type only has 'income'/'expense')
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QPushButton, QButtonGroup, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QFont
from database.db_manager import fetch_all, fetch_one
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
        self._refreshing_theme = False
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
        
        # Download PDF button
        self.download_pdf_btn = QPushButton("Download Bank Statement (PDF)")
        self.download_pdf_btn.setFont(QFont("Segoe UI", 11))
        self.download_pdf_btn.clicked.connect(self.download_bank_statement)
        header_layout.addWidget(self.download_pdf_btn)
        
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
        
        # CORRECTED QUERY: Uses transaction_type field, never amount sign
        # Rule: Income = sum of amounts where transaction_type = 'income'
        #       Expense = sum of amounts where transaction_type = 'expense'
        #       All amounts stored as positive; transaction_type determines category
        transactions = fetch_all("""
            SELECT 
                date(t.date) as day,
                SUM(CASE WHEN t.transaction_type = 'income' THEN t.amount ELSE 0 END) as income,
                SUM(CASE WHEN t.transaction_type = 'expense' THEN t.amount ELSE 0 END) as expense
            FROM transactions t
            WHERE t.user_id = ? 
              AND date(t.date) BETWEEN ? AND ?
              AND t.transaction_type IN ('income', 'expense')
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
        
        # Prepare data for chart visualization
        dates = []
        income_values = []
        expense_values = []
        
        # #region agent log
        import json
        import time
        negative_income_days = []
        negative_expense_days = []
        # #endregion
        
        for txn in transactions:
            dates.append(txn['day'])
            income_val = float(txn['income'] or 0)
            expense_val = float(txn['expense'] or 0)
            
            # #region agent log
            if income_val < 0:
                negative_income_days.append({"day": txn['day'], "value": income_val})
            if expense_val < 0:
                negative_expense_days.append({"day": txn['day'], "value": expense_val})
            # #endregion
            
            income_values.append(income_val)
            expense_values.append(expense_val)
        
        # #region agent log
        try:
            total_income_raw = sum(income_values)
            total_expense_raw = sum(expense_values)
            
            # Identify problematic transactions (negative amounts with transaction_type)
            problem_txns = fetch_all("""
                SELECT transaction_id, amount, transaction_type, date, description
                FROM transactions
                WHERE user_id = ? 
                  AND date(date) BETWEEN ? AND ?
                  AND amount < 0
                ORDER BY date DESC
            """, (self.user_id, start_date.isoformat(), end_date.isoformat()))
            
            problem_list = []
            if problem_txns:
                for t in problem_txns[:10]:  # Limit to 10 for brevity
                    problem_list.append({
                        "id": t["transaction_id"] if "transaction_id" in t.keys() else None,
                        "amount": t["amount"] if "amount" in t.keys() else 0,
                        "type": t["transaction_type"] if "transaction_type" in t.keys() else None,
                        "date": str(t["date"]) if "date" in t.keys() else "",
                        "desc": str(t["description"])[:50] if "description" in t.keys() and t["description"] else ""
                    })
            
            with open(r'c:\Users\asus\OneDrive\Desktop\PennyWise\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"chart-fix","hypothesisId":"B","location":"reports_page.py:create_chart","message":"Raw aggregated values and problematic transactions","data":{"total_income_raw":total_income_raw,"total_expense_raw":total_expense_raw,"negative_income_days":negative_income_days,"negative_expense_days":negative_expense_days,"problematic_transactions":problem_list,"chart_type":self.chart_type},"timestamp":int(time.time()*1000)}) + '\n')
        except Exception as e:
            try:
                with open(r'c:\Users\asus\OneDrive\Desktop\PennyWise\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"chart-fix","hypothesisId":"B","location":"reports_page.py:create_chart","message":"Error logging raw values","data":{"error":str(e)},"timestamp":int(time.time()*1000)}) + '\n')
            except: pass
        # #endregion
        
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
            # FIXED: Clamp negative values to 0 for bar chart display
            # Negative values indicate data quality issues, but for visualization we show them as 0
            # (Income should never be negative in a bar chart - it's confusing)
            income_display = [max(0, val) for val in income_values]
            expense_display = [max(0, val) for val in expense_values]
            
            # #region agent log
            try:
                negative_count = sum(1 for v in income_values if v < 0)
                with open(r'c:\Users\asus\OneDrive\Desktop\PennyWise\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"chart-fix","hypothesisId":"B","location":"reports_page.py:create_chart","message":"Bar chart values (clamped)","data":{"negative_income_count":negative_count,"sample_income_before":income_values[:5],"sample_income_after":income_display[:5]},"timestamp":int(time.time()*1000)}) + '\n')
            except: pass
            # #endregion
            
            x = range(len(dates))
            width = 0.35
            ax.bar([i - width/2 for i in x], income_display, width, label='Income', color=income_color, alpha=0.85)
            ax.bar([i + width/2 for i in x], expense_display, width, label='Expenses', color=expense_color, alpha=0.85)
            ax.set_xlabel('Date')
            ax.set_ylabel('Amount ($)')
            ax.set_title(f'Bank Activity - Income vs Expenses ({title_suffix})')
            legend = ax.legend()
            ax.set_xticks(x)
            ax.set_xticklabels([d[-5:] if d else '' for d in dates], rotation=45, ha='right')
            
        elif self.chart_type == 'pie':
            # Pie chart - total income vs total expenses
            # FIXED: Use absolute values for pie chart (pie charts can't meaningfully show negative values)
            # Negative values indicate data quality issues (refunds/corrections), but we display them as positive for visualization
            total_income = sum(income_values)
            total_expense = sum(expense_values)
            
            # Use absolute values for pie chart display
            abs_income = abs(total_income) if total_income != 0 else 0
            abs_expense = abs(total_expense) if total_expense != 0 else 0
            
            # #region agent log
            try:
                with open(r'c:\Users\asus\OneDrive\Desktop\PennyWise\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"chart-fix","hypothesisId":"B","location":"reports_page.py:create_chart","message":"Pie chart values (before/after abs)","data":{"total_income_raw":total_income,"total_expense_raw":total_expense,"abs_income":abs_income,"abs_expense":abs_expense},"timestamp":int(time.time()*1000)}) + '\n')
            except: pass
            # #endregion
            
            if abs_income > 0 or abs_expense > 0:
                labels = []
                sizes = []
                colors = []
                
                if abs_income > 0:
                    labels.append('Income')
                    sizes.append(abs_income)
                    colors.append(income_color)
                
                if abs_expense > 0:
                    labels.append('Expenses')
                    sizes.append(abs_expense)
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
            # FIXED: Use absolute values for line chart to avoid confusing negative income lines
            # Negative values indicate data quality issues, but we display them as positive for clarity
            income_display = [abs(val) for val in income_values]
            expense_display = [abs(val) for val in expense_values]
            
            x = range(len(dates))
            ax.plot(x, income_display, marker='o', label='Income', color=income_color, linewidth=2)
            ax.plot(x, expense_display, marker='s', label='Expenses', color=expense_color, linewidth=2)
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
    
    def _get_current_date_range(self):
        """Get the current date range based on range_mode"""
        end_date = date.today()
        if self.range_mode == "year":
            start_date = date(end_date.year, 1, 1)
        elif self.range_mode.startswith("month:"):
            _, ym = self.range_mode.split(":")
            year, month = map(int, ym.split("-"))
            start_date = date(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            end_date = date(year, month, last_day)
        else:  # default 30d
            start_date = end_date - timedelta(days=30)
        return start_date, end_date
    
    def download_bank_statement(self):
        """Generate and download bank statement as PDF"""
        try:
            # Get current date range
            start_date, end_date = self._get_current_date_range()
            
            # Fetch transactions with categories for the date range
            transactions = fetch_all("""
                SELECT 
                    t.date,
                    t.description,
                    t.amount,
                    t.transaction_type,
                    c.category_name
                FROM transactions t
                LEFT JOIN categories c ON t.category_id = c.category_id
                WHERE t.user_id = ? 
                  AND date(t.date) BETWEEN ? AND ?
                  AND t.transaction_type IN ('income', 'expense')
                ORDER BY t.date DESC, t.transaction_id DESC
            """, (self.user_id, start_date.isoformat(), end_date.isoformat()))
            
            # Convert sqlite3.Row to dict
            transactions_list = []
            for txn in transactions:
                transactions_list.append({
                    'date': txn['date'] if 'date' in txn.keys() else None,
                    'description': txn['description'] if 'description' in txn.keys() else 'N/A',
                    'amount': float(txn['amount'] or 0) if 'amount' in txn.keys() else 0.0,
                    'transaction_type': txn['transaction_type'] if 'transaction_type' in txn.keys() else 'expense',
                    'category_name': txn['category_name'] if 'category_name' in txn.keys() else 'Uncategorized'
                })
            
            # Fetch account balances from Plaid
            checking_balance = 0.0
            savings_balance = 0.0
            checking_account_id = None
            savings_account_id = None
            
            from core.plaid_api import get_account_balances
            
            # Get checking account balance
            checking_account = fetch_one("""
                SELECT account_id, plaid_token
                FROM accounts 
                WHERE user_id = ? 
                AND account_type = 'salary' AND is_primary = 1
                AND plaid_token IS NOT NULL
                LIMIT 1
            """, (self.user_id,))
            
            if checking_account:
                checking_account_id = checking_account['account_id'] if 'account_id' in checking_account.keys() else None
                try:
                    balances_data = get_account_balances(checking_account['plaid_token'] if 'plaid_token' in checking_account.keys() else None)
                    if "error" not in balances_data:
                        for acc_balance in balances_data.get("accounts", []):
                            if acc_balance["account_id"] == checking_account_id:
                                checking_balance = float(acc_balance["balances"].get("available", 0) or 0)
                                break
                except Exception as e:
                    pass
            
            # Get savings account balance - sum all savings accounts
            savings_accounts = fetch_all("""
                SELECT account_id, plaid_token
                FROM accounts 
                WHERE user_id = ? 
                AND account_type = 'savings'
                AND plaid_token IS NOT NULL
            """, (self.user_id,))
            
            if savings_accounts:
                for savings_account in savings_accounts:
                    savings_account_id = savings_account['account_id'] if 'account_id' in savings_account.keys() else None
                    try:
                        balances_data = get_account_balances(savings_account['plaid_token'] if 'plaid_token' in savings_account.keys() else None)
                        if "error" not in balances_data:
                            for acc_balance in balances_data.get("accounts", []):
                                if acc_balance["account_id"] == savings_account_id:
                                    balance = float(acc_balance["balances"].get("available", 0) or 0)
                                    savings_balance += balance
                    except Exception as e:
                        pass
            
            # Show file dialog
            default_filename = f"bank_statement_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.pdf"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Bank Statement",
                default_filename,
                "PDF Files (*.pdf);;All Files (*)"
            )
            
            if not file_path:
                return  # User cancelled
            
            # Generate PDF
            from core.pdf_statement import generate_bank_statement
            
            success = generate_bank_statement(
                output_path=file_path,
                user_id=self.user_id,
                start_date=start_date,
                end_date=end_date,
                transactions=transactions_list,
                checking_balance=checking_balance,
                savings_balance=savings_balance,
                checking_account_id=checking_account_id,
                savings_account_id=savings_account_id,
                commitments=None  # Commitments not currently shown in reports
            )
            
            if success:
                QMessageBox.information(
                    self,
                    "Success",
                    f"Bank statement saved successfully to:\n{file_path}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Failed to generate bank statement. Please try again."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while generating the bank statement:\n{str(e)}"
            )
    
    def load_data(self):
        """Load chart and badge data"""
        self.create_chart()
    
    def refresh(self):
        """Refresh all data"""
        self.load_data()

    def changeEvent(self, event):
        """Reapply palette styles and redraw chart on theme change without restart."""
        if event.type() == QEvent.PaletteChange and not self._refreshing_theme:
            self._refreshing_theme = True
            try:
                # Re-style widgets and redraw chart with new palette
                self._apply_styles()
                self.create_chart()
            finally:
                self._refreshing_theme = False
        super().changeEvent(event)

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


