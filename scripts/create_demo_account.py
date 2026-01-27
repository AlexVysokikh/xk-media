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
        
        # 3. Создаем 4 ТВ-точки с типом VENUE (70% выплата)
        print("[*] Создаю 4 ТВ-точки для площадки...")
        tv_locations = [
            {
                "code": "DEMO001",
                "name": "ТВ-экран в кофейне «Уютная»",
                "address": "ул. Тверская, д. 10, стр. 1",
                "category": VenueCategory.CAFE,
                "clients_per_day": 400,
                "avg_check": Decimal("450.00")
            },
            {
                "code": "DEMO002",
                "name": "ТВ-экран в бизнес-центре «Столица»",
                "address": "ул. Новый Арбат, д. 15",
                "category": VenueCategory.BUSINESS_CENTER,
                "clients_per_day": 600,
                "avg_check": Decimal("800.00")
            },
            {
                "code": "DEMO003",
                "name": "ТВ-экран в фитнес-клубе «Актив»",
                "address": "пр-т Мира, д. 25",
                "category": VenueCategory.GYM,
                "clients_per_day": 350,
                "avg_check": Decimal("1200.00")
            },
            {
                "code": "DEMO004",
                "name": "ТВ-экран в торговом центре «Мега»",
                "address": "Ленинградский пр-т, д. 80",
                "category": VenueCategory.SHOPPING_CENTER,
                "clients_per_day": 1200,
                "avg_check": Decimal("2500.00")
            }
        ]
        
        tvs = []
        for tv_data in tv_locations:
            tv = TV(
                code=tv_data["code"],
                name=tv_data["name"],
                venue_name="Кофейня «Уютная»",
                category=tv_data["category"],
                target_audience=TargetAudience.MASS,
                city="Москва",
                address=tv_data["address"],
                legal_name="ИП Петров Иван Сергеевич",
                inn="7701987654",
                contact_person="Иван Петров",
                contact_phone="+7 (495) 123-45-67",
                contact_email="venue@demo-tv.ru",
                description=f"Современный ТВ-экран. Ежедневный поток: {tv_data['clients_per_day']} посетителей.",
                clients_per_day=tv_data["clients_per_day"],
                avg_check=tv_data["avg_check"],
                working_hours="08:00-22:00",
                venue_id=venue.id,
                equipment_type=EquipmentType.VENUE,  # Собственное оборудование = 70% выплата
                revenue_share=Decimal("70.00"),  # 70% площадке
                is_active=True,
                is_approved=True,
                created_at=datetime.utcnow() - timedelta(days=100)
            )
            db.add(tv)
            tvs.append(tv)
        
        db.flush()
        print(f"[OK] Создано {len(tvs)} ТВ-точек")
        
        # 4. Создаем рекламные кампании для демо-рекламодателя на всех 4 ТВ-точках
        print("[*] Создаю рекламные кампании для демо-рекламодателя на 4 ТВ-точках...")
        
        campaigns = [
            {
                "title": "Скидка 20% на весь ассортимент",
                "url": "https://demo-reklama.ru/promo/sale20",
                "description": "Специальное предложение",
                "image_url": "https://via.placeholder.com/800x600/4CAF50/FFFFFF?text=Sale+20%25"
            },
            {
                "title": "Новая коллекция весна-лето 2024",
                "url": "https://demo-reklama.ru/collection/spring2024",
                "description": "Свежие модели уже в продаже",
                "image_url": "https://via.placeholder.com/800x600/2196F3/FFFFFF?text=New+Collection"
            },
            {
                "title": "Бесплатная доставка при заказе от 2000₽",
                "url": "https://demo-reklama.ru/delivery/free",
                "description": "Быстрая доставка по Москве",
                "image_url": "https://via.placeholder.com/800x600/FF9800/FFFFFF?text=Free+Delivery"
            }
        ]
        
        # Распределяем кампании по ТВ-точкам с разными показателями
        tv_impressions_base = [12500, 15000, 9800, 18000]  # Базовые показы для каждой ТВ
        tv_clicks_base = [487, 585, 382, 702]  # Базовые клики для каждой ТВ
        
        links = []
        total_impressions = 0
        total_clicks = 0
        
        for tv_idx, tv in enumerate(tvs):
            for camp_idx, camp in enumerate(campaigns):
                # Распределяем показы и клики по ТВ
                impressions = tv_impressions_base[tv_idx] + (camp_idx * 500)
                clicks = int(tv_clicks_base[tv_idx] * (1 + camp_idx * 0.1))
                
                link = TVLink(
                    tv_id=tv.id,
                    advertiser_id=advertiser.id,
                    advertiser_name=advertiser.company_name,
                    title=camp["title"],
                    url=camp["url"],
                    description=camp["description"],
                    image_url=camp["image_url"],
                    impressions=impressions,
                    clicks=clicks,
                    position=camp_idx,
                    is_active=True,
                    created_at=datetime.utcnow() - timedelta(days=60 - (tv_idx * 10))
                )
                db.add(link)
                links.append(link)
                total_impressions += impressions
                total_clicks += clicks
        
        db.flush()
        print(f"[OK] Создано {len(links)} рекламных кампаний на {len(tvs)} ТВ-точках")
        
        # Вычисляем общие метрики
        avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        print(f"   [*] Общая статистика:")
        print(f"      Показов: {total_impressions:,}")
        print(f"      Кликов: {total_clicks:,}")
        print(f"      CTR: {avg_ctr:.2f}%")
        
        # 5. Создаем подписки для демо-рекламодателя на всех 4 ТВ-точках
        print("[*] Создаю подписки для демо-рекламодателя на 4 ТВ-точках...")
        
        active_sub_start = date.today() - timedelta(days=15)
        active_sub_end = date.today() + timedelta(days=15)
        sub_price_per_tv = Decimal("15000.00")
        
        for tv in tvs:
            active_payment = Payment(
                user_id=advertiser.id,
                amount=sub_price_per_tv,
                currency="RUB",
                payment_type="subscription",
                description=f"Подписка на ТВ {tv.code} ({active_sub_start.strftime('%d.%m.%Y')} - {active_sub_end.strftime('%d.%m.%Y')})",
                order_id=f"DEMO-{tv.code}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                status=PaymentStatus.SUCCEEDED,
                yk_payment_id=f"yk_demo_{tv.code}_{datetime.utcnow().timestamp()}",
                created_at=datetime.utcnow() - timedelta(days=15),
                paid_at=datetime.utcnow() - timedelta(days=15)
            )
            db.add(active_payment)
            db.flush()
            
            active_sub = Subscription(
                advertiser_id=advertiser.id,
                tv_id=tv.id,
                payment_id=active_payment.id,
                start_date=active_sub_start,
                end_date=active_sub_end,
                price=sub_price_per_tv,
                venue_payout=sub_price_per_tv * Decimal("0.70"),
                venue_payout_status="paid",
                is_active=True,
                created_at=datetime.utcnow() - timedelta(days=15)
            )
            db.add(active_sub)
        
        db.flush()
        print(f"[OK] Создано {len(tvs)} активных подписок для демо-рекламодателя")
        
        # 6. Создаем 15 рекламодателей для площадки (по 7000 руб каждый, 70% = 4900 руб площадке)
        print("[*] Создаю 15 рекламодателей для площадки...")
        
        advertiser_names = [
            "ООО «Стиль и Мода»", "ИП Иванов Сергей", "ООО «ТехноМарт»",
            "ИП Петрова Мария", "ООО «Красота и Здоровье»", "ИП Сидоров Алексей",
            "ООО «Дом и Сад»", "ИП Козлова Анна", "ООО «СпортПро»",
            "ИП Волков Дмитрий", "ООО «АвтоСервис Плюс»", "ИП Морозова Елена",
            "ООО «Кулинария»", "ИП Лебедев Павел", "ООО «Электроника»"
        ]
        
        venue_total_revenue = Decimal("0.00")
        venue_subscriptions = []
        
        for i, company_name in enumerate(advertiser_names):
            # Создаем рекламодателя
            new_advertiser = User(
                email=f"advertiser{i+1}@demo-tv.ru",
                hashed_password=get_password_hash("Advertiser2024!"),
                role=Role.ADVERTISER,
                first_name=f"Рекламодатель{i+1}",
                company_name=company_name,
                inn=f"7701{1000000 + i:07d}",
                is_active=True,
                is_verified=True,
                balance=Decimal("10000.00"),
                created_at=datetime.utcnow() - timedelta(days=90 - i*5)
            )
            db.add(new_advertiser)
            db.flush()
            
            # Создаем подписку на первую ТВ-точку (DEMO001)
            sub_price = Decimal("7000.00")
            venue_payout = sub_price * Decimal("0.70")  # 70% = 4900 руб
            venue_total_revenue += venue_payout
            
            sub_start = date.today() - timedelta(days=10)
            sub_end = date.today() + timedelta(days=20)
            
            payment = Payment(
                user_id=new_advertiser.id,
                amount=sub_price,
                currency="RUB",
                payment_type="subscription",
                description=f"Подписка на ТВ {tvs[0].code} ({sub_start.strftime('%d.%m.%Y')} - {sub_end.strftime('%d.%m.%Y')})",
                order_id=f"VENUE-ADV{i+1}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                status=PaymentStatus.SUCCEEDED,
                yk_payment_id=f"yk_venue_adv{i+1}_{datetime.utcnow().timestamp()}",
                created_at=datetime.utcnow() - timedelta(days=10),
                paid_at=datetime.utcnow() - timedelta(days=10)
            )
            db.add(payment)
            db.flush()
            
            subscription = Subscription(
                advertiser_id=new_advertiser.id,
                tv_id=tvs[0].id,
                payment_id=payment.id,
                start_date=sub_start,
                end_date=sub_end,
                price=sub_price,
                venue_payout=venue_payout,
                venue_payout_status="paid",
                is_active=True,
                created_at=datetime.utcnow() - timedelta(days=10)
            )
            db.add(subscription)
            venue_subscriptions.append(subscription)
        
        db.flush()
        print(f"[OK] Создано 15 рекламодателей для площадки")
        print(f"   [*] Каждый платит: 7,000 RUB")
        print(f"   [*] Выплата площадке (70%): 4,900 RUB с каждого")
        print(f"   [*] Общий доход площадки: {venue_total_revenue:,.0f} RUB")
        
        # 7. Создаем дополнительные платежи (пополнение баланса)
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
        print(f"   - ТВ-площадка: {venue.company_name}")
        print(f"   - ТВ-точек: {len(tvs)}")
        print(f"   - Рекламных кампаний: {len(links)}")
        print(f"   - Всего показов: {total_impressions:,}")
        print(f"   - Всего кликов: {total_clicks:,}")
        print(f"   - Средний CTR: {avg_ctr:.2f}%")
        print(f"   - Активных подписок демо-рекламодателя: {len(tvs)}")
        print(f"   - Выплата площадке: 70%")
        print(f"   - Баланс рекламодателя: {advertiser.balance:,.0f} RUB")
        print(f"\nСТАТИСТИКА ПЛОЩАДКИ:")
        print(f"   - Рекламодателей на площадке: 15")
        print(f"   - Платеж с каждого: 7,000 RUB")
        print(f"   - Выплата площадке (70%): 4,900 RUB с каждого")
        print(f"   - Общий доход площадки: {venue_total_revenue:,.0f} RUB")
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
