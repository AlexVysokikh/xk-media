#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для активации всех ТВ у всех рекламодателей.
Обновляет даты подписок так, чтобы они были активными (включают сегодняшнюю дату).
"""

import sys
import os
from pathlib import Path

# Настройка кодировки для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date, timedelta
from app.db import SessionLocal, engine
from app.models import Subscription

def activate_all_tvs():
    """Обновляет все подписки, чтобы они были активными."""
    db = SessionLocal()
    try:
        today = date.today()
        
        # Находим все подписки
        subscriptions = db.query(Subscription).all()
        
        updated_count = 0
        for sub in subscriptions:
            # Если подписка не активна (даты не включают сегодня)
            if not (sub.start_date <= today <= sub.end_date):
                # Обновляем даты так, чтобы подписка была активной
                # Если end_date в прошлом, продлеваем на 30 дней от сегодня
                if sub.end_date < today:
                    sub.end_date = today + timedelta(days=30)
                
                # Если start_date в будущем, делаем её сегодня
                if sub.start_date > today:
                    sub.start_date = today
                
                updated_count += 1
        
        db.commit()
        print(f"Обновлено подписок: {updated_count}")
        print(f"Всего подписок в базе: {len(subscriptions)}")
        
        # Проверяем результат
        active_count = db.query(Subscription).filter(
            Subscription.start_date <= today,
            Subscription.end_date >= today
        ).count()
        print(f"Активных подписок после обновления: {active_count}")
        
    except Exception as e:
        db.rollback()
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Активация всех ТВ у всех рекламодателей...")
    activate_all_tvs()
    print("Готово!")
