# core/animations.py - UPDATED
from PyQt5.QtCore import QPropertyAnimation,QEasingCurve,QSequentialAnimationGroup
from PyQt5.QtWidgets import QGraphicsOpacityEffect,QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QRect


class AnimationManager:
    """Manages micro-animations throughout the app"""

    @staticmethod
    def fade_in_widget(widget,duration=400):
        """Fade in a widget with ease-out curve"""
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)

        animation = QPropertyAnimation(effect,b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        return animation

    @staticmethod
    def pulse_widget(widget,scale_factor=1.05,duration=300):
        """Create a gentle pulse animation - FIXED with integer geometry"""
        animation = QPropertyAnimation(widget,b"geometry")
        animation.setDuration(duration)

        original_geometry = widget.geometry()
        center = original_geometry.center()

        # Calculate scaled geometry - CONVERT TO INTEGERS
        new_width = int(original_geometry.width() * scale_factor)
        new_height = int(original_geometry.height() * scale_factor)

        new_geometry = QRect(
            center.x() - new_width // 2,  # Integer division
            center.y() - new_height // 2,  # Integer division
            new_width,
            new_height
        )

        animation.setStartValue(original_geometry)
        animation.setKeyValueAt(0.5,new_geometry)
        animation.setEndValue(original_geometry)
        animation.setEasingCurve(QEasingCurve.InOutQuad)

        return animation

    @staticmethod
    def highlight_widget(widget,color="#F59E0B",duration=600):
        """Highlight widget with color glow"""
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setColor(QColor(color))
        shadow.setBlurRadius(0)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        widget.setGraphicsEffect(shadow)

        # Animate shadow radius
        animation = QPropertyAnimation(shadow,b"blurRadius")
        animation.setDuration(duration)
        animation.setStartValue(0)
        animation.setKeyValueAt(0.5,20)
        animation.setEndValue(0)
        animation.setEasingCurve(QEasingCurve.InOutQuad)

        return animation


class AnimatedMetricChip:
    """Enhanced metric chip with value change animations"""

    @staticmethod
    def animate_value_change(metric_widget,old_value,new_value):
        """Animate metric value changes"""
        # Create a sequential animation group
        sequence = QSequentialAnimationGroup()

        # First, pulse the widget
        pulse = AnimationManager.pulse_widget(metric_widget,1.08,200)
        sequence.addAnimation(pulse)

        # Then highlight briefly
        highlight = AnimationManager.highlight_widget(metric_widget,"#10B981",400)
        sequence.addAnimation(highlight)

        return sequence