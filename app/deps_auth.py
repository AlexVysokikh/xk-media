"""
Authentication dependencies for FastAPI routes.
Supports both Bearer token (API) and Cookie (Browser) authentication.
"""

from typing import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.deps import get_db
from app.security import decode_access_token
from app.models import User, Role

# For API (Bearer token)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

COOKIE_NAME = "access_token"
COOKIE_CURRENT_ROLE_VIEW = "current_role_view"  # для пользователей с двумя ролями: advertiser | venue


# ─────────────────────────────────────────────────────────────
# Custom Exception for Redirects
# ─────────────────────────────────────────────────────────────

class RedirectException(Exception):
    def __init__(self, url: str):
        self.url = url


# ─────────────────────────────────────────────────────────────
# API Dependencies (Bearer token)
# ─────────────────────────────────────────────────────────────

async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    """
    API Dependency - extracts user_id from Bearer token.
    Raises 401 if token is invalid.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return int(user_id)


async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> User:
    """
    API Dependency - returns full User object.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is inactive")
    return user


def require_role(role: str) -> Callable:
    """
    API Dependency factory - requires specific role.
    Usage: user = Depends(require_role(Role.ADMIN))
    """
    async def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role != role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency


# ─────────────────────────────────────────────────────────────
# Browser Dependencies (Cookie-based)
# ─────────────────────────────────────────────────────────────

async def get_current_user_from_cookie(
    request: Request,
    db: Session = Depends(get_db),
) -> User | None:
    """
    Browser Dependency - extracts user from cookie.
    Returns None if not authenticated (doesn't raise).
    """
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    
    payload = decode_access_token(token)
    if payload is None:
        return None
    
    user_id = payload.get("sub")
    if user_id is None:
        return None
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        return None
    
    return user


async def require_auth_for_page(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """
    Browser Dependency - requires authentication.
    Redirects to /login if not authenticated.
    """
    user = await get_current_user_from_cookie(request, db)
    if not user:
        raise RedirectException("/login")
    return user


def get_effective_view_role(request: Request, user: User) -> str:
    """
    Текущая «видимая» роль для редиректов и отображения ЛК.
    У пользователей с двумя ролями берётся из cookie current_role_view, иначе — user.role.
    """
    if user.role == Role.ADMIN:
        return Role.ADMIN
    if user.has_dual_roles():
        view = request.cookies.get(COOKIE_CURRENT_ROLE_VIEW)
        if view in (Role.ADVERTISER, Role.VENUE):
            return view
        return user.role
    return user.role


def get_role_context(request: Request, user: User) -> dict:
    """Контекст для шаблонов: current_role, has_dual_roles (переключатель показывать только при двух ролях)."""
    return {
        "current_role": get_effective_view_role(request, user),
        "has_dual_roles": user.has_dual_roles(),
    }


def require_role_for_page(role: str) -> Callable:
    """
    Browser Dependency factory - requires specific role for page.
    Redirects to login if not authenticated, or to appropriate dashboard if wrong role.
    
    Usage: user = Depends(require_role_for_page(Role.ADMIN))
    """
    async def dependency(
        request: Request,
        db: Session = Depends(get_db),
    ) -> User:
        user = await get_current_user_from_cookie(request, db)
        
        if not user:
            # Not logged in - redirect to login
            raise RedirectException("/login")
        
        # Доступ: по основной или второй роли (кроме админа — только основная)
        has_role = False
        if role == Role.ADMIN:
            has_role = user.role == Role.ADMIN
        elif role == Role.ADVERTISER:
            has_role = user.has_advertiser_role()
        elif role == Role.VENUE:
            has_role = user.has_venue_role()
        if not has_role:
            effective = get_effective_view_role(request, user)
            redirect_url = "/advertiser"
            if effective == Role.ADMIN:
                redirect_url = "/admin"
            elif effective == Role.VENUE:
                redirect_url = "/venue"
            raise RedirectException(redirect_url)
        
        return user
    
    return dependency
