from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ─────────────────────────────────────────────────────────────
    # Application
    # ─────────────────────────────────────────────────────────────
    APP_NAME: str = "XK Media API"
    DEBUG: bool = True
    
    # ─────────────────────────────────────────────────────────────
    # Database
    # ─────────────────────────────────────────────────────────────
    # SQLite for dev, PostgreSQL for production
    DATABASE_URL: str = "sqlite:///./xk_media.db"
    
    # ─────────────────────────────────────────────────────────────
    # Security
    # ─────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    ALGORITHM: str = "HS256"
    
    # ─────────────────────────────────────────────────────────────
    # CORS
    # ─────────────────────────────────────────────────────────────
    # В pydantic-settings v2 любые "complex" типы (list/dict) из env/.env
    # по умолчанию парсятся как JSON. Поэтому для удобства держим строку
    # вида "a,b,c" и уже в коде конвертим в list[str].
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    @property
    def cors_origins_list(self) -> list[str]:
        v = self.CORS_ORIGINS
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        # на всякий случай
        try:
            return list(v)  # type: ignore[arg-type]
        except Exception:
            return []
    
    # ─────────────────────────────────────────────────────────────
    # YooKassa (замена PayKeeper)
    # ─────────────────────────────────────────────────────────────
    YOOKASSA_SHOP_ID: str = "1253109"  # ID магазина xk-media
    YOOKASSA_SECRET_KEY: str = "live_dZfwwGWY8uocS8YHrJIbZhJdGGlxXxP5FVBswXgovzY"
    YOOKASSA_WEBHOOK_PATH: str = "/payments/yookassa/webhook"
    YOOKASSA_RETURN_URL: str = "https://xk-media.ru/advertiser/payments"
    
    # ─────────────────────────────────────────────────────────────
    # PayKeeper (deprecated - оставлено для обратной совместимости)
    # ─────────────────────────────────────────────────────────────
    PAYKEEPER_BASE_URL: str = "https://demo.paykeeper.ru"
    PAYKEEPER_USER: str = "demo"
    PAYKEEPER_PASSWORD: str = "demo"
    PAYKEEPER_SECRET_WORD: str = "your_secret_word_for_post_notifications"
    PAYKEEPER_NOTIFY_PATH: str = "/payments/paykeeper/notify"
    PAYKEEPER_RETURN_URL: str = "https://xk-media.ru/advertiser/payments"
    
    # ─────────────────────────────────────────────────────────────
    # Admin (auto-created on first run)
    # ─────────────────────────────────────────────────────────────
    ADMIN_EMAIL: str = "admin@xk-media.ru"
    ADMIN_PASSWORD: str = "admin123"
    
    # ─────────────────────────────────────────────────────────────
    # OAuth2 Providers
    # ─────────────────────────────────────────────────────────────
    # Base URL for callbacks (change in production)
    BASE_URL: str = "http://localhost:8080"
    
    # Yandex OAuth
    YANDEX_CLIENT_ID: str = ""
    YANDEX_CLIENT_SECRET: str = ""
    
    # VK OAuth
    VK_CLIENT_ID: str = ""
    VK_CLIENT_SECRET: str = ""
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    
    # ─────────────────────────────────────────────────────────────
    # Email (SMTP) для уведомлений
    # ─────────────────────────────────────────────────────────────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_USE_TLS: bool = True
    # Куда приходят заявки с лендинга и из ЛК (создать рекламную кампанию)
    NOTIFY_EMAIL: str = "av.vysokikh@gmail.com"
    
    # ─────────────────────────────────────────────────────────────
    # Telegram для уведомлений
    # ─────────────────────────────────────────────────────────────
    TELEGRAM_BOT_TOKEN: str = ""

    # Поддержка нескольких получателей.
    # Можно задать один chat id через TELEGRAM_CHAT_ID (старое имя),
    # или несколько через TELEGRAM_CHAT_IDS (через запятую).
    TELEGRAM_CHAT_ID: str = ""
    TELEGRAM_CHAT_IDS: str = ""

    # Необязательный allow-list по username (через запятую, без @),
    # используется в скрипте настройки.
    TELEGRAM_ALLOWED_USERNAMES: str = ""

    @property
    def telegram_chat_ids_list(self) -> list[str]:
        raw = (self.TELEGRAM_CHAT_IDS or self.TELEGRAM_CHAT_ID or "").strip()
        if not raw:
            return []
        return [s.strip() for s in raw.split(",") if s.strip()]
    
    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
