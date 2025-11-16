"""
Migration: Add institution_id and institution_name to accounts table
This migration is safe to run multiple times - it checks if columns exist first
"""

def apply_institution_migration():
    """Add institution_id and institution_name columns to accounts table"""
    import sqlite3
    from database.db_manager import connect_db
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Check if accounts table exists first
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts'")
            if not cursor.fetchone():
                print("[WARN] Accounts table doesn't exist yet, skipping migration")
                conn.close()
                return False
        except Exception as e:
            print(f"[WARN] Could not check for accounts table: {e}")
            conn.close()
            return False
        
        # Check which columns exist by querying table info
        cursor.execute("PRAGMA table_info(accounts)")
        columns = [row[1] for row in cursor.fetchall()]  # Column names are in index 1
        
        has_institution_id = 'institution_id' in columns
        has_institution_name = 'institution_name' in columns
        has_is_primary = 'is_primary' in columns
        
        if has_institution_id and has_institution_name and has_is_primary:
            print("[OK] All institution columns already exist")
            conn.close()
            return True
        
        # Add missing columns
        print("[INFO] Adding missing institution columns...")
        
        if not has_institution_id:
            try:
                cursor.execute("ALTER TABLE accounts ADD COLUMN institution_id TEXT")
                print("  [OK] Added institution_id column")
            except sqlite3.OperationalError as e:
                if "duplicate column" not in str(e).lower():
                    print(f"  [WARN] Could not add institution_id: {e}")
        
        if not has_institution_name:
            try:
                cursor.execute("ALTER TABLE accounts ADD COLUMN institution_name TEXT")
                print("  [OK] Added institution_name column")
            except sqlite3.OperationalError as e:
                if "duplicate column" not in str(e).lower():
                    print(f"  [WARN] Could not add institution_name: {e}")
        
        if not has_is_primary:
            try:
                cursor.execute("ALTER TABLE accounts ADD COLUMN is_primary INTEGER DEFAULT 0")
                print("  [OK] Added is_primary column")
            except sqlite3.OperationalError as e:
                if "duplicate column" not in str(e).lower():
                    print(f"  [WARN] Could not add is_primary: {e}")
        
        # Update existing accounts to have institution_name from bank_name if null
        try:
            cursor.execute("""
                UPDATE accounts 
                SET institution_name = bank_name 
                WHERE institution_name IS NULL AND bank_name IS NOT NULL
            """)
        except Exception as e:
            print(f"  [WARN] Could not update institution_name: {e}")
        
        # Set first checking account as primary if no primary exists
        try:
            cursor.execute("""
                UPDATE accounts 
                SET is_primary = 1 
                WHERE id = (
                    SELECT id FROM accounts 
                    WHERE user_id IN (SELECT DISTINCT user_id FROM accounts)
                    AND account_type = 'salary'
                    AND COALESCE(is_primary, 0) = 0
                    LIMIT 1
                )
            """)
        except Exception as e:
            print(f"  [WARN] Could not set primary account: {e}")
        
        conn.commit()
        conn.close()
        print("[OK] Institution migration completed successfully")
        return True
            
    except Exception as e:
        print(f"[ERROR] Error applying institution migration: {e}")
        import traceback
        traceback.print_exc()
        try:
            conn.close()
        except:
            pass
        return False

if __name__ == "__main__":
    import sqlite3
    apply_institution_migration()

