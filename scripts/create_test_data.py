# -*- coding: utf-8 -*-
"""Create test data for the application."""

from app.db import SessionLocal
from app.models import User, Role, TV, VenueCategory, TargetAudience, EquipmentType, SiteSettings
from app.security import get_password_hash
from decimal import Decimal
from datetime import datetime

db = SessionLocal()

# Create offer
offer_content = """<h2>1. Общие положения</h2>
<p>Настоящая Оферта является официальным предложением ООО "XK Media" (далее — Исполнитель) заключить Договор на оказание услуг по размещению рекламы на ТВ-экранах.</p>

<h2>2. Предмет договора</h2>
<p>Исполнитель обязуется оказать Заказчику услуги по размещению рекламных материалов на ТВ-экранах сети XK Media в соответствии с выбранным тарифом.</p>

<h2>3. Стоимость услуг</h2>
<ul>
    <li>Стоимость размещения определяется действующим прайс-листом</li>
    <li>Оплата производится на условиях 100% предоплаты</li>
    <li>Возврат денежных средств осуществляется в соответствии с законодательством РФ</li>
</ul>

<h2>4. Права и обязанности сторон</h2>
<p>Исполнитель обязуется:</p>
<ul>
    <li>Обеспечить размещение рекламных материалов в соответствии с заказом</li>
    <li>Предоставлять статистику показов</li>
</ul>

<h2>5. Конфиденциальность</h2>
<p>Стороны обязуются сохранять конфиденциальность полученной информации.</p>

<h2>6. Реквизиты</h2>
<p>ООО "XK Media"<br>ИНН: 7712345678<br>ОГРН: 1234567890123</p>"""

offer = SiteSettings(
    key='offer',
    title='Оферта на оказание услуг',
    content=offer_content,
    version='1.0',
    is_active=True
)
db.add(offer)
db.commit()
print('Created offer')

# Create advertiser with offer accepted
advertiser = User(
    email='test@advertiser.ru',
    hashed_password=get_password_hash('test123'),
    role=Role.ADVERTISER,
    first_name='Test',
    last_name='Advertiser',
    company_name='Test Company',
    balance=Decimal('50000'),
    is_active=True,
    is_verified=True,
    offer_accepted_at=datetime.utcnow(),
    offer_version='1.0'
)
db.add(advertiser)
db.commit()
print(f'Created advertiser: {advertiser.email}')

# Create venue with offer accepted
venue = User(
    email='venue@test.ru',
    hashed_password=get_password_hash('test123'),
    role=Role.VENUE,
    first_name='Vladimir',
    last_name='Petrov',
    company_name='Coffeeshop Sunrise',
    is_active=True,
    is_verified=True,
    offer_accepted_at=datetime.utcnow(),
    offer_version='1.0'
)
db.add(venue)
db.commit()
print(f'Created venue: {venue.email}')

# Create TV
tv = TV(
    code='tv-sunrise-01',
    name='TV at Entrance',
    venue_name='Coffeeshop Sunrise',
    category=VenueCategory.CAFE,
    city='Moscow',
    equipment_type=EquipmentType.AGGREGATOR,
    revenue_share=Decimal('60.0'),
    venue_id=venue.id,
    is_active=True,
    is_approved=True
)
db.add(tv)
db.commit()
print('Created TV')

db.close()
print('Done!')
