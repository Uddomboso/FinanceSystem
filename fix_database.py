#!/usr/bin/env python3
"""
Database Fix Script
Fixes the schema_version table issue
"""

import sqlite3
import os

def fix_database():
    """Fix the database schema issues"""
    db_path = "pennywise.db"
    
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Fixing database schema...")
        
        # 1. Create schema_version table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Check if settings table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
        settings_exists = cursor.fetchone()
        
        if not settings_exists:
            print("Creating settings table...")
            cursor.execute("""
                CREATE TABLE settings (
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
            """)
            
            # Create index
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_settings_user_id ON settings(user_id)
            """)
        
        # 3. Set schema version to 3
        cursor.execute("""
            INSERT OR REPLACE INTO schema_version (version, updated_at) 
            VALUES (3, CURRENT_TIMESTAMP)
        """)
        
        # 4. Commit changes
        conn.commit()
        
        # 5. Verify the fix
        cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
        version = cursor.fetchone()
        
        if version:
            print(f"Database fixed! Schema version: {version[0]}")
        else:
            print("Failed to set schema version")
            return False
            
        # 6. Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        print(f"Database contains {len(tables)} tables:")
        for table in sorted(table_names):
            print(f"   - {table}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error fixing database: {e}")
        return False

if __name__ == "__main__":
    print("PennyWise Database Fix Script")
    print("=" * 40)
    
    if fix_database():
        print("\nDatabase fix completed successfully!")
        print("You can now run the application normally.")
    else:
        print("\nDatabase fix failed!")
        print("Please check the error messages above.")
