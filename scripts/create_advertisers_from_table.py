"""
Скрипт для создания аккаунтов рекламодателей и их рекламных кампаний на основе данных из таблицы.
"""
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy.orm import Session

from app.db import SessionLocal, init_db
from app.models import (
    User, Role, TV, TVLink, Subscription, Payment, PaymentStatus,
    VenueCategory, TargetAudience, EquipmentType
)
from app.security import get_password_hash


# Данные из таблицы
ADVERTISERS_DATA = [
    {
        "company_name": "Shapeme",
        "legal_name": "Самойлова Анна Вик",
        "description": "Косметика и уход за телом",
        "campaigns": [
            {
                "tv_name": "Руслан привез",
                "start_date": date(2025, 12, 29),
                "end_date": date(2026, 1, 31),
            },
            {
                "tv_name": "Любимые места",
                "start_date": date(2025, 12, 29),
                "end_date": date(2026, 1, 31),
            },
        ]
    },
    {
        "company_name": "Поселок Верхняя Руза",
        "legal_name": "Никогосов Иван Арноевич",
        "description": "Недвижимость",
        "campaigns": [
            {
                "tv_name": "Руслан привез",
                "start_date": date(2025, 12, 26),
                "end_date": date(2026, 1, 31),
            },
            {
                "tv_name": "Одинцово Лакма",
                "start_date": date(2025, 12, 26),
                "end_date": date(2026, 1, 31),
            },
        ]
    },
    {
        "company_name": "Apelsin Travel",
        "legal_name": "АПЕЛЬСИН ТРЕВЕЛ ООО",
        "description": "Туризм и путешествия",
        "campaigns": [
            {
                "tv_name": "Руслан привез",
                "start_date": date(2025, 12, 30),
                "end_date": date(2026, 1, 31),
            },
            {
                "tv_name": "Любимые места",
                "start_date": date(2025, 12, 30),
                "end_date": date(2026, 1, 31),
            },
        ]
    },
    {
        "company_name": "Epilate Me",
        "legal_name": "Овчинников Максим Андреевич",
        "description": "Эпиляция и косметология",
        "campaigns": [
            {
                "tv_name": "Любимые места",
                "start_date": date(2025, 12, 15),
                "end_date": date(2026, 1, 31),
            },
            {
                "tv_name": "Руслан привез",
                "start_date": date(2025, 12, 15),
                "end_date": date(2026, 1, 31),
            },
        ]
    },
    {
        "company_name": "Творческая мастерская - Раёк",
        "legal_name": None,
        "description": "Обучение детей",
        "campaigns": [
            {
                "tv_name": "Одинцово Лакма",
                "start_date": date(2026, 1, 27),
                "end_date": date(2026, 2, 28),
            },
        ]
    },
]


def generate_email(company_name: str) -> str:
    """Генерирует email на основе названия компании."""
    # Простая транслитерация русских букв в латинские
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
    }
    
    # Приводим к нижнему регистру
    email_base = company_name.lower()
    
    # Транслитерируем
    result = []
    for char in email_base:
        if char in translit_map:
            result.append(translit_map[char])
        elif char.isalnum():
            result.append(char)
        elif char in [' ', '-', '_']:
            result.append('_')
    
    email_base = ''.join(result)
    
    # Убираем множественные подчеркивания
    while '__' in email_base:
        email_base = email_base.replace('__', '_')
    
    # Убираем подчеркивания в начале и конце
    email_base = email_base.strip('_')
    
    return f"{email_base}@xk-media.ru"


def generate_password(company_name: str) -> str:
    """Генерирует пароль на основе названия компании."""
    # Убираем спецсимволы и дефисы
    clean_name = company_name.replace("-", " ").replace("_", " ")
    words = clean_name.split()
    
    if len(words) >= 2:
        # Берем первые 3-4 буквы из первого и второго слова
        first_part = words[0][:4].upper() if len(words[0]) >= 4 else words[0].upper()
        second_part = words[1][:3].lower() if len(words[1]) >= 3 else words[1].lower()
        password = first_part + second_part + "2026!"
    elif len(words) == 1:
        # Если одно слово, берем первые 6-7 символов
        password = words[0][:7].upper() + "2026!"
    else:
        # Fallback
        password = company_name[:7].upper().replace("-", "").replace("_", "") + "2026!"
    
    return password


