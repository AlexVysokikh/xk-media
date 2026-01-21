# Настройка продакшн окружения

## 1. Настройка SSL (Let's Encrypt)

### Требования:
- Домен должен указывать на IP сервера (109.69.21.98)
- Порты 80 и 443 должны быть открыты

### Выполнение:

```bash
cd /var/www/xk-media-backend
chmod +x scripts/setup_ssl.sh
./scripts/setup_ssl.sh xk-media.ru admin@xk-media.ru
```

Или вручную:

```bash
# Установка certbot
apt update
apt install -y certbot python3-certbot-nginx

# Получение сертификата
certbot --nginx -d xk-media.ru -d www.xk-media.ru --non-interactive --agree-tos --email admin@xk-media.ru

# Настройка автообновления
systemctl enable certbot.timer
systemctl start certbot.timer
```

После получения сертификата обновите конфигурацию Nginx (скрипт сделает это автоматически).

---

## 2. Смена пароля администратора

### Выполнение:

```bash
cd /var/www/xk-media-backend
source venv/bin/activate
python scripts/change_admin_password.py "новый_надежный_пароль"
```

**Важно:** Используйте надежный пароль (минимум 8 символов, буквы, цифры, спецсимволы).

---

## 3. Настройка резервного копирования базы данных

### Ручное создание бэкапа:

```bash
cd /var/www/xk-media-backend
chmod +x scripts/backup_database.sh
./scripts/backup_database.sh
```

Бэкапы сохраняются в `/var/backups/xk-media/`

### Автоматическое резервное копирование (ежедневно в 2:00):

```bash
cd /var/www/xk-media-backend
chmod +x scripts/setup_backup_cron.sh
./scripts/setup_backup_cron.sh
```

### Восстановление из бэкапа:

```bash
# Для .sql файла
gunzip /var/backups/xk-media/xk_media_backup_YYYYMMDD_HHMMSS.sql.gz
PGPASSWORD=пароль psql -h localhost -U xk_media_user -d xk_media < /var/backups/xk-media/xk_media_backup_YYYYMMDD_HHMMSS.sql

# Для .dump файла
gunzip /var/backups/xk-media/xk_media_backup_YYYYMMDD_HHMMSS.dump.gz
PGPASSWORD=пароль pg_restore -h localhost -U xk_media_user -d xk_media /var/backups/xk-media/xk_media_backup_YYYYMMDD_HHMMSS.dump
```

---

## 4. Настройка мониторинга

### Ручная проверка:

```bash
cd /var/www/xk-media-backend
chmod +x scripts/monitor.sh
./scripts/monitor.sh
```

### Автоматический мониторинг (каждые 5 минут):

```bash
cd /var/www/xk-media-backend
chmod +x scripts/setup_monitoring.sh
./scripts/setup_monitoring.sh
```

Мониторинг проверяет:
- ✅ Статус сервиса xk-media
- ✅ Статус Nginx
- ✅ Доступность базы данных
- ✅ Использование диска
- ✅ Использование памяти
- ✅ HTTP endpoint

Логи сохраняются в `/var/log/xk-media-monitor.log`

---

## Полезные команды

### Просмотр логов мониторинга:
```bash
tail -f /var/log/xk-media-monitor.log
```

### Просмотр логов бэкапов:
```bash
tail -f /var/log/xk-media-backup.log
```

### Проверка cron задач:
```bash
crontab -l
```

### Ручной запуск бэкапа:
```bash
/var/www/xk-media-backend/scripts/backup_database.sh
```

### Ручной запуск мониторинга:
```bash
/var/www/xk-media-backend/scripts/monitor.sh
```

---

## Проверка статуса всех сервисов

```bash
# Статус приложения
systemctl status xk-media

# Статус Nginx
systemctl status nginx

# Статус PostgreSQL
systemctl status postgresql

# Статус certbot (SSL)
systemctl status certbot.timer
```

---

## Обновление приложения

После обновления кода через GitHub Actions или вручную:

```bash
cd /var/www/xk-media-backend
git pull
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
systemctl restart xk-media
```
