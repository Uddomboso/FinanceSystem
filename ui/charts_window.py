from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
from matplotlib.figure import Figure
from core.transactions import get_total_by_type, get_txn_summary_by_cat

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QVBoxLayout,QWidget,QLabel
from database.db_manager import fetch_all


class ChartsWindow(QWidget):
    def __init__(self,user_id):
        super().__init__()
        self.user_id = user_id
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Income vs Expense Chart
        self.income_expense_chart = self.make_pie_chart()
        if self.income_expense_chart:
            layout.addWidget(QLabel("Income vs Expenses"))
            layout.addWidget(self.income_expense_chart)
        else:
            layout.addWidget(QLabel("No data available for Income vs Expenses chart"))

        # Expense by Category Chart
        self.expense_category_chart = self.make_expense_by_category_chart()
        if self.expense_category_chart:
            layout.addWidget(QLabel("Expenses by Category"))
            layout.addWidget(self.expense_category_chart)
        else:
            layout.addWidget(QLabel("No data available for Expenses by Category chart"))

    def make_pie_chart(self):
        """Create income vs expense pie chart with error handling"""
        try:
            # Get total income
            income_data = fetch_all(
                "SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'income' AND amount > 0",
                (self.user_id,)
            )
            total_income = income_data[0][0] if income_data and income_data[0][0] is not None else 0

            # Get total expenses
            expense_data = fetch_all(
                "SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'expense' AND amount > 0",
                (self.user_id,)
            )
            total_expense = expense_data[0][0] if expense_data and expense_data[0][0] is not None else 0

            # Check if we have valid data
            if total_income <= 0 and total_expense <= 0:
                return None

            # Prepare data for pie chart
            labels = []
            values = []

            if total_income > 0:
                labels.append('Income')
                values.append(total_income)

            if total_expense > 0:
                labels.append('Expenses')
                values.append(total_expense)

            # Create the chart
            fig,ax = plt.subplots(figsize=(8,6))
            ax.pie(values,labels=labels,autopct="%1.1f%%",startangle=90)
            ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
            ax.set_title('Income vs Expenses')

            canvas = FigureCanvas(fig)
            return canvas

        except Exception as e:
            print(f"Error creating pie chart: {e}")
            return None

    def make_expense_by_category_chart(self):
        """Create expense by category bar chart with error handling"""
        try:
            # Get expenses by category
            category_data = fetch_all("""
                SELECT c.category_name, SUM(t.amount) 
                FROM transactions t
                JOIN categories c ON t.category_id = c.category_id
                WHERE t.user_id = ? AND t.type = 'expense' AND t.amount > 0
                GROUP BY c.category_name
                HAVING SUM(t.amount) > 0
            """,(self.user_id,))

            if not category_data:
                return None

            categories = [row[0] for row in category_data]
            amounts = [row[1] for row in category_data]

            # Create the chart
            fig,ax = plt.subplots(figsize=(10,6))
            bars = ax.bar(categories,amounts,color=['#ff9999','#66b3ff','#99ff99','#ffcc99'])
            ax.set_title('Expenses by Category')
            ax.set_ylabel('Amount')
            plt.xticks(rotation=45)

            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2.,height,
                        f'${height:.2f}',
                        ha='center',va='bottom')

            canvas = FigureCanvas(fig)
            return canvas

        except Exception as e:
            print(f"Error creating category chart: {e}")
            return None