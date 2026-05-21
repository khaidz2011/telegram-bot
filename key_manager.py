# ==================== key_manager.py ====================
# Cài đặt: pip install flask
# Chạy: python key_manager.py

from flask import Flask, request, jsonify, render_template_string
from datetime import datetime, timedelta
import json
import os
import secrets

app = Flask(__name__)

KEYS_FILE = "keys.json"
ADMIN_PASSWORD = "admin123"

def load_keys():
    if os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_keys(keys):
    with open(KEYS_FILE, 'w', encoding='utf-8') as f:
        json.dump(keys, f, ensure_ascii=False, indent=2)

def generate_key():
    return secrets.token_hex(16).upper()

HTML = '''
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quản Lý Key Tool Tài Xỉu</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: linear-gradient(135deg, #1a0a2a, #0a0515);
            font-family: 'Segoe UI', sans-serif;
            min-height: 100vh;
            padding: 20px;
            color: #fff;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { text-align: center; margin-bottom: 30px; background: linear-gradient(135deg, #ff66ff, #00ffff); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .card { background: rgba(0,0,0,0.7); backdrop-filter: blur(10px); border-radius: 20px; padding: 25px; margin-bottom: 20px; border: 1px solid rgba(255,102,255,0.3); }
        .card h2 { margin-bottom: 20px; color: #ff66ff; }
        .input-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; color: #aaa; }
        input, select { width: 100%; padding: 12px; border-radius: 10px; border: 1px solid #ff66ff; background: rgba(0,0,0,0.5); color: #fff; font-size: 16px; }
        button { background: linear-gradient(135deg, #ff66ff, #cc33ff); border: none; padding: 12px 25px; border-radius: 10px; color: white; font-weight: bold; cursor: pointer; font-size: 16px; margin-right: 10px; }
        button.danger { background: linear-gradient(135deg, #ff4444, #cc0000); }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }
        th { color: #ffaa44; }
        .status-active { color: #00ff00; }
        .status-expired { color: #ff4444; }
        .key-code { font-family: monospace; background: #1a1a2a; padding: 5px 10px; border-radius: 5px; font-size: 12px; }
        .message { padding: 10px; border-radius: 10px; margin-top: 15px; }
        .success { background: rgba(0,255,0,0.2); border: 1px solid #00ff00; }
        .error { background: rgba(255,0,0,0.2); border: 1px solid #ff0000; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 QUẢN LÝ KEY TOOL TÀI XỈU</h1>
        <div class="card" id="loginCard">
            <h2>ĐĂNG NHẬP</h2>
            <div class="input-group">
                <label>Mật khẩu quản trị</label>
                <input type="password" id="adminPass" placeholder="Nhập mật khẩu">
            </div>
            <button onclick="login()">Đăng Nhập</button>
            <div id="loginMsg"></div>
        </div>
        <div id="mainContent" style="display:none;">
            <div class="card">
                <h2>✨ TẠO KEY MỚI</h2>
                <div class="input-group">
                    <label>Số ngày sử dụng</label>
                    <select id="daySelect">
                        <option value="1">1 ngày</option>
                        <option value="3">3 ngày</option>
                        <option value="7">7 ngày</option>
                        <option value="15">15 ngày</option>
                        <option value="30">30 ngày</option>
                        <option value="90">90 ngày</option>
                    </select>
                </div>
                <div class="input-group">
                    <label>Ghi chú (tên người dùng)</label>
                    <input type="text" id="note" placeholder="Tên người dùng">
                </div>
                <button onclick="createKey()">➕ TẠO KEY</button>
                <div id="createMsg"></div>
            </div>
            <div class="card">
                <h2>📋 DANH SÁCH KEY</h2>
                <div style="overflow-x: auto;">
                    <table>
                        <thead><tr><th>STT</th><th>KEY</th><th>Người dùng</th><th>Ngày tạo</th><th>Hết hạn</th><th>Trạng thái</th><th>Thao tác</th></tr></thead>
                        <tbody id="keyList"></tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    <script>
        function login() {
            fetch('/api/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({password: document.getElementById('adminPass').value})
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    document.getElementById('loginCard').style.display = 'none';
                    document.getElementById('mainContent').style.display = 'block';
                    loadKeys();
                } else {
                    document.getElementById('loginMsg').innerHTML = '<div class="message error">❌ Sai mật khẩu!</div>';
                }
            });
        }
        function createKey() {
            let days = parseInt(document.getElementById('daySelect').value);
            const note = document.getElementById('note').value;
            fetch('/api/create_key', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({days: days, note: note})
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    document.getElementById('createMsg').innerHTML = `<div class="message success">✅ Key: <strong>${data.key}</strong><br>Hết hạn: ${data.expiry}</div>`;
                    loadKeys();
                    document.getElementById('note').value = '';
                }
            });
        }
        function deleteKey(key) {
            if(confirm('Xóa key này?')) {
                fetch('/api/delete_key', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({key: key})})
                .then(() => loadKeys());
            }
        }
        function loadKeys() {
            fetch('/api/list_keys').then(res => res.json()).then(data => {
                const tbody = document.getElementById('keyList');
                tbody.innerHTML = '';
                data.keys.forEach((k, idx) => {
                    const isExpired = new Date() > new Date(k.expiry);
                    tbody.innerHTML += `<tr>
                        <td>${idx+1}</td>
                        <td><span class="key-code">${k.key}</span></td>
                        <td>${k.note || '---'}</td>
                        <td>${k.created}</td>
                        <td>${k.expiry}</td>
                        <td>${isExpired ? '<span class="status-expired">❌ Hết hạn</span>' : '<span class="status-active">✅ Còn hiệu lực</span>'}</td>
                        <td><button class="danger" onclick="deleteKey('${k.key}')">🗑️ Xóa</button></td>
                    </tr>`;
                });
            });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/login', methods=['POST'])
def api_login():
    return jsonify({'success': request.json.get('password') == ADMIN_PASSWORD})

@app.route('/api/create_key', methods=['POST'])
def api_create_key():
    data = request.json
    days = data.get('days', 1)
    keys = load_keys()
    new_key = generate_key()
    created = datetime.now()
    expiry = created + timedelta(days=days)
    keys[new_key] = {
        'note': data.get('note', ''),
        'created': created.strftime('%d/%m/%Y %H:%M'),
        'expiry': expiry.strftime('%d/%m/%Y %H:%M')
    }
    save_keys(keys)
    return jsonify({'success': True, 'key': new_key, 'expiry': expiry.strftime('%d/%m/%Y %H:%M')})

@app.route('/api/delete_key', methods=['POST'])
def api_delete_key():
    keys = load_keys()
    key = request.json.get('key')
    if key in keys:
        del keys[key]
        save_keys(keys)
    return jsonify({'success': True})

@app.route('/api/list_keys', methods=['GET'])
def api_list_keys():
    keys = load_keys()
    key_list = [{'key': k, **v} for k, v in keys.items()]
    key_list.sort(key=lambda x: x['expiry'], reverse=True)
    return jsonify({'keys': key_list})

@app.route('/api/verify_key', methods=['POST'])
def api_verify_key():
    key = request.json.get('key')
    keys = load_keys()
    if key not in keys:
        return jsonify({'success': False, 'message': 'Key không tồn tại'})
    expiry = datetime.strptime(keys[key]['expiry'], '%d/%m/%Y %H:%M')
    if expiry < datetime.now():
        return jsonify({'success': False, 'message': f'Key đã hết hạn từ {keys[key]["expiry"]}'})
    return jsonify({'success': True, 'message': 'Key hợp lệ', 'expiry': keys[key]['expiry']})

if __name__ == '__main__':
    print("=" * 50)
    print("🔐 WEB QUẢN LÝ KEY - KHỞI ĐỘNG")
    print("=" * 50)
    print("📱 Truy cập: http://localhost:5000")
    print("🔑 Mật khẩu: admin123")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)