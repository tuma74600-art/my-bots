import telebot
import sqlite3
import re
from telebot import types

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "9133533408:AAHN2vawZ8v9J-uG0vtuF5lyX3sAK_rb87w" 
ADMIN_ID = 7969267809 # Твой главный ID
# ============================================

telebot.apihelper.API_URL = "https://hyrepgram.tuma74600.workers.dev/bot{0}/{1}"
bot = telebot.TeleBot(BOT_TOKEN)

# Подключаемся к базе основного бота
conn = sqlite3.connect('bot.db', check_same_thread=False)
cursor = conn.cursor()

# ================= ЗАЩИТА =================
def check_access(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ Вы не можете пользоваться этим ботом. Доступ запрещен.")
        return False
    return True

# ================= КЛАВИАТУРА РАЗРАБОТЧИКА =================
def get_dev_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton('⭐ Выдать звезды'), types.KeyboardButton('🌿 Выдать граммы'),
               types.KeyboardButton('🎁 Выдать NFT'), types.KeyboardButton('📛 Выдать ник'),
               types.KeyboardButton('🛡️ Выдать админку'))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    if not check_access(message): return
    text = ("🕵️‍♂️ **СЕКРЕТНАЯ ПАНЕЛЬ РАЗРАБОТЧИКА** 🕵️‍♂️\n\n"
            "Добро пожаловать в теневой штаб управления Hypergram.\n"
            "Выбери действие на кнопках ниже:")
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=get_dev_menu())

# ================= ОБРАБОТЧИКИ КНОПОК (ЗАПРОС ДАННЫХ) =================

@bot.message_handler(func=lambda message: message.text == '⭐ Выдать звезды')
def ask_stars(message):
    if not check_access(message): return
    msg = bot.send_message(message.chat.id, "✨ **Выдача звезд**\n\nНапиши в формате:\n`@username КОЛИЧЕСТВО`\n*(например: @Ivan 5000)*", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_stars)

@bot.message_handler(func=lambda message: message.text == '🌿 Выдать граммы')
def ask_grams(message):
    if not check_access(message): return
    msg = bot.send_message(message.chat.id, "🌿 **Выдача граммов**\n\nНапиши в формате:\n`@username КОЛИЧЕСТВО`\n*(например: @Ivan 50)*", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_grams)

@bot.message_handler(func=lambda message: message.text == '🎁 Выдать NFT')
def ask_nft(message):
    if not check_access(message): return
    msg = bot.send_message(message.chat.id, "🎁 **Выдача NFT**\n\nНапиши в формате:\n`@username НАЗВАНИЕ_НФТ`\n*(например: @Ivan Золотой_Дедос)*", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_nft)

@bot.message_handler(func=lambda message: message.text == '📛 Выдать ник')
def ask_nick(message):
    if not check_access(message): return
    msg = bot.send_message(message.chat.id, "📛 **Выдача кастомного ника**\n\nНапиши в формате:\n`@username_кому_выдаем @НовыйНик`\n*(Правила: начинается с @, только английские буквы/цифры, любой длины)*", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_nick)

@bot.message_handler(func=lambda message: message.text == '🛡️ Выдать админку')
def ask_admin(message):
    if not check_access(message): return
    msg = bot.send_message(message.chat.id, "🛡️ **Выдача прав Админа**\n\nНапиши кому выдать права:\n`@username` или `ID`\n*(Он сможет зайти в главного бота по команде /admin пароль)*", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_admin_access)

# ================= ОБРАБОТЧИКИ ВВОДА =================

def find_user(username_or_id):
    clean_target = username_or_id.replace('@', '')
    if clean_target.isdigit():
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (int(clean_target),))
    else:
        cursor.execute("SELECT user_id FROM users WHERE LOWER(username) = LOWER(?)", (clean_target,))
    return cursor.fetchone()

def process_stars(message):
    if message.text.startswith('/'): return bot.send_message(message.chat.id, "❌ Отмена.", reply_markup=get_dev_menu())
    args = message.text.split()
    if len(args) < 2: return bot.send_message(message.chat.id, "❌ Неверный формат.", reply_markup=get_dev_menu())
    
    user = find_user(args[0])
    if not user: return bot.send_message(message.chat.id, "❌ Игрок не найден в базе.", reply_markup=get_dev_menu())
    
    try: amount = int(args[1])
    except: return bot.send_message(message.chat.id, "❌ Сумма должна быть числом.", reply_markup=get_dev_menu())
    
    cursor.execute("UPDATE users SET stars = stars + ? WHERE user_id = ?", (amount, user[0]))
    conn.commit()
    bot.send_message(message.chat.id, f"✅ **Успех!**\nВыдано **{amount}** ⭐ игроку {args[0]}.", parse_mode="Markdown", reply_markup=get_dev_menu())

