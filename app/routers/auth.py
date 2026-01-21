"""
Authentication routes - API (Bearer) and Browser (Cookie) authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, Form, Request, Response, BackgroundTasks
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.deps import get_db
from app.models import Role
from app.services.auth_service import AuthService

router = APIRouter(tags=["Auth"])
templates = Jinja2Templates(directory="app/templates")

COOKIE_NAME = "access_token"


# ─────────────────────────────────────────────────────────────
# Schemas for API
# ─────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    role: str = "advertiser"
    first_name: str | None = None
    last_name: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    first_name: str | None
    last_name: str | None

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────
# API Routes (Bearer token)
# ─────────────────────────────────────────────────────────────

@router.post("/auth/login", response_model=TokenResponse, tags=["Auth API"])
def api_login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    API Login - returns Bearer token for Swagger/API clients.
    """
    auth = AuthService(db)
    user = auth.authenticate(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = auth.create_token_for_user(user)
    return TokenResponse(access_token=token)


@router.post("/auth/register", response_model=UserResponse, tags=["Auth API"])
async def api_register(payload: RegisterRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    API Register - creates new user.
    """
    auth = AuthService(db)
    
    # Check if user exists
    if auth.get_user_by_email(payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate role
    if payload.role not in [Role.ADVERTISER, Role.VENUE]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    user = auth.create_user(
        email=payload.email,
        password=payload.password,
        role=payload.role,
        first_name=payload.first_name,
        last_name=payload.last_name,
    )
    
    # Отправляем уведомление о новом пользователе (в фоне)
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
    
    return user


# ─────────────────────────────────────────────────────────────
# Browser Routes (Cookie-based)
# ─────────────────────────────────────────────────────────────

@router.post("/login", tags=["Auth Browser"])
async def browser_login(
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Browser Login - sets HttpOnly cookie and redirects based on role.
    """
    auth = AuthService(db)
    user = auth.authenticate(email, password)
    
    if not user:
        # Redirect back to login with error
        return RedirectResponse(url="/login?error=invalid", status_code=303)
    
    token = auth.create_token_for_user(user)
    
    # Determine redirect URL based on role
    # Для админа сразу в админку, для остальных - выбор роли
    if user.role == Role.ADMIN:
        redirect_url = "/admin"
    else:
        redirect_url = "/choose-role"
    
    # Create response with redirect
    redirect = RedirectResponse(url=redirect_url, status_code=303)
    
    # Set HttpOnly cookie
    redirect.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=60 * 60 * 24 * 7,  # 7 days
        samesite="lax",
    )
    
    return redirect


@router.post("/register", tags=["Auth Browser"])
async def browser_register(
    response: Response,
    background_tasks: BackgroundTasks,
    role: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(None),
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    accept_offer: str = Form(None),
    db: Session = Depends(get_db),
):
    """
    Browser Register - creates user, sets cookie, and redirects.
    """
    from datetime import datetime
    from app.models import SiteSettings
    
    auth = AuthService(db)
    
    # Validate passwords match
    if password != password_confirm:
        return RedirectResponse(url=f"/register?role={role}&error=passwords", status_code=303)
    
    # Validate offer acceptance
    if not accept_offer:
        return RedirectResponse(url=f"/register?role={role}&error=offer", status_code=303)
    
    # Check if user exists
    if auth.get_user_by_email(email):
        return RedirectResponse(url=f"/register?role={role}&error=exists", status_code=303)
    
    # Validate role
    if role not in [Role.ADVERTISER, Role.VENUE]:
        role = Role.ADVERTISER
    
    # Get current offer version
    offer = db.query(SiteSettings).filter(SiteSettings.key == "offer", SiteSettings.is_active == True).first()
    offer_version = offer.version if offer else "1.0"
    
    # Create user
    user = auth.create_user(
        email=email,
        password=password,
        role=role,
        first_name=first_name,
        last_name=last_name,
    )
    
    # Record offer acceptance
    user.offer_accepted_at = datetime.utcnow()
    user.offer_version = offer_version
    db.commit()
    
    # Отправляем уведомление о новом пользователе (в фоне)
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
    
    token = auth.create_token_for_user(user)
    
    # Redirect to role selection page
    redirect = RedirectResponse(url="/choose-role", status_code=303)
    
    redirect.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        samesite="lax",
    )
    
    return redirect


@router.get("/logout", tags=["Auth Browser"])
async def browser_logout():
    """
    Browser Logout - clears cookie and redirects to home.
    """
    redirect = RedirectResponse(url="/", status_code=303)
    redirect.delete_cookie(key=COOKIE_NAME)
    return redirect


