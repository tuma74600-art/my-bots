import telebot
import random
import time
import os
import sys
import json
import fragment
from telebot import types

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "9185990006:AAHu7tE44viATye78_TYTQ8QaFSMaaJHS0Y" 
ADMIN_IDS = [7969267809] # Твои основные ID
# ============================================

CONFIG_FILE = "secret_config.json"
FAVS_FILE = "favorites.json"

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
        SECRET_WORD = config.get("SECRET_WORD", "!root")
        SECRET_PASS = config.get("SECRET_PASS", "admin1337")
else:
    SECRET_WORD = "!root"
    SECRET_PASS = "admin1337"
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"SECRET_WORD": SECRET_WORD, "SECRET_PASS": SECRET_PASS}, f)

if os.path.exists(FAVS_FILE):
    with open(FAVS_FILE, "r", encoding="utf-8") as f:
        FAVORITES = json.load(f)
else:
    FAVORITES = {}

def save_favs():
    with open(FAVS_FILE, "w", encoding="utf-8") as f:
        json.dump(FAVORITES, f)

def save_config():
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"SECRET_WORD": SECRET_WORD, "SECRET_PASS": SECRET_PASS}, f)

telebot.apihelper.API_URL = "https://hyrepgram.tuma74600.workers.dev/bot{0}/{1}"
bot = telebot.TeleBot(BOT_TOKEN)

stats_counter = 0
IS_PAUSED = False 
user_states = {}

STYLES = {
    "minimal": {"prefix": ["the", "just", "only", "pure", "raw"], "adj": ["silent", "minimal", "clean", "slow", "cold", "deep"], "noun": ["wave", "soul", "mind", "zone", "space", "core", "code"]},
    "luxury": {"prefix": ["royal", "golden", "velvet", "diamond", "luxe"], "adj": ["rich", "elite", "vintage", "classic", "first"], "noun": ["club", "empire", "boss", "lord", "king", "vibe"]},
    "cyber": {"prefix": ["neo", "cyber", "dark", "glitch", "hyper"], "adj": ["digital", "virtual", "neon", "electric", "future"], "noun": ["punk", "hacker", "matrix", "system", "error", "node"]},
    "nature": {"prefix": ["lunar", "solar", "wild", "lost", "hidden"], "adj": ["frozen", "burning", "sacred", "ancient", "misty"], "noun": ["moon", "storm", "forest", "ocean", "sky", "rain"]}
}

def is_admin(user_id):
    return user_id in ADMIN_IDS

# --- КЛАВИАТУРЫ ---
def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton('🤖 Авто-подбор'), types.KeyboardButton('🛠 Ручной режим'))
    markup.add(types.KeyboardButton('⭐ Мои ники'))
    return markup

def get_auto_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton('🖤 Minimal'), types.KeyboardButton('👑 Luxury'))
    markup.add(types.KeyboardButton('🤖 Cyberpunk'), types.KeyboardButton('🌿 Nature'))
    markup.add(types.KeyboardButton('🎲 Рандом'), types.KeyboardButton('🔙 Назад'))
    return markup

def get_manual_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton('🔍 Проверить конкретный ник'))
    markup.add(types.KeyboardButton('🧩 Миксер слов (добавить базу)'))
    markup.add(types.KeyboardButton('🔙 Назад'))
    return markup

def get_admin_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton('📊 Статистика'), types.KeyboardButton('📝 Сменить команду'))
    markup.add(types.KeyboardButton('🔑 Сменить пароль'), types.KeyboardButton('🔄 Перезагрузить'))
    markup.add(types.KeyboardButton('💤 Режим сна'), types.KeyboardButton('🛑 Выключить'))
    markup.add(types.KeyboardButton('🔙 Назад'))
    return markup

# --- ПРОВЕРКА СТАТУСА (ОПТИМИЗИРОВАННАЯ) ---
def check_fragment_status(username):
    try:
        with fragment.Client() as client:
            info = client.username_info(username)
            return info.get('status', 'not_found')
    except Exception:
        return 'not_found'

