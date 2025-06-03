import requests
from bs4 import BeautifulSoup
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

BOT_TOKEN = "8045217918:AAGqMoKrbMNni9eM7VGlmgETy6tZpMzSuos"
CHAT_ID = "-1002618033336"

bot = Bot(token=BOT_TOKEN)
scheduler = BackgroundScheduler()

try:
    bot.delete_webhook()
except:
    pass

def fetch_all_results():
    url = "https://satta-king-fixed-no.in/"
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        blocks = soup.find_all("div", class_="resultmain")

        results_by_date = {}
        for block in blocks:
            date_tag = block.find("p", class_="resultmaintime")
            if not date_tag:
                continue

            try:
                date_text = date_tag.text.strip()
                date_obj = datetime.strptime(date_text, "%d %B %Y %I:%M %p")
                date_key = date_obj.strftime("%d-%m-%Y")
            except:
                continue

            games = block.find_all("p", class_="livegame")
            values = block.find_all("p", class_="liveresult")

            day_result = {}
            for g, v in zip(games, values):
                name = g.text.strip().lower()
                value = v.text.strip()
                if name == "char minar":
                    continue
                day_result[name] = value

            if date_key not in results_by_date:
                results_by_date[date_key] = {}

            results_by_date[date_key].update(day_result)

        return results_by_date
    except:
        return {}

def format_result(data: dict, date_label: str):
    msg = f"*📅 {date_label} के रिज़ल्ट:*\n"
    for game, val in data.items():
        emoji_val = ''.join(f"{d}\u20E3" for d in val) if val.upper() != "WAIT" else "⏳"
        msg += f"*{game.upper()}* == {emoji_val}\n"
    return msg

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🙏 *स्वागत है Fast Satta Live Bot में!*\n\n"
        "📢 रिज़ल्ट देखने के लिए:\n"
        "👉 /result - आज का रिज़ल्ट\n"
        "👉 /date DD-MM-YYYY - किसी दिन का\n"
        "👉 /history - पिछले दिन के रिज़ल्ट\n"
        "👉 /help - सभी कमांड्स",
        parse_mode="Markdown"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 *Available Commands:*\n"
        "/start - स्वागत संदेश\n"
        "/help - सभी कमांड्स\n"
        "/result - आज का लाइव रिज़ल्ट\n"
        "/date DD-MM-YYYY - किसी तारीख़ का रिज़ल्ट\n"
        "/history - पिछले 5 दिन के रिज़ल्ट",
        parse_mode="Markdown"
    )

async def result_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_data = fetch_all_results()
    today = datetime.now().strftime("%d-%m-%Y")
    data = all_data.get(today)
    if data:
        msg = format_result(data, today)
    else:
        msg = "❌ आज का रिज़ल्ट अभी उपलब्ध नहीं है।"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def history_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_data = fetch_all_results()
    sorted_dates = sorted(all_data.keys(), reverse=True)[:5]
    msg = "📅 *Recent Results:*\n"
    for date in sorted_dates:
        results = all_data[date]
        line = ', '.join([f"{k.upper()}={v}" for k, v in results.items()])
        msg += f"{date} ➤ {line}\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

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

def schedule_jobs():
    times = ["03:15", "04:48", "06:15", "09:58", "11:57", "05:35"]
    for t in times:
        hr, mn = map(int, t.split(":"))
        scheduler.add_job(lambda: bot.send_message(chat_id=CHAT_ID, text="⏳ Auto Result Update Coming Soon"), "cron", hour=hr, minute=mn)
    scheduler.start()

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
