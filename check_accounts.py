"""Quick script to check database contents"""
import sqlite3
import sys
from database.db_manager import connect_db, fetch_all

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

def check_database():
    """Check what's in the database"""
    try:
        # Check users
        users = fetch_all("SELECT user_id, username, email, role FROM users")
        print(f"\nUSERS ({len(users)} found):")
        if users:
            for user in users:
                print(f"  - ID: {user['user_id']}, Username: {user['username']}, Email: {user['email']}, Role: {user['role']}")
        else:
            print("  [WARNING] No users found in database!")
        
        # Check accounts (bank accounts)
        accounts = fetch_all("SELECT id, user_id, account_id, account_type, bank_name FROM accounts")
        print(f"\nBANK ACCOUNTS ({len(accounts)} found):")
        if accounts:
            for acc in accounts:
                print(f"  - ID: {acc['id']}, User ID: {acc['user_id']}, Type: {acc['account_type']}, Bank: {acc['bank_name']}")
        else:
            print("  [WARNING] No bank accounts found in database!")
        
        # Check all tables
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        print(f"\nDATABASE TABLES ({len(tables)}):")
        for table in tables:
            try:
                cursor = connect_db().cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                cursor.connection.close()
                print(f"  - {table}: {count} rows")
            except:
                print(f"  - {table}: (error reading)")
        
    except Exception as e:
        print(f"[ERROR] Error checking database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Checking PennyWise Database...")
    check_database()

