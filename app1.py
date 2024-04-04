from flask import Flask, request, render_template, jsonify,render_template_string, redirect, url_for, flash,session,make_response
from flask_socketio import SocketIO, emit, join_room, leave_room
from markupsafe import Markup
import sqlite3
import json
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.tables import TableExtension
import markdown
import os
from werkzeug.utils import secure_filename
import subprocess
<<<<<<< HEAD
from datetime import datetime

=======
import io
import sys
from RestrictedPython import safe_builtins, limited_builtins, utility_builtins
from RestrictedPython import compile_restricted
from RestrictedPython.Guards import safe_globals
>>>>>>> 0d6b98685513353f9ccddc40a57e9292edf8ad87

#---------前處理---------
app = Flask(__name__)
socketio = SocketIO(app)
db_initialized = False
db_initialized_c = False
app.secret_key = 'b3c6a398b4ac82e5b5e3040588cbfec57472937775f639f3141d867493400e9a' #SHA256函數加密
UPLOAD_FOLDER = r'mdp' #裝Markdown文件用

if not os.path.exists(UPLOAD_FOLDER): #防爆措施
    os.makedirs(UPLOAD_FOLDER)

DATABASEC = 'chat.db'
# 與DATABASE進行溝通用
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn
def get_db_connection_chat():
    conn = sqlite3.connect(DATABASEC)
    conn.row_factory = sqlite3.Row
    return conn
DATABASE = 'app.db'


# 設定SQL邏輯

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
    print("yes")
#---------網站主函數---------


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


@app.before_request
def initialize_database():
    global db_initialized,db_initialized_c
    if not db_initialized:
        create_table()
        db_initialized = True
    if not db_initialized_c:
        create_chat_sql()
        db_initialized_c = True

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

        # 插入新用戶
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


@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")


@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if not session.get('user_id'):  # 如果用戶未登入，重定向到登入頁面
        flash('請先登錄。')
        return redirect(url_for('login'))

    if request.method == "POST":
        file = request.files["file"]
        if file:
            # 確保文件名是安全的
            filename = secure_filename(file.filename)
            # 儲存文件時加入用戶 ID 作為文件名的一部分
            user_id = session['user_id']  # 從 session 中取得用戶 ID
            save_path = os.path.join(UPLOAD_FOLDER, f"{user_id}_{filename}")
            file.save(save_path)
            return render_template("upload_success.html", filename=filename)
    return render_template("upload.html")

@app.route("/math", methods=["GET", "POST"])
def math():
    return render_template("lat.html")


@app.route("/view/<filename>")
def view_file(filename):
    # 解析出原始的文件名和用戶 ID
    parts = filename.split('_', 1)
    if len(parts) == 2:
        user_id, original_filename = parts
    else:
        # If there aren't two parts, handle the error appropriately
        flash('Invalid filename format.')
        return redirect(url_for('index'))  # Redirect to a safe page

    user_id, original_filename = parts
    markdown_path = os.path.join(UPLOAD_FOLDER, filename)

    if os.path.exists(markdown_path):
        # 從數據庫中獲取用戶名
        conn = get_db_connection()
        user = conn.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()

        if user is None:
            return "User not found."

        with open(markdown_path, 'r', encoding='utf-8') as f:
            markdown_text = f.read()
            html = Markup(markdown.markdown(markdown_text, extensions=['codehilite', 'fenced_code', 'tables']))

        # 將用戶名傳遞給模板
        return render_template("display.html", content=html, username=user['username'], original_filename=original_filename)
    else:
        return "File not found"



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
        return redirect(url_for('profile',user_id=user_id))

    else:
        profile = db.execute('SELECT * FROM profiles WHERE user_id = ?', (user_id,)).fetchone()
        db.close()

        if not profile:
            flash('未找到指定的個人資料。')
            return redirect(url_for('index'))

        profile_dict = dict(profile) if profile else None

        return render_template('edit_profile.html', profile=profile_dict)

@app.route('/about', methods=["GET", "POST"])
def about():
    return render_template('about.html')

@app.route('/comingsoon', methods=["GET", "POST"])
def comingsoon():
    return render_template("ComingSoon.html")

