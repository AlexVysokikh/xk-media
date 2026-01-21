# Исправление OAuth авторизации

## Проблемы и решения

### Google OAuth - "Запрещен доступ"

**Причина:** Неправильный redirect_uri в настройках Google OAuth приложения.

**Решение:**

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Выберите ваш проект
3. Перейдите в **APIs & Services** → **Credentials**
4. Откройте ваше OAuth 2.0 Client ID
5. В разделе **Authorized redirect URIs** добавьте:
   - Для разработки: `http://localhost:8080/auth/oauth/google/callback`
   - Для продакшена: `https://xk-media.ru/auth/oauth/google/callback`
   - Или: `http://109.69.21.98/auth/oauth/google/callback` (если используете IP)

6. Сохраните изменения

**Важно:** Redirect URI должен точно совпадать с тем, что указано в коде (включая протокол http/https и порт).

### Yandex OAuth - ошибки

**Причина:** Неправильный redirect_uri в настройках Yandex OAuth приложения.

**Решение:**

1. Перейдите в [Yandex OAuth](https://oauth.yandex.ru/)
2. Откройте ваше приложение
3. В разделе **Redirect URI** добавьте:
   - Для разработки: `http://localhost:8080/auth/oauth/yandex/callback`
   - Для продакшена: `https://xk-media.ru/auth/oauth/yandex/callback`

4. Сохраните изменения

### VK OAuth - ошибки

**Причина:** Неправильный redirect_uri в настройках VK приложения.

**Решение:**

1. Перейдите в [VK Developers](https://dev.vk.com/)
2. Откройте ваше приложение
3. Перейдите в **Настройки** → **Базовые**
4. В разделе **Адрес сайта** и **Redirect URI** добавьте:
   - Для разработки: `http://localhost:8080/auth/oauth/vk/callback`
   - Для продакшена: `https://xk-media.ru/auth/oauth/vk/callback`

5. Сохраните изменения

## Проверка настроек

Убедитесь, что в `.env` файле указаны правильные значения:

```env
BASE_URL=https://xk-media.ru  # или http://109.69.21.98 для IP

GOOGLE_CLIENT_ID=ваш_client_id
GOOGLE_CLIENT_SECRET=ваш_client_secret

YANDEX_CLIENT_ID=ваш_client_id
YANDEX_CLIENT_SECRET=ваш_client_secret

VK_CLIENT_ID=ваш_client_id
VK_CLIENT_SECRET=ваш_client_secret
```

## После настройки

1. Перезапустите приложение:
   ```bash
   systemctl restart xk-media
   ```

2. Проверьте логи на наличие ошибок:
   ```bash
   journalctl -u xk-media -f
   ```

3. Попробуйте авторизоваться через OAuth

## Отладка

Если проблемы сохраняются, проверьте логи приложения. В коде добавлено логирование:
- Redirect URI, который используется
- Ошибки от провайдеров
- Статус коды ответов

Все ошибки выводятся в консоль и логи systemd.
