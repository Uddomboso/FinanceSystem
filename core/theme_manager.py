"""
Theme management for PennyWise - styles built from a single palette source.
"""

from PyQt5.QtWidgets import QApplication

from core.logger import logger
from assets.styles.penny_colors import PennyColors

# Module-level active theme (kept in sync with ThemeManager instance)
current_theme = "light"


class ThemeManager:
    """Manage application themes and styling."""

    def __init__(self):
        self.current_theme = "light"
        self.stylesheets = {}
        self._sync_global_theme()

    def load_stylesheets(self):
        """Build light/dark stylesheets from the unified palette."""
        try:
            self.stylesheets["light"] = self._build_stylesheet(PennyColors.get_palette("light"))
            self.stylesheets["dark"] = self._build_stylesheet(PennyColors.get_palette("dark"))
            logger.info("✅ Themes built from palette")
        except Exception as e:
            logger.error(f"❌ Failed to build stylesheets: {e}")
            # Minimal fallback
            fallback = self._get_minimal_stylesheet()
            self.stylesheets["light"] = fallback
            self.stylesheets["dark"] = fallback

    def apply_theme(self, app=None, theme_name="light"):
        """
        Apply theme to the running QApplication.

        - Defaults to QApplication.instance() to avoid stray app objects.
        - Lazily builds stylesheets if not loaded yet.
        - Processes events to reflect the change immediately.
        """
        target_app = app or QApplication.instance()
        if target_app is None:
            logger.error("❌ Cannot apply theme: no QApplication instance is running")
            return False

        # Guard against passing a different app than the active instance
        active_app = QApplication.instance()
        if app is not None and active_app is not None and app is not active_app:
            logger.warning("⚠️ apply_theme called with non-active QApplication; using the active instance instead")
            target_app = active_app

        if not self.stylesheets:
            self.load_stylesheets()

        theme_name = (theme_name or "light").lower()

        if theme_name not in self.stylesheets:
            logger.warning(f"⚠️  Theme '{theme_name}' not found, using light")
            theme_name = "light"

        self.current_theme = theme_name
        self._sync_global_theme()
        target_app.setStyleSheet(self.stylesheets[theme_name])
        # Ensure queued updates flush so widgets repaint without restart
        try:
            target_app.processEvents()
        except Exception:
            # If processEvents isn't available (unlikely), continue silently
            pass
        logger.info(f"🎨 Applied {theme_name} theme")
        return True

    def _sync_global_theme(self):
        """Keep module-level current_theme in sync for legacy imports."""
        global current_theme
        current_theme = self.current_theme

    def _build_stylesheet(self, p: dict) -> str:
        """Create a stylesheet string from a palette dict."""
        return f"""
        /* Base */
        QMainWindow, QWidget {{
            background: {p['background']};
            color: {p['text_primary']};
            font-family: 'Segoe UI', system-ui, sans-serif;
        }}

        /* Cards */
        QFrame.card, QGroupBox {{
            background: {p['surface']};
            border: 1px solid {p['border']};
            border-radius: 16px;
            padding: 16px;
        }}
        QFrame.card:hover {{
            border-color: {p['accent']};
        }}

        /* Text */
        QLabel {{
            color: {p['text_primary']};
        }}
        QLabel[role="meta"], QLabel.meta, QLabel.small {{
            color: {p['text_secondary']};
        }}

        /* Buttons */
        QPushButton.primary {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {p['primary']}, stop:1 {p['accent']});
            color: white;
            border: none;
            border-radius: 12px;
        }}
        QPushButton.primary:hover {{
            background: {p['accent']};
        }}
        QPushButton {{
            background: {p['surface']};
            color: {p['text_primary']};
            border: 1px solid {p['border']};
            border-radius: 8px;
            padding: 8px 16px;
        }}
        QPushButton:hover {{
            background: {p['surface_alt']};
            border-color: {p['accent']};
        }}
        QPushButton:checked {{
            background: {p['accent']};
            border-color: {p['accent']};
            color: {p['background']};
        }}
        QPushButton:disabled {{
            color: {p['muted']};
            border-color: {p['border']};
        }}

        /* Inputs */
        QLineEdit, QTextEdit, QComboBox {{
            background: {p['surface']};
            color: {p['text_primary']};
            border: 2px solid {p['border']};
            border-radius: 12px;
            padding: 12px 16px;
            selection-background-color: {p['primary']};
        }}
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
            border-color: {p['accent']};
            background: {p['surface']};
        }}

        /* Scroll areas */
        QScrollArea {{
            background: transparent;
            border: none;
        }}
        QScrollArea::viewport {{
            background: {p['background']};
        }}
        /* Nested scroll content */
        QScrollArea QWidget {{
            background: transparent;
        }}

        /* Chips & meta */
        QFrame.metric-chip {{
            background: {p['surface']};
            border: 1px solid {p['border']};
            border-radius: 16px;
            padding: 16px;
        }}

        QLabel.metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: {p['text_primary']};
        }}
        QLabel.metric-label {{
            font-size: 12px;
            color: {p['text_secondary']};
        }}

        /* Progress bars */
        QProgressBar {{
            border: none;
            background: {p['border']};
            border-radius: 10px;
            text-align: center;
            color: {p['text_primary']};
        }}
        QProgressBar::chunk {{
            background: {p['success']};
            border-radius: 10px;
        }}

        /* Navigation */
        QPushButton.nav-item {{
            background: transparent;
            color: {p['text_secondary']};
            border: none;
            border-radius: 12px;
            padding: 12px 16px;
            text-align: left;
            font-size: 14px;
        }}
        QPushButton.nav-item:hover {{
            background: {p.get('row_hover', p['accent'])};
            color: {p['primary']};
        }}

        /* Scrollbars */
        QScrollBar:vertical {{
            background: {p.get('surface_alt', p['background'])};
            width: 8px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: {p.get('scroll_thumb', p['border'])};
            border-radius: 4px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {p.get('scroll_hover', p['text_secondary'])};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
            background: none;
        }}
        """

    def _get_minimal_stylesheet(self):
        """Get minimal fallback stylesheet."""
        p = PennyColors.get_palette("light")
        return f"""
        QMainWindow {{
            background: {p['background']};
            font-family: 'Segoe UI', sans-serif;
            color: {p['text_primary']};
        }}
        QFrame.card {{
            background: {p['surface']};
            border: 1px solid {p['border']};
            border-radius: 12px;
            padding: 16px;
        }}
        """


# Global theme manager instance
theme_manager = ThemeManager()

def get_current_theme():
    """Return the active theme name (light/dark)."""
    return getattr(theme_manager, "current_theme", current_theme)