"""
Migration: Add level column to system_logs table and ensure table exists
"""
from database.db_manager import execute_query, fetch_one, connect_db

def add_level_column_to_logs():
    """Add level column to system_logs table if it doesn't exist"""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Check if level column exists
        cursor.execute("PRAGMA table_info(system_logs)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'level' not in columns:
            # Add level column with default 'INFO'
            execute_query("""
                ALTER TABLE system_logs 
                ADD COLUMN level TEXT DEFAULT 'INFO' CHECK(level IN ('INFO', 'WARNING', 'ERROR', 'DEBUG'))
            """, commit=True)
            print("[Migration] Added level column to system_logs table")
        else:
            print("[Migration] Level column already exists")
            
        # Ensure table exists with all required columns
        execute_query("""
            CREATE TABLE IF NOT EXISTS system_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT,
                level TEXT DEFAULT 'INFO' CHECK(level IN ('INFO', 'WARNING', 'ERROR', 'DEBUG')),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
            )
        """, commit=True)
        
    except Exception as e:
        print(f"[Migration] Error checking/adding level column: {e}")
    finally:
        conn.close()

def apply_logging_migration():
    """Apply all logging-related migrations"""
    add_level_column_to_logs()
    print("[Migration] Logging support migration completed")

if __name__ == "__main__":
    apply_logging_migration()

