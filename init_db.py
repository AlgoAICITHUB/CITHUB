import sqlite3

DATABASE = 'app.db'

def get_db_connection(database=DATABASE):
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    tables = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            likes INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            user_id INTEGER,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            bio TEXT,
            photo TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    ]

    for table in tables:
        c.execute(table)

    conn.commit()
    conn.close()
