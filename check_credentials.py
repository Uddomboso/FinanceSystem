#!/usr/bin/env python3
"""
Check User Credentials
Shows available users and allows password reset
"""

import sqlite3
import bcrypt

def show_users():
    """Show all users in the database"""
    conn = sqlite3.connect('pennywise.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT user_id, username, email FROM users')
    users = cursor.fetchall()
    
    print('Users in database:')
    print('=' * 60)
    for user in users:
        print(f'User ID: {user["user_id"]}')
        print(f'Username: {user["username"]}')
        print(f'Email: {user["email"]}')
        print('-' * 60)
    
    conn.close()

def reset_password(user_id, new_password):
    """Reset password for a user"""
    conn = sqlite3.connect('pennywise.db')
    cursor = conn.cursor()
    
    # Hash the new password
    password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    
    try:
        cursor.execute('UPDATE users SET password_hash = ? WHERE user_id = ?', 
                      (password_hash, user_id))
        conn.commit()
        print(f'Password reset successfully for user ID {user_id}')
        print(f'New password: {new_password}')
        return True
    except Exception as e:
        print(f'Error resetting password: {e}')
        return False
    finally:
        conn.close()

def main():
    print('PennyWise - User Credentials Manager')
    print('=' * 60)
    
    # Show all users
    show_users()
    
    print('\nOptions:')
    print('1. The email addresses above are what you use to login')
    print('2. If you forgot your password, I can help reset it')
    print('3. You can also create a new account using "Sign Up" in the login window')
    
    # Get user input
    choice = input('\nEnter user ID to reset password (or press Enter to exit): ')
    
    if choice.strip():
        try:
            user_id = int(choice)
            new_password = input('Enter new password: ')
            if new_password:
                reset_password(user_id, new_password)
                print(f'\nYou can now login with:')
                conn = sqlite3.connect('pennywise.db')
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT email FROM users WHERE user_id = ?', (user_id,))
                user = cursor.fetchone()
                if user:
                    print(f'Email: {user["email"]}')
                    print(f'Password: {new_password}')
                conn.close()
        except ValueError:
            print('Invalid user ID')
        except Exception as e:
            print(f'Error: {e}')

if __name__ == "__main__":
    main()