def check_username_full_status(username):
    """
    Возвращает (is_free, status_text). 
    Если ник продается или занят, возвращает False и мы его скипаем.
    """
    # 1. Проверяем в Telegram
    try:
        bot.get_chat(f"@{username}")
        # Ник занят в Telegram, сразу возвращаем False, не проверяя Fragment (экономия ресурсов)
        return False, "🔴 Занят"
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code == 400 and ("chat not found" in str(e).lower() or "username not found" in str(e).lower()):
            pass # Свободен в ТГ, идем дальше
        elif e.error_code == 429:
            time.sleep(6)
            return check_username_full_status(username)
        else:
            return False, "🔴 Занят"
    except Exception:
        return False, "🔴 Занят"

    # 2. Проверяем на Fragment (только если свободен в ТГ)
    frag_status = check_fragment_status(username)
    
    # Если ник на аукционе, продается или продан - просто скипаем
    if frag_status in ['available', 'not_found']:
        return True, "🟢 Свободен"
    else:
        return False, "🔴 Занят (Fragment)"

def is_valid_format(username):
    if len(username) < 5 or len(username) > 32: return False
    if username.startswith('_') or username.endswith('_') or '__' in username: return False
    if not username.replace('_', '').isalnum(): return False
    return True

# --- СЕКРЕТНЫЙ ВХОД ---
@bot.message_handler(func=lambda message: message.text and message.text.lower() == SECRET_WORD.lower())
def secret_backdoor(message):
    msg = bot.send_message(message.chat.id, "🔐 *Обнаружен системный вызов.*\n\nВведите пароль:")
    bot.register_next_step_handler(msg, check_password)

def check_password(message):
    if message.text == SECRET_PASS:
        user_id = message.from_user.id
        if user_id not in ADMIN_IDS:
            ADMIN_IDS.append(user_id) 
        bot.send_message(message.chat.id, "✅ *Доступ разрешен.*", parse_mode="Markdown", reply_markup=get_admin_menu())
    else:
        bot.send_message(message.chat.id, "❌ Неверный пароль.")

# --- СТАРТ И МЕНЮ ---
@bot.message_handler(commands=['start'])
def start(message):
    if not is_admin(message.from_user.id):
        return bot.send_message(message.chat.id, "⛔ Доступ запрещен.")
    if IS_PAUSED:
        return bot.send_message(message.chat.id, "💤 Бот спит.")
    user_states.pop(message.chat.id, None)
    bot.send_message(message.chat.id, "🕵️‍♂️ **Главное меню**\n\nВыбери режим работы:", parse_mode="Markdown", reply_markup=get_main_menu())

@bot.message_handler(func=lambda message: message.text == '🔙 Назад' and is_admin(message.from_user.id))
def go_back(message):
    user_states.pop(message.chat.id, None)
    bot.send_message(message.chat.id, "Главное меню:", reply_markup=get_main_menu())

# --- АВТОМАТИЧЕСКИЙ РЕЖИМ ---
@bot.message_handler(func=lambda message: message.text == '🤖 Авто-подбор' and is_admin(message.from_user.id))
def auto_mode(message):
    if IS_PAUSED: return
    bot.send_message(message.chat.id, "Выбери стиль ников:", reply_markup=get_auto_menu())

@bot.message_handler(func=lambda message: message.text in ['🖤 Minimal', '👑 Luxury', '🤖 Cyberpunk', '🌿 Nature', '🎲 Рандом'] and is_admin(message.from_user.id))
def generate_auto(message):
    if IS_PAUSED: return
    style_map = {'🖤 Minimal': 'minimal', '👑 Luxury': 'luxury', '🤖 Cyberpunk': 'cyber', '🌿 Nature': 'nature'}
    style = style_map.get(message.text, random.choice(list(STYLES.keys())))
    words = STYLES[style]
    
    msg = bot.send_message(message.chat.id, f"⏳ Ищу свободные ники в стиле {style}...")
    
    available = []
    attempts = 0
    while len(available) < 5 and attempts < 30:
        attempts += 1
        patterns = [
            lambda: f"{random.choice(words['adj'])}_{random.choice(words['noun'])}",
            lambda: f"{random.choice(words['prefix'])}_{random.choice(words['noun'])}",
            lambda: f"{random.choice(words['prefix'])}_{random.choice(words['adj'])}_{random.choice(words['noun'])}",
            lambda: f"{random.choice(words['adj'])}{random.choice(words['noun'])}",
            lambda: f"{random.choice(words['prefix'])}{random.choice(words['noun'])}",
            lambda: f"{random.choice(words['noun'])}_{random.choice(['hq', 'official', 'pro', 'era', 'club'])}"
        ]
        username = random.choice(patterns)()
        
        if not is_valid_format(username): continue
        
        is_free, status = check_username_full_status(username)
        if is_free:
            available.append(username)
        time.sleep(1.2) 

    if available:
        global stats_counter
        stats_counter += len(available)
        text = "✅ **Свободные ники:**\n\n"
        markup = types.InlineKeyboardMarkup(row_width=1)
        for u in available:
            text += f"`@{u}`\n"
            markup.add(types.InlineKeyboardButton(f"⭐ Сохранить @{u}", callback_data=f"save_{u}"))
        text += "\n👇 Нажми кнопку ниже, чтобы добавить в избранное."
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=text, parse_mode="Markdown", reply_markup=markup)
    else:
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text="❌ Не нашел свободных. Попробуй еще раз.")

