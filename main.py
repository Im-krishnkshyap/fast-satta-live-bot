import requests
from bs4 import BeautifulSoup
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
import re
from datetime import datetime

BOT_TOKEN = "8045217918:AAGqMoKrbMNni9eM7VGlmgETy6tZpMzSuos"
CHAT_ID = "-1002618033336"

bot = Bot(token=BOT_TOKEN)
scheduler = BackgroundScheduler()

# ✅ Reset webhook to avoid polling conflict
try:
    bot.delete_webhook()
except:
    pass

# 🔍 Parse all result blocks from site
def fetch_all_results():
    url = "https://satta-king-fixed-no.in/"
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        content = soup.find_all("div", class_="resultmain")
        results_by_date = {}

        for section in content:
            date_tag = section.find("p", class_="resultmaintime")
            if not date_tag:
                continue
            date_text = date_tag.text.strip().split()[0:3]  # e.g. '03 June 2025'
            date_fmt = datetime.strptime(' '.join(date_text), "%d %B %Y").strftime("%d-%m-%Y")

            games = section.find_all("p", class_="livegame")
            values = section.find_all("p", class_="liveresult")

            results = {}
            for g, v in zip(games, values):
                game = g.text.strip()
                val = v.text.strip()
                results[game] = val

            results_by_date[date_fmt] = results
        return results_by_date
    except:
        return {}

# 🧾 Format result message
def format_result(data: dict, date_label: str):
    msg = f"*📅 {date_label} के रिज़ल्ट:*\n"
    for game, val in data.items():
        emoji_val = ''.join(f"{d}\u20E3" for d in val) if val.upper() != "WAIT" else "⏳"
        msg += f"*{game}* == {emoji_val}\n"
    return msg

# 🟢 /start
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🙏 *स्वागत है Fast Satta Live Bot में!*\n\n"
        "📢 यहां आप सभी लाइव रिज़ल्ट देख सकते हैं:\n"
        "🔹 दिल्ली बाजार, श्री गणेश, फरीदाबाद, गाजियाबाद, गली, दिशावर\n\n"
        "🧾 रिज़ल्ट देखने के लिए:\n"
        "👉 /result - आज का रिज़ल्ट\n"
        "👉 /date DD-MM-YYYY - किसी दिन का रिज़ल्ट\n"
        "👉 /history - पिछले कुछ दिन के रिज़ल्ट\n"
        "👉 /help - सभी कमांड्स"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

# 🟢 /help
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📌 *Available Commands:*\n"
        "/start - स्वागत संदेश\n"
        "/help - कमांड्स की सूची\n"
        "/result - आज का लाइव रिज़ल्ट\n"
        "/date DD-MM-YYYY - किसी विशेष दिन का रिज़ल्ट\n"
        "/history - पिछले 5 दिन के रिज़ल्ट"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

# 🟢 /result
async def result_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_data = fetch_all_results()
    today = datetime.now().strftime("%d-%m-%Y")
    data = all_data.get(today)
    if data:
        msg = format_result(data, today)
    else:
        msg = "❌ आज का रिज़ल्ट अभी उपलब्ध नहीं है।"
    await update.message.reply_text(msg, parse_mode="Markdown")

# 🟢 /history
async def history_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_data = fetch_all_results()
    sorted_dates = sorted(all_data.keys(), reverse=True)[:5]
    msg = "📅 *Recent Results:*\n"
    for date in sorted_dates:
        day_result = all_data[date]
        result_line = ', '.join([f"{k}={v}" for k, v in day_result.items()])
        msg += f"{date} ➤ {result_line}\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

# 🟢 /date DD-MM-YYYY
async def date_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ कृपया तारीख़ दें, जैसे: /date 03-06-2025")
        return
    user_date = context.args[0]
    all_data = fetch_all_results()
    data = all_data.get(user_date)
    if data:
        msg = format_result(data, user_date)
    else:
        msg = f"❌ {user_date} का कोई डेटा नहीं मिला।"
    await update.message.reply_text(msg, parse_mode="Markdown")

# 📅 Schedule Time-based Jobs (You can customize)
def schedule_jobs():
    times = ["03:15", "04:48", "06:15", "09:58", "11:57", "05:35"]
    for t in times:
        hr, mn = map(int, t.split(":"))
        scheduler.add_job(lambda: bot.send_message(chat_id=CHAT_ID, text="⏳ Auto Result Update Coming Soon"), "cron", hour=hr, minute=mn)
    scheduler.start()

# 🚀 Run Bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("result", result_cmd))
    app.add_handler(CommandHandler("history", history_cmd))
    app.add_handler(CommandHandler("date", date_cmd))
    schedule_jobs()
    print("✅ Bot started.")
    app.run_polling()
