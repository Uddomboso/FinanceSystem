from PyQt5.QtWidgets import QWidget,QVBoxLayout,QLabel
from PyQt5.QtCore import Qt,QTimer,QPropertyAnimation,pyqtProperty,QPoint
from PyQt5.QtGui import QFont,QColor,QPainter,QPen,QPainterPath
import qtawesome as qta
from core.theme_manager import theme_manager
from assets.styles.penny_colors import PennyColors


class CircularCommitment(QWidget):
    """Modern circular commitment tracker with muted pastel colors"""

    def __init__(self,category_name,expected_amount,actual_amount=None,
                 status="pending",user_color="#4CAF50",parent=None):
        super().__init__(parent)
        self.category_name = category_name
        self.expected_amount = expected_amount
        self.actual_amount = actual_amount or expected_amount
        self.status = status  # "pending", "paid", "overdue"
        self.user_color = self.mute_color(user_color)
        self._progress = 0
        self._text_color = QColor("#1F2937")  # Default, will be updated

        self.setFixedSize(140,160)
        self.setup_ui()
        self.setup_animations()

    def mute_color(self,hex_color):
        """Convert any color to a muted pastel version"""
        try:
            color = QColor(hex_color)
            if not color.isValid():
                return "#A3BFFA"  # Default muted blue

            # Lighten and desaturate for pastel effect
            h,s,v,a = color.getHsv()
            return QColor.fromHsv(h,min(80,s),min(220,v),a).name()
        except:
            return "#A3BFFA"  # Fallback color

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)
        layout.setContentsMargins(0,0,0,0)

        # Circular container
        self.circle_container = QWidget()
        self.circle_container.setFixedSize(100,100)

        # Status icon
        self.status_icon = QLabel(self.circle_container)
        self.status_icon.setFixedSize(20,20)
        self.status_icon.move(70,10)  # Top-right position
        self.update_status_icon()

        # Amount label (will be drawn in paintEvent)

        # Category name with theme-aware color
        self.name_label = QLabel(self.category_name)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.update_text_colors()

        layout.addWidget(self.circle_container)
        layout.addWidget(self.name_label)

    def update_text_colors(self):
        """Update text colors based on current theme"""
        p = PennyColors.get_palette(theme_manager.current_theme)
        
        # For circular commitments, use dark text on light pastel backgrounds
        # The circles are always light (pastel muted colors), so we need dark text for contrast
        if theme_manager.current_theme == "dark":
            # In dark mode, use dark text on the light pastel circles
            text_color = "#1a3b46"  # Dark teal for good contrast on pastel backgrounds
        else:
            # In light mode, use normal dark text
            text_color = p['text_primary']
        
        self.name_label.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 600;
            color: {text_color};
            background: transparent;
            border: none;
            margin-top: 4px;
        """)
        # Store the text color for use in paintEvent (amount inside circle)
        self._text_color = QColor(text_color)

    def update_status_icon(self):
        """Update the status icon based on current state"""
        try:
            if self.status == "paid":
                icon = qta.icon('fa5s.check',color='#10B981')
            elif self.status == "overdue":
                icon = qta.icon('fa5s.exclamation',color='#EF4444')
            else:  # pending
                icon = qta.icon('fa5s.clock',color='#3B82F6')

            self.status_icon.setPixmap(icon.pixmap(16,16))
            self.status_icon.setStyleSheet("background: transparent; border: none;")
        except Exception as e:
            print(f"Error updating status icon: {e}")

    def setup_animations(self):
        # Calculate target progress
        if self.status == "paid":
            target_progress = 100
        elif self.status == "overdue":
            target_progress = min(100,
                                  (self.actual_amount / self.expected_amount) * 100) if self.expected_amount > 0 else 0
        else:  # pending
            target_progress = 0

        # Progress animation
        self.progress_animation = QPropertyAnimation(self,b"progress")
        self.progress_animation.setDuration(800)
        self.progress_animation.setStartValue(0)
        self.progress_animation.setEndValue(target_progress)
        self.progress_animation.start()

        # Pulsing animation for overdue items
        if self.status == "overdue":
            self.pulse_animation = QPropertyAnimation(self,b"windowOpacity")
            self.pulse_animation.setDuration(1200)
            self.pulse_animation.setStartValue(1.0)
            self.pulse_animation.setEndValue(0.7)
            self.pulse_animation.setLoopCount(-1)
            self.pulse_animation.start()

    def paintEvent(self,event):
        """Custom paint event for the circular design"""
        painter = QPainter(self.circle_container)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw circular background (muted pastel)
        bg_color = QColor(self.user_color)
        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(5,5,90,90)

        # Draw progress ring
        if self._progress > 0:
            pen = QPen()
            if self.status == "paid":
                pen.setColor(QColor("#10B981"))
            elif self.status == "overdue":
                pen.setColor(QColor("#EF4444"))
            else:  # pending
                pen.setColor(QColor("#3B82F6"))

            pen.setWidth(3)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)

            # Draw progress arc
            start_angle = -90 * 16  # Start at top
            span_angle = -self._progress * 3.6 * 16  # Convert percentage to degrees

            painter.drawArc(10,10,80,80,start_angle,span_angle)

        # Draw amount text with theme-aware color (darker for better contrast in dark mode)
        if theme_manager.current_theme == "dark":
            # Use even darker color for amount text inside circle for maximum contrast
            amount_color = QColor("#0a1519")  # Very dark, almost black for best readability
        else:
            amount_color = self._text_color
        painter.setPen(amount_color)
        painter.setFont(QFont("Segoe UI",12,QFont.Bold))
        painter.drawText(5,5,90,90,Qt.AlignCenter,f"${self.expected_amount:.0f}")

        painter.end()

    @pyqtProperty(float)
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self,value):
        self._progress = value
        self.circle_container.update()  # Trigger repaint

    def update_status(self,new_status,actual_amount=None):
        """Update commitment status and refresh display"""
        self.status = new_status
        if actual_amount:
            self.actual_amount = actual_amount

        self.update_status_icon()
        self.setup_animations()
        self.circle_container.update()

    def mousePressEvent(self,event):
        """Make the widget clickable"""
        self.clicked.emit() if hasattr(self,'clicked') else super().mousePressEvent(event)