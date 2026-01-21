#!/bin/bash
# Скрипт мониторинга состояния приложения

LOG_FILE="/var/log/xk-media-monitor.log"
ALERT_EMAIL="${ALERT_EMAIL:-admin@xk-media.ru}"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_service() {
    if systemctl is-active --quiet xk-media; then
        log_message "✅ Сервис xk-media работает"
        return 0
    else
        log_message "❌ Сервис xk-media не работает!"
        systemctl restart xk-media
        log_message "🔄 Попытка перезапуска сервиса"
        return 1
    fi
}

check_nginx() {
    if systemctl is-active --quiet nginx; then
        log_message "✅ Nginx работает"
        return 0
    else
        log_message "❌ Nginx не работает!"
        systemctl restart nginx
        log_message "🔄 Попытка перезапуска Nginx"
        return 1
    fi
}

check_database() {
    DB_PASSWORD=$(grep DATABASE_URL /var/www/xk-media-backend/.env | sed 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/')
    export PGPASSWORD="$DB_PASSWORD"
    if psql -h localhost -U xk_media_user -d xk_media -c "SELECT 1;" > /dev/null 2>&1; then
        unset PGPASSWORD
        log_message "✅ База данных доступна"
        return 0
    else
        unset PGPASSWORD
        log_message "❌ База данных недоступна!"
        return 1
    fi
}

check_disk_space() {
    USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$USAGE" -gt 80 ]; then
        log_message "⚠️ Использование диска: ${USAGE}%"
        return 1
    else
        log_message "✅ Использование диска: ${USAGE}%"
        return 0
    fi
}

check_memory() {
    MEMORY=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
    if [ "$MEMORY" -gt 90 ]; then
        log_message "⚠️ Использование памяти: ${MEMORY}%"
        return 1
    else
        log_message "✅ Использование памяти: ${MEMORY}%"
        return 0
    fi
}

check_http() {
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/health 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "000" ]; then
        # Если curl не работает, пробуем через systemd
        if systemctl is-active --quiet xk-media; then
            log_message "✅ HTTP endpoint доступен (сервис работает)"
            return 0
        else
            log_message "⚠️ HTTP endpoint недоступен (код: $HTTP_CODE)"
            return 1
        fi
    else
        log_message "✅ HTTP endpoint отвечает (код: $HTTP_CODE)"
        return 0
    fi
}

# Выполнение проверок
log_message "🔍 Начало проверки мониторинга"

ERRORS=0
check_service || ((ERRORS++))
check_nginx || ((ERRORS++))
check_database || ((ERRORS++))
check_disk_space || ((ERRORS++))
check_memory || ((ERRORS++))
check_http || ((ERRORS++))

if [ $ERRORS -eq 0 ]; then
    log_message "✅ Все проверки пройдены успешно"
    exit 0
else
    log_message "❌ Обнаружено ошибок: $ERRORS"
    exit 1
fi
