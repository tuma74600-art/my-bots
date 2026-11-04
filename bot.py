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

# --- ПОДКЛЮЧЕНИЕ ЧЕРЕЗ CLOUDFLARE (если надо, раскомментируй) ---
# telebot.apihelper.API_URL = "https://hyrepgram.tuma74600.workers.dev/bot{0}/{1}"

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

@bot.message_handler(func=lambda message: message.text == '❓ Помощь')
def help_menu(message):
    if check_banned(message): return
    bot.send_message(message.chat.id, "🆔 Чтобы узнать свой ID, напиши боту @userinfobot.", reply_markup=get_user_menu())

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

@bot.message_handler(commands=['nick'])
@bot.message_handler(func=lambda message: message.text == '✏️ Сменить ник')
def change_nick(message):
    if check_banned(message) or is_flooding(message.from_user.id): return
    msg = bot.send_message(message.chat.id, "📛 Введи свой новый ник для топа (ТОЛЬКО на английском, макс. 15 символов):")
    bot.register_next_step_handler(msg, process_my_nick)

def process_my_nick(message):
    if check_cancel(message): return bot.send_message(message.chat.id, "❌ Отмена.", reply_markup=get_user_menu())
    new_nick = message.text.strip()
    if len(new_nick) > 15: return bot.send_message(message.chat.id, "❌ Ник слишком длинный (макс. 15).", reply_markup=get_user_menu())
    if re.search('[а-яА-ЯёЁ]', new_nick): return bot.send_message(message.chat.id, "❌ Ошибка: Ник должен состоять только из английских букв!", reply_markup=get_user_menu())
    with db_lock:
        cursor.execute("UPDATE users SET custom_nickname = ? WHERE user_id = ?", (new_nick, message.from_user.id))
        conn.commit()
    bot.send_message(message.chat.id, f"✅ Твой новый ник: **{new_nick}**!", parse_mode="Markdown", reply_markup=get_user_menu())

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

@bot.message_handler(commands=['vip'])
@bot.message_handler(func=lambda message: message.text == '👑 VIP Меню')
def vip_menu(message):
    if check_banned(message) or is_flooding(message.from_user.id): return
    with db_lock:
        cursor.execute("SELECT is_vip FROM users WHERE user_id = ?", (message.from_user.id,))
        is_vip = cursor.fetchone()[0]
    if is_vip: bot.send_message(message.chat.id, "👑 **VIP-зона!**\n\nШанс победы: **65%**.\nБонус: **100 ⭐** в день.", reply_markup=get_vip_menu(), parse_mode="Markdown")
    else: bot.send_message(message.chat.id, "❌ У тебя нет VIP.\nКупи в магазине (`/buy vip`).", parse_mode="Markdown")

@bot.message_handler(commands=['vipbonus'])
@bot.message_handler(func=lambda message: message.text == '⭐ VIP Бонус')
def vip_bonus(message):
    if check_banned(message) or is_flooding(message.from_user.id): return
    with db_lock:
        cursor.execute("SELECT is_vip, last_vip_bonus FROM users WHERE user_id = ?", (message.from_user.id,))
        ud = cursor.fetchone()
    if not ud or ud[0] == 0: return bot.send_message(message.chat.id, "❌ У тебя нет VIP.")
    now = int(time.time())
    if now - ud[1] < 86400: return bot.send_message(message.chat.id, "⏳ Рано.")
    with db_lock:
        cursor.execute("UPDATE users SET stars = stars + 100, last_vip_bonus = ? WHERE user_id = ?", (now, message.from_user.id))
        conn.commit()
    bot.send_message(message.chat.id, "👑 Ты получил **100 ⭐**!", parse_mode="Markdown")

@bot.message_handler(commands=['bonus'])
@bot.message_handler(func=lambda message: message.text == '🎁 Бонус')
def daily_bonus(message):
    if check_banned(message) or is_flooding(message.from_user.id): return
    now = int(time.time())
    with db_lock:
        cursor.execute("SELECT last_bonus FROM users WHERE user_id = ?", (message.from_user.id,))
        last_b = cursor.fetchone()[0]
    if now - last_b < 86400: return bot.send_message(message.chat.id, "⏳ Рано.")
    bonus = random.randint(50, 200)
    with db_lock:
        cursor.execute("UPDATE users SET balance = balance + ?, last_bonus = ? WHERE user_id = ?", (bonus, now, message.from_user.id))
        conn.commit()
    bot.send_message(message.chat.id, f"🎁 Бонус: {bonus} монет!")

@bot.message_handler(commands=['shop'])
@bot.message_handler(func=lambda message: message.text == '🛒 Магазин')
def shop_info(message):
    if check_banned(message): return
    bot.send_message(message.chat.id, "🛒 Магазин\n\n👑 VIP (5000 ⭐) - `/buy vip`\n🎁 Коробка (500 ⭐) - `/buy box`", parse_mode="Markdown")

