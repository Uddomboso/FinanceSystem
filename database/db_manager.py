import sqlite3
import os

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
        print(" Database initialized.")
    else:
        print("Database already exists.")


def execute_query(query, params=(), commit=False):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if commit:
            conn.commit()
        return cursor


def fetch_all(query, params=()):
    cursor = execute_query(query, params)
    return cursor.fetchall()


def fetch_one(query, params=()):
    cursor = execute_query(query, params)
    return cursor.fetchone()

def insert_user(email, username, password_hash, role):
    query = '''
    INSERT INTO users (email, username, password_hash, role)
    VALUES (?, ?, ?, ?)
    '''
    execute_query(query, (email, username, password_hash, role), commit=True)
