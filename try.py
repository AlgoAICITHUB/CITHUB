def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn
conn = get_db_connection()
post = conn.execute('SELECT * FROM  WHERE id = ?', (post_id,)).fetchone()
conn.execute('UPDATE posts SET title = ?, content = ? WHERE id = ?', (title, content, post_id))