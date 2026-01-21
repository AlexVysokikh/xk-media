"""
Скрипт для добавления недостающей колонки yk_payment_id в таблицу payments
"""
import sqlite3
import os

# Путь к базе данных
db_path = "xk_media.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Проверяем, существует ли колонка
        cursor.execute("PRAGMA table_info(payments)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'yk_payment_id' not in columns:
            print("Adding column yk_payment_id...")
            cursor.execute("""
                ALTER TABLE payments 
                ADD COLUMN yk_payment_id VARCHAR(100)
            """)
            conn.commit()
            print("SUCCESS: Column yk_payment_id added!")
        else:
            print("OK: Column yk_payment_id already exists")
        
        # Проверяем индекс
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='ix_payments_yk_payment_id'")
        if not cursor.fetchone():
            print("Creating index for yk_payment_id...")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS ix_payments_yk_payment_id 
                ON payments(yk_payment_id)
            """)
            conn.commit()
            print("SUCCESS: Index created!")
        else:
            print("OK: Index already exists")
            
    except Exception as e:
        print(f"ERROR: {e}")
        conn.rollback()
    finally:
        conn.close()
else:
    print(f"⚠️ База данных {db_path} не найдена. Она будет создана при первом запуске приложения.")
