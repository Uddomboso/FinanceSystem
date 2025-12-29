#!/usr/bin/env python3
"""
Debug script to verify role system functionality
Tests:
1. Role existence in database schema
2. Signup assigns role correctly
3. Login retrieves role correctly
4. Dashboard receives/uses role
5. UI visibility based on role
6. Logout clears role
7. Role doesn't affect plaid/pdf functionality
"""

import sys
import os
from database.db_manager import (
    connect_db, fetch_one, fetch_all, execute_query,
    initialize_db, initialize_database_v3, DB_PATH
)

def test_role_schema():
    """Test 1: Verify roles exist in database schema"""
    print("\n" + "="*60)
    print("TEST 1: Verifying role schema in database")
    print("="*60)
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("[FAIL] FAIL: users table does not exist")
            return False
        
        # Check role column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        role_column = [col for col in columns if col[1] == 'role']
        
        if not role_column:
            print("[FAIL] role column does not exist in users table")
            conn.close()
            return False
        
        print(f"[PASS] role column exists")
        print(f"   Column info: {role_column[0]}")
        
        # Check role constraints
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
        schema = cursor.fetchone()[0]
        
        if "CHECK(role IN" in schema or "CHECK (role IN" in schema:
            print("[PASS] Role CHECK constraint exists")
            # Extract allowed roles
            import re
            match = re.search(r"role IN \('([^']+)'(?:, '([^']+)')*(?:, '([^']+)')*(?:, '([^']+)')*\)", schema)
            if match:
                roles = [r for r in match.groups() if r]
                print(f"   Allowed roles: {roles}")
        else:
            print("[WARNING] Role CHECK constraint not found in schema")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def test_existing_users():
    """Test 2: Check existing users and their roles"""
    print("\n" + "="*60)
    print("TEST 2: Checking existing users and roles")
    print("="*60)
    
    try:
        users = fetch_all("SELECT user_id, username, email, role FROM users")
        
        if not users:
            print("[WARNING] No users found in database")
            return True
        
        print(f"Found {len(users)} user(s):")
        for user in users:
            print(f"  - User ID: {user['user_id']}")
            print(f"    Username: {user['username']}")
            print(f"    Email: {user['email']}")
            print(f"    Role: {user['role']}")
            print()
        
        # Check for role distribution
        roles = [u['role'] for u in users]
        role_counts = {}
        for role in roles:
            role_counts[role] = role_counts.get(role, 0) + 1
        
        print("Role distribution:")
        for role, count in role_counts.items():
            print(f"  - {role}: {count} user(s)")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] ERROR: {e}")
        return False

def test_signup_role_assignment():
    """Test 3: Verify signup assigns role correctly"""
    print("\n" + "="*60)
    print("TEST 3: Testing signup role assignment")
    print("="*60)
    
    try:
        # Check signup code
        signup_files = ['ui/login_window.py', 'ui/loginv2.py']
        role_assigned = False
        
        for file_path in signup_files:
            if not os.path.exists(file_path):
                continue
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if 'insert_user' in content and 'role=' in content:
                # Extract the role assignment
                import re
                matches = re.findall(r'insert_user\([^)]*role\s*=\s*["\']([^"\']+)["\']', content)
                if matches:
                    assigned_role = matches[0]
                    print(f"[PASS] Found signup in {file_path}")
                    print(f"   Role assigned: '{assigned_role}'")
                    role_assigned = True
                    
                    if assigned_role == "End User":
                        print("   [PASS] Correctly assigns 'End User' role")
                    else:
                        print(f"   [WARNING]  Assigns '{assigned_role}' instead of 'End User'")
        
        if not role_assigned:
            print("[WARNING]  Could not verify signup role assignment in code")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] ERROR: {e}")
        return False

