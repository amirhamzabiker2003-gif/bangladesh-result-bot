import requests
from bs4 import BeautifulSoup
import threading
import os

from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ===== TOKEN (Render ENV থেকে নিবে) =====
TOKEN = os.getenv("TOKEN")

BASE_URL = "https://hscresult.bise-ctg.gov.bd/h_x_y_ctg25/individual/result_mark_details.php"

# ===== FLASK KEEP ALIVE =====
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app_flask.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.start()

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🚀 Start"]]

    await update.message.reply_text(
        "📩 Start চাপ দিয়ে শুরু করো:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# ===== MAIN HANDLE =====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # 👉 Start button
    if text == "🚀 Start":
        await update.message.reply_text(
            "📥 তোমার Roll নম্বর দাও:",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # 👉 Next button
    if text.startswith("➡️ Next"):
        text = text.split("(")[-1].replace(")", "")

    wait_msg = await update.message.reply_text(
        "⏳ একটু অপেক্ষা করো...\nResult আনতেছি..."
    )

    payload = {
        "roll": text,
        "button2": "Submit"
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://hscresult.bise-ctg.gov.bd/h_x_y_ctg25/individual/index.php"
    }

    try:
        res = requests.post(BASE_URL, data=payload, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")

        data = {}

        for row in soup.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) == 4:
                data[cols[0].get_text(strip=True)] = cols[1].get_text(strip=True)
                data[cols[2].get_text(strip=True)] = cols[3].get_text(strip=True)

        name = data.get("Name", "")
        father = data.get("Father's Name", "")
        mother = data.get("Mother's Name", "")
        roll = data.get("Roll No", "")
        reg = data.get("Reg. NO", "")
        board = data.get("Board", "")
        group = data.get("Group", "")
        result = data.get("Result", "")
        gpa = data.get("GPA", "")
        institute = data.get("Institute", "")

        if not name:
            await wait_msg.delete()
            await update.message.reply_text("❌ Result পাওয়া যায়নি!")
            return

        await wait_msg.delete()

        msg = (
            "🧑‍🎓 STUDENT INFORMATION\n"
            "━━━━━━━━━━━━━━\n\n"

            f"👤 Name: {name}\n"
            f"👨 Father: {father}\n"
            f"👩 Mother: {mother}\n\n"

            "━━━━━━━━━━━━━━\n"
            "📘 HSC RESULT 2025\n"
            "━━━━━━━━━━━━━━\n\n"

            f"🆔 Roll No: {roll}\n"
            f"📄 Registration No: {reg}\n\n"

            f"🏫 Board: {board}\n"
            f"📚 Group: {group}\n\n"

            f"📊 Result: {result}\n"
            f"⭐ GPA: {gpa}\n\n"

            f"🏫 Institute: {institute}"
        )

        await update.message.reply_text(msg)

        # ===== NEXT BUTTON =====
        next_roll = str(int(roll) + 1)

        keyboard = [[f"➡️ Next ({next_roll})"]]

        await update.message.reply_text(
            "👉 Next করতে নিচের বাটনে চাপ দাও",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )

    except Exception as e:
        await wait_msg.delete()
        await update.message.reply_text("❌ Server Error!")

# ===== RUN =====
def main():
    keep_alive()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
