from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton
from core.ai_suggestions import generate_suggestions, get_recent_suggestions

class AISuggestions(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("AI Suggestions")
        layout = QVBoxLayout()

        label = QLabel(" AI Based Financial Tips")
        label.setStyleSheet("font-size: 18px; font-weight: bold; color: #704b3b;")

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet("font-size: 14px; background-color: #fff9dc;")

        refresh_btn = QPushButton("🔁 Refresh")
        refresh_btn.clicked.connect(self.update_suggestions)
        refresh_btn.setStyleSheet("background-color: #d6733a; color: white; font-weight: bold; padding: 6px;")

        layout.addWidget(label)
        layout.addWidget(self.text_area)
        layout.addWidget(refresh_btn)
        self.setLayout(layout)

        self.update_suggestions()

    def update_suggestions(self):
        try:
            tips_list = generate_suggestions(self.user_id)
            if tips_list:
                tips = "\n\n".join(tips_list)
            else:
                tips = "No suggestions yet. Add budgets or transactions first."
        except Exception as e:
            tips = f" Error:\n{str(e)}"

        self.text_area.setText(tips)
