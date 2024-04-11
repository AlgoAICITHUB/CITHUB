from jinja2 import Template

# 定義模板
template_str = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>每季文章期刊</title>
<style>
  /* Reset CSS */
  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }

  /* Global styles */
  body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    background-color: #f9f9f9;
    color: #333;
    margin: 0;
  }

  .container {
    max-width: 1100px;
    margin: 20px auto;
    padding: 0 20px;
  }

  h1 {
    text-align: center;
    font-size: 2.5em;
    margin-bottom: 30px;
    color: #333;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .article {
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    padding: 30px;
    margin-bottom: 30px;
    transition: box-shadow 0.3s ease;
  }

  .article:hover {
    box-shadow: 0 6px 10px rgba(0, 0, 0, 0.2);
  }

  .article h2 {
    font-size: 1.8em;
    color: #007bff;
    margin-bottom: 20px;
  }

  .article p {
    font-size: 1.2em;
    color: #555;
    line-height: 1.8;
  }

  @media only screen and (max-width: 768px) {
    .article {
      padding: 20px;
    }
    .article h2 {
      font-size: 1.5em;
    }
    .article p {
      font-size: 1em;
    }
  }
  footer {
    background-color: #fff;
   /* color: #CCCCCC;*/
   color: #07edea;
    text-align: center;
    padding: 10px;
    margin-top: 20px;
}
</style>
</head>
<body>

<div class="container">
  <h1>{{ year }}年第{{ quarter }}季文章期刊</h1>
  
  {% for article in articles %}
  <div class="article">
    <h2>{{ article.title }}</h2>
    <p>{{ article.content }}</p>
  </div>
  {% endfor %}
<footer><p>Copyright &copy; 2024 Cithub. All rights reserved.</p></footer>
</div>

</body>
</html>
"""

# 建立Jinja2模板對象
template = Template(template_str)

# 定義文章數據
year = 2024
quarter = "第一"
articles = [
    {"title": "文章標題一", "content": "文章內容一"},
    {"title": "文章標題二", "content": "文章內容二"},
    # 添加更多文章數據
]

# 渲染模板
rendered_html = template.render(year=year, quarter=quarter, articles=articles)

# 將HTML保存到文件或在網頁中顯示
print(rendered_html)
