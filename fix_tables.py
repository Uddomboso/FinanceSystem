# simple_fix.py
import sqlite3
import os

def create_missing_tables():
    """Create missing database tables"""
    # Direct path to your database
    db_path = "pennywise.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Creating missing tables...")
    
    # Create user_badges table
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_badges (
                user_badge_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                badge_id TEXT NOT NULL,
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created user_badges table")
    except Exception as e:
        print(f"❌ Error creating user_badges: {e}")
    
    # Create savings_goals table
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS savings_goals (
                goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                goal_name TEXT NOT NULL,
                target_amount DECIMAL(10,2) NOT NULL,
                current_amount DECIMAL(10,2) DEFAULT 0,
                target_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_completed BOOLEAN DEFAULT 0,
                progress_percentage DECIMAL(5,2) DEFAULT 0
            )
        """)
        print("✅ Created savings_goals table")
    except Exception as e:
        print(f"❌ Error creating savings_goals: {e}")
    
    conn.commit()
    conn.close()
    print("✅ Database fix completed")

if __name__ == "__main__":
    create_missing_tables()