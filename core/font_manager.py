"""
Font Manager - Global Font Size Control
Provides application-wide font size management
"""

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont


# Font size definitions (base size in points)
FONT_SIZES = {
    "Small": 9,
    "Medium": 11,
    "Large": 13
}

# Font scale factors for scaling existing fonts
FONT_SCALES = {
    "Small": 0.85,
    "Medium": 1.0,
    "Large": 1.15
}

# Default font size
DEFAULT_SIZE = "Medium"

# Current active font size label
_current_font_size = DEFAULT_SIZE


def apply_font_size(size_label):
    """
    Apply font size globally to the application.
    
    Args:
        size_label (str): One of "Small", "Medium", or "Large"
    """
    global _current_font_size
    
    # Validate and default to Medium if invalid
    if size_label not in FONT_SIZES:
        size_label = DEFAULT_SIZE
    
    # Update current font size
    _current_font_size = size_label
    
    # Get the font size in points
    size_points = FONT_SIZES[size_label]
    
    # Get the application instance
    app = QApplication.instance()
    if app:
        # Create a new font with the specified size
        font = QFont("Segoe UI", size_points)
        app.setFont(font)
        
        # Force update all widgets
        for widget in app.allWidgets():
            widget.setFont(font)


def get_font_size(size_label):
    """
    Get the font size in points for a given size label.
    
    Args:
        size_label (str): One of "Small", "Medium", or "Large"
        
    Returns:
        int: Font size in points
    """
    return FONT_SIZES.get(size_label, FONT_SIZES[DEFAULT_SIZE])


def get_font_scale(size_label=None):
    """
    Get the font scale factor for a given size label.
    If no size_label is provided, uses the current active font size.
    
    Args:
        size_label (str, optional): One of "Small", "Medium", or "Large"
        
    Returns:
        float: Font scale factor (0.85 for Small, 1.0 for Medium, 1.15 for Large)
    """
    if size_label is None:
        size_label = _current_font_size
    
    return FONT_SCALES.get(size_label, FONT_SCALES[DEFAULT_SIZE])

