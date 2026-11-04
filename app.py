import os
import threading
from flask import Flask
from bot import bot as main_bot

app = Flask(__name__)

@app.route('/')
def health():
    return "Bot is running", 200

def run_bot():
    main_bot.polling(non_stop=True)

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
