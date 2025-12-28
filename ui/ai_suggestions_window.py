from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton
from core.ai_suggestions import generate_suggestions, get_recent_suggestions
from core.theme_manager import theme_manager
from assets.styles.penny_colors import PennyColors

class AISuggestions(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("AI Suggestions")
        layout = QVBoxLayout()

        self.label = QLabel("💡 AI-Based Financial Tips")
        layout.addWidget(self.label)
        
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)

        self.refresh_btn = QPushButton("🔁 Refresh")
        self.refresh_btn.clicked.connect(self.update_suggestions)
        layout.addWidget(self.refresh_btn)
        
        self.setLayout(layout)
        
        # Apply theme-aware colors after widgets are created
        self._update_colors()

        self.update_suggestions()
    
    def _update_colors(self):
        """Update all text colors based on current theme"""
        p = PennyColors.get_palette(theme_manager.current_theme)
        
        # Update label color
        if hasattr(self, 'label'):
            self.label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {p['text_primary']};")
        
        # Update text area colors
        if hasattr(self, 'text_area'):
            self.text_area.setStyleSheet(f"""
                font-size: 14px; 
                background-color: {p['surface']}; 
                color: {p['text_primary']};
                border: 1px solid {p['border']};
            """)
        
        # Update button colors
        if hasattr(self, 'refresh_btn'):
            self.refresh_btn.setStyleSheet(f"""
                background-color: {p['accent']}; 
                color: {p['background']}; 
                font-weight: bold; 
                padding: 6px;
                border-radius: 8px;
            """)

    def update_suggestions(self):
        try:
            tips_list = generate_suggestions(self.user_id)
            if tips_list:
                tips = "\n\n".join(tips_list)
            else:
                tips = "No suggestions yet. Add budgets or transactions first."
        except Exception as e:
            tips = f"⚠️ Error:\n{str(e)}"

        self.text_area.setText(tips)
