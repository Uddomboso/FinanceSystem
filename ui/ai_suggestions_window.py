from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit
from core.ai_suggestions import generate_suggestions

class AISuggestions(QWidget):
    def __init__(self, user_id=1):  # temporary hardcoded user_id
        super().__init__()

        self.setWindowTitle("AI Suggestions")
        layout = QVBoxLayout()

        label = QLabel("AI-Based Financial Tips")
        label.setStyleSheet("font-size: 18px; font-weight: bold; color: #704b3b;")

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet("font-size: 14px; background-color: #fff9dc;")

        try:
            tips_list = generate_suggestions(user_id)
            if tips_list:
                tips = "\n\n".join(tips_list)
            else:
                tips = "No suggestions yet. Add some budget or transactions."
        except Exception as e:
            tips = f"Failed to load suggestions:\n{str(e)}"

        self.text_area.setText(tips)

        layout.addWidget(label)
        layout.addWidget(self.text_area)
        self.setLayout(layout)
