import telebot
import asyncio
import logging
import phonenumbers
import socket
import whois
import requests
import dns.resolver
from urllib.parse import urlparse
from phonenumbers import geocoder, carrier, timezone
from maigret import search as maigret_search
from maigret.sites import MaigretDatabase

# Пытаемся импортировать Sherlock (если не установлен, бот продолжит работать без него)
try:
    from sherlock_project import sherlock as sherlock_search
    HAS_SHERLOCK = True
except ImportError:
    HAS_SHERLOCK = False

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "9236282771:AAFDaaXMXQPiGIHTCv4eonyyd9DnGM1l8Xc" 
ADMIN_IDS = [8975587652, 7969267809] # Твои ID
# ============================================

telebot.apihelper.API_URL = "https://hyrepgram.tuma74600.workers.dev/bot{0}/{1}"
bot = telebot.TeleBot(BOT_TOKEN)

try:
    db = MaigretDatabase().load_from_path("data.json")
    sites = db.ranked_sites_dict(top=100) 
    logger = logging.getLogger("maigret")
except Exception as e:
    print(f"Ошибка загрузки базы Maigret: {e}")
    sites = None

def check_access(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "⛔ Доступ запрещен.")
        return False
    return True

def analyze_domain(url):
    try:
        parsed = urlparse(url if url.startswith('http') else f'http://{url}')
        domain = parsed.netloc or parsed.path.split('/')[0]
        
        try: ip = socket.gethostbyname(domain)
        except: ip = "Не удалось определить"
            
        try:
            w = whois.whois(domain)
            org = w.org if w.org else "Скрыто"
            country = w.country if w.country else "Неизвестно"
            creation = w.creation_date
            if isinstance(creation, list): creation = creation[0]
            whois_text = f"🏢 **Орг:** {org} | 🌍 **Страна:** {country} | 📅 **Создан:** {creation.strftime('%Y-%m-%d') if creation else '?'}"
        except:
            whois_text = "🏢 WHOIS: Скрыто."

        dns_text = ""
        try:
            mx_records = [str(x.exchange) for x in dns.resolver.resolve(domain, 'MX')]
            dns_text += f"\n📧 **MX (Почта):** {', '.join(mx_records[:3])}"
        except: pass

        subdomains = ""
        try:
            r = requests.get(f"https://crt.sh/?q=%.{domain}&output=json", timeout=5)
            if r.status_code == 200:
                subs = set([item['name_value'] for item in r.json()])
                sub_list = [s for s in subs if s != domain][:5]
                if sub_list: subdomains = f"\n🔍 **Поддомены:** {', '.join(sub_list)}"
        except: pass

        return (f"🌐 **Досье на `{domain}`**\n\n"
                f"📍 **IP:** `{ip}`\n"
                f"{whois_text}{dns_text}{subdomains}")
    except Exception as e:
        return f"❌ Ошибка: {e}"

def analyze_email(email):
    try:
        r = requests.get(f"https://emailrep.io/{email}", headers={'User-Agent': 'OSINT-Bot'}, timeout=5)
        if r.status_code == 200:
            data = r.json()
            rep = data.get('reputation', 'unknown')
            suspicious = data.get('suspicious', False)
            profiles = data.get('details', {}).get('profiles', [])
            
            text = f"📧 **Анализ почты:** `{email}`\n\n"
            text += f"📊 **Репутация:** {rep.capitalize()}\n"
            text += f"⚠️ **Подозрительная:** {'Да' if suspicious else 'Нет'}\n"
            if profiles: text += f"🔗 **Найдена на сайтах:** {', '.join(profiles)}\n"
            return text
        return f"📧 Почта `{email}` валидна, но данных в базе нет."
    except Exception:
        return f"📧 Почта `{email}`. Не удалось проверить (лимит API)."

@bot.message_handler(commands=['start'])
def start(message):
    if not check_access(message): return
    text = ("🕵️‍♂️ **МЕГА OSINT-Разведчик**\n\n"
            "Отправь мне:\n"
            "1️⃣ **Юзернейм** (Maigret + Sherlock)\n"
            "2️⃣ **Номер телефона** (`+79123456789`)\n"
            "3️⃣ **Ссылку/домен** (WHOIS + DNS)\n"
            "4️⃣ **Email** (проверка репутации)\n\n"
            "⏳ *Сканирование: 30–60 секунд.*")
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def scan_target(message):
    if not check_access(message): return
    if message.text.startswith('/'): return
    
    query = message.text.strip().replace('@', '')
    
    # Email
    if '@' in query and '.' in query.split('@')[-1]:
        msg = bot.send_message(message.chat.id, f"📧 Анализирую почту `{query}`...", parse_mode="Markdown")
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=analyze_email(query), parse_mode="Markdown")
        return

    # URL
    is_url = '.' in query and not query.replace('.', '').isdigit()
    if is_url:
        msg = bot.send_message(message.chat.id, f"🌐 Анализирую домен `{query}`...", parse_mode="Markdown")
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=analyze_domain(query), parse_mode="Markdown")
        return
        
    if not sites:
        return bot.send_message(message.chat.id, "❌ База Maigret не загружена.")

    # Ник или Телефон
    is_phone = query.startswith('+') or (query.isdigit() and len(query) > 8)
    id_type = 'phone' if is_phone else 'username'
    
    if not is_phone and not query.isalnum():
        return bot.send_message(message.chat.id, "❌ Ник должен состоять только из букв и цифр.")
        
    msg = bot.send_message(message.chat.id, f"🔎 Сканирую `{query}`...\n*(Займёт 30–60 секунд)*", parse_mode="Markdown")
    
    try:
        report_lines = []
        header = ""
        
        if is_phone:
            try:
                parsed_num = phonenumbers.parse(query, "RU")
                if phonenumbers.is_valid_number(parsed_num):
                    region = geocoder.description_for_number(parsed_num, "ru")
                    operator = carrier.name_for_number(parsed_num, "ru")
                    tz = timezone.time_zones_for_number(parsed_num)
                    header = (f"📱 **Инфо о номере `{query}`**\n\n"
                              f"🌍 **Регион:** {region if region else '?'}\n"
                              f"📡 **Оператор:** {operator if operator else '?'}\n"
                              f"🕒 **Часовой пояс:** {', '.join(tz)}\n\n"
                              f"👇 **Аккаунты:**\n")
            except: pass

        # Maigret
        maigret_results = asyncio.run(maigret_search(
            username=query, site_dict=sites, logger=logger, timeout=30, is_parsing_enabled=True, id_type=id_type
        ))
        
        found_count = 0
        for site_name, data in maigret_results.items():
            if data['status'].is_found():
                found_count += 1
                line = f"\n✅ **{site_name}** (Maigret)\n🔗 {data['url_user']}"
                ids = data.get('ids_data', {})
                if ids:
                    details = []
                    for key, label in [('fullname', 'Имя'), ('bio', 'Био'), ('location', 'Локация')]:
                        if key in ids and ids[key]: details.append(f"   • {label}: {ids[key]}")
                    if details: line += "\n" + "\n".join(details)
                report_lines.append(line)

        # Sherlock
        if not is_phone and HAS_SHERLOCK:
            try:
                sherlock_results = sherlock_search(query, timeout=10)
                for site, result in sherlock_results.items():
                    if result.get("status") == "Claimed":
                        found_count += 1
                        report_lines.append(f"\n✅ **{site}** (Sherlock)\n🔗 {result.get('url_user', 'Ссылка не найдена')}")
            except: pass

        if found_count > 0 or is_phone:
            if not header: header = f"📋 **Досье на `{query}`**\n\nНайдено: **{found_count}**\n"
            report = header + "\n".join(report_lines)
            if found_count == 0: report += "❌ *Сайтов не найдено.*"
            
            if len(report) > 4000:
                for i in range(0, len(report), 4000):
                    bot.send_message(message.chat.id, report[i:i+4000], parse_mode="Markdown")
            else:
                bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=report, parse_mode="Markdown")
        else:
            bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=f"❌ По запросу `{query}` ничего не найдено.", parse_mode="Markdown")
            
    except Exception as e:
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=f"❌ Ошибка: {e}")

print("МЕГА OSINT-бот запущен...")
bot.polling(non_stop=True)
