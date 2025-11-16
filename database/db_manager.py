import sqlite3
import os
import sqlite3
from pprint import pprint

import os
print("Using DB:", os.path.abspath("pennywise.db"))

DB_PATH = "pennywise.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("PRAGMA table_info(notifications)")
columns = cur.fetchall()
pprint(columns)
conn.close()


DB_PATH = "pennywise.db"
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db():
    if not os.path.exists(DB_PATH):
        with connect_db() as conn:
            with open(SCHEMA_PATH, "r") as f:
                conn.executescript(f.read())
        print("Database initialized.")
    else:
        print("Database already exists.")


def execute_query(query, params=(), commit=False):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(query, params)
    if commit:
        conn.commit()
    conn.close()
    return cursor


def fetch_all(query, params=()):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return results


def fetch_one(query, params=()):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = cursor.fetchone()
    conn.close()
    return result

def insert_user(email, username, password_hash, role):
    query = '''
    INSERT INTO users (email, username, password_hash, role)
    VALUES (?, ?, ?, ?)
    '''
    execute_query(query, (email, username, password_hash, role), commit=True)


# ... your existing db_manager.py code ...

def insert_user(email, username, password_hash, role):
    query = '''
    INSERT INTO users (email, username, password_hash, role)
    VALUES (?, ?, ?, ?)
    '''
    execute_query(query, (email, username, password_hash, role), commit=True)

# Add this alias to maintain compatibility
init_db = initialize_db


# Add these functions to your existing db_manager.py

def initialize_database_v2():
    """Initialize v2 database features"""
    from database.schema_updates import update_schema,set_schema_version

    current_version = get_schema_version()
    if current_version < 2:
        print("Updating database schema to v2...")
        update_schema()
        set_schema_version(2)
        print("Database updated to v2 schema")

    return True

def initialize_database_v3():
    """Initialize v3 database features with settings support"""
    from database.schema_updates import update_schema_v3, set_schema_version

    try:
        current_version = get_schema_version()
        if current_version < 3:
            print("Updating database schema to v3...")
            update_schema_v3()
            set_schema_version(3)
            print("Database updated to v3 schema with settings support")
        else:
            print("Database already at v3 schema")
    except Exception as e:
        print(f"Schema version check failed, forcing v3 update: {e}")
        update_schema_v3()
        set_schema_version(3)
        print("Database updated to v3 schema with settings support")
    
    # Apply institution migration (always run to ensure columns exist)
    try:
        from database.migrations.add_institution_migration import apply_institution_migration
        apply_institution_migration()
    except Exception as e:
        print(f"Warning: Institution migration failed (may already be applied): {e}")

    return True


def get_schema_version():
    """Get current schema version"""
    try:
        result = fetch_one("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
        return result["version"] if result else 0
    except:
        return 0


