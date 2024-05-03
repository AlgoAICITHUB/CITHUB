# database.py
import sqlite3

DATABASE = 'app.db'

def get_db_connection(database=DATABASE):
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = get_db_connection(DATABASE)
    c = conn.cursor()

    tables = [
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        );""",
        """CREATE TABLE IF NOT EXISTS profiles (
            user_id INTEGER PRIMARY KEY,
            photo TEXT,
            bio TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );""",
        """CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            content TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );"""
    ]

    for table in tables:
        c.execute(table)

    conn.commit()
    conn.close()
