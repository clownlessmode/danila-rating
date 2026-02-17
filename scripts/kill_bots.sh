#!/bin/bash
# Найти и убить все процессы бота
echo "=== Процессы bot.py ==="
ps aux | grep -E "[b]ot\.py|[p]ython.*bot"
echo ""
echo "Убиваю..."
pkill -f "python.*bot\.py" 2>/dev/null && echo "Готово" || echo "Процессов не найдено"
