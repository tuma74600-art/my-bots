import telebot
import sqlite3
import random
from telebot import types

# ================= НАСТРОЙКИ (ЗАМЕНИ ЭТО) =================
BOT_TOKEN = "9265394181:AAHpWlUaNDuaSayoPJ0HXRH69eoRJxs5wv0" 
ADMIN_ID = 7969267809
ADMIN_PASSWORD = "MYSOR_DROP_OT_HYPERGRAM"    
# ==========================================================

bot = telebot.TeleBot(BOT_TOKEN)

conn = sqlite3.connect('bot.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY, username TEXT, balance INTEGER DEFAULT 100,
    stars INTEGER DEFAULT 0, grams INTEGER DEFAULT 0, is_banned INTEGER DEFAULT 0, inventory TEXT DEFAULT ''
)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)''')
conn.commit()

def is_admin(user_id):
    if user_id == ADMIN_ID: return True
    cursor.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,))
    return cursor.fetchone() is not None

def get_user_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton('🚀 Старт'), types.KeyboardButton('👤 Профиль'), 
               types.KeyboardButton('🏆 Топ богачей'), types.KeyboardButton('🎰 Казино'), 
               types.KeyboardButton('⚙️ Админ-панель'))
    return markup

def get_admin_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton('🚫 Забанить'), types.KeyboardButton('✅ Разбанить'),
               types.KeyboardButton('⭐ Выдать звезды'), types.KeyboardButton('🌿 Выдать граммы'), 
               types.KeyboardButton('🎁 Выдать предмет'), types.KeyboardButton('🔙 Назад в меню'))
    return markup

@bot.message_handler(commands=['start'])
@bot.message_handler(func=lambda message: message.text == '🚀 Старт')
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    cursor.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    if res and res[0] == 1: return bot.send_message(message.chat.id, "🚫 Вы заблокированы.")
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    bot.send_message(message.chat.id, "👋 Привет! Бот работает.", reply_markup=get_user_menu())

@bot.message_handler(commands=['profile'])
@bot.message_handler(func=lambda message: message.text == '👤 Профиль')
def profile(message):
    cursor.execute("SELECT balance, stars, grams, inventory FROM users WHERE user_id = ?", (message.from_user.id,))
    ud = cursor.fetchone()
    if not ud: return bot.send_message(message.chat.id, "Напиши /start")
    bot.send_message(message.chat.id, f"👤 Профиль\n\n💰 Баланс: {ud[0]}\n⭐ Звезды: {ud[1]}\n🌿 Граммы: {ud[2]}\n🎒 Инвентарь: {ud[3] if ud[3] else 'Пусто'}")

@bot.message_handler(commands=['top'])
@bot.message_handler(func=lambda message: message.text == '🏆 Топ богачей')
def top(message):
    cursor.execute("SELECT username, balance FROM users ORDER BY balance DESC LIMIT 10")
    users = cursor.fetchall()
    text = "🏆 Топ богачей:\n\n"
    for i, (u, b) in enumerate(users, start=1):
        text += f"{i}. @{u if u else 'Аноним'} — {b} 💰\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['casino'])
@bot.message_handler(func=lambda message: message.text == '🎰 Казино')
def casino_info(message):
    bot.send_message(message.chat.id, "🎰 Введи сумму ставки командой:\n`/casino 100`", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text.startswith('/casino'))
def casino_game(message):
    args = message.text.split()
    if len(args) < 2: return bot.send_message(message.chat.id, "Формат: /casino 100")
    try: bet = int(args[1])
    except ValueError: return bot.send_message(message.chat.id, "Ставка должна быть числом.")
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (message.from_user.id,))
    res = cursor.fetchone()
    if not res or res[0] < bet: return bot.send_message(message.chat.id, "У тебя недостаточно денег.")
    if random.choice([True, False]):
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (bet, message.from_user.id))
        bot.send_message(message.chat.id, f"🎰 Ты выиграл {bet} монет! 🤑")
    else:
        cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (bet, message.from_user.id))
        bot.send_message(message.chat.id, f"🎰 Ты проиграл {bet} монет... 😭")
    conn.commit()

@bot.message_handler(commands=['admin'])
@bot.message_handler(func=lambda message: message.text == '⚙️ Админ-панель')
def admin_panel(message):
    if is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "⚙️ Админ-панель открыта.", reply_markup=get_admin_menu())
    else:
        bot.send_message(message.chat.id, "🔑 Введи пароль: `/admin ТВОЙ_ПАРОЛЬ`", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == '🔙 Назад в меню')
def back_to_menu(message):
    bot.send_message(message.chat.id, "Главное меню:", reply_markup=get_user_menu())

@bot.message_handler(func=lambda message: message.text in ['🚫 Забанить', '✅ Разбанить', '⭐ Выдать звезды', '🌿 Выдать граммы', '🎁 Выдать предмет'])
def admin_buttons_hint(message):
    if not is_admin(message.from_user.id): return
    hints = {
        '🚫 Забанить': "Напиши: `/ban ID`",
        '✅ Разбанить': "Напиши: `/unban ID`",
        '⭐ Выдать звезды': "Напиши: `/give_stars ID СУММА`",
        '🌿 Выдать граммы': "Напиши: `/give_grams ID СУММА`",
        '🎁 Выдать предмет': "Напиши: `/give_collect ID ПРЕДМЕТ`"
    }
    bot.send_message(message.chat.id, hints[message.text], parse_mode="Markdown")

@bot.message_handler(commands=['ban', 'unban', 'give_stars', 'give_grams', 'give_collect'])
def admin_commands(message):
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    cmd = args[0]
    
    if len(args) < 2: return bot.send_message(message.chat.id, "Не хватает аргументов.")
    
    try:
        target_id = int(args[1])
        if cmd == '/ban':
            cursor.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (target_id,))
            msg = "🚫 Забанен."
        elif cmd == '/unban':
            cursor.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (target_id,))
            msg = "✅ Разбанен."
        elif cmd == '/give_stars' and len(args) > 2:
            cursor.execute("UPDATE users SET stars = stars + ? WHERE user_id = ?", (int(args[2]), target_id))
            msg = "⭐ Выдано."
        elif cmd == '/give_grams' and len(args) > 2:
            cursor.execute("UPDATE users SET grams = grams + ? WHERE user_id = ?", (int(args[2]), target_id))
            msg = "🌿 Выдано."
        elif cmd == '/give_collect' and len(args) > 2:
            cursor.execute("SELECT inventory FROM users WHERE user_id = ?", (target_id,))
            inv = cursor.fetchone()
            if inv:
                new_inv = f"{inv[0]}, {args[2]}" if inv[0] else args[2]
                cursor.execute("UPDATE users SET inventory = ? WHERE user_id = ?", (new_inv, target_id))
                msg = "🎁 Выдан."
            else: msg = "Нет такого юзера."
        else:
            return bot.send_message(message.chat.id, "Неверный формат.")
            
        conn.commit()
        bot.send_message(message.chat.id, msg)
    except ValueError:
        bot.send_message(message.chat.id, "ID и сумма должны быть числами.")

print("Бот запущен...")
bot.infinity_polling()
