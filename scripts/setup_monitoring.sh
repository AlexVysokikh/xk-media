#!/bin/bash
# Настройка автоматического мониторинга через cron

MONITOR_SCRIPT="/var/www/xk-media-backend/scripts/monitor.sh"

# Делаем скрипт исполняемым
chmod +x "$MONITOR_SCRIPT"

# Добавляем задачу в crontab (каждые 5 минут)
(crontab -l 2>/dev/null | grep -v "$MONITOR_SCRIPT"; echo "*/5 * * * * $MONITOR_SCRIPT") | crontab -

echo "✅ Автоматический мониторинг настроен"
echo "📅 Проверки будут выполняться каждые 5 минут"
echo "📝 Логи: /var/log/xk-media-monitor.log"
