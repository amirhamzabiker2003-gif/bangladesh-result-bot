import requests
import re
from bs4 import BeautifulSoup
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8704841795:AAEXokGxG2gtGDcLzKIySygwPD61RdQHWqg"

user_data = {}

# ---------- CAPTCHA FETCH ----------
headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "http://www.educationboardresults.gov.bd/index.php"
}

def get_captcha(session):
    url = "http://www.educationboardresults.gov.bd/index.php"
    res = session.get(url, headers=headers)

    match = re.search(r'(\d+\s*\+\s*\d+)', res.text)
    if match:
        return match.group(1)

    return None

def fetch_captcha(session):
    for _ in range(5):
        cap = get_captcha(session)
        if cap:
            return cap
    return None

# ---------- RESULT CHECK ----------
def check_result(data):
    session = requests.Session()

    captcha = fetch_captcha(session)
    if not captcha:
        return None

    answer = str(eval(captcha))

    payload = {
        "sr": "3",
        "et": "2",
        "exam": data["exam"],
        "year": data["year"],
        "board": data["board"],
        "roll": data["roll"],
        "reg": data["reg"],
        "value_s": answer,
        "button2": "Submit"
    }

    res = session.post(
        "http://www.educationboardresults.gov.bd/result.php",
        data=payload,
        headers=headers
    )

    if "Result" not in res.text:
        return "retry"

    return res.text

def get_final_result(data):
    for _ in range(5):
        result = check_result(data)
        if result and result != "retry":
            return result
    return None

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🚀 Result Check"]]
    await update.message.reply_text(
        "📢 Welcome!\nClick below 👇",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# ---------- HANDLE ----------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text

    data = user_data.setdefault(chat_id, {})

    if text == "🚀 Result Check":
        user_data[chat_id] = {}

        keyboard = [
            ["SSC", "HSC"],
            ["JSC", "SSC VOC"],
            ["HSC VOC", "HSC BM"]
        ]

        await update.message.reply_text("📚 Select Exam:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

    elif "exam" not in data:
        exam_map = {
            "SSC": "ssc",
            "HSC": "hsc",
            "JSC": "jsc",
            "SSC VOC": "ssc_voc",
            "HSC VOC": "hsc_voc",
            "HSC BM": "hsc_bm"
        }
        data["exam"] = exam_map.get(text, "ssc")

        keyboard = [["2025","2024","2023"],["2022","2021","2020"],["2019","2018","2017"]]
        await update.message.reply_text("📅 Select Year:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

    elif "year" not in data:
        data["year"] = text

        keyboard = [
            ["Dhaka","Chattogram","Rajshahi"],
            ["Sylhet","Barishal","Cumilla"],
            ["Dinajpur","Jashore","Mymensingh"],
            ["Madrasah","Technical"]
        ]
        await update.message.reply_text("🏫 Select Board:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

    elif "board" not in data:
        data["board"] = text.lower()
        await update.message.reply_text("🔢 Enter Roll:")

    elif "roll" not in data:
        data["roll"] = text
        await update.message.reply_text("📝 Enter Registration:")

    elif "reg" not in data:
        data["reg"] = text

        await update.message.reply_text("⏳ Checking Result...")

        html = get_final_result(data)

        if not html:
            await update.message.reply_text("❌ Failed! Try again later")
            user_data[chat_id] = {}
            return

        soup = BeautifulSoup(html, "html.parser")

        def get_val(label):
            tag = soup.find(string=label)
            return tag.find_next().text.strip() if tag else "N/A"

        name = get_val("Name")
        father = get_val("Father's Name")
        mother = get_val("Mother's Name")
        dob = get_val("Date of Birth")
        group = get_val("Group")
        result_status = get_val("Result")
        gpa = get_val("GPA")
        institute = get_val("Institute")

        subjects_text = ""
        for row in soup.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) == 3:
                subjects_text += f"{cols[0].text} → {cols[1].text} → {cols[2].text}\n"

        result = f"""
👨‍🎓 STUDENT INFO
━━━━━━━━━━━━━━━
👤 Name: {name}
👨 Father: {father}
👩 Mother: {mother}
🎂 DOB: {dob}

📘 RESULT {data['year']}
━━━━━━━━━━━━━━━
🆔 Roll: {data['roll']}
📄 Reg: {data['reg']}
🏫 Board: {data['board'].upper()}

📊 Result: {result_status}
⭐ GPA: {gpa}

🏫 {institute}

📊 SUBJECTS
━━━━━━━━━━━━━━━
{subjects_text}
"""

        await update.message.reply_text(result)

        user_data[chat_id] = {}

# ---------- RUN ----------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🚀 RESULT BD BOT STARTED SUCCESSFULLY ✅")

    app.run_polling()
