from flask import Flask, render_template_string

app = Flask(__name__)

# HTML模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<title>非常召集通知</title>
<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
</head>
<body>

<h2>點擊按鈕以觸發「非常召集」通知</h2>
<button onclick="triggerAlert()">非常召集</button>

<script>
function triggerAlert() {
    // 使用SweetAlert來模擬像Windows更新那樣的通知彈窗
    Swal.fire({
        title: '非常召集！',
        text: '這是一個緊急通知。',
        icon: 'warning',
        confirmButtonText: '了解'
    });
}
</script>

</body>
</html>
"""

@app.route('/')
def index():
    # 使用render_template_string來渲染HTML模板
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(debug=True)
