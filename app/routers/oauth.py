"""
OAuth routes для регистрации и входа через Yandex.
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
from app.settings import settings

router = APIRouter(prefix="/auth/oauth", tags=["OAuth"])

COOKIE_NAME = "access_token"

# Хранилище state для проверки (в продакшене использовать Redis)
oauth_states = {}


def set_cookie_and_redirect(response: RedirectResponse, user: User, role: str):
    """Установить cookie и перенаправить пользователя."""
    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    
    # Для админа сразу в админку, для остальных - выбор роли
    if user.role == Role.ADMIN:
        redirect_url = "/admin"
    else:
        redirect_url = "/choose-role"
    
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
# Yandex OAuth
# ─────────────────────────────────────────────────────────────

@router.get("/yandex")
async def yandex_oauth_start(role: str = Query("advertiser", description="Роль: advertiser или venue")):
    """Начать OAuth авторизацию через Yandex."""
    if not settings.YANDEX_CLIENT_ID:
        return RedirectResponse(url="/login?error=oauth_not_configured", status_code=303)
    
    if role not in [Role.ADVERTISER, Role.VENUE]:
        role = Role.ADVERTISER
    
    try:
        state = OAuthService.generate_state()
        oauth_states[state] = {"role": role, "provider": "yandex"}
        
        auth_url = OAuthService.get_yandex_auth_url(state, role)
        return RedirectResponse(url=auth_url)
    except Exception as e:
        print(f"Yandex OAuth start error: {e}")
        return RedirectResponse(url="/login?error=oauth_config_error", status_code=303)


@router.get("/yandex/callback")
async def yandex_oauth_callback(
    code: str = Query(None),
    state: str = Query(None),
    error: str = Query(None),
    error_description: str = Query(None),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    """Обработка callback от Yandex OAuth."""
    # Проверяем, есть ли ошибка от Yandex
    if error:
        error_msg = error_description or error
        print(f"Yandex OAuth error: {error} - {error_msg}")
        return RedirectResponse(url=f"/login?error=oauth_failed&details={error}", status_code=303)
    
    # Проверяем наличие обязательных параметров
    if not code or not state:
        print(f"Yandex OAuth callback missing parameters: code={code}, state={state}")
        return RedirectResponse(url="/login?error=oauth_invalid", status_code=303)
    
    if state not in oauth_states:
        print(f"Yandex OAuth invalid state: {state}")
        return RedirectResponse(url="/login?error=oauth_invalid", status_code=303)
    
    state_data = oauth_states.pop(state)
    role = state_data.get("role", Role.ADVERTISER)
    
    try:
        token_data = await OAuthService.get_yandex_token(code)
        if not token_data or "access_token" not in token_data:
            print(f"Yandex OAuth token error: {token_data}")
            return RedirectResponse(url="/login?error=oauth_failed", status_code=303)
        
        user_info = await OAuthService.get_yandex_user_info(token_data["access_token"])
        if not user_info:
            print(f"Yandex OAuth user info is None")
            return RedirectResponse(url="/login?error=oauth_failed", status_code=303)
        
        # Проверяем наличие email разными способами
        email = None
        if "default_email" in user_info:
            email = user_info["default_email"]
        elif "emails" in user_info and user_info["emails"]:
            email = user_info["emails"][0]
        elif "email" in user_info:
            email = user_info["email"]
        
        if not email:
            print(f"Yandex OAuth user info error: no email found. Keys: {list(user_info.keys())}")
            print(f"User info: {user_info}")
            return RedirectResponse(url="/login?error=oauth_no_email", status_code=303)
    except Exception as e:
        print(f"Yandex OAuth callback exception: {e}")
        import traceback
        traceback.print_exc()
        return RedirectResponse(url="/login?error=oauth_failed", status_code=303)
    
    email = email.lower().strip()
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
        
        # Отправляем уведомление о новом пользователе (в фоне)
        if background_tasks:
            try:
                from app.services.notification_service import NotificationService
                background_tasks.add_task(
                    NotificationService.notify_new_user,
                    email=user.email,
                    role=user.role,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    company_name=user.company_name
                )
            except Exception as e:
                print(f"Error scheduling new user notification: {e}")
    
    redirect = RedirectResponse(url="/", status_code=303)
    return set_cookie_and_redirect(redirect, user, user.role)


