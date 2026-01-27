"""
HTML pages routes using Jinja2 templates.
"""

import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal

from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from app.deps import get_db
from app.deps_auth import get_current_user_from_cookie, require_role_for_page
from app.models import (
    Payment, User, Role, TV, TVLink, PaymentStatus,
    VenueCategory, TargetAudience, Subscription, VenuePayout, TVStats,
    EquipmentType, VenueDocument, DocumentType, SiteSettings
)
from app.security import get_password_hash, verify_password
from app.settings import settings

router = APIRouter(tags=["Pages"])
templates = Jinja2Templates(directory="app/templates")


# ─────────────────────────────────────────────────────────────
# Public pages
# ─────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def landing(request: Request, user: User = Depends(get_current_user_from_cookie)):
    """Landing page."""
    if user:
        if user.role == Role.ADMIN:
            return RedirectResponse(url="/admin", status_code=303)
        elif user.role == Role.VENUE:
            return RedirectResponse(url="/venue", status_code=303)
        else:
            return RedirectResponse(url="/advertiser", status_code=303)
    
    return templates.TemplateResponse("landing.html", {"request": request})


@router.post("/landing/advertiser-request", response_class=HTMLResponse)
async def advertiser_request(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    company: str = Form(None),
    description: str = Form(...),
    db: Session = Depends(get_db),
):
    """Обработка формы заявки рекламодателя с лендинга."""
    try:
        # Отправляем уведомления
        from app.services.notification_service import NotificationService
        
        await NotificationService.notify_advertiser_request(
            name=name,
            email=email,
            phone=phone,
            company=company,
            description=description
        )
        
        print(f"Новая заявка от рекламодателя: {name} ({email}), телефон: {phone}, компания: {company}")
        
        return templates.TemplateResponse(
            "landing.html",
            {
                "request": request,
                "success_message": "Спасибо! Мы получили вашу заявку и свяжемся с вами в ближайшее время."
            }
        )
    except Exception as e:
        print(f"Ошибка при обработке заявки: {e}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse(
            "landing.html",
            {
                "request": request,
                "error_message": "Произошла ошибка при отправке заявки. Попробуйте еще раз."
            }
        )


@router.post("/landing/venue-request", response_class=HTMLResponse)
async def venue_request(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    venue_name: str = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_db),
):
    """Обработка формы заявки площадки с лендинга (кнопка "ХОЧУ ПОЛУЧАТЬ!")."""
    try:
        # Отправляем уведомления
        from app.services.notification_service import NotificationService
        
        await NotificationService.notify_venue_request(
            name=name,
            email=email,
            phone=phone,
            venue_name=venue_name,
            description=description
        )
        
        print(f"Новая заявка от площадки: {name} ({email}), телефон: {phone}, заведение: {venue_name}")
        
        return templates.TemplateResponse(
            "landing.html",
            {
                "request": request,
                "success_message": "Спасибо! Мы получили вашу заявку и свяжемся с вами в ближайшее время."
            }
        )
    except Exception as e:
        print(f"Ошибка при обработке заявки площадки: {e}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse(
            "landing.html",
            {
                "request": request,
                "error_message": "Произошла ошибка при отправке заявки. Попробуйте еще раз."
            }
        )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None, user: User = Depends(get_current_user_from_cookie)):
    """Login page."""
    if user:
        if user.role == Role.ADMIN:
            return RedirectResponse(url="/admin", status_code=303)
        elif user.role == Role.VENUE:
            return RedirectResponse(url="/venue", status_code=303)
        else:
            return RedirectResponse(url="/advertiser", status_code=303)
    
    error_message = None
    if error == "invalid":
        error_message = "Неверный email или пароль"
    
    return templates.TemplateResponse("login.html", {"request": request, "error": error_message})


@router.get("/choose-role", response_class=HTMLResponse)
async def choose_role_page(request: Request, error: str = None, user: User = Depends(get_current_user_from_cookie)):
    """Page for choosing user role after registration/login."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Если роль уже выбрана и это не первый вход, можно пропустить выбор
    # Но для универсальности всегда показываем выбор
    error_message = None
    if error:
        error_message = "Ошибка при выборе роли. Попробуйте еще раз."
    
    return templates.TemplateResponse("choose_role.html", {
        "request": request,
        "user": user,
        "error": error_message
    })


@router.post("/choose-role", response_class=HTMLResponse)
async def choose_role_save(
    request: Request,
    role: str = Form(...),
    user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db),
):
    """Save selected role and redirect to appropriate dashboard."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Validate role
    if role not in [Role.ADVERTISER, Role.VENUE]:
        return RedirectResponse(url="/choose-role?error=invalid", status_code=303)
    
    # Update user role
    user.role = role
    db.commit()
    
    # Redirect based on selected role
    redirect_url = "/venue" if role == Role.VENUE else "/advertiser"
    return RedirectResponse(url=redirect_url, status_code=303)


@router.post("/switch-role", response_class=HTMLResponse)
async def switch_role(
    request: Request,
    role: str = Form(...),
    user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db),
):
    """Switch user role and redirect to appropriate dashboard."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Admin cannot switch roles
    if user.role == Role.ADMIN:
        return RedirectResponse(url="/admin", status_code=303)
    
    # Validate role
    if role not in [Role.ADVERTISER, Role.VENUE]:
        # Redirect back to current dashboard
        redirect_url = "/venue" if user.role == Role.VENUE else "/advertiser"
        return RedirectResponse(url=redirect_url, status_code=303)
    
    # Don't switch if already in that role
    if user.role == role:
        redirect_url = "/venue" if role == Role.VENUE else "/advertiser"
        return RedirectResponse(url=redirect_url, status_code=303)
    
    # Update user role
    user.role = role
    db.commit()
    
    # Redirect based on selected role
    redirect_url = "/venue" if role == Role.VENUE else "/advertiser"
    return RedirectResponse(url=redirect_url, status_code=303)


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, role: str = "advertiser", error: str = None, user: User = Depends(get_current_user_from_cookie), db: Session = Depends(get_db)):
    """Registration page."""
    if user:
        return RedirectResponse(url="/choose-role", status_code=303)
    
    error_message = None
    if error == "passwords":
        error_message = "Пароли не совпадают"
    elif error == "exists":
        error_message = "Пользователь с таким email уже существует"
    elif error == "offer":
        error_message = "Необходимо принять условия оферты"
    
    # Get offer for checkbox
    offer = db.query(SiteSettings).filter(SiteSettings.key == "offer", SiteSettings.is_active == True).first()
    
    return templates.TemplateResponse("register.html", {
        "request": request, "role": role, "error": error_message,
        "offer": offer
    })


# ─────────────────────────────────────────────────────────────
# Password Reset
# ─────────────────────────────────────────────────────────────

@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request, success: str = None, error: str = None):
    """Forgot password page."""
    success_message = None
    error_message = None
    
    if success == "sent":
        success_message = "✓ Письмо с инструкциями отправлено на вашу почту"
    if error == "not_found":
        error_message = "Пользователь с таким email не найден"
    
    return templates.TemplateResponse("forgot_password.html", {
        "request": request, "success": success_message, "error": error_message
    })


@router.post("/forgot-password", response_class=HTMLResponse)
async def forgot_password_submit(request: Request, db: Session = Depends(get_db)):
    """Process forgot password request."""
    import secrets
    from datetime import timedelta
    
    form = await request.form()
    email = form.get("email", "").lower().strip()
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return RedirectResponse(url="/forgot-password?error=not_found", status_code=303)
    
    # Generate reset token
    token = secrets.token_urlsafe(32)
    user.password_reset_token = token
    user.password_reset_expires = datetime.utcnow() + timedelta(hours=24)
    db.commit()
    
    # In production, send email here
    # For now, just log the reset link
    reset_url = f"{settings.BASE_URL}/reset-password?token={token}"
    print(f"Password reset link for {email}: {reset_url}")
    
    return RedirectResponse(url="/forgot-password?success=sent", status_code=303)


@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request, token: str = None, error: str = None, db: Session = Depends(get_db)):
    """Reset password page."""
    if not token:
        return RedirectResponse(url="/forgot-password", status_code=303)
    
    # Validate token
    user = db.query(User).filter(
        User.password_reset_token == token,
        User.password_reset_expires > datetime.utcnow()
    ).first()
    
    if not user:
        return templates.TemplateResponse("reset_password.html", {
            "request": request, "token": None, "error": "Ссылка недействительна или истекла"
        })
    
    error_message = None
    if error == "mismatch":
        error_message = "Пароли не совпадают"
    elif error == "short":
        error_message = "Пароль должен быть не менее 6 символов"
    
    return templates.TemplateResponse("reset_password.html", {
        "request": request, "token": token, "error": error_message
    })


@router.post("/reset-password", response_class=HTMLResponse)
async def reset_password_submit(request: Request, db: Session = Depends(get_db)):
    """Process password reset."""
    form = await request.form()
    token = form.get("token", "")
    password = form.get("password", "")
    password_confirm = form.get("password_confirm", "")
    
    if password != password_confirm:
        return RedirectResponse(url=f"/reset-password?token={token}&error=mismatch", status_code=303)
    
    if len(password) < 6:
        return RedirectResponse(url=f"/reset-password?token={token}&error=short", status_code=303)
    
    user = db.query(User).filter(
        User.password_reset_token == token,
        User.password_reset_expires > datetime.utcnow()
    ).first()
    
    if not user:
        return RedirectResponse(url="/forgot-password", status_code=303)
    
    # Update password
    user.hashed_password = get_password_hash(password)
    user.password_reset_token = None
    user.password_reset_expires = None
    db.commit()
    
    return RedirectResponse(url="/login?success=password_reset", status_code=303)


# ─────────────────────────────────────────────────────────────
# Offer (Оферта)
# ─────────────────────────────────────────────────────────────

@router.get("/offer", response_class=HTMLResponse)
async def offer_page(request: Request, db: Session = Depends(get_db)):
    """Public offer page."""
    offer = db.query(SiteSettings).filter(SiteSettings.key == "offer", SiteSettings.is_active == True).first()
    
    return templates.TemplateResponse("offer.html", {"request": request, "offer": offer})


# ─────────────────────────────────────────────────────────────
# Advertiser pages
# ─────────────────────────────────────────────────────────────

@router.get("/advertiser", response_class=HTMLResponse)
async def advertiser_dashboard(request: Request, user: User = Depends(require_role_for_page(Role.ADVERTISER)), db: Session = Depends(get_db)):
    """Advertiser dashboard."""
    payments = db.query(Payment).filter(Payment.user_id == user.id).order_by(Payment.created_at.desc()).limit(5).all()
    campaigns = db.query(TVLink).options(joinedload(TVLink.tv)).filter(TVLink.advertiser_id == user.id).all()
    subscriptions = db.query(Subscription).options(joinedload(Subscription.tv)).filter(Subscription.advertiser_id == user.id).order_by(Subscription.end_date.desc()).limit(5).all()
    
    # Mark active subscriptions
    today = date.today()
    for s in subscriptions:
        s.is_active = s.start_date <= today <= s.end_date
    
    # Normalize payment status to string
    for p in payments:
        if hasattr(p.status, 'value'):
            p.status = p.status.value
    
    total_impressions = sum(c.impressions or 0 for c in campaigns)
    total_clicks = sum(c.clicks or 0 for c in campaigns)
    active_tvs = sum(1 for c in campaigns if c.is_active)
    
    # Calculate total paid (handle both string and enum status)
    all_payments = db.query(Payment).filter(Payment.user_id == user.id).all()
    total_paid = sum(float(p.amount) for p in all_payments if (p.status.value if hasattr(p.status, 'value') else p.status) == 'succeeded')
    
    stats = {
        "total_impressions": total_impressions,
        "total_clicks": total_clicks,
        "active_tvs": active_tvs,
        "total_paid": f"{total_paid:.0f}",
        "balance": f"{float(user.balance or 0):.0f}"
    }
    
    return templates.TemplateResponse("advertiser_dashboard.html", {
        "request": request, "user": user, "stats": stats, 
        "payments": payments, "campaigns": campaigns, "subscriptions": subscriptions
    })


def send_video_email(user_email: str, user_name: str, company_name: str, comment: str, video_path: str) -> bool:
    """Отправить ролик и комментарий на почту content@xk-media.ru."""
    try:
        # Настройки SMTP (можно вынести в settings)
        smtp_server = os.getenv("SMTP_SERVER", "smtp.yandex.ru")
        smtp_port = int(os.getenv("SMTP_PORT", "465"))
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        from_email = os.getenv("SMTP_FROM", smtp_user)
        
        to_email = "content@xk-media.ru"
        
        # Если SMTP не настроен, просто логируем
        if not smtp_user or not smtp_password:
            print(f"SMTP не настроен. Ролик от {user_email} ({user_name}) сохранен: {video_path}")
            print(f"Комментарий: {comment}")
            print(f"Отправить на: {to_email}")
            return True  # Возвращаем True, так как файл сохранен
        
        # Создаем сообщение
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = f"Новый ролик от рекламодателя: {user_name or user_email}"
        
        # Текст сообщения
        body = f"""
