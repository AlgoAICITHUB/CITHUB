from flask import Flask, request, render_template, jsonify,render_template_string, redirect, url_for, flash,session,make_response,jsonify,send_from_directory
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
import secrets
import string
import rate_limiting
import logging_setup
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_mail import Mail, Message
#---------前處理---------
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
db_initialized = False
db_initialized_c = False
app.secret_key = 'b3c6a398b4ac82e5b5e3040588cbfec57472937775f639f3141d867493400e9a' #SHA256函數加密
current_color = "white"
click_count = 0
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'ttako015@gmail.com'
app.config['MAIL_PASSWORD'] = 'dleo aszx ehqy bvpt'
app.config['SECRET_KEY'] = 'b3c6a398b4ac82e5b5e3040588cbfec57472937775f639f3141d867493400e9a'
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
mail = Mail(app)
# 與DATABASE進行溝通用
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

DATABASE = 'app.db'


with app.app_context():
    init_db.create_table()

rate_limiting.setup_rate_limiting(app)


logging_setup.setup_logging(app)




#---------網站主函數---------



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        if db.get_user_by_username(username):
            error="用戶名已被使用過"
            return render_template("register.html",error=error)
        
        if db.get_user_by_email(email):
            error="電子郵件已被使用過"
            return render_template("register.html",error=error)

        user_id = db.create_user(username, password,email)
        db.create_profile_for_user(user_id)

        return render_template("IN_out/registerOp.html")
    else:
        return render_template("IN_out/register.html")

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
            return render_template("IN_out/login.html", error="無效的使用者名稱或密碼。")

    return render_template("IN_out/login.html")

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
                return render_template("IN_out/login.html", error="無效的使用者名稱或密碼。")
        
        #沒登入過（註冊）
        user_id = db.create_user(username, password,gmail)
        db.create_profile_for_user(user_id)

        return render_template("IN_out/register_success.html")
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

@app.route('/video/<video_name>', methods=["GET"])
def serve_video(video_name):
    video_path = 'static/'
    return send_from_directory(video_path, f"{video_name}.mp4")
