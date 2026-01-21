#!/bin/bash
# Настройка автоматического резервного копирования через cron

BACKUP_SCRIPT="/var/www/xk-media-backend/scripts/backup_database.sh"

# Делаем скрипт исполняемым
chmod +x "$BACKUP_SCRIPT"

# Добавляем задачу в crontab (ежедневно в 2:00)
(crontab -l 2>/dev/null | grep -v "$BACKUP_SCRIPT"; echo "0 2 * * * $BACKUP_SCRIPT >> /var/log/xk-media-backup.log 2>&1") | crontab -

echo "✅ Автоматическое резервное копирование настроено"
echo "📅 Бэкапы будут создаваться ежедневно в 2:00"
echo "📝 Логи: /var/log/xk-media-backup.log"
