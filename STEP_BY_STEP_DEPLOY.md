# Пошаговая инструкция по деплою

## Шаг 1: Подключение к серверу

Выполните в терминале (PowerShell или cmd):

```bash
ssh root@109.69.21.98
```

Когда попросит пароль, введите: `ni*WfSCBE7eZ`

**После подключения напишите мне "подключился"**

---

## Шаг 2: Обновление системы и установка пакетов

На сервере выполните:

```bash
# Обновление системы
apt update && apt upgrade -y

# Установка необходимых пакетов
apt install -y python3 python3-pip python3-venv git nginx postgresql postgresql-contrib curl

# Проверка установки
python3 --version
git --version
nginx -v
```

**После выполнения напишите мне "пакеты установлены"**

---

## Шаг 3: Создание директории для проекта

```bash
mkdir -p /var/www/xk-media-backend
cd /var/www/xk-media-backend
pwd
```

**Должно показать: `/var/www/xk-media-backend`**

**Напишите мне "директория создана"**

---

## Шаг 4: Настройка PostgreSQL

```bash
# Переключитесь на пользователя postgres
sudo -u postgres psql
```

В psql выполните (скопируйте все команды сразу):

```sql
CREATE DATABASE xk_media;
CREATE USER xk_media_user WITH PASSWORD 'xk_media_secure_pass_2024';
GRANT ALL PRIVILEGES ON DATABASE xk_media TO xk_media_user;
\q
```

**После выхода из psql напишите мне "база данных создана"**

---

## Шаг 5: Клонирование репозитория

```bash
cd /var/www/xk-media-backend
git clone https://github.com/AlexVysokikh/xk-media.git .
ls -la
```

**Напишите мне "репозиторий склонирован"**

---

## Шаг 6: Создание виртуального окружения

```bash
cd /var/www/xk-media-backend
python3 -m venv venv
source venv/bin/activate
which python
```

**Должно показать путь с `/venv/bin/python`**

**Напишите мне "окружение создано"**

---

## Шаг 7: Установка зависимостей

```bash
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Это может занять несколько минут. Напишите мне "зависимости установлены"**

---

## Шаг 8: Создание .env файла

```bash
cd /var/www/xk-media-backend
cp .env.example .env
nano .env
```

В nano отредактируйте следующие строки (используйте стрелки для навигации, Ctrl+O для сохранения, Ctrl+X для выхода):

```env
DATABASE_URL=postgresql://xk_media_user:xk_media_secure_pass_2024@localhost:5432/xk_media
SECRET_KEY=ваш_секретный_ключ_сгенерируйте_случайную_строку
YOOKASSA_SHOP_ID=1000001
YOOKASSA_SECRET_KEY=test_eN10mBer9WHYOB8vJrixABlU2WZZdKOl6wjbvBqbqAI
BASE_URL=http://109.69.21.98
```

**Для генерации SECRET_KEY выполните:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Скопируйте результат и вставьте в SECRET_KEY.

**После сохранения напишите мне ".env настроен"**

---

## Шаг 9: Применение миграций БД

```bash
cd /var/www/xk-media-backend
source venv/bin/activate
alembic upgrade head
```

**Напишите мне "миграции применены"**

---

## Шаг 10: Тестовый запуск приложения

```bash
cd /var/www/xk-media-backend
source venv/bin/activate
python run_server.py
```

**Оставьте запущенным на 10 секунд, затем нажмите Ctrl+C**

**Напишите мне "приложение запускается"**

---

## Шаг 11: Создание SSH ключа для GitHub Actions

```bash
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_deploy -N ""
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
cat ~/.ssh/github_deploy
```

**Скопируйте ВЕСЬ вывод последней команды (включая -----BEGIN и -----END) и пришлите мне**

---

## Шаг 12: Настройка GitHub Secrets

1. Откройте: https://github.com/AlexVysokikh/xk-media/settings/secrets/actions
2. Нажмите **"New repository secret"**
3. Добавьте следующие secrets:

   - **Name:** `DEPLOY_HOST` → **Value:** `109.69.21.98`
   - **Name:** `DEPLOY_USER` → **Value:** `root`
   - **Name:** `DEPLOY_SSH_KEY` → **Value:** (приватный ключ из шага 11)
   - **Name:** `DEPLOY_PATH` → **Value:** `/var/www/xk-media-backend`

**После добавления всех secrets напишите мне "secrets добавлены"**

---

## Шаг 13: Настройка systemd сервиса

```bash
cd /var/www/xk-media-backend
cp deploy/xk-media.service /etc/systemd/system/
nano /etc/systemd/system/xk-media.service
```

Проверьте, что пути правильные (должно быть `/var/www/xk-media-backend`).

Затем:

```bash
systemctl daemon-reload
systemctl enable xk-media
systemctl start xk-media
systemctl status xk-media
```

**Напишите мне "сервис запущен" и пришлите вывод последней команды**

---

## Шаг 14: Настройка Nginx

```bash
cd /var/www/xk-media-backend
cp deploy/nginx.conf /etc/nginx/sites-available/xk-media
ln -s /etc/nginx/sites-available/xk-media /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
systemctl status nginx
```

**Напишите мне "nginx настроен"**

---

## Шаг 15: Проверка работы

Откройте в браузере: http://109.69.21.98

**Напишите мне, что видите на странице**

---

## Готово! 🎉

Теперь каждый push в ветку `main` будет автоматически деплоить изменения на сервер.
