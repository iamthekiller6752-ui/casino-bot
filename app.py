import os
import asyncio
import logging
from threading import Thread
from flask import Flask
from bot import bot, dp

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

@app.route('/')
@app.route('/health')
def home():
    return "Bot is alive", 200

def start_bot():
    async def _run():
        # Сбрасываем вебхук, чтобы не было конфликтов
        await bot.delete_webhook(drop_pending_updates=True)
        # ГЛАВНЫЙ ФИКС: handle_signals=False
        await dp.start_polling(bot, drop_pending_updates=True, handle_signals=False)

    try:
        asyncio.run(_run())
    except Exception as e:
        logging.exception("Бот упал: %s", e)

if __name__ == "__main__":
    Thread(target=start_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