@bot.message_handler(commands=['buy'])
def buy_item(message):
    if check_banned(message): return
    args = message.text.split()
    if len(args) < 2: return
    item = args[1].lower()
    with db_lock:
        cursor.execute("SELECT stars, is_vip FROM users WHERE user_id = ?", (message.from_user.id,))
        ud = cursor.fetchone()
    if item == 'vip' and ud[1] == 0 and ud[0] >= 5000:
        with db_lock:
            cursor.execute("UPDATE users SET stars = stars - 5000, is_vip = 1 WHERE user_id = ?", (message.from_user.id,))
            conn.commit()
        bot.send_message(message.chat.id, "👑 Ты купил VIP!")
    elif item == 'box' and ud[0] >= 500:
        with db_lock:
            cursor.execute("UPDATE users SET stars = stars - 500 WHERE user_id = ?", (message.from_user.id,))
            conn.commit()
        luck = random.randint(1, 2)
        if luck == 1:
            prize = random.randint(100, 500)
            with db_lock:
                cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (prize, message.from_user.id))
                conn.commit()
            bot.send_message(message.chat.id, f"🎁 Ты нашел **{prize} монет**!", parse_mode="Markdown")
        else:
            with db_lock:
                cursor.execute("SELECT inventory FROM users WHERE user_id = ?", (message.from_user.id,))
                inv = cursor.fetchone()[0]
                cursor.execute("UPDATE users SET inventory = ? WHERE user_id = ?", (f"{inv}, НФТ" if inv else "НФТ", message.from_user.id))
                conn.commit()
            bot.send_message(message.chat.id, "🎁 Ты нашел **Редкий НФТ**!", parse_mode="Markdown")

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

@bot.message_handler(func=lambda message: message.text in ['🚫 Забанить', '✅ Разбанить', '🛑 Админ-бан', '🔄 Админ-разбан', '⭐ Выдать звезды', '🌿 Выдать граммы', '🎁 Выдать НФТ', '✏️ Выдать ник'])
def admin_buttons(message):
    if not is_admin(message.from_user.id): return
    prompts = {
        '🚫 Забанить': ("Напиши ID или @username кого забанить:", process_ban),
        '✅ Разбанить': ("Напиши ID или @username кого разбанить:", process_unban),
        '🛑 Админ-бан': ("Напиши ID или @username кого лишить админки:", process_aban),
        '🔄 Админ-разбан': ("Напиши ID или @username кого вернуть в админы:", process_aunban),
        '⭐ Выдать звезды': ("Напиши: `ID/@username СУММА`\n(например: `123456789 1000`):", process_stars),
        '🌿 Выдать граммы': ("Напиши: `ID/@username СУММА`\n(например: `@user 10`):", process_grams),
        '🎁 Выдать НФТ': ("Напиши: `ID/@username НАЗВАНИЕ`\n(например: `@user Крутой НФТ`):", process_nft),
        '✏️ Выдать ник': ("Напиши: `ID/@username НОВЫЙ_НИК`\n(например: `@user Boss`):", process_admin_nick)
    }
    text, next_func = prompts[message.text]
    msg = bot.send_message(message.chat.id, text, parse_mode="Markdown")
    bot.register_next_step_handler(msg, next_func)

def process_ban(message):
    if check_cancel(message): return bot.send_message(message.chat.id, "❌ Отмена.", reply_markup=get_admin_menu())
    target_id, display = find_target(message.text)
    if target_id == "self": target_id = message.from_user.id
    if not target_id: return bot.send_message(message.chat.id, "❌ Отмена (ошибка ввода).", reply_markup=get_admin_menu())
    if target_id == ADMIN_ID: return bot.send_message(message.chat.id, "❌ Создателя нельзя банить!", reply_markup=get_admin_menu())
    with db_lock:
        cursor.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (target_id,))
        conn.commit()
    bot.send_message(message.chat.id, f"🚫 {display} забанен.", reply_markup=get_admin_menu())

def process_unban(message):
    if check_cancel(message): return bot.send_message(message.chat.id, "❌ Отмена.", reply_markup=get_admin_menu())
    target_id, display = find_target(message.text)
    if target_id == "self": target_id = message.from_user.id
    if not target_id: return bot.send_message(message.chat.id, "❌ Отмена (ошибка ввода).", reply_markup=get_admin_menu())
    with db_lock:
        cursor.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (target_id,))
        conn.commit()
    bot.send_message(message.chat.id, f"✅ {display} разбанен.", reply_markup=get_admin_menu())

def process_aban(message):
    if check_cancel(message): return bot.send_message(message.chat.id, "❌ Отмена.", reply_markup=get_admin_menu())
    target_id, display = find_target(message.text)
    if target_id == "self": target_id = message.from_user.id
    if not target_id: return bot.send_message(message.chat.id, "❌ Отмена (ошибка ввода).", reply_markup=get_admin_menu())
    if target_id == ADMIN_ID: return bot.send_message(message.chat.id, "❌ Создателя нельзя банить!", reply_markup=get_admin_menu())
    with db_lock:
        cursor.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (target_id,))
        conn.commit()
    bot.send_message(message.chat.id, f"🛑 Админ {display} забанен.", reply_markup=get_admin_menu())

