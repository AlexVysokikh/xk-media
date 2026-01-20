# Настройка YooKassa (замена PayKeeper)

## Что изменено

✅ **PayKeeper заменен на YooKassa** во всех частях системы:
- Создан новый клиент `app/payments/yookassa_client.py`
- Обновлен webhook endpoint `/payments/yookassa/webhook`
- Обновлены роутеры для создания платежей
- Обновлена модель Payment (добавлено поле `yk_payment_id`)
- Сохранена обратная совместимость с PayKeeper

## Установка зависимостей

```bash
pip install yookassa==3.0.0
```

Или установите все зависимости из `requirements.txt`:
```bash
pip install -r requirements.txt
```

## Настройка

### 1. Переменные окружения

Добавьте в `.env` файл:

```env
# YooKassa настройки
YOOKASSA_SHOP_ID=1000001
YOOKASSA_SECRET_KEY=test_eN10mBer9WHYOB8vJrixABlU2WZZdKOl6wjbvBqbqAI
YOOKASSA_RETURN_URL=http://localhost:8080/advertiser/payments
YOOKASSA_WEBHOOK_PATH=/payments/yookassa/webhook
```

**Для продакшена:**
- Замените `test_` ключ на реальный секретный ключ из личного кабинета ЮКассы
- Укажите реальный `YOOKASSA_SHOP_ID` (ID магазина)
- Укажите реальный `YOOKASSA_RETURN_URL` (URL вашего сайта)

### 2. Настройка Webhook в личном кабинете ЮКассы

1. Войдите в [личный кабинет ЮКассы](https://yookassa.ru/)
2. Перейдите в раздел "Настройки" → "Уведомления"
3. Добавьте URL для webhook: `https://ваш-домен.ru/payments/yookassa/webhook`
4. Выберите события: `payment.succeeded` (обязательно)

**Для тестирования локально:**
- Используйте [ngrok](https://ngrok.com/) или аналогичный сервис для туннелирования
- Настройте webhook на `https://ваш-ngrok-домен.ngrok.io/payments/yookassa/webhook`

## API Endpoints

### Создание платежа

**POST** `/api/advertiser/payments/create`

Создает платеж и возвращает URL для оплаты.

**Пример запроса:**
```json
{
  "amount": 1000.00,
  "purpose": "Пополнение баланса"
}
```

**Пример ответа:**
```json
{
  "id": 1,
  "purpose": "Пополнение баланса",
  "amount": 1000.00,
  "currency": "RUB",
  "status": "waiting",
  "pkInvoiceId": "2c5d8b1a-0001-5000-8000-1a2b3c4d5e6f",
  "payUrl": "https://yoomoney.ru/checkout/payments/v2/contract?orderId=...",
  "pkPaymentId": "2c5d8b1a-0001-5000-8000-1a2b3c4d5e6f"
}
```

### Webhook (автоматический)

**POST** `/payments/yookassa/webhook`

YooKassa автоматически отправляет уведомления при изменении статуса платежа.

**События:**
- `payment.succeeded` - платеж успешно проведен
- `payment.canceled` - платеж отменен
- `payment.waiting_for_capture` - ожидает подтверждения

При успешном платеже (`payment.succeeded`):
- Статус платежа обновляется на `succeeded`
- Баланс пользователя автоматически пополняется
- Записывается время оплаты (`paid_at`)

## Миграция базы данных

Если у вас уже есть платежи с PayKeeper, нужно добавить новое поле в таблицу `payments`:

```sql
ALTER TABLE payments ADD COLUMN yk_payment_id VARCHAR(100);
CREATE INDEX IF NOT EXISTS ix_payments_yk_payment_id ON payments(yk_payment_id);
```

Или используйте Alembic миграцию:

```python
# alembic/versions/xxxx_add_yookassa_fields.py
def upgrade():
    op.add_column('payments', sa.Column('yk_payment_id', sa.String(100), nullable=True))
    op.create_index(op.f('ix_payments_yk_payment_id'), 'payments', ['yk_payment_id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_payments_yk_payment_id'), table_name='payments')
    op.drop_column('payments', 'yk_payment_id')
```

## Тестирование

### Тестовый режим

Текущий ключ `test_eN10mBer9WHYOB8vJrixABlU2WZZdKOl6wjbvBqbqAI` - это тестовый ключ.

**Тестовые карты для оплаты:**
- Успешная оплата: `5555 5555 5555 4444` (любая дата, любой CVC)
- Отклоненная оплата: `5555 5555 5555 4477` (любая дата, любой CVC)

### Проверка работы

1. Создайте платеж через API или веб-интерфейс
2. Перейдите по ссылке `payUrl`
3. Используйте тестовую карту для оплаты
4. Проверьте, что баланс пользователя пополнился
5. Проверьте статус платежа в базе данных

## Отличия от PayKeeper

| PayKeeper | YooKassa |
|-----------|----------|
| `pk_invoice_id` | `yk_payment_id` |
| `pk_payment_id` | `yk_payment_id` |
| MD5 hash для проверки | JSON webhook с подписью |
| Form-data webhook | JSON webhook |
| `/payments/paykeeper/notify` | `/payments/yookassa/webhook` |

## Обратная совместимость

Старые платежи с PayKeeper продолжают работать:
- Поля `pk_invoice_id`, `pk_payment_id` сохранены в модели
- Webhook PayKeeper `/payments/paykeeper/notify` продолжает работать
- В API ответах используются оба формата для совместимости

## Проблемы и решения

### Ошибка "YooKassa SDK not installed"

```bash
pip install yookassa==3.0.0
```

### Ошибка "Invalid shop_id or secret_key"

Проверьте настройки в `.env`:
- `YOOKASSA_SHOP_ID` должен быть числом (строка)
- `YOOKASSA_SECRET_KEY` должен начинаться с `test_` для теста или быть реальным ключом

### Webhook не приходит

1. Проверьте, что URL доступен из интернета (используйте ngrok для локальной разработки)
2. Проверьте настройки webhook в личном кабинете ЮКассы
3. Проверьте логи сервера на наличие ошибок

### Баланс не пополняется после оплаты

1. Проверьте логи webhook - приходит ли событие `payment.succeeded`
2. Проверьте, что `order_id` в метаданных платежа соответствует ID платежа в БД
3. Проверьте, что пользователь существует и активен

## Дополнительная информация

- [Документация YooKassa API](https://yookassa.ru/developers/api)
- [Python SDK YooKassa](https://github.com/yoomoney/yookassa-sdk-python)
- [Тестирование платежей](https://yookassa.ru/developers/payment-acceptance/testing-and-going-live/testing)
