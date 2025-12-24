"""
Penny's Official Color Palette - Warm, Friendly Financial Colors
"""

class PennyColors:
    """Penny's official color system"""
    
    # Primary Brand Colors
    PRIMARY = "#2563EB"
    SECONDARY = "#10B981"
    ACCENT = "#F59E0B"
    
    # Neutral Colors (Light) — untouched
    BACKGROUND = "#f9f7f5"
    SURFACE = "#FFFFFF"
    TEXT_PRIMARY = "#1F2937"
    TEXT_SECONDARY = "#6B7280"
    
    # Neutral Colors (Dark) — refined
    BACKGROUND_DARK = "#0b1f26"        # main app bg
    SURFACE_DARK = "#132f3a"           # cards
    SURFACE_ALT_DARK = "#102a33"       # sections / rows
    TEXT_PRIMARY_DARK = "#e6f2f6"      # headings / main text
    TEXT_SECONDARY_DARK = "#b7d4df"    # labels / meta
    TEXT_MUTED_DARK = "#8fb3c1"        # muted
    
    # Semantic Colors
    SUCCESS = "#22C55E"
    WARNING = "#F59E0B"
    ERROR = "#DC2626"
    INFO = "#3B82F6"

    # Utility / Dashboard-specific shades
    CTA_GRADIENT = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #d6733a, stop:1 #b45131)"
    CTA_GRADIENT_HOVER = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e6824a, stop:1 #c56141)"
    CTA_PRESSED = "#b45131"
    DASHED_BORDER = "#D1D5DB"
    DASHED_HOVER_BORDER = "#3B82F6"
    DASHED_BG = "#F9FAFB"
    SOFT_PANEL_BG = "#fffaf5"
    SLATE_DARK = "#374151"
    DARK_TEAL_BORDER = "#1e4554"
    LOGO_BG_ACTIVE_LIGHT = "rgba(214, 115, 58, 0.1)"
    LOGO_BG_INACTIVE_LIGHT = "rgba(107, 114, 128, 0.1)"
    LOGO_BG_ACTIVE_DARK = "rgba(37, 150, 190, 0.15)"
    LOGO_BG_INACTIVE_DARK = "rgba(111, 143, 153, 0.18)"
    HIGHLIGHT_BG_ORANGE = "rgba(245, 158, 11, 0.05)"
    HIGHLIGHT_BG_GREEN = "rgba(34, 197, 94, 0.05)"
    MUTED_LILAC = "#D7C6E6"
    # Penny's Special Colors (Dark-safe)
    PENNY_VOICE = "#1a3b46"            # ai banner bg (dark)
    PENNY_BORDER = "#2596be"           # ai accent line
    PENNY_AVATAR = "#2596be"           # ai icon bg
    COMMITMENT_BG = "#183843"
    COMMITMENT_BORDER = "#245160"
    
    # Chart Colors (unchanged)
    CHART_COLORS = [
        "#60A5FA",
        "#34D399",
        "#FBBF24",
        "#F87171",
        "#A78BFA",
        "#2DD4BF",
        "#FB923C",
        "#C084FC",
    ]
    
    # Gradient Definitions (light gradients kept; penny_voice dark-safe)
    GRADIENTS = {
        "primary": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2563EB, stop:1 #1D4ED8)",
        "success": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #10B981, stop:1 #059669)",
        "accent": "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F59E0B, stop:1 #D97706)",
        "penny_voice": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1a3b46, stop:1 #204c5a)"
    }
    
    # Nav colors (light original and dark mapped to palette)
    NAV_LIGHT = {
        "bg": "#e8d2c4",
        "bg_alt": "#e8d2c4",
        "highlight": "#d6733a",
        "highlight_bg": "rgba(214, 115, 58, 0.18)",
        "text_primary": "#704b3b",
        "text_secondary": "#704b3b",
        "text_disabled": "#8c6a59",
        "icon_inactive": "#704b3b",
        "icon_active": "#d6733a",
        "icon_hover": "#d6733a",
        "border": "#e0d3cc",
        "notif_border": "#e7ddd6",
        "logout_hover_border": "#EF4444",
        "logout_hover_bg": "rgba(239, 68, 68, 0.1)",
    }
    
    NAV_DARK = {
        "bg": BACKGROUND_DARK,
        "bg_alt": SURFACE_DARK,
        "highlight": "#2596be",
        "highlight_bg": "rgba(37,150,190,0.08)",
        "text_primary": TEXT_PRIMARY_DARK,
        "text_secondary": TEXT_SECONDARY_DARK,
        "text_disabled": TEXT_MUTED_DARK,
        "icon_inactive": TEXT_SECONDARY_DARK,
        "icon_active": "#2596be",
        "icon_hover": "#3bb0da",
        "border": DARK_TEAL_BORDER,
        "notif_border": DARK_TEAL_BORDER,
        "logout_hover_border": ERROR,
        "logout_hover_bg": "rgba(239,68,68,0.12)",
    }
    
    # Palette dictionaries
    LIGHT = {
        "background": BACKGROUND,
        "surface": SURFACE,
        "surface_alt": "#F3F4F6",
        "text_primary": TEXT_PRIMARY,
        "text_secondary": TEXT_SECONDARY,
        "border": "#E5E7EB",
        "primary": PRIMARY,
        "secondary": SECONDARY,
        "accent": ACCENT,
        "success": SUCCESS,
        "warning": WARNING,
        "error": ERROR,
        "info": INFO,
        "muted": "#9CA3AF",
    }
    
    # Dark — fully aligned with PennyWise dark UI
    DARK = {
        "background": BACKGROUND_DARK,
        "surface": SURFACE_DARK,
        "surface_alt": SURFACE_ALT_DARK,
        "text_primary": TEXT_PRIMARY_DARK,
        "text_secondary": TEXT_SECONDARY_DARK,
        "border": DARK_TEAL_BORDER,
        "primary": "#2596be",
        "secondary": "#27c084",
        "accent": "#2596be",
        "success": "#27c084",
        "warning": "#f6a21a",
        "error": "#ff5c5c",
        "info": "#2596be",
        "muted": TEXT_MUTED_DARK,
        "row_bg": SURFACE_ALT_DARK,
        "row_hover": "rgba(37,150,190,0.08)",
        "scroll_thumb": "#245160",
        "scroll_hover": "#2596be",
        "commitment_bg": COMMITMENT_BG,
        "commitment_border": COMMITMENT_BORDER,
        "ai_bg": PENNY_VOICE,
        "ai_accent": PENNY_BORDER,
    }
    
    @classmethod
    def get_chart_color(cls, index):
        return cls.CHART_COLORS[index % len(cls.CHART_COLORS)]
    
    @classmethod
    def get_palette(cls, name: str):
        name = (name or "light").lower()
        if name == "dark":
            return dict(cls.DARK)
        return dict(cls.LIGHT)