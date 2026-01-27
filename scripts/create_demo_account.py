"""
Скрипт для создания демо-аккаунта с хорошими показателями для демонстрации эффективности рекламы.
"""
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.db import SessionLocal, init_db
from app.models import (
    User, Role, TV, TVLink, Subscription, Payment, PaymentStatus,
    VenueCategory, TargetAudience, EquipmentType
)
from app.security import get_password_hash
from app.services.auth_service import AuthService


def create_demo_account():
    """Создает демо-аккаунт с тестовыми данными."""
    db: Session = SessionLocal()
    
    try:
        # Инициализация БД
        init_db()
        
        # Данные для демо-аккаунта
        demo_email = "demo@xk-media.ru"
        demo_password = "Demo2024!"
        
        # Проверяем, существует ли уже демо-аккаунт
        existing_user = db.query(User).filter(User.email == demo_email).first()
        if existing_user:
            print(f"[WARNING] Демо-аккаунт {demo_email} уже существует!")
            print(f"   ID: {existing_user.id}")
            print(f"   Роль: {existing_user.role}")
            return
        
        # 1. Создаем рекламодателя (демо-аккаунт)
        print("[*] Создаю демо-аккаунт рекламодателя...")
        advertiser = User(
            email=demo_email,
            hashed_password=get_password_hash(demo_password),
            role=Role.ADVERTISER,
            first_name="Демо",
            last_name="Рекламодатель",
            company_name="ООО «Демо Реклама»",
            legal_name="Общество с ограниченной ответственностью «Демо Реклама»",
            inn="7701234567",
            website="https://demo-reklama.ru",
            description="Демонстрационный аккаунт для показа эффективности indoor-рекламы",
            is_active=True,
            is_verified=True,
            balance=Decimal("50000.00"),  # Начальный баланс
            created_at=datetime.utcnow() - timedelta(days=90)  # Аккаунт создан 3 месяца назад
        )
        db.add(advertiser)
        db.flush()
        print(f"[OK] Создан рекламодатель: {advertiser.email} (ID: {advertiser.id})")
        
        # 2. Создаем площадку (venue) с ТВ
        print("[*] Создаю демо-площадку с ТВ...")
        venue = User(
            email="venue@demo-tv.ru",
            hashed_password=get_password_hash("Venue2024!"),
            role=Role.VENUE,
            first_name="Иван",
            last_name="Петров",
            company_name="Кофейня «Уютная»",
            legal_name="ИП Петров Иван Сергеевич",
            inn="7701987654",
            website="https://coffee-demo.ru",
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow() - timedelta(days=120)
        )
        db.add(venue)
        db.flush()
        print(f"[OK] Создана площадка: {venue.company_name} (ID: {venue.id})")
        
        # 3. Создаем ТВ с типом VENUE (70% выплата)
        tv = TV(
            code="DEMO001",
            name="ТВ-экран в кофейне «Уютная»",
            venue_name="Кофейня «Уютная»",
            category=VenueCategory.CAFE,
            target_audience=TargetAudience.MASS,
            city="Москва",
            address="ул. Тверская, д. 10, стр. 1",
            legal_name="ИП Петров Иван Сергеевич",
            inn="7701987654",
            contact_person="Иван Петров",
            contact_phone="+7 (495) 123-45-67",
            contact_email="venue@demo-tv.ru",
            description="Современный ТВ-экран в центре зала кофейни. Ежедневный поток: 300-500 посетителей.",
            clients_per_day=400,
            avg_check=Decimal("450.00"),
            working_hours="08:00-22:00",
            venue_id=venue.id,
            equipment_type=EquipmentType.VENUE,  # Собственное оборудование = 70% выплата
            revenue_share=Decimal("70.00"),  # 70% площадке
            is_active=True,
            is_approved=True,
            created_at=datetime.utcnow() - timedelta(days=100)
        )
        db.add(tv)
        db.flush()
        print(f"[OK] Создано ТВ: {tv.name} (Код: {tv.code}, ID: {tv.id})")
        
        # 4. Создаем несколько рекламных кампаний с хорошими показателями
        print("[*] Создаю рекламные кампании с хорошими показателями...")
        
        campaigns = [
            {
                "title": "Скидка 20% на весь ассортимент",
                "url": "https://demo-reklama.ru/promo/sale20",
                "description": "Специальное предложение для посетителей кофейни",
                "image_url": "https://via.placeholder.com/800x600/4CAF50/FFFFFF?text=Sale+20%25",
                "impressions": 12500,  # 12500 показов
                "clicks": 487,  # 487 кликов
                "position": 0,
                "created_at": datetime.utcnow() - timedelta(days=60)
            },
            {
                "title": "Новая коллекция весна-лето 2024",
                "url": "https://demo-reklama.ru/collection/spring2024",
                "description": "Свежие модели уже в продаже",
                "image_url": "https://via.placeholder.com/800x600/2196F3/FFFFFF?text=New+Collection",
                "impressions": 9800,
                "clicks": 342,
                "position": 1,
                "created_at": datetime.utcnow() - timedelta(days=45)
            },
            {
                "title": "Бесплатная доставка при заказе от 2000₽",
                "url": "https://demo-reklama.ru/delivery/free",
                "description": "Быстрая доставка по Москве",
                "image_url": "https://via.placeholder.com/800x600/FF9800/FFFFFF?text=Free+Delivery",
                "impressions": 11200,
                "clicks": 521,
                "position": 2,
                "created_at": datetime.utcnow() - timedelta(days=30)
            },
            {
                "title": "Акция: 2+1 = 3 товара по цене 2",
                "url": "https://demo-reklama.ru/promo/buy2get1",
                "description": "Выгодное предложение ограничено",
                "image_url": "https://via.placeholder.com/800x600/E91E63/FFFFFF?text=2%2B1",
                "impressions": 8500,
                "clicks": 298,
                "position": 3,
                "created_at": datetime.utcnow() - timedelta(days=15)
            }
        ]
        
        links = []
        for i, camp in enumerate(campaigns):
            link = TVLink(
                tv_id=tv.id,
                advertiser_id=advertiser.id,
                advertiser_name=advertiser.company_name,
                title=camp["title"],
                url=camp["url"],
                description=camp["description"],
                image_url=camp["image_url"],
                impressions=camp["impressions"],
                clicks=camp["clicks"],
                position=camp["position"],
                is_active=True,
                created_at=camp["created_at"]
            )
            db.add(link)
            links.append(link)
        
        db.flush()
        print(f"[OK] Создано {len(links)} рекламных кампаний")
        
        # Вычисляем общие метрики
        total_impressions = sum(c["impressions"] for c in campaigns)
        total_clicks = sum(c["clicks"] for c in campaigns)
        avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        print(f"   [*] Общая статистика:")
        print(f"      Показов: {total_impressions:,}")
        print(f"      Кликов: {total_clicks:,}")
        print(f"      CTR: {avg_ctr:.2f}%")
        
        # 5. Создаем подписки с выплатами 70%
        print("[*] Создаю подписки с выплатами 70%...")
        
        # Текущая активная подписка
        active_sub_start = date.today() - timedelta(days=15)
        active_sub_end = date.today() + timedelta(days=15)
        active_sub_price = Decimal("15000.00")
        active_sub_payout = active_sub_price * Decimal("0.70")  # 70% площадке
        
        # Прошлые подписки
        past_subscriptions = [
            {
                "start": date.today() - timedelta(days=75),
                "end": date.today() - timedelta(days=45),
                "price": Decimal("12000.00")
            },
            {
                "start": date.today() - timedelta(days=45),
                "end": date.today() - timedelta(days=15),
                "price": Decimal("13500.00")
            }
        ]
        
        # Создаем платеж для активной подписки
        active_payment = Payment(
            user_id=advertiser.id,
            amount=active_sub_price,
            currency="RUB",
            payment_type="subscription",
            description=f"Подписка на ТВ {tv.code} ({active_sub_start.strftime('%d.%m.%Y')} - {active_sub_end.strftime('%d.%m.%Y')})",
            order_id=f"DEMO-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            status=PaymentStatus.SUCCEEDED,
            yk_payment_id=f"yk_demo_{datetime.utcnow().timestamp()}",
            created_at=datetime.utcnow() - timedelta(days=15),
            paid_at=datetime.utcnow() - timedelta(days=15)
        )
        db.add(active_payment)
        db.flush()
        
        # Активная подписка
        active_sub = Subscription(
            advertiser_id=advertiser.id,
            tv_id=tv.id,
            payment_id=active_payment.id,
            start_date=active_sub_start,
            end_date=active_sub_end,
            price=active_sub_price,
            venue_payout=active_sub_payout,
            venue_payout_status="paid",
            is_active=True,
            created_at=datetime.utcnow() - timedelta(days=15)
        )
        db.add(active_sub)
        
        # Прошлые подписки
        for i, past_sub in enumerate(past_subscriptions):
            past_payment = Payment(
                user_id=advertiser.id,
                amount=past_sub["price"],
                currency="RUB",
                payment_type="subscription",
                description=f"Подписка на ТВ {tv.code} ({past_sub['start'].strftime('%d.%m.%Y')} - {past_sub['end'].strftime('%d.%m.%Y')})",
                order_id=f"DEMO-PAST-{i}-{past_sub['start'].strftime('%Y%m%d')}",
                status=PaymentStatus.SUCCEEDED,
                yk_payment_id=f"yk_demo_past_{i}_{past_sub['start'].strftime('%Y%m%d')}",
                created_at=past_sub["start"] - timedelta(days=1),
                paid_at=past_sub["start"] - timedelta(days=1)
            )
            db.add(past_payment)
            db.flush()
            
            past_subscription = Subscription(
                advertiser_id=advertiser.id,
                tv_id=tv.id,
                payment_id=past_payment.id,
                start_date=past_sub["start"],
                end_date=past_sub["end"],
                price=past_sub["price"],
                venue_payout=past_sub["price"] * Decimal("0.70"),
                venue_payout_status="paid",
                is_active=False,
                created_at=past_sub["start"] - timedelta(days=1)
            )
            db.add(past_subscription)
        
        db.flush()
        print(f"[OK] Создано 3 подписки (1 активная, 2 завершенные)")
        print(f"   [*] Активная подписка: {active_sub_price:,.0f} RUB")
        print(f"   [*] Выплата площадке (70%): {active_sub_payout:,.0f} RUB")
        
        # 6. Создаем дополнительные платежи (пополнение баланса)
        print("[*] Создаю историю платежей...")
        balance_payments = [
            {"amount": Decimal("30000.00"), "days_ago": 80},
            {"amount": Decimal("20000.00"), "days_ago": 50},
            {"amount": Decimal("25000.00"), "days_ago": 20}
        ]
        
        for pay in balance_payments:
            payment = Payment(
                user_id=advertiser.id,
                amount=pay["amount"],
                currency="RUB",
                payment_type="balance",
                description="Пополнение баланса",
                order_id=f"DEMO-BALANCE-{pay['days_ago']}",
                status=PaymentStatus.SUCCEEDED,
                yk_payment_id=f"yk_balance_{pay['days_ago']}",
                created_at=datetime.utcnow() - timedelta(days=pay["days_ago"]),
                paid_at=datetime.utcnow() - timedelta(days=pay["days_ago"])
            )
            db.add(payment)
        
        db.commit()
        print("[OK] Создано 3 платежа на пополнение баланса")
        
        # Итоговая информация
        print("\n" + "="*60)
        print("[OK] ДЕМО-АККАУНТ УСПЕШНО СОЗДАН!")
        print("="*60)
        print(f"\nЛОГИН: {demo_email}")
        print(f"ПАРОЛЬ: {demo_password}")
        print(f"\nСТАТИСТИКА:")
        print(f"   - Рекламодатель: {advertiser.company_name}")
        print(f"   - ТВ-площадка: {tv.venue_name} ({tv.code})")
        print(f"   - Рекламных кампаний: {len(links)}")
        print(f"   - Всего показов: {total_impressions:,}")
        print(f"   - Всего кликов: {total_clicks:,}")
        print(f"   - Средний CTR: {avg_ctr:.2f}%")
        print(f"   - Активных подписок: 1")
        print(f"   - Выплата площадке: 70%")
        print(f"   - Баланс рекламодателя: {advertiser.balance:,.0f} RUB")
        print(f"\nВойдите в систему и проверьте дашборд рекламодателя!")
        print("="*60)
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Ошибка при создании демо-аккаунта: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_demo_account()
