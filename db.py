# db.py
import sqlite3

DATABASE = 'app.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_by_username(username):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return user

def get_user_by_email(email):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return user

def create_user(username, password,email):
    conn = get_db_connection()
    conn.execute("INSERT INTO users (username, password,email) VALUES (?, ?,?)", (username, password,email))
    conn.commit()
    user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return user_id

def create_profile_for_user(user_id):
    conn = get_db_connection()
    conn.execute("INSERT INTO profiles (user_id, bio) VALUES (?, '')", (user_id,))
    conn.commit()
    conn.close()
def validate_user_login(username, password):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
    conn.close()
    return user

def validate_user_email(username, email):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ? AND email = ?", (username, email)).fetchone()
    conn.close()
    return user

def update_user_password(username, password):
    conn = get_db_connection()
    conn.execute("UPDATE users SET password = ? WHERE username = ?", (password, username))
    conn.commit()
    conn.close()
