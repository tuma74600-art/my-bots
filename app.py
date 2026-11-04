import telebot
import sqlite3
import random
import time
import re
import threading
from telebot import types

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "9011759800:AAHDc5BkcZ1j6hNVJ-kSTVdm-xNd328I-n8" 
ADMIN_ID = 7969267809 # Твой ID
ADMIN_PASSWORD = "admin123"    
# ============================================

telebot.apihelper.API_URL = "https://hyrepgram.tuma74600.workers.dev/bot{0}/{1}"
bot = telebot.TeleBot(BOT_TOKEN)

conn = sqlite3.connect('bot.db', check_same_thread=False)
cursor = conn.cursor()
db_lock = threading.Lock()

cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY, username TEXT, balance INTEGER DEFAULT 100,
    stars INTEGER DEFAULT 0, grams INTEGER DEFAULT 0, is_banned INTEGER DEFAULT 0, inventory TEXT DEFAULT '', 
    last_bonus INTEGER DEFAULT 0, is_vip INTEGER DEFAULT 0, last_vip_bonus INTEGER DEFAULT 0,
    custom_nickname TEXT DEFAULT NULL
)''')
try: cursor.execute("ALTER TABLE users ADD COLUMN is_vip INTEGER DEFAULT 0")
except: pass
try: cursor.execute("ALTER TABLE users ADD COLUMN last_vip_bonus INTEGER DEFAULT 0")
except: pass
try: cursor.execute("ALTER TABLE users ADD COLUMN custom_nickname TEXT DEFAULT NULL")
except: pass
cursor.execute('''CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)''')
conn.commit()

user_last_action = {}

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def is_admin(user_id):
    if user_id == ADMIN_ID: return True
    with db_lock:
        cursor.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,))
        if not cursor.fetchone(): return False
        cursor.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
        res = cursor.fetchone()
        if res and res[0] == 1: return False 
    return True

def check_banned(message):
    if message.from_user.id == ADMIN_ID: return False
    with db_lock:
        cursor.execute("SELECT is_banned FROM users WHERE user_id = ?", (message.from_user.id,))
        res = cursor.fetchone()
    if res and res[0] == 1:
        bot.send_message(message.chat.id, "🚫 Вы заблокированы.")
        return True
    return False

def is_flooding(user_id):
    now = time.time()
    if user_id in user_last_action:
        if now - user_last_action[user_id] < 1.0: return True
    user_last_action[user_id] = now
    return False

def find_target(text):
    text = text.strip()
    if text.lower() in ['себе', 'me', 'self']: return "self", "себе"
    clean_target = text[1:] if text.startswith('@') else text
    if clean_target.isdigit(): return int(clean_target), text
    else:
        with db_lock:
            cursor.execute("SELECT user_id FROM users WHERE LOWER(username) = LOWER(?)", (clean_target,))
            res = cursor.fetchone()
        if res: return res[0], f"@{clean_target}"
        return None, text

def check_cancel(message):
    menu_buttons = ['🚀 Старт', '👤 Профиль', '✏️ Сменить ник', '🏆 Топ богачей', '🎲 Играть', '🛒 Магазин', '🎁 Бонус', '👑 VIP Меню', '❓ Помощь', '⚙️ Админ-панель', '🔙 Назад в меню', '🚫 Забанить', '✅ Разбанить', '🛑 Админ-бан', '🔄 Админ-разбан', '⭐ Выдать звезды', '🌿 Выдать граммы', '🎁 Выдать НФТ', '✏️ Выдать ник', '⭐ VIP Бонус']
    if message.text in menu_buttons or message.text.startswith('/'): return True
    return False

# --- КЛАВИАТУРЫ ---
def get_user_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton('🚀 Старт'), types.KeyboardButton('👤 Профиль'), types.KeyboardButton('✏️ Сменить ник'), types.KeyboardButton('🏆 Топ богачей'), types.KeyboardButton('🎲 Играть'), types.KeyboardButton('🛒 Магазин'), types.KeyboardButton('🎁 Бонус'), types.KeyboardButton('👑 VIP Меню'), types.KeyboardButton('❓ Помощь'), types.KeyboardButton('⚙️ Админ-панель'))
    return markup

def get_vip_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton('⭐ VIP Бонус'), types.KeyboardButton('🔙 Назад в меню'))
    return markup

def get_admin_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton('🚫 Забанить'), types.KeyboardButton('✅ Разбанить'), types.KeyboardButton('🛑 Админ-бан'), types.KeyboardButton('🔄 Админ-разбан'), types.KeyboardButton('⭐ Выдать звезды'), types.KeyboardButton('🌿 Выдать граммы'), types.KeyboardButton('🎁 Выдать НФТ'), types.KeyboardButton('✏️ Выдать ник'), types.KeyboardButton('🔙 Назад в меню'))
    return markup

# --- КОМАНДЫ ---
@bot.message_handler(commands=['start'])
@bot.message_handler(func=lambda message: message.text == '🚀 Старт')
def start(message):
    if check_banned(message) or is_flooding(message.from_user.id): return
    with db_lock:
        cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (message.from_user.id, message.from_user.username))
        cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (message.from_user.username, message.from_user.id))
        conn.commit()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
    msg = bot.send_message(message.chat.id, f"👋 Привет! Добро пожаловать в Hypergram.\n\n👥 Нас уже: **{total_users}** человек!", parse_mode="Markdown", reply_markup=get_user_menu())
    try: bot.pin_chat_message(message.chat.id, msg.message_id, disable_notification=True)
    except: pass

@bot.message_handler(commands=['profile'])
@bot.message_handler(func=lambda message: message.text == '👤 Профиль')
def profile(message):
    if check_banned(message) or is_flooding(message.from_user.id): return
    with db_lock:
        cursor.execute("SELECT balance, stars, grams, inventory, is_vip, custom_nickname FROM users WHERE user_id = ?", (message.from_user.id,))
        ud = cursor.fetchone()
    if not ud: return bot.send_message(message.chat.id, "Напиши /start")
    vip_status = "👑 (VIP)" if ud[4] else ""
    nick = ud[5] if ud[5] else "Не задан"
    bot.send_message(message.chat.id, f"👤 Профиль {vip_status}\n\n📛 Ник: {nick}\n💰 Баланс: {ud[0]}\n⭐ Звезды: {ud[1]}\n🌿 Граммы: {ud[2]}\n🎒 Инвентарь: {ud[3] if ud[3] else 'Пусто'}")

@bot.message_handler(commands=['top'])
@bot.message_handler(func=lambda message: message.text == '🏆 Топ богачей')
def top(message):
    if check_banned(message) or is_flooding(message.from_user.id): return
    with db_lock:
        cursor.execute("SELECT username, balance, stars, is_vip, custom_nickname FROM users ORDER BY (balance + stars) DESC LIMIT 10")
        users = cursor.fetchall()
    text = "🏆 Топ богачей Hypergram:\n\n"
    for i, (u, b, s, vip, nick) in enumerate(users, start=1):
        crown = "👑 " if vip else ""
        display_name = nick if nick else (f"@{u}" if u else "Аноним")
        text += f"{i}. {crown}{display_name} — {b} 💰 и {s} ⭐\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['game'])
@bot.message_handler(func=lambda message: message.text == '🎲 Играть')
def game_info(message):
    if check_banned(message) or is_flooding(message.from_user.id): return
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(types.InlineKeyboardButton('10', callback_data='bet_10'), types.InlineKeyboardButton('50', callback_data='bet_50'), types.InlineKeyboardButton('100', callback_data='bet_100'), types.InlineKeyboardButton('500', callback_data='bet_500'), types.InlineKeyboardButton('🔥 Ва-банк', callback_data='bet_all'))
    bot.send_message(message.chat.id, "🎲 **Выбери ставку:**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('bet_'))
def game_callback(call):
    if check_banned(call.message): return
    user_id = call.from_user.id
    with db_lock:
        cursor.execute("SELECT balance, is_vip FROM users WHERE user_id = ?", (user_id,))
        ud = cursor.fetchone()
    balance, is_vip = ud[0], ud[1]
    bet = balance if call.data == 'bet_all' else int(call.data.split('_')[1])
    if bet <= 0 or balance < bet: return bot.answer_callback_query(call.id, "❌ Мало монет!", show_alert=True)
    win_chance = 0.65 if is_vip else 0.50
    with db_lock:
        if random.random() < win_chance:
            cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (bet, user_id))
            res = f"🎉 Выиграл **{bet} монет**!"
        else:
            cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (bet, user_id))
            res = f"💸 Проиграл **{bet} монет**..."
        conn.commit()
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"🎲 {res}", parse_mode="Markdown")
    bot.answer_callback_query(call.id, "Готово!")

@bot.message_handler(commands=['admin'])
@bot.message_handler(func=lambda message: message.text == '⚙️ Админ-панель')
def handle_admin(message):
    if check_banned(message): return
    if message.text in ['⚙️ Админ-панель', '/admin']:
        if is_admin(message.from_user.id): 
            with db_lock:
                cursor.execute("SELECT COUNT(*) FROM users")
                total_users = cursor.fetchone()[0]
            bot.send_message(message.chat.id, f"⚙️ Меню:\n👥 Всего пользователей: {total_users}", reply_markup=get_admin_menu())
        else: bot.send_message(message.chat.id, "🔑 Введи: `/admin пароль`", parse_mode="Markdown")
        return
    args = message.text.split()
    if len(args) > 1 and args[1] == ADMIN_PASSWORD:
        with db_lock:
            cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (message.from_user.id,))
            conn.commit()
        bot.send_message(message.chat.id, "✅ Доступ разрешен.", reply_markup=get_admin_menu())

@bot.message_handler(func=lambda message: message.text == '🔙 Назад в меню')
def back_to_menu(message):
    if check_banned(message): return
    bot.send_message(message.chat.id, "Главное меню:", reply_markup=get_user_menu())
