#!/bin/bash
termux-wake-lock
python bot.py &
python osint_bot.py &
python logger_bot.py &
python username_bot.py &
echo "Все боты запущены!"