def get_or_create_tv(db: Session, tv_name: str) -> TV:
    """Создает или находит ТВ-точку по названию."""
    tv = db.query(TV).filter(TV.name == tv_name).first()
    
    if not tv:
        # Создаем новую ТВ-точку
        tv_code = tv_name.upper().replace(" ", "_").replace("-", "_")[:20]
        tv = TV(
            code=tv_code,
            name=tv_name,
            venue_name=tv_name,
            category=VenueCategory.OTHER,
            target_audience=TargetAudience.MASS,
            city="Москва",
            address=f"Адрес для {tv_name}",
            description=f"ТВ-точка: {tv_name}",
            clients_per_day=300,
            avg_check=Decimal("500.00"),
            working_hours="09:00-21:00",
            equipment_type=EquipmentType.AGGREGATOR,
            revenue_share=Decimal("60.00"),
            is_active=True,
            is_approved=True,
        )
        db.add(tv)
        db.flush()
        print(f"   [*] Создана ТВ-точка: {tv_name}")
    
    return tv


def create_advertisers():
    """Создает аккаунты рекламодателей и их рекламные кампании."""
    db: Session = SessionLocal()
    
    try:
        # Инициализация БД
        init_db()
        
        created_accounts = []
        
        print("="*70)
        print("СОЗДАНИЕ АККАУНТОВ РЕКЛАМОДАТЕЛЕЙ")
        print("="*70)
        
        for adv_data in ADVERTISERS_DATA:
            company_name = adv_data["company_name"]
            legal_name = adv_data["legal_name"]
            description = adv_data["description"]
            
            # Генерируем email и пароль
            email = generate_email(company_name)
            password = generate_password(company_name)
            
            print(f"\n[*] Обрабатываю: {company_name}")
            print(f"   Email: {email}")
            print(f"   Пароль: {password}")
            
            # Проверяем, существует ли уже аккаунт
            existing_user = db.query(User).filter(User.email == email).first()
            
            if existing_user:
                print(f"   [WARNING] Аккаунт {email} уже существует, обновляю данные...")
                advertiser = existing_user
                
                # Обновляем данные
                advertiser.company_name = company_name
                advertiser.legal_name = legal_name
                advertiser.description = description
                advertiser.is_active = True
                advertiser.is_verified = True
                
                # Удаляем старые подписки и ссылки
                db.query(Subscription).filter(Subscription.advertiser_id == advertiser.id).delete()
                db.query(TVLink).filter(TVLink.advertiser_id == advertiser.id).delete()
                db.commit()
            else:
                # Создаем нового рекламодателя
                advertiser = User(
                    email=email,
                    hashed_password=get_password_hash(password),
                    role=Role.ADVERTISER,
                    company_name=company_name,
                    legal_name=legal_name,
                    description=description,
                    is_active=True,
                    is_verified=True,
                    balance=Decimal("10000.00"),  # Начальный баланс
                )
                db.add(advertiser)
                db.flush()
                print(f"   [OK] Создан аккаунт рекламодателя (ID: {advertiser.id})")
            
            # Создаем или находим ТВ-точки и создаем подписки
            for campaign in adv_data["campaigns"]:
                tv_name = campaign["tv_name"]
                start_date = campaign["start_date"]
                end_date = campaign["end_date"]
                
                print(f"   [*] Создаю кампанию на ТВ: {tv_name}")
                
                # Получаем или создаем ТВ-точку
                tv = get_or_create_tv(db, tv_name)
                
                # Вычисляем стоимость подписки (примерно 1000 руб за день)
                days = (end_date - start_date).days + 1
                price = Decimal(str(days * 1000))
                
                # Создаем платеж
                payment = Payment(
                    user_id=advertiser.id,
                    amount=price,
                    currency="RUB",
                    payment_type="subscription",
                    description=f"Подписка на ТВ {tv_name} ({start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')})",
                    order_id=f"ADV-{advertiser.id}-{tv.id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                    status=PaymentStatus.SUCCEEDED,
                    yk_payment_id=f"yk_{advertiser.id}_{tv.id}_{datetime.now(timezone.utc).timestamp()}",
                    created_at=datetime.now(timezone.utc),
                    paid_at=datetime.now(timezone.utc)
                )
                db.add(payment)
                db.flush()
                
                # Вычисляем выплату площадке (60% для агрегатора)
                venue_payout = price * Decimal("0.60")
                
                # Создаем подписку
                subscription = Subscription(
                    advertiser_id=advertiser.id,
                    tv_id=tv.id,
                    payment_id=payment.id,
                    start_date=start_date,
                    end_date=end_date,
                    price=price,
                    venue_payout=venue_payout,
                    venue_payout_status="pending",
                    is_active=True,
                )
                db.add(subscription)
                db.flush()
                
                # Создаем рекламную ссылку (TVLink)
                tv_link = TVLink(
                    tv_id=tv.id,
                    advertiser_id=advertiser.id,
                    advertiser_name=company_name,
                    title=f"Реклама {company_name}",
                    url=f"https://{generate_email(company_name).split('@')[0]}.ru",
                    description=description,
                    position=0,
                    is_active=True,
                )
                db.add(tv_link)
                
                print(f"      [OK] Создана подписка: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')} ({price:,.0f} руб)")
            
            db.commit()
            
            created_accounts.append({
                "company_name": company_name,
                "email": email,
                "password": password,
                "legal_name": legal_name,
                "description": description,
                "campaigns_count": len(adv_data["campaigns"])
            })
        
        # Выводим итоговую информацию
        print("\n" + "="*70)
        print("ИТОГОВАЯ ИНФОРМАЦИЯ")
        print("="*70)
        print("\nСОЗДАННЫЕ АККАУНТЫ РЕКЛАМОДАТЕЛЕЙ:\n")
        
        for i, acc in enumerate(created_accounts, 1):
            print(f"{i}. {acc['company_name']}")
            print(f"   ЛОГИН: {acc['email']}")
            print(f"   ПАРОЛЬ: {acc['password']}")
            print(f"   ЮЛ: {acc['legal_name'] or 'Не указано'}")
            print(f"   Описание: {acc['description']}")
            print(f"   Рекламных кампаний: {acc['campaigns_count']}")
            print()
        
        # Сохраняем информацию в файл
        output_file = project_root / "advertisers_accounts.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("="*70 + "\n")
            f.write("СОЗДАННЫЕ АККАУНТЫ РЕКЛАМОДАТЕЛЕЙ\n")
            f.write("="*70 + "\n\n")
            
            for i, acc in enumerate(created_accounts, 1):
                f.write(f"{i}. {acc['company_name']}\n")
                f.write(f"   ЛОГИН: {acc['email']}\n")
                f.write(f"   ПАРОЛЬ: {acc['password']}\n")
                f.write(f"   ЮЛ: {acc['legal_name'] or 'Не указано'}\n")
                f.write(f"   Описание: {acc['description']}\n")
                f.write(f"   Рекламных кампаний: {acc['campaigns_count']}\n")
                f.write("\n")
            
            f.write("="*70 + "\n")
            f.write("ВАЖНО: Сохраните эти данные в безопасном месте!\n")
            f.write("="*70 + "\n")
        
        print(f"[OK] Информация сохранена в файл: {output_file}")
        print("="*70)
        print("[OK] ВСЕ АККАУНТЫ УСПЕШНО СОЗДАНЫ!")
        print("="*70)
        
    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Ошибка при создании аккаунтов: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_advertisers()