@app.route("/regSuc",methods=["GET", "POST"])
def regSuc():
    return render_template("IN_out/register_success.html")

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

        return render_template("post/upload_success.html") 

    return render_template("post/upload.html")

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()

    if post is None:
        flash('文章未找到。')
        return redirect(url_for('list_md_files'))

    if session.get('user_id') != post['user_id']:
        flash('您無權編輯這篇文章。')
        return redirect(url_for('list_md_files'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        conn.execute('UPDATE posts SET title = ?, content = ? WHERE id = ?', (title, content, post_id))
        conn.commit()
        conn.close()
        flash('文章更新成功！')
        return redirect(url_for('list_md_files'))

    conn.close()
    return render_template('post/edit.html', post=post)

@app.route('/view/<int:post_id>', methods=['GET', 'POST'])
def view_post(post_id):
    conn = get_db_connection()
    post = conn.execute('SELECT p.*, u.username FROM posts p JOIN users u ON p.user_id = u.id WHERE p.id = ?', (post_id,)).fetchone()
    comments = conn.execute('SELECT c.*, u.username FROM comments c JOIN users u ON c.user_id = u.id WHERE c.post_id = ? ORDER BY c.created_at ASC', (post_id,)).fetchall()
    conn.close()

    if post is None:
        flash('帖子未找到。')
        return redirect(url_for('index'))

    if request.method == 'POST':
        content = request.form['content']
        user_id = session.get('user_id')
        if user_id:
            conn = get_db_connection()
            conn.execute('INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)', (post_id, user_id, content))
            conn.commit()
            conn.close()
            flash('評論已添加。')
            return redirect(url_for('view_post', post_id=post_id))
        else:
            flash('請先登錄。')
            return redirect(url_for('login'))

    html_content = Markup(markdown.markdown(post['content'], extensions=['extra', 'codehilite', 'fenced_code', 'tables']))

    return render_template('post/post.html', post=post, content=html_content, comments=comments)


@app.route("/termOfUse")
def termOfUse():
    return render_template('IN_out/term_of_use.html')

@app.route('/profile/<int:user_id>')
def profile(user_id):
    conn = get_db_connection()
    post_rows = conn.execute('''
    SELECT p.id, p.title, p.content, p.created_at, u.username 
    FROM posts p
    JOIN users u ON p.user_id = u.id
    WHERE p.user_id = ?
    ORDER BY p.created_at DESC
    ''', (user_id,)).fetchall()
    conn.close()

    posts = [dict(post) for post in post_rows]  
    db = get_db_connection()
    user_profile = db.execute('SELECT * FROM profiles WHERE user_id = ?', (user_id,)).fetchone()
    db.close()

    if user_profile and user_profile['bio']:
        profile_bio_html = markdown.markdown(user_profile['bio'], extensions=['codehilite', 'fenced_code', 'tables'])
    else:
        profile_bio_html = "No bio available."

    return render_template('profile.html', profile=user_profile, profile_bio_html=profile_bio_html, posts=posts)

@app.route('/profilem', methods=['GET','POST'])
def profilem():

    user_id = session.get('user_id')
    return profile(user_id)
@app.route('/logout', methods=['POST','GET'])
def logout():
    session.clear()
    return render_template('IN_out/logout.html')
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
"""
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
"""
@app.route("/files")
def list_md_files():
    query = request.args.get('query', '')
    conn = get_db_connection()
    
    if query:
        post_rows = conn.execute('''
        SELECT p.id, p.title, p.content, p.created_at, u.username 
        FROM posts p
        JOIN users u ON p.user_id = u.id
        WHERE p.title LIKE ?
        ORDER BY p.created_at DESC
        ''', ('%' + query + '%',)).fetchall()
    else:
        post_rows = conn.execute('''
        SELECT p.id, p.title, p.content, p.created_at, u.username 
        FROM posts p
        JOIN users u ON p.user_id = u.id
        ORDER BY p.created_at DESC
        ''').fetchall()
    
    conn.close()

    posts = [dict(post) for post in post_rows]  
    
    return render_template('post/files.html', posts=posts, query=query)
@app.route('/law', methods=['GET','POST'])
def law():
    return render_template('law.html')
@app.route('/about', methods=["GET", "POST"])
def about():
    return render_template('about.html')
@app.route('/slide', methods=['GET', "POST"])
def slide():
    return render_template('about_open.html')
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
        input_data = request.form["username_or_email"]

        if '@' in input_data:
            email = input_data
            username = db.get_username_from_email(email)
        else:
            username = input_data
            email = db.get_email_from_username(username)

        if username and email:
            session['username'] = username
            token = s.dumps(email, salt='email-confirm')
            confirm_url = url_for('confirm_email', token=token, _external=True)
            html = render_template_string('''
            <p>Hi {{ username }},</p>
            <p>To reset your password, click the following link:</p>
            <p><a href="{{ confirm_url }}">Reset Password</a></p>
            ''', username=username, confirm_url=confirm_url)
            msg = Message(subject="Password Reset Request",
                          sender=app.config['MAIL_USERNAME'],
                          recipients=[email],
                          html=html)
            mail.send(msg)
            return redirect('/changepassword')
    return render_template("IN_out/forget.html")


@app.route("/changepassword", methods=["GET", "POST"])
def changepassword():
    random_cookie_value = session.get('random_cookie_value')
    verified = request.cookies.get('verified')
    if verified and random_cookie_value and verified == random_cookie_value:
        if request.method == "POST":
            password1 = request.form['password1']
            password2 = request.form['password2']
            if password1 == password2:
                username = session.get('username')
                db.update_user_password(username, password1)
                resp = delete_cookie()
                return resp
            else:
                alert_message = "密碼不一致!"
                return render_template("change_password.html", alert_message=alert_message)
        return render_template("IN_out/change_password.html")
    else:
        return render_template("IN_out/waitcheck.html")
    
def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

def delete_cookie():
    resp = make_response(redirect('/login'))
    resp.set_cookie('verified', '', expires=0)
    return resp
    
@app.route('/confirm/<token>', methods=["GET"])
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=900)
        text = """
        <h1 style="text-align: center;">Email verified successfully!</h1>
        <br><a href="/changepassword style="text-aling:center">Change Password</a>

        """
        resp = make_response(text)
        random_cookie_value = generate_random_string(30) 
        session['random_cookie_value'] = random_cookie_value  # 將隨機cookie值存儲到會話(session)中
        resp.set_cookie('verified', random_cookie_value, max_age=900)
        
        return resp
    except SignatureExpired:
        return render_template('IN_out/link_expired.html')


#####################################################
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
#2024/5/18
