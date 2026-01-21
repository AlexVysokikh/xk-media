#!/usr/bin/env python3
"""
Скрипт для тестирования Yandex OAuth конфигурации.
"""

import os
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.settings import settings

def test_yandex_config():
    """Проверка конфигурации Yandex OAuth."""
    print("=" * 60)
    print("Проверка конфигурации Yandex OAuth")
    print("=" * 60)
    
    # Проверка BASE_URL
    print(f"\n📌 BASE_URL: {settings.BASE_URL}")
    if not settings.BASE_URL:
        print("❌ BASE_URL не настроен!")
    else:
        redirect_uri = f"{settings.BASE_URL.rstrip('/')}/auth/oauth/yandex/callback"
        print(f"✅ Redirect URI: {redirect_uri}")
    
    # Проверка Yandex Client ID
    print(f"\n📌 YANDEX_CLIENT_ID: {settings.YANDEX_CLIENT_ID[:20] + '...' if settings.YANDEX_CLIENT_ID else 'НЕ НАСТРОЕН'}")
    if not settings.YANDEX_CLIENT_ID:
        print("❌ YANDEX_CLIENT_ID не настроен!")
    else:
        print(f"✅ YANDEX_CLIENT_ID настроен (длина: {len(settings.YANDEX_CLIENT_ID)})")
    
    # Проверка Yandex Client Secret
    print(f"\n📌 YANDEX_CLIENT_SECRET: {'Настроен' if settings.YANDEX_CLIENT_SECRET else 'НЕ НАСТРОЕН'}")
    if not settings.YANDEX_CLIENT_SECRET:
        print("❌ YANDEX_CLIENT_SECRET не настроен!")
    else:
        print(f"✅ YANDEX_CLIENT_SECRET настроен (длина: {len(settings.YANDEX_CLIENT_SECRET)})")
    
    # Итоговая проверка
    print("\n" + "=" * 60)
    if settings.YANDEX_CLIENT_ID and settings.YANDEX_CLIENT_SECRET and settings.BASE_URL:
        print("✅ Все настройки Yandex OAuth присутствуют")
        print(f"\n📋 Инструкция:")
        print(f"1. Откройте: https://oauth.yandex.ru/")
        print(f"2. Найдите ваше приложение с ID: {settings.YANDEX_CLIENT_ID}")
        print(f"3. Убедитесь, что в настройках указан Redirect URI:")
        print(f"   {redirect_uri}")
        print(f"4. Убедитесь, что включено право доступа: 'Доступ к email адресу'")
    else:
        print("❌ Настройки Yandex OAuth неполные!")
        print("\nДобавьте в .env файл:")
        print("BASE_URL=https://xk-media.ru")
        print("YANDEX_CLIENT_ID=ваш_client_id")
        print("YANDEX_CLIENT_SECRET=ваш_client_secret")
    print("=" * 60)

if __name__ == "__main__":
    test_yandex_config()
