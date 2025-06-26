from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
from matplotlib.figure import Figure
from core.transactions import get_total_by_type, get_txn_summary_by_cat

class ChartsWindow(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("charts")
        self.setMinimumSize(600, 400)

        self.init_ui()

    def init_ui(self):
        box = QVBoxLayout()

        self.income_expense_chart = self.make_pie_chart()
        self.cat_chart = self.make_bar_chart()

        box.addWidget(QLabel("income vs expense"))
        box.addWidget(self.income_expense_chart)

        box.addWidget(QLabel("top categories"))
        box.addWidget(self.cat_chart)

        self.setLayout(box)

    def make_pie_chart(self):
        fig = Figure(figsize=(4, 3))
        canvas = Canvas(fig)
        ax = fig.add_subplot(111)

        data = get_total_by_type(self.user_id)
        labels = [r["transaction_type"] for r in data]
        values = [r["total"] for r in data]

        if values:
            ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
            ax.axis("equal")
        else:
            ax.text(0.5, 0.5, "no data", ha="center", va="center")

        return canvas

    def make_bar_chart(self):
        fig = Figure(figsize=(5, 3))
        canvas = Canvas(fig)
        ax = fig.add_subplot(111)

        rows = get_txn_summary_by_cat(self.user_id)
        cats = [r["category_name"] for r in rows]
        totals = [r["total"] for r in rows]

        if totals:
            ax.bar(cats, totals, color="#d6733a")
            ax.set_xticklabels(cats, rotation=45, ha="right")
            ax.set_ylabel("amount")
        else:
            ax.text(0.5, 0.5, "no data", ha="center", va="center")

        return canvas
