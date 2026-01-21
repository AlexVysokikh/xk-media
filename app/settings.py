from pydantic_settings import BaseSettings
from pydantic import field_validator
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
    # CORS (comma-separated string in .env)
    # ─────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    # ─────────────────────────────────────────────────────────────
    # YooKassa (замена PayKeeper)
    # ─────────────────────────────────────────────────────────────
    YOOKASSA_SHOP_ID: str = "1000001"  # ID магазина (для теста можно оставить дефолтный)
    YOOKASSA_SECRET_KEY: str = "test_eN10mBer9WHYOB8vJrixABlU2WZZdKOl6wjbvBqbqAI"
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
    
    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
