"""
SQLAlchemy models - compatible with both SQLite and PostgreSQL.
"""

from datetime import datetime, date

from sqlalchemy import Column, Integer, String, DateTime, Date, Numeric, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base


# ─────────────────────────────────────────────────────────────
# Enums (as string constants for SQLite compatibility)
# ─────────────────────────────────────────────────────────────

class Role:
    ADMIN = "admin"
    ADVERTISER = "advertiser"
    VENUE = "venue"


class PaymentStatus:
    PENDING = "pending"
    WAITING = "waiting"
    SUCCEEDED = "succeeded"
    CANCELED = "canceled"
    FAILED = "failed"


class VenueCategory:
    """Категории заведений"""
    CAFE = "cafe"                    # Кофейня
    RESTAURANT = "restaurant"        # Ресторан
    BAR = "bar"                      # Бар
    SHOPPING_CENTER = "shopping"     # ТЦ
    BUSINESS_CENTER = "business"     # БЦ
    CLINIC = "clinic"                # Клиника
    GYM = "gym"                      # Фитнес
    HOTEL = "hotel"                  # Отель
    BEAUTY = "beauty"                # Салон красоты
    AUTO = "auto"                    # Автосервис
    COWORKING = "coworking"          # Коворкинг
    OTHER = "other"                  # Другое
    
    CHOICES = {
        CAFE: "Кофейня",
        RESTAURANT: "Ресторан",
        BAR: "Бар",
        SHOPPING_CENTER: "Торговый центр",
        BUSINESS_CENTER: "Бизнес-центр",
        CLINIC: "Клиника",
        GYM: "Фитнес-клуб",
        HOTEL: "Отель",
        BEAUTY: "Салон красоты",
        AUTO: "Автосервис",
        COWORKING: "Коворкинг",
        OTHER: "Другое",
    }


class EquipmentType:
    """Тип ТВ оборудования"""
    AGGREGATOR = "aggregator"        # ТВ агрегатора (60% владельцу)
    VENUE = "venue"                  # ТВ заведения (70% владельцу)
    
    CHOICES = {
        AGGREGATOR: "ТВ агрегатора XK Media",
        VENUE: "Собственное оборудование",
    }
    
    REVENUE_SHARE = {
        AGGREGATOR: 60.0,            # 60% владельцу
        VENUE: 70.0,                 # 70% владельцу
    }


class TargetAudience:
    """Целевая аудитория"""
    BUSINESS = "business"      # Бизнес-аудитория
    YOUTH = "youth"            # Молодёжь 18-25
    FAMILY = "family"          # Семейная
    PREMIUM = "premium"        # Премиум
    MASS = "mass"              # Массовая
    
    CHOICES = {
        BUSINESS: "Бизнес-аудитория",
        YOUTH: "Молодёжь 18-25",
        FAMILY: "Семейная",
        PREMIUM: "Премиум",
        MASS: "Массовая",
    }


# ─────────────────────────────────────────────────────────────
# TV model (расширенная)
# ─────────────────────────────────────────────────────────────

class TV(Base):
    """TV screen / digital display at a venue."""
    __tablename__ = "tvs"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)  # Unique code for QR
    name = Column(String(200), nullable=False)  # Название ТВ
    
    # ─── Информация о месте ───
    venue_name = Column(String(200), nullable=True)       # Название заведения (Кофейня "Рассвет")
    category = Column(String(50), default=VenueCategory.OTHER)  # Категория заведения
    target_audience = Column(String(50), default=TargetAudience.MASS)  # Целевая аудитория
    
    # ─── Адрес ───
    address = Column(String(500), nullable=True)          # Полный адрес
    city = Column(String(100), nullable=True)             # Город
    
    # ─── Юр. лицо площадки ───
    legal_name = Column(String(300), nullable=True)       # Юр. название (ООО "Рассвет")
    inn = Column(String(12), nullable=True)               # ИНН
    kpp = Column(String(9), nullable=True)                # КПП
    bank_name = Column(String(200), nullable=True)        # Название банка
    bank_bik = Column(String(9), nullable=True)           # БИК банка
    bank_account = Column(String(20), nullable=True)      # Расчетный счет
    contact_person = Column(String(200), nullable=True)   # Контактное лицо
    contact_phone = Column(String(20), nullable=True)     # Телефон
    contact_email = Column(String(255), nullable=True)    # Email
    
    # ─── Описание и характеристики ───
    description = Column(Text, nullable=True)             # Описание ТВ/места
    photo_url = Column(String(500), nullable=True)        # Фото заведения
    clients_per_day = Column(Integer, default=0)          # Среднее кол-во клиентов в день
    avg_check = Column(Numeric(10, 2), default=0)         # Средний чек
    working_hours = Column(String(100), nullable=True)    # Часы работы (напр. "09:00-22:00")
    
    # ─── Владелец (площадка) ───
    venue_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # ─── Тип оборудования и финансы ───
    equipment_type = Column(String(20), default=EquipmentType.AGGREGATOR)  # Тип оборудования
    revenue_share = Column(Numeric(5, 2), default=60.00)  # % выплаты площадке (60% или 70%)
    
    # ─── Статус ───
    is_active = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=False)          # Одобрен ли модерацией
    
    # ─── Timestamps ───
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ─── Relationships ───
    links = relationship("TVLink", back_populates="tv", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="tv", cascade="all, delete-orphan")
    venue_owner = relationship("User", back_populates="owned_tvs", foreign_keys=[venue_id])
    documents = relationship("VenueDocument", back_populates="tv", cascade="all, delete-orphan")


