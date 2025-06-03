#!/usr/bin/env python3
"""
Working Telegram Bot based on your original code
"""

import os
import sys

# Get bot token from environment
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

try:
    # Try to import the required modules
    sys.path.insert(0, '.pythonlibs/lib/python3.11/site-packages')
    
    from telegram.ext import Application, CommandHandler
    from telegram import Update
    
    async def get_id(update, context):
        """Handle the /id command"""
        chat = update.effective_chat
        message = f"Chat ID: {chat.id}"
        await update.message.reply_text(message)
        print(f"Chat ID requested: {chat.id}")

    async def start_command(update, context):
        """Handle the /start command"""
        await update.message.reply_text("Bot running. Send /id in group.")

    def main():
        """Main function to run the bot"""
        if not TOKEN:
            print("Error: No TELEGRAM_BOT_TOKEN found in environment variables")
            return
            
        print("Bot running. Send /id in group.")
        
        # Create application
        app = Application.builder().token(TOKEN).build()
        
        # Add handlers
        app.add_handler(CommandHandler("id", get_id))
        app.add_handler(CommandHandler("start", start_command))
        
        # Start polling
        app.run_polling()

    if __name__ == '__main__':
        main()

except ImportError as e:
    print(f"Import error: {e}")
    print("Trying fallback approach...")
    
    # Fallback approach using direct HTTP requests
    import asyncio
    import json
    try:
        import httpx
    except ImportError:
        print("Installing httpx for HTTP requests...")
        os.system("python -m pip install --user httpx")
        import httpx
    
    class SimpleTelegramBot:
        def __init__(self, token):
            self.token = token
            self.base_url = f"https://api.telegram.org/bot{token}"
            
        async def get_updates(self, offset=None):
            url = f"{self.base_url}/getUpdates"
            params = {"timeout": 10}
            if offset:
                params["offset"] = offset
                
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                return response.json()
        
        async def send_message(self, chat_id, text):
            url = f"{self.base_url}/sendMessage"
            data = {"chat_id": chat_id, "text": text}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data)
                return response.json()
        
        async def run(self):
            print("Bot running. Send /id in group.")
            offset = None
            
            while True:
                try:
                    updates = await self.get_updates(offset)
                    
                    if updates.get("ok"):
                        for update in updates.get("result", []):
                            offset = update["update_id"] + 1
                            
                            if "message" in update:
                                message = update["message"]
                                chat = message["chat"]
                                text = message.get("text", "")
                                
                                if text == "/id":
                                    chat_info = f"Chat ID: {chat['id']}"
                                    await self.send_message(chat["id"], chat_info)
                                    print(f"Sent chat ID {chat['id']} to user")
                                
                                elif text == "/start":
                                    welcome = "Bot running. Send /id in group."
                                    await self.send_message(chat["id"], welcome)
                    
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"Error: {e}")
                    await asyncio.sleep(5)
    
    async def fallback_main():
        if not TOKEN:
            print("Error: No TELEGRAM_BOT_TOKEN found in environment variables")
            return
            
        bot = SimpleTelegramBot(TOKEN)
        await bot.run()
    
    if __name__ == '__main__':
        asyncio.run(fallback_main())