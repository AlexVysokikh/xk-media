#!/bin/bash
# Скрипт для проверки статуса сервера

echo "=== Проверка статуса сервиса xk-media ==="
sudo systemctl status xk-media --no-pager -l

echo ""
echo "=== Последние 50 строк логов ==="
sudo journalctl -u xk-media -n 50 --no-pager

echo ""
echo "=== Проверка порта 8080 ==="
sudo netstat -tlnp | grep 8080 || ss -tlnp | grep 8080

echo ""
echo "=== Проверка процесса Python ==="
ps aux | grep -E "uvicorn|python.*main.py" | grep -v grep

echo ""
echo "=== Проверка конфигурации Nginx ==="
sudo nginx -t

echo ""
echo "=== Последние ошибки Nginx ==="
sudo tail -n 20 /var/log/nginx/error.log
