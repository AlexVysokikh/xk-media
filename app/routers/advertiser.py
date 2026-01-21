"""
Advertiser routes - payments and profile management.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import Payment, PaymentStatus, User
from app.schemas import CreateAdvertiserPaymentIn, PaymentOut
from app.payments.yookassa_client import create_payment
from app.settings import settings

router = APIRouter(prefix="/api/advertiser", tags=["Advertiser API"])


@router.post("/payments/create", response_model=PaymentOut)
def create_payment_for_advertiser(
    payload: CreateAdvertiserPaymentIn,
    db: Session = Depends(get_db),
    user_id: int = 1,  # TODO: replace with real auth
):
    """Create a new payment for advertiser."""
    order_id = f"adv-{user_id}-{uuid.uuid4().hex[:8]}"
    
    payment = Payment(
        user_id=user_id,
        amount=float(payload.amount),
        currency="RUB",
        description=payload.purpose,
        order_id=order_id,
        status=PaymentStatus.WAITING,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    # Получаем пользователя для email
    user = db.query(User).filter(User.id == user_id).first()
    user_email = user.email if user else None
    
    try:
        # Создаем платеж в YooKassa
        return_url = settings.YOOKASSA_RETURN_URL
        yk_result = create_payment(
            amount=float(payload.amount),
            order_id=str(payment.id),
            description=payload.purpose,
            return_url=return_url,
            client_email=user_email,
        )
        
        payment.yk_payment_id = yk_result["payment_id"]
        payment.pay_url = yk_result["confirmation_url"]
        db.commit()
        db.refresh(payment)
    except Exception as e:
        print(f"YooKassa error: {e}")
        # В случае ошибки платеж остается в статусе WAITING

    return PaymentOut(
        id=payment.id,
        purpose=payment.description,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status,
        pkInvoiceId=payment.yk_payment_id,  # Используем yk_payment_id для совместимости со схемой
        payUrl=payment.pay_url,
        pkPaymentId=payment.yk_payment_id,
    )


@router.get("/payments", response_model=list[PaymentOut])
def list_advertiser_payments(
    db: Session = Depends(get_db),
    user_id: int = 1,
):
    """List all payments for current advertiser."""
    payments = db.query(Payment).filter(Payment.user_id == user_id).order_by(Payment.created_at.desc()).all()
    
    return [
        PaymentOut(
            id=p.id,
            purpose=p.description,
            amount=p.amount,
            currency=p.currency,
            status=p.status,
            pkInvoiceId=p.yk_payment_id or p.pk_invoice_id,  # Поддержка обоих форматов
            payUrl=p.pay_url,
            pkPaymentId=p.yk_payment_id or p.pk_payment_id,
        )
        for p in payments
    ]


@router.get("/payments/{payment_id}", response_model=PaymentOut)
def get_advertiser_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    user_id: int = 1,
):
    """Get specific payment details."""
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.user_id == user_id
    ).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return PaymentOut(
        id=payment.id,
        purpose=payment.description,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status,
        pkInvoiceId=payment.yk_payment_id or payment.pk_invoice_id,
        payUrl=payment.pay_url,
        pkPaymentId=payment.yk_payment_id or payment.pk_payment_id,
    )
