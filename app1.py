from flask import Flask, request, render_template, jsonify,render_template_string, redirect, url_for, flash,session
from markupsafe import Markup
import sqlite3
import json
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.tables import TableExtension
import markdown
import os


app = Flask(__name__)
db_initialized = False
app.secret_key = 'b3c6a398b4ac82e5b5e3040588cbfec57472937775f639f3141d867493400e9a'
UPLOAD_FOLDER = r'C:\Gdrive_tudo\spell_training\flaskwebb\mdp'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/login", methods=["GET", "POST"])
def login():
     if request.method == "POST":
         username = request.form['username']
         password = request.form['password']

         conn = sqlite3.connect("app.db")
         conn.row_factory = sqlite3.Row # 使得資料庫查詢結果可以透過列名稱進行訪問
         c = conn.cursor()

         # 使用參數化查詢來防止SQL注入
         c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
         result = c.fetchone()

         if result:
             # 登入成功，將user_id儲存到會話中
             session['user_id'] = result['id']
             print(result['id'])
             # 重定向到儀表板或其他頁面
             return redirect(url_for('profile', user_id=session['user_id']))

         else:
             # 登入失敗，顯示錯誤訊息
             return render_template("login.html", error="無效的使用者名稱或密碼。")

     # 對於GET請求，顯示登入表單
     return render_template("login.html")

DATABASE = 'app.db'

def create_table():
    # 連接到 SQLite 數據庫（如果文件不存在，會自動創建）
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # 創建表的 SQL 命令
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
    
    # 提交更改
    conn.commit()
    
    # 關閉連接
    conn.close()

@app.before_request
def initialize_database():
    global db_initialized
    if not db_initialized:
        create_table()
        db_initialized = True

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect("app.db")
        c = conn.cursor()
        
        # 插入新用戶前，檢查用戶名是否已存在
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        if c.fetchone():
            return "用戶名已存在。"

        # 插入新用戶
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
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
        return render_template_string(success)
    else:
        return render_template("register.html")


@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")
@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files["file"]
        filename = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filename)
        return render_template("upload_success.html", filename=filename)
    return render_template("upload.html")

@app.route("/math", methods=["GET", "POST"])
def math():
    return render_template("lat.html")
@app.route("/view/<filename>")
def view_file(filename):
    markdown_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(markdown_path):
        with open(markdown_path, 'r', encoding='utf-8') as f:
            markdown_text = f.read()
            # 使用 Markdown 庫將 Markdown 文件轉換為 HTML
            html = Markup(markdown.markdown(markdown_text, extensions=['codehilite', 'fenced_code', 'tables']))
            return render_template("display.html", content=html)
    else:
        return "File not found"

@app.route('/profile/<int:user_id>')
def profile(user_id):
    db = get_db_connection()
    user_profile = db.execute('SELECT * FROM profiles WHERE user_id = ?', (user_id,)).fetchone()
    posts = db.execute('SELECT * FROM posts WHERE user_id = ? ORDER BY created_at DESC', (user_id,)).fetchall()
    db.close()
    return render_template('profile.html', profile=user_profile, posts=posts)


@app.route('/edit-profile/<int:user_id>', methods=['GET', 'POST'])
def edit_profile(user_id):
    db = get_db_connection()
    if request.method == 'POST':
        # 假設表單中有照片和自我介紹的字段
        photo = request.form['photo']
        bio = request.form['bio']

        # 更新數據庫中的用戶資料
        db.execute('UPDATE profiles SET photo = ?, bio = ? WHERE user_id = ?', (photo, bio, user_id))
        db.commit()
        db.close()
        flash('個人資料更新成功！')
        return redirect(url_for('profile', user_id=user_id))
    
    # 用 GET 請求獲取當前用戶資料，並顯示在表單中
    profile = db.execute('SELECT * FROM profiles WHERE user_id = ?', (user_id,)).fetchone()
    db.close()
    return render_template('edit_profile.html', profile=profile)


if __name__ == "__main__":
    app.run(debug=True)
