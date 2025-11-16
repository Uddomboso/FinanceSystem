"""
Theme management for PennyWise - UPDATED WITH FINAL CSS
"""

import os
from core.logger import logger

class ThemeManager:
    """Manage application themes and styling"""

    def __init__(self):
        self.current_theme = "light"
        self.stylesheets = {}

    def load_stylesheets(self):
        """Load all stylesheets from assets"""
        try:
            # Try final theme first
            final_path = "assets/styles/pennywise_final.qss"
            if os.path.exists(final_path):
                with open(final_path, 'r') as f:
                    self.stylesheets['light'] = f.read()
                logger.info("✅ Final theme stylesheet loaded")
            else:
                # Fallback to minimal
                self.stylesheets['light'] = self._get_minimal_stylesheet()
                logger.info("⚠️  Using minimal theme")

            # Future: Load dark theme
            self.stylesheets['dark'] = self.stylesheets['light']

        except Exception as e:
            logger.error(f"❌ Failed to load stylesheets: {e}")
            self.stylesheets['light'] = self._get_minimal_stylesheet()
            self.stylesheets['dark'] = self.stylesheets['light']

    def apply_theme(self, app, theme_name="light"):
        """Apply theme to QApplication"""
        if theme_name not in self.stylesheets:
            logger.warning(f"⚠️  Theme '{theme_name}' not found, using light")
            theme_name = "light"

        self.current_theme = theme_name
        stylesheet = self.stylesheets[theme_name]
        app.setStyleSheet(stylesheet)

        logger.info(f"🎨 Applied {theme_name} theme")
        return True

    def _get_minimal_stylesheet(self):
        """Get minimal fallback stylesheet"""
        return """
        QMainWindow {
            background: #F9FAFB;
            font-family: 'Segoe UI', sans-serif;
            color: #1F2937;
        }
        QFrame.card {
            background: white;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 16px;
        }
        """

# Global theme manager instance
theme_manager = ThemeManager()