Новый ролик от рекламодателя

Рекламодатель: {user_name or 'Не указано'}
Email: {user_email}
Компания: {company_name or 'Не указано'}
Дата отправки: {datetime.now().strftime('%d.%m.%Y %H:%M')}

Комментарий:
{comment or 'Комментарий не указан'}

---
Это автоматическое сообщение от системы XK Media.
"""
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Прикрепляем файл
        if os.path.exists(video_path):
            with open(video_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(video_path)}'
            )
            msg.attach(part)
        
        # Отправляем email
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
        
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Ошибка отправки email: {e}")
        # Все равно возвращаем True, так как файл сохранен
        return True


@router.post("/advertiser/upload-video", response_class=HTMLResponse)
async def advertiser_upload_video(
    request: Request,
    video_file: UploadFile = File(...),
    comment: str = Form(None),
    user: User = Depends(require_role_for_page(Role.ADVERTISER)),
    db: Session = Depends(get_db),
):
    """Обработка загрузки ролика от рекламодателя."""
    try:
        # Проверка размера файла (100 МБ)
        file_content = await video_file.read()
        file_size = len(file_content)
        max_size = 100 * 1024 * 1024  # 100 МБ
        
        if file_size > max_size:
            return RedirectResponse(url="/advertiser?error=video_too_large", status_code=303)
        
        # Проверка типа файла
        allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        file_ext = Path(video_file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            return RedirectResponse(url="/advertiser?error=video_invalid_format", status_code=303)
        
        # Создаем директорию для загрузок, если её нет
        upload_dir = Path("app/static/uploads/videos")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Генерируем уникальное имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{user.id}_{timestamp}_{video_file.filename}"
        file_path = upload_dir / safe_filename
        
        # Сохраняем файл
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Отправляем на почту
        user_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email
        send_video_email(
            user_email=user.email,
            user_name=user_name,
            company_name=user.company_name or "",
            comment=comment or "",
            video_path=str(file_path)
        )
        
        return RedirectResponse(url="/advertiser?success=video_sent", status_code=303)
        
    except Exception as e:
        print(f"Ошибка загрузки ролика: {e}")
        return RedirectResponse(url="/advertiser?error=video_upload_failed", status_code=303)


@router.get("/advertiser/payments", response_class=HTMLResponse)
async def advertiser_payments_page(request: Request, warning: str = None, error: str = None, msg: str = None, success: str = None, user: User = Depends(require_role_for_page(Role.ADVERTISER)), db: Session = Depends(get_db)):
    """Advertiser payments page."""
    payments = db.query(Payment).filter(Payment.user_id == user.id).order_by(Payment.created_at.desc()).all()
    
    # Normalize status to string for template
    for p in payments:
        if hasattr(p.status, 'value'):
            p.status = p.status.value
    
    # Calculate stats
    success_payments = [p for p in payments if p.status == 'succeeded']
    total_paid = sum(float(p.amount) for p in success_payments)
    
    # Total spent on subscriptions
    subscriptions = db.query(Subscription).filter(Subscription.advertiser_id == user.id).all()
    total_spent = sum(float(s.price) for s in subscriptions)
    
    stats = {
        "total_paid": f"{total_paid:.0f}",
        "total_spent": f"{total_spent:.0f}",
        "payments_count": len(payments),
        "success_count": len(success_payments)
    }
    
    warning_message = None
    error_message = None
    
    if error == "yookassa":
        error_message = f"⚠️ Ошибка YooKassa: {msg or 'Не удалось создать платеж. Проверьте настройки или попробуйте позже.'}"
    elif warning == "yookassa":
        warning_message = "⚠️ YooKassa не настроен. Платёж создан, но оплата недоступна."
    elif warning == "paykeeper":
        warning_message = "⚠️ PayKeeper не настроен. Платёж создан, но оплата недоступна."
    
    success_message = None
    if success == "paid":
        success_message = "✓ Платёж успешно проведён! Баланс пополнен."
    
    return templates.TemplateResponse("advertiser_payments.html", {
        "request": request, "user": user, "payments": payments, "stats": stats,
        "balance": f"{float(user.balance or 0):.0f}", "warning": warning_message, "error": error_message, "success": success_message
    })


@router.post("/advertiser/payments/create-page", response_class=HTMLResponse)
async def advertiser_create_payment_page(request: Request, user: User = Depends(require_role_for_page(Role.ADVERTISER)), db: Session = Depends(get_db)):
    """Create payment and redirect to YooKassa."""
    import uuid
    from app.payments.yookassa_client import create_payment
    from app.settings import settings
    
    form = await request.form()
    amount = float(form.get("amount", 0))
    purpose = form.get("purpose", "Пополнение баланса")
    order_id = f"adv-{user.id}-{uuid.uuid4().hex[:8]}"
    
    payment = Payment(user_id=user.id, amount=amount, currency="RUB", description=purpose, order_id=order_id, status=PaymentStatus.WAITING)
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    try:
        return_url = settings.YOOKASSA_RETURN_URL
        yk_result = create_payment(
            amount=amount,
            order_id=str(payment.id),
            description=purpose,
            return_url=return_url,
            client_email=user.email,
            client_phone=user.phone,
        )
        
        payment.yk_payment_id = yk_result["payment_id"]
        payment.pay_url = yk_result["confirmation_url"]
        db.commit()
        return RedirectResponse(url=payment.pay_url, status_code=303)
    except Exception as e:
        error_msg = str(e)
        print(f"YooKassa error: {error_msg}")
        import traceback
        traceback.print_exc()
        # Сохраняем ошибку в платеже для отладки
        payment.raw_notify = f"Error: {error_msg}"
        db.commit()
        return RedirectResponse(url=f"/advertiser/payments?error=yookassa&msg={error_msg[:50]}", status_code=303)


@router.get("/advertiser/stats", response_class=HTMLResponse)
async def advertiser_stats(request: Request, period: str = None, date_from: str = None, date_to: str = None, tv_id: int = None, user: User = Depends(require_role_for_page(Role.ADVERTISER)), db: Session = Depends(get_db)):
    """Advertiser stats with filters."""
    from datetime import timedelta
    
    # Load campaigns with TV relationship
    campaigns = db.query(TVLink).options(joinedload(TVLink.tv)).filter(TVLink.advertiser_id == user.id).all()
    all_campaigns = list(campaigns)  # for filter dropdown
    
    # Filter by TV if specified
    selected_tv_id = None
    if tv_id:
        campaigns = [c for c in campaigns if c.tv_id == tv_id]
        selected_tv_id = tv_id
    
    # Calculate stats
    total_impressions = sum(c.impressions or 0 for c in campaigns)
    total_clicks = sum(c.clicks or 0 for c in campaigns)
    active_count = sum(1 for c in campaigns if c.is_active)
    conversion = f"{(total_clicks / total_impressions * 100):.2f}" if total_impressions > 0 else "0"
    
    stats = {
        "impressions": total_impressions,
        "clicks": total_clicks,
        "active_count": active_count,
        "conversion": conversion
    }
    
    # Daily stats placeholder (will be populated from API later)
    daily_stats = []
    
    today = date.today()
    date_from_val = date_from or (today - timedelta(days=30)).strftime("%Y-%m-%d")
    date_to_val = date_to or today.strftime("%Y-%m-%d")
    
    return templates.TemplateResponse("advertiser_stats.html", {
        "request": request, "user": user, "campaigns": campaigns, "all_campaigns": all_campaigns,
        "stats": stats, "daily_stats": daily_stats, "period": period,
        "date_from": date_from_val, "date_to": date_to_val, "selected_tv_id": selected_tv_id
    })


@router.get("/advertiser/subscriptions", response_class=HTMLResponse)
async def advertiser_subscriptions(request: Request, error: str = None, success: str = None, user: User = Depends(require_role_for_page(Role.ADVERTISER)), db: Session = Depends(get_db)):
    """Advertiser subscriptions page."""
    subscriptions = db.query(Subscription).options(joinedload(Subscription.tv)).filter(Subscription.advertiser_id == user.id).order_by(Subscription.end_date.desc()).all()
    available_tvs = db.query(TV).filter(TV.is_active == True).all()
    
    # Mark active subscriptions and calculate days left
    today = date.today()
    active_subscriptions = []
    expired_subscriptions = []
    
    for s in subscriptions:
        s.is_active = s.start_date <= today <= s.end_date
        s.days_left = (s.end_date - today).days if s.is_active else 0
        if s.is_active:
            active_subscriptions.append(s)
        else:
            expired_subscriptions.append(s)
    
    error_message = None
    if error == "balance":
        error_message = "❌ Недостаточно средств на балансе. Пополните баланс."
    elif error == "dates":
        error_message = "❌ Неверные даты. Дата окончания должна быть позже даты начала."
    
    success_message = None
    if success == "created":
        success_message = "✓ Подписка успешно оформлена! Размещение активно."
    
    return templates.TemplateResponse("advertiser_subscriptions.html", {
        "request": request, "user": user, 
        "active_subscriptions": active_subscriptions,
        "expired_subscriptions": expired_subscriptions,
        "available_tvs": available_tvs, "balance": f"{float(user.balance or 0):.0f}",
        "today": date.today().strftime("%Y-%m-%d"),
        "error": error_message, "success": success_message,
        "categories": VenueCategory.CHOICES, "audiences": TargetAudience.CHOICES
    })


@router.post("/advertiser/subscriptions/create", response_class=HTMLResponse)
async def advertiser_subscriptions_create(request: Request, background_tasks: BackgroundTasks, user: User = Depends(require_role_for_page(Role.ADVERTISER)), db: Session = Depends(get_db)):
    """Create subscription from advertiser balance."""
    form = await request.form()
    
    tv_id = int(form.get("tv_id", 0))
    start_date_str = form.get("start_date", "")
    end_date_str = form.get("end_date", "")
    title = form.get("title", "")
    url = form.get("url", "")
    description = form.get("description") or None
    price = float(form.get("price", 0))
    
    # Validate dates
    try:
        start_dt = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        if end_dt < start_dt:
            return RedirectResponse(url="/advertiser/subscriptions?error=dates", status_code=303)
    except:
        return RedirectResponse(url="/advertiser/subscriptions?error=dates", status_code=303)
    
    # Check balance
    current_balance = float(user.balance or 0)
    if current_balance < price:
        return RedirectResponse(url="/advertiser/subscriptions?error=balance", status_code=303)
    
    # Get TV
    tv = db.query(TV).filter(TV.id == tv_id).first()
    if not tv:
        return RedirectResponse(url="/advertiser/subscriptions?error=tv", status_code=303)
    
    # Create subscription
    subscription = Subscription(
        advertiser_id=user.id,
        tv_id=tv_id,
        start_date=start_dt,
        end_date=end_dt,
        price=Decimal(str(price)),
        venue_payout=Decimal(str(price * (tv.revenue_share or 30) / 100)),
        is_active=True
    )
    db.add(subscription)
    
    # Create TV link
    link = TVLink(
        tv_id=tv_id,
        advertiser_id=user.id,
        advertiser_name=user.company_name or f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email,
        title=title,
        url=url,
        description=description,
        is_active=True
    )
    db.add(link)
    
    # Deduct from balance
    user.balance = Decimal(str(current_balance - price))
    
    db.commit()
    db.refresh(subscription)
    
    # Отправляем уведомление о создании подписки (в фоне)
    try:
        from app.services.notification_service import NotificationService
        background_tasks.add_task(
            NotificationService.notify_subscription_created,
            user_email=user.email,
            user_name=user.company_name or f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email,
            tv_name=tv.name,
            start_date=start_dt.strftime("%d.%m.%Y"),
            end_date=end_dt.strftime("%d.%m.%Y"),
            amount=float(price),
            subscription_id=subscription.id
        )
    except Exception as e:
        print(f"Error scheduling subscription notification: {e}")
    
    return RedirectResponse(url="/advertiser/subscriptions?success=created", status_code=303)


@router.get("/advertiser/export/csv")
async def advertiser_export_csv(request: Request, date_from: str = None, date_to: str = None, user: User = Depends(require_role_for_page(Role.ADVERTISER)), db: Session = Depends(get_db)):
    """Export advertiser stats to CSV."""
    from fastapi.responses import Response
    import csv
    import io
    
    campaigns = db.query(TVLink).options(joinedload(TVLink.tv)).filter(TVLink.advertiser_id == user.id).all()
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    # Header
    writer.writerow(['ТВ-экран', 'Место размещения', 'Город', 'Адрес', 'Название рекламы', 'URL', 'Показы', 'Переходы (CPC)', 'Конверсия %', 'Статус'])
    
    # Data
    for c in campaigns:
        conv = f"{(c.clicks or 0) / (c.impressions or 1) * 100:.2f}" if c.impressions else "0"
        writer.writerow([
            c.tv.name,
            c.tv.venue_name or '',
            c.tv.city or '',
            c.tv.address or '',
            c.title,
            c.url,
            c.impressions or 0,
            c.clicks or 0,
            conv,
            'Активна' if c.is_active else 'Неактивна'
        ])
    
    # Totals
    total_imp = sum(c.impressions or 0 for c in campaigns)
    total_clicks = sum(c.clicks or 0 for c in campaigns)
    total_conv = f"{total_clicks / total_imp * 100:.2f}" if total_imp else "0"
    writer.writerow(['ИТОГО', '', '', '', '', '', total_imp, total_clicks, total_conv, ''])
    
    content = output.getvalue()
    
    return Response(
        content=content.encode('utf-8-sig'),
        media_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename=xk_media_stats_{date.today().strftime("%Y%m%d")}.csv'}
    )


@router.get("/advertiser/campaigns", response_class=HTMLResponse)
async def advertiser_campaigns(request: Request, user: User = Depends(require_role_for_page(Role.ADVERTISER)), db: Session = Depends(get_db)):
    """Advertiser campaigns list."""
    campaigns = db.query(TVLink).options(joinedload(TVLink.tv)).filter(TVLink.advertiser_id == user.id).all()
    
    total_impressions = sum(c.impressions or 0 for c in campaigns)
    total_clicks = sum(c.clicks or 0 for c in campaigns)
    active_count = sum(1 for c in campaigns if c.is_active)
    
    stats = {
        "total_impressions": total_impressions,
        "total_clicks": total_clicks,
        "active_count": active_count
    }
    
    return templates.TemplateResponse("advertiser_campaigns.html", {
        "request": request, "user": user, "campaigns": campaigns, "stats": stats
    })


@router.get("/advertiser/profile", response_class=HTMLResponse)
async def advertiser_profile(request: Request, success: str = None, user: User = Depends(require_role_for_page(Role.ADVERTISER)), db: Session = Depends(get_db)):
    """Advertiser profile page."""
    success_message = None
    if success == "saved":
        success_message = "Данные сохранены"
    elif success == "password":
        success_message = "Пароль изменён"
    
    return templates.TemplateResponse("advertiser_profile.html", {"request": request, "user": user, "success": success_message})


@router.post("/advertiser/profile", response_class=HTMLResponse)
async def advertiser_profile_update(request: Request, user: User = Depends(require_role_for_page(Role.ADVERTISER)), db: Session = Depends(get_db)):
    """Update advertiser profile."""
    form = await request.form()
    user.first_name = form.get("first_name") or None
    user.last_name = form.get("last_name") or None
    user.phone = form.get("phone") or None
    db.commit()
    return RedirectResponse(url="/advertiser/profile?success=saved", status_code=303)


@router.post("/advertiser/profile/company", response_class=HTMLResponse)
async def advertiser_profile_company(request: Request, user: User = Depends(require_role_for_page(Role.ADVERTISER)), db: Session = Depends(get_db)):
    """Update advertiser company info."""
    form = await request.form()
    user.company_name = form.get("company_name") or None
    user.website = form.get("website") or None
    user.legal_name = form.get("legal_name") or None
    user.inn = form.get("inn") or None
    user.kpp = form.get("kpp") or None
    user.legal_address = form.get("legal_address") or None
    user.description = form.get("description") or None
    db.commit()
    return RedirectResponse(url="/advertiser/profile?success=saved", status_code=303)


@router.post("/advertiser/profile/password", response_class=HTMLResponse)
async def advertiser_profile_password(request: Request, user: User = Depends(require_role_for_page(Role.ADVERTISER)), db: Session = Depends(get_db)):
    """Change advertiser password."""
    form = await request.form()
    current = form.get("current_password", "")
    new_pass = form.get("new_password", "")
    confirm = form.get("confirm_password", "")
    
    if not verify_password(current, user.hashed_password):
        return RedirectResponse(url="/advertiser/profile?error=wrong_password", status_code=303)
    
    if new_pass != confirm or len(new_pass) < 6:
        return RedirectResponse(url="/advertiser/profile?error=password_mismatch", status_code=303)
    
    user.hashed_password = get_password_hash(new_pass)
    db.commit()
    return RedirectResponse(url="/advertiser/profile?success=password", status_code=303)


# ─────────────────────────────────────────────────────────────
# Venue pages
# ─────────────────────────────────────────────────────────────

@router.get("/venue", response_class=HTMLResponse)
async def venue_dashboard(request: Request, user: User = Depends(require_role_for_page(Role.VENUE)), db: Session = Depends(get_db)):
    """Venue dashboard with earnings overview."""
    tvs = db.query(TV).filter(TV.venue_id == user.id).all()
    
    # Calculate earnings
    total_earnings = Decimal('0')
    total_paid = Decimal('0')
    total_impressions = 0
    total_clicks = 0
    active_advertisers = set()
    
    for tv in tvs:
        # Get subscriptions for this TV
        subscriptions = db.query(Subscription).filter(Subscription.tv_id == tv.id).all()
        for sub in subscriptions:
            total_earnings += sub.venue_payout or Decimal('0')
            active_advertisers.add(sub.advertiser_id)
        
        # Get impressions from links
        links = db.query(TVLink).filter(TVLink.tv_id == tv.id).all()
        for link in links:
            total_impressions += link.impressions or 0
            total_clicks += link.clicks or 0
    
    # Get paid payouts
    payouts = db.query(VenuePayout).filter(VenuePayout.venue_id == user.id, VenuePayout.status == "paid").all()
    total_paid = sum(Decimal(str(p.amount)) for p in payouts)
    
    # Pending payouts
    pending = total_earnings - total_paid
    
    # Recent payouts
    recent_payouts = db.query(VenuePayout).filter(VenuePayout.venue_id == user.id).order_by(VenuePayout.created_at.desc()).limit(5).all()
    
    stats = {
        "total_tvs": len(tvs),
        "active_tvs": sum(1 for tv in tvs if tv.is_active and tv.is_approved),
        "total_impressions": total_impressions,
        "total_clicks": total_clicks,
        "total_earnings": f"{float(total_earnings):.0f}",
        "total_paid": f"{float(total_paid):.0f}",
        "pending": f"{float(pending):.0f}",
        "advertisers_count": len(active_advertisers)
    }
    
    return templates.TemplateResponse("venue_dashboard.html", {
        "request": request, "user": user, "stats": stats, "tvs": tvs, "recent_payouts": recent_payouts
    })


@router.get("/venue/tvs", response_class=HTMLResponse)
async def venue_tvs_list(request: Request, success: str = None, error: str = None, user: User = Depends(require_role_for_page(Role.VENUE)), db: Session = Depends(get_db)):
    """Venue TV list."""
    tvs = db.query(TV).filter(TV.venue_id == user.id).order_by(TV.created_at.desc()).all()
    
    # Enrich TVs with stats
    for tv in tvs:
        tv.links_count = db.query(TVLink).filter(TVLink.tv_id == tv.id).count()
        tv.active_subscriptions = db.query(Subscription).filter(
            Subscription.tv_id == tv.id,
            Subscription.end_date >= date.today()
        ).count()
        impressions = db.query(TVLink).filter(TVLink.tv_id == tv.id).all()
        tv.total_impressions = sum(l.impressions or 0 for l in impressions)
    
    success_message = None
    if success == "created":
        success_message = "✓ ТВ успешно добавлен! Ожидайте подтверждения модерацией."
    elif success == "updated":
        success_message = "✓ Данные ТВ обновлены."
    
    error_message = None
    if error == "code_exists":
        error_message = "❌ ТВ с таким кодом уже существует."
    
    return templates.TemplateResponse("venue_tvs.html", {
        "request": request, "user": user, "tvs": tvs,
        "categories": VenueCategory.CHOICES, "audiences": TargetAudience.CHOICES,
        "equipment_types": EquipmentType.CHOICES,
        "success": success_message, "error": error_message
    })


@router.get("/venue/tv/add", response_class=HTMLResponse)
async def venue_tv_add_page(request: Request, user: User = Depends(require_role_for_page(Role.VENUE)), db: Session = Depends(get_db)):
    """Add new TV page."""
    return templates.TemplateResponse("venue_tv_add.html", {
        "request": request, "user": user,
        "categories": VenueCategory.CHOICES, "audiences": TargetAudience.CHOICES,
        "equipment_types": EquipmentType.CHOICES
    })


@router.post("/venue/tv/add", response_class=HTMLResponse)
async def venue_tv_add(request: Request, user: User = Depends(require_role_for_page(Role.VENUE)), db: Session = Depends(get_db)):
    """Create new TV."""
    import uuid
    form = await request.form()
    
    # Generate unique code
    code = form.get("code", "").strip()
    if not code:
        code = f"tv-{uuid.uuid4().hex[:8]}"
    
    # Check if code exists
    if db.query(TV).filter(TV.code == code).first():
        return RedirectResponse(url="/venue/tvs?error=code_exists", status_code=303)
    
    # Determine revenue share based on equipment type
    equipment_type = form.get("equipment_type", EquipmentType.AGGREGATOR)
    revenue_share = EquipmentType.REVENUE_SHARE.get(equipment_type, 60.0)
    
    tv = TV(
        code=code,
        name=form.get("name", ""),
        venue_name=form.get("venue_name") or user.company_name or None,
        category=form.get("category", VenueCategory.OTHER),
        target_audience=form.get("target_audience", TargetAudience.MASS),
        city=form.get("city") or None,
        address=form.get("address") or None,
        description=form.get("description") or None,
        photo_url=form.get("photo_url") or None,
        clients_per_day=int(form.get("clients_per_day", 0) or 0),
        avg_check=float(form.get("avg_check", 0) or 0),
        working_hours=form.get("working_hours") or None,
        
        # Legal info from user
        legal_name=form.get("legal_name") or user.legal_name or None,
        inn=form.get("inn") or user.inn or None,
        kpp=form.get("kpp") or None,
        bank_name=form.get("bank_name") or None,
        bank_bik=form.get("bank_bik") or None,
        bank_account=form.get("bank_account") or None,
        contact_person=form.get("contact_person") or f"{user.first_name or ''} {user.last_name or ''}".strip() or None,
        contact_phone=form.get("contact_phone") or user.phone or None,
        contact_email=form.get("contact_email") or user.email or None,
        
        # Financials
        equipment_type=equipment_type,
        revenue_share=revenue_share,
        
        # Owner and status
        venue_id=user.id,
        is_active=True,
        is_approved=False  # Needs moderation
    )
    db.add(tv)
    db.commit()
    
    return RedirectResponse(url="/venue/tvs?success=created", status_code=303)


@router.get("/venue/tv/{tv_id}", response_class=HTMLResponse)
async def venue_tv_detail(request: Request, tv_id: int, user: User = Depends(require_role_for_page(Role.VENUE)), db: Session = Depends(get_db)):
    """Venue TV detail page."""
    tv = db.query(TV).filter(TV.id == tv_id, TV.venue_id == user.id).first()
    if not tv:
        return RedirectResponse(url="/venue/tvs", status_code=303)
    
    # Get advertisers on this TV
    links = db.query(TVLink).options(joinedload(TVLink.advertiser)).filter(TVLink.tv_id == tv.id).all()
    
    # Get subscriptions for this TV
    subscriptions = db.query(Subscription).options(joinedload(Subscription.advertiser)).filter(Subscription.tv_id == tv.id).order_by(Subscription.end_date.desc()).all()
    
    # Calculate earnings for this TV
    total_earned = sum(float(s.venue_payout or 0) for s in subscriptions)
    active_subs = [s for s in subscriptions if s.start_date <= date.today() <= s.end_date]
    
    # Impressions stats
    total_impressions = sum(l.impressions or 0 for l in links)
    total_clicks = sum(l.clicks or 0 for l in links)
    
    return templates.TemplateResponse("venue_tv_detail.html", {
        "request": request, "user": user, "tv": tv,
        "links": links, "subscriptions": subscriptions,
        "total_earned": f"{total_earned:.0f}",
        "active_subs_count": len(active_subs),
        "total_impressions": total_impressions, "total_clicks": total_clicks,
        "categories": VenueCategory.CHOICES, "audiences": TargetAudience.CHOICES,
        "equipment_types": EquipmentType.CHOICES
    })


@router.post("/venue/tv/{tv_id}", response_class=HTMLResponse)
async def venue_tv_update(request: Request, tv_id: int, user: User = Depends(require_role_for_page(Role.VENUE)), db: Session = Depends(get_db)):
    """Update TV info."""
    tv = db.query(TV).filter(TV.id == tv_id, TV.venue_id == user.id).first()
    if not tv:
        return RedirectResponse(url="/venue/tvs", status_code=303)
    
    form = await request.form()
    
    tv.name = form.get("name", tv.name)
    tv.venue_name = form.get("venue_name") or None
    tv.category = form.get("category", tv.category)
    tv.target_audience = form.get("target_audience", tv.target_audience)
    tv.city = form.get("city") or None
    tv.address = form.get("address") or None
    tv.description = form.get("description") or None
    tv.photo_url = form.get("photo_url") or None
    tv.clients_per_day = int(form.get("clients_per_day", 0) or 0)
    tv.avg_check = float(form.get("avg_check", 0) or 0)
    tv.working_hours = form.get("working_hours") or None
    
    db.commit()
    return RedirectResponse(url=f"/venue/tv/{tv_id}?success=updated", status_code=303)


@router.post("/venue/tv/{tv_id}/legal", response_class=HTMLResponse)
async def venue_tv_update_legal(request: Request, tv_id: int, user: User = Depends(require_role_for_page(Role.VENUE)), db: Session = Depends(get_db)):
    """Update TV legal and bank info."""
    tv = db.query(TV).filter(TV.id == tv_id, TV.venue_id == user.id).first()
    if not tv:
        return RedirectResponse(url="/venue/tvs", status_code=303)
    
    form = await request.form()
    
    tv.legal_name = form.get("legal_name") or None
    tv.inn = form.get("inn") or None
    tv.kpp = form.get("kpp") or None
    tv.bank_name = form.get("bank_name") or None
    tv.bank_bik = form.get("bank_bik") or None
    tv.bank_account = form.get("bank_account") or None
    tv.contact_person = form.get("contact_person") or None
    tv.contact_phone = form.get("contact_phone") or None
    tv.contact_email = form.get("contact_email") or None
    
    db.commit()
    return RedirectResponse(url=f"/venue/tv/{tv_id}?success=legal_updated", status_code=303)


@router.get("/venue/advertisers", response_class=HTMLResponse)
async def venue_advertisers(request: Request, tv_id: int = None, user: User = Depends(require_role_for_page(Role.VENUE)), db: Session = Depends(get_db)):
    """Venue advertisers page - shows who advertises on venue's TVs."""
    tvs = db.query(TV).filter(TV.venue_id == user.id).all()
    tv_ids = [tv.id for tv in tvs]
    
    # Filter by specific TV if requested
    if tv_id and tv_id in tv_ids:
        query_tv_ids = [tv_id]
    else:
        query_tv_ids = tv_ids
    
    # Get all links for venue's TVs
    links = db.query(TVLink).options(
        joinedload(TVLink.tv),
        joinedload(TVLink.advertiser)
    ).filter(TVLink.tv_id.in_(query_tv_ids)).all() if query_tv_ids else []
    
    # Get subscriptions with payment info
    subscriptions = db.query(Subscription).options(
        joinedload(Subscription.tv),
        joinedload(Subscription.advertiser)
    ).filter(Subscription.tv_id.in_(query_tv_ids)).order_by(Subscription.end_date.desc()).all() if query_tv_ids else []
    
    # Aggregate by advertiser
    advertiser_data = {}
    for sub in subscriptions:
        adv_id = sub.advertiser_id
        if adv_id not in advertiser_data:
            advertiser_data[adv_id] = {
                "advertiser": sub.advertiser,
                "total_paid": 0,
                "venue_share": 0,
                "subscriptions": [],
                "tv_names": set()
            }
        advertiser_data[adv_id]["total_paid"] += float(sub.price or 0)
        advertiser_data[adv_id]["venue_share"] += float(sub.venue_payout or 0)
        advertiser_data[adv_id]["subscriptions"].append(sub)
        advertiser_data[adv_id]["tv_names"].add(sub.tv.name if sub.tv else "")
    
    # Calculate total
    total_revenue = sum(d["total_paid"] for d in advertiser_data.values())
    total_venue_share = sum(d["venue_share"] for d in advertiser_data.values())
    
    return templates.TemplateResponse("venue_advertisers.html", {
        "request": request, "user": user, "tvs": tvs,
        "links": links, "advertiser_data": advertiser_data.values(),
        "total_revenue": f"{total_revenue:.0f}",
        "total_venue_share": f"{total_venue_share:.0f}",
        "selected_tv_id": tv_id
    })


