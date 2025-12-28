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
    
    # #region agent log
    import json
    from datetime import datetime
    try:
        with open(r'c:\Users\asus\OneDrive\Desktop\PennyWise\.cursor\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"location":"font_manager.py:28","message":"apply_font_size called","data":{"size_label":size_label,"valid":size_label in FONT_SIZES},"timestamp":datetime.now().timestamp()*1000,"sessionId":"debug-session","runId":"run1","hypothesisId":"A,D,E"})+'\n')
    except: pass
    # #endregion
    
    # Validate and default to Medium if invalid
    if size_label not in FONT_SIZES:
        size_label = DEFAULT_SIZE
    
    # Update current font size
    _current_font_size = size_label
    
    # Get the font size in points
    size_points = FONT_SIZES[size_label]
    
    # #region agent log
    try:
        with open(r'c:\Users\asus\OneDrive\Desktop\PennyWise\.cursor\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"location":"font_manager.py:45","message":"applying font size","data":{"size_label":size_label,"size_points":size_points,"scale":FONT_SCALES[size_label]},"timestamp":datetime.now().timestamp()*1000,"sessionId":"debug-session","runId":"run1","hypothesisId":"A,D,E"})+'\n')
    except: pass
    # #endregion
    
    # Get the application instance
    app = QApplication.instance()
    if app:
        # Create a new font with the specified size
        font = QFont("Segoe UI", size_points)
        app.setFont(font)
        
        # #region agent log
        try:
            widget_count = len(list(app.allWidgets()))
            with open(r'c:\Users\asus\OneDrive\Desktop\PennyWise\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"location":"font_manager.py:58","message":"updating widgets","data":{"widget_count":widget_count},"timestamp":datetime.now().timestamp()*1000,"sessionId":"debug-session","runId":"run1","hypothesisId":"D,E"})+'\n')
        except: pass
        # #endregion
        
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
    
    # #region agent log
    import json
    from datetime import datetime
    try:
        scale = FONT_SCALES.get(size_label, FONT_SCALES[DEFAULT_SIZE])
        with open(r'c:\Users\asus\OneDrive\Desktop\PennyWise\.cursor\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"location":"font_manager.py:87","message":"get_font_scale called","data":{"size_label":size_label,"scale":scale},"timestamp":datetime.now().timestamp()*1000,"sessionId":"debug-session","runId":"run1","hypothesisId":"A,B,C"})+'\n')
    except: pass
    # #endregion
    
    return FONT_SCALES.get(size_label, FONT_SCALES[DEFAULT_SIZE])

