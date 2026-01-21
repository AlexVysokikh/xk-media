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
        
        if user.role != role:
            # Wrong role - redirect to their dashboard
            redirect_url = "/advertiser"
            if user.role == Role.ADMIN:
                redirect_url = "/admin"
            elif user.role == Role.VENUE:
                redirect_url = "/venue"
            raise RedirectException(redirect_url)
        
        return user
    
    return dependency
