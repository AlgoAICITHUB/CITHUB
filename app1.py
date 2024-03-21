from flask import Flask, request, render_template, jsonify
from markupsafe import Markup
import sqlite3
import torch
import torch.nn as nn
from tensorflow.keras.preprocessing.text import tokenizer_from_json
from tensorflow.keras.preprocessing.sequence import pad_sequences
import json
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.tables import TableExtension
import markdown
import os
app = Flask(__name__)

UPLOAD_FOLDER = r'C:\Gdrive_tudo\spell_training\flaskwebb\mdp'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 模型定義
class TextLSTM(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, num_layers, num_classes):
        super(TextLSTM, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, num_classes)

    def forward(self, x):
        x = self.embedding(x)
        x, _ = self.lstm(x)
        x = x[:, -1, :]
        x = self.fc(x)
        return x

# 加載模型和 tokenizer
with open("tokenizer_config.json") as f:
    tokenizer_data = f.read()
tokenizer = tokenizer_from_json(tokenizer_data)

model = TextLSTM(vocab_size=10000, embed_dim=100, hidden_dim=128, num_layers=2, num_classes=6)
model.load_state_dict(torch.load("lstm.pt", map_location=torch.device('cpu')))
model.eval()

# 預處理函數
def preprocess_data(sentence):
    test_tokenized = tokenizer.texts_to_sequences([sentence])
    test_padded = pad_sequences(test_tokenized, maxlen=171)
    test_padded_tensor = torch.tensor(test_padded, dtype=torch.long)
    return test_padded_tensor

# 預測情緒函數
def predict_emotion(text):
    preprocessed_text = preprocess_data(text)
    with torch.no_grad():
        prediction = model(preprocessed_text)
        predicted_class = torch.argmax(prediction, dim=1)
        result = predicted_class.item()
        emotions = ["Sadness", "Joy", "Love", "Anger", "Fear", "Surprise"]
        return emotions[result]

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

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    text = data.get("text", "")
    emotion = predict_emotion(text)
    return jsonify({"emotion": emotion})

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
