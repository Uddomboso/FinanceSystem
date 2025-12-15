"""Investigate what happened to the database"""
import sqlite3
import os
from datetime import datetime
from database.db_manager import connect_db, fetch_all

def investigate_database():
    """Check database history and structure"""
    
    db_path = "pennywise.db"
    
    # Check file size and modification time
    if os.path.exists(db_path):
        stat = os.stat(db_path)
        file_size = stat.st_size
        mod_time = datetime.fromtimestamp(stat.st_mtime)
        print(f"Database File: {db_path}")
        print(f"Size: {file_size} bytes ({file_size/1024:.2f} KB)")
        print(f"Last Modified: {mod_time}")
        print()
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Check if there are any deleted records (SQLite keeps some metadata)
        print("=== CHECKING FOR EVIDENCE OF DELETED DATA ===")
        
        # Check users table
        cursor.execute("SELECT COUNT(*) as count FROM users")
        user_count = cursor.fetchone()[0]
        print(f"Users: {user_count}")
        
        # Check accounts table
        cursor.execute("SELECT COUNT(*) as count FROM accounts")
        account_count = cursor.fetchone()[0]
        print(f"Bank Accounts: {account_count}")
        
        # Check if there are foreign key violations (orphaned records)
        cursor.execute("""
            SELECT a.id, a.user_id, a.account_id, u.username 
            FROM accounts a 
            LEFT JOIN users u ON a.user_id = u.user_id
        """)
        orphaned = cursor.fetchall()
        if orphaned:
            print(f"\nFound {len(orphaned)} orphaned account records!")
        
        # Check transactions that might reference accounts
        cursor.execute("SELECT COUNT(*) FROM transactions")
        tx_count = cursor.fetchone()[0]
        print(f"Transactions: {tx_count}")
        
        # Check when users were created
        cursor.execute("SELECT user_id, username, email, created_at, last_login FROM users")
        users = cursor.fetchall()
        print(f"\n=== USER DETAILS ===")
        for user in users:
            print(f"ID: {user[0]}, Username: {user[1]}, Email: {user[2]}")
            print(f"  Created: {user[3]}, Last Login: {user[4]}")
        
        # Check database schema version
        try:
            cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
            version = cursor.fetchone()
            if version:
                print(f"\nDatabase Schema Version: {version[0]}")
        except:
            print("\nSchema version not found")
        
        # Check if database was recently initialized
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"\nTables found: {len(tables)}")
        
        # Check for any logs that might indicate what happened
        try:
            cursor.execute("SELECT COUNT(*) FROM system_logs")
            log_count = cursor.fetchone()[0]
            print(f"System Logs: {log_count} entries")
            
            if log_count > 0:
                cursor.execute("SELECT * FROM system_logs ORDER BY timestamp DESC LIMIT 10")
                logs = cursor.fetchall()
                print("\nRecent System Logs:")
                for log in logs:
                    print(f"  {log}")
        except:
            print("System logs table not accessible")
        
        conn.close()
        
        print("\n=== ANALYSIS ===")
        if account_count == 0 and user_count > 0:
            print("[POSSIBLE CAUSES]")
            print("1. Bank accounts were deleted manually")
            print("2. Database was reset/reinitialized")
            print("3. Foreign key CASCADE deletion occurred")
            print("4. Plaid tokens expired and accounts were removed")
            print("5. Database migration/schema update cleared accounts")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    investigate_database()


