#!/bin/bash
# ============================================================================
# XK Media - Quick Deploy Script
# Скопируйте весь этот скрипт и вставьте в консоль сервера
# ============================================================================

set -e
echo "🚀 Начинаем установку XK Media..."

# Переходим в папку
cd /opt/xk-media

# Активируем виртуальное окружение и ставим зависимости
echo "📦 Устанавливаем Python зависимости..."
source .venv/bin/activate
pip install -r requirements.txt -q

# Создаём .env
echo "⚙️ Создаём конфигурацию..."
cat > .env << 'ENVFILE'
APP_NAME=XK Media
DEBUG=False
DATABASE_URL=sqlite:///./xk_media.db
SECRET_KEY=xkmedia2024secretkey987654321abcdefghijk
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ALGORITHM=HS256
ADMIN_EMAIL=admin@xk-media.ru
ADMIN_PASSWORD=XkMedia2024!Secure
BASE_URL=https://xk-media.ru
PAYKEEPER_BASE_URL=https://demo.paykeeper.ru
PAYKEEPER_USER=demo
PAYKEEPER_PASSWORD=demo
PAYKEEPER_SECRET_WORD=secret
PAYKEEPER_RETURN_URL=https://xk-media.ru/advertiser/payments
ENVFILE

# Права доступа
echo "🔒 Настраиваем права..."
chown -R www-data:www-data /opt/xk-media
chmod 600 /opt/xk-media/.env

# Systemd сервис
echo "⚡ Создаём systemd сервис..."
cat > /etc/systemd/system/xk-media.service << 'SERVICE'
[Unit]
Description=XK Media FastAPI
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/xk-media
Environment="PATH=/opt/xk-media/.venv/bin"
ExecStart=/opt/xk-media/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable xk-media
systemctl restart xk-media

# Nginx
echo "🌐 Настраиваем Nginx..."
cat > /etc/nginx/sites-available/xk-media << 'NGINX'
server {
    listen 80;
    server_name xk-media.ru www.xk-media.ru;
    
    client_max_body_size 10M;
    
    location /static {
        alias /opt/xk-media/app/static;
        expires 30d;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
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
NGINX

rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/xk-media /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx

# SSL
echo "🔐 Получаем SSL сертификат..."
certbot --nginx -d xk-media.ru -d www.xk-media.ru --non-interactive --agree-tos --email id1@xk-media.ru || echo "SSL: возможно уже установлен или домен не направлен на сервер"

# Проверка
echo ""
echo "============================================"
echo "✅ Установка завершена!"
echo "============================================"
echo ""
echo "🌐 Сайт: https://xk-media.ru"
echo ""
echo "👤 Админ:"
echo "   Email: admin@xk-media.ru"
echo "   Пароль: XkMedia2024!Secure"
echo ""
echo "📋 Команды:"
echo "   Статус:    systemctl status xk-media"
echo "   Логи:      journalctl -u xk-media -f"
echo "   Рестарт:   systemctl restart xk-media"
echo ""
systemctl status xk-media --no-pager | head -10
