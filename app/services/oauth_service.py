"""
OAuth service для регистрации и входа через Google, Yandex, VK.
"""

import secrets
import httpx
from typing import Optional, Dict, Any
from urllib.parse import urlencode

from app.settings import settings


class OAuthService:
    """Сервис для работы с OAuth провайдерами."""
    
    @staticmethod
    def get_google_auth_url(state: str, role: str = "advertiser") -> str:
        """Получить URL для авторизации через Google."""
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": f"{settings.BASE_URL}/auth/oauth/google/callback",
            "response_type": "code",
            "scope": "openid email profile",
            "state": f"{state}:{role}",  # Сохраняем роль в state
            "access_type": "offline",
            "prompt": "consent"
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    
    @staticmethod
    async def get_google_token(code: str) -> Optional[Dict[str, Any]]:
        """Обменять код на токен Google."""
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            return None
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "code": code,
                        "grant_type": "authorization_code",
                        "redirect_uri": f"{settings.BASE_URL}/auth/oauth/google/callback"
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"Google token error: {e}")
                return None
    
    @staticmethod
    async def get_google_user_info(access_token: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о пользователе Google."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"Google user info error: {e}")
                return None
    
    @staticmethod
    def get_yandex_auth_url(state: str, role: str = "advertiser") -> str:
        """Получить URL для авторизации через Yandex."""
        params = {
            "client_id": settings.YANDEX_CLIENT_ID,
            "redirect_uri": f"{settings.BASE_URL}/auth/oauth/yandex/callback",
            "response_type": "code",
            "state": f"{state}:{role}"
        }
        return f"https://oauth.yandex.ru/authorize?{urlencode(params)}"
    
    @staticmethod
    async def get_yandex_token(code: str) -> Optional[Dict[str, Any]]:
        """Обменять код на токен Yandex."""
        if not settings.YANDEX_CLIENT_ID or not settings.YANDEX_CLIENT_SECRET:
            return None
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://oauth.yandex.ru/token",
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "client_id": settings.YANDEX_CLIENT_ID,
                        "client_secret": settings.YANDEX_CLIENT_SECRET
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
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
        params = {
            "client_id": settings.VK_CLIENT_ID,
            "redirect_uri": f"{settings.BASE_URL}/auth/oauth/vk/callback",
            "response_type": "code",
            "scope": "email",
            "state": f"{state}:{role}",
            "v": "5.131"  # Версия API VK
        }
        return f"https://oauth.vk.com/authorize?{urlencode(params)}"
    
    @staticmethod
    async def get_vk_token(code: str) -> Optional[Dict[str, Any]]:
        """Обменять код на токен VK."""
        if not settings.VK_CLIENT_ID or not settings.VK_CLIENT_SECRET:
            return None
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://oauth.vk.com/access_token",
                    params={
                        "client_id": settings.VK_CLIENT_ID,
                        "client_secret": settings.VK_CLIENT_SECRET,
                        "redirect_uri": f"{settings.BASE_URL}/auth/oauth/vk/callback",
                        "code": code
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
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
