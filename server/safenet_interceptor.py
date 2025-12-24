from mitmproxy import http, ctx
import json
import os
import datetime
import re
import sqlite3
from urllib.parse import parse_qs

# ✅ נתיבי קבצים מתוך הפרויקט שלך
CONFIG_PATH = "config.json"
BLACKLIST_PATH = "blacklist.txt"
WHITELIST_PATH = "whitelist.txt"
BLOCKED_PAGE_PATH = "blocked.html"
TEXT_LOG_FILE = "traffic_log.txt"
SQLITE_DB_FILE = "safenet_logs.db"

# ✅ מילות מפתח עם ניקוד
KEYWORD_WEIGHTS = {
    "porn": 5,
    "xxx": 5,
    "vpn": 3,
    "darkweb": 4,
    "proxy": 3,
    "tor": 4,
    "malware": 5,
    "casino": 3,
    "gambling": 3
}

# ✅ regex לזיהוי base64, tor, jwt וכו’
REGEX_PATTERNS = [
    (re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"), "base64"),
    (re.compile(r"\.onion\b", re.I), "tor_onion"),
    (re.compile(r"\.exe\b", re.I), "exe_download"),
    (re.compile(r"data:application\/octet-stream", re.I), "binary_stream"),
    (re.compile(r"jwt\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+", re.I), "jwt_like")
]

BLOCK_THRESHOLD = 60
WARN_THRESHOLD = 31

# קריאת קבצי config
def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("filter_level", "normal"), config.get("filter_active", False)
    except:
        return "normal", False

def load_blacklist():
    try:
        with open(BLACKLIST_PATH, "r", encoding="utf-8") as f:
            return [line.strip().lower() for line in f if line.strip()]
    except:
        return []

def load_whitelist():
    try:
        with open(WHITELIST_PATH, "r", encoding="utf-8") as f:
            return [line.strip().lower() for line in f if line.strip()]
    except:
        return []

def load_block_page():
    try:
        with open(BLOCKED_PAGE_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "<html><body><h1>האתר נחסם</h1></body></html>"

def log_to_file(url, blocked, reason):
    try:
        with open(TEXT_LOG_FILE, "a", encoding="utf-8") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = "BLOCKED" if blocked else "ALLOWED"
            f.write(f"{timestamp} | {status} {url} | Reason: {reason}\n")
    except:
        pass

def init_db():
    conn = sqlite3.connect(SQLITE_DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT,
            method TEXT,
            host TEXT,
            path TEXT,
            score INTEGER,
            reasons TEXT,
            raw TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_to_db(method, host, path, score, reasons, raw_text):
    conn = sqlite3.connect(SQLITE_DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO logs (ts, method, host, path, score, reasons, raw) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (datetime.datetime.utcnow().isoformat(), method, host, path, score, json.dumps(reasons, ensure_ascii=False), raw_text[:2000]))
    conn.commit()
    conn.close()

# "שיטוח" JSON
def flatten_json(x):
    out = []
    if isinstance(x, dict):
        for k, v in x.items():
            out.append(str(k))
            out += flatten_json(v)
    elif isinstance(x, list):
        for item in x:
            out += flatten_json(item)
    else:
        out.append(str(x))
    return out

# חילוץ טקסט מהבקשה
def extract_request_text(flow: http.HTTPFlow):
    parts = []
    req = flow.request
    try:
        parts.append(" ".join([f"{k}:{v}" for k, v in req.headers.items()]))
    except:
        pass
    try:
        parts.append(req.pretty_url)
    except:
        pass
    try:
        raw = req.get_text(strict=False) or ""
        ctype = req.headers.get("Content-Type", "")
        if "application/json" in ctype:
            try:
                j = json.loads(raw)
                parts.append(" ".join(flatten_json(j)))
            except:
                parts.append(raw)
        elif "application/x-www-form-urlencoded" in ctype or "multipart/form-data" in ctype:
            try:
                parsed = parse_qs(raw)
                parts.append(" ".join([k + " " + " ".join(v) for k, v in parsed.items()]))
            except:
                parts.append(raw)
        else:
            parts.append(raw)
    except:
        pass
    return "\n".join(parts)

def regex_matches(text):
    return [name for pattern, name in REGEX_PATTERNS if pattern.search(text)]

def keywords_score(text):
    text = text.lower()
    total = sum(KEYWORD_WEIGHTS.values())
    found = sum(w for k, w in KEYWORD_WEIGHTS.items() if k in text)
    return min(1.0, found / total) if total else 0

BAD_WORDS = ["porn", "xxx", "malware", "crack", "exploit", "vpn", "proxy"]
GOOD_WORDS = ["login", "profile", "home", "search", "help"]

def ai_score(text):
    text = text.lower()
    bad = sum(text.count(w) for w in BAD_WORDS)
    good = sum(text.count(w) for w in GOOD_WORDS)
    return bad / (bad + good + 1)

def compute_risk_score(text):
    score_regex = min(1.0, len(regex_matches(text)) * 0.5)
    score_kw = keywords_score(text)
    score_ai = ai_score(text)
    combined = 0.45 * score_regex + 0.35 * score_kw + 0.20 * score_ai
    score = int(round(combined * 100))
    reasons = []
    if score_regex > 0:
        reasons.append({"type": "regex", "value": score_regex})
    if score_kw > 0:
        reasons.append({"type": "keywords", "value": score_kw})
    if score_ai > 0:
        reasons.append({"type": "ai", "value": score_ai})
    return score, reasons

# ✅ תוסף הסינון
class SafeNetInterceptor:
    def __init__(self):
        self.block_page = load_block_page()
        self.blacklist = load_blacklist()
        self.whitelist = load_whitelist()
        self.level, self.active = load_config()
        init_db()

    def request(self, flow: http.HTTPFlow) -> None:
        self.blacklist = load_blacklist()
        self.whitelist = load_whitelist()
        self.level, self.active = load_config()
        if not self.active:
            return
        url = flow.request.pretty_url.lower()
        for allowed in self.whitelist:
            if allowed in url:
                log_to_file(url, blocked=False, reason="whitelist")
                return
        effective_blacklist = self.blacklist.copy()
        if self.level == "strict":
            effective_blacklist += ["facebook", "tiktok", "instagram", "discord", "chatgpt", "omegle"]
        body = flow.request.content.lower() if flow.request.content else b""
        for keyword in effective_blacklist + list(KEYWORD_WEIGHTS.keys()):
            if keyword.encode() in url.encode() or keyword.encode() in body:
                flow.response = http.Response.make(
                    403,
                    self.block_page.encode("utf-8"),
                    {"Content-Type": "text/html; charset=utf-8"}
                )
                log_to_file(url, blocked=True, reason=f"keyword:{keyword}")
                log_to_db(flow.request.method, flow.request.host, flow.request.path, 100,
                          [{"type": "blacklist", "value": keyword}], "")
                return

        combined_text = extract_request_text(flow)
        score, reasons = compute_risk_score(combined_text)
        log_to_db(flow.request.method, flow.request.host, flow.request.path, score, reasons, combined_text)

        if score > BLOCK_THRESHOLD:
            flow.response = http.Response.make(
                403,
                self.block_page.encode("utf-8"),
                {"Content-Type": "text/html; charset=utf-8"}
            )
            log_to_file(url, blocked=True, reason=f"risk_score:{score}")
        elif score >= WARN_THRESHOLD:
            flow.request.headers["X-SafeNet-Risk"] = str(score)
            log_to_file(url, blocked=False, reason=f"warn_score:{score}")
        else:
            log_to_file(url, blocked=False, reason=f"risk_score:{score}")

addons = [SafeNetInterceptor()]