def process_grams(message):
    if message.text.startswith('/'): return bot.send_message(message.chat.id, "❌ Отмена.", reply_markup=get_dev_menu())
    args = message.text.split()
    if len(args) < 2: return bot.send_message(message.chat.id, "❌ Неверный формат.", reply_markup=get_dev_menu())
    
    user = find_user(args[0])
    if not user: return bot.send_message(message.chat.id, "❌ Игрок не найден в базе.", reply_markup=get_dev_menu())
    
    try: amount = int(args[1])
    except: return bot.send_message(message.chat.id, "❌ Сумма должна быть числом.", reply_markup=get_dev_menu())
    
    cursor.execute("UPDATE users SET grams = grams + ? WHERE user_id = ?", (amount, user[0]))
    conn.commit()
    bot.send_message(message.chat.id, f"✅ **Успех!**\nВыдано **{amount}** 🌿 игроку {args[0]}.", parse_mode="Markdown", reply_markup=get_dev_menu())

def process_nft(message):
    if message.text.startswith('/'): return bot.send_message(message.chat.id, "❌ Отмена.", reply_markup=get_dev_menu())
    args = message.text.split(maxsplit=1)
    if len(args) < 2: return bot.send_message(message.chat.id, "❌ Неверный формат.", reply_markup=get_dev_menu())
    
    user = find_user(args[0])
    if not user: return bot.send_message(message.chat.id, "❌ Игрок не найден в базе.", reply_markup=get_dev_menu())
    
    item_name = args[1]
    cursor.execute("SELECT inventory FROM users WHERE user_id = ?", (user[0],))
    inv = cursor.fetchone()[0]
    new_inv = f"{inv}, {item_name}" if inv else item_name
    cursor.execute("UPDATE users SET inventory = ? WHERE user_id = ?", (new_inv, user[0]))
    conn.commit()
    bot.send_message(message.chat.id, f"✅ **Успех!**\nВыдан NFT **{item_name}** игроку {args[0]}.", parse_mode="Markdown", reply_markup=get_dev_menu())

def process_nick(message):
    if message.text.startswith('/'): return bot.send_message(message.chat.id, "❌ Отмена.", reply_markup=get_dev_menu())
    args = message.text.split()
    if len(args) < 2: return bot.send_message(message.chat.id, "❌ Неверный формат.", reply_markup=get_dev_menu())
    
    user = find_user(args[0])
    if not user: return bot.send_message(message.chat.id, "❌ Игрок не найден в базе.", reply_markup=get_dev_menu())
    
    new_nick = args[1]
    
    # ПРОВЕРКИ НИКА
    if not new_nick.startswith('@'):
        return bot.send_message(message.chat.id, "❌ Ник должен начинаться с @", reply_markup=get_dev_menu())
    if re.search('[а-яА-ЯёЁ]', new_nick):
        return bot.send_message(message.chat.id, "❌ Ник должен быть только на английском языке!", reply_markup=get_dev_menu())
        
    cursor.execute("UPDATE users SET custom_nickname = ? WHERE user_id = ?", (new_nick, user[0]))
    conn.commit()
    bot.send_message(message.chat.id, f"✅ **Успех!**\nИгроку {args[0]} выдан ник **{new_nick}**", parse_mode="Markdown", reply_markup=get_dev_menu())

def process_admin_access(message):
    if message.text.startswith('/'): return bot.send_message(message.chat.id, "❌ Отмена.", reply_markup=get_dev_menu())
    user = find_user(message.text.strip())
    if not user: return bot.send_message(message.chat.id, "❌ Игрок не найден в базе.", reply_markup=get_dev_menu())
    
    cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user[0],))
    conn.commit()
    bot.send_message(message.chat.id, f"✅ **Успех!**\nИгрок {message.text} теперь Админ. Он может зайти в главного бота по паролю.", parse_mode="Markdown", reply_markup=get_dev_menu())

# Защита от левых сообщений
@bot.message_handler(func=lambda message: True)
def block_strangers(message):
    if not check_access(message): return
    bot.send_message(message.chat.id, "🤖 Используй кнопки внизу для управления.", reply_markup=get_dev_menu())

print("Секретный бот-разработчик запущен...")
bot.polling(non_stop=True)
