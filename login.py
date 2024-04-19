from flask import Flask,request,redirect,url_for,render_template,render_template_string,session
import sqlite3 as sql3


app = Flask(__name__)
app.secret_key = "BlingBangBangBlingBangBangBorn"
db = "log.db"
def get_db_connection():
    conn = sql3.connect(db)
    conn.row_factory = sql3.Row
    return conn

def validate_user_login(username, password):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
    conn.close()
    return user
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        result = validate_user_login(username, password)
        if result:
            session['user_id'] = result["id"]
            session['user_name'] = username
            return redirect(url_for('Myterriotory.html'))
        else:
            render_template("Log.html")