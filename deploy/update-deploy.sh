#!/bin/bash
# ============================================================================
# XK Media - Update Deploy Script
# Обновление существующего деплоя
# ============================================================================

set -e
echo "🔄 Обновление XK Media..."

# Определяем путь к проекту
if [ -d "/opt/xk-media" ]; then
    PROJECT_DIR="/opt/xk-media"
elif [ -d "/var/www/xk-media-backend" ]; then
    PROJECT_DIR="/var/www/xk-media-backend"
else
    echo "❌ Не найден путь к проекту. Проверьте /opt/xk-media или /var/www/xk-media-backend"
    exit 1
fi

echo "📁 Рабочая директория: $PROJECT_DIR"
cd "$PROJECT_DIR"

# Обновляем код
echo "📥 Обновляем код из Git..."
git pull origin main

# Активируем виртуальное окружение и обновляем зависимости
echo "📦 Обновляем Python зависимости..."
if [ -d ".venv" ]; then
    source .venv/bin/activate
    pip install -r requirements.txt -q
else
    echo "⚠️ Виртуальное окружение не найдено, пропускаем обновление зависимостей"
fi

# Обновляем конфигурацию nginx
echo "🌐 Обновляем конфигурацию Nginx..."

# Определяем путь к конфигу nginx
NGINX_CONF="/etc/nginx/sites-available/xk-media"
if [ ! -f "$NGINX_CONF" ]; then
    # Пробуем найти конфиг
    NGINX_CONF=$(find /etc/nginx -name "*xk-media*" -type f 2>/dev/null | head -1)
    if [ -z "$NGINX_CONF" ]; then
        echo "⚠️ Конфиг nginx не найден, пропускаем обновление"
    fi
fi

if [ -f "$NGINX_CONF" ]; then
    # Обновляем client_max_body_size до 50M
    if grep -q "client_max_body_size" "$NGINX_CONF"; then
        sed -i 's/client_max_body_size [0-9]*M;/client_max_body_size 50M;/g' "$NGINX_CONF"
        echo "✓ Обновлен $NGINX_CONF (client_max_body_size = 50M)"
    else
        # Добавляем client_max_body_size если его нет
        if grep -q "server_name" "$NGINX_CONF"; then
            sed -i '/server_name/a\    \n    # Max upload size\n    client_max_body_size 50M;' "$NGINX_CONF"
            echo "✓ Добавлен client_max_body_size в $NGINX_CONF"
        fi
    fi
    
    # Проверяем конфигурацию
    if nginx -t 2>/dev/null; then
        echo "✓ Конфигурация nginx валидна"
        systemctl reload nginx
        echo "✓ Nginx перезагружен"
    else
        echo "⚠️ Ошибка в конфигурации nginx, проверьте вручную"
    fi
fi

# Перезапускаем приложение
echo "🔄 Перезапускаем приложение..."
if systemctl is-active --quiet xk-media; then
    systemctl restart xk-media
    echo "✓ Сервис xk-media перезапущен"
elif systemctl is-active --quiet xk-media-backend; then
    systemctl restart xk-media-backend
    echo "✓ Сервис xk-media-backend перезапущен"
else
    echo "⚠️ Сервис не найден, проверьте вручную"
fi

# Проверка статуса
echo ""
echo "============================================"
echo "✅ Обновление завершено!"
echo "============================================"
echo ""
echo "📋 Статус сервиса:"
systemctl status xk-media --no-pager 2>/dev/null | head -5 || systemctl status xk-media-backend --no-pager 2>/dev/null | head -5 || echo "Проверьте статус вручную"
echo ""
echo "🌐 Сайт: https://xk-media.ru"
echo ""
