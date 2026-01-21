# Инструкция по настройке продакшн окружения

Выполните эти команды на сервере по порядку.

## 1. Настройка SSL (Let's Encrypt)

**Важно:** Перед выполнением убедитесь, что домен `xk-media.ru` указывает на IP сервера `109.69.21.98`.

```bash
cd /var/www/xk-media-backend
git pull  # Обновить код с новыми скриптами
chmod +x scripts/setup_ssl.sh
./scripts/setup_ssl.sh xk-media.ru admin@xk-media.ru
```

Или вручную (если скрипт не работает):

```bash
apt update
apt install -y certbot python3-certbot-nginx
certbot --nginx -d xk-media.ru -d www.xk-media.ru --non-interactive --agree-tos --email admin@xk-media.ru
systemctl enable certbot.timer
systemctl start certbot.timer
```

После этого обновите `.env` файл, изменив `BASE_URL` на `https://xk-media.ru`:

```bash
nano /var/www/xk-media-backend/.env
# Измените: BASE_URL=https://xk-media.ru
systemctl restart xk-media
```

---

## 2. Смена пароля администратора

```bash
cd /var/www/xk-media-backend
source venv/bin/activate
python scripts/change_admin_password.py "ВашНовыйНадежныйПароль123!"
```

**Рекомендации для пароля:**
- Минимум 12 символов
- Буквы (заглавные и строчные)
- Цифры
- Специальные символы (!@#$%^&*)

---

## 3. Настройка резервного копирования

### Создание первого бэкапа:

```bash
cd /var/www/xk-media-backend
chmod +x scripts/backup_database.sh
./scripts/backup_database.sh
```

### Настройка автоматического бэкапа (ежедневно в 2:00):

```bash
cd /var/www/xk-media-backend
chmod +x scripts/setup_backup_cron.sh
./scripts/setup_backup_cron.sh
```

Бэкапы будут сохраняться в `/var/backups/xk-media/` и автоматически удаляться через 30 дней.

---

## 4. Настройка мониторинга

### Настройка автоматического мониторинга (каждые 5 минут):

```bash
cd /var/www/xk-media-backend
chmod +x scripts/monitor.sh scripts/setup_monitoring.sh
./scripts/setup_monitoring.sh
```

### Проверка работы мониторинга:

```bash
./scripts/monitor.sh
tail -f /var/log/xk-media-monitor.log
```

Мониторинг проверяет:
- ✅ Статус сервиса xk-media
- ✅ Статус Nginx
- ✅ Доступность базы данных
- ✅ Использование диска (предупреждение при >80%)
- ✅ Использование памяти (предупреждение при >90%)
- ✅ HTTP endpoint (health check)

---

## Проверка всех настроек

После выполнения всех шагов проверьте:

```bash
# SSL сертификат
certbot certificates

# Статус сервисов
systemctl status xk-media
systemctl status nginx
systemctl status postgresql

# Cron задачи
crontab -l

# Последние логи мониторинга
tail -20 /var/log/xk-media-monitor.log

# Последние бэкапы
ls -lh /var/backups/xk-media/
```

---

## Полезные команды

### Просмотр логов:
```bash
# Логи приложения
journalctl -u xk-media -f

# Логи мониторинга
tail -f /var/log/xk-media-monitor.log

# Логи бэкапов
tail -f /var/log/xk-media-backup.log
```

### Ручное создание бэкапа:
```bash
/var/www/xk-media-backend/scripts/backup_database.sh
```

### Ручной запуск мониторинга:
```bash
/var/www/xk-media-backend/scripts/monitor.sh
```

---

## Восстановление из бэкапа

Если нужно восстановить базу данных:

```bash
# Найдите нужный бэкап
ls -lh /var/backups/xk-media/

# Для .sql.gz файла
gunzip /var/backups/xk-media/xk_media_backup_YYYYMMDD_HHMMSS.sql.gz
PGPASSWORD=xk_media_secure_pass_2024 psql -h localhost -U xk_media_user -d xk_media < /var/backups/xk-media/xk_media_backup_YYYYMMDD_HHMMSS.sql

# Для .dump.gz файла
gunzip /var/backups/xk-media/xk_media_backup_YYYYMMDD_HHMMSS.dump.gz
PGPASSWORD=xk_media_secure_pass_2024 pg_restore -h localhost -U xk_media_user -d xk_media -c /var/backups/xk-media/xk_media_backup_YYYYMMDD_HHMMSS.dump
```

---

Готово! Все настройки применены. 🎉
