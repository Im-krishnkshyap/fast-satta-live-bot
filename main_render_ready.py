import os
import requests
from bs4 import BeautifulSoup
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=BOT_TOKEN)
scheduler = BackgroundScheduler()

def get_live_results():
    url = "https://satta-king-fixed-no.in/"
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        live_games = soup.find_all("p", class_="livegame")
        live_results = soup.find_all("p", class_="liveresult")
        data = dict()
        for game, result in zip(live_games, live_results):
            name = game.text.strip().lower()
            value = result.text.strip()
            if value != "WAIT":
                data[name] = value
        return data
    except Exception as e:
        return {}

def format_result(data: dict):
    msg = "*🔛खबर की जानकारी👉\n⚠️⚠️⚠️⚠️⚠️⚠️〽️〽️*\n"
    ordered_names = ["दिल्ली बाजार", "श्री गणेश", "फरीदाबाद", "गाजियाबाद", "गली", "दिसावर"]
    name_map = {
        "delhi bazar": "दिल्ली बाजार",
        "shree ganesh": "श्री गणेश",
        "faridabad": "फरीदाबाद",
        "ghaziabad": "गाजियाबाद",
        "gali": "गली",
        "desawar": "दिसावर",
        "disawar": "दिसावर"
    }
    result_lines = []
    for eng_name, hindi_name in name_map.items():
        num = data.get(eng_name.lower())
        if num:
            digits = "".join(f"{d}⃣" for d in num)
            result_lines.append(f"*{hindi_name}* =={digits}")
        else:
            result_lines.append(f"*{hindi_name}* ==")
    return msg + "\n".join(result_lines)

async def send_result(context: ContextTypes.DEFAULT_TYPE):
    data = get_live_results()
    if data:
        msg = format_result(data)
        await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

async def result_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_live_results()
    if data:
        msg = format_result(data)
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text("⏳ कृपया प्रतीक्षा करें, परिणाम अभी उपलब्ध नहीं हैं।")

def schedule_jobs(app):
    times = [
        ("03:15", "delhi bazar"),
        ("04:48", "shree ganesh"),
        ("06:15", "faridabad"),
        ("09:58", "ghaziabad"),
        ("11:57", "gali"),
        ("05:35", "disawar")
    ]
    for t, name in times:
        hr, mn = map(int, t.split(":"))
        scheduler.add_job(send_result, "cron", hour=hr, minute=mn)
    scheduler.start()

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("result", result_cmd))
    schedule_jobs(app)
    print("🤖 Bot started...")
    app.run_polling()
