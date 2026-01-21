# Быстрая настройка OAuth - пошаговая инструкция

## 🚀 Автоматическая настройка на сервере

Выполните на сервере:

```bash
cd /var/www/xk-media-backend
git pull
chmod +x scripts/setup_oauth_interactive.sh
./scripts/setup_oauth_interactive.sh
```

Скрипт проведет вас через настройку всех провайдеров и автоматически обновит `.env` файл.

---

## 📋 Или настройте вручную

### Шаг 1: Определите ваш BASE_URL

На сервере проверьте:
```bash
grep BASE_URL /var/www/xk-media-backend/.env
```

Должно быть: `BASE_URL=https://xk-media.ru` или `BASE_URL=http://109.69.21.98`

### Шаг 2: Настройте Google OAuth

1. **Откройте:** https://console.cloud.google.com/apis/credentials
2. **Создайте OAuth Client ID** (если еще нет):
   - Application type: **Web application**
   - Name: **XK Media**
   - Authorized redirect URIs: 
     ```
     https://xk-media.ru/auth/oauth/google/callback
     ```
3. **Скопируйте Client ID и Client Secret**

### Шаг 3: Настройте Yandex OAuth

1. **Откройте:** https://oauth.yandex.ru/
2. **Создайте приложение:**
   - Название: **XK Media**
   - Redirect URI: `https://xk-media.ru/auth/oauth/yandex/callback`
   - Права: **Доступ к email адресу**
3. **Скопируйте ID приложения и Пароль**

### Шаг 4: Настройте VK OAuth

1. **Откройте:** https://dev.vk.com/
2. **Создайте приложение:**
   - Тип: **Веб-сайт**
   - Redirect URI: `https://xk-media.ru/auth/oauth/vk/callback`
3. **Скопируйте ID приложения и Защищенный ключ**

### Шаг 5: Добавьте в .env на сервере

```bash
cd /var/www/xk-media-backend
nano .env
```

Добавьте/обновите:
```env
BASE_URL=https://xk-media.ru

GOOGLE_CLIENT_ID=ваш_google_client_id
GOOGLE_CLIENT_SECRET=ваш_google_client_secret

YANDEX_CLIENT_ID=ваш_yandex_id
YANDEX_CLIENT_SECRET=ваш_yandex_secret

VK_CLIENT_ID=ваш_vk_id
VK_CLIENT_SECRET=ваш_vk_secret
```

Сохраните (`Ctrl+O`, `Enter`, `Ctrl+X`)

### Шаг 6: Перезапустите приложение

```bash
systemctl restart xk-media
```

### Шаг 7: Проверьте

1. Откройте: https://xk-media.ru/admin/settings
2. Нажмите **Проверить OAuth**
3. Попробуйте авторизоваться: https://xk-media.ru/login

---

## ✅ Готово!

После выполнения всех шагов OAuth будет работать.

**Важно:** Redirect URIs должны точно совпадать (включая http/https и порт)!
