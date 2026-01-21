"""
OAuth routes для регистрации и входа через Google, Yandex, VK.
"""

import secrets
from datetime import datetime
from fastapi import APIRouter, Depends, Request, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import User, Role, SiteSettings
from app.services.auth_service import AuthService
from app.services.oauth_service import OAuthService
from app.security import create_access_token

router = APIRouter(prefix="/auth/oauth", tags=["OAuth"])

COOKIE_NAME = "access_token"

# Хранилище state для проверки (в продакшене использовать Redis)
oauth_states = {}


def set_cookie_and_redirect(response: RedirectResponse, user: User, role: str):
    """Установить cookie и перенаправить пользователя."""
    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    
    redirect_url = "/advertiser"
    if role == Role.ADMIN:
        redirect_url = "/admin"
    elif role == Role.VENUE:
        redirect_url = "/venue"
    
    response.url = redirect_url
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=60 * 60 * 24 * 7,  # 7 days
        samesite="lax",
    )
    return response


# ─────────────────────────────────────────────────────────────
# Google OAuth
# ─────────────────────────────────────────────────────────────

@router.get("/google")
async def google_oauth_start(role: str = Query("advertiser", description="Роль: advertiser или venue")):
    """Начать OAuth авторизацию через Google."""
    if role not in [Role.ADVERTISER, Role.VENUE]:
        role = Role.ADVERTISER
    
    state = OAuthService.generate_state()
    oauth_states[state] = {"role": role, "provider": "google"}
    
    auth_url = OAuthService.get_google_auth_url(state, role)
    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
):
    """Обработка callback от Google OAuth."""
    # Проверяем state
    if state not in oauth_states:
        return RedirectResponse(url="/login?error=oauth_invalid", status_code=303)
    
    state_data = oauth_states.pop(state)
    role = state_data.get("role", Role.ADVERTISER)
    
    # Получаем токен
    token_data = await OAuthService.get_google_token(code)
    if not token_data or "access_token" not in token_data:
        return RedirectResponse(url="/login?error=oauth_failed", status_code=303)
    
    # Получаем информацию о пользователе
    user_info = await OAuthService.get_google_user_info(token_data["access_token"])
    if not user_info or "email" not in user_info:
        return RedirectResponse(url="/login?error=oauth_no_email", status_code=303)
    
    email = user_info["email"].lower().strip()
    first_name = user_info.get("given_name") or user_info.get("name", "").split()[0] if user_info.get("name") else None
    last_name = user_info.get("family_name") or (user_info.get("name", "").split()[1] if len(user_info.get("name", "").split()) > 1 else None)
    provider_id = user_info.get("id") or user_info.get("sub")
    
    # Ищем существующего пользователя
    auth = AuthService(db)
    user = auth.get_user_by_email(email)
    
    # Или ищем по OAuth провайдеру
    if not user:
        user = db.query(User).filter(
            User.oauth_provider == "google",
            User.oauth_provider_id == str(provider_id)
        ).first()
    
    if user:
        # Обновляем OAuth данные
        user.oauth_provider = "google"
        user.oauth_provider_id = str(provider_id)
        user.oauth_email = email
        user.last_login = datetime.utcnow()
        db.commit()
    else:
        # Создаем нового пользователя
        # Генерируем случайный пароль (пользователь не будет его знать, но он нужен для модели)
        random_password = secrets.token_urlsafe(32)
        
        # Получаем версию оферты
        offer = db.query(SiteSettings).filter(SiteSettings.key == "offer", SiteSettings.is_active == True).first()
        offer_version = offer.version if offer else "1.0"
        
        user = auth.create_user(
            email=email,
            password=random_password,  # Случайный пароль, вход только через OAuth
            role=role,
            first_name=first_name,
            last_name=last_name,
        )
        user.oauth_provider = "google"
        user.oauth_provider_id = str(provider_id)
        user.oauth_email = email
        user.offer_accepted_at = datetime.utcnow()
        user.offer_version = offer_version
        user.is_verified = True  # OAuth пользователи считаются верифицированными
        db.commit()
    
    # Авторизуем пользователя
    redirect = RedirectResponse(url="/", status_code=303)
    return set_cookie_and_redirect(redirect, user, user.role)


# ─────────────────────────────────────────────────────────────
# Yandex OAuth
# ─────────────────────────────────────────────────────────────

@router.get("/yandex")
async def yandex_oauth_start(role: str = Query("advertiser", description="Роль: advertiser или venue")):
    """Начать OAuth авторизацию через Yandex."""
    if role not in [Role.ADVERTISER, Role.VENUE]:
        role = Role.ADVERTISER
    
    state = OAuthService.generate_state()
    oauth_states[state] = {"role": role, "provider": "yandex"}
    
    auth_url = OAuthService.get_yandex_auth_url(state, role)
    return RedirectResponse(url=auth_url)


@router.get("/yandex/callback")
async def yandex_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
):
    """Обработка callback от Yandex OAuth."""
    if state not in oauth_states:
        return RedirectResponse(url="/login?error=oauth_invalid", status_code=303)
    
    state_data = oauth_states.pop(state)
    role = state_data.get("role", Role.ADVERTISER)
    
    token_data = await OAuthService.get_yandex_token(code)
    if not token_data or "access_token" not in token_data:
        return RedirectResponse(url="/login?error=oauth_failed", status_code=303)
    
    user_info = await OAuthService.get_yandex_user_info(token_data["access_token"])
    if not user_info or "default_email" not in user_info:
        return RedirectResponse(url="/login?error=oauth_no_email", status_code=303)
    
    email = user_info["default_email"].lower().strip()
    first_name = user_info.get("first_name")
    last_name = user_info.get("last_name")
    provider_id = str(user_info.get("id"))
    
    auth = AuthService(db)
    user = auth.get_user_by_email(email)
    
    if not user:
        user = db.query(User).filter(
            User.oauth_provider == "yandex",
            User.oauth_provider_id == provider_id
        ).first()
    
    if user:
        user.oauth_provider = "yandex"
        user.oauth_provider_id = provider_id
        user.oauth_email = email
        user.last_login = datetime.utcnow()
        db.commit()
    else:
        random_password = secrets.token_urlsafe(32)
        offer = db.query(SiteSettings).filter(SiteSettings.key == "offer", SiteSettings.is_active == True).first()
        offer_version = offer.version if offer else "1.0"
        
        user = auth.create_user(
            email=email,
            password=random_password,
            role=role,
            first_name=first_name,
            last_name=last_name,
        )
        user.oauth_provider = "yandex"
        user.oauth_provider_id = provider_id
        user.oauth_email = email
        user.offer_accepted_at = datetime.utcnow()
        user.offer_version = offer_version
        user.is_verified = True
        db.commit()
    
    redirect = RedirectResponse(url="/", status_code=303)
    return set_cookie_and_redirect(redirect, user, user.role)


# ─────────────────────────────────────────────────────────────
# VK OAuth
# ─────────────────────────────────────────────────────────────

@router.get("/vk")
async def vk_oauth_start(role: str = Query("advertiser", description="Роль: advertiser или venue")):
    """Начать OAuth авторизацию через VK."""
    if role not in [Role.ADVERTISER, Role.VENUE]:
        role = Role.ADVERTISER
    
    state = OAuthService.generate_state()
    oauth_states[state] = {"role": role, "provider": "vk"}
    
    auth_url = OAuthService.get_vk_auth_url(state, role)
    return RedirectResponse(url=auth_url)


@router.get("/vk/callback")
async def vk_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
):
    """Обработка callback от VK OAuth."""
    if state not in oauth_states:
        return RedirectResponse(url="/login?error=oauth_invalid", status_code=303)
    
    state_data = oauth_states.pop(state)
    role = state_data.get("role", Role.ADVERTISER)
    
    token_data = await OAuthService.get_vk_token(code)
    if not token_data or "access_token" not in token_data:
        return RedirectResponse(url="/login?error=oauth_failed", status_code=303)
    
    user_id = str(token_data.get("user_id"))
    email = token_data.get("email")  # VK возвращает email в токене
    
    if not email:
        return RedirectResponse(url="/login?error=oauth_no_email", status_code=303)
    
    email = email.lower().strip()
    
    user_info = await OAuthService.get_vk_user_info(token_data["access_token"], user_id)
    first_name = user_info.get("first_name") if user_info else None
    last_name = user_info.get("last_name") if user_info else None
    
    auth = AuthService(db)
    user = auth.get_user_by_email(email)
    
    if not user:
        user = db.query(User).filter(
            User.oauth_provider == "vk",
            User.oauth_provider_id == user_id
        ).first()
    
    if user:
        user.oauth_provider = "vk"
        user.oauth_provider_id = user_id
        user.oauth_email = email
        user.last_login = datetime.utcnow()
        db.commit()
    else:
        random_password = secrets.token_urlsafe(32)
        offer = db.query(SiteSettings).filter(SiteSettings.key == "offer", SiteSettings.is_active == True).first()
        offer_version = offer.version if offer else "1.0"
        
        user = auth.create_user(
            email=email,
            password=random_password,
            role=role,
            first_name=first_name,
            last_name=last_name,
        )
        user.oauth_provider = "vk"
        user.oauth_provider_id = user_id
        user.oauth_email = email
        user.offer_accepted_at = datetime.utcnow()
        user.offer_version = offer_version
        user.is_verified = True
        db.commit()
    
    redirect = RedirectResponse(url="/", status_code=303)
    return set_cookie_and_redirect(redirect, user, user.role)