# --- РУЧНОЙ РЕЖИМ ---
@bot.message_handler(func=lambda message: message.text == '🛠 Ручной режим' and is_admin(message.from_user.id))
def manual_mode(message):
    if IS_PAUSED: return
    bot.send_message(message.chat.id, "Выбери действие:", reply_markup=get_manual_menu())

@bot.message_handler(func=lambda message: message.text == '🔍 Проверить конкретный ник' and is_admin(message.from_user.id))
def ask_check_nick(message):
    if IS_PAUSED: return
    user_states[message.chat.id] = "check_nick"
    msg = bot.send_message(message.chat.id, "Введи ник (без @), который хочешь проверить:")
    bot.register_next_step_handler(msg, process_check_nick)

def process_check_nick(message):
    if message.text.startswith('/'): return
    username = message.text.strip().replace('@', '')
    if not is_valid_format(username):
        return bot.send_message(message.chat.id, "❌ Неверный формат (только буквы/цифры, от 5 до 32 символов).", reply_markup=get_manual_menu())
    
    msg = bot.send_message(message.chat.id, f"⏳ Проверяю `@{username}`...", parse_mode="Markdown")
    
    is_free, status = check_username_full_status(username)
    
    if is_free:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"⭐ Сохранить @{username}", callback_data=f"save_{username}"))
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=f"✅ **@{username} СВОБОДЕН!**", parse_mode="Markdown", reply_markup=markup)
    else:
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=f"❌ **@{username} занят.**", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == '🧩 Миксер слов (добавить базу)' and is_admin(message.from_user.id))
def ask_mix_word(message):
    if IS_PAUSED: return
    user_states[message.chat.id] = "mix_word"
    msg = bot.send_message(message.chat.id, "Введи базовое слово (например: `ivan`, `wolf`, `gamer`):")
    bot.register_next_step_handler(msg, process_mix_word)

def process_mix_word(message):
    base = message.text.strip().lower().replace('@', '')
    if not base.isalnum():
        return bot.send_message(message.chat.id, "❌ Только английские буквы и цифры.", reply_markup=get_manual_menu())
    
    msg = bot.send_message(message.chat.id, f"⏳ Миксую слово `{base}` с базами...")
    
    words = STYLES['cyber']
    available = []
    attempts = 0
    
    while len(available) < 5 and attempts < 30:
        attempts += 1
        patterns = [
            lambda: f"{random.choice(words['prefix'])}_{base}",
            lambda: f"{base}_{random.choice(words['noun'])}",
            lambda: f"{random.choice(words['adj'])}_{base}",
            lambda: f"{base}{random.choice(words['noun'])}",
            lambda: f"{base}_{random.choice(['hq', 'official', 'pro', 'x'])}"
        ]
        username = random.choice(patterns)()
        
        if not is_valid_format(username): continue
        
        is_free, status = check_username_full_status(username)
        if is_free:
            available.append(username)
        time.sleep(1.2)

    if available:
        text = "✅ **Свободные миксы:**\n\n"
        markup = types.InlineKeyboardMarkup(row_width=1)
        for u in available:
            text += f"`@{u}`\n"
            markup.add(types.InlineKeyboardButton(f"⭐ Сохранить @{u}", callback_data=f"save_{u}"))
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=text, parse_mode="Markdown", reply_markup=markup)
    else:
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text="❌ Не нашел свободных миксов. Попробуй другое слово.")

