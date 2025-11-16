"""
Penny's Official Color Palette - Warm, Friendly Financial Colors
"""

class PennyColors:
    """Penny's official color system"""
    
    # Primary Brand Colors
    PRIMARY = "#2563EB"      # Confident sky blue - trust & clarity
    SECONDARY = "#10B981"    # Emerald green - growth & prosperity  
    ACCENT = "#F59E0B"       # Warm gold - Penny's voice & energy
    
    # Neutral Colors
    BACKGROUND = "#F9FAFB"   # Soft cloud white - airy canvas
    SURFACE = "#FFFFFF"      # True white - modern glass look
    TEXT_PRIMARY = "#1F2937" # Cool slate - professional readability
    TEXT_SECONDARY = "#6B7280" # Muted gray - secondary text
    
    # Semantic Colors
    SUCCESS = "#22C55E"      # Vibrant success
    WARNING = "#F59E0B"      # Attention highlight  
    ERROR = "#DC2626"        # Important alerts
    INFO = "#3B82F6"         # Informational
    
    # Penny's Special Colors
    PENNY_VOICE = "#FEF3C7"  # Penny's speech bubble background
    PENNY_BORDER = "#F59E0B" # Penny's speech bubble border
    PENNY_AVATAR = "#FBBF24" # Penny's avatar color
    
    # Chart Colors (Pastel Finance Spectrum)
    CHART_COLORS = [
        "#60A5FA",  # Blue
        "#34D399",  # Green  
        "#FBBF24",  # Amber
        "#F87171",  # Red
        "#A78BFA",  # Purple
        "#2DD4BF",  # Teal
        "#FB923C",  # Orange
        "#C084FC",  # Light purple
    ]
    
    # Gradient Definitions
    GRADIENTS = {
        "primary": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2563EB, stop:1 #1D4ED8)",
        "success": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #10B981, stop:1 #059669)",
        "accent": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F59E0B, stop:1 #D97706)",
        "penny_voice": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FEF3C7, stop:1 #FDE68A)"
    }
    
    @classmethod
    def get_chart_color(cls, index):
        """Get chart color with cycling"""
        return cls.CHART_COLORS[index % len(cls.CHART_COLORS)]