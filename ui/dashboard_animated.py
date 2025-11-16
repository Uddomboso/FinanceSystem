# ui/dashboard_animated.py - FIXED
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtCore import QTimer
from core.animations import AnimationManager
from core.logger import logger

# import base dashboard safely
try:
    from ui.dashboard_main import DashboardMain
except ImportError:
    try:
        from .dashboard_main import DashboardMain
    except ImportError as e:
        logger.error(f"Cannot import DashboardMain: {e}")
        from PyQt5.QtWidgets import QMainWindow


        class DashboardMain(QMainWindow):
            def __init__(self,user_id,username,show_tutorial=True):
                super().__init__()
                self.setWindowTitle("Fallback Dashboard")
                self.setMinimumSize(800,600)


class AnimatedDashboardMain(DashboardMain):
    """Dashboard with micro animations"""

    def __init__(self,user_id,username,show_tutorial=True):
        super().__init__(user_id,username,show_tutorial)
        self.animation_manager = AnimationManager()

        # Store references to prevent garbage collection
        self._animation_timers = []

        # Start animations with safer delays
        self.start_animations()

    def start_animations(self):
        """Safely start animations with stored timer references"""
        timer1 = QTimer()
        timer1.timeout.connect(self.animate_metrics_entrance)
        timer1.setSingleShot(True)
        timer1.start(800)  # Longer delay

        timer2 = QTimer()
        timer2.timeout.connect(self.animate_cards_entrance)
        timer2.setSingleShot(True)
        timer2.start(1200)

        # Keep references
        self._animation_timers.extend([timer1,timer2])

    def animate_metrics_entrance(self):
        """Fade in metrics - SAFER VERSION"""
        try:
            # Get all metric widgets safely
            metric_attrs = ['metric_balance','metric_spending','metric_savings','metric_goals']
            metrics = []

            for attr in metric_attrs:
                metric = getattr(self,attr,None)
                if metric and hasattr(metric,'setGraphicsEffect'):
                    metrics.append(metric)

            for i,metric in enumerate(metrics):
                timer = QTimer()
                timer.timeout.connect(lambda m=metric: self.safe_fade_in(m))
                timer.setSingleShot(True)
                timer.start(i * 150)
                self._animation_timers.append(timer)

        except Exception as e:
            logger.warning(f"Metric animation failed: {e}")

    def safe_fade_in(self,widget):
        """Safely fade in a single widget"""
        try:
            if widget and widget.isVisible():
                anim = self.animation_manager.fade_in_widget(widget,700)
                if anim:
                    anim.start()
        except Exception as e:
            logger.debug(f"Fade animation skipped: {e}")

    def animate_cards_entrance(self):
        """Fade in cards - SAFER VERSION"""
        try:
            card_attrs = ['spending_card','goals_card','story_card','actions_card']
            cards = []

            for attr in card_attrs:
                card = getattr(self,attr,None)
                if card and hasattr(card,'setGraphicsEffect'):
                    cards.append(card)

            for i,card in enumerate(cards):
                timer = QTimer()
                timer.timeout.connect(lambda c=card: self.safe_fade_in(c))
                timer.setSingleShot(True)
                timer.start(i * 200)
                self._animation_timers.append(timer)

        except Exception as e:
            logger.warning(f"Card animation failed: {e}")