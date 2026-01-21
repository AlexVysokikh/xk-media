# Статус сервера и управление

## Текущий статус

Сервер запущен в фоновом режиме на порту **8080**.

## Проверка статуса

### Windows PowerShell

```powershell
# Проверить, запущен ли сервер
Invoke-WebRequest -Uri http://localhost:8080/health

# Проверить процессы Python
Get-Process | Where-Object {$_.ProcessName -eq "python"}

# Проверить порт 8080
netstat -ano | Select-String ":8080"
```

### Проверка через браузер

Откройте в браузере:
- `http://localhost:8080/health` - проверка здоровья
- `http://localhost:8080/` - главная страница
- `http://localhost:8080/docs` - API документация

## Управление сервером

### Запуск

```powershell
cd c:/Users/avvys/Desktop/Cursor/xk-media/backend
python run_server.py
```

Или напрямую через uvicorn:
```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

### Остановка

```powershell
# Найти процесс
Get-Process | Where-Object {$_.ProcessName -eq "python"}

# Остановить все Python процессы (осторожно!)
Get-Process | Where-Object {$_.ProcessName -eq "python"} | Stop-Process -Force
```

Или нажмите `Ctrl+C` в терминале, где запущен сервер.

### Перезапуск

```powershell
# Остановить
Get-Process | Where-Object {$_.ProcessName -eq "python"} | Stop-Process -Force

# Запустить
cd c:/Users/avvys/Desktop/Cursor/xk-media/backend
python run_server.py
```

## Важно для Windows

⚠️ **`systemctl`** - это команда Linux, на Windows она не работает!

На Windows используйте:
- `Get-Process` вместо `systemctl status`
- `Stop-Process` вместо `systemctl stop`
- `Start-Process` вместо `systemctl start`

## Продакшен (для будущего)

Для продакшена на Linux сервере можно использовать:

1. **systemd service** (Linux):
```ini
[Unit]
Description=XK Media API
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/backend
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
```

2. **Nginx как reverse proxy** (опционально):
```nginx
server {
    listen 80;
    server_name xk-media.ru;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Но сейчас вы на Windows, поэтому просто используйте `python run_server.py`.
