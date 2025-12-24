from flask import Flask, request, jsonify
import os

app = Flask(__name__)
BLACKLIST_FILE = 'blacklist.txt'


# טוען את רשימת החסימות
def load_blacklist():
    if not os.path.exists(BLACKLIST_FILE):
        return []
    with open(BLACKLIST_FILE, 'r') as f:
        return [line.strip() for line in f if line.strip()]


# שומר רשימה חדשה לקובץ
def save_blacklist(blacklist):
    with open(BLACKLIST_FILE, 'w') as f:
        for item in blacklist:
            f.write(item.strip() + '\n')


# 👉 צפייה ברשימה
@app.route('/api/blacklist', methods=['GET'])
def get_blacklist():
    return jsonify(load_blacklist())


# 👉 הוספה לרשימה
@app.route('/api/blacklist', methods=['POST'])
def add_to_blacklist():
    data = request.json
    url = data.get('url', '').strip()
    if not url:
        return jsonify({'error': 'Missing URL'}), 400

    current = load_blacklist()
    if url in current:
        return jsonify({'message': 'URL already exists'}), 200

    current.append(url)
    save_blacklist(current)
    return jsonify({'message': 'URL added'}), 201


# 👉 מחיקה מרשימת החסימות
@app.route('/api/blacklist', methods=['DELETE'])
def remove_from_blacklist():
    data = request.json
    url = data.get('url', '').strip()
    if not url:
        return jsonify({'error': 'Missing URL'}), 400

    current = load_blacklist()
    if url not in current:
        return jsonify({'message': 'URL not found'}), 404

    current = [item for item in current if item != url]
    save_blacklist(current)
    return jsonify({'message': 'URL removed'}), 200


if __name__ == '__main__':
    app.run(port=5001)