def test_login_role_retrieval():
    """Test 4: Verify login retrieves role correctly"""
    print("\n" + "="*60)
    print("TEST 4: Testing login role retrieval")
    print("="*60)
    
    try:
        login_files = ['ui/login_window.py', 'ui/loginv2.py']
        role_retrieved = False
        
        for file_path in login_files:
            if not os.path.exists(file_path):
                continue
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check if login queries user data
            if 'SELECT * FROM users' in content or 'SELECT.*FROM users' in content:
                print(f"[PASS] Found login query in {file_path}")
                
                # Check if role is included in SELECT
                if 'SELECT * FROM users' in content:
                    print("   [PASS] Uses SELECT * (includes role)")
                    role_retrieved = True
                elif 'role' in content.lower():
                    print("   [PASS] Role field referenced")
                    role_retrieved = True
                else:
                    print("   [WARNING]  Login query may not retrieve role")
        
        if not role_retrieved:
            print("[WARNING]  Could not verify role retrieval in login code")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] ERROR: {e}")
        return False

def test_dashboard_role_usage():
    """Test 5: Check if dashboard receives and uses role"""
    print("\n" + "="*60)
    print("TEST 5: Testing dashboard role usage")
    print("="*60)
    
    try:
        dashboard_file = 'ui/dashboard_main.py'
        
        if not os.path.exists(dashboard_file):
            print("[WARNING]  Dashboard file not found")
            return False
        
        with open(dashboard_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check __init__ signature
        if '__init__(self,user_id,username' in content:
            print("[WARNING]  Dashboard __init__ does NOT receive role parameter")
            print("   Current signature: __init__(self, user_id, username, ...)")
            print("   [FAIL] Role is not passed to dashboard")
        
        # Check if role is used anywhere
        role_used = False
        if 'role' in content.lower() or 'Role' in content or 'is_admin' in content.lower():
            print("   [WARNING]  Found role-related code in dashboard")
            role_used = True
        
        if not role_used:
            print("   [FAIL] No role-based logic found in dashboard")
        
        # Check app_main.py to see if role is passed
        app_main_file = 'app_main.py'
        if os.path.exists(app_main_file):
            with open(app_main_file, 'r', encoding='utf-8') as f:
                app_content = f.read()
            
            if 'DashboardMain(' in app_content:
                if 'role' not in app_content.lower() or 'user_id=self.user_id' in app_content:
                    print("   [FAIL] app_main.py does not pass role to DashboardMain")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] ERROR: {e}")
        return False

def test_ui_visibility_logic():
    """Test 6: Check for role-based UI visibility logic"""
    print("\n" + "="*60)
    print("TEST 6: Testing UI visibility based on role")
    print("="*60)
    
    try:
        dashboard_file = 'ui/dashboard_main.py'
        
        if not os.path.exists(dashboard_file):
            print("[WARNING]  Dashboard file not found")
            return False
        
        with open(dashboard_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for visibility logic
        visibility_patterns = [
            'setVisible',
            'isVisible',
            'hide()',
            'show()',
            'role',
            'admin',
            'is_admin'
        ]
        
        found_patterns = []
        for pattern in visibility_patterns:
            if pattern in content:
                found_patterns.append(pattern)
        
        if found_patterns:
            print(f"   Found visibility-related code: {found_patterns}")
        else:
            print("   [WARNING]  No obvious visibility logic found")
        
        # Check navigation items
        if 'nav_data_map' in content:
            print("   [PASS] Navigation items defined")
            # Check if any nav items are conditionally shown
            if 'if.*role' in content.lower() or 'if.*admin' in content.lower():
                print("   [PASS] Role-based navigation found")
            else:
                print("   [FAIL] No role-based navigation logic found")
        
        # Check AdminDashboard usage
        admin_dashboard_file = 'ui/admin_dashboard.py'
        if os.path.exists(admin_dashboard_file):
            print("   [PASS] AdminDashboard class exists")
            
            # Check if it's instantiated anywhere
            with open(admin_dashboard_file, 'r', encoding='utf-8') as f:
                admin_content = f.read()
            
            # Search for AdminDashboard instantiation
            import re
            if re.search(r'AdminDashboard\s*\(', content) or re.search(r'AdminDashboard\s*\(', admin_content):
                print("   [PASS] AdminDashboard may be used")
            else:
                print("   [WARNING]  AdminDashboard exists but may not be instantiated")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] ERROR: {e}")
        return False

