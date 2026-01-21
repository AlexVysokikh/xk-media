"""
Payment webhooks and notifications from YooKassa (и PayKeeper для обратной совместимости).
"""

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Request, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse, JSONResponse
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import Payment, PaymentStatus, User
from app.settings import settings

router = APIRouter(prefix="/payments", tags=["Payments"])


# ─────────────────────────────────────────────────────────────
# YooKassa Webhook
# ─────────────────────────────────────────────────────────────

@router.post("/yookassa/webhook", response_class=JSONResponse)
async def yookassa_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    YooKassa webhook endpoint для уведомлений о платежах.
    
    YooKassa отправляет POST запросы с JSON телом при изменении статуса платежа.
    """
    try:
        data = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    
    # Проверяем тип события
    event = data.get("event")
    if event != "payment.succeeded":
        # Игнорируем другие события (payment.canceled, payment.waiting_for_capture и т.д.)
        return JSONResponse({"status": "ok", "message": "Event ignored"})
    
    # Получаем объект платежа
    payment_object = data.get("object", {})
    payment_id = payment_object.get("id")
    status = payment_object.get("status")
    metadata = payment_object.get("metadata", {})
    order_id = metadata.get("order_id")
    
    if not payment_id or not order_id:
        raise HTTPException(status_code=400, detail="Missing payment_id or order_id")
    
    # Ищем платеж по order_id (это наш внутренний ID платежа)
    try:
        payment_db_id = int(order_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid order_id format")
    
    payment = db.query(Payment).filter(Payment.id == payment_db_id).first()
    
    if not payment:
        # Платеж не найден - возможно это тестовый запрос или старый платеж
        return JSONResponse({"status": "ok", "message": "Payment not found"})
    
    # Обновляем статус платежа
    if status == "succeeded" and payment.status != PaymentStatus.SUCCEEDED:
        payment.status = PaymentStatus.SUCCEEDED
        payment.yk_payment_id = payment_id
        payment.paid_at = datetime.now(timezone.utc)
        payment.raw_notify = json.dumps(data)
        
        # Пополняем баланс пользователя
        user = db.query(User).filter(User.id == payment.user_id).first()
        if user:
            current_balance = Decimal(str(user.balance or 0))
            payment_amount = Decimal(str(payment.amount))
            user.balance = current_balance + payment_amount
            
            # Отправляем уведомление об оплате (в фоне)
            try:
                from app.services.notification_service import NotificationService
                background_tasks.add_task(
                    NotificationService.notify_payment_success,
                    user_email=user.email,
                    user_name=user.company_name or f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email,
                    amount=float(payment_amount),
                    payment_id=payment.id,
                    purpose=payment.description or "Пополнение баланса"
                )
            except Exception as e:
                print(f"Error scheduling payment notification: {e}")
        
        db.commit()
    
    return JSONResponse({"status": "ok"})


# ─────────────────────────────────────────────────────────────
# PayKeeper Webhook (deprecated, для обратной совместимости)
# ─────────────────────────────────────────────────────────────

def md5_hex(s: str) -> str:
    """Calculate MD5 hash and return hex string."""
    return hashlib.md5(s.encode("utf-8")).hexdigest()


@router.post("/paykeeper/notify", response_class=PlainTextResponse)
async def paykeeper_notify(request: Request, db: Session = Depends(get_db)):
    """
    PayKeeper POST notification endpoint (deprecated - используйте YooKassa).
    """
    form = await request.form()

    pk_payment_id = (form.get("id") or "").strip()
    summ = (form.get("sum") or "").strip()
    clientid = (form.get("clientid") or "").strip()
    orderid = (form.get("orderid") or "").strip()
    key = (form.get("key") or "").strip()
    ps_id = (form.get("ps_id") or "").strip()

    if not pk_payment_id or not summ or not key:
        return PlainTextResponse("Error! Missing or invalid parameters!")

    try:
        summ = f"{float(summ):.2f}"
    except ValueError:
        return PlainTextResponse("Error! Invalid sum format!")

    expected_key = md5_hex(f"{pk_payment_id}{summ}{clientid}{orderid}{settings.PAYKEEPER_SECRET_WORD}")
    if key != expected_key:
        return PlainTextResponse("Error! Hash mismatch!")

    try:
        payment_id = int(orderid)
    except ValueError:
        return PlainTextResponse("Error! Invalid orderid!")

    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if payment:
        payment.status = PaymentStatus.SUCCEEDED
        payment.pk_payment_id = pk_payment_id
        payment.pk_ps_id = ps_id or None
        payment.paid_at = datetime.now(timezone.utc)
        payment.raw_notify = json.dumps({k: form.get(k) for k in form.keys()})
        db.commit()

    response_hash = md5_hex(f"{pk_payment_id}{settings.PAYKEEPER_SECRET_WORD}")
    return PlainTextResponse(f"OK {response_hash}")
