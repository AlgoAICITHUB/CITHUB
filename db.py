import sqlite3

DATABASE = 'app.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def execute_query(query, args=(), one=False, commit=False):
    with get_db_connection() as conn:
        cursor = conn.execute(query, args)
        if commit:
            conn.commit()
        return cursor.fetchone() if one else cursor.fetchall()

def get_user_by_username(username):
    return execute_query("SELECT * FROM users WHERE username = ?", (username,), one=True)

def get_user_by_email(email):
    return execute_query("SELECT * FROM users WHERE email = ?", (email,), one=True)

def create_user(username, password, email=None):
    if email is None:
        email = "no-email@example.com"  
    conn = get_db_connection()
    conn.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", (username, password, email))
    conn.commit()
    user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return user_id

def create_profile_for_user(user_id):
    execute_query("INSERT INTO profiles (user_id, bio) VALUES (?, '')", (user_id,), commit=True)

def validate_user_login(username, password):
    return execute_query("SELECT * FROM users WHERE username = ? AND password = ?", 
                         (username, password), one=True)

def update_user_password(username, password):
    execute_query("UPDATE users SET password = ? WHERE username = ?", 
                  (password, username), commit=True)

def update_user_profile_photo(user_id, photo):
    execute_query("UPDATE profiles SET photo = ? WHERE user_id = ?", (photo, user_id), commit=True)

def get_username_from_email(email):
    result = execute_query("SELECT username FROM users WHERE email = ?", (email,), one=True)
    return result['username'] if result else None

def get_email_from_username(username):
    result = execute_query("SELECT email FROM users WHERE username = ?", (username,), one=True)
    return result['email'] if result else None