@router.get("/venue/earnings", response_class=HTMLResponse)
async def venue_earnings(request: Request, period: str = None, user: User = Depends(require_role_for_page(Role.VENUE)), db: Session = Depends(get_db)):
    """Venue earnings and payouts page."""
    from datetime import timedelta
    
    tvs = db.query(TV).filter(TV.venue_id == user.id).all()
    tv_ids = [tv.id for tv in tvs]
    
    # Get all subscriptions for earnings calculation
    subscriptions = db.query(Subscription).options(
        joinedload(Subscription.tv),
        joinedload(Subscription.advertiser)
    ).filter(Subscription.tv_id.in_(tv_ids)).order_by(Subscription.created_at.desc()).all() if tv_ids else []
    
    # Get payouts
    payouts = db.query(VenuePayout).filter(VenuePayout.venue_id == user.id).order_by(VenuePayout.created_at.desc()).all()
    
    # Calculate totals
    total_earned = sum(float(s.venue_payout or 0) for s in subscriptions)
    total_paid = sum(float(p.amount) for p in payouts if p.status == "paid")
    pending = total_earned - total_paid
    
    # Pending payouts
    pending_payouts = [p for p in payouts if p.status in ["pending", "processing"]]
    completed_payouts = [p for p in payouts if p.status == "paid"]
    
    # Monthly breakdown
    monthly_data = {}
    for sub in subscriptions:
        month_key = sub.start_date.strftime("%Y-%m") if sub.start_date else "unknown"
        if month_key not in monthly_data:
            monthly_data[month_key] = {"earnings": 0, "count": 0}
        monthly_data[month_key]["earnings"] += float(sub.venue_payout or 0)
        monthly_data[month_key]["count"] += 1
    
    # Sort by month
    monthly_breakdown = sorted(monthly_data.items(), key=lambda x: x[0], reverse=True)
    
    stats = {
        "total_earned": f"{total_earned:.0f}",
        "total_paid": f"{total_paid:.0f}",
        "pending": f"{pending:.0f}",
        "subscriptions_count": len(subscriptions)
    }
    
    return templates.TemplateResponse("venue_earnings.html", {
        "request": request, "user": user, "stats": stats,
        "subscriptions": subscriptions[:20],  # Last 20
        "pending_payouts": pending_payouts,
        "completed_payouts": completed_payouts[:10],
        "monthly_breakdown": monthly_breakdown,
        "tvs": tvs
    })


