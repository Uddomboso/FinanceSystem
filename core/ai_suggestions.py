"""
Updated AI suggestions using the enhanced EnnyBrain service
"""

import os
import requests
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import QEvent
from core.config import Config
from core.logger import logger
from ai.penny_brain import penny_brain
from core.ai_insights_cache import _get_financial_context
from core.mood_calculator import MoodCalculator

# Emotional cycling state tracking (per user_id)
_advice_state_tracking = {}  # {user_id: {'state': 'bad'|'good', 'count': int, 'last_mood': str}}


def generate_openai_tip(user_id):
    """Generate an AI tip using the enhanced EnnyBrain service"""

    # Get financial context for better tips
    financial_context = _get_financial_context(user_id) if user_id else None

    # Use EnnyBrain for robust AI service
    tip, tone = penny_brain.get_financial_tip(user_id, financial_context)

    logger.info(f"AI tip generated with tone: {tone}")
    return tip


def get_ai_service_status():
    """Get the current status of the AI service"""
    return penny_brain.get_service_status()


def generate_penny_message(financial_context: dict) -> dict:
    """Generate Penny's complete message with separated emotion framing and financial advice.
    
    This function orchestrates the mood calculation, emotion phrase generation, and financial
    actions generation to create a complete message where emotion and advice are cleanly separated.
    Includes emotional cycling to prevent nagging.
    
    Args:
        financial_context: Dictionary containing financial context data.
                         Should include 'user_id' key for mood calculation.
                         If 'user_id' is missing, mood will default to 'neutral'.
        
    Returns:
        Dictionary with keys:
            - 'mood': str - The mood label (excellent, good, neutral, concerned, needs_attention)
            - 'message': str - Complete assembled message with emotion opener, phrase, and actions
    """
    try:
        # Extract user_id from context
        user_id = financial_context.get('user_id') if isinstance(financial_context, dict) else None
        
        # Step 1: Calculate mood using MoodCalculator (only use mood_label, not message)
        if user_id:
            mood_calculator = MoodCalculator(user_id)
            mood_data = mood_calculator.calculate_overall_mood()
            mood_label = mood_data.get('mood_level', 'neutral')
        else:
            # Fallback if no user_id
            mood_label = 'neutral'
        
        # Step 2: Determine state (bad vs good) for cycling
        bad_state_moods = ['concerned', 'needs_attention']
        good_state_moods = ['excellent', 'good', 'neutral']
        current_state = 'bad' if mood_label in bad_state_moods else 'good'
        
        # Step 3: Track cycling state (reset if state changed)
        if user_id:
            tracking = _advice_state_tracking.get(user_id, {'state': None, 'count': 0, 'last_mood': None})
            
            if tracking['last_mood'] != mood_label:
                # State changed - reset counter
                tracking['state'] = current_state
                tracking['count'] = 1
                tracking['last_mood'] = mood_label
            else:
                # Same state - increment counter
                tracking['count'] += 1
                tracking['last_mood'] = mood_label
            
            _advice_state_tracking[user_id] = tracking
            cycle_count = tracking['count']
        else:
            cycle_count = 1
        
        # Step 4: Determine advice_mode based on cycling
        if current_state == 'bad':
            # Bad state: 2 strict cycles, then 1 supportive cycle
            if cycle_count <= 2:
                advice_mode = "strict"
            else:
                advice_mode = "supportive"
                # Reset to 1 after 3rd cycle
                if user_id and cycle_count > 3:
                    _advice_state_tracking[user_id]['count'] = 1
        else:
            # Good state: 2 positive cycles, then 1 cautionary cycle
            if cycle_count <= 2:
                advice_mode = "standard"
            else:
                advice_mode = "cautionary"
                # Reset to 1 after 3rd cycle
                if user_id and cycle_count > 3:
                    _advice_state_tracking[user_id]['count'] = 1
        
        # Step 5: Select emotion opener based on mood and mode
        if advice_mode == "supportive":
            # Supportive mode: softer opener
            emotion_openers = {
                'concerned': 'hey,',
                'needs_attention': 'hey,',
                'neutral': 'hey,',
                'good': 'hey,',
                'excellent': 'hey,'
            }
        elif advice_mode == "cautionary":
            # Cautionary mode: neutral opener
            emotion_openers = {
                'concerned': 'hey,',
                'needs_attention': 'hey,',
                'neutral': 'hey,',
                'good': 'hey,',
                'excellent': 'hey,'
            }
        else:
            # Standard/strict mode: mood-based opener
            emotion_openers = {
                'concerned': 'oh no,',
                'needs_attention': 'oh no,',
                'neutral': 'hey,',
                'good': 'oh wow,',
                'excellent': 'oh wow,'
            }
        opener = emotion_openers.get(mood_label, 'hey,')
        
        # Step 6: Generate emotion phrase with advice_mode
        emotion_phrase = penny_brain.generate_emotion_phrase(mood_label, financial_context, advice_mode)
        
        # Step 7: Generate financial actions with advice_mode
        financial_actions = penny_brain.generate_financial_actions(financial_context, advice_mode)
        
        # Step 8: Assemble final message
        # Format: <emotion opener> <emotion phrase> <financial actions sentence>
        actions_text = '. '.join(financial_actions) if financial_actions else 'prioritize essential bills'
        if actions_text and not actions_text.endswith(('.', '!', '?')):
            actions_text += '.'
        
        # Combine: opener + emotion phrase + actions
        final_message = f"{opener} {emotion_phrase} {actions_text}".strip()
        # Ensure lowercase
        final_message = final_message.lower()
        
        # Step 9: Map advice_mode to expression for visual display
        if advice_mode == "supportive":
            expression = "supportive"  # Upturned mouth + green border
        elif advice_mode == "strict":
            expression = "alert"  # Downturned mouth + yellow/red border
        elif advice_mode == "cautionary":
            expression = "neutral"  # Neutral face
        elif advice_mode == "standard":
            if current_state == 'good':
                expression = "positive"  # Upturned mouth + green border
            else:
                expression = "neutral"  # Neutral face
        else:
            expression = "neutral"  # Fallback
        
        logger.info(f"✅ Generated Penny message with mood: {mood_label}, mode: {advice_mode}, expression: {expression}, cycle: {cycle_count}")
        
        return {
            'mood': mood_label,
            'message': final_message,
            'expression': expression
        }
        
    except Exception as e:
        logger.error(f"❌ Error generating Penny message: {e}")
        # Safe fallback
        return {
            'mood': 'neutral',
            'message': 'hey, things look steady. prioritize essential bills.',
            'expression': 'neutral'
        }


class AiSuggestionWidget(QWidget):
    def __init__(self, parent=None, user_id=None):
        super().__init__(parent)
        self.user_id = user_id
        self.logger = logger

        self.label = QLabel("Penny is thinking... 🤔")
        # Apply theme-aware text color
        self._update_text_color()
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.get_ai_suggestion()
    
    def _update_text_color(self):
        """Update label text color based on current theme"""
        from core.theme_manager import theme_manager
        from assets.styles.penny_colors import PennyColors
        p = PennyColors.get_palette(theme_manager.current_theme)
        self.label.setStyleSheet(f"color: {p['text_primary']}; font-size: 14px;")
    
    def changeEvent(self, event):
        """Update text color when theme changes"""
        if event.type() == QEvent.PaletteChange:
            self._update_text_color()
        super().changeEvent(event)

    def get_ai_suggestion(self):
        try:
            tip = generate_openai_tip(self.user_id)
            self.label.setText(f"💡 Penny says: {tip}")
            self.logger.info(f"AI suggestion displayed for user {self.user_id}")
        except Exception as e:
            self.logger.error(f"AI suggestion error: {e}")
            self.label.setText("💡 Try setting a weekly budget to control spending.")