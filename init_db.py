import sqlite3

conn = sqlite3.connect('login.db')
c = conn.cursor()

# 創建一個使用者表
c.execute('''
    CREATE TABLE users (username TEXT, password TEXT)
''')

# 插入一個示例使用者
c.execute("INSERT INTO users VALUES ('admin', '1234')")

conn.commit()
conn.close()
