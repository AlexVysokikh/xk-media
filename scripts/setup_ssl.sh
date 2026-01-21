#!/bin/bash
# Скрипт для настройки SSL сертификата через Let's Encrypt

set -e

DOMAIN="${1:-xk-media.ru}"
EMAIL="${2:-admin@xk-media.ru}"

echo "🔒 Настройка SSL для домена: $DOMAIN"
echo "📧 Email для уведомлений: $EMAIL"

# Проверка, что домен указывает на этот сервер
echo "Проверка DNS..."
SERVER_IP=$(curl -s ifconfig.me)
echo "IP сервера: $SERVER_IP"
echo "Убедитесь, что домен $DOMAIN указывает на этот IP"

read -p "Продолжить? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Установка certbot
echo "📦 Установка certbot..."
apt update
apt install -y certbot python3-certbot-nginx

# Получение сертификата
echo "🔐 Получение SSL сертификата..."
certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "$EMAIL"

# Настройка автообновления
echo "🔄 Настройка автообновления сертификата..."
systemctl enable certbot.timer
systemctl start certbot.timer

# Обновление конфигурации Nginx для HTTPS
echo "📝 Обновление конфигурации Nginx..."
cat > /etc/nginx/sites-available/xk-media << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name xk-media.ru www.xk-media.ru;
    
    # Редирект на HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name xk-media.ru www.xk-media.ru;

    # SSL сертификаты
    ssl_certificate /etc/letsencrypt/live/xk-media.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/xk-media.ru/privkey.pem;
    
    # SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Max upload size
    client_max_body_size 10M;

    # Static files
    location /static {
        alias /var/www/xk-media-backend/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy to FastAPI
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

# Проверка конфигурации
nginx -t

# Перезапуск Nginx
systemctl restart nginx

echo "✅ SSL настроен успешно!"
echo "🌐 Сайт доступен по адресу: https://$DOMAIN"
echo "🔄 Сертификат будет автоматически обновляться"