@app.route('/create-repo', methods=['GET','POST'])
def create_repo():
    if request.method == 'POST':
        repo_name = request.form['repo_name']
        license_type = request.form['license_type']
        readme_contents = request.form.get('readme_contents', '')

        repo_path = os.path.join('repositories', repo_name)

        if not os.path.exists(repo_path):
            os.makedirs(repo_path)

        # 初始化 git 倉庫
        subprocess.run(['git', 'init', repo_path])

        # 創建 LICENSE
        if license_type != 'No License':
            with open(os.path.join(repo_path, 'LICENSE'), 'w') as f:
                f.write(f"This is a placeholder for the {license_type} license.")

        # 創建 README
        if readme_contents:
            with open(os.path.join(repo_path, 'README.md'), 'w') as f:
                f.write(readme_contents)

        return '倉庫創建成功，包含選定的 License 和自定義 README。'
    else:
        return render_template('create_repo.html')

@app.route('/repos')
def list_repos():
    repo_directory = 'repositories'
    repos = [d for d in os.listdir(repo_directory) if os.path.isdir(os.path.join(repo_directory, d))]
    return render_template('list_repos.html', repos=repos)

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

@socketio.on('send_message')
def handle_send_message_event(data):
    user_id = request.cookies.get('user_id')
    if not user_id:
        return
    user_name = request.cookies.get('user_name', '匿名')
    msg = data['msg']
    
    # 將Markdown消息轉換為HTML
    html_msg = markdown.markdown(msg)
    
    # 存儲轉換後的HTML消息到數據庫
    db = get_db_connection_chat()
    db.execute('INSERT INTO messages (user_id, username, message) VALUES (?, ?, ?)', (user_id, user_name, html_msg))
    db.commit()
    db.close()
    
    emit('announce_message', {'user': user_name, 'msg': html_msg}, broadcast=True)
@app.route('/slide')
def slide():
    return render_template('slide.html')
<<<<<<< HEAD

@app.route('/files')
def list_md_files():
    # 獲取 UPLOAD_FOLDER 目錄下的所有 .md 文件
    md_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.md')]
    
    # 獲取每個文件的作者和創建時間
    files_info = []
    for filename in md_files:
        # 從文件名中提取用戶 ID
        user_id, _ = filename.split('_', 1)
        user_id = user_id.strip()
        
        # 從資料庫中獲取用戶名稱
        conn = get_db_connection()
        user = conn.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        
        if user:
            # 獲取文件的創建時間
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            created_at = os.path.getmtime(file_path)
            created_at = datetime.fromtimestamp(created_at).strftime('%Y-%m-%d %H:%M:%S')
            
            # 添加到列表
            files_info.append({
                'filename': filename,
                'author': user['username'],
                'created_at': created_at
            })
    
    # 根據創建時間進行排序
    files_info.sort(key=lambda x: x['created_at'], reverse=True)
    
    # 呈現模板並傳遞 files_info 列表
    return render_template('files.html', files=files_info)
=======
@app.route("/coding")
def coding():
    return render_template("coding.html")
@socketio.on('execute_code')
def handle_code_execution(data):
    code = data['code']

    blacklist = ["open", "exec", "eval", "__import__", "os", "sys"]
    

    if any(keyword in code for keyword in blacklist):
        result = "執行錯誤: 代碼包含不允許的操作。"
        socketio.emit('code_result', {'result': result})
        return
    
    if "for" in code and "in range" in code:
        # 檢查 for 迴圈是否在範圍內
        start_index = code.index("range")
        end_index = code.index(")", start_index)
        range_content = code[start_index:end_index + 1]
        if "1000" not in range_content:
            result = "執行錯誤: for 迴圈次數需小於1000。"
            socketio.emit('code_result', {'result': result})
            return
    
    if "while" in code:
        # 檢查 while 迴圈是否有終止條件
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
        # 獲取執行輸出
        result = captured_output.getvalue()
    finally:

        sys.stdout = sys.__stdout__  
        socketio.emit('code_result', {'result': result})


>>>>>>> 0d6b98685513353f9ccddc40a57e9292edf8ad87
if __name__ == "__main__":
    app.run(debug=True)
