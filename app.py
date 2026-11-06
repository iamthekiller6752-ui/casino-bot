import os
import asyncio
from threading import Thread
from flask import Flask
from bot import bot, dp

app = Flask(__name__)

@app.route('/')
@app.route('/health')
def home():
    return "Bot is alive", 200

def start_bot():
    asyncio.run(dp.start_polling(bot))

if __name__ == "__main__":
    Thread(target=start_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)