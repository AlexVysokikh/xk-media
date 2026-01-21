#!/usr/bin/env python
"""Скрипт для запуска сервера"""
import uvicorn

if __name__ == "__main__":
    print("🚀 Запуск XK Media сервера...")
    print("📍 Доступен по адресу: http://localhost:8080")
    print("📚 API документация: http://localhost:8080/docs")
    print("=" * 50)
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8080,
        reload=True,
        log_level="info"
    )
