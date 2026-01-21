#!/usr/bin/env python3
"""
Скрипт для проверки конфигурации OAuth провайдеров
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.settings import settings

def check_oauth_config():
    """Проверить конфигурацию OAuth."""
    print("🔍 Проверка конфигурации OAuth провайдеров\n")
    print(f"BASE_URL: {settings.BASE_URL}\n")
    
    issues = []
    
    # Google
    print("📱 Google OAuth:")
    if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
        print(f"  ✅ Client ID: {settings.GOOGLE_CLIENT_ID[:20]}...")
        print(f"  ✅ Client Secret: {'*' * 20}")
        redirect_uri = f"{settings.BASE_URL.rstrip('/')}/auth/oauth/google/callback"
        print(f"  📍 Redirect URI должен быть: {redirect_uri}")
        print(f"  ⚠️  Убедитесь, что этот URI добавлен в Google Cloud Console")
    else:
        print("  ❌ Не настроен (GOOGLE_CLIENT_ID или GOOGLE_CLIENT_SECRET отсутствуют)")
        issues.append("Google OAuth не настроен")
    print()
    
    # Yandex
    print("📱 Yandex OAuth:")
    if settings.YANDEX_CLIENT_ID and settings.YANDEX_CLIENT_SECRET:
        print(f"  ✅ Client ID: {settings.YANDEX_CLIENT_ID[:20]}...")
        print(f"  ✅ Client Secret: {'*' * 20}")
        redirect_uri = f"{settings.BASE_URL.rstrip('/')}/auth/oauth/yandex/callback"
        print(f"  📍 Redirect URI должен быть: {redirect_uri}")
        print(f"  ⚠️  Убедитесь, что этот URI добавлен в Yandex OAuth")
    else:
        print("  ❌ Не настроен (YANDEX_CLIENT_ID или YANDEX_CLIENT_SECRET отсутствуют)")
        issues.append("Yandex OAuth не настроен")
    print()
    
    # VK
    print("📱 VK OAuth:")
    if settings.VK_CLIENT_ID and settings.VK_CLIENT_SECRET:
        print(f"  ✅ Client ID: {settings.VK_CLIENT_ID[:20]}...")
        print(f"  ✅ Client Secret: {'*' * 20}")
        redirect_uri = f"{settings.BASE_URL.rstrip('/')}/auth/oauth/vk/callback"
        print(f"  📍 Redirect URI должен быть: {redirect_uri}")
        print(f"  ⚠️  Убедитесь, что этот URI добавлен в VK Developers")
    else:
        print("  ❌ Не настроен (VK_CLIENT_ID или VK_CLIENT_SECRET отсутствуют)")
        issues.append("VK OAuth не настроен")
    print()
    
    if issues:
        print("⚠️  Обнаружены проблемы:")
        for issue in issues:
            print(f"  - {issue}")
        print("\n📖 См. инструкцию в OAUTH_FIX.md")
        return False
    else:
        print("✅ Все OAuth провайдеры настроены!")
        print("\n⚠️  Не забудьте добавить redirect URIs в настройках провайдеров!")
        return True

if __name__ == "__main__":
    success = check_oauth_config()
    sys.exit(0 if success else 1)