def process_aunban(message):
    if check_cancel(message): return bot.send_message(message.chat.id, "❌ Отмена.", reply_markup=get_admin_menu())
    target_id, display = find_target(message.text)
    if target_id == "self": target_id = message.from_user.id
    if not target_id: return bot.send_message(message.chat.id, "❌ Отмена (ошибка ввода).", reply_markup=get_admin_menu())
    with db_lock:
        cursor.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (target_id,))
        conn.commit()
    bot.send_message(message.chat.id, f"🔄 Админ {display} разбанен.", reply_markup=get_admin_menu())

def process_stars(message):
    if check_cancel(message): return bot.send_message(message.chat.id, "❌ Отмена.", reply_markup=get_admin_menu())
    args = message.text.split()
    if len(args) < 2: return bot.send_message(message.chat.id, "❌ Отмена (неверный формат).", reply_markup=get_admin_menu())
    target_id, display = find_target(args[0])
    if target_id == "self": target_id = message.from_user.id
    if not target_id: return bot.send_message(message.chat.id, "❌ Отмена (ошибка ввода).", reply_markup=get_admin_menu())
    try: amount = int(args[1])
    except: return bot.send_message(message.chat.id, "❌ Отмена (нужна сумма).", reply_markup=get_admin_menu())
    if amount > 10000: return bot.send_message(message.chat.id, "❌ Максимум 10000 за раз!", reply_markup=get_admin_menu())
    with db_lock:
        cursor.execute("UPDATE users SET stars = stars + ? WHERE user_id = ?", (amount, target_id))
        conn.commit()
    bot.send_message(message.chat.id, f"⭐ Выдано {amount} звезд: {display}.", reply_markup=get_admin_menu())

def process_grams(message):
    if check_cancel(message): return bot.send_message(message.chat.id, "❌ Отмена.", reply_markup=get_admin_menu())
    args = message.text.split()
    if len(args) < 2: return bot.send_message(message.chat.id, "❌ Отмена (неверный формат).", reply_markup=get_admin_menu())
    target_id, display = find_target(args[0])
    if target_id == "self": target_id = message.from_user.id
    if not target_id: return bot.send_message(message.chat.id, "❌ Отмена (ошибка ввода).", reply_markup=get_admin_menu())
    try: amount = int(args[1])
    except: return bot.send_message(message.chat.id, "❌ Отмена (нужна сумма).", reply_markup=get_admin_menu())
    with db_lock:
        cursor.execute("UPDATE users SET grams = grams + ? WHERE user_id = ?", (amount, target_id))
        conn.commit()
    bot.send_message(message.chat.id, f"🌿 Выдано {amount} грамм: {display}.", reply_markup=get_admin_menu())

def process_nft(message):
    if check_cancel(message): return bot.send_message(message.chat.id, "❌ Отмена.", reply_markup=get_admin_menu())
    args = message.text.split(maxsplit=1)
    if len(args) < 2: return bot.send_message(message.chat.id, "❌ Отмена (неверный формат).", reply_markup=get_admin_menu())
    target_id, display = find_target(args[0])
    if target_id == "self": target_id = message.from_user.id
    if not target_id: return bot.send_message(message.chat.id, "❌ Отмена (ошибка ввода).", reply_markup=get_admin_menu())
    item_name = args[1]
    with db_lock:
        cursor.execute("SELECT inventory FROM users WHERE user_id = ?", (target_id,))
        inv = cursor.fetchone()[0]
        new_inv = f"{inv}, {item_name}" if inv else item_name
        cursor.execute("UPDATE users SET inventory = ? WHERE user_id = ?", (new_inv, target_id))
        conn.commit()
    bot.send_message(message.chat.id, f"🎁 НФТ '{item_name}' выдан: {display}.", reply_markup=get_admin_menu())

def process_admin_nick(message):
    if check_cancel(message): return bot.send_message(message.chat.id, "❌ Отмена.", reply_markup=get_admin_menu())
    args = message.text.split(maxsplit=1)
    if len(args) < 2: return bot.send_message(message.chat.id, "❌ Отмена (неверный формат).", reply_markup=get_admin_menu())
    target_id, display = find_target(args[0])
    if target_id == "self": target_id = message.from_user.id
    if not target_id: return bot.send_message(message.chat.id, "❌ Отмена (ошибка ввода).", reply_markup=get_admin_menu())
    new_nick = args[1].strip()
    if len(new_nick) > 15: return bot.send_message(message.chat.id, "❌ Ник слишком длинный (макс. 15).", reply_markup=get_admin_menu())
    if re.search('[а-яА-ЯёЁ]', new_nick): return bot.send_message(message.chat.id, "❌ Ошибка: Ник должен быть на английском!", reply_markup=get_admin_menu())
    with db_lock:
        cursor.execute("UPDATE users SET custom_nickname = ? WHERE user_id = ?", (new_nick, target_id))
        conn.commit()
    bot.send_message(message.chat.id, f"📛 {display} выдан новый ник: **{new_nick}**", parse_mode="Markdown", reply_markup=get_admin_menu())

# ВНИМАНИЕ: Ниже нет bot.polling(), так как мы запускаем его через app.py!
