import requests
from bs4 import BeautifulSoup
from colorama import Fore, Style, init
import time

# Инициализируем цвета
init(autoreset=True)

def print_banner():
    banner = f"""
{Fore.GREEN}
██╗  ██╗ █████╗  ██████╗██╗  ██╗███████╗██████╗ 
██║  ██║██╔══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗
███████║███████║██║     █████╔╝ █████╗  ██████╔╝
██╔══██║██╔══██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗
██║  ██║██║  ██║╚██████╗██║  ██╗███████╗██║  ██║
╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
{Fore.CYAN}       [ OSINT & SEARCH TERMINAL v1.2 ]
{Fore.WHITE}===================================================
{Fore.YELLOW}Введи запрос. Выдам только текст без ссылок.
{Fore.YELLOW}Для выхода напиши: {Fore.RED}exit{Fore.WHITE}
===================================================
"""
    print(banner)

def search_info(query):
    print(f"\n{Fore.YELLOW}[*] Поиск информации...")
    time.sleep(1)

    # Отправляем запрос к HTML-версии DuckDuckGo
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    params = {"q": query}

    try:
        response = requests.post(url, data=params, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results = soup.find_all("div", class_="result__body")

        if not results:
            print(f"{Fore.RED}[!] По запросу '{query}' ничего не найдено.")
            return

        print(f"{Fore.GREEN}[+] Найдено {len(results)} результатов (только текст):\n")

        for i, res in enumerate(results[:5], start=1):
            title_tag = res.find("a", class_="result__a")
            snippet_tag = res.find("a", class_="result__snippet")

            title = title_tag.get_text(strip=True) if title_tag else "Без названия"
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else "Нет описания"

            print(f"{Fore.CYAN}[{i}] {Fore.WHITE}{title}")
            print(f"    {Fore.WHITE}{snippet}\n")

    except Exception as e:
        print(f"{Fore.RED}[!] Ошибка сети: {e}")

def main():
    print_banner()
    while True:
        try:
            query = input(f"{Fore.GREEN}root@kali:~# {Fore.WHITE}")

            if query.lower() in ["exit", "quit", "q"]:
                print(f"{Fore.RED}Отключение от сети...")
                break

            if len(query.strip()) == 0:
                continue

            search_info(query)

        except KeyboardInterrupt:
            print(f"\n{Fore.RED}Экстренный выход...")
            break
        except Exception as e:
            print(f"{Fore.RED}[!] Ошибка: {e}")

if __name__ == "__main__":
    main()
