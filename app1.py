from flask import Flask, request, render_template, jsonify
from markupsafe import Markup
import sqlite3
import json
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.tables import TableExtension
import markdown
import os
app = Flask(__name__)

UPLOAD_FOLDER = r'C:\Gdrive_tudo\spell_training\flaskwebb\mdp'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)



@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        
        # 假設這裡是你的數據庫連接代碼
        # 請確保你的數據庫路徑是正確的
        conn = sqlite3.connect("login.db")
        c = conn.cursor()
        
        # 注意：這裡有 SQL 注入的風險
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        c.execute(query)
        result = c.fetchone()
        
        if result:
            return render_template("dashboard.html")
        else:
            error = "無效的使用者名稱或密碼。"
    
    return render_template("login.html", error=error)



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



if __name__ == "__main__":
    app.run(debug=True)
