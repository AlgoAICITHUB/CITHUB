from flask import Flask, request, render_template, jsonify,render_template_string, redirect, url_for, flash,session,make_response,jsonify
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
from datetime import datetime
import io
import sys
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect
import bcrypt
#---------前處理---------
app = Flask(__name__)
socketio = SocketIO(app)
db_initialized = False
db_initialized_c = False
app.secret_key = 'b3c6a398b4ac82e5b5e3040588cbfec57472937775f639f3141d867493400e9a' #SHA256函數加密
current_color = "white"
click_count = 0

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

@app.before_request
def initialize_database():
    global db_initialized,db_initialized_c
    if not db_initialized:
        create_table()
        db_initialized = True
    if not db_initialized_c:
        create_chat_sql()
        db_initialized_c = True
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

        c.execute("INSERT INTO profiles (user_id, photo, bio) VALUES (?, '', '')", (user_id,))

        conn.commit()
        return render_template("register_success.html")
    else:
        return render_template("register.html")



@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route("/askew", methods=["GET", "POST"])
def askew():
    return render_template("askew.html")
@app.route("/earthquake", methods=["GET", "POST"])
def earthquake():
    return render_template("earthquake.html")
@app.route("/judge", methods=["GET", "POST"])
def judge():
    return render_template("judge.html")
@app.route("/lawmake", methods=["GET", "POST"])
def lawmake():
    return render_template("lawmake.html")
@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if not session.get('user_id'):  # 如果用戶未登入，重定向到登入頁面
        flash('請先登錄。')
        return redirect(url_for('login'))

    if request.method == "POST":
        title = request.form['title']
        content = request.form['content']
        user_id = session['user_id']  # 從 session 中取得用戶 ID

        # 將帖子資訊保存到資料庫
        conn = get_db_connection()
        conn.execute('INSERT INTO posts (user_id, title, content) VALUES (?, ?, ?)', (user_id, title, content))
        conn.commit()
        conn.close()

        return render_template("upload_success.html")  # 或者其他你想重定向到的頁面

    return render_template("upload.html")


@app.route("/math", methods=["GET", "POST"])
def math():
    return render_template("lat.html")

@app.route("/love", methods=["GET", "POST"])
def love():
    return render_template("love.html")

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

@app.route('/law', methods=['GET','POST'])
def law():
    return render_template('law.html')
@app.route('/about', methods=["GET", "POST"])
def about():
    return render_template('about.html')

@app.route('/comingsoon', methods=["GET", "POST"])
def comingsoon():
    return render_template("ComingSoon.html")
@app.route('/pop', methods=["GET", "POST"])
def pop():
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Click Test</title>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
            <script type="text/javascript">
                document.addEventListener('DOMContentLoaded', function() {
                    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);
                    socket.on('update_count', function(data) {
                        document.getElementById('clickCount').innerHTML = 'Clicks: ' + data.count;
                    });
                    document.getElementById('clickButton').onclick = function() {
                        socket.emit('click');
                    };
                });
            </script>
        </head>
        <body>
            <h1>Click Test</h1>
            <button id="clickButton">Click me!</button>
            <p id="clickCount">Clicks: 0</p>
        </body>
        </html>
    ''')

@socketio.on('click')
def handle_click():
    global click_count
    click_count += 1
    socketio.emit('update_count', {'count': click_count})
@app.route('/esp_feedback', methods=['POST'])
def esp_feedback():
    global click_count
    click_count += 1  
    socketio.emit('update_count', {'count': click_count})
    return jsonify({"success": True})
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


@app.route('/trigger_color', methods=['POST'])
def trigger_color():
    color = request.json.get('color', 'white')  # 默認顏色為白色
    cnt = request.json.get('cnt', 0)  # 默認計數器值為 0
    socketio.emit('update_color', {'color': color, 'cnt': cnt})
    
    return jsonify({"status": "success", "color": color, "cnt": cnt})

@app.route('/esp_page')
def esp_page():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>ESP Control Page</title>
    <style>
        .rainbow {
            background: linear-gradient(90deg, red, orange, yellow, green, blue, indigo, violet);
            color: white; 
            font-size: 72px; 
            text-align: center; 
            padding: 20px;
        }
        //https://stackoverflow.com/questions/56418763/creating-the-perfect-rainbow-gradient-in-css
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script type="text/javascript">
        var socket = io.connect('http://' + document.domain + ':' + location.port);
        console.log(document.domain, location.port)
        socket.on('update_color', function(data) {
            var content = document.getElementById("content");
            if(data.color === "rainbow") {
                content.className = "rainbow";
                content.innerHTML = "42"; // 在彩虹背景下顯示 42
            } else {
                document.body.style.backgroundColor = data.color;
                content.className = "";
                content.innerHTML = ""; // 清空內容
            }
            // 檢查計數器值並顯示警告
            if(data.cnt == 43) {
                alert('還要繼續嗎?你已經解開了宇宙謎團了');
            }
        });

    </script>
</head>
<body>
    <h1>ESP 控制頁面</h1>
    <div id="content" style="height: 100vh;"></div>
</body>
</html>

''')





@app.route("/coding")
def coding():
    return render_template("coding.html")
@app.route("/shop")
def shop():
    return render_template("shop.html")
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

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route("/adminonly", methods=['GET','POST'])
def adminonly():
    return "x"    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
