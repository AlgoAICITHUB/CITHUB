from flask import (
    Flask, request, render_template, jsonify, render_template_string, 
    redirect, url_for, flash, session, make_response, send_from_directory
)
from flask_socketio import SocketIO, emit, join_room, leave_room
from markupsafe import Markup
import sqlite3
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.tables import TableExtension
import markdown
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import init_db
import db
import requests
from dotenv import load_dotenv
import secrets
import string
import rate_limiting
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_mail import Mail, Message
import subprocess
import uuid
from flask_dance.contrib.github import make_github_blueprint, github
from db import get_db_connection, get_user_by_username, create_user, create_profile_for_user, update_user_profile_photo, validate_user_login
from requests import post, get
basedir = os.path.abspath(os.path.dirname(__file__))


load_dotenv(os.path.join(basedir, '.env'))



#---------前處理---------
# 初始化應用程式和配置
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
DATABASE = 'app.db'
UPLOAD_FOLDER = 'static/uploads'
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
    SECRET_KEY=os.getenv('SECRET_KEY'),
    UPLOAD_FOLDER=UPLOAD_FOLDER
)
load_dotenv()
s = URLSafeTimedSerializer(os.getenv('SECRET_KEY'))
mail = Mail(app)
rate_limiting.setup_rate_limiting(app)

ALLOWED_EXTENSIONS = {"png","jpg","jpeg","gif"}
# 初始化資料庫
with app.app_context():
    init_db.create_table()



# 功能函數
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

def delete_cookie():
    resp = make_response(redirect('/login'))
    resp.set_cookie('verified', '', expires=0)
    return resp

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
#---------網站主函數---------


# Register & Login & Logout

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        if db.get_user_by_username(username):
            return jsonify({'error': '用戶名已被使用過'})
        
        if db.get_user_by_email(email):
            return jsonify({'error': "電子郵件已被使用過"})

        user_id = db.create_user(username, password, email)
        db.create_profile_for_user(user_id)

        return render_template("IN_out/registerOp.html")
    else:
        return render_template("IN_out/register.html")

@app.route("/termOfUse")
def termOfUse():
    return render_template('IN_out/term_of_use.html')
@app.route('/registerOp')
def register_op():
    return render_template('IN_out/registerOp.html')
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
        avatar = user_info['picture']
        print(avatar)
        
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
        db.update_user_profile_photo(user_id,avatar)
        db.create_profile_for_user(user_id)

        return render_template("IN_out/register_success.html")
    else:
        return page_not_found()

@app.route("/github")
def github_login():
    return redirect(f"{GITHUB_AUTH_URL}?client_id={os.getenv('GITHUB_CLIENT_ID')}&redirect_uri=http://127.0.0.1:5000/oauthgitcallback&scope=user,user:email")

@app.route('/oauthgitcallback', methods=["GET", "POST"])
def github_account():
    code = request.args.get('code')
    if not code:
        return "Error: No code provided.", 400

    access_token = exchange_code_for_token(code)
    if not access_token:
        return "Error: Failed to retrieve access token.", 500

    user_info = get_user_info(access_token)
    if not user_info:
        return render_template('404.html'), 404

    username = user_info.get('login')
    password = str(user_info.get('node_id'))
    email = user_info.get('email', 'no-email@example.com')  # Default placeholder
    photo = user_info.get('avatar_url')

    return process_user_login(username, password, email, photo)