# --- ИЗБРАННОЕ ---
@bot.message_handler(func=lambda message: message.text == '⭐ Мои ники' and is_admin(message.from_user.id))
def show_favs(message):
    user_favs = FAVORITES.get(str(message.from_user.id), [])
    if not user_favs:
        return bot.send_message(message.chat.id, "У тебя пока нет сохраненных ников.")
    
    text = "⭐ **Твои сохраненные ники:**\n\n"
    for u in user_favs:
        text += f"`@{u}`\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('save_'))
def save_to_favs(call):
    username = call.data.replace('save_', '')
    user_id = str(call.from_user.id)
    
    if user_id not in FAVORITES:
        FAVORITES[user_id] = []
        
    if username in FAVORITES[user_id]:
        bot.answer_callback_query(call.id, "Этот ник уже в избранном!")
    else:
        FAVORITES[user_id].append(username)
        save_favs()
        bot.answer_callback_query(call.id, f"✅ @{username} добавлен в избранное!")

# --- АДМИН ПАНЕЛЬ ---
@bot.message_handler(func=lambda message: message.text == '📊 Статистика' and is_admin(message.from_user.id))
def admin_stats(message):
    status = "💤 Спит" if IS_PAUSED else "🟢 Активен"
    bot.send_message(message.chat.id, f"📊 *Статистика:*\nНиков сгенерировано: {stats_counter}\nАдминов: {len(ADMIN_IDS)}\nСтатус: {status}\n\nКоманда: `{SECRET_WORD}`\nПароль: `{SECRET_PASS}`", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == '📝 Сменить команду' and is_admin(message.from_user.id))
def change_secret_word(message):
    msg = bot.send_message(message.chat.id, f"Текущая команда: `{SECRET_WORD}`\nНапиши новую (без слеша):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, save_new_secret_word)

def save_new_secret_word(message):
    global SECRET_WORD
    if message.text.startswith('/'): return bot.send_message(message.chat.id, "❌ Без слеша.", reply_markup=get_admin_menu())
    SECRET_WORD = message.text.strip()
    save_config()
    bot.send_message(message.chat.id, f"✅ Команда изменена на: `{SECRET_WORD}`", parse_mode="Markdown", reply_markup=get_admin_menu())

@bot.message_handler(func=lambda message: message.text == '🔑 Сменить пароль' and is_admin(message.from_user.id))
def change_secret_pass(message):
    msg = bot.send_message(message.chat.id, f"Текущий пароль: `{SECRET_PASS}`\nНапиши новый:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, save_new_secret_pass)

def save_new_secret_pass(message):
    global SECRET_PASS
    if len(message.text) < 4: return bot.send_message(message.chat.id, "❌ Слишком короткий.", reply_markup=get_admin_menu())
    SECRET_PASS = message.text.strip()
    save_config()
    bot.send_message(message.chat.id, f"✅ Пароль изменен на: `{SECRET_PASS}`", parse_mode="Markdown", reply_markup=get_admin_menu())

@bot.message_handler(func=lambda message: message.text == '🔄 Перезагрузить' and is_admin(message.from_user.id))
def restart_bot(message):
    bot.send_message(message.chat.id, "🔄 Перезагрузка...")
    time.sleep(1)
    os.execl(sys.executable, sys.executable, *sys.argv)

@bot.message_handler(func=lambda message: message.text == '🛑 Выключить' and is_admin(message.from_user.id))
def shutdown_bot(message):
    bot.send_message(message.chat.id, "🛑 Выключен.")
    time.sleep(1)
    os._exit(0)

@bot.message_handler(func=lambda message: message.text == '💤 Режим сна' and is_admin(message.from_user.id))
def toggle_sleep(message):
    global IS_PAUSED
    IS_PAUSED = not IS_PAUSED
    bot.send_message(message.chat.id, "💤 Спит" if IS_PAUSED else "🟢 Проснулся")

print("Бот-комбайн для ников (оптимизированный) запущен...")
bot.polling(non_stop=True)
