# Инструкция по деплою через GitHub

## Подготовка репозитория

### 1. Инициализация Git (если еще не сделано)

```bash
cd c:/Users/avvys/Desktop/Cursor/xk-media/backend
git init
git add .
git commit -m "Initial commit"
```

### 2. Подключение к GitHub

```bash
# Добавьте remote (замените на ваш репозиторий)
git remote add origin https://github.com/ваш-username/xk-media-backend.git

# Или через SSH
git remote add origin git@github.com:ваш-username/xk-media-backend.git
```

### 3. Первый push

```bash
git branch -M main
git push -u origin main
```

## Настройка GitHub Secrets

Для автоматического деплоя добавьте secrets в GitHub:

1. Перейдите в ваш репозиторий на GitHub
2. Settings → Secrets and variables → Actions
3. Добавьте следующие secrets:

### Для деплоя на сервер

- `DEPLOY_HOST` - IP адрес или домен вашего сервера (например: `123.45.67.89`)
- `DEPLOY_USER` - пользователь для SSH (например: `root` или `deploy`)
- `DEPLOY_KEY` - приватный SSH ключ для доступа к серверу
- `DEPLOY_PATH` - путь к проекту на сервере (например: `/var/www/xk-media-backend`)

### Для работы приложения (опционально, можно в .env на сервере)

- `SECRET_KEY` - секретный ключ для JWT
- `DATABASE_URL` - URL базы данных
- `YOOKASSA_SECRET_KEY` - ключ YooKassa
- И другие переменные окружения

## Настройка сервера

### 1. Подготовка сервера (Linux)

```bash
# Установка Python и зависимостей
sudo apt update
sudo apt install python3.11 python3-pip postgresql nginx

# Создание пользователя для деплоя
sudo useradd -m -s /bin/bash deploy
sudo mkdir -p /var/www/xk-media-backend
sudo chown deploy:deploy /var/www/xk-media-backend
```

### 2. Настройка SSH ключа

На вашем локальном компьютере:

```bash
# Генерация SSH ключа (если нет)
ssh-keygen -t ed25519 -C "github-deploy"

# Копирование публичного ключа на сервер
ssh-copy-id deploy@ваш-сервер
```

Добавьте приватный ключ в GitHub Secrets как `DEPLOY_KEY`.

### 3. Настройка systemd service (опционально)

Создайте файл `/etc/systemd/system/xk-media.service`:

```ini
[Unit]
Description=XK Media Backend
After=network.target postgresql.service

[Service]
Type=simple
User=deploy
WorkingDirectory=/var/www/xk-media-backend
Environment="PATH=/var/www/xk-media-backend/venv/bin"
ExecStart=/var/www/xk-media-backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Активация:

```bash
sudo systemctl daemon-reload
sudo systemctl enable xk-media
sudo systemctl start xk-media
sudo systemctl status xk-media
```

### 4. Настройка Nginx (опционально)

Создайте файл `/etc/nginx/sites-available/xk-media`:

```nginx
server {
    listen 80;
    server_name ваш-домен.ru;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Статические файлы
    location /static/ {
        alias /var/www/xk-media-backend/app/static/;
        expires 30d;
    }
}
```

Активация:

```bash
sudo ln -s /etc/nginx/sites-available/xk-media /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Автоматический деплой

После настройки:

1. **Push в main/master** автоматически запустит деплой
2. GitHub Actions выполнит:
   - Установку зависимостей
   - Запуск тестов (если есть)
   - Деплой на сервер через SSH

## Ручной деплой

Если нужно задеплоить вручную:

```bash
# На сервере
cd /var/www/xk-media-backend
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart xk-media
```

## Docker деплой (альтернатива)

Если используете Docker:

```bash
# На сервере
cd /var/www/xk-media-backend
git pull origin main
docker-compose build
docker-compose up -d
```

## Мониторинг

### Проверка статуса

```bash
# Статус сервиса
sudo systemctl status xk-media

# Логи
sudo journalctl -u xk-media -f

# Или если через Docker
docker-compose logs -f
```

### Health check

```bash
curl http://localhost:8080/health
```

## Откат изменений

Если что-то пошло не так:

```bash
# На сервере
cd /var/www/xk-media-backend
git log  # Посмотреть историю
git checkout <предыдущий-коммит>
sudo systemctl restart xk-media
```

## Безопасность

1. ✅ Используйте HTTPS (Let's Encrypt)
2. ✅ Храните секреты в GitHub Secrets, не в коде
3. ✅ Используйте сильные пароли для БД
4. ✅ Настройте firewall (откройте только нужные порты)
5. ✅ Регулярно обновляйте зависимости

## Troubleshooting

### Ошибка "Permission denied"

```bash
sudo chown -R deploy:deploy /var/www/xk-media-backend
```

### Ошибка подключения к БД

Проверьте `DATABASE_URL` в `.env` на сервере.

### Порт занят

```bash
# Найти процесс на порту 8080
sudo lsof -i :8080
# Остановить
sudo kill <PID>
```
