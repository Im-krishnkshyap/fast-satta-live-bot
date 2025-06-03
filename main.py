import requests
from bs4 import BeautifulSoup
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler

BOT_TOKEN = "8045217918:AAGqMoKrbMNni9eM7VGlmgETy6tZpMzSuos"
CHAT_ID = "-1002618033336"

bot = Bot(token=BOT_TOKEN)
scheduler = BackgroundScheduler()

# ✅ Webhook हटाना (conflict से बचाव)
try:
    bot.delete_webhook()
    print("✅ Webhook deleted to enable polling.")
except Exception as e:
    print(f"⚠️ Failed to delete webhook: {e}")

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
            data[name] = value
        return data
    except Exception:
        return {}

def format_result(data: dict):
    msg = "*🔛खबर की जानकारी👉*\n*⚠️⚠️⚠️⚠️⚠️⚠️〽️〽️*\n"
    name_map = {
        "delhi bazar": "दिल्ली बाजार",
        "shree ganesh": "श्री गणेश",
        "faridabad": "फरीदाबाद",
        "ghaziabad": "गाजियाबाद",
        "gali": "गली",
        "desawar": "दिसावर",
        "disawar": "दिसावर"
    }
    lines = []
    for eng_name, hindi_name in name_map.items():
        val = data.get(eng_name, "WAIT")
        if val.upper() == "WAIT":
            lines.append(f"*{hindi_name}* ==⏳")
        else:
            digits = ''.join(f"{d}\u20E3" for d in val)
            lines.append(f"*{hindi_name}* =={digits}")
    return msg + "\n".join(lines)

async def send_result(context: ContextTypes.DEFAULT_TYPE = None):
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

def schedule_jobs():
    times = ["03:15", "04:48", "06:15", "09:58", "11:57", "05:35"]
    for t in times:
        hr, mn = map(int, t.split(":"))
        scheduler.add_job(send_result, "cron", hour=hr, minute=mn)
    scheduler.start()

if __name__ == "__main__":
    try:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("result", result_cmd))
        schedule_jobs()
        print("🤖 Bot started polling...")
        app.run_polling()
    except Exception as e:
        print(f"⚠️ Error: {e}")
