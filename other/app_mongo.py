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
import init_mongo

import requests
from dotenv import load_dotenv
from bson.objectid import ObjectId
from pymongo import MongoClient
#---------前處理---------
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
db_initialized = False
db_initialized_c = False
app.secret_key = 'b3c6a398b4ac82e5b5e3040588cbfec57472937775f639f3141d867493400e9a' #SHA256函數加密
current_color = "white"
click_count = 0
DATABASE = 'cithubNever'
uri = "mongodb+srv://tudo:tudo@cluster0.xrxmrc8.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
db = client[DATABASE]

# 與DATABASE進行溝通用




#---------網站主函數---------



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        if init_mongo.get_user_by_username(username):
            return "用戶名已存在。"
        else:
            init_mongo.create_user(username,password,email)
        return render_template("register_success.html")
    else:
        return render_template("register.html")
    
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        result = init_mongo.validate_user_login(username, password)

        if result:
            session['user_id'] = str(result['_id'])
            session['username'] = username
            return redirect(url_for('edit_profile', user_id=str(result['_id'])))
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
        
        #已經登過（登入）
        if init_mongo.get_user_by_username(username):
            result = init_mongo.validate_user_login(username, password)
            if result:
                user_id_str = str(result['_id'])
                session['user_id'] = user_id_str
                session['username'] = username
                return redirect(url_for('edit_profile', user_id=user_id_str))
            else:
                return render_template("login.html", error="無效的使用者名稱或密碼。")
        
        #沒登入過（註冊）
        user_id = init_mongo.create_user(username, password)
        init_mongo.create_profile_for_user(user_id)

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
@app.route("/askew", methods=["GET", "POST"])
def askew():
    return render_template("askew.html")
@app.route("/earthquake", methods=["GET", "POST"])
def earthquake():
    return render_template("earthquake.html")



@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if not session.get('user_id'): 
        flash('請先登錄。')
        return redirect(url_for('login'))

    if request.method == "POST":
        title = request.form['title']
        content = request.form['content']
        user_id = session['user_id'] 
        init_mongo.upload(user_id, title,content)

        return render_template("upload_success.html") 

    return render_template("upload.html")




@app.route("/love", methods=["GET", "POST"])
def love():
    return render_template("love.html")
@app.route("/view/<post_id>")
def view_file(post_id):
    try:
        post = db.posts.find_one({"_id": ObjectId(post_id)}, {'_id': 1, 'title': 1, 'content': 1, 'user_id': 1})
    except:
        post = None  

    if post is None:
        flash('帖子未找到。')
        return redirect(url_for('index'))

    user = db.users.find_one({"_id": post['user_id']}, {'username': 1})
    if user:
        post['username'] = user['username']

    html_content = Markup(markdown.markdown(post['content'], extensions=['codehilite', 'fenced_code', 'tables']))

    return render_template("display.html", post=post, content=html_content)



@app.route('/profile/<user_id>')
def profile(user_id):
    try:
        user_profile = db.profiles.find_one({"user_id": int(user_id)})  # 假設 user_id 存儲為整數
    except:
        user_profile = None

    if user_profile and user_profile.get('bio'):
        profile_bio_html = Markup(markdown.markdown(user_profile['bio'], extensions=['codehilite', 'fenced_code', 'tables']))
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
@app.route('/edit-profile/<user_id>', methods=['GET', 'POST'])
def edit_profile(user_id):
    if not session.get('user_id'):
        flash('請先登錄。')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        bio = request.form.get('bio')
        
        # Update profile bio in MongoDB
        db.profiles.update_one(
            {"user_id": user_id},
            {"$set": {"bio": bio}}
        )
        
        flash('個人資料更新成功！')
        return redirect(url_for('profile', user_id=user_id))
    else:
        profile = db.profiles.find_one({"user_id": user_id})
        
        if not profile:
            flash('未找到指定的個人資料。')
            return redirect(url_for('index'))

        return render_template('edit_profile.html', profile=profile)

    
@app.route("/files")
def list_md_files():
    posts = list(db.posts.find({}).sort("created_at", -1))  # 按創建時間降序排序

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

    return render_template('Pop.html')

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
    return render_template("esp_page.html")



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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)