"""Check database schema to see if it was altered"""
import sqlite3
from database.db_manager import connect_db, fetch_all

def check_schema():
    """Check the current schema structure"""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        print("=== CHECKING ACCOUNTS TABLE SCHEMA ===\n")
        
        # Get the actual structure of accounts table
        cursor.execute("PRAGMA table_info(accounts)")
        columns = cursor.fetchall()
        
        print("ACCOUNTS TABLE STRUCTURE:")
        print("-" * 60)
        for col in columns:
            print(f"Column: {col[1]}")
            print(f"  Type: {col[2]}")
            print(f"  Not Null: {col[3]}")
            print(f"  Default: {col[4]}")
            print(f"  Primary Key: {col[5]}")
            print()
        
        # Check for foreign key constraints
        print("\n=== FOREIGN KEY CONSTRAINTS ===")
        cursor.execute("PRAGMA foreign_key_list(accounts)")
        fks = cursor.fetchall()
        if fks:
            for fk in fks:
                print(f"FK: {fk[3]} -> {fk[2]}.{fk[4]}")
                print(f"  On Delete: {fk[5]}")
                print(f"  On Update: {fk[6]}")
        else:
            print("No foreign keys found")
        
        # Check what the schema.sql expects
        print("\n=== EXPECTED SCHEMA (from schema.sql) ===")
        print("Expected columns:")
        print("  - id (PRIMARY KEY)")
        print("  - user_id (NOT NULL, FK to users)")
        print("  - account_id (NOT NULL, TEXT)")
        print("  - account_type (NOT NULL, CHECK IN ('salary', 'savings'))")
        print("  - bank_name (TEXT)")
        print("  - currency (DEFAULT 'USD')")
        print("  - plaid_token (TEXT)")
        print("  - last_sync (TIMESTAMP)")
        
        # Try to insert a test account to see what happens
        print("\n=== TESTING ACCOUNT INSERTION ===")
        try:
            cursor.execute("""
                INSERT INTO accounts (user_id, account_id, account_type, bank_name, currency)
                VALUES (?, ?, ?, ?, ?)
            """, (1, 'test_account_123', 'salary', 'Test Bank', 'USD'))
            conn.commit()
            print("✓ Test account inserted successfully")
            
            # Check if it appears
            cursor.execute("SELECT * FROM accounts WHERE account_id = ?", ('test_account_123',))
            result = cursor.fetchone()
            if result:
                print(f"✓ Test account found: {dict(result)}")
                # Clean up
                cursor.execute("DELETE FROM accounts WHERE account_id = ?", ('test_account_123',))
                conn.commit()
                print("✓ Test account deleted")
            else:
                print("✗ Test account not found after insert!")
        except Exception as e:
            print(f"✗ Error inserting test account: {e}")
            conn.rollback()
        
        # Check if there are any constraints preventing insertion
        print("\n=== CHECKING CONSTRAINTS ===")
        cursor.execute("PRAGMA table_info(accounts)")
        cols = cursor.fetchall()
        required_cols = []
        for col in cols:
            if col[3] == 1 and col[5] == 0:  # NOT NULL and not PRIMARY KEY
                required_cols.append(col[1])
        print(f"Required columns (NOT NULL): {required_cols}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking schema: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_schema()