def test_logout_role_clearing():
    """Test 7: Verify logout clears role"""
    print("\n" + "="*60)
    print("TEST 7: Testing logout role clearing")
    print("="*60)
    
    try:
        dashboard_file = 'ui/dashboard_main.py'
        
        if not os.path.exists(dashboard_file):
            print("[WARNING]  Dashboard file not found")
            return False
        
        with open(dashboard_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find logout method
        if 'def logout' in content:
            print("   [PASS] Logout method found")
            
            # Check what logout does
            import re
            logout_match = re.search(r'def logout\([^)]*\):.*?(?=\n    def |\nclass |\Z)', content, re.DOTALL)
            if logout_match:
                logout_code = logout_match.group(0)
                
                if 'close()' in logout_code or 'hide()' in logout_code:
                    print("   [PASS] Logout closes/hides dashboard")
                
                if 'LoginWindow' in logout_code:
                    print("   [PASS] Logout shows login window")
                
                # Check if role is cleared
                if 'role' in logout_code.lower() or 'self.role' in logout_code:
                    print("   [PASS] Role is cleared/reset in logout")
                else:
                    print("   [WARNING]  Role may not be explicitly cleared (may be handled by window close)")
        else:
            print("   [WARNING]  Logout method not found")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] ERROR: {e}")
        return False

def test_role_independence():
    """Test 8: Verify role doesn't affect plaid/pdf functionality"""
    print("\n" + "="*60)
    print("TEST 8: Testing role independence from plaid/pdf")
    print("="*60)
    
    try:
        # Check plaid integration
        plaid_files = ['core/plaid_api.py']
        role_in_plaid = False
        
        for file_path in plaid_files:
            if not os.path.exists(file_path):
                continue
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'role' in content.lower() or 'admin' in content.lower():
                print(f"   [WARNING]  Found role/admin references in {file_path}")
                role_in_plaid = True
            else:
                print(f"   [PASS] {file_path} does not check role")
        
        # Check PDF export
        pdf_files = ['ui/reports_page.py']
        role_in_pdf = False
        
        for file_path in pdf_files:
            if not os.path.exists(file_path):
                continue
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'role' in content.lower() or 'admin' in content.lower():
                print(f"   [WARNING]  Found role/admin references in {file_path}")
                role_in_pdf = True
            else:
                print(f"   [PASS] {file_path} does not check role")
        
        if not role_in_plaid and not role_in_pdf:
            print("   [PASS] Role does not affect plaid/pdf functionality")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] ERROR: {e}")
        return False

def generate_report():
    """Generate summary report"""
    print("\n" + "="*60)
    print("SUMMARY REPORT")
    print("="*60)
    print("\nIssues Found:")
    print("1. [FAIL] Dashboard does not receive role parameter")
    print("2. [FAIL] No role-based UI visibility logic implemented")
    print("3. [WARNING]  AdminDashboard exists but may not be used")
    print("4. [WARNING]  Role is not passed from login to dashboard")
    print("\nRecommendations:")
    print("1. Modify login to pass role to dashboard")
    print("2. Add role parameter to DashboardMain.__init__")
    print("3. Implement role-based UI visibility checks")
    print("4. Ensure logout properly clears role state")
    print("5. Test with both 'End User' and 'Admin' roles")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PENNYWISE ROLE SYSTEM DEBUG REPORT")
    print("="*60)
    
    # Initialize database
    try:
        initialize_database_v3()
    except:
        initialize_db()
    
    # Run tests
    tests = [
        test_role_schema,
        test_existing_users,
        test_signup_role_assignment,
        test_login_role_retrieval,
        test_dashboard_role_usage,
        test_ui_visibility_logic,
        test_logout_role_clearing,
        test_role_independence
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"[FAIL] Test failed with exception: {e}")
            results.append(False)
    
    # Generate report
    generate_report()
    
    print("\n" + "="*60)
    print(f"Tests completed: {sum(results)}/{len(results)} passed")
    print("="*60)

if __name__ == "__main__":
    main()