def exchange_code_for_token(code):
    payload = {
        'client_id': os.getenv('GITHUB_CLIENT_ID'),
        'client_secret': os.getenv('GITHUB_CLIENT_SECRET'),
        'code': code,
        'redirect_uri': 'http://127.0.0.1:5000/oauthgitcallback'
    }
    headers = {'Accept': 'application/json'}
    response = post(GITHUB_TOKEN_URL, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json().get('access_token')
    return None

def get_user_info(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    response = get(GITHUB_USER_URL, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def process_user_login(username, password, email,photo):
    from db import get_user_by_username, update_user_profile_photo, create_user, create_profile_for_user
    existing_user = get_user_by_username(username)
    if existing_user:
        update_user_profile_photo(existing_user['id'], photo)
        session['user_id'] = existing_user['id']
        session['username'] = username
        return redirect(url_for('edit_profile', user_id=existing_user['id']))
    else:
        user_id = create_user(username, password)
        create_profile_for_user(user_id)
        session['user_id'] = user_id
        session['username'] = username
        return render_template("IN_out/register_success.html")

@app.route("/regSuc",methods=["GET", "POST"])
def regSuc():
    return render_template("IN_out/register_success.html")

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
            html = render_template('reset_password_email.html', username=username, confirm_url=confirm_url)
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
                return render_template("IN_out/change_password.html", alert_message=alert_message)
        return render_template("IN_out/change_password.html")
    else:
        return render_template("IN_out/waitcheck.html")
    

@app.route('/confirm/<token>', methods=["GET"])
def confirm_email(token):
    try:
        #email = s.loads(token, salt='email-confirm', max_age=900)
        resp = make_response(render_template("IN_out/reset_success.html"))
        random_cookie_value = generate_random_string(30) 
        session['random_cookie_value'] = random_cookie_value  # 將隨機cookie值存儲到會話(session)中
        resp.set_cookie('verified', random_cookie_value, max_age=900)
        
        return resp
    except SignatureExpired:
        return render_template('IN_out/link_expired.html')

@app.route('/logout', methods=['POST','GET'])
def logout():
    session.clear()
    return render_template('IN_out/logout.html')

# Profiles

@app.route('/profile/<string:user_name>')
def profile(user_name):
    conn = get_db_connection()

    user_row = conn.execute('SELECT id FROM users WHERE username = ?', (user_name,)).fetchone()
    if not user_row:
        return "User not found", 404
    user_id = user_row['id']

    post_rows = conn.execute('''
    SELECT p.id, p.title, p.content, p.created_at, u.username 
    FROM posts p
    JOIN users u ON p.user_id = u.id
    WHERE p.user_id = ?
    ORDER BY p.created_at DESC
    ''', (user_id,)).fetchall()
    posts = [dict(post) for post in post_rows]

    user_profile = conn.execute('SELECT * FROM profiles WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()

    profile_bio_html = "No bio available."
    user_photo = None
    if user_profile:
        if user_profile['bio']:
            profile_bio_html = markdown.markdown(user_profile['bio'], extensions=['codehilite', 'fenced_code', 'tables'])
        if user_profile['photo']:
            user_photo = user_profile['photo']
        else:
            user_photo = "/static/default_avatar.png"

    return render_template('profile.html', profile=user_profile, profile_bio_html=profile_bio_html, posts=posts, photo=user_photo, username=session.get('username'))


@app.route('/profilem', methods=['GET','POST'])
def profilem():
    user_name = session.get('username')
    return profile(user_name)

@app.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    user_name = session.get('username')
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    db = get_db_connection()
    if request.method == 'POST':
        bio = request.form.get('bio')
        file = request.files.get('file')
        if bio:
            db.execute('UPDATE profiles SET bio = ? WHERE user_id = ?', (bio, user_id))
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            file_url = url_for('static', filename='uploads/' + filename)
            db.execute('UPDATE profiles SET photo = ? WHERE user_id = ?', (file_url, user_id))
        db.commit()
        db.close()
        flash('個人資料更新成功！')
        return redirect(url_for('profile', user_name=user_name))
    else:
        profile = db.execute('SELECT * FROM profiles WHERE user_id = ?', (user_id,)).fetchone()
        db.close()

        if not profile:
            flash('未找到指定的個人資料。')
            return redirect(url_for('index'))

        profile_dict = dict(profile) if profile else None
        return render_template('edit_profile.html', profile=profile_dict)

# Posts

@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if not session.get('user_id'): 
        return redirect(url_for('login'))

    if request.method == "POST":
        title = request.form['title']
        content = request.form['content']
        user_id = session['user_id'] 
        label = request.form['labels']


        conn = get_db_connection()
        conn.execute('INSERT INTO posts (user_id, title, content,label) VALUES (?, ?, ?,?)', (user_id, title, content,label))
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
            return redirect(url_for('login'))

    html_content = Markup(markdown.markdown(post['content'], extensions=['extra', 'codehilite', 'fenced_code', 'tables']))

    return render_template('post/post.html', post=post, content=html_content, comments=comments)

@app.route("/files")
def list_md_files():
    query = request.args.get('query', '')
    labels = request.args.getlist('labels')
    conn = get_db_connection()

    sql_query = '''
    SELECT p.id, p.title, p.content, p.created_at, u.username, COUNT(l.id) as likes
    FROM posts p
    JOIN users u ON p.user_id = u.id
    LEFT JOIN likes l ON p.id = l.post_id
    '''

    params = []
    conditions = []

    if query:
        conditions.append("p.title LIKE ?")
        params.append('%' + query + '%')

    if labels:
        label_conditions = " OR ".join(["p.label LIKE ?" for _ in labels])
        conditions.append(f"({label_conditions})")
        params.extend(['%' + label + '%' for label in labels])

    if conditions:
        sql_query += " WHERE " + " AND ".join(conditions)

    sql_query += '''
    GROUP BY p.id
    ORDER BY p.created_at DESC
    '''


    post_rows = conn.execute(sql_query, params).fetchall()
    conn.close()

    posts = [dict(post) for post in post_rows]

    return render_template('post/files.html', posts=posts, query=query)



@app.route('/like/<int:post_id>', methods=['POST'])
def like_post(post_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT INTO likes (user_id, post_id) VALUES (?, ?)', (user_id, post_id))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # already liked

    cursor.execute('SELECT COUNT(*) as like_count FROM likes WHERE post_id = ?', (post_id,))
    likes = cursor.fetchone()['like_count']
    conn.close()
    
    return jsonify({'likes': likes})

@app.route('/unlike/<int:post_id>', methods=['POST'])
def unlike_post(post_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM likes WHERE user_id = ? AND post_id = ?', (user_id, post_id))
    conn.commit()
    
    cursor.execute('SELECT COUNT(*) as like_count FROM likes WHERE post_id = ?', (post_id,))
    likes = cursor.fetchone()['like_count']
    conn.close()
    
    return jsonify({'likes': likes})

@app.route('/share/<int:post_id>', methods=['POST'])
def share_post(post_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    flash('帖子已成功分享！')
    
    return redirect(url_for('view_post', post_id=post_id))

#Courses
@app.route('/num_courses', methods=['GET', 'POST'])
def num_courses():
    if request.method == 'POST':
        course_name = request.form.get('course_name')
        num_courses = int(request.form.get('num_courses', 0))
        return redirect(url_for('create_course', course_name=course_name, total_lessons=num_courses, lesson_num=1))
    return render_template('num_courses.html')

@app.route('/create_course/<string:course_name>/<int:total_lessons>/<int:lesson_num>', methods=['GET', 'POST'])
def create_course(course_name, total_lessons, lesson_num):
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        question = request.form['question']
        answer = request.form['answer']

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 插入課程資訊
        if lesson_num == 1:
            cursor.execute('INSERT INTO courses (name, description) VALUES (?, ?)', (course_name, ''))
            course_id = cursor.lastrowid
        else:
            course = conn.execute('SELECT id FROM courses WHERE name = ?', (course_name,)).fetchone()
            course_id = course['id']
        
        # 插入課堂內容
        cursor.execute('INSERT INTO lessons (course_id, title, content) VALUES (?, ?, ?)', (course_id, title, content))
        lesson_id = cursor.lastrowid

        # 插入測驗問題
        cursor.execute('INSERT INTO quizzes (lesson_id, question, answer) VALUES (?, ?, ?)', (lesson_id, question, answer))

        conn.commit()
        conn.close()

        # 檢查是否完成所有課堂創建
        if lesson_num < total_lessons:
            return redirect(url_for('create_course', course_name=course_name, total_lessons=total_lessons, lesson_num=lesson_num + 1))
        else:
            return redirect(url_for('view_course', course_name=course_name, lesson_num=1))

    return render_template('create_course.html', course_name=course_name, lesson_num=lesson_num)

@app.route('/view_course/<string:course_name>/<int:lesson_num>')
def view_course(course_name, lesson_num):
    conn = get_db_connection()
    course = conn.execute('SELECT * FROM courses WHERE name = ?', (course_name,)).fetchone()
    if not course:
        return "Course not found", 404

    lesson = conn.execute('SELECT * FROM lessons WHERE course_id = ? LIMIT 1 OFFSET ?', (course['id'], lesson_num - 1)).fetchone()
    quiz = conn.execute('SELECT * FROM quizzes WHERE lesson_id = ?', (lesson['id'],)).fetchone() if lesson else None
    conn.close()

    course_description_markdown = markdown.markdown(course['description'], extensions=['codehilite', 'fenced_code', 'tables'])

    return render_template('course_detail.html', course=course, lesson=lesson, quiz=quiz, course_description_markdown=course_description_markdown, lesson_num=lesson_num)

@app.route('/submit_quiz/<int:course_id>', methods=['POST'])
def submit_quiz(course_id):
    user_id = session.get('user_id')
    if user_id is None:
        return redirect(url_for('login'))

    user_answer = request.form['answer']
    conn = get_db_connection()
    quiz = conn.execute('SELECT * FROM quizzes WHERE lesson_id = ?', (course_id,)).fetchone()
    correct_answer = quiz['answer']
    if user_answer == correct_answer:
        result = "恭喜，您答對了！"
        conn.execute('INSERT OR REPLACE INTO user_progress (user_id, course_id, completed) VALUES (?, ?, ?)', 
                     (user_id, course_id, True))
    else:
        result = "很抱歉，答案錯誤。"
    conn.commit()
    conn.close()
    return render_template('quiz_result.html', result=result, course_id=course_id)

@app.route("/view_courses", methods=["GET", "POST"])
def view_courses():
    conn = get_db_connection()
    courses = conn.execute('SELECT * FROM courses').fetchall()
    conn.close()
    return render_template('courses.html', courses=courses)










# Main
@app.route("/index", methods=["GET", "POST"])
def index():
    user_id = session.get('user_id')
    if user_id:
        conn = get_db_connection()
        user_profile = conn.execute('SELECT photo FROM profiles WHERE user_id = ?', (user_id,)).fetchone()
        conn.close()

        if user_profile and user_profile['photo']:
            user_photo = user_profile['photo']
        else:
            user_photo = "static/default_avatar.png"
        return render_template("index.html", photo=user_photo)
    else:
        user_photo = None

    return render_template("index_open.html")

@app.route("/",methods=["GET", "POST"])
def open():
    return render_template("open.html")

@app.route('/law', methods=['GET','POST'])
def law():
    return render_template('law.html')

@app.route('/privacy', methods=['GET','POST'])
def privacy():
    return render_template('privacy.html')
@app.route('/about', methods=["GET", "POST"])
def about():
    return render_template('about.html')

@app.route('/slide', methods=['GET', "POST"])
def slide():
    return render_template('about_open.html')

@app.route('/countdown', methods=['GET'])
def countdown():
    now = datetime.now()
    target_date = datetime(2025, 1, 18)

    # 計算差異
    difference = target_date - now
    now_time = now.strftime("%Y/%m/%d")
    total_seconds = int(difference.total_seconds())
    days, remainder = divmod(total_seconds, 86400)  
    hours, remainder = divmod(remainder, 3600)  
    minutes, seconds = divmod(remainder, 60)  
    target_time = target_date.strftime("%Y/%m/%d")
    return render_template('countdown.html',now_time=now_time,day=days,hours=hours,minutes=minutes,seconds=seconds,target_time=target_time)

@app.route("/noIn")
def no():
    return render_template("IN_out/wrongx.html")
# Assist
@app.route('/video/<video_name>', methods=["GET"])
def serve_video(video_name):
    video_path = 'static/'
    return send_from_directory(video_path, f"{video_name}.mp4")

@app.route('/comingsoon', methods=["GET", "POST"])
def comingsoon():
    return render_template("ComingSoon.html")
 
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404



#####################################################
if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True,port=5000,host="0.0.0.0")
#2024/5/18
