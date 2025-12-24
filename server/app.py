# --- ייבוא ספריות ---
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from io import BytesIO
from openpyxl import Workbook
from urllib.parse import urlparse

# --- ייבוא רכיבים פנימיים ---
from db import SessionLocal, Log, Setting
from filter_control import enable_filtering, disable_filtering, proxy_bp  # ✅ קובץ שמטפל בהפעלת וכיבוי פרוקסי mitmproxy

# --- יצירת האפליקציה ---
app = Flask(__name__)
app.register_blueprint(proxy_bp, url_prefix="/api/filter")
CORS(app)  # מאפשר קריאות API מדפדפן (react)


# --- אתחול ברירת מחדל של הסינון כפעיל במסד הנתונים ---
def init_settings():
    session = SessionLocal()
    exists = session.query(Setting).filter_by(key="filter_enabled").first()
    if not exists:
        setting = Setting(key="filter_enabled", value="true")
        session.add(setting)
        session.commit()
    session.close()

init_settings()


# --- רשימת חסימות קשיחה לדוגמה ---
blacklist = ["facebook.com", "instagram.com", "tiktok.com"]


# --- בדיקת סטטוס הסינון (האם מופעל או לא) ---
@app.route("/api/status", methods=["GET"])
def get_status():
    session = SessionLocal()
    setting = session.query(Setting).filter_by(key="filter_enabled").first()
    session.close()
    return jsonify({"filter_enabled": setting.value == "true"})


# --- הפעלת/כיבוי סינון דרך כפתור Toggle ---
@app.route("/api/toggle", methods=["POST"])
def toggle_filter():
    session = SessionLocal()
    setting = session.query(Setting).filter_by(key="filter_enabled").first()
    new_value = "false" if setting.value == "true" else "true"
    setting.value = new_value
    session.commit()
    session.close()

    try:
        if new_value == "true":
            enable_filtering()   # ✅ מפעיל mitmproxy
        else:
            disable_filtering()  # ✅ מכבה mitmproxy
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"filter_enabled": new_value == "true"})



# --- בדיקת URL (לשימוש ידני או ע"י טופס) ---
@app.route("/api/check_url", methods=["POST"])
def check_url():
    data = request.get_json()
    url = data.get("url", "")

    if not url:
        return jsonify({"error": "Missing URL"}), 400

    # בדיקה מול רשימת חסימות
    result = "allowed"
    for pattern in blacklist:
        if pattern in url:
            result = "blocked"
            break

    # שמירת הלוג למסד הנתונים
    session = SessionLocal()
    log = Log(url=url, result=result)
    session.add(log)
    session.commit()
    session.close()

    # אם נחסם – החזר דף חסימה
    if result == "blocked":
        return render_template("blocked.html"), 200

    return jsonify({
        "url": url,
        "result": result
    })


# --- קריאת לוגים עם חיפוש, סינון, מיון ועמוד ---
@app.route("/api/logs", methods=["GET"])
def get_logs():
    session = SessionLocal()
    query = session.query(Log)

    # חיפוש לפי טקסט
    search = request.args.get("search", "").strip()
    if search:
        like = f"%{search}%"
        query = query.filter((Log.url.ilike(like)) | (Log.result.ilike(like)))

    # סינון לפי סטטוס
    status = request.args.get("status", "all").lower()
    if status in ["allowed", "blocked"]:
        query = query.filter(Log.result == status)

    # מיון לפי תאריך
    sort = request.args.get("sort", "newest")
    query = query.order_by(Log.timestamp.desc() if sort != "oldest" else Log.timestamp.asc())

    # עימוד
    try:
        page = max(1, int(request.args.get("page", 1)))
        page_size = min(100, max(1, int(request.args.get("page_size", 25))))
    except:
        page, page_size = 1, 25

    total = query.count()
    logs = query.offset((page - 1) * page_size).limit(page_size).all()
    session.close()

    return jsonify({
        "items": [{
            "url": log.url,
            "result": log.result,
            "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        } for log in logs],
        "total": total,
        "page": page,
        "page_size": page_size
    })


# --- מחיקת לוגים לפי סוג ותאריך (רק עם אישור!) ---
@app.route("/api/logs", methods=["DELETE"])
def delete_logs():
    if request.args.get("confirm") != "YES":
        return jsonify({"error": "You must confirm by passing ?confirm=YES"}), 400

    session = SessionLocal()
    query = session.query(Log)

    # מחיקה לפי allowed / blocked
    status = request.args.get("status")
    if status in ["allowed", "blocked"]:
        query = query.filter(Log.result == status)

    # מחיקה עד תאריך מסוים
    before = request.args.get("before")
    if before:
        from datetime import datetime
        try:
            dt = datetime.strptime(before, "%Y-%m-%d")
            query = query.filter(Log.timestamp < dt)
        except ValueError:
            session.close()
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    deleted_count = query.delete(synchronize_session=False)
    session.commit()
    session.close()

    return jsonify({"deleted": deleted_count})


# --- קבלת רמת הסינון הנוכחית ---
@app.route("/api/filter_level", methods=["GET"])
def get_filter_level():
    session = SessionLocal()
    setting = session.query(Setting).filter_by(key="filter_level").first()
    session.close()
    return jsonify({"filter_level": setting.value if setting else "normal"})


# --- עדכון רמת הסינון הנוכחית במסד הנתונים ---
@app.route("/api/filter_level", methods=["POST"])
def set_filter_level():
    data = request.get_json()
    new_level = data.get("level", "normal")

    session = SessionLocal()
    setting = session.query(Setting).filter_by(key="filter_level").first()
    if not setting:
        setting = Setting(key="filter_level", value=new_level)
        session.add(setting)
    else:
        setting.value = new_level
    session.commit()
    session.close()

    return jsonify({"filter_level": new_level})


# --- יצוא לוגים כקובץ אקסל (xlsx) ---
@app.route("/api/logs/export", methods=["GET"])
def export_logs():
    session = SessionLocal()
    logs = session.query(Log).order_by(Log.timestamp.desc()).all()
    session.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Logs"
    ws.append(["URL", "Result", "Timestamp"])

    for log in logs:
        ws.append([log.url, log.result, log.timestamp.strftime("%Y-%m-%d %H:%M:%S")])

    file_stream = BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)

    return send_file(
        file_stream,
        as_attachment=True,
        download_name="logs.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# --- הפעלת השרת ---
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
