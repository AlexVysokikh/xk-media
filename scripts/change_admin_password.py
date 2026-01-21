#!/usr/bin/env python3
"""
Скрипт для смены пароля администратора
"""
import sys
import hashlib
from pathlib import Path

# Добавляем путь к приложению
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import SessionLocal
from app.models import User
from app.security import Role


def change_admin_password(new_password: str):
    """Изменить пароль администратора"""
    db = SessionLocal()
    try:
        # Находим админа
        admin = db.query(User).filter(User.role == Role.ADMIN).first()
        
        if not admin:
            print("❌ Администратор не найден!")
            return False
        
        # Хешируем новый пароль
        hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
        
        # Обновляем пароль
        admin.hashed_password = hashed_password
        db.commit()
        
        print(f"✅ Пароль администратора ({admin.email}) успешно изменен!")
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка при смене пароля: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python change_admin_password.py <новый_пароль>")
        sys.exit(1)
    
    new_password = sys.argv[1]
    
    if len(new_password) < 8:
        print("❌ Пароль должен быть не менее 8 символов!")
        sys.exit(1)
    
    success = change_admin_password(new_password)
    sys.exit(0 if success else 1)
