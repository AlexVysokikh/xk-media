"""
Admin API routes для проверки OAuth конфигурации
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.deps import get_db
from app.deps_auth import require_role_for_page
from app.models import User, Role
from app.settings import settings

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/oauth/check")
async def check_oauth_config(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_for_page(Role.ADMIN)),
):
    """Проверить конфигурацию OAuth провайдеров (только для админа)."""
    base_url = settings.BASE_URL.rstrip('/')
    
    config = {
        "base_url": base_url,
        "providers": {}
    }
    
    # Yandex
    config["providers"]["yandex"] = {
        "configured": bool(settings.YANDEX_CLIENT_ID and settings.YANDEX_CLIENT_SECRET),
        "client_id": settings.YANDEX_CLIENT_ID[:20] + "..." if settings.YANDEX_CLIENT_ID else None,
        "redirect_uri": f"{base_url}/auth/oauth/yandex/callback",
        "setup_url": "https://oauth.yandex.ru/",
        "instructions": "Добавьте redirect URI в настройках приложения"
    }
    
    return JSONResponse(content=config)
