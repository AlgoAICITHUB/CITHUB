# FlaskWEB

2024 IZCC Friday放課-- Flask網頁成發。

網頁主題: Cithub 一個輕鬆的學術blog討論社區

## Cithub 一個輕鬆的學術blog討論社區
成員:
- TudoHuang
- Chenya
- A1u
## 作品說明:
自從3月19日進行第一次的init commit以來，我們三個的共同專案正式啟動。起初，我們計劃建立一個什麼都有的網站，但隨著時間的推移和項目進展，我們逐漸地明確了目標，聚焦於打造一個學術討論社區。一個一個的BUG、一個一個的功能使我們的製作之路坎坷，但最後還是作出了這一個完整的作品。
### 使用模組:
- flask
    - Flask, request, render_template, jsonify, render_template_string, redirect, url_for, flash, session, make_response
- flask_socketio
    - SocketIO, emit, join_room, leave_room
- markupsafe
    - Markup
- sqlite3
- json
- markdown
    - CodeHiliteExtension, TableExtension
- os
- werkzeug.utils
    - secure_filename
- subprocess
- datetime
    - datetime
- requests
- dotenv
    - load_dotenv
- time
- logging
- concurrent
    - ThreadPoolExecutor

### Route
- /
- /index
- /register
- /login
- /oauth2callback
- /upload
- /view/<int:post_id>
- /profile/<int:user_id>
- /profilem
= /logout
- /edit_profile
- /files
- /law
- /about
- /comingsoon
- errorhandler(404)
- /forget
### Safety
We made a simple ddos(denial-of-service attack) prevent system to interrupt too many requests from same and different IPs. Also, we used simple technique to stop common SQL injection from stealing our members profile.

## Contributer
感謝所有參與本專案製作的人

<a href="https://github.com/tudohuang/Flaskweb/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=tudohuang/Flaskweb" />
</a>
