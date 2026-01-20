# Настройка OAuth (Google, Yandex, VK)

## Что добавлено

✅ **OAuth регистрация и вход** через:
- Google
- Yandex  
- VK

✅ **Сквозная регистрация** - пользователь может зарегистрироваться и войти через социальные сети

## Установка зависимостей

```bash
pip install authlib httpx
```

Или установите все зависимости:
```bash
pip install -r requirements.txt
```

## Настройка OAuth приложений

### 1. Google OAuth

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. Включите **Google+ API**
4. Перейдите в **Credentials** → **Create Credentials** → **OAuth client ID**
5. Выберите **Web application**
6. Добавьте **Authorized redirect URIs**:
   ```
   http://localhost:8080/auth/oauth/google/callback
   https://ваш-домен.ru/auth/oauth/google/callback
   ```
7. Скопируйте **Client ID** и **Client Secret**

### 2. Yandex OAuth

1. Перейдите в [Yandex OAuth](https://oauth.yandex.ru/)
2. Нажмите **"Создать новое приложение"**
3. Заполните форму:
   - Название: XK Media
   - Платформы: Web-сервисы
   - Callback URI: `http://localhost:8080/auth/oauth/yandex/callback`
4. После создания скопируйте **ID приложения** и **Пароль**

### 3. VK OAuth

1. Перейдите в [VK Developers](https://vk.com/apps?act=manage)
2. Создайте новое приложение
3. Выберите тип: **Веб-сайт**
4. В настройках приложения:
   - Добавьте **Redirect URI**: `http://localhost:8080/auth/oauth/vk/callback`
   - Включите **Email** в правах доступа
5. Скопируйте **Application ID** и **Secure key**

## Настройка переменных окружения

Добавьте в `.env` файл:

```env
# OAuth Providers
BASE_URL=http://localhost:8080

# Google OAuth
GOOGLE_CLIENT_ID=ваш-google-client-id
GOOGLE_CLIENT_SECRET=ваш-google-client-secret

# Yandex OAuth
YANDEX_CLIENT_ID=ваш-yandex-client-id
YANDEX_CLIENT_SECRET=ваш-yandex-client-secret

# VK OAuth
VK_CLIENT_ID=ваш-vk-client-id
VK_CLIENT_SECRET=ваш-vk-client-secret
```

## Обновление базы данных

После добавления OAuth полей в модель User, нужно обновить базу:

```python
# Запустите скрипт обновления БД
python -c "from app.db import init_db; init_db()"
```

Или вручную через SQL:

```sql
ALTER TABLE users ADD COLUMN oauth_provider VARCHAR(20);
ALTER TABLE users ADD COLUMN oauth_provider_id VARCHAR(100);
ALTER TABLE users ADD COLUMN oauth_email VARCHAR(255);

CREATE INDEX IF NOT EXISTS ix_users_oauth_provider ON users(oauth_provider);
CREATE INDEX IF NOT EXISTS ix_users_oauth_provider_id ON users(oauth_provider_id);
```

## Использование

### Регистрация через OAuth

1. Перейдите на страницу регистрации: `http://localhost:8080/register`
2. Выберите роль (Рекламодатель или Площадка)
3. Нажмите на кнопку нужного провайдера:
   - "Регистрация через Google"
   - "Регистрация через Yandex"
   - "Регистрация через VK"
4. Авторизуйтесь в выбранном сервисе
5. Разрешите доступ приложению
6. Вы будете автоматически зарегистрированы и авторизованы

### Вход через OAuth

1. Перейдите на страницу входа: `http://localhost:8080/login`
2. Нажмите на кнопку нужного провайдера
3. Авторизуйтесь
4. Вы будете автоматически авторизованы

## Особенности

- **Автоматическая регистрация**: Если пользователь с таким email не существует, создается новый аккаунт
- **Связывание аккаунтов**: Если пользователь уже существует, OAuth данные привязываются к аккаунту
- **Верификация**: OAuth пользователи автоматически считаются верифицированными
- **Принятие оферты**: При регистрации через OAuth автоматически принимается текущая версия оферты

## Безопасность

- Используется **state** параметр для защиты от CSRF атак
- State хранится в памяти (в продакшене рекомендуется использовать Redis)
- Токены OAuth не сохраняются в базе данных
- Сохраняются только ID провайдера и email

## Тестирование

### Локальное тестирование

1. Настройте OAuth приложения с redirect URI: `http://localhost:8080/auth/oauth/{provider}/callback`
2. Добавьте credentials в `.env`
3. Перезапустите сервер
4. Попробуйте зарегистрироваться через OAuth

### Продакшен

1. Обновите `BASE_URL` в `.env` на реальный домен
2. Добавьте redirect URI для продакшена в настройках OAuth приложений
3. Используйте HTTPS (обязательно для OAuth)

## Troubleshooting

### Ошибка "oauth_invalid"
- State не найден или истек
- Попробуйте снова

### Ошибка "oauth_failed"
- Неверные credentials в `.env`
- Проверьте Client ID и Client Secret

### Ошибка "oauth_no_email"
- Провайдер не вернул email
- Проверьте права доступа в настройках OAuth приложения

### Redirect URI mismatch
- Убедитесь, что redirect URI в настройках OAuth приложения точно совпадает с `BASE_URL/auth/oauth/{provider}/callback`

## API Endpoints

- `GET /auth/oauth/google?role=advertiser` - Начать авторизацию через Google
- `GET /auth/oauth/google/callback` - Callback от Google
- `GET /auth/oauth/yandex?role=advertiser` - Начать авторизацию через Yandex
- `GET /auth/oauth/yandex/callback` - Callback от Yandex
- `GET /auth/oauth/vk?role=advertiser` - Начать авторизацию через VK
- `GET /auth/oauth/vk/callback` - Callback от VK
