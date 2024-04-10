# database.py
import sqlite3

DATABASE = 'app.db'
DATABASEC = 'chat.db'

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
            password TEXT NOT NULL
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

def create_chat_db():
    conn = sqlite3.connect(DATABASEC)
    c = conn.cursor()

    # 創建 users 表（如果需要）
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        );
    """)

    # 創建 messages 表
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    """)

    conn.commit()
    conn.close()