from flask import Flask, request, render_template, jsonify, redirect,render_template_string, url_for, flash, session
from flask_socketio import SocketIO, emit
from markupsafe import Markup
import sqlite3
import json
import markdown
import os
import subprocess
import io
import sys
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app)
db_initialized = False
db_initialized_c = False
app.secret_key = 'b3c6a398b4ac82e5b5e3040588cbfec57472937775f639f3141d867493400e9a'  # SHA256函數加密

DATABASE = 'app.db'
DATABASEC = 'chat.db'

# Database connection functions
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_db_connection_chat():
    conn = sqlite3.connect(DATABASEC)
    conn.row_factory = sqlite3.Row
    return conn

# Create tables in the database
def create_table():
    conn = sqlite3.connect(DATABASE)
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

def create_chat_sql():
    conn = sqlite3.connect(DATABASEC)
    c = conn.cursor()
    table = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
"""
    c.execute(table)
    conn.commit()
    conn.close()

# Initialize database before request
@app.before_request
def initialize_database():
    global db_initialized, db_initialized_c
    if not db_initialized:
        create_table()
        db_initialized = True
    if not db_initialized_c:
        create_chat_sql()
        db_initialized_c = True

# Route for user login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect("app.db")
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        result = c.fetchone()

        if result:
            session['user_id'] = result['id']
            session['username'] = username
            return redirect(url_for('edit_profile', user_id=result['id']))
        else:
            return render_template("login.html", error="無效的使用者名稱或密碼。")

    return render_template("login.html")

# Route for user registration
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect("app.db")
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        if c.fetchone():
            return "用戶名已存在。"

        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        user_id = c.lastrowid 

        success = """
<!DOCTYPE html>
<html lang="zh-tw">
<head>
    <meta charset="UTF-8">
    <title>註冊成功</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }

        .success-message {
            width: 90%;
            max-width: 400px;
            margin: auto;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            text-align: center;
        }

        h1 {
            color: #4CAF50;
        }

        p {
            color: #666;
            line-height: 1.6;
        }

        a {
            display: inline-block;
            margin-top: 20px;
            padding: 10px 30px;
            background-color: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 5px;
        }

        a:hover {
            background-color: #45a049;
        }
    </style>
</head>
<body>
    <div class="success-message">
        <h1>註冊成功！</h1>
        <p>恭喜您成功註冊。現在您可以使用新的帳戶進行登錄。</p>
        <a href="/login">登錄</a>
    </div>
</body>
</html>
"""

        c.execute("INSERT INTO profiles (user_id, photo, bio) VALUES (?, '', '')", (user_id,))
        conn.commit()

        return render_template_string(success)
    else:
        return render_template("register.html")

# Main route
@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

# Route for uploading files
@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if not session.get('user_id'):
        flash('請先登錄。')
        return redirect(url_for('login'))

    if request.method == "POST":
        title = request.form['title']
        content = request.form['content']
        user_id = session['user_id']

        conn = get_db_connection()
        conn.execute('INSERT INTO posts (user_id, title, content) VALUES (?, ?, ?)', (user_id, title, content))
        conn.commit()
        conn.close()

        return render_template("upload_success.html")

    return render_template("upload.html")

# Route for rendering math template
@app.route("/math", methods=["GET", "POST"])
def math():
    return render_template("lat.html")

# Route for viewing a specific post
@app.route("/view/<int:post_id>")
def view_file(post_id):
    conn = get_db_connection()
    post = conn.execute('SELECT p.id, p.title, p.content, u.username FROM posts p JOIN users u ON p.user_id = u.id WHERE p.id = ?', (post_id,)).fetchone()
    conn.close()

    if post is None:
        flash('帖子未找到。')
        return redirect(url_for('index'))

    html_content = Markup(markdown.markdown(post['content'], extensions=['codehilite', 'fenced_code', 'tables']))

    return render_template("display.html", post=post, content=html_content)

# Route for user profile
@app.route('/profile/<int:user_id>')
def profile(user_id):
    db = get_db_connection()
    user_profile = db.execute('SELECT * FROM profiles WHERE user_id = ?', (user_id,)).fetchone()
    db.close()

    if user_profile and user_profile['bio']:
        profile_bio_html = markdown.markdown(user_profile['bio'], extensions=['codehilite', 'fenced_code', 'tables'])
    else:
        profile_bio_html = "No bio available."

    return render_template('profile.html', profile=user_profile, profile_bio_html=profile_bio_html)

# Route for editing user profile
@app.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    user_id = session.get('user_id')
    if not user_id:
        flash('請先登錄。')
        return redirect(url_for('login'))
    
    db = get_db_connection()
    if request.method == 'POST':
        bio = request.form.get('bio')

        db.execute('UPDATE profiles SET bio = ? WHERE user_id = ?', (bio, user_id))
        db.commit()
        db.close()

        flash('個人資料更新成功！')
        return redirect(url_for('profile', user_id=user_id))

    else:
        profile = db.execute('SELECT * FROM profiles WHERE user_id = ?', (user_id,)).fetchone()
        db.close()

        if not profile:
            flash('未找到指定的個人資料。')
            return redirect(url_for('index'))

        profile_dict = dict(profile) if profile else None

        return render_template('edit_profile.html', profile=profile_dict)

# Route for listing Markdown files
@app.route("/files")
def list_md_files():
    conn = get_db_connection()
    post_rows = conn.execute('''
    SELECT p.id, p.title, p.content, p.created_at, u.username 
    FROM posts p
    JOIN users u ON p.user_id = u.id
    ORDER BY p.created_at DESC
    ''').fetchall()
    conn.close()

    posts = [dict(post) for post in post_rows]  
    
    return render_template('files.html', posts=posts)

# Route for the about page
@app.route('/about', methods=["GET", "POST"])
def about():
    return render_template('about.html')

# Route for the coming soon page
@app.route('/comingsoon', methods=["GET", "POST"])
def comingsoon():
    return render_template("ComingSoon.html")

# Route for creating a new repository
@app.route('/create-repo', methods=['GET','POST'])
def create_repo():
    if request.method == 'POST':
        repo_name = request.form['repo_name']
        license_type = request.form['license_type']
        readme_contents = request.form.get('readme_contents', '')

        repo_path = os.path.join('repositories', repo_name)

        if not os.path.exists(repo_path):
            os.makedirs(repo_path)

        # Initialize git repository
        subprocess.run(['git', 'init', repo_path])

        # Create LICENSE
        if license_type != 'No License':
            with open(os.path.join(repo_path, 'LICENSE'), 'w') as f:
                f.write(f"This is a placeholder for the {license_type} license.")

        # Create README
        if readme_contents:
            with open(os.path.join(repo_path, 'README.md'), 'w') as f:
                f.write(readme_contents)

        return '倉庫創建成功，包含選定的 License 和自定義 README。'
    else:
        return render_template('create_repo.html')

# Route for listing repositories
@app.route('/repos')
def list_repos():
    repo_directory = 'repositories'
    repos = [d for d in os.listdir(repo_directory) if os.path.isdir(os.path.join(repo_directory, d))]
    return render_template('list_repos.html', repos=repos)

# Route for the discussion page
@app.route('/discussion')
def discussion():
    user_id = request.cookies.get('user_id')
    if user_id:
        db = get_db_connection_chat()
        recent_messages = db.execute('SELECT username, message, created_at FROM messages ORDER BY created_at DESC LIMIT 50').fetchall()
        db.close()
        messages = [dict(message) for message in recent_messages]
        return render_template('discussion.html', messages=messages)
    else:
        flash('請先登錄才能進入討論室。')
        return redirect(url_for('login'))

# SocketIO event for sending messages
@socketio.on('send_message')
def handle_send_message_event(data):
    user_id = request.cookies.get('user_id')
    if not user_id:
        return
    user_name = request.cookies.get('user_name', '匿名')
    msg = data['msg']
    
    # Convert Markdown message to HTML
    html_msg = markdown.markdown(msg)
    
    # Store the converted HTML message in the database
    db = get_db_connection_chat()
    db.execute('INSERT INTO messages (user_id, username, message) VALUES (?, ?, ?)', (user_id, user_name, html_msg))
    db.commit()
    db.close()
    
    emit('announce_message', {'user': user_name, 'msg': html_msg}, broadcast=True)

# Route for rendering the slide page
@app.route('/slide')
def slide():
    return render_template('slide.html')

# Route for the coding page
@app.route("/coding")
def coding():
    return render_template("coding.html")

# SocketIO event for executing code
@socketio.on('execute_code')
def handle_code_execution(data):
    code = data['code']

    blacklist = ["open", "exec", "eval", "__import__", "os", "sys"]
    
    if any(keyword in code for keyword in blacklist):
        result = "執行錯誤: 代碼包含不允許的操作。"
        socketio.emit('code_result', {'result': result})
        return
    
    if "for" in code and "in range" in code:
        start_index = code.index("range")
        end_index = code.index(")", start_index)
        range_content = code[start_index:end_index + 1]
        if "1000" not in range_content:
            result = "執行錯誤: for 迴圈次數需小於1000。"
            socketio.emit('code_result', {'result': result})
            return
    
    if "while" in code:
        if "True" in code or "False" in code:
            result = "執行錯誤: while 迴圈應有終止條件。"
            socketio.emit('code_result', {'result': result})
            return

    captured_output = io.StringIO()  
    sys.stdout = captured_output  
    
    try:
        exec(code)
    except Exception as e:
        result = f'執行錯誤: {str(e)}'
    else:
        result = captured_output.getvalue()
    finally:
        sys.stdout = sys.__stdout__  
        socketio.emit('code_result', {'result': result})

if __name__ == "__main__":
    app.run(debug=True)
