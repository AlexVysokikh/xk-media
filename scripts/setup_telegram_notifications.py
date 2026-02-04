#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для настройки Telegram уведомлений.

Показывает chat_id пользователей, которые написали боту.
Можно использовать allow-list по TELEGRAM_ALLOWED_USERNAMES (через запятую, без @).
"""

import sys
import os
import httpx
import asyncio
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.settings import settings


async def get_chat_ids(bot_token: str, allowed_usernames: set[str] | None = None):
    """Получить список chat_id из обновлений бота."""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        if not data.get("ok"):
            print(f"❌ Ошибка API: {data.get('description', 'Unknown error')}")
            return []

        updates = data.get("result") or []
        if not updates:
            print("❌ Нет обновлений. Напишите боту /start и любое сообщение (с нужных аккаунтов) и запустите скрипт снова.")
            return []

        chats: dict[int, dict] = {}
        for upd in updates:
            msg = upd.get("message") or upd.get("edited_message")
            if not msg:
                continue
            chat = msg.get("chat") or {}
            chat_id = chat.get("id")
            if chat_id is None:
                continue
            username = (chat.get("username") or "").lstrip("@").strip().lower()
            if allowed_usernames and username and username not in allowed_usernames:
                continue
            chats[int(chat_id)] = {
                "chat_id": int(chat_id),
                "username": username,
                "first_name": chat.get("first_name") or "",
                "type": chat.get("type") or "",
            }

        if not chats:
            print("❌ Не нашёл подходящих чатов в updates. Убедитесь что нужные аккаунты написали боту /start.")
            return []

        print("\n✅ Найденные чаты:")
        for c in chats.values():
            u = f"@{c['username']}" if c.get("username") else "(no username)"
            print(f"  - chat_id={c['chat_id']}  {u}  {c.get('first_name','')}")

        chat_ids = [str(cid) for cid in chats.keys()]
        print("\nДобавьте в .env (.env.local) файл:")
        print(f"TELEGRAM_CHAT_IDS={','.join(chat_ids)}")
        return chat_ids
    except Exception as e:
        print(f"❌ Ошибка при получении chat_id: {e}")
        import traceback
        traceback.print_exc()
        return []


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

    bot_token = settings.TELEGRAM_BOT_TOKEN

    allow_raw = (getattr(settings, "TELEGRAM_ALLOWED_USERNAMES", "") or "").strip().lower()
    allowed = {u.strip().lstrip("@").lower() for u in allow_raw.split(",") if u.strip()} if allow_raw else None

    print(f"\nТекущие настройки:")
    print(f"  TELEGRAM_BOT_TOKEN: {'✅ Установлен' if bot_token else '❌ Не установлен'}")
    if allowed:
        print(f"  TELEGRAM_ALLOWED_USERNAMES: {', '.join(sorted(allowed))}")

    if not bot_token:
        print("\nДобавьте токен в .env/.env.local:")
        print("TELEGRAM_BOT_TOKEN=ваш_токен_бота")
        print("\nПосле этого напишите боту /start с нужных аккаунтов.")
        return

    print("\n" + "=" * 60)
    print("Получение chat_id из getUpdates...")
    print("=" * 60)

    chat_ids = await get_chat_ids(bot_token, allowed_usernames=allowed)

    # Тестовая отправка
    if chat_ids:
        print("\n" + "=" * 60)
        print("Тестовая отправка сообщения...")
        print("=" * 60)

        for cid in chat_ids:
            await test_telegram_send(bot_token, cid)

    print("\n" + "=" * 60)
    print("✅ Настройка завершена!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
