# ui/components/penny_avatar.py

"""
Enhanced Penny Avatar with Emotional States - FIXED VERSION
"""

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt,QTimer
from PyQt5.QtGui import QPixmap,QPainter,QRadialGradient,QColor,QPen
import random
import json
import time


class PennyAvatar(QLabel):
    """Enhanced Penny avatar with emotional state animations - FIXED"""

    def __init__(self,size=60,parent=None):
        super().__init__(parent)
        self.size = size
        self.is_blinking = False
        self.current_emotion = "neutral"  # neutral, happy, excited, concerned, supportive
        self.emotion_color_map = {
            "neutral": ("#FBBF24","#F59E0B"),  # Yellow
            "happy": ("#34D399","#10B981"),  # Green
            "excited": ("#F472B6","#EC4899"),  # Pink
            "concerned": ("#FCD34D","#F59E0B"),  # Yellow
            "supportive": ("#34D399","#10B981"),  # Green (upturned)
            "celebratory": ("#34D399","#10B981"),  # Green (upturned)
            "positive": ("#34D399","#10B981"),  # Green (upturned)
            "friendly": ("#FBBF24","#F59E0B"),  # Yellow
            "warning": ("#FCD34D","#F59E0B"),  # Yellow (downturned)
            "alert": ("#FEE2E2","#FCA5A5"),  # Red (downturned)
            "strict": ("#FCD34D","#F59E0B")  # Yellow (downturned)
        }

        self.setup_avatar()  # This method now exists!
        self.start_blink_animation()

    def setup_avatar(self):
        """Setup avatar appearance and behavior - ADDED THIS METHOD"""
        self.setFixedSize(self.size,self.size)
        self.setProperty("class","penny_avatar")
        self.setAlignment(Qt.AlignCenter)

        # Make it clickable
        self.setCursor(Qt.PointingHandCursor)

        # Create initial avatar
        self.draw_avatar(eyes_open=True)

    def update_emotional_state(self,emotion):
        """Update avatar's emotional state"""
        self.current_emotion = emotion
        self.draw_avatar(eyes_open=True)

    def draw_avatar(self,eyes_open=True):
        """Draw Penny's avatar with emotional coloring"""
        pixmap = QPixmap(self.size,self.size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        try:
            # Draw soft white background circle with shadow
            shadow_offset = 2
            shadow_radius = self.size - 4
            
            # Draw shadow (subtle)
            painter.setBrush(QColor(0, 0, 0, 15))  # Very light shadow
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(shadow_offset, shadow_offset, shadow_radius, shadow_radius)
            
            # Draw white background circle
            painter.setBrush(QColor(255, 255, 255, 240))  # Soft white with slight transparency
            painter.setPen(QPen(QColor(0, 0, 0, 8), 1))  # Very subtle border
            painter.drawEllipse(1, 1, self.size - 2, self.size - 2)

            # Get colors for current emotion
            start_color,end_color = self.emotion_color_map.get(
                self.current_emotion,
                self.emotion_color_map["neutral"]
            )

            # Draw face (smaller circle with emotion-based gradient)
            face_size = self.size - 12  # Smaller face within the white circle
            face_offset = 6
            gradient = QRadialGradient(
                self.size / 2, self.size / 2, face_size / 2
            )
            gradient.setColorAt(0,QColor(start_color))
            gradient.setColorAt(1,QColor(end_color))

            painter.setBrush(gradient)
            painter.setPen(Qt.NoPen)

            # Draw face circle (smaller and centered)
            painter.drawEllipse(face_offset, face_offset, face_size, face_size)

            # Draw eyes based on emotion
            self._draw_emotional_eyes(painter,eyes_open)

            # Draw mouth based on emotion
            self._draw_emotional_mouth(painter)

        finally:
            painter.end()

        self.setPixmap(pixmap)

    def _draw_emotional_eyes(self,painter,eyes_open):
        """Draw eyes based on emotional state"""
        eye_color = QColor("#1F2937")
        painter.setBrush(eye_color)
        painter.setPen(Qt.NoPen)

        # Adjust eye size and position for smaller face
        face_size = self.size - 12
        face_offset = 6
        eye_size = 4
        center_x = self.size / 2
        center_y = self.size / 2

        if eyes_open:
            # Open eyes - position varies by emotion
            if self.current_emotion in ["excited","celebratory"]:
                # Wide, excited eyes
                painter.drawEllipse(int(center_x - 10),int(center_y - 6),eye_size,eye_size)
                painter.drawEllipse(int(center_x + 6),int(center_y - 6),eye_size,eye_size)
            elif self.current_emotion in ["concerned","supportive"]:
                # Slightly concerned/supportive eyes
                painter.drawEllipse(int(center_x - 8),int(center_y - 4),eye_size - 1,eye_size - 1)
                painter.drawEllipse(int(center_x + 4),int(center_y - 4),eye_size - 1,eye_size - 1)
            else:
                # Normal happy eyes
                painter.drawEllipse(int(center_x - 8),int(center_y - 4),eye_size,eye_size)
                painter.drawEllipse(int(center_x + 4),int(center_y - 4),eye_size,eye_size)
        else:
            # Closed eyes (blinking)
            painter.drawRect(int(center_x - 8),int(center_y - 2),6,1)
            painter.drawRect(int(center_x + 2),int(center_y - 2),6,1)

    def _draw_emotional_mouth(self,painter):
        """Draw mouth based on emotional state"""
        mouth_color = QColor("#1F2937")
        painter.setPen(QPen(mouth_color,1.5))  # Thinner line for smaller face
        painter.setBrush(Qt.NoBrush)

        center_x = self.size / 2
        center_y = self.size / 2

        # Map expressions to mouth states based on expression (not mood)
        # Downturned mouth: strict/alert/warning
        downturned_expressions = ["strict", "alert", "warning"]
        # Upturned mouth: supportive/positive/celebratory/happy/excited
        upturned_expressions = ["supportive", "positive", "celebratory", "happy", "excited"]
        
        is_downturned = self.current_emotion in downturned_expressions
        is_upturned = self.current_emotion in upturned_expressions
        
        if is_downturned:
            # Downturned mouth (frown) for strict/alert expressions
            painter.drawArc(
                int(center_x - 6),
                int(center_y + 1),
                12,8,
                0,180 * 16  # Downward frown
            )
        elif is_upturned:
            # Upturned mouth (smile) for supportive/positive expressions
            if self.current_emotion in ["supportive", "positive"]:
                # Gentle supportive/positive smile
                painter.drawArc(
                    int(center_x - 6),
                    int(center_y + 3),
                    12,6,
                    0,-180 * 16  # Gentle upward smile
                )
            else:
                # Big happy smile for excited/celebratory
                painter.drawArc(
                    int(center_x - 8),
                    int(center_y + 2),
                    16,8,
                    0,-180 * 16  # Upward smile
                )
        else:
            # Neutral mouth (neutral expression)
            painter.drawArc(
                int(center_x - 6),
                int(center_y + 4),
                12,4,
                0,180 * 16  # Neutral/straight line
            )

    def start_blink_animation(self):
        """Start random blinking animation"""
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.random_blink)
        self.blink_timer.start(3000)  # Blink every 3-5 seconds

    def random_blink(self):
        """Perform a random blink"""
        if random.random() < 0.3:  # 30% chance to blink
            self.blink()

    def blink(self):
        """Perform a blink animation"""
        if self.is_blinking:
            return

        self.is_blinking = True

        # Close eyes
        self.draw_avatar(eyes_open=False)

        # Reopen eyes after short delay
        QTimer.singleShot(150,lambda: self.draw_avatar(eyes_open=True))
        QTimer.singleShot(200,lambda: setattr(self,'is_blinking',False))