"""
OAuth routes для регистрации и входа через Yandex.
"""

import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Request, HTTPException, Query, BackgroundTasks
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import User, Role, SiteSettings, OAuthState
from app.services.auth_service import AuthService
from app.services.oauth_service import OAuthService
from app.security import create_access_token
from app.settings import settings

router = APIRouter(prefix="/auth/oauth", tags=["OAuth"])

COOKIE_NAME = "access_token"


def set_cookie_and_redirect(response: RedirectResponse, user: User, role: str):
    """Установить cookie и перенаправить пользователя в ЛК (без выбора роли)."""
    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    
    if user.role == Role.ADMIN:
        redirect_url = "/admin"
    elif user.role == Role.VENUE:
        redirect_url = "/venue"
    else:
        redirect_url = "/advertiser"
    
    new_response = RedirectResponse(url=redirect_url, status_code=303)
    new_response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=60 * 60 * 24 * 7,  # 7 days
        samesite="lax",
    )
    return new_response


# ─────────────────────────────────────────────────────────────
# Yandex OAuth
# ─────────────────────────────────────────────────────────────

@router.get("/yandex")
async def yandex_oauth_start(
    role: str = Query("advertiser", description="Роль: advertiser или venue"),
    db: Session = Depends(get_db)
):
    """Начать OAuth авторизацию через Yandex."""
    if not settings.YANDEX_CLIENT_ID:
        return RedirectResponse(url="/login?error=oauth_not_configured", status_code=303)
    
    if role not in [Role.ADVERTISER, Role.VENUE]:
        role = Role.ADVERTISER
    
    try:
        # Очищаем старые state (старше 10 минут)
        cutoff_time = datetime.utcnow() - timedelta(minutes=10)
        db.query(OAuthState).filter(OAuthState.created_at < cutoff_time).delete()
        db.commit()
        
        state = OAuthService.generate_state()
        # Сохраняем state в базу данных вместо памяти
        oauth_state = OAuthState(
            state=state,
            provider="yandex",
            role=role
        )
        db.add(oauth_state)
        db.commit()
        
        auth_url = OAuthService.get_yandex_auth_url(state, role)
        return RedirectResponse(url=auth_url)
    except Exception as e:
        print(f"Yandex OAuth start error: {e}")
        db.rollback()
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
    
    # Ищем state в базе данных вместо памяти
    oauth_state = db.query(OAuthState).filter(OAuthState.state == state).first()
    if not oauth_state:
        print(f"Yandex OAuth invalid state: {state}")
        return RedirectResponse(url="/login?error=oauth_invalid", status_code=303)
    
    # Проверяем, не истек ли state (старше 10 минут)
    if datetime.utcnow() - oauth_state.created_at > timedelta(minutes=10):
        db.delete(oauth_state)
        db.commit()
        print(f"Yandex OAuth expired state: {state}")
        return RedirectResponse(url="/login?error=oauth_invalid", status_code=303)
    
    role = oauth_state.role
    provider = oauth_state.provider
    
    # Удаляем использованный state
    db.delete(oauth_state)
    db.commit()
    
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
        
        try:
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
        except Exception as e:
            raise
        
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
    
    # Создаем временный redirect для передачи в функцию
    temp_redirect = RedirectResponse(url="/", status_code=303)
    return set_cookie_and_redirect(temp_redirect, user, user.role)


