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
import init_db
import db
import requests
from dotenv import load_dotenv
import time
import logging
from concurrent.futures import ThreadPoolExecutor

#---------前處理---------
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
db_initialized = False
db_initialized_c = False
app.secret_key = 'b3c6a398b4ac82e5b5e3040588cbfec57472937775f639f3141d867493400e9a' #SHA256函數加密
current_color = "white"
click_count = 0


# 與DATABASE進行溝通用
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

DATABASE = 'app.db'


with app.app_context():
    init_db.create_table()

request_count = {}
RATE_LIMIT = 100  
TIME_WINDOW = 60  

@app.before_request
def rate_limit():
    ip = request.remote_addr
    now = time.time()
    if ip not in request_count:
        request_count[ip] = []

    # 清理過期的時間戳
    request_count[ip] = [timestamp for timestamp in request_count[ip] if now - timestamp < TIME_WINDOW]

    # 檢查當前時間窗口內的請求次數是否超過限制
    if len(request_count[ip]) >= RATE_LIMIT:
        return jsonify({"message": "請求過於頻繁，請稍後再試。"}), 429

    # 增加當前時間戳
    request_count[ip].append(now)
logger = logging.getLogger('async_logger')
logger.setLevel(logging.INFO)
fh = logging.FileHandler('async_app.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

# 創建一個 ThreadPoolExecutor 用於異步日誌記錄
executor = ThreadPoolExecutor(max_workers=2)

def log_message(message):
    logger.info(message)

@app.before_request
def log_request_info():
    # 將日誌記錄任務提交給線程池
    executor.submit(log_message, f"IP: {request.remote_addr}, URL: {request.url}")




#---------網站主函數---------



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        if db.get_user_by_username(username):
            return "用戶名已存在。"

        user_id = db.create_user(username, password,email)
        db.create_profile_for_user(user_id)

        return render_template("register_success.html")
    else:
        return render_template("register.html")
    
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        result = db.validate_user_login(username, password)

        if result:
            session['user_id'] = result['id']
            session['username'] = username
            return redirect(url_for('edit_profile', user_id=result['id']))
        else:
            return render_template("login.html", error="無效的使用者名稱或密碼。")

    return render_template("login.html")

@app.route('/oauth2callback', methods=["GET", "POST"])
def google_account():
    # 向 Google 發送 POST 請求以交換授權碼為訪問令牌
    load_dotenv()
    payload = {
        'client_id': os.getenv('client_id'),
        'client_secret': os.getenv('client_secret'),
        'code': request.args.get('code'),
        'redirect_uri': 'http://127.0.0.1:5000/oauth2callback',
        'grant_type': 'authorization_code'
    }
    response = requests.post("https://oauth2.googleapis.com/token", data=payload)

    # 處理 Google 返回的 JSON 格式的回應
    if response.status_code == 200:
        access_token = response.json()['access_token']
        # 使用 access_token 向 Google 發送請求以獲取使用者資訊
        user_info_response = requests.get('https://www.googleapis.com/oauth2/v1/userinfo', headers={'Authorization': f'Bearer {access_token}'})
        user_info = user_info_response.json()
        username = user_info['name']
        password = user_info['id']
        gmail = user_info['email']
        
        #已經登過（登入）
        if db.get_user_by_username(username):
            result = db.validate_user_login(username, password)
            if result:
                session['user_id'] = result['id']
                session['username'] = username
                return redirect(url_for('edit_profile', user_id=result['id']))
            else:
                return render_template("login.html", error="無效的使用者名稱或密碼。")
        
        #沒登入過（註冊）
        user_id = db.create_user(username, password,gmail)
        db.create_profile_for_user(user_id)

        return render_template("register_success.html")
    else:
        return render_template('404.html'), 404

        
@app.route("/index", methods=["GET", "POST"])
def index():
    user_id = session.get('user_id')
    if user_id == 2:
        return render_template("admin-room.html")
    else:
        return render_template("index.html")
@app.route("/",methods=["GET", "POST"])
def open():
    return render_template("open.html")



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
@app.route('/profilem', methods=['GET','POST'])
def profilem():
    user_id = session.get('user_id')
    return profile(user_id)
@app.route('/logout', methods=['POST','GET'])
def logout():
    session.clear()
    return render_template('logout.html')
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
 


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route("/adminonly", methods=['GET','POST'])
def adminonly():
    user_id = session.get('user_id')
    if user_id == 2 or user_id == 3:
        return render_template('index.html')
    else:
        return render_template_string("""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>Forbidden</title>
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
</head>
<body>
    <script>
    window.onload = function() {
        Swal.fire({
            title: '禁止進入！',
            text: '立即停止您的行為！任何未經授權的進入嘗試都將遭到無上法典的制裁。',
            icon: 'error',
            confirmButtonText: '我已瞭解',
            confirmButtonColor: '#d33', 
        }).then((result) => {
            if (result.value) {
                window.location.href = '/';
            }
        });

    };
    </script>
</body>
</html>
""")


@app.route("/forget", methods=["GET", "POST"])
def forget():
    if request.method == "POST":
        email = request.form["email"]
        username = request.form["username"]
        if db.validate_user_email(username,email):
            return render_template_string(email)
        else:
            return "x"
    return render_template("forget.html")
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