@router.get("/venue/documents", response_class=HTMLResponse)
async def venue_documents(request: Request, user: User = Depends(require_role_for_page(Role.VENUE)), db: Session = Depends(get_db)):
    """Venue closing documents page."""
    documents = db.query(VenueDocument).filter(VenueDocument.venue_id == user.id).order_by(VenueDocument.created_at.desc()).all()
    
    # Get payouts for document generation
    payouts = db.query(VenuePayout).filter(VenuePayout.venue_id == user.id, VenuePayout.status == "paid").all()
    
    # Stats
    total_amount = sum(float(d.amount or 0) for d in documents if d.status == "signed")
    pending_docs = [d for d in documents if d.status in ["created", "sent"]]
    signed_docs = [d for d in documents if d.status == "signed"]
    
    return templates.TemplateResponse("venue_documents.html", {
        "request": request, "user": user, "documents": documents,
        "payouts": payouts, "pending_docs": pending_docs, "signed_docs": signed_docs,
        "total_amount": f"{total_amount:.0f}",
        "document_types": DocumentType.CHOICES
    })


@router.post("/venue/documents/request", response_class=HTMLResponse)
async def venue_request_document(request: Request, user: User = Depends(require_role_for_page(Role.VENUE)), db: Session = Depends(get_db)):
    """Request a closing document."""
    form = await request.form()
    
    doc_type = form.get("document_type", DocumentType.ACT)
    payout_id = form.get("payout_id")
    
    # Get payout if specified
    payout = None
    if payout_id:
        payout = db.query(VenuePayout).filter(VenuePayout.id == int(payout_id), VenuePayout.venue_id == user.id).first()
    
    # Generate document number
    doc_count = db.query(VenueDocument).filter(VenueDocument.venue_id == user.id).count()
    doc_number = f"XK-{user.id}-{doc_count + 1}"
    
    title_map = {
        DocumentType.ACT: "Акт выполненных работ",
        DocumentType.INVOICE: "Счёт на оплату",
        DocumentType.REPORT: "Отчёт о размещении рекламы",
        DocumentType.CONTRACT: "Договор на размещение рекламы"
    }
    
    document = VenueDocument(
        venue_id=user.id,
        payout_id=int(payout_id) if payout_id else None,
        document_type=doc_type,
        number=doc_number,
        title=f"{title_map.get(doc_type, 'Документ')} №{doc_number}",
        period_start=payout.period_start if payout else None,
        period_end=payout.period_end if payout else None,
        amount=payout.amount if payout else Decimal('0'),
        status="created"
    )
    db.add(document)
    db.commit()
    
    return RedirectResponse(url="/venue/documents?success=requested", status_code=303)


