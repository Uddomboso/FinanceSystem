"""
User Settings and Preferences Management
"""

from database.db_manager import fetch_one, execute_query


class UserSettings:
    """Manage user preferences and settings"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.settings = self.load_settings()
        
    def load_settings(self):
        """Load user settings from database"""
        settings = fetch_one("SELECT * FROM settings WHERE user_id = ?", (self.user_id,))
        if not settings:
            # Create default settings for new user
            settings = self.create_default_settings()
        return settings
        
    def create_default_settings(self):
        """Create default settings for new user"""
        default_settings = {
            'user_id': self.user_id,
            'currency': 'USD',
            'tutorial_completed': 0,  # 0 = not completed, show tutorial
            'notifications_enabled': 1,
            'dark_mode': 0,
            'dashboard_layout': 'simple'  # 'simple' or 'advanced'
        }
        
        # Save to database
        execute_query("""
            INSERT INTO settings (user_id, currency, tutorial_completed, 
                                notifications_enabled, dark_mode, dashboard_layout)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            self.user_id, 'USD', 0, 1, 0, 'simple'
        ), commit=True)
        
        return default_settings
        
    def update_setting(self, key, value):
        """Update a specific setting"""
        self.settings[key] = value
        execute_query(f"""
            UPDATE settings SET {key} = ? WHERE user_id = ?
        """, (value, self.user_id), commit=True)
        
    def should_show_tutorial(self):
        """Check if tutorial should be shown"""
        return not self.settings.get('tutorial_completed', 0)
        
    def complete_tutorial(self):
        """Mark tutorial as completed"""
        self.update_setting('tutorial_completed', 1)
        
    def get_dashboard_layout(self):
        """Get user's preferred dashboard layout"""
        return self.settings.get('dashboard_layout', 'simple')
        
    def set_dashboard_layout(self, layout):
        """Set dashboard layout preference"""
        valid_layouts = ['simple', 'advanced']
        if layout in valid_layouts:
            self.update_setting('dashboard_layout', layout)