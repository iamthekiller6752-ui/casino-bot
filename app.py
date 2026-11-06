import os
import asyncio
import logging
from threading import Thread
from flask import Flask
from bot import bot, dp
import database as db

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

@app.route('/')
@app.route('/health')
def home():
    return "Bot is alive", 200

def start_bot():
    async def _run():
        await db.init_db()
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, handle_signals=False)
    asyncio.run(_run())

if __name__ == "__main__":
    Thread(target=start_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
