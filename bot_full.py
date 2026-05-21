# ==================== bot_full.py ====================
from flask import Flask
import threading
import requests
import time
import json
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

# ==================== WEB SERVER (GIỮ BOT KHÔNG NGỦ) ====================
app = Flask('')

@app.route('/')
def home():
    return "Bot is running 24/7!"

def keep_alive():
    app.run(host='0.0.0.0', port=8080)

# Chạy web server trong thread riêng
threading.Thread(target=keep_alive).start()

# ==================== TOKEN & ADMIN ====================
BOT_TOKEN = "8578642240:AAEl0IoOEHIZUOcNMKL-b7f-5yif_HmNTuI"
ADMIN_ID = 8271248551

# ==================== URL WEB TẠO KEY ====================
KEY_API_URL = "http://localhost:5000/api/verify_key"

# ==================== THUẬT TOÁN CẦU 8T ====================
PATTERN_MAP = {
    "TXXTTXTX": "Xỉu", "XXTTXTXX": "Tài", "XTTXTXXT": "Tài", "TTXTXXTT": "Tài",
    "TXTXXTTT": "Xỉu", "XTXXTTTX": "Xỉu", "TXXTTTXX": "Tài", "XXTTTXXT": "Xỉu",
    "XTTTXXTX": "Xỉu", "TTTXXTXX": "Xỉu", "TTXXTXXX": "Xỉu", "TXXTXXXX": "Xỉu",
    "XXTXXXXX": "Tài", "XTXXXXXT": "Xỉu", "TXXXXXTX": "Xỉu", "XXXXXTXX": "Xỉu",
    "XXXXTXXX": "Tài", "XXXTXXXT": "Xỉu", "XXTXXXTX": "Xỉu", "XTXXXTXX": "Xỉu",
    "TXXXTXXX": "Tài", "TTTTTTTT": "Xỉu", "TTTTTTTX": "Xỉu", "TTTTTTXX": "Tài",
    "TTTTTXXT": "Xỉu", "TTTTXXTX": "Xỉu", "TTTXXTXX": "Tài", "TTXXTXXT": "Xỉu",
    "TXXTXXTX": "Xỉu", "XXTXXTXX": "Xỉu", "XTXXTXXX": "Tài", "TXXTXXXT": "Tài",
    "XXTXXXTT": "Xỉu", "XTXXXTTX": "Tài", "TXXXTTXT": "Xỉu", "XXXTTXTX": "Xỉu",
    "XXTTXTXX": "Tài", "XTTXTXXT": "Tài", "TTXTXXTT": "Xỉu", "TXTXXTTX": "Xỉu",
    "XTXXTTXX": "Tài", "TXXTTXXT": "Tài", "XXTTXXTT": "Tài", "XTTXXTTT": "Xỉu",
    "TTXXTTTX": "Xỉu", "TXXTTTXX": "Tài", "XXTTTXXX": "Tài", "XTTTXXXT": "Tài",
    "TTTXXXTT": "Xỉu", "TTXXXTTX": "Tài", "TXXXTTXT": "Tài", "XXXTTXTT": "Xỉu",
    "XXXXXXXX": "Xỉu", "XXXXXXXT": "Tài", "XXXXXXTT": "Xỉu", "XXXXXTTT": "Tài",
    "XXXXTTTT": "Tài", "XXXTTTTT": "Tài", "XXTTTTTT": "Xỉu", "XTTTTTTT": "Tài",
}

def convert_to_char(result):
    return "T" if result == "Tài" else "X"

def predict_by_cau8t(history):
    if len(history) < 8:
        if len(history) < 3:
            return {"prediction": "Tài", "confidence": 55}
        last = history[-1]
        count = 1
        for i in range(len(history)-2, -1, -1):
            if history[i] == last:
                count += 1
            else:
                break
        if count >= 3:
            opposite = "Xỉu" if last == "Tài" else "Tài"
            return {"prediction": opposite, "confidence": 75}
        opposite = "Xỉu" if last == "Tài" else "Tài"
        return {"prediction": opposite, "confidence": 65}
    
    last8 = ''.join([convert_to_char(r) for r in history[-8:]])
    
    if last8 in PATTERN_MAP:
        return {"prediction": PATTERN_MAP[last8], "confidence": 88}
    
    last = history[-1]
    last4 = ''.join([convert_to_char(r) for r in history[-4:]])
    if last4 in ["TTTT", "XXXX"]:
        opposite = "Xỉu" if last == "Tài" else "Tài"
        return {"prediction": opposite, "confidence": 82}
    
    opposite = "Xỉu" if last == "Tài" else "Tài"
    return {"prediction": opposite, "confidence": 68}

