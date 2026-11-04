`python
import sqlite3
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

TOKEN="9265394181:AAHZ9RJE-Fl6feCiBCbpn_R1oVXBCqc8b6E"
ADMIN_ID = "7969267809"
ADMIN_CODE= "HYPER-7429-ADMIN"

db = sqlite3.connect("bot.db", check_same_thread=False)
db.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    coins INTEGER DEFAULT 1000,
    stars INTEGER DEFAULT 0
)
""")
db.commit()

waiting_for_code = set()


def add_user(user):
    db.execute(
        "INSERT OR IGNORE INTO users (user_id, name) VALUES (?, ?)",
        (user.id, user.first_name or "Игрок")
    )
    db.commit()


def menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎰 Казино", callback_data="casino"),
            InlineKeyboardButton("🏆 Топ богачей", callback_data="top"),
        ],
        [
            InlineKeyboardButton("⭐ Мои звёзды", callback_data="stars"),
            InlineKeyboardButton("💰 Баланс", callback_data="balance"),
        ],
        [
            InlineKeyboardButton("🛠 Админ-панель", callback_data="admin"),
        ],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user(update.effective_user)
    await update.message.reply_text(
        "Привет! Я Hypergrambot.\nВыбирай действие в меню:",
        reply_markup=menu()
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    add_user(user)

    if query.data == "balance":
        row = db.execute(
            "SELECT coins FROM users WHERE user_id = ?", (user.id,)
        ).fetchone()
        await query.message.reply_text(
            f"💰 Твой баланс: {row[0]} монет",
            reply_markup=menu()
        )

    elif query.data == "stars":
        row = db.execute(
            "SELECT stars FROM users WHERE user_id = ?", (user.id,)
        ).fetchone()
        await query.message.reply_text(
            f"⭐ У тебя звёзд: {row[0]}",
            reply_markup=menu()
        )

    elif query.data == "casino":
        row = db.execute(
            "SELECT coins FROM users WHERE user_id = ?", (user.id,)
      
        coins = row[0]

        if coins < 100:
            await query.message.reply_text(
                "Нужно минимум 100 монет для игры.",
                reply_markup=menu()
            )
            return

        numbers = [random.randint(1, 9) for _ in range(3)]

        if numbers[0] == numbers[1] == numbers[2]:
            prize = 1000
            result = "ДЖЕКПОТ!"
        elif len(set(numbers)) == 2:
            prize = 250
            result = "Неплохо! Два одинаковых."
        else:
    
