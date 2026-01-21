"""
YooKassa payment client - замена PayKeeper.
"""

import uuid
from typing import Any, Optional
from decimal import Decimal

try:
    from yookassa import Configuration, Payment
    YOOKASSA_AVAILABLE = True
except ImportError:
    YOOKASSA_AVAILABLE = False
    print("Warning: yookassa package not installed. Install with: pip install yookassa")

from app.settings import settings


def configure_yookassa():
    """Настроить YooKassa с API ключами."""
    if not YOOKASSA_AVAILABLE:
        raise RuntimeError("YooKassa SDK not installed")
    
    shop_id = settings.YOOKASSA_SHOP_ID
    secret_key = settings.YOOKASSA_SECRET_KEY
    
    if not secret_key:
        raise RuntimeError("YOOKASSA_SECRET_KEY not configured")
    
    if not shop_id:
        raise RuntimeError("YOOKASSA_SHOP_ID not configured. Please set it in .env file.")
    
    Configuration.configure(shop_id, secret_key)


def create_payment(
    *,
    amount: float | Decimal,
    order_id: str,
    description: str,
    return_url: str,
    client_email: Optional[str] = None,
    client_phone: Optional[str] = None,
) -> dict[str, Any]:
    """
    Создать платеж в YooKassa.
    
    Args:
        amount: Сумма платежа
        order_id: Уникальный ID заказа
        description: Описание платежа
        return_url: URL для возврата после оплаты
        client_email: Email клиента (опционально)
        client_phone: Телефон клиента (опционально)
    
    Returns:
        dict с payment_id и confirmation_url
    """
    if not YOOKASSA_AVAILABLE:
        raise RuntimeError("YooKassa SDK not installed")
    
    configure_yookassa()
    
    # Генерируем уникальный ключ идемпотентности
    idempotency_key = str(uuid.uuid4())
    
    # Формируем сумму (YooKassa требует строку с 2 знаками после запятой)
    amount_value = f"{float(amount):.2f}"
    
    # Базовые параметры платежа
    payment_data = {
        "amount": {
            "value": amount_value,
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": return_url
        },
        "capture": True,
        "description": description,
        "metadata": {
            "order_id": order_id
        }
    }
    
    # Добавляем данные клиента и чек (обязательно для YooKassa в РФ)
    # Для live режима чек обязателен, если сумма > 0
    receipt = {
        "items": [{
            "description": description[:128],  # Максимум 128 символов
            "quantity": "1",
            "amount": {
                "value": amount_value,
                "currency": "RUB"
            },
            "vat_code": 1  # НДС не облагается
        }]
    }
    
    # Добавляем данные клиента если есть
    if client_email or client_phone:
        receipt["customer"] = {}
        if client_email:
            receipt["customer"]["email"] = client_email
        if client_phone:
            receipt["customer"]["phone"] = client_phone
    
    payment_data["receipt"] = receipt
    
    try:
        # Создаем платеж
        payment = Payment.create(payment_data, idempotency_key)
        
        # Проверяем наличие confirmation_url
        if not payment.confirmation or not payment.confirmation.confirmation_url:
            raise RuntimeError("YooKassa did not return confirmation_url. Payment may be in wrong state.")
        
        return {
            "payment_id": payment.id,
            "confirmation_url": payment.confirmation.confirmation_url,
            "status": payment.status,
            "amount": {
                "value": payment.amount.value,
                "currency": payment.amount.currency
            }
        }
    except Exception as e:
        error_msg = str(e)
        print(f"YooKassa payment creation error: {error_msg}")
        print(f"Payment data: {payment_data}")
        # Пробрасываем более детальную ошибку
        if "shop_id" in error_msg.lower() or "shop" in error_msg.lower():
            raise RuntimeError(f"YooKassa configuration error (check shop_id): {error_msg}")
        elif "receipt" in error_msg.lower():
            raise RuntimeError(f"YooKassa receipt error: {error_msg}")
        else:
            raise RuntimeError(f"YooKassa payment creation error: {error_msg}")


def get_payment_status(payment_id: str) -> dict[str, Any]:
    """
    Получить статус платежа из YooKassa.
    
    Args:
        payment_id: ID платежа в YooKassa
    
    Returns:
        dict с информацией о платеже
    """
    if not YOOKASSA_AVAILABLE:
        raise RuntimeError("YooKassa SDK not installed")
    
    configure_yookassa()
    
    try:
        payment = Payment.find_one(payment_id)
        return {
            "payment_id": payment.id,
            "status": payment.status,
            "paid": payment.paid,
            "amount": {
                "value": payment.amount.value,
                "currency": payment.amount.currency
            },
            "created_at": payment.created_at.isoformat() if payment.created_at else None,
            "captured_at": payment.captured_at.isoformat() if payment.captured_at else None,
            "metadata": payment.metadata or {}
        }
    except Exception as e:
        raise RuntimeError(f"YooKassa payment status error: {str(e)}")


def cancel_payment(payment_id: str) -> dict[str, Any]:
    """
    Отменить платеж в YooKassa.
    
    Args:
        payment_id: ID платежа в YooKassa
    
    Returns:
        dict с информацией об отмененном платеже
    """
    if not YOOKASSA_AVAILABLE:
        raise RuntimeError("YooKassa SDK not installed")
    
    configure_yookassa()
    
    idempotency_key = str(uuid.uuid4())
    
    try:
        payment = Payment.cancel(payment_id, idempotency_key)
        return {
            "payment_id": payment.id,
            "status": payment.status,
            "cancelled_at": payment.cancelled_at.isoformat() if payment.cancelled_at else None
        }
    except Exception as e:
        raise RuntimeError(f"YooKassa payment cancellation error: {str(e)}")