@router.get("/venue/profile", response_class=HTMLResponse)
async def venue_profile(request: Request, success: str = None, user: User = Depends(require_role_for_page(Role.VENUE)), db: Session = Depends(get_db)):
    """Venue profile page."""
    tvs = db.query(TV).filter(TV.venue_id == user.id).all()
    
    success_message = None
    if success == "saved":
        success_message = "✓ Данные сохранены"
    elif success == "password":
        success_message = "✓ Пароль изменён"
    
    return templates.TemplateResponse("venue_profile.html", {
        "request": request, "user": user, "tvs": tvs, "success": success_message
    })


@router.post("/venue/profile", response_class=HTMLResponse)
async def venue_profile_update(request: Request, user: User = Depends(require_role_for_page(Role.VENUE)), db: Session = Depends(get_db)):
    """Update venue profile."""
    form = await request.form()
    user.first_name = form.get("first_name") or None
    user.last_name = form.get("last_name") or None
    user.phone = form.get("phone") or None
    user.company_name = form.get("company_name") or None
    user.legal_name = form.get("legal_name") or None
    user.inn = form.get("inn") or None
    user.kpp = form.get("kpp") or None
    user.legal_address = form.get("legal_address") or None
    user.website = form.get("website") or None
    user.description = form.get("description") or None
    db.commit()
    return RedirectResponse(url="/venue/profile?success=saved", status_code=303)


@router.post("/venue/profile/password", response_class=HTMLResponse)
async def venue_profile_password(request: Request, user: User = Depends(require_role_for_page(Role.VENUE)), db: Session = Depends(get_db)):
    """Change venue password."""
    form = await request.form()
    current = form.get("current_password", "")
    new_pass = form.get("new_password", "")
    confirm = form.get("confirm_password", "")
    
    if not verify_password(current, user.hashed_password):
        return RedirectResponse(url="/venue/profile?error=wrong_password", status_code=303)
    
    if new_pass != confirm or len(new_pass) < 6:
        return RedirectResponse(url="/venue/profile?error=password_mismatch", status_code=303)
    
    user.hashed_password = get_password_hash(new_pass)
    db.commit()
    return RedirectResponse(url="/venue/profile?success=password", status_code=303)


# ─────────────────────────────────────────────────────────────
# Admin pages
# ─────────────────────────────────────────────────────────────

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Admin dashboard."""
    payments = db.query(Payment).order_by(Payment.created_at.desc()).limit(5).all()
    
    total_users = db.query(User).count()
    advertisers = db.query(User).filter(User.role == Role.ADVERTISER).count()
    venues = db.query(User).filter(User.role == Role.VENUE).count()
    total_tvs = db.query(TV).count()
    total_revenue = sum(float(p.amount) for p in db.query(Payment).filter(Payment.status == "succeeded").all())
    
    stats = {
        "total_users": total_users, "total_tvs": total_tvs,
        "total_revenue": f"{total_revenue:.0f}", "advertisers": advertisers, "venues": venues
    }
    
    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "user": user, "stats": stats, "payments": payments})


# ─────────────────────────────────────────────────────────────
# Admin: Users
# ─────────────────────────────────────────────────────────────

@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users_list(request: Request, role: str = None, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Admin users list."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    users = query.order_by(User.created_at.desc()).all()
    
    return templates.TemplateResponse("admin_users.html", {"request": request, "user": user, "users": users, "role_filter": role})


@router.get("/admin/user/{user_id}", response_class=HTMLResponse)
async def admin_user_detail(request: Request, user_id: int, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Admin user detail page."""
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        return RedirectResponse(url="/admin/users", status_code=303)
    
    payments = db.query(Payment).filter(Payment.user_id == user_id).order_by(Payment.created_at.desc()).all()
    subscriptions = db.query(Subscription).filter(Subscription.advertiser_id == user_id).all()
    owned_tvs = db.query(TV).filter(TV.venue_id == user_id).all()
    
    return templates.TemplateResponse("admin_user_detail.html", {
        "request": request, "user": user, "target_user": target_user,
        "payments": payments, "subscriptions": subscriptions, "owned_tvs": owned_tvs
    })


