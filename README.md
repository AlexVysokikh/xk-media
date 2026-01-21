# XK Media Backend

Backend для медиа-платформы с поддержкой трех типов пользователей:
- **Админ** - управление системой, пользователями, контентом
- **Рекламодатели** - создание и управление рекламными кампаниями
- **Площадки показа** - управление экранами и показ рекламы

## Возможности

- Система аутентификации и авторизации с ролями (JWT, OAuth2)
- Три отдельных кабинета с разными правами доступа
- Внешний API для QR-кодов и ТВ-экранов (омниканальность)
- Управление рекламными кампаниями
- Управление площадками и экранами
- Интеграция с YooKassa для платежей
- OAuth регистрация через Yandex, VK
- Docker и Docker Compose для развертывания
- CI/CD через GitHub Actions

## Технологии

- **FastAPI** - веб-фреймворк
- **SQLAlchemy** - ORM
- **PostgreSQL** - база данных
- **Alembic** - миграции БД
- **YooKassa** - платежная система
- **Docker** - контейнеризация

## Установка

```bash
# Установка зависимостей
pip install -r requirements.txt
```

## Настройка

1. Скопируйте `.env.example` в `.env` и заполните необходимые переменные:
   ```bash
   cp .env.example .env
   ```

2. Настройте базу данных PostgreSQL в `.env`:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/xk_media
   ```

3. Настройте YooKassa (см. `YOOKASSA_SETUP.md`):
   ```
   YOOKASSA_SHOP_ID=your_shop_id
   YOOKASSA_SECRET_KEY=your_secret_key
   ```

4. Настройте OAuth провайдеры (см. `QUICK_OAUTH_SETUP.md`):
   ```
   YANDEX_CLIENT_ID=...
   YANDEX_CLIENT_SECRET=...
   VK_CLIENT_ID=...
   VK_CLIENT_SECRET=...
   ```

## Запуск

### Локальная разработка

```bash
# Запуск сервера
python run_server.py

# Или через uvicorn напрямую
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### Docker

```bash
# Запуск через Docker Compose
docker-compose up -d
```

### Миграции БД

```bash
# Создание миграций
alembic revision --autogenerate -m "description"

# Применение миграций
alembic upgrade head
```

## API Endpoints

### Аутентификация
- `POST /api/auth/register` - Регистрация
- `POST /api/auth/login` - Вход
- `GET /api/auth/me` - Текущий пользователь

### Админ
- `GET /api/admin/users` - Список пользователей
- `GET /api/admin/campaigns` - Все кампании
- `GET /api/admin/platforms` - Все площадки

### Рекламодатели
- `GET /api/advertiser/campaigns` - Мои кампании
- `POST /api/advertiser/campaigns` - Создать кампанию
- `PUT /api/advertiser/campaigns/:id` - Обновить кампанию

### Площадки
- `GET /api/platform/screens` - Мои экраны
- `POST /api/platform/screens` - Добавить экран
- `GET /api/platform/statistics` - Статистика показов

### Публичный API (QR/ТВ)
- `GET /api/public/screen/:screenId` - Получить контент для экрана
- `GET /api/public/qr/:qrCode` - Получить контент по QR-коду
