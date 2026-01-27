#!/bin/bash
# Скрипт для обновления лимита загрузки файлов в nginx

echo "Обновление лимита загрузки файлов в nginx..."

# Путь к конфигу nginx на сервере
NGINX_CONF="/etc/nginx/sites-available/xk-media"

if [ -f "$NGINX_CONF" ]; then
    # Обновляем client_max_body_size до 50M
    sed -i 's/client_max_body_size [0-9]*M;/client_max_body_size 50M;/g' "$NGINX_CONF"
    echo "✓ Обновлен $NGINX_CONF"
else
    echo "⚠ Конфиг $NGINX_CONF не найден, проверьте путь"
fi

# Проверяем основной конфиг nginx
NGINX_MAIN="/etc/nginx/nginx.conf"
if [ -f "$NGINX_MAIN" ] && grep -q "client_max_body_size" "$NGINX_MAIN"; then
    sed -i 's/client_max_body_size [0-9]*M;/client_max_body_size 50M;/g' "$NGINX_MAIN"
    echo "✓ Обновлен $NGINX_MAIN"
fi

# Тестируем конфигурацию
echo "Проверка конфигурации nginx..."
nginx -t

if [ $? -eq 0 ]; then
    echo "✓ Конфигурация nginx валидна"
    echo "Перезапуск nginx..."
    systemctl reload nginx
    echo "✓ Nginx перезапущен"
else
    echo "✗ Ошибка в конфигурации nginx, проверьте вручную"
    exit 1
fi

echo "Готово! Лимит загрузки файлов увеличен до 50MB"
