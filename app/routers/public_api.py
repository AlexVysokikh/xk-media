"""
Public API для омниканальности - интеграция digital и оффлайн.
Доступ к контенту ТВ через QR-коды, API для мобильных приложений и веб-сайтов.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List

from app.deps import get_db
from app.models import TV, TVLink, TVStats

router = APIRouter(prefix="/api/public", tags=["Public API"])


# ─────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────

class TVLinkResponse(BaseModel):
    """Ссылка рекламодателя на ТВ."""
    id: int
    title: str
    url: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    position: int
    advertiser_name: Optional[str] = None

    class Config:
        from_attributes = True


class TVContentResponse(BaseModel):
    """Контент для ТВ-экрана."""
    tv_id: int
    tv_code: str
    tv_name: str
    venue_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    links: List[TVLinkResponse] = []
    content_version: int = Field(description="Версия контента для кеширования")
    updated_at: datetime

    class Config:
        from_attributes = True


class QRRedirectResponse(BaseModel):
    """Ответ для QR-кода - редирект или данные."""
    redirect_url: Optional[str] = None
    tv_data: Optional[TVContentResponse] = None
    qr_code: str


class StatsRequest(BaseModel):
    """Запрос на отправку статистики от ТВ-плеера."""
    tv_id: int
    tv_code: Optional[str] = None
    link_id: Optional[int] = None
    event_type: str = Field(..., description="impression, click, view")
    timestamp: Optional[datetime] = None
    device_info: Optional[str] = None
    user_agent: Optional[str] = None


# ─────────────────────────────────────────────────────────────
# Public Endpoints
# ─────────────────────────────────────────────────────────────

@router.get("/screen/{identifier}", response_model=TVContentResponse)
async def get_tv_content(
    identifier: str,
    format: str = Query("json", description="Формат ответа: json или html"),
    db: Session = Depends(get_db),
):
    """
    Получить контент для ТВ-экрана по коду или ID.
    
    Поддерживает:
    - /api/public/screen/{tv_code} - по коду ТВ
    - /api/public/screen/{tv_id} - по ID ТВ
    
    Использование:
    - Для ТВ-плееров: JSON формат для отображения контента
    - Для веб-сайтов: можно использовать HTML формат для редиректа
    - Версионирование контента для кеширования на клиенте
    """
    # Попытка найти по коду
    tv = db.query(TV).filter(TV.code == identifier).first()
    
    # Если не найден по коду, пробуем по ID
    if not tv:
        try:
            tv = db.query(TV).filter(TV.id == int(identifier)).first()
        except (ValueError, TypeError):
            pass
    
    if not tv:
        raise HTTPException(status_code=404, detail="ТВ не найден")
    
    if not tv.is_active:
        raise HTTPException(status_code=403, detail="ТВ неактивен")
    
    # Получаем активные ссылки рекламодателей
    links = db.query(TVLink).filter(
        TVLink.tv_id == tv.id,
        TVLink.is_active == True
    ).order_by(TVLink.position).all()
    
    # Версия контента (можно использовать updated_at или счетчик)
    content_version = int(tv.updated_at.timestamp()) if tv.updated_at else 0
    
    # Формируем ответ
    response_data = TVContentResponse(
        tv_id=tv.id,
        tv_code=tv.code,
        tv_name=tv.name,
        venue_name=tv.venue_name,
        address=tv.address,
        city=tv.city,
        links=[TVLinkResponse(
            id=link.id,
            title=link.title,
            url=link.url,
            description=link.description,
            image_url=link.image_url,
            position=link.position,
            advertiser_name=link.advertiser_name
        ) for link in links],
        content_version=content_version,
        updated_at=tv.updated_at or datetime.utcnow()
    )
    
    # Если запрошен HTML формат, редиректим на публичную страницу
    if format.lower() == "html":
        return RedirectResponse(url=f"/tv/{tv.code}", status_code=302)
    
    return response_data


@router.get("/qr/{qr_code}", response_model=QRRedirectResponse)
async def get_qr_content(
    qr_code: str,
    redirect: bool = Query(True, description="Редирект на HTML страницу или вернуть JSON"),
    db: Session = Depends(get_db),
):
    """
    Получить контент по QR-коду.
    
    QR-код может содержать:
    - Код ТВ (tv_code)
    - ID ТВ (число)
    - Специальный QR-код формата "tv-{code}" или "tv-{id}"
    
    Если redirect=true, перенаправляет на HTML страницу.
    Если redirect=false, возвращает JSON с данными.
    """
    # Очистка QR-кода (может содержать префиксы)
    clean_code = qr_code.strip()
    if clean_code.startswith("tv-"):
        clean_code = clean_code[3:]
    
    # Поиск ТВ
    tv = db.query(TV).filter(TV.code == clean_code).first()
    
    if not tv:
        try:
            tv = db.query(TV).filter(TV.id == int(clean_code)).first()
        except (ValueError, TypeError):
            pass
    
    if not tv:
        raise HTTPException(status_code=404, detail="ТВ не найден по QR-коду")
    
    if not tv.is_active:
        raise HTTPException(status_code=403, detail="ТВ неактивен")
    
    # Если нужен редирект
    if redirect:
        return RedirectResponse(url=f"/tv/{tv.code}", status_code=302)
    
    # Иначе возвращаем JSON
    links = db.query(TVLink).filter(
        TVLink.tv_id == tv.id,
        TVLink.is_active == True
    ).order_by(TVLink.position).all()
    
    content_version = int(tv.updated_at.timestamp()) if tv.updated_at else 0
    
    tv_data = TVContentResponse(
        tv_id=tv.id,
        tv_code=tv.code,
        tv_name=tv.name,
        venue_name=tv.venue_name,
        address=tv.address,
        city=tv.city,
        links=[TVLinkResponse(
            id=link.id,
            title=link.title,
            url=link.url,
            description=link.description,
            image_url=link.image_url,
            position=link.position,
            advertiser_name=link.advertiser_name
        ) for link in links],
        content_version=content_version,
        updated_at=tv.updated_at or datetime.utcnow()
    )
    
    return QRRedirectResponse(
        redirect_url=f"/tv/{tv.code}",
        tv_data=tv_data,
        qr_code=qr_code
    )


@router.post("/stats", response_model=dict)
async def submit_tv_stats(
    stats: StatsRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Отправить статистику от ТВ-плеера.
    
    События:
    - impression: показ ссылки на экране
    - click: клик по ссылке (переход)
    - view: просмотр страницы с рекламодателями
    
    Статистика сохраняется в TVStats для аналитики.
    """
    # Валидация типа события
    valid_events = ["impression", "click", "view"]
    if stats.event_type not in valid_events:
        raise HTTPException(
            status_code=400,
            detail=f"Неверный тип события. Допустимые: {', '.join(valid_events)}"
        )
    
    # Поиск ТВ
    tv = None
    if stats.tv_id:
        tv = db.query(TV).filter(TV.id == stats.tv_id).first()
    elif stats.tv_code:
        tv = db.query(TV).filter(TV.code == stats.tv_code).first()
    
    if not tv:
        raise HTTPException(status_code=404, detail="ТВ не найден")
    
    # Получаем User-Agent из запроса, если не передан
    user_agent = stats.user_agent or request.headers.get("user-agent", "")
    
    # Получаем advertiser_id из TVLink если указан link_id
    advertiser_id = None
    if stats.link_id:
        link = db.query(TVLink).filter(TVLink.id == stats.link_id).first()
        if link:
            advertiser_id = link.advertiser_id
    
    # Сохраняем статистику
    today = datetime.utcnow().date()
    
    # Ищем существующую запись за сегодня
    existing_stat = db.query(TVStats).filter(
        TVStats.tv_id == tv.id,
        TVStats.stat_date == today,
        TVStats.tv_link_id == stats.link_id if stats.link_id else None
    ).first()
    
    if existing_stat:
        # Обновляем существующую запись
        if stats.event_type == "impression":
            existing_stat.impressions += 1
        elif stats.event_type == "click":
            existing_stat.clicks += 1
        elif stats.event_type == "view":
            existing_stat.unique_views += 1
        existing_stat.updated_at = datetime.utcnow()
    else:
        # Создаем новую запись
        new_stat = TVStats(
            tv_id=tv.id,
            tv_link_id=stats.link_id,
            advertiser_id=advertiser_id,
            stat_date=today,
            impressions=1 if stats.event_type == "impression" else 0,
            clicks=1 if stats.event_type == "click" else 0,
            unique_views=1 if stats.event_type == "view" else 0,
            screen_time_seconds=0
        )
        db.add(new_stat)
    
    # Обновляем счетчики в TVLink если это клик или показ
    if stats.link_id:
        link = db.query(TVLink).filter(TVLink.id == stats.link_id).first()
        if link:
            if stats.event_type == "impression":
                link.impressions = (link.impressions or 0) + 1
            elif stats.event_type == "click":
                link.clicks = (link.clicks or 0) + 1
    
    db.commit()
    
    return {
        "status": "ok",
        "message": "Статистика сохранена",
        "tv_id": tv.id,
        "event_type": stats.event_type,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/screen/{identifier}/version")
async def get_content_version(
    identifier: str,
    db: Session = Depends(get_db),
):
    """
    Получить только версию контента для проверки обновлений.
    Используется для оптимизации - клиент может проверить версию
    перед загрузкой полного контента.
    """
    tv = db.query(TV).filter(TV.code == identifier).first()
    
    if not tv:
        try:
            tv = db.query(TV).filter(TV.id == int(identifier)).first()
        except (ValueError, TypeError):
            pass
    
    if not tv:
        raise HTTPException(status_code=404, detail="ТВ не найден")
    
    content_version = int(tv.updated_at.timestamp()) if tv.updated_at else 0
    
    return {
        "tv_id": tv.id,
        "tv_code": tv.code,
        "content_version": content_version,
        "updated_at": tv.updated_at.isoformat() if tv.updated_at else None
    }
