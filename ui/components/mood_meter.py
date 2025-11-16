"""
Visual Financial Mood Meter Widget - animated & emotionally aware
"""

from PyQt5.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                            QProgressBar, QGraphicsOpacityEffect)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PyQt5.QtGui import QFont
from core.mood_calculator import MoodCalculator

class MoodMeter(QFrame):
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.mood_calculator = MoodCalculator(user_id)
        self.current_mood = None
        self.setup_ui()
        self.apply_style()
        self.fade_in()
        self.load_mood_data()

    def setup_ui(self):
        self.setProperty("class", "mood_meter")
        self.setFixedHeight(120)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        # header
        top = QHBoxLayout()
        title = QLabel("💖 Financial Mood")
        title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        title.setStyleSheet("color:#1F2937;")
        self.mood_label = QLabel("Loading...")
        self.mood_label.setStyleSheet("""
            background:#6B7280;color:white;padding:4px 10px;
            border-radius:10px;font-size:11px;font-weight:bold;
        """)
        top.addWidget(title); top.addStretch(); top.addWidget(self.mood_label)
        layout.addLayout(top)

        # message
        self.mood_msg = QLabel("Analyzing your financial health...")
        self.mood_msg.setWordWrap(True)
        self.mood_msg.setStyleSheet("color:#6B7280;font-size:13px;")
        layout.addWidget(self.mood_msg)

        # progress
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(10)
        self.bar.setStyleSheet("""
            QProgressBar {background:#E5E7EB;border:none;border-radius:6px;}
            QProgressBar::chunk {border-radius:6px;background:#2563EB;}
        """)
        layout.addWidget(self.bar)

        # scale
        scale = QHBoxLayout()
        for s in ["Needs Help", "Concerned", "Neutral", "Good", "Excellent"]:
            lbl = QLabel(s)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color:#6B7280;font-size:10px;")
            scale.addWidget(lbl)
        layout.addLayout(scale)

    def apply_style(self):
        self.setStyleSheet("""
            QFrame[class="mood_meter"] {
                background:#FFFFFF;
                border:1px solid rgba(0,0,0,0.06);
                border-radius:16px;
            }
        """)

    def fade_in(self):
        eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(eff)
        self.anim = QPropertyAnimation(eff, b"opacity")
        self.anim.setDuration(600)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        QTimer.singleShot(100, self.anim.start)

    def load_mood_data(self):
        self.current_mood = self.mood_calculator.calculate_overall_mood()
        self.update_display()
        self.animate_bar()

    def update_display(self):
        if not self.current_mood: return
        mood = self.current_mood['mood_level']
        score = int(self.current_mood['score'])
        msg = self.current_mood['message']

        colors = {
            "excellent":"#10B981","good":"#22C55E","neutral":"#F59E0B",
            "concerned":"#F97316","needs_attention":"#EF4444"
        }
        texts = {
            "excellent":"🎉 Excellent","good":"👍 Good","neutral":"💭 Neutral",
            "concerned":"🤔 Concerned","needs_attention":"🆗 Needs Help"
        }

        color = colors.get(mood,"#F59E0B")
        text = texts.get(mood,"💭 Neutral")
        self.mood_label.setText(text)
        self.mood_label.setStyleSheet(f"""
            background:{color};color:white;padding:4px 10px;
            border-radius:10px;font-size:11px;font-weight:bold;
        """)
        self.mood_msg.setText(msg)
        self.bar.setStyleSheet(f"""
            QProgressBar {{background:#E5E7EB;border:none;border-radius:6px;}}
            QProgressBar::chunk {{border-radius:6px;background:{color};}}
        """)

    def animate_bar(self):
        if not self.current_mood: return
        self.anim_bar = QPropertyAnimation(self.bar, b"value")
        self.anim_bar.setDuration(1200)
        self.anim_bar.setStartValue(0)
        self.anim_bar.setEndValue(int(self.current_mood['score']))
        self.anim_bar.setEasingCurve(QEasingCurve.OutCubic)
        self.anim_bar.start()

    def refresh(self):
        self.current_mood = self.mood_calculator.calculate_overall_mood()
        self.update_display()
        self.animate_bar()
        return self.current_mood