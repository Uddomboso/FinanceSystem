"""
Updated AI suggestions using the enhanced EnnyBrain service
"""

import os
import requests
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
from core.config import Config
from core.logger import logger
from ai.penny_brain import penny_brain
from core.ai_insights_cache import _get_financial_context


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


class AiSuggestionWidget(QWidget):
    def __init__(self, parent=None, user_id=None):
        super().__init__(parent)
        self.user_id = user_id
        self.logger = logger

        self.label = QLabel("Penny is thinking... 🤔")
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.get_ai_suggestion()

    def get_ai_suggestion(self):
        try:
            tip = generate_openai_tip(self.user_id)
            self.label.setText(f"💡 Penny says: {tip}")
            self.logger.info(f"AI suggestion displayed for user {self.user_id}")
        except Exception as e:
            self.logger.error(f"AI suggestion error: {e}")
            self.label.setText("💡 Try setting a weekly budget to control spending.")