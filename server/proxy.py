from http.server import BaseHTTPRequestHandler, HTTPServer
from db import Log, SessionLocal
from urllib.parse import urlparse, parse_qs
import requests

# 🛑 מילות מפתח אסורות
forbidden_keywords = ["porn", "xxx", "vpn", "chatgpt", "darkweb"]

NORMAL_BLACKLIST = [
    "porn", "sex", "xvideos", "xnxx", "redtube", "xhamster", "youporn"
]

STRICT_BLACKLIST = NORMAL_BLACKLIST + [
    "tiktok", "facebook", "instagram", "discord", "chatgpt", "omegle", "4chan"
]


# 🧾 טען blacklist מקובץ חיצוני
def load_blacklist():
    try:
        with open("blacklist.txt", "r", encoding="utf-8") as f:
            return [line.strip().lower() for line in f if line.strip()]
    except Exception as e:
        print(f"⚠️ שגיאה בקריאת blacklist.txt: {e}")
        return []

# 🧾 טען whitelist מקובץ חיצוני
def load_whitelist():
    try:
        with open("whitelist.txt", "r", encoding="utf-8") as f:
            return [line.strip().lower() for line in f if line.strip()]
    except Exception as e:
        print(f"⚠️ שגיאה בקריאת whitelist.txt: {e}")
        return []



# 🔍 בדיקת URL מול blacklist
def is_blocked(url):
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    blacklist = load_blacklist()
    return any(domain in host for domain in blacklist)

# 🔍 בדיקת מילים אסורות ב־path או query
def contains_forbidden_terms(path, query):
    combined = f"{path} {query}".lower()
    return any(term in combined for term in forbidden_keywords)

# 🔍 בדיקת whitelist
def is_whitelisted(url):
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    whitelist = load_whitelist()
    return any(domain in host for domain in whitelist)

# 🧠 מחלקת הפרוקסי
class ProxyHandler(BaseHTTPRequestHandler):
    def _log_request(self, url, result):
        try:
            session = SessionLocal()
            log = Log(url=url, result=result)
            session.add(log)
            session.commit()
            session.close()
            print(f"📝 לוג → {url} → {result}")
        except Exception as e:
            print(f"⚠️ שגיאה בשמירה ללוג: {e}")

    def _serve_blocked_page(self):
        self.send_response(403)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        try:
            with open("blocked.html", "rb") as f:
                self.wfile.write(f.read())
        except Exception as e:
            self.wfile.write(b"<h1>Blocked (no HTML template found)</h1>")

    def do_GET(self):
        if self.path.startswith("http://") or self.path.startswith("https://"):
            url = self.path
        else:
            url = f"http://{self.headers['Host']}{self.path}"

        parsed_url = urlparse(url)
        path = parsed_url.path
        query = parsed_url.query

        print(f"➡️ GET → {url}")
        print(f"📄 Path: {path}")
        print(f"🔍 Query: {query}")

        if is_whitelisted(url):
            print(f"✅ {url} מאושר ב־whitelist")
        elif contains_forbidden_terms(path, query):
            self._serve_blocked_page()
            self._log_request(url, "blocked-keyword")
            return
        elif is_blocked(url):
            self._serve_blocked_page()
            self._log_request(url, "blocked")
            return

        try:
            response = requests.get(
                url,
                headers={"User-Agent": "SafeNetProxy"},
                timeout=5,
                proxies={},
                verify=False,
                allow_redirects=True,
                stream=True
            )
            self.send_response(response.status_code)
            for key, value in response.headers.items():
                if key.lower() != 'transfer-encoding':
                    self.send_header(key, value)
            self.end_headers()
            self.flush_headers()
            for chunk in response.iter_content(1024):
                if chunk:
                    self.wfile.write(chunk)
            self._log_request(url, "allowed")
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(f"שגיאה בפרוקסי: {e}".encode())
            self._log_request(url, "error")

    def do_POST(self):
        if self.path.startswith("http://") or self.path.startswith("https://"):
            url = self.path
        else:
            url = f"http://{self.headers['Host']}{self.path}"

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        parsed_url = urlparse(url)
        path = parsed_url.path
        query = parsed_url.query

        print(f"➡️ POST → {url} | body size: {len(post_data)} bytes")

        if is_whitelisted(url):
            print(f"✅ {url} מאושר ב־whitelist")
        elif contains_forbidden_terms(path, query):
            self._serve_blocked_page()
            self._log_request(url, "blocked-keyword")
            return
        elif is_blocked(url):
            self._serve_blocked_page()
            self._log_request(url, "blocked")
            return

        try:
            headers = {key: self.headers[key] for key in self.headers if key.lower() != 'host'}
            response = requests.post(
                url,
                headers=headers,
                data=post_data,
                timeout=5,
                proxies={},
                verify=False,
                allow_redirects=True,
                stream=True
            )
            self.send_response(response.status_code)
            for key, value in response.headers.items():
                if key.lower() != 'transfer-encoding':
                    self.send_header(key, value)
            self.end_headers()
            self.flush_headers()
            for chunk in response.iter_content(1024):
                if chunk:
                    self.wfile.write(chunk)
            self._log_request(url, "allowed")
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(f"שגיאה בפרוקסי: {e}".encode())
            self._log_request(url, "error")


def run_proxy(port=8888):
    server_address = ('', port)
    httpd = HTTPServer(server_address, ProxyHandler)
    print(f"🚀 |SafeNet Proxy| {port}  טרופ לע ןיזאמ ")
    httpd.serve_forever()

if __name__ == "__main__":
    run_proxy()