# ─────────────────────────────────────────────────────────────
# TV Link model (advertiser links on a TV)
# ─────────────────────────────────────────────────────────────

class TVLink(Base):
    """Advertiser link displayed on a TV screen."""
    __tablename__ = "tv_links"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # TV reference
    tv_id = Column(Integer, ForeignKey("tvs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Advertiser reference
    advertiser_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    advertiser_name = Column(String(200), nullable=True)
    
    # Link info
    title = Column(String(200), nullable=False)
    url = Column(String(1000), nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)        # Картинка для рекламы
    
    # Stats (будет заполняться из API плеера)
    clicks = Column(Integer, default=0)                   # Клики по ссылке
    impressions = Column(Integer, default=0)              # Показы на экране
    
    # Order
    position = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tv = relationship("TV", back_populates="links")
    advertiser = relationship("User", back_populates="tv_links")


# ─────────────────────────────────────────────────────────────
# User model (расширенная)
# ─────────────────────────────────────────────────────────────

class User(Base):
    """User model with role-based access."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # ─── Профиль ───
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # ─── Роль: admin, advertiser, venue ───
    role = Column(String(20), default=Role.ADVERTISER, nullable=False, index=True)
    
    # ─── Данные компании (для рекламодателей и площадок) ───
    company_name = Column(String(300), nullable=True)     # Название компании
    legal_name = Column(String(300), nullable=True)       # Юр. название
    inn = Column(String(12), nullable=True)               # ИНН
    kpp = Column(String(9), nullable=True)                # КПП
    legal_address = Column(String(500), nullable=True)    # Юр. адрес
    website = Column(String(500), nullable=True)          # Сайт компании
    logo_url = Column(String(500), nullable=True)         # URL логотипа
    description = Column(Text, nullable=True)             # Описание компании
    
    # ─── Баланс (для рекламодателей) ───
    balance = Column(Numeric(12, 2), default=0.00)        # Текущий баланс
    
    # ─── Статус ───
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)          # Верифицирован ли
    
    # ─── Согласие на оферту ───
    offer_accepted_at = Column(DateTime, nullable=True)   # Когда принял оферту
    offer_version = Column(String(50), nullable=True)     # Версия оферты
    
    # ─── Сброс пароля ───
    password_reset_token = Column(String(100), nullable=True, index=True)
    password_reset_expires = Column(DateTime, nullable=True)
    
    # ─── OAuth провайдеры ───
    oauth_provider = Column(String(20), nullable=True, index=True)  # yandex
    oauth_provider_id = Column(String(100), nullable=True, index=True)  # ID пользователя в провайдере
    oauth_email = Column(String(255), nullable=True)  # Email из OAuth (может отличаться от основного)
    
    # ─── Timestamps ───
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # ─── Relationships ───
    owned_tvs = relationship("TV", back_populates="venue_owner", foreign_keys="TV.venue_id")
    subscriptions = relationship("Subscription", back_populates="advertiser")
    payments = relationship("Payment", back_populates="user")
    tv_links = relationship("TVLink", back_populates="advertiser")


# ─────────────────────────────────────────────────────────────
# Subscription model (подписка рекламодателя на ТВ)
# ─────────────────────────────────────────────────────────────

class Subscription(Base):
    """Подписка рекламодателя на размещение на ТВ."""
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # ─── Связи ───
    advertiser_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tv_id = Column(Integer, ForeignKey("tvs.id"), nullable=False, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True, index=True)
    
    # ─── Период размещения ───
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # ─── Финансы ───
    price = Column(Numeric(12, 2), nullable=False)        # Стоимость размещения
    venue_payout = Column(Numeric(12, 2), default=0.00)   # Выплата площадке
    venue_payout_status = Column(String(20), default="pending")  # pending, paid
    
    # ─── Статус ───
    is_active = Column(Boolean, default=True)
    
    # ─── Timestamps ───
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # ─── Relationships ───
    advertiser = relationship("User", back_populates="subscriptions")
    tv = relationship("TV", back_populates="subscriptions")
    payment = relationship("Payment", back_populates="subscription")


# ─────────────────────────────────────────────────────────────
# Payment model (расширенная)
# ─────────────────────────────────────────────────────────────

class Payment(Base):
    """Платёж от рекламодателя."""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # ─── Связь с пользователем ───
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    
    # ─── Сумма ───
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="RUB", nullable=False)
    
    # ─── Тип платежа ───
    payment_type = Column(String(50), default="balance")  # balance, subscription
    
    # ─── Описание ───
    description = Column(String(500), nullable=True)
    order_id = Column(String(100), unique=True, index=True, nullable=False)
    
    # ─── Статус ───
    status = Column(String(20), default=PaymentStatus.PENDING, nullable=False, index=True)
    
    # ─── YooKassa fields ───
    yk_payment_id = Column(String(100), index=True, nullable=True)  # ID платежа в YooKassa
    pay_url = Column(String(500), nullable=True)  # URL для оплаты
    
    # ─── PayKeeper fields (deprecated, для обратной совместимости) ───
    pk_invoice_id = Column(String(100), index=True, nullable=True)
    pk_payment_id = Column(String(100), index=True, nullable=True)
    pk_ps_id = Column(String(100), nullable=True)
    raw_notify = Column(Text, nullable=True)
    
    # ─── Timestamps ───
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    paid_at = Column(DateTime, nullable=True)
    
    # ─── Relationships ───
    user = relationship("User", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payment", uselist=False)


# ─────────────────────────────────────────────────────────────
# VenuePayout model (выплаты площадкам)
# ─────────────────────────────────────────────────────────────

class VenuePayout(Base):
    """Выплата площадке за размещение рекламы."""
    __tablename__ = "venue_payouts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # ─── Связи ───
    venue_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # Площадка
    tv_id = Column(Integer, ForeignKey("tvs.id"), nullable=True, index=True)
    
    # ─── Период ───
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    # ─── Финансы ───
    amount = Column(Numeric(12, 2), nullable=False)       # Сумма выплаты
    status = Column(String(20), default="pending")        # pending, processing, paid
    
    # ─── Реквизиты ───
    payment_details = Column(Text, nullable=True)         # Реквизиты для выплаты
    
    # ─── Timestamps ───
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)


# ─────────────────────────────────────────────────────────────
# TVStats model (статистика показов по дням)
# ─────────────────────────────────────────────────────────────

class TVStats(Base):
    """Статистика показов рекламы на ТВ по дням (заполняется из API плеера)."""
    __tablename__ = "tv_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # ─── Связи ───
    tv_id = Column(Integer, ForeignKey("tvs.id", ondelete="CASCADE"), nullable=False, index=True)
    tv_link_id = Column(Integer, ForeignKey("tv_links.id", ondelete="CASCADE"), nullable=True, index=True)
    advertiser_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # ─── Дата ───
    stat_date = Column(Date, nullable=False, index=True)
    
    # ─── Метрики (заполняются из API плеера) ───
    impressions = Column(Integer, default=0)              # Количество показов
    clicks = Column(Integer, default=0)                   # Клики по QR/ссылке
    screen_time_seconds = Column(Integer, default=0)      # Время показа в секундах
    unique_views = Column(Integer, default=0)             # Уникальные просмотры (если есть данные)
    
    # ─── Timestamps ───
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ─────────────────────────────────────────────────────────────
# VenueDocument model (закрывающие документы для площадок)
# ─────────────────────────────────────────────────────────────

class DocumentType:
    """Типы документов"""
    ACT = "act"                      # Акт выполненных работ
    INVOICE = "invoice"              # Счёт на оплату
    REPORT = "report"                # Отчёт
    CONTRACT = "contract"            # Договор
    
    CHOICES = {
        ACT: "Акт выполненных работ",
        INVOICE: "Счёт на оплату",
        REPORT: "Отчёт о размещении",
        CONTRACT: "Договор",
    }


class VenueDocument(Base):
    """Закрывающие документы для площадок."""
    __tablename__ = "venue_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # ─── Связи ───
    venue_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tv_id = Column(Integer, ForeignKey("tvs.id"), nullable=True, index=True)
    payout_id = Column(Integer, ForeignKey("venue_payouts.id"), nullable=True, index=True)
    
    # ─── Документ ───
    document_type = Column(String(50), default=DocumentType.ACT)
    number = Column(String(50), nullable=True)            # Номер документа
    title = Column(String(300), nullable=False)           # Название документа
    
    # ─── Период ───
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    
    # ─── Сумма ───
    amount = Column(Numeric(12, 2), default=0)
    
    # ─── Файл ───
    file_url = Column(String(500), nullable=True)         # URL файла
    
    # ─── Статус ───
    status = Column(String(20), default="created")        # created, sent, signed
    
    # ─── Timestamps ───
    created_at = Column(DateTime, default=datetime.utcnow)
    signed_at = Column(DateTime, nullable=True)
    
    # ─── Relationships ───
    tv = relationship("TV", back_populates="documents")


# ─────────────────────────────────────────────────────────────
# SiteSettings model (настройки сайта, включая оферту)
# ─────────────────────────────────────────────────────────────

class SiteSettings(Base):
    """Настройки сайта (оферта, политика конфиденциальности и т.д.)."""
    __tablename__ = "site_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)  # offer, privacy, etc.
    title = Column(String(300), nullable=True)           # Заголовок
    content = Column(Text, nullable=True)                # Содержимое (HTML/Markdown)
    version = Column(String(50), nullable=True)          # Версия документа
    is_active = Column(Boolean, default=True)
    
    # ─── Timestamps ───
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
