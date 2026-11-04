#!/bin/bash
termux-wake-lock
while true; do
    pgrep -f "python bot.py" > /dev/null || python bot.py &
    pgrep -f "python osint_bot.py" > /dev/null || python osint_bot.py &
    pgrep -f "python logger_bot.py" > /dev/null || python logger_bot.py &
    pgrep -f "python username_bot.py" > /dev/null || python username_bot.py &
    sleep 30
done