# ==================== API CÁC GAME ====================
APIS = {
    "SUNWIN": "https://era-technology-particular-domestic.trycloudflare.com/api/tx",
    "HITCLUB": "https://preference-assuming-picnic-concentration.trycloudflare.com/api/tx",
    "HITCLUB_MD5": "https://preference-assuming-picnic-concentration.trycloudflare.com/api/txmd5",
    "BETVIP": "https://eve-hydrocodone-offshore-eagle.trycloudflare.com/api/tx",
    "LC79": "https://strategy-cube-vinyl-warcraft.trycloudflare.com/api/tx",
    "LC79_MD5": "https://strategy-cube-vinyl-warcraft.trycloudflare.com/api/txmd5",
    "B52": "https://b52-taixiu-l69b.onrender.com/api/taixiu"
}

# File lưu danh sách người dùng đã có key
AUTH_USERS_FILE = "auth_users.json"

# Lưu dữ liệu
authorized_users = {}
user_history = {}
group_auto = {}
predicting_threads = {}

def load_auth_users():
    global authorized_users
    if os.path.exists(AUTH_USERS_FILE):
        with open(AUTH_USERS_FILE, 'r', encoding='utf-8') as f:
            authorized_users = json.load(f)

def save_auth_users():
    with open(AUTH_USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(authorized_users, f, ensure_ascii=False, indent=2)

def call_api(url):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def get_game_result(tool):
    data = call_api(APIS[tool])
    if not data:
        return None
    
    if tool == "B52":
        return {
            'phien': data.get('phien_hien_tai', '--'),
            'current_predict': data.get('Du_doan', 'Tài'),
            'current_conf': data.get('Do_tin_cay', '75%'),
            'type': 'predict'
        }
    else:
        x1 = data.get('xuc_xac_1', '?')
        x2 = data.get('xuc_xac_2', '?')
        x3 = data.get('xuc_xac_3', '?')
        return {
            'phien': data.get('phien', '--'),
            'result': data.get('ket_qua', 'Xỉu'),
            'dice': f"{x1} - {x2} - {x3}",
            'tong': data.get('tong', 0),
            'type': 'result'
        }

def verify_key(key):
    try:
        r = requests.post(KEY_API_URL, json={'key': key}, timeout=5)
        if r.status_code == 200:
            data = r.json()
            return data.get('success', False), data.get('message', ''), data.get('expiry', '')
    except Exception as e:
        print(f"Lỗi kết nối server key: {e}")
    return False, "Không thể kết nối server key", None

def is_authorized(user_id):
    if user_id == ADMIN_ID:
        return True
    return str(user_id) in authorized_users

def add_authorized_user(user_id, name, expiry):
    authorized_users[str(user_id)] = {'name': name, 'expiry': expiry}
    save_auth_users()

# ==================== MENU ====================
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("🎲 SUNWIN", callback_data="SUNWIN")],
        [InlineKeyboardButton("💜 HITCLUB - Tài Xỉu Hũ", callback_data="HITCLUB")],
        [InlineKeyboardButton("🔐 HITCLUB - Tài Xỉu MD5", callback_data="HITCLUB_MD5")],
        [InlineKeyboardButton("🔵 BETVIP", callback_data="BETVIP")],
        [InlineKeyboardButton("🟡 LC79 - Tài Xỉu Hũ", callback_data="LC79")],
        [InlineKeyboardButton("🔐 LC79 - Tài Xỉu MD5", callback_data="LC79_MD5")],
        [InlineKeyboardButton("🟢 B52", callback_data="B52")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_control_menu():
    keyboard = [
        [InlineKeyboardButton("▶️ DỰ ĐOÁN LIÊN TỤC", callback_data="auto_start")],
        [InlineKeyboardButton("⏹️ DỪNG DỰ ĐOÁN", callback_data="auto_stop")],
        [InlineKeyboardButton("🏠 MENU CHÍNH", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_auto_running_menu():
    keyboard = [
        [InlineKeyboardButton("⏹️ DỪNG DỰ ĐOÁN", callback_data="auto_stop")],
        [InlineKeyboardButton("🏠 MENU CHÍNH", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_key_request_menu():
    keyboard = [
        [InlineKeyboardButton("🔑 NHẬP KEY", callback_data="enter_key")],
        [InlineKeyboardButton("📞 LIÊN HỆ ADMIN", url="https://t.me/hupcungs77")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== ĐỊNH DẠNG TEXT ====================
def format_tx_result(tool_name, current_data, history, last_predict=None):
    phien = current_data.get('phien', '--')
    result = current_data.get('result', 'Xỉu')
    dice = current_data.get('dice', '? - ? - ?')
    tong = current_data.get('tong', 0)
    result_icon = "🔴" if result == "Tài" else "🟢"
    
    if history is not None:
        history.append(result)
        if len(history) > 50:
            history.pop(0)
    
    prediction = predict_by_cau8t(history if history else [result])
    next_predict = prediction['prediction']
    next_conf = prediction['confidence']
    next_icon = "🔴" if next_predict == "Tài" else "🟢"
    next_phien = int(phien) + 1 if str(phien).isdigit() else "?"
    
    msg = f"🎲 *{tool_name} - Tài Xỉu Hũ*\n━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📌 Phiên: #{phien}\n"
    msg += f"🎲 Kết quả: {dice} => {tong} điểm\n"
    msg += f"🎯 Kết quả: {result_icon} `{result}`\n"
    
    if last_predict:
        is_correct = (last_predict == result)
        if is_correct:
            msg += f"\n✅ *Dự đoán trước: {last_predict} → WIN* 🎉\n"
        else:
            msg += f"\n❌ *Dự đoán trước: {last_predict} → LOSS* 💔\n"
    
    msg += f"\n━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"🔮 *DỰ ĐOÁN PHIÊN #{next_phien}*\n"
    msg += f"🎯 Cửa: {next_icon} `{next_predict}`\n"
    msg += f"📊 Độ tin cậy: `{next_conf}%`\n"
    
    return msg, next_predict

def format_md5_result(tool_name, current_data, history, last_predict=None):
    phien = current_data.get('phien', '--')
    result = current_data.get('result', 'Xỉu')
    dice = current_data.get('dice', '? - ? - ?')
    tong = current_data.get('tong', 0)
    result_icon = "🔴" if result == "Tài" else "🟢"
    
    if history is not None:
        history.append(result)
        if len(history) > 50:
            history.pop(0)
    
    prediction = predict_by_cau8t(history if history else [result])
    next_predict = prediction['prediction']
    next_conf = prediction['confidence']
    next_icon = "🔴" if next_predict == "Tài" else "🟢"
    next_phien = int(phien) + 1 if str(phien).isdigit() else "?"
    
    msg = f"🔐 *{tool_name} - Tài Xỉu MD5*\n━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📌 Phiên: #{phien}\n"
    msg += f"🎲 Kết quả: {dice} => {tong} điểm\n"
    msg += f"🎯 Kết quả: {result_icon} `{result}`\n"
    
    if last_predict:
        is_correct = (last_predict == result)
        if is_correct:
            msg += f"\n✅ *Dự đoán trước: {last_predict} → WIN* 🎉\n"
        else:
            msg += f"\n❌ *Dự đoán trước: {last_predict} → LOSS* 💔\n"
    
    msg += f"\n━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"🔮 *DỰ ĐOÁN PHIÊN #{next_phien}*\n"
    msg += f"🎯 Cửa: {next_icon} `{next_predict}`\n"
    msg += f"📊 Độ tin cậy: `{next_conf}%`\n"
    
    return msg, next_predict

def format_b52_result(tool_name, current_data):
    phien = current_data.get('phien', '--')
    current_predict = current_data.get('current_predict', 'Tài')
    current_conf = current_data.get('current_conf', '75%')
    current_icon = "🔴" if current_predict == "Tài" else "🟢"
    
    next_predict = "Xỉu" if current_predict == "Tài" else "Tài"
    next_icon = "🔴" if next_predict == "Tài" else "🟢"
    next_phien = int(phien) + 1 if str(phien).isdigit() else "?"
    
    msg = f"🟢 *{tool_name} - Dự Đoán*\n━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📌 Phiên hiện tại: #{phien}\n"
    msg += f"🔮 Dự đoán hiện tại: {current_icon} `{current_predict}`\n"
    msg += f"🎯 Độ tin cậy: {current_conf}\n"
    
    msg += f"\n━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"🔮 *DỰ ĐOÁN PHIÊN #{next_phien}*\n"
    msg += f"🎯 Cửa: {next_icon} `{next_predict}`\n"
    msg += f"📊 Độ tin cậy: 68%\n"
    
    return msg

# ==================== DỰ ĐOÁN LIÊN TỤC ====================
def auto_predict_loop(user_id, chat_id, tool, context):
    last_phien = None
    last_predict = None
    history = user_history.get(user_id, {}).get('history', [])
    
    while user_history.get(user_id, {}).get('auto', False):
        try:
            current_data = get_game_result(tool)
            if current_data:
                current_phien = current_data.get('phien')
                current_result = current_data.get('result') if tool != "B52" else current_data.get('current_predict')
                
                if current_phien != last_phien and last_phien is not None:
                    if tool == "B52":
                        msg = format_b52_result(tool, current_data)
                    elif "MD5" in tool:
                        msg, next_predict = format_md5_result(tool, current_data, history, last_predict)
                        last_predict = next_predict
                    else:
                        msg, next_predict = format_tx_result(tool, current_data, history, last_predict)
                        last_predict = next_predict
                    
                    context.bot.send_message(
                        chat_id=chat_id,
                        text=f"🔔 *CẬP NHẬT PHIÊN MỚI!*\n\n{msg}",
                        parse_mode='Markdown',
                        reply_markup=get_auto_running_menu()
                    )
                    last_phien = current_phien
                    
                elif current_phien != last_phien and last_phien is None:
                    if tool == "B52":
                        msg = format_b52_result(tool, current_data)
                    elif "MD5" in tool:
                        msg, next_predict = format_md5_result(tool, current_data, history, None)
                        last_predict = next_predict
                    else:
                        msg, next_predict = format_tx_result(tool, current_data, history, None)
                        last_predict = next_predict
                    
                    context.bot.send_message(
                        chat_id=chat_id,
                        text=msg,
                        parse_mode='Markdown',
                        reply_markup=get_auto_running_menu()
                    )
                    last_phien = current_phien
                    
        except Exception as e:
            print(f"Lỗi: {e}")
        
        time.sleep(6)
    
    context.bot.send_message(
        chat_id=chat_id,
        text="🛑 *ĐÃ DỪNG DỰ ĐOÁN LIÊN TỤC!*",
        parse_mode='Markdown'
    )

# ==================== XỬ LÝ LỆNH ====================
def start(update, context):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if user_id == ADMIN_ID:
        update.message.reply_text(
            f"👑 *Chào Admin {user_name}!*\n👇 *Chọn sảnh:*",
            parse_mode='Markdown',
            reply_markup=get_main_menu()
        )
        return
    
    if is_authorized(user_id):
        update.message.reply_text(
            f"👋 *Chào mừng {user_name}!*\n👇 *Chọn sảnh:*",
            parse_mode='Markdown',
            reply_markup=get_main_menu()
        )
    else:
        update.message.reply_text(
            f"🤖 *Chào {user_name}!*\n━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔑 *Bạn cần nhập KEY để sử dụng tool.*\n\n"
            f"📝 *Cú pháp:* `/key [mã_key]`\n\n"
            f"💡 Liên hệ Admin để mua key: @hupcungs77",
            parse_mode='Markdown',
            reply_markup=get_key_request_menu()
        )

def enter_key(update, context):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    text = update.message.text.strip()
    
    if text.startswith('/key'):
        parts = text.split(' ')
        if len(parts) < 2:
            update.message.reply_text("❌ Sai cú pháp!\n📝 Nhập: /key [mã_key]")
            return
        key = parts[1]
    else:
        key = text
    
    valid, msg, expiry = verify_key(key)
    
    if valid:
        add_authorized_user(user_id, user_name, expiry)
        update.message.reply_text(
            f"✅ *KEY HỢP LỆ!*\n━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔓 Chào mừng {user_name}!\n"
            f"📅 Hết hạn: {expiry}\n\n"
            f"👇 *Chọn sảnh bên dưới:*",
            parse_mode='Markdown',
            reply_markup=get_main_menu()
        )
    else:
        update.message.reply_text(
            f"❌ *KEY KHÔNG HỢP LỆ!*\n📌 {msg}\n\n"
            f"💡 Nhập lại: /key [mã_key]",
            parse_mode='Markdown'
        )

def ignore_message(update, context):
    """Bỏ qua tin nhắn thường - KHÔNG PHẢN HỒI"""
    return

def callback(update, context):
    query = update.callback_query
    query.answer()
    data = query.data
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    is_group = update.effective_chat.type in ['group', 'supergroup']
    
    if not is_authorized(user_id):
        query.edit_message_text(
            "🔒 *BẠN CHƯA NHẬP KEY!*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "📝 Vui lòng nhập: `/key [mã_key]`\n\n"
            "💡 Liên hệ Admin để mua key: @hupcungs77\n\n"
            "❌ *Bạn không thể sử dụng bất kỳ chức năng nào khi chưa có key!*",
            parse_mode='Markdown'
        )
        return
    
    if data == "menu":
        query.edit_message_text(
            "👇 *Chọn sảnh:*",
            parse_mode='Markdown',
            reply_markup=get_main_menu()
        )
        return
    
    if data == "enter_key":
        query.edit_message_text(
            "🔑 *Vui lòng nhập KEY:*\n📝 `/key [mã_key]`",
            parse_mode='Markdown'
        )
        return
    
    if data == "auto_start" or data == "auto_stop":
        if data == "auto_start":
            if is_group:
                group_id = chat_id
                current_tool = group_auto.get(group_id, {}).get('tool')
                if not current_tool:
                    query.edit_message_text("⚠️ *Vui lòng chọn sảnh trước!*", parse_mode='Markdown', reply_markup=get_main_menu())
                    return
                
                if user_id not in user_history:
                    user_history[user_id] = {'history': [], 'auto': False, 'tool': current_tool}
                else:
                    user_history[user_id]['auto'] = True
                    user_history[user_id]['tool'] = current_tool
                
                thread = threading.Thread(target=auto_predict_loop, args=(user_id, chat_id, current_tool, context))
                thread.daemon = True
                thread.start()
                predicting_threads[user_id] = thread
                
                query.edit_message_text(
                    f"▶️ *ĐÃ BẮT ĐẦU DỰ ĐOÁN LIÊN TỤC!*\n━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🎯 Tool: {current_tool}",
                    parse_mode='Markdown',
                    reply_markup=get_auto_running_menu()
                )
            else:
                current_tool = context.user_data.get('user_selected_tool')
                if not current_tool:
                    query.edit_message_text("⚠️ *Vui lòng chọn sảnh trước!*", parse_mode='Markdown', reply_markup=get_main_menu())
                    return
                
                if user_id not in user_history:
                    user_history[user_id] = {'history': [], 'auto': False, 'tool': current_tool}
                else:
                    user_history[user_id]['auto'] = True
                    user_history[user_id]['tool'] = current_tool
                
                thread = threading.Thread(target=auto_predict_loop, args=(user_id, chat_id, current_tool, context))
                thread.daemon = True
                thread.start()
                predicting_threads[user_id] = thread
                
                query.edit_message_text(
                    f"▶️ *ĐÃ BẮT ĐẦU DỰ ĐOÁN LIÊN TỤC!*\n━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🎯 Tool: {current_tool}",
                    parse_mode='Markdown',
                    reply_markup=get_auto_running_menu()
                )
        else:
            if user_id in user_history:
                user_history[user_id]['auto'] = False
            query.edit_message_text(
                "🛑 *ĐÃ DỪNG DỰ ĐOÁN LIÊN TỤC!*",
                parse_mode='Markdown',
                reply_markup=get_main_menu()
            )
        return
    
    if data in APIS:
        if is_group:
            group_id = chat_id
            group_auto[group_id] = {'auto': False, 'tool': data}
        else:
            context.user_data['user_selected_tool'] = data
        
        current_data = get_game_result(data)
        
        if not current_data:
            query.edit_message_text(f"❌ *Lỗi kết nối {data}!*", parse_mode='Markdown', reply_markup=get_main_menu())
            return
        
        if user_id not in user_history:
            user_history[user_id] = {'history': [], 'last_predict': None}
        
        history = user_history[user_id]['history']
        last_predict = user_history[user_id]['last_predict']
        
        if data == "B52":
            msg = format_b52_result(data, current_data)
            query.edit_message_text(msg, parse_mode='Markdown', reply_markup=get_control_menu())
        elif "MD5" in data:
            msg, next_predict = format_md5_result(data, current_data, history, last_predict)
            user_history[user_id]['last_predict'] = next_predict
            query.edit_message_text(msg, parse_mode='Markdown', reply_markup=get_control_menu())
        else:
            msg, next_predict = format_tx_result(data, current_data, history, last_predict)
            user_history[user_id]['last_predict'] = next_predict
            query.edit_message_text(msg, parse_mode='Markdown', reply_markup=get_control_menu())

def main():
    load_auth_users()
    
    print("=" * 50)
    print("🎲 BOT TÀI XỈU - KHÔNG KEY KHÔNG BẤM ĐƯỢC GÌ")
    print("=" * 50)
    print(f"👑 Admin ID: {ADMIN_ID}")
    print(f"📋 Số user đã có key: {len(authorized_users)}")
    print("=" * 50)
    print("✅ QUY TẮC:")
    print("   • Có KEY: Được bấm tất cả nút, dùng tool")
    print("   • Không KEY: KHÔNG được bấm BẤT KỲ nút nào")
    print("=" * 50)
    
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("key", enter_key))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, ignore_message))
    dp.add_handler(CallbackQueryHandler(callback))
    
    print("✅ Bot đã sẵn sàng!")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()