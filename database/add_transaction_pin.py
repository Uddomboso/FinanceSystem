"""
Migration script to add transaction_pin column to settings table
Run this once to add the PIN column to existing databases
"""
from database.db_manager import execute_query, fetch_one


def add_transaction_pin_column():
    """Add transaction_pin column to settings table if it doesn't exist"""
    try:
        # Check if column exists by trying to select it
        test_query = fetch_one("SELECT transaction_pin FROM settings LIMIT 1", ())
        print("✅ transaction_pin column already exists")
    except:
        # Column doesn't exist, add it
        try:
            execute_query("""
                ALTER TABLE settings ADD COLUMN transaction_pin TEXT
            """, commit=True)
            print("✅ Added transaction_pin column to settings table")
        except Exception as e:
            print(f"⚠️ Error adding transaction_pin column: {e}")
            print("   Column may already exist or database error occurred")


if __name__ == "__main__":
    add_transaction_pin_column()






