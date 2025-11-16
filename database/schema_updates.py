"""
Database schema enhancements for PennyWise v2
"""

from database.db_manager import execute_query, fetch_all, fetch_one

def update_schema():
    """Apply schema updates for v2 features"""
    
    # 1. AI Insights Cache Table
    execute_query("""
        CREATE TABLE IF NOT EXISTS ai_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            insight_text TEXT NOT NULL,
            tone TEXT DEFAULT 'neutral',
            context_hash TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            UNIQUE(user_id, context_hash)
        )
    """, commit=True)
    
    # 2. Demo Scenarios Table
    execute_query("""
        CREATE TABLE IF NOT EXISTS demo_scenarios (
            scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
            scenario_name TEXT NOT NULL,
            scenario_type TEXT NOT NULL, -- 'healthy', 'needs_help', 'savings_challenge'
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """, commit=True)
    
    # 3. Demo Data Cache
    execute_query("""
        CREATE TABLE IF NOT EXISTS demo_data_cache (
            cache_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            data_type TEXT NOT NULL, -- 'accounts', 'transactions', 'budgets'
            scenario_type TEXT NOT NULL,
            json_data TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """, commit=True)
    
    # 4. Add index for better performance
    execute_query("""
        CREATE INDEX IF NOT EXISTS idx_ai_insights_user_context 
        ON ai_insights(user_id, context_hash)
    """)
    
    print("Database schema updated for v2 features")

def get_schema_version():
    """Get current schema version"""
    try:
        # First check if table exists
        result = fetch_one("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'")
        if not result:
            # Table doesn't exist, create it
            execute_query("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """, commit=True)
            return 0
        
        # Table exists, get version
        result = fetch_one("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
        return result["version"] if result else 0
    except Exception as e:
        print(f"Warning: Could not get schema version: {e}")
        return 0

def set_schema_version(version):
    """Set schema version"""
    execute_query("""
        INSERT OR REPLACE INTO schema_version (version) VALUES (?)
    """, (version,), commit=True)


# database/schema_updates.py - ADD THIS

def add_badges_tables():
    """Add badges system tables"""
    execute_query("""
        CREATE TABLE IF NOT EXISTS user_badges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            badge_id TEXT NOT NULL,
            earned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            UNIQUE(user_id, badge_id)
        )
    """,commit=True)

    print("Badges tables created/verified")

def add_settings_table():
    """Add comprehensive settings table for Use Case 5.3.5"""
    execute_query("""
        CREATE TABLE IF NOT EXISTS settings (
            user_id INTEGER PRIMARY KEY,
            dark_mode BOOLEAN DEFAULT 0,
            theme TEXT DEFAULT 'Default',
            language TEXT DEFAULT 'English',
            date_format TEXT DEFAULT 'MM/DD/YYYY',
            currency TEXT DEFAULT 'USD',
            number_format TEXT DEFAULT '1,234.56',
            email_notifications BOOLEAN DEFAULT 1,
            push_notifications BOOLEAN DEFAULT 1,
            notification_frequency TEXT DEFAULT 'Daily',
            auto_save BOOLEAN DEFAULT 1,
            custom_accent_color TEXT DEFAULT '#d6733a',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """, commit=True)
    
    # Add indexes for better performance
    execute_query("""
        CREATE INDEX IF NOT EXISTS idx_settings_user_id ON settings(user_id)
    """)
    
    print("Settings table created/verified")

def update_schema_v3():
    """Update schema to v3 with settings support"""
    # Ensure schema_version table exists first
    execute_query("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """, commit=True)
    
    # Add settings table
    add_settings_table()
    
    # Add any other v3 features here
    print("Database schema updated to v3 with settings support")