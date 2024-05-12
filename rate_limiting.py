from flask import request, jsonify
import time

RATE_LIMIT = 100
TIME_WINDOW = 60
request_count = {}

def rate_limit():
    ip = request.remote_addr
    now = time.time()
    if ip not in request_count:
        request_count[ip] = []

    request_count[ip] = [timestamp for timestamp in request_count[ip] if now - timestamp < TIME_WINDOW]

    if len(request_count[ip]) >= RATE_LIMIT:
        return jsonify({"message": "請求過於頻繁，請稍後再試。"}), 429
    request_count[ip].append(now)

def setup_rate_limiting(app):
    app.before_request(rate_limit)
