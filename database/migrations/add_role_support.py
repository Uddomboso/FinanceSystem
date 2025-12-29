"""
Migration: Add role column support and seed admin user
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import bcrypt
from database.db_manager import execute_query, fetch_one, connect_db

def add_role_column_if_missing():
    """Ensure role column exists with default value"""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Check if role column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'role' not in columns:
            # Add role column with default
            execute_query("""
                ALTER TABLE users 
                ADD COLUMN role TEXT NOT NULL DEFAULT 'End User'
            """, commit=True)
            print("[Migration] Added role column to users table")
        else:
            # Ensure default is set for existing rows without role
            execute_query("""
                UPDATE users 
                SET role = 'End User' 
                WHERE role IS NULL OR role = ''
            """, commit=True)
            print("[Migration] Role column already exists, updated NULL values")
    except Exception as e:
        print(f"[Migration] Error checking/adding role column: {e}")
    finally:
        conn.close()

def seed_admin_user():
    """Seed admin user if it doesn't exist"""
    try:
        # Check if admin1 already exists
        admin = fetch_one("SELECT user_id FROM users WHERE email = ?", ("admin1@pw.com",))
        
        if admin:
            # Update existing admin user to ensure correct role
            execute_query("""
                UPDATE users 
                SET role = 'Admin', username = 'admin1'
                WHERE email = ?
            """, ("admin1@pw.com",), commit=True)
            print("[Migration] Admin user already exists, updated role")
            return
        
        # Create admin user
        password = "admin"
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        
        execute_query("""
            INSERT INTO users (email, username, password_hash, role)
            VALUES (?, ?, ?, ?)
        """, ("admin1@pw.com", "admin1", hashed, "Admin"), commit=True)
        
        print("[Migration] Admin user created: admin1@pw.com / admin")
    except Exception as e:
        print(f"[Migration] Error seeding admin user: {e}")

def apply_role_migration():
    """Apply all role-related migrations"""
    add_role_column_if_missing()
    seed_admin_user()
    print("[Migration] Role support migration completed")

if __name__ == "__main__":
    apply_role_migration()

