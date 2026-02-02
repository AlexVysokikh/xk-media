#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для настройки Telegram уведомлений.
Помогает получить chat_id для пользователя @Aleksandr_Vys.
"""

import sys
import os
import httpx
import asyncio
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.settings import settings


async def get_chat_id(bot_token: str):
    """Получить chat_id из последних обновлений бота."""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data.get("ok") and data.get("result"):
                updates = data["result"]
                if updates:
                    # Берем последнее обновление
                    last_update = updates[-1]
                    if "message" in last_update:
                        chat = last_update["message"]["chat"]
                        chat_id = chat.get("id")
                        username = chat.get("username", "N/A")
                        first_name = chat.get("first_name", "N/A")
                        
                        print(f"\n✅ Найден chat_id:")
                        print(f"   Chat ID: {chat_id}")
                        print(f"   Username: @{username}")
                        print(f"   Имя: {first_name}")
                        print(f"\nДобавьте в .env файл:")
                        print(f"TELEGRAM_CHAT_ID={chat_id}")
                        return chat_id
                    else:
                        print("❌ В обновлениях нет сообщений. Напишите боту сообщение и попробуйте снова.")
                else:
                    print("❌ Нет обновлений. Напишите боту сообщение и попробуйте снова.")
            else:
                print(f"❌ Ошибка API: {data.get('description', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Ошибка при получении chat_id: {e}")
        import traceback
        traceback.print_exc()
    return None


async def test_telegram_send(bot_token: str, chat_id: str):
    """Тестовая отправка сообщения в Telegram."""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": "✅ Тестовое сообщение от XK Media. Telegram уведомления настроены правильно!",
            "parse_mode": "HTML"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            
            if result.get("ok"):
                print("\n✅ Тестовое сообщение успешно отправлено в Telegram!")
                return True
            else:
                print(f"❌ Ошибка отправки: {result.get('description', 'Unknown error')}")
                return False
    except Exception as e:
        print(f"❌ Ошибка при отправке тестового сообщения: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("=" * 60)
    print("Настройка Telegram уведомлений для XK Media")
    print("=" * 60)
    
    # Проверяем текущие настройки
    bot_token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    
    print(f"\nТекущие настройки:")
    print(f"  TELEGRAM_BOT_TOKEN: {'✅ Установлен' if bot_token else '❌ Не установлен'}")
    print(f"  TELEGRAM_CHAT_ID: {'✅ Установлен' if chat_id else '❌ Не установлен'}")
    
    if not bot_token:
        print("\n" + "=" * 60)
        print("📝 Инструкция по созданию Telegram бота:")
        print("=" * 60)
        print("1. Откройте Telegram и найдите @BotFather")
        print("2. Отправьте команду /newbot")
        print("3. Следуйте инструкциям для создания бота")
        print("4. Скопируйте токен бота (выглядит как: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)")
        print("5. Добавьте токен в .env файл:")
        print("   TELEGRAM_BOT_TOKEN=ваш_токен_бота")
        print("\nПосле создания бота, напишите ему любое сообщение от вашего аккаунта @Aleksandr_Vys")
        return
    
    print("\n" + "=" * 60)
    print("Получение chat_id...")
    print("=" * 60)
    
    if not chat_id:
        print("\n⚠️  Chat ID не установлен. Пытаемся получить автоматически...")
        print("Убедитесь, что вы написали боту сообщение от аккаунта @Aleksandr_Vys")
        
        new_chat_id = await get_chat_id(bot_token)
        if new_chat_id:
            print(f"\n✅ Добавьте в .env файл:")
            print(f"TELEGRAM_CHAT_ID={new_chat_id}")
    else:
        print(f"\n✅ Chat ID уже установлен: {chat_id}")
    
    # Тестовая отправка
    if bot_token and chat_id:
        print("\n" + "=" * 60)
        print("Тестовая отправка сообщения...")
        print("=" * 60)
        
        await test_telegram_send(bot_token, chat_id)
    
    print("\n" + "=" * 60)
    print("✅ Настройка завершена!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
