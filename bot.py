import requests
import os
from flask import Flask, request

TOKEN = os.getenv("TOKEN")
URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

users = {}

# ================= SEND MESSAGE =================
def send_message(chat_id, text, keyboard=None):
    data = {
        "chat_id": chat_id,
        "text": text
    }
    if keyboard:
        data["reply_markup"] = keyboard

    requests.post(f"{URL}/sendMessage", json=data)

# ================= SEND PHOTO =================
def send_photo(chat_id, photo_bytes, keyboard=None):
    files = {"photo": photo_bytes}
    data = {"chat_id": chat_id}

    if keyboard:
        data["reply_markup"] = str(keyboard)

    requests.post(f"{URL}/sendPhoto", data=data, files=files)

# ================= MAIN MENU =================
def main_menu():
    return {
        "keyboard": [
            ["🚀 রেজাল্ট বের করুন 🚀"],
            ["⁉️ Help", "⭐ Rate"]
        ],
        "resize_keyboard": True
    }

# ================= CAPTCHA =================
def send_captcha(chat_id, data):
    url = "https://eboardresults.com/v2/captcha"
    r = data["session"].get(url)

    keyboard = {
        "keyboard": [["🔄 Reload Captcha"]],
        "resize_keyboard": True
    }

    requests.post(
        f"{URL}/sendPhoto",
        data={"chat_id": chat_id, "reply_markup": str(keyboard)},
        files={"photo": r.content}
    )

    send_message(chat_id, "🔐 Captcha লিখুন:")

# ================= WEBHOOK =================
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()

    if "message" not in update:
        return "ok"

    msg = update["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")

    if chat_id not in users:
        users[chat_id] = {}

    data = users[chat_id]

    # ================= START =================
    if text == "/start":
        users[chat_id] = {}
        send_message(chat_id, "🎉 Welcome!\nResult দেখতে বাটনে চাপ দিন 👇", main_menu())
        return "ok"

    # ================= MAIN =================
    if text == "🚀 রেজাল্ট বের করুন 🚀":
        users[chat_id] = {}
        keyboard = {
            "keyboard": [["SSC", "HSC"]],
            "resize_keyboard": True
        }
        send_message(chat_id, "📘 Exam নির্বাচন করুন:", keyboard)
        return "ok"

    # ================= EXAM =================
    if "exam" not in data:
        data["exam"] = text.lower()
        keyboard = {
            "keyboard": [["2025", "2024"], ["2023", "2022"]],
            "resize_keyboard": True
        }
        send_message(chat_id, "📅 Year নির্বাচন করুন:", keyboard)
        return "ok"

    # ================= YEAR =================
    if "year" not in data:
        data["year"] = text
        keyboard = {
            "keyboard": [["Dhaka", "Chattogram"], ["Rajshahi", "Cumilla"]],
            "resize_keyboard": True
        }
        send_message(chat_id, "🏫 Board নির্বাচন করুন:", keyboard)
        return "ok"

    # ================= BOARD =================
    if "board" not in data:
        data["board"] = text.lower()
        send_message(chat_id, "🆔 Roll লিখুন:")
        return "ok"

    # ================= ROLL =================
    if "roll" not in data:
        data["roll"] = text
        send_message(chat_id, "📄 Registration লিখুন:")
        return "ok"

    # ================= REG =================
    if "reg" not in data:
        data["reg"] = text
        data["session"] = requests.Session()
        send_captcha(chat_id, data)
        return "ok"

    # ================= RELOAD CAPTCHA =================
    if text == "🔄 Reload Captcha":
        send_captcha(chat_id, data)
        return "ok"

    # ================= CAPTCHA =================
    if "captcha" not in data:
        data["captcha"] = text

        payload = {
            "board": data["board"],
            "exam": data["exam"],
            "year": data["year"],
            "result_type": "1",
            "roll": data["roll"],
            "reg": data["reg"],
            "captcha": data["captcha"]
        }

        headers = {
            "User-Agent": "Mozilla/5.0",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://eboardresults.com",
            "Referer": "https://eboardresults.com/v2/home"
        }

        res = data["session"].post(
            "https://eboardresults.com/v2/getres",
            data=payload,
            headers=headers
        )

        result = res.json()

        if result.get("status") != 0:
            send_message(chat_id, "❌ Captcha ভুল")
            send_captcha(chat_id, data)
            return "ok"

        info = result["res"]

        gpa = info.get("res_detail", "").replace("GPA=", "")

        msg = f"""
👨‍🎓 STUDENT INFO
━━━━━━━━━━━━━━

👤 Name: {info.get('name')}
👨 Father: {info.get('fname')}
👩 Mother: {info.get('mname')}

📘 {data['exam'].upper()} RESULT {data['year']}
━━━━━━━━━━━━━━

🆔 Roll: {data['roll']}
📄 Reg: {data['reg']}

🏫 Board: {info.get('board_name')}
📚 Group: {info.get('stud_group')}

📊 Result: PASSED
⭐ GPA: {gpa}

🏫 Institute: {info.get('inst_name')}
"""

        send_message(chat_id, msg, main_menu())

        users[chat_id] = {}

    return "ok"

# ================= ROOT =================
@app.route("/")
def home():
    return "Bot Running ✅"

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
