"""
OAuth service для регистрации и входа через Yandex.
"""

import secrets
import httpx
from typing import Optional, Dict, Any
from urllib.parse import urlencode

from app.settings import settings


class OAuthService:
    """Сервис для работы с OAuth провайдерами."""
    
    @staticmethod
    def get_yandex_auth_url(state: str, role: str = "advertiser") -> str:
        """Получить URL для авторизации через Yandex."""
        if not settings.YANDEX_CLIENT_ID:
            raise ValueError("YANDEX_CLIENT_ID not configured")
        
        base_url = settings.BASE_URL.rstrip('/')
        redirect_uri = f"{base_url}/auth/oauth/yandex/callback"
        
        params = {
            "client_id": settings.YANDEX_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "state": state,
            "force_confirm": "yes"  # Принудительно запрашивать подтверждение
        }
        # Yandex требует scope для получения email, но он не передается в authorize
        # Email запрашивается автоматически при правильной настройке приложения
        return f"https://oauth.yandex.ru/authorize?{urlencode(params)}"
    
    @staticmethod
    async def get_yandex_token(code: str) -> Optional[Dict[str, Any]]:
        """Обменять код на токен Yandex."""
        if not settings.YANDEX_CLIENT_ID or not settings.YANDEX_CLIENT_SECRET:
            print("Yandex OAuth credentials not configured")
            return None
        
        base_url = settings.BASE_URL.rstrip('/')
        redirect_uri = f"{base_url}/auth/oauth/yandex/callback"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://oauth.yandex.ru/token",
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "client_id": settings.YANDEX_CLIENT_ID,
                        "client_secret": settings.YANDEX_CLIENT_SECRET,
                        "redirect_uri": redirect_uri
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=10.0
                )
                if response.status_code != 200:
                    error_text = response.text
                    print(f"Yandex token error {response.status_code}: {error_text}")
                    print(f"Redirect URI used: {redirect_uri}")
                    print(f"Client ID: {settings.YANDEX_CLIENT_ID[:10]}...")
                    try:
                        error_json = response.json()
                        print(f"Error details: {error_json}")
                    except:
                        pass
                    return None
                return response.json()
            except httpx.HTTPStatusError as e:
                error_detail = e.response.text if e.response else str(e)
                print(f"Yandex token HTTP error: {e.response.status_code} - {error_detail}")
                print(f"Redirect URI used: {redirect_uri}")
                return None
            except Exception as e:
                print(f"Yandex token error: {e}")
                import traceback
                traceback.print_exc()
                return None
    
    @staticmethod
    async def get_yandex_user_info(access_token: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о пользователе Yandex."""
        async with httpx.AsyncClient() as client:
            try:
                # Запрашиваем информацию с полями email, first_name, last_name
                response = await client.get(
                    "https://login.yandex.ru/info",
                    headers={"Authorization": f"OAuth {access_token}"},
                    params={"format": "json"},
                    timeout=10.0
                )
                response.raise_for_status()
                user_data = response.json()
                
                # Логируем полученные данные для отладки
                print(f"Yandex user info received: {list(user_data.keys())}")
                
                # Проверяем наличие email
                if "default_email" not in user_data and "emails" in user_data:
                    # Если default_email нет, но есть emails, берем первый
                    emails = user_data.get("emails", [])
                    if emails:
                        user_data["default_email"] = emails[0]
                
                return user_data
            except httpx.HTTPStatusError as e:
                print(f"Yandex user info HTTP error: {e.response.status_code} - {e.response.text}")
                return None
            except Exception as e:
                print(f"Yandex user info error: {e}")
                import traceback
                traceback.print_exc()
                return None
    
    @staticmethod
    def generate_state() -> str:
        """Генерирует случайный state для OAuth."""
        return secrets.token_urlsafe(32)
