import markdown
from flask import Flask, request, render_template
import os
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.tables import TableExtension
app = Flask(__name__)

@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files["file"]
        markdown_text = file.read().decode("utf-8")
        # 確保啟用了代碼高亮和表格的擴展
        html = markdown.markdown(markdown_text, extensions=['codehilite', 'fenced_code', 'tables'])
        return render_template("display.html", content=html)
    return render_template("upload.html")

if __name__ == "__main__":
    app.run(debug=True)