@router.post("/admin/user/{user_id}", response_class=HTMLResponse)
async def admin_user_update(request: Request, user_id: int, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Update user basic info."""
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        return RedirectResponse(url="/admin/users", status_code=303)
    
    form = await request.form()
    target_user.first_name = form.get("first_name") or None
    target_user.last_name = form.get("last_name") or None
    target_user.phone = form.get("phone") or None
    target_user.role = form.get("role", target_user.role)
    target_user.is_verified = "is_verified" in form
    db.commit()
    
    return RedirectResponse(url=f"/admin/user/{user_id}", status_code=303)


@router.post("/admin/user/{user_id}/company", response_class=HTMLResponse)
async def admin_user_update_company(request: Request, user_id: int, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Update user company info."""
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        return RedirectResponse(url="/admin/users", status_code=303)
    
    form = await request.form()
    target_user.company_name = form.get("company_name") or None
    target_user.legal_name = form.get("legal_name") or None
    target_user.inn = form.get("inn") or None
    target_user.kpp = form.get("kpp") or None
    target_user.legal_address = form.get("legal_address") or None
    db.commit()
    
    return RedirectResponse(url=f"/admin/user/{user_id}", status_code=303)


@router.post("/admin/user/{user_id}/add-balance", response_class=HTMLResponse)
async def admin_user_add_balance(request: Request, user_id: int, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Add balance to user manually."""
    import uuid
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        return RedirectResponse(url="/admin/users", status_code=303)
    
    form = await request.form()
    amount = float(form.get("amount", 0))
    comment = form.get("comment", "Ручное пополнение администратором")
    
    if amount > 0:
        # Create payment record
        payment = Payment(
            user_id=user_id, amount=amount, currency="RUB",
            description=comment, order_id=f"manual-{uuid.uuid4().hex[:8]}",
            status=PaymentStatus.SUCCEEDED, paid_at=datetime.utcnow()
        )
        db.add(payment)
        target_user.balance = Decimal(str(float(target_user.balance or 0) + amount))
        db.commit()
    
    return RedirectResponse(url=f"/admin/user/{user_id}", status_code=303)


@router.get("/admin/user/{user_id}/block", response_class=HTMLResponse)
async def admin_user_block(request: Request, user_id: int, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Block user."""
    target_user = db.query(User).filter(User.id == user_id).first()
    if target_user and target_user.id != user.id:
        target_user.is_active = False
        db.commit()
    return RedirectResponse(url=f"/admin/user/{user_id}", status_code=303)


@router.get("/admin/user/{user_id}/unblock", response_class=HTMLResponse)
async def admin_user_unblock(request: Request, user_id: int, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Unblock user."""
    target_user = db.query(User).filter(User.id == user_id).first()
    if target_user:
        target_user.is_active = True
        db.commit()
    return RedirectResponse(url=f"/admin/user/{user_id}", status_code=303)


@router.get("/admin/user/{user_id}/delete", response_class=HTMLResponse)
async def admin_user_delete(request: Request, user_id: int, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Delete user account and all related data."""
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        return RedirectResponse(url="/admin/users", status_code=303)
    
    # Нельзя удалить админа
    if target_user.role == Role.ADMIN:
        return RedirectResponse(url=f"/admin/user/{user_id}?error=cannot_delete_admin", status_code=303)
    
    # Удаляем все связанные данные
    # Подписки
    db.query(Subscription).filter(Subscription.advertiser_id == user_id).delete()
    
    # Рекламные ссылки
    db.query(TVLink).filter(TVLink.advertiser_id == user_id).delete()
    
    # Платежи
    db.query(Payment).filter(Payment.user_id == user_id).delete()
    
    # ТВ, принадлежащие площадке
    if target_user.role == Role.VENUE:
        venue_tvs = db.query(TV).filter(TV.venue_id == user_id).all()
        for tv in venue_tvs:
            # Удаляем ссылки и подписки на эти ТВ
            db.query(TVLink).filter(TVLink.tv_id == tv.id).delete()
            db.query(Subscription).filter(Subscription.tv_id == tv.id).delete()
            db.query(VenuePayout).filter(VenuePayout.tv_id == tv.id).delete()
            db.delete(tv)
        
        # Выплаты площадке
        db.query(VenuePayout).filter(VenuePayout.venue_id == user_id).delete()
    
    # Удаляем пользователя
    db.delete(target_user)
    db.commit()
    
    return RedirectResponse(url="/admin/users?deleted=1", status_code=303)


@router.get("/admin/advertisers/add", response_class=HTMLResponse)
async def admin_advertiser_add_page(request: Request, error: str = None, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Add advertiser page."""
    error_message = None
    if error == "exists":
        error_message = "Пользователь с таким email уже существует"
    return templates.TemplateResponse("admin_advertiser_add.html", {"request": request, "user": user, "error": error_message})


@router.post("/admin/advertisers/add", response_class=HTMLResponse)
async def admin_advertiser_add(request: Request, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Create new advertiser."""
    form = await request.form()
    email = form.get("email", "").lower().strip()
    password = form.get("password", "")
    
    # Check if exists
    if db.query(User).filter(User.email == email).first():
        return RedirectResponse(url="/admin/advertisers/add?error=exists", status_code=303)
    
    initial_balance = float(form.get("initial_balance", 0))
    
    new_user = User(
        email=email,
        hashed_password=get_password_hash(password),
        role=Role.ADVERTISER,
        first_name=form.get("first_name") or None,
        last_name=form.get("last_name") or None,
        phone=form.get("phone") or None,
        company_name=form.get("company_name") or None,
        website=form.get("website") or None,
        legal_name=form.get("legal_name") or None,
        inn=form.get("inn") or None,
        kpp=form.get("kpp") or None,
        legal_address=form.get("legal_address") or None,
        description=form.get("description") or None,
        balance=Decimal(str(initial_balance)),
        is_verified="is_verified" in form,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    
    return RedirectResponse(url=f"/admin/user/{new_user.id}", status_code=303)


# ─────────────────────────────────────────────────────────────
# Admin: TVs
# ─────────────────────────────────────────────────────────────

@router.get("/admin/tvs", response_class=HTMLResponse)
async def admin_tvs_list(request: Request, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Admin TV list."""
    tvs = db.query(TV).order_by(TV.id.desc()).all()
    for tv in tvs:
        tv.links_count = len(tv.links) if tv.links else 0
    
    return templates.TemplateResponse("admin_tvs.html", {
        "request": request, "user": user, "tvs": tvs,
        "categories": VenueCategory.CHOICES, "audiences": TargetAudience.CHOICES
    })


@router.post("/admin/tvs/add", response_class=HTMLResponse)
async def admin_tvs_add(
    request: Request,
    user: User = Depends(require_role_for_page(Role.ADMIN)),
    db: Session = Depends(get_db),
    photo_file: UploadFile = File(None)
):
    """Add new TV."""
    form = await request.form()
    
    # Check if code exists
    code = form.get("code", "").strip()
    if db.query(TV).filter(TV.code == code).first():
        return RedirectResponse(url="/admin/tvs?error=code_exists", status_code=303)
    
    # Обработка фото
    photo_url = form.get("photo_url", "").strip() or None
    
    # Если загружен файл, сохраняем его
    if photo_file and photo_file.filename:
        from pathlib import Path
        import uuid
        
        upload_dir = Path("app/static/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Генерируем уникальное имя файла
        file_ext = Path(photo_file.filename).suffix
        file_name = f"tv_{code}_{uuid.uuid4().hex[:8]}{file_ext}"
        file_path = upload_dir / file_name
        
        # Сохраняем файл
        with open(file_path, "wb") as buffer:
            content = await photo_file.read()
            buffer.write(content)
        
        photo_url = f"/static/uploads/{file_name}"
    
    tv = TV(
        code=code,
        name=form.get("name", ""),
        venue_name=form.get("venue_name") or None,
        category=form.get("category", VenueCategory.OTHER),
        target_audience=form.get("target_audience", TargetAudience.MASS),
        city=form.get("city") or None,
        address=form.get("address") or None,
        legal_name=form.get("legal_name") or None,
        inn=form.get("inn") or None,
        revenue_share=float(form.get("revenue_share", 30)),
        contact_person=form.get("contact_person") or None,
        contact_phone=form.get("contact_phone") or None,
        contact_email=form.get("contact_email") or None,
        description=form.get("description") or None,
        photo_url=photo_url,
        is_active=True
    )
    db.add(tv)
    db.commit()
    
    return RedirectResponse(url=f"/admin/tv/{tv.code}", status_code=303)


@router.get("/admin/tv/{tv_code}", response_class=HTMLResponse)
async def admin_tv_detail(request: Request, tv_code: str, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Admin TV detail page."""
    tv = db.query(TV).filter(TV.code == tv_code).first()
    if not tv:
        try:
            tv = db.query(TV).filter(TV.id == int(tv_code)).first()
        except ValueError:
            pass
    
    if not tv:
        return RedirectResponse(url="/admin/tvs", status_code=303)
    
    links = db.query(TVLink).options(joinedload(TVLink.advertiser)).filter(TVLink.tv_id == tv.id).order_by(TVLink.position).all()
    advertisers = db.query(User).filter(User.role == Role.ADVERTISER).all()
    venues = db.query(User).filter(User.role == Role.VENUE).all()
    subscriptions = db.query(Subscription).options(joinedload(Subscription.advertiser)).filter(Subscription.tv_id == tv.id).all()
    
    return templates.TemplateResponse("admin_tv_detail.html", {
        "request": request, "user": user, "tv": tv, "links": links,
        "advertisers": advertisers, "venues": venues, "subscriptions": subscriptions,
        "categories": VenueCategory.CHOICES, "audiences": TargetAudience.CHOICES
    })


@router.post("/admin/tv/{tv_code}", response_class=HTMLResponse)
async def admin_tv_update(
    request: Request,
    tv_code: str,
    user: User = Depends(require_role_for_page(Role.ADMIN)),
    db: Session = Depends(get_db),
    photo_file: UploadFile = File(None)
):
    """Update TV basic info."""
    tv = db.query(TV).filter(TV.code == tv_code).first()
    if not tv:
        return RedirectResponse(url="/admin/tvs", status_code=303)
    
    form = await request.form()
    tv.name = form.get("name", tv.name)
    tv.venue_name = form.get("venue_name") or None
    tv.category = form.get("category", tv.category)
    tv.target_audience = form.get("target_audience", tv.target_audience)
    tv.description = form.get("description") or None
    tv.is_active = "is_active" in form
    
    # Обработка фото
    photo_url = form.get("photo_url", "").strip() or None
    
    # Если загружен файл, сохраняем его
    if photo_file and photo_file.filename:
        from pathlib import Path
        import uuid
        
        upload_dir = Path("app/static/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Генерируем уникальное имя файла
        file_ext = Path(photo_file.filename).suffix
        file_name = f"tv_{tv_code}_{uuid.uuid4().hex[:8]}{file_ext}"
        file_path = upload_dir / file_name
        
        # Сохраняем файл
        with open(file_path, "wb") as buffer:
            content = await photo_file.read()
            buffer.write(content)
        
        photo_url = f"/static/uploads/{file_name}"
    
    if photo_url is not None:
        tv.photo_url = photo_url
    
    db.commit()
    
    return RedirectResponse(url=f"/admin/tv/{tv.code}", status_code=303)


@router.post("/admin/tv/{tv_code}/location", response_class=HTMLResponse)
async def admin_tv_update_location(request: Request, tv_code: str, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Update TV location and legal info."""
    tv = db.query(TV).filter(TV.code == tv_code).first()
    if not tv:
        return RedirectResponse(url="/admin/tvs", status_code=303)
    
    form = await request.form()
    tv.city = form.get("city") or None
    tv.address = form.get("address") or None
    tv.legal_name = form.get("legal_name") or None
    tv.inn = form.get("inn") or None
    tv.revenue_share = float(form.get("revenue_share", 30))
    tv.contact_person = form.get("contact_person") or None
    tv.contact_phone = form.get("contact_phone") or None
    tv.contact_email = form.get("contact_email") or None
    db.commit()
    
    return RedirectResponse(url=f"/admin/tv/{tv.code}", status_code=303)


@router.post("/admin/tv/{tv_code}/owner", response_class=HTMLResponse)
async def admin_tv_update_owner(request: Request, tv_code: str, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Update TV owner (venue)."""
    tv = db.query(TV).filter(TV.code == tv_code).first()
    if not tv:
        return RedirectResponse(url="/admin/tvs", status_code=303)
    
    form = await request.form()
    venue_id = form.get("venue_id")
    tv.venue_id = int(venue_id) if venue_id else None
    db.commit()
    
    return RedirectResponse(url=f"/admin/tv/{tv.code}", status_code=303)


@router.get("/admin/tv/{tv_code}/delete", response_class=HTMLResponse)
async def admin_tv_delete(request: Request, tv_code: str, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Delete TV."""
    tv = db.query(TV).filter(TV.code == tv_code).first()
    if tv:
        db.delete(tv)
        db.commit()
    return RedirectResponse(url="/admin/tvs", status_code=303)


@router.post("/admin/tv/{tv_code}/add-link", response_class=HTMLResponse)
async def admin_tv_add_link(request: Request, tv_code: str, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Add advertiser link to TV."""
    tv = db.query(TV).filter(TV.code == tv_code).first()
    if not tv:
        return RedirectResponse(url="/admin/tvs", status_code=303)
    
    form = await request.form()
    advertiser_id = int(form.get("advertiser_id", 0))
    title = form.get("title", "")
    url = form.get("url", "")
    description = form.get("description", "")
    
    if advertiser_id and title and url:
        advertiser = db.query(User).filter(User.id == advertiser_id).first()
        max_pos = db.query(TVLink).filter(TVLink.tv_id == tv.id).count()
        
        link = TVLink(
            tv_id=tv.id, advertiser_id=advertiser_id,
            advertiser_name=advertiser.company_name or f"{advertiser.first_name or ''} {advertiser.last_name or ''}".strip() or advertiser.email if advertiser else "Unknown",
            title=title, url=url, description=description, position=max_pos
        )
        db.add(link)
        db.commit()
    
    return RedirectResponse(url=f"/admin/tv/{tv.code}", status_code=303)


@router.get("/admin/tv/{tv_code}/link/{link_id}/delete", response_class=HTMLResponse)
async def admin_tv_delete_link(request: Request, tv_code: str, link_id: int, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Delete advertiser link from TV."""
    link = db.query(TVLink).filter(TVLink.id == link_id).first()
    if link:
        db.delete(link)
        db.commit()
    return RedirectResponse(url=f"/admin/tv/{tv_code}", status_code=303)


# ─────────────────────────────────────────────────────────────
# Admin: TV Advertisers (отдельная страница)
# ─────────────────────────────────────────────────────────────

@router.get("/admin/tv/{tv_code}/advertisers", response_class=HTMLResponse)
async def admin_tv_advertisers(request: Request, tv_code: str, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """TV advertisers page."""
    tv = db.query(TV).filter(TV.code == tv_code).first()
    if not tv:
        return RedirectResponse(url="/admin/tvs", status_code=303)
    
    links = db.query(TVLink).options(joinedload(TVLink.advertiser)).filter(TVLink.tv_id == tv.id).order_by(TVLink.position).all()
    all_advertisers = db.query(User).filter(User.role == Role.ADVERTISER).all()
    
    total_impressions = sum(l.impressions or 0 for l in links)
    total_clicks = sum(l.clicks or 0 for l in links)
    
    return templates.TemplateResponse("admin_tv_advertisers.html", {
        "request": request, "user": user, "tv": tv, "links": links,
        "all_advertisers": all_advertisers, "total_impressions": total_impressions, "total_clicks": total_clicks
    })


@router.post("/admin/tv/{tv_code}/advertisers/add", response_class=HTMLResponse)
async def admin_tv_advertisers_add(request: Request, tv_code: str, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Add advertiser to TV."""
    tv = db.query(TV).filter(TV.code == tv_code).first()
    if not tv:
        return RedirectResponse(url="/admin/tvs", status_code=303)
    
    form = await request.form()
    advertiser_id = int(form.get("advertiser_id", 0))
    advertiser = db.query(User).filter(User.id == advertiser_id).first()
    
    if advertiser:
        max_pos = db.query(TVLink).filter(TVLink.tv_id == tv.id).count()
        link = TVLink(
            tv_id=tv.id,
            advertiser_id=advertiser_id,
            advertiser_name=advertiser.company_name or f"{advertiser.first_name or ''} {advertiser.last_name or ''}".strip() or advertiser.email,
            title=form.get("title", ""),
            url=form.get("url", ""),
            description=form.get("description") or None,
            image_url=form.get("image_url") or None,
            position=max_pos,
            is_active=True
        )
        db.add(link)
        db.commit()
    
    return RedirectResponse(url=f"/admin/tv/{tv_code}/advertisers", status_code=303)


@router.get("/admin/tv/{tv_code}/advertisers/{link_id}/edit", response_class=HTMLResponse)
async def admin_tv_advertiser_edit_page(request: Request, tv_code: str, link_id: int, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Edit TV advertiser page."""
    tv = db.query(TV).filter(TV.code == tv_code).first()
    link = db.query(TVLink).options(joinedload(TVLink.advertiser)).filter(TVLink.id == link_id).first()
    if not tv or not link:
        return RedirectResponse(url="/admin/tvs", status_code=303)
    
    all_advertisers = db.query(User).filter(User.role == Role.ADVERTISER).all()
    
    return templates.TemplateResponse("admin_tv_advertiser_edit.html", {
        "request": request, "user": user, "tv": tv, "link": link, "all_advertisers": all_advertisers
    })


@router.post("/admin/tv/{tv_code}/advertisers/{link_id}/edit", response_class=HTMLResponse)
async def admin_tv_advertiser_edit(request: Request, tv_code: str, link_id: int, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Update TV advertiser."""
    link = db.query(TVLink).filter(TVLink.id == link_id).first()
    if not link:
        return RedirectResponse(url=f"/admin/tv/{tv_code}/advertisers", status_code=303)
    
    form = await request.form()
    
    # Update advertiser if changed
    new_advertiser_id = int(form.get("advertiser_id", link.advertiser_id))
    if new_advertiser_id != link.advertiser_id:
        advertiser = db.query(User).filter(User.id == new_advertiser_id).first()
        if advertiser:
            link.advertiser_id = new_advertiser_id
            link.advertiser_name = advertiser.company_name or f"{advertiser.first_name or ''} {advertiser.last_name or ''}".strip() or advertiser.email
    
    link.title = form.get("title", link.title)
    link.url = form.get("url", link.url)
    link.description = form.get("description") or None
    link.image_url = form.get("image_url") or None
    link.position = int(form.get("position", link.position))
    link.is_active = "is_active" in form
    link.impressions = int(form.get("impressions", link.impressions or 0))
    link.clicks = int(form.get("clicks", link.clicks or 0))
    
    db.commit()
    return RedirectResponse(url=f"/admin/tv/{tv_code}/advertisers", status_code=303)


@router.get("/admin/tv/{tv_code}/advertisers/{link_id}/toggle", response_class=HTMLResponse)
async def admin_tv_advertiser_toggle(request: Request, tv_code: str, link_id: int, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Toggle TV advertiser status."""
    link = db.query(TVLink).filter(TVLink.id == link_id).first()
    if link:
        link.is_active = not link.is_active
        db.commit()
    return RedirectResponse(url=f"/admin/tv/{tv_code}/advertisers", status_code=303)


@router.get("/admin/tv/{tv_code}/advertisers/{link_id}/delete", response_class=HTMLResponse)
async def admin_tv_advertiser_delete(request: Request, tv_code: str, link_id: int, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Delete TV advertiser."""
    link = db.query(TVLink).filter(TVLink.id == link_id).first()
    if link:
        db.delete(link)
        db.commit()
    return RedirectResponse(url=f"/admin/tv/{tv_code}/advertisers", status_code=303)


# ─────────────────────────────────────────────────────────────
# Admin: Payments
# ─────────────────────────────────────────────────────────────

@router.get("/admin/payments", response_class=HTMLResponse)
async def admin_payments_list(request: Request, status: str = None, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Admin payments list."""
    query = db.query(Payment)
    if status:
        query = query.filter(Payment.status == status)
    payments = query.order_by(Payment.created_at.desc()).all()
    
    # Stats
    all_payments = db.query(Payment).all()
    total_revenue = sum(float(p.amount) for p in all_payments if p.status == "succeeded")
    
    # This month
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_revenue = sum(float(p.amount) for p in all_payments if p.status == "succeeded" and p.paid_at and p.paid_at >= month_start)
    pending_count = sum(1 for p in all_payments if p.status in ["pending", "waiting"])
    
    stats = {
        "total_revenue": f"{total_revenue:.0f}",
        "month_revenue": f"{month_revenue:.0f}",
        "pending_count": pending_count
    }
    
    return templates.TemplateResponse("admin_payments.html", {
        "request": request, "user": user, "payments": payments,
        "stats": stats, "status_filter": status
    })


@router.get("/admin/payment/{payment_id}/confirm", response_class=HTMLResponse)
async def admin_payment_confirm(request: Request, payment_id: int, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Manually confirm payment."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if payment and payment.status in ["pending", "waiting"]:
        payment.status = PaymentStatus.SUCCEEDED
        payment.paid_at = datetime.utcnow()
        
        # Update user balance
        target_user = db.query(User).filter(User.id == payment.user_id).first()
        if target_user:
            target_user.balance = Decimal(str(float(target_user.balance or 0) + float(payment.amount)))
        
        db.commit()
    
    return RedirectResponse(url="/admin/payments", status_code=303)


@router.get("/admin/payment/{payment_id}/cancel", response_class=HTMLResponse)
async def admin_payment_cancel(request: Request, payment_id: int, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Cancel payment."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if payment and payment.status in ["pending", "waiting"]:
        payment.status = PaymentStatus.CANCELED
        db.commit()
    
    return RedirectResponse(url="/admin/payments", status_code=303)


# ─────────────────────────────────────────────────────────────
# Admin: Payouts
# ─────────────────────────────────────────────────────────────

@router.get("/admin/payouts", response_class=HTMLResponse)
async def admin_payouts_list(request: Request, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Admin payouts list."""
    payouts = db.query(VenuePayout).order_by(VenuePayout.created_at.desc()).all()
    venues = db.query(User).filter(User.role == Role.VENUE).all()
    
    # Calculate stats
    total_payouts = sum(float(p.amount) for p in payouts if p.status == "paid")
    pending_payouts = sum(float(p.amount) for p in payouts if p.status in ["pending", "processing"])
    
    # Venue stats
    venue_stats = []
    for venue in venues:
        tv_count = db.query(TV).filter(TV.venue_id == venue.id).count()
        total_earned = sum(float(s.venue_payout or 0) for s in db.query(Subscription).join(TV).filter(TV.venue_id == venue.id).all())
        total_paid = sum(float(p.amount) for p in db.query(VenuePayout).filter(VenuePayout.venue_id == venue.id, VenuePayout.status == "paid").all())
        
        venue_stats.append({
            "venue": venue,
            "tv_count": tv_count,
            "total_earned": total_earned,
            "total_paid": total_paid,
            "pending": total_earned - total_paid
        })
    
    stats = {
        "total_payouts": f"{total_payouts:.0f}",
        "pending_payouts": f"{pending_payouts:.0f}",
        "venues_count": len(venues)
    }
    
    return templates.TemplateResponse("admin_payouts.html", {
        "request": request, "user": user, "payouts": payouts,
        "venues": venues, "venue_stats": venue_stats, "stats": stats
    })


@router.post("/admin/payout/create", response_class=HTMLResponse)
async def admin_payout_create(request: Request, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Create new payout."""
    form = await request.form()
    
    payout = VenuePayout(
        venue_id=int(form.get("venue_id")),
        period_start=datetime.strptime(form.get("period_start"), "%Y-%m-%d").date(),
        period_end=datetime.strptime(form.get("period_end"), "%Y-%m-%d").date(),
        amount=float(form.get("amount", 0)),
        payment_details=form.get("payment_details") or None,
        status="pending"
    )
    db.add(payout)
    db.commit()
    
    return RedirectResponse(url="/admin/payouts", status_code=303)


@router.get("/admin/payout/{payout_id}/process", response_class=HTMLResponse)
async def admin_payout_process(request: Request, payout_id: int, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Mark payout as processing."""
    payout = db.query(VenuePayout).filter(VenuePayout.id == payout_id).first()
    if payout:
        payout.status = "processing"
        db.commit()
    return RedirectResponse(url="/admin/payouts", status_code=303)


@router.get("/admin/payout/{payout_id}/complete", response_class=HTMLResponse)
async def admin_payout_complete(request: Request, payout_id: int, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Mark payout as paid."""
    payout = db.query(VenuePayout).filter(VenuePayout.id == payout_id).first()
    if payout:
        payout.status = "paid"
        payout.paid_at = datetime.utcnow()
        db.commit()
    return RedirectResponse(url="/admin/payouts", status_code=303)


# ─────────────────────────────────────────────────────────────
# Public TV showcase
# ─────────────────────────────────────────────────────────────

@router.get("/tv/{tv_code}", response_class=HTMLResponse)
async def public_tv_showcase(request: Request, tv_code: str, db: Session = Depends(get_db)):
    """
    Public TV showcase page (what users see after scanning QR).
    Совмещение digital и оффлайн - показывает рекламодателей на данном ТВ.
    Поддерживает доступ по коду (tv_code) или по ID.
    """
    tv = db.query(TV).filter(TV.code == tv_code).first()
    if not tv:
        try:
            tv = db.query(TV).filter(TV.id == int(tv_code)).first()
        except ValueError:
            pass
    
    if not tv:
        return HTMLResponse(content="<h1>ТВ не найден</h1>", status_code=404)
    
    if not tv.is_active:
        return HTMLResponse(content="<h1>ТВ неактивен</h1>", status_code=403)
    
    links = db.query(TVLink).filter(TVLink.tv_id == tv.id, TVLink.is_active == True).order_by(TVLink.position).all()
    
    # Формируем ссылки с отслеживанием кликов
    links_html = ""
    if links:
        for link in links:
            # URL для отслеживания кликов через API
            track_url = f"/api/public/stats"
            # Прямая ссылка с отслеживанием через JavaScript
            links_html += f'''
            <a href="{link.url}" 
               class="link-card" 
               target="_blank"
               data-link-id="{link.id}"
               data-tv-id="{tv.id}"
               onclick="trackClick(event, {link.id}, {tv.id})">
                <div class="link-title">{link.title}</div>
                <div class="link-desc">{link.description or ""}</div>
            </a>
            '''
    else:
        links_html = '<p class="empty">Ссылки скоро появятся</p>'
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{tv.name} — XK Media</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: system-ui, sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                min-height: 100vh;
                color: #edf2f4;
                padding: 2rem;
            }}
            .container {{ max-width: 480px; margin: 0 auto; }}
            h1 {{ font-size: 1.5rem; text-align: center; margin-bottom: 0.5rem; }}
            .venue {{ text-align: center; color: #8d99ae; margin-bottom: 2rem; }}
            .links {{ display: flex; flex-direction: column; gap: 1rem; }}
            .link-card {{
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 12px;
                padding: 1.25rem;
                text-decoration: none;
                color: inherit;
                transition: all 0.2s;
                display: block;
            }}
            .link-card:hover {{
                background: rgba(233, 69, 96, 0.1);
                border-color: #e94560;
                transform: translateY(-2px);
            }}
            .link-title {{ font-weight: 600; margin-bottom: 0.25rem; }}
            .link-desc {{ font-size: 0.875rem; color: #8d99ae; }}
            .empty {{ text-align: center; padding: 3rem; color: #8d99ae; }}
            .footer {{ text-align: center; margin-top: 2rem; font-size: 0.75rem; color: #8d99ae; }}
        </style>
        <script>
            // Отслеживание кликов для статистики (омниканальность)
            async function trackClick(event, linkId, tvId) {{
                try {{
                    // Отправляем статистику о клике
                    await fetch('/api/public/stats', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{
                            tv_id: tvId,
                            link_id: linkId,
                            event_type: 'click',
                            timestamp: new Date().toISOString(),
                            user_agent: navigator.userAgent
                        }})
                    }});
                }} catch (error) {{
                    console.error('Ошибка отслеживания:', error);
                }}
                // Продолжаем переход по ссылке
            }}
            
            // Отслеживание просмотра страницы
            window.addEventListener('load', function() {{
                fetch('/api/public/stats', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{
                        tv_id: {tv.id},
                        event_type: 'view',
                        timestamp: new Date().toISOString(),
                        user_agent: navigator.userAgent
                    }})
                }}).catch(err => console.error('Ошибка отслеживания просмотра:', err));
            }});
        </script>
    </head>
    <body>
        <div class="container">
            <h1>📺 {tv.name}</h1>
            <p class="venue">{tv.venue_name or tv.address or ''}</p>
            <div class="links">
                {links_html}
            </div>
            <p class="footer">Powered by XK Media</p>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)


# ─────────────────────────────────────────────────────────────
# Admin: Site Settings (Оферта)
# ─────────────────────────────────────────────────────────────

@router.get("/admin/settings", response_class=HTMLResponse)
async def admin_settings(request: Request, success: str = None, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Admin site settings page."""
    offer = db.query(SiteSettings).filter(SiteSettings.key == "offer").first()
    privacy = db.query(SiteSettings).filter(SiteSettings.key == "privacy").first()
    
    success_message = None
    error_message = None
    if success == "saved":
        success_message = "✓ Настройки сохранены"
    elif success == "password":
        success_message = "✓ Пароль изменён"
    elif success == "oauth_saved":
        success_message = "✓ OAuth настройки сохранены. Перезапустите приложение для применения изменений."
    elif success == "oauth_save_failed":
        error_message = "✗ Ошибка сохранения OAuth настроек"
    elif success == "wrong_password":
        error_message = "✗ Неверный текущий пароль"
    elif success == "password_mismatch":
        error_message = "✗ Пароли не совпадают"
    
    return templates.TemplateResponse("admin_settings.html", {
        "request": request, "user": user, "offer": offer, "privacy": privacy, 
        "success": success_message, "error": error_message, "settings": settings
    })


@router.post("/admin/settings/offer", response_class=HTMLResponse)
async def admin_settings_offer(request: Request, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """Save offer settings."""
    form = await request.form()
    
    offer = db.query(SiteSettings).filter(SiteSettings.key == "offer").first()
    if not offer:
        offer = SiteSettings(key="offer")
        db.add(offer)
    
    offer.title = form.get("title", "Оферта")
    offer.content = form.get("content", "")
    offer.version = form.get("version", "1.0")
    offer.is_active = "is_active" in form
    
    db.commit()
    return RedirectResponse(url="/admin/settings?success=saved", status_code=303)


def update_env_file(env_vars: dict) -> bool:
    """Update .env file with new variables."""
    try:
        # Find .env file (check current directory and parent directories)
        env_path = Path(".env")
        if not env_path.exists():
            # Try parent directory (for production deployment)
            env_path = Path("/var/www/xk-media-backend/.env")
            if not env_path.exists():
                env_path = Path(__file__).parent.parent.parent / ".env"
        
        if not env_path.exists():
            # Create new .env file
            env_path.touch()
        
        # Read existing content
        content = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
        
        # Update or add each variable
        for key, value in env_vars.items():
            if value is None or value == "":
                continue  # Skip empty values
            
            # Escape value if needed
            escaped_value = str(value).replace('"', '\\"')
            if ' ' in escaped_value or '#' in escaped_value or '$' in escaped_value:
                escaped_value = f'"{escaped_value}"'
            
            # Pattern to match existing variable
            pattern = rf'^{re.escape(key)}\s*=\s*.*$'
            
            if re.search(pattern, content, re.MULTILINE):
                # Update existing variable
                content = re.sub(pattern, f'{key}={escaped_value}', content, flags=re.MULTILINE)
            else:
                # Add new variable at the end
                if content and not content.endswith('\n'):
                    content += '\n'
                content += f'{key}={escaped_value}\n'
        
        # Write back to file
        env_path.write_text(content, encoding="utf-8")
        return True
    except Exception as e:
        print(f"Error updating .env file: {e}")
        return False


@router.post("/admin/settings/password", response_class=HTMLResponse)
async def admin_settings_password(
    request: Request,
    user: User = Depends(require_role_for_page(Role.ADMIN)),
    db: Session = Depends(get_db),
):
    """Change admin password."""
    form = await request.form()
    
    current = form.get("current_password", "")
    new_pass = form.get("new_password", "")
    confirm = form.get("confirm_password", "")
    
    if not verify_password(current, user.hashed_password):
        return RedirectResponse(url="/admin/settings?success=wrong_password", status_code=303)
    
    if new_pass != confirm:
        return RedirectResponse(url="/admin/settings?success=password_mismatch", status_code=303)
    
    user.hashed_password = get_password_hash(new_pass)
    db.commit()
    
    return RedirectResponse(url="/admin/settings?success=password", status_code=303)


@router.post("/admin/settings/oauth", response_class=HTMLResponse)
async def admin_settings_oauth(request: Request, user: User = Depends(require_role_for_page(Role.ADMIN))):
    """Save OAuth settings to .env file."""
    form = await request.form()
    
    env_updates = {}
    
    # Yandex OAuth
    if form.get("yandex_client_id"):
        env_updates["YANDEX_CLIENT_ID"] = form.get("yandex_client_id")
    if form.get("yandex_client_secret"):
        env_updates["YANDEX_CLIENT_SECRET"] = form.get("yandex_client_secret")
    
    # Base URL
    if form.get("base_url"):
        env_updates["BASE_URL"] = form.get("base_url")
    
    if env_updates:
        success = update_env_file(env_updates)
        if success:
            return RedirectResponse(url="/admin/settings?success=oauth_saved", status_code=303)
        else:
            return RedirectResponse(url="/admin/settings?error=oauth_save_failed", status_code=303)
    
    return RedirectResponse(url="/admin/settings?success=saved", status_code=303)


@router.get("/admin/users/offers", response_class=HTMLResponse)
async def admin_users_offers(request: Request, user: User = Depends(require_role_for_page(Role.ADMIN)), db: Session = Depends(get_db)):
    """View users who accepted offer."""
    users = db.query(User).filter(User.offer_accepted_at != None).order_by(User.offer_accepted_at.desc()).all()
    
    # Stats
    total_accepted = len(users)
    advertisers = sum(1 for u in users if u.role == Role.ADVERTISER)
    venues = sum(1 for u in users if u.role == Role.VENUE)
    
    return templates.TemplateResponse("admin_users_offers.html", {
        "request": request, "user": user, "users": users,
        "total_accepted": total_accepted, "advertisers": advertisers, "venues": venues
    })
