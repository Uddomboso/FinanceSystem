from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton
from core.ai_suggestions import get_recent_suggestions, generate_suggestions

class AiSuggestionsWindow(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("ai tips")
        self.setMinimumSize(400, 300)

        self.list = QListWidget()
        self.refresh_btn = QPushButton("refresh tips")

        self.refresh_btn.clicked.connect(self.load_suggestions)

        box = QVBoxLayout()
        box.addWidget(QLabel("some smart things we noticed..."))
        box.addWidget(self.list)
        box.addWidget(self.refresh_btn)

        self.setLayout(box)
        self.load_suggestions()

    def load_suggestions(self):
        self.list.clear()
        generate_suggestions(self.user_id)
        tips = get_recent_suggestions(self.user_id)
        if not tips:
            self.list.addItem("no suggestions yet")
        else:
            for t in tips:
                self.list.addItem(QListWidgetItem(t["content"]))
