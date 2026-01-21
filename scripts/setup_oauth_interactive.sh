#!/bin/bash
# Интерактивный скрипт для настройки OAuth провайдеров

set -e

cd /var/www/xk-media-backend
source venv/bin/activate

echo "🔐 Настройка OAuth провайдеров для XK Media"
echo "=========================================="
echo ""

# Проверка текущей конфигурации
python scripts/check_oauth_config.py

echo ""
echo "📝 Настройка OAuth провайдеров"
echo ""

BASE_URL=$(grep BASE_URL .env | cut -d'=' -f2 | tr -d '"' | tr -d "'" || echo "http://109.69.21.98")
BASE_URL=${BASE_URL:-http://109.69.21.98}

echo "Текущий BASE_URL: $BASE_URL"
read -p "Использовать этот URL? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    read -p "Введите BASE_URL (например, https://xk-media.ru): " BASE_URL
fi

# Обновление BASE_URL в .env
if grep -q "BASE_URL=" .env; then
    sed -i "s|BASE_URL=.*|BASE_URL=$BASE_URL|" .env
else
    echo "BASE_URL=$BASE_URL" >> .env
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  Google OAuth"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 Redirect URI для добавления в Google Cloud Console:"
echo "   ${BASE_URL}/auth/oauth/google/callback"
echo ""
read -p "Введите Google Client ID (или нажмите Enter для пропуска): " GOOGLE_ID
if [ ! -z "$GOOGLE_ID" ]; then
    read -sp "Введите Google Client Secret: " GOOGLE_SECRET
    echo
    
    if grep -q "GOOGLE_CLIENT_ID=" .env; then
        sed -i "s|GOOGLE_CLIENT_ID=.*|GOOGLE_CLIENT_ID=$GOOGLE_ID|" .env
    else
        echo "GOOGLE_CLIENT_ID=$GOOGLE_ID" >> .env
    fi
    
    if grep -q "GOOGLE_CLIENT_SECRET=" .env; then
        sed -i "s|GOOGLE_CLIENT_SECRET=.*|GOOGLE_CLIENT_SECRET=$GOOGLE_SECRET|" .env
    else
        echo "GOOGLE_CLIENT_SECRET=$GOOGLE_SECRET" >> .env
    fi
    
    echo "✅ Google OAuth настроен"
else
    echo "⏭️  Google OAuth пропущен"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  Yandex OAuth"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 Redirect URI для добавления в Yandex OAuth:"
echo "   ${BASE_URL}/auth/oauth/yandex/callback"
echo ""
read -p "Введите Yandex Client ID (или нажмите Enter для пропуска): " YANDEX_ID
if [ ! -z "$YANDEX_ID" ]; then
    read -sp "Введите Yandex Client Secret: " YANDEX_SECRET
    echo
    
    if grep -q "YANDEX_CLIENT_ID=" .env; then
        sed -i "s|YANDEX_CLIENT_ID=.*|YANDEX_CLIENT_ID=$YANDEX_ID|" .env
    else
        echo "YANDEX_CLIENT_ID=$YANDEX_ID" >> .env
    fi
    
    if grep -q "YANDEX_CLIENT_SECRET=" .env; then
        sed -i "s|YANDEX_CLIENT_SECRET=.*|YANDEX_CLIENT_SECRET=$YANDEX_SECRET|" .env
    else
        echo "YANDEX_CLIENT_SECRET=$YANDEX_SECRET" >> .env
    fi
    
    echo "✅ Yandex OAuth настроен"
else
    echo "⏭️  Yandex OAuth пропущен"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  VK OAuth"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 Redirect URI для добавления в VK Developers:"
echo "   ${BASE_URL}/auth/oauth/vk/callback"
echo ""
read -p "Введите VK Client ID (или нажмите Enter для пропуска): " VK_ID
if [ ! -z "$VK_ID" ]; then
    read -sp "Введите VK Client Secret: " VK_SECRET
    echo
    
    if grep -q "VK_CLIENT_ID=" .env; then
        sed -i "s|VK_CLIENT_ID=.*|VK_CLIENT_ID=$VK_ID|" .env
    else
        echo "VK_CLIENT_ID=$VK_ID" >> .env
    fi
    
    if grep -q "VK_CLIENT_SECRET=" .env; then
        sed -i "s|VK_CLIENT_SECRET=.*|VK_CLIENT_SECRET=$VK_SECRET|" .env
    else
        echo "VK_CLIENT_SECRET=$VK_SECRET" >> .env
    fi
    
    echo "✅ VK OAuth настроен"
else
    echo "⏭️  VK OAuth пропущен"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Настройка завершена!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Финальная проверка
python scripts/check_oauth_config.py

echo ""
echo "🔄 Перезапуск приложения..."
systemctl restart xk-media

echo ""
echo "✅ Готово! Проверьте OAuth авторизацию на странице входа."
echo ""
echo "⚠️  Не забудьте добавить redirect URIs в настройках провайдеров!"
echo "   См. инструкцию: OAUTH_AUTO_SETUP.md"
