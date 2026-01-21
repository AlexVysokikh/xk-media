"""
OAuth service для регистрации и входа через Yandex, VK.
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
            "state": state
        }
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
                    return None
                return response.json()
            except httpx.HTTPStatusError as e:
                error_detail = e.response.text if e.response else str(e)
                print(f"Yandex token HTTP error: {e.response.status_code} - {error_detail}")
                print(f"Redirect URI used: {redirect_uri}")
                return None
            except Exception as e:
                print(f"Yandex token error: {e}")
                return None
    
    @staticmethod
    async def get_yandex_user_info(access_token: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о пользователе Yandex."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://login.yandex.ru/info",
                    headers={"Authorization": f"OAuth {access_token}"},
                    params={"format": "json"},
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"Yandex user info error: {e}")
                return None
    
    @staticmethod
    def get_vk_auth_url(state: str, role: str = "advertiser") -> str:
        """Получить URL для авторизации через VK."""
        if not settings.VK_CLIENT_ID:
            raise ValueError("VK_CLIENT_ID not configured")
        
        base_url = settings.BASE_URL.rstrip('/')
        redirect_uri = f"{base_url}/auth/oauth/vk/callback"
        
        params = {
            "client_id": settings.VK_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "email",  # Право на доступ к email
            "state": state,
            "v": "5.131"  # Версия API VK
        }
        # Если scope вызывает проблемы, можно убрать его (но тогда email не будет доступен)
        return f"https://oauth.vk.com/authorize?{urlencode(params)}"
    
    @staticmethod
    async def get_vk_token(code: str) -> Optional[Dict[str, Any]]:
        """Обменять код на токен VK."""
        if not settings.VK_CLIENT_ID or not settings.VK_CLIENT_SECRET:
            print("VK OAuth credentials not configured")
            return None
        
        base_url = settings.BASE_URL.rstrip('/')
        redirect_uri = f"{base_url}/auth/oauth/vk/callback"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://oauth.vk.com/access_token",
                    params={
                        "client_id": settings.VK_CLIENT_ID,
                        "client_secret": settings.VK_CLIENT_SECRET,
                        "redirect_uri": redirect_uri,
                        "code": code
                    },
                    timeout=10.0
                )
                if response.status_code != 200:
                    error_text = response.text
                    print(f"VK token error {response.status_code}: {error_text}")
                    print(f"Redirect URI used: {redirect_uri}")
                    return None
                data = response.json()
                if "error" in data:
                    print(f"VK token error: {data.get('error_description', data.get('error'))}")
                    print(f"Redirect URI used: {redirect_uri}")
                    return None
                return data
            except httpx.HTTPStatusError as e:
                error_detail = e.response.text if e.response else str(e)
                print(f"VK token HTTP error: {e.response.status_code} - {error_detail}")
                print(f"Redirect URI used: {redirect_uri}")
                return None
            except Exception as e:
                print(f"VK token error: {e}")
                return None
    
    @staticmethod
    async def get_vk_user_info(access_token: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о пользователе VK."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://api.vk.com/method/users.get",
                    params={
                        "user_ids": user_id,
                        "fields": "email,first_name,last_name",
                        "access_token": access_token,
                        "v": "5.131"
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                if "response" in data and len(data["response"]) > 0:
                    user_data = data["response"][0]
                    # VK возвращает email в токене, добавляем его вручную
                    return {
                        "id": str(user_data.get("id")),
                        "first_name": user_data.get("first_name"),
                        "last_name": user_data.get("last_name"),
                        "email": None  # Email будет в токене
                    }
                return None
            except Exception as e:
                print(f"VK user info error: {e}")
                return None
    
    @staticmethod
    def generate_state() -> str:
        """Генерирует случайный state для OAuth."""
        return secrets.token_urlsafe(32)
