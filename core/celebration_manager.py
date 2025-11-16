# core/celebration_manager.py

"""
Celebration Manager - Orchestrates celebrations for achievements and milestones
"""

from PyQt5.QtCore import QTimer,QPropertyAnimation,QEasingCurve
from PyQt5.QtWidgets import QGraphicsOpacityEffect
from core.logger import logger


class CelebrationManager:
    """Manages all celebration animations and effects"""

    def __init__(self,parent_widget):
        self.parent = parent_widget
        self.active_celebrations = []

    def celebrate_badges(self,badge_ids,badge_definitions):
        """Celebrate newly earned badges"""
        if not badge_ids:
            return

        badge_names = [badge_definitions[badge_id]['name'] for badge_id in badge_ids]

        # Pulse the badges widget
        self.pulse_badges_widget()

        # Special celebration for rare badges
        for badge_id in badge_ids:
            badge_info = badge_definitions[badge_id]
            if badge_info['rarity'] in ['rare','epic','legendary']:
                self.special_celebration(badge_info)

        logger.info(f"🎉 Celebrating badges: {', '.join(badge_names)}")

    def celebrate_mood_improvement(self,old_mood,new_mood):
        """Celebrate significant mood improvements"""
        improvement = new_mood['score'] - old_mood['score']

        if improvement >= 10:
            self.pulse_mood_meter()
            logger.info(f"📈 Celebrating mood improvement: +{improvement} points")

    def celebrate_goal_completion(self,goal_name):
        """Celebrate financial goal completion"""
        self.pulse_goals_widget()
        logger.info(f"🎯 Celebrating goal completion: {goal_name}")

    def pulse_badges_widget(self):
        """Pulse animation for badges widget"""
        if hasattr(self.parent,'badges_widget'):
            self.pulse_widget(self.parent.badges_widget)

    def pulse_mood_meter(self):
        """Pulse animation for mood meter"""
        if hasattr(self.parent,'mood_meter'):
            self.pulse_widget(self.parent.mood_meter)

    def pulse_goals_widget(self):
        """Pulse animation for goals card"""
        if hasattr(self.parent,'goals_card'):
            self.pulse_widget(self.parent.goals_card)

    def pulse_widget(self,widget):
        """Generic pulse animation for any widget"""
        try:
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)

            # Create pulse animation
            anim = QPropertyAnimation(effect,b"opacity")
            anim.setDuration(800)
            anim.setKeyValueAt(0,1.0)
            anim.setKeyValueAt(0.3,0.6)
            anim.setKeyValueAt(0.6,1.0)
            anim.setKeyValueAt(1.0,1.0)
            anim.setEasingCurve(QEasingCurve.InOutCubic)
            anim.start()

            # Clean up after animation
            QTimer.singleShot(1000,lambda: widget.setGraphicsEffect(None))

        except Exception as e:
            logger.debug(f"Pulse animation skipped: {e}")

    def special_celebration(self,badge_info):
        """Special celebration for rare badges"""
        if badge_info['rarity'] == 'legendary':
            # Multiple pulses for legendary badges
            QTimer.singleShot(500,lambda: self.pulse_badges_widget())

    def cleanup(self):
        """Clean up all active celebrations"""
        for celebration in self.active_celebrations:
            try:
                celebration.stop_celebration()
            except:
                pass
        self.active_celebrations.clear()