import subprocess
import os
import time
import signal
from flask import Blueprint, jsonify

proxy_bp = Blueprint("proxy_control", __name__)

PROXY_PORT = 8080
SCRIPT_PATH = os.path.abspath("safenet_interceptor.py")
MITMDUMP_PATH = r"C:\Program Files\mitmproxy\bin\mitmdump.exe"  # עדכן אם שונה

mitmproxy_process = None

# --- הפעלת פרוקסי + mitmdump ---
def enable_filtering():
    global mitmproxy_process

    # הגדרת פרוקסי ברמת המשתמש
    subprocess.run([
        "reg", "add",
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings",
        "/v", "ProxyEnable", "/t", "REG_DWORD", "/d", "1", "/f"
    ], check=True)

    subprocess.run([
        "reg", "add",
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings",
        "/v", "ProxyServer", "/t", "REG_SZ", "/d", f"127.0.0.1:{PROXY_PORT}", "/f"
    ], check=True)

    # הפעלת mitmdump אם לא רץ כבר
    if not mitmproxy_process or mitmproxy_process.poll() is not None:
        mitmproxy_process = subprocess.Popen([
            MITMDUMP_PATH,
            "-s", SCRIPT_PATH
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    time.sleep(1)

# --- כיבוי פרוקסי + עצירת mitmdump ---
def disable_filtering():
    global mitmproxy_process

    # כיבוי הפרוקסי
    subprocess.run([
        "reg", "add",
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings",
        "/v", "ProxyEnable", "/t", "REG_DWORD", "/d", "0", "/f"
    ], check=True)

    # עצירת mitmdump אם רץ
    if mitmproxy_process and mitmproxy_process.poll() is None:
        mitmproxy_process.terminate()
        mitmproxy_process.wait(timeout=5)
        mitmproxy_process = None

# --- API הפעלה ---
@proxy_bp.route("/on", methods=["GET"])
def api_enable():
    try:
        enable_filtering()
        return jsonify({"message": "Filtering enabled"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- API כיבוי ---
@proxy_bp.route("/off", methods=["GET"])
def api_disable():
    try:
        disable_filtering()
        return jsonify({"message": "Filtering disabled"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
