"""Test account insertion to see what's wrong"""
import sqlite3
from database.db_manager import connect_db, fetch_all, execute_query, fetch_one

def test_account_insert():
    """Test if we can insert an account"""
    user_id = 1  # demo user
    
    print("=== TESTING ACCOUNT INSERTION ===\n")
    
    # First check if user exists
    user = fetch_one("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not user:
        print(f"ERROR: User {user_id} doesn't exist!")
        return
    
    print(f"User {user_id} exists: ✓")
    
    # Test account data
    test_account = {
        "account_id": "test_acc_12345",
        "name": "Test Bank Checking",
        "subtype": "checking",
        "balances": {"available": 1000.0, "iso_currency_code": "USD"}
    }
    
    institution_id = "ins_test"
    institution_name = "Test Institution"
    access_token = "access-test-token-123"
    
    # Try the INSERT statement from bank_connect_window.py
    try:
        print("\nTrying INSERT with all columns...")
        q = """
        INSERT INTO accounts (
            user_id, account_id, bank_name, account_type, currency, 
            plaid_token, last_sync, institution_id, institution_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        execute_query(q, (
            user_id,
            test_account["account_id"],
            test_account.get("name", "Unknown Bank"),
            "salary",
            test_account.get("balances", {}).get("iso_currency_code", "USD"),
            access_token,
            "2025-11-20T18:00:00",
            institution_id,
            institution_name
        ), commit=True)
        print("✓ Account inserted successfully!")
        
        # Check if it was saved
        result = fetch_one("""
            SELECT id, account_id, bank_name, account_type, plaid_token 
            FROM accounts 
            WHERE account_id = ? AND user_id = ?
        """, (test_account["account_id"], user_id))
        
        if result:
            print(f"\n✓ Account found in database:")
            print(f"  ID: {result['id']}")
            print(f"  Account ID: {result['account_id']}")
            print(f"  Bank Name: {result['bank_name']}")
            print(f"  Type: {result['account_type']}")
            print(f"  Plaid Token: {result['plaid_token'][:20]}...")
        else:
            print("\n✗ Account NOT found after insert!")
        
        # Now test the SELECT query from dashboard
        print("\n=== TESTING DASHBOARD QUERY ===")
        accounts = fetch_all("""
            SELECT id, account_id, bank_name, account_type, institution_name,
                   is_primary, plaid_token
            FROM accounts 
            WHERE user_id = ? AND plaid_token IS NOT NULL
            AND (account_type = 'salary' OR (account_type = 'savings' AND is_primary = 1))
        """, (user_id,))
        
        print(f"Dashboard query returned {len(accounts)} accounts")
        if accounts:
            for acc in accounts:
                print(f"  - {acc['bank_name']} ({acc['account_type']})")
        else:
            print("  No accounts found!")
        
        # Clean up test account
        execute_query("DELETE FROM accounts WHERE account_id = ?", (test_account["account_id"],), commit=True)
        print("\n✓ Test account cleaned up")
        
    except Exception as e:
        print(f"\n✗ ERROR inserting account: {e}")
        import traceback
        traceback.print_exc()
        
        # Check if institution_logo column exists (might be the issue)
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(accounts)")
        columns = [col[1] for col in cursor.fetchall()]
        conn.close()
        
        print(f"\nColumns in accounts table: {columns}")
        if 'institution_logo' not in columns:
            print("\n⚠️  WARNING: institution_logo column doesn't exist!")
            print("This might cause issues in bank_connect_window.py line 286")

if __name__ == "__main__":
    test_account_insert()


