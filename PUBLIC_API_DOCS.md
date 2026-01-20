# Публичный API для омниканальности (Digital + Оффлайн)

## Обзор

Публичный API позволяет интегрировать digital и оффлайн каналы:
- **QR-коды** на ТВ-экранах → переход на страницу с рекламодателями
- **ТВ-плееры** → получение контента в JSON формате
- **Мобильные приложения** → доступ к контенту через API
- **Веб-сайты** → встраивание контента

## Endpoints

### 1. Получить контент для ТВ-экрана

**GET** `/api/public/screen/{identifier}`

Получить контент (рекламодатели) для ТВ-экрана по коду или ID.

**Параметры:**
- `identifier` (path) - код ТВ или ID ТВ
- `format` (query, optional) - формат ответа: `json` (по умолчанию) или `html`

**Примеры:**
```bash
# По коду ТВ
GET /api/public/screen/tv-abc123

# По ID ТВ
GET /api/public/screen/42

# HTML формат (редирект)
GET /api/public/screen/tv-abc123?format=html
```

**Ответ (JSON):**
```json
{
  "tv_id": 1,
  "tv_code": "tv-abc123",
  "tv_name": "ТВ в кофейне",
  "venue_name": "Кофейня Рассвет",
  "address": "ул. Ленина, 10",
  "city": "Москва",
  "links": [
    {
      "id": 1,
      "title": "Скидка 20% на первый заказ",
      "url": "https://example.com/promo",
      "description": "Используйте промокод WELCOME20",
      "image_url": "https://example.com/image.jpg",
      "position": 0,
      "advertiser_name": "ООО Реклама"
    }
  ],
  "content_version": 1704067200,
  "updated_at": "2024-01-01T12:00:00"
}
```

**Использование:**
- ТВ-плееры могут кешировать контент и проверять `content_version` для обновлений
- Мобильные приложения могут использовать JSON для отображения
- Веб-сайты могут использовать HTML формат для редиректа

---

### 2. Получить контент по QR-коду

**GET** `/api/public/qr/{qr_code}`

Получить контент по QR-коду. Поддерживает различные форматы QR-кодов.

**Параметры:**
- `qr_code` (path) - QR-код (может быть код ТВ, ID, или формат "tv-{code}")
- `redirect` (query, optional) - редирект на HTML страницу (по умолчанию `true`)

**Примеры:**
```bash
# QR-код с кодом ТВ
GET /api/public/qr/tv-abc123

# QR-код с ID
GET /api/public/qr/42

# QR-код формата "tv-{code}"
GET /api/public/qr/tv-abc123

# JSON ответ без редиректа
GET /api/public/qr/tv-abc123?redirect=false
```

**Ответ (при redirect=false):**
```json
{
  "redirect_url": "/tv/tv-abc123",
  "tv_data": {
    "tv_id": 1,
    "tv_code": "tv-abc123",
    ...
  },
  "qr_code": "tv-abc123"
}
```

---

### 3. Отправить статистику от ТВ-плеера

**POST** `/api/public/stats`

Отправить статистику показов, кликов и просмотров от ТВ-плеера или веб-страницы.

**Тело запроса:**
```json
{
  "tv_id": 1,
  "tv_code": "tv-abc123",  // опционально, если не указан tv_id
  "link_id": 5,            // опционально, для кликов/показов конкретной ссылки
  "event_type": "click",    // "impression", "click", "view"
  "timestamp": "2024-01-01T12:00:00",  // опционально
  "device_info": "Android TV",          // опционально
  "user_agent": "Mozilla/5.0..."        // опционально
}
```

**Типы событий:**
- `impression` - показ ссылки на экране
- `click` - клик по ссылке (переход)
- `view` - просмотр страницы с рекламодателями

**Ответ:**
```json
{
  "status": "ok",
  "message": "Статистика сохранена",
  "tv_id": 1,
  "event_type": "click",
  "timestamp": "2024-01-01T12:00:00"
}
```

**Использование:**
- ТВ-плееры отправляют статистику показов
- Веб-страница автоматически отслеживает клики через JavaScript
- Мобильные приложения могут отправлять статистику просмотров

---

### 4. Проверить версию контента

**GET** `/api/public/screen/{identifier}/version`

Получить только версию контента для проверки обновлений. Используется для оптимизации - клиент может проверить версию перед загрузкой полного контента.

**Пример:**
```bash
GET /api/public/screen/tv-abc123/version
```

**Ответ:**
```json
{
  "tv_id": 1,
  "tv_code": "tv-abc123",
  "content_version": 1704067200,
  "updated_at": "2024-01-01T12:00:00"
}
```

**Использование:**
- ТВ-плеер проверяет версию каждые 5 минут
- Если версия изменилась, загружает полный контент
- Экономит трафик и ускоряет работу

---

## HTML Страница

**GET** `/tv/{tv_code}`

Публичная HTML страница для пользователей, которые отсканировали QR-код.

**Особенности:**
- Автоматическое отслеживание просмотров и кликов
- Адаптивный дизайн для мобильных устройств
- Поддержка доступа по коду или ID

**Пример:**
```
https://xk-media.ru/tv/tv-abc123
https://xk-media.ru/tv/42
```

---

## Примеры использования

### ТВ-плеер (Python)

```python
import requests
import time

tv_code = "tv-abc123"
base_url = "https://xk-media.ru"

# Проверка версии контента
version_response = requests.get(f"{base_url}/api/public/screen/{tv_code}/version")
current_version = version_response.json()["content_version"]

# Загрузка контента
content_response = requests.get(f"{base_url}/api/public/screen/{tv_code}")
content = content_response.json()

# Отображение ссылок
for link in content["links"]:
    display_link(link["title"], link["url"], link["image_url"])

# Отправка статистики показа
requests.post(f"{base_url}/api/public/stats", json={
    "tv_id": content["tv_id"],
    "link_id": link["id"],
    "event_type": "impression"
})
```

### Мобильное приложение (JavaScript)

```javascript
// Получение контента по QR-коду
async function getContentFromQR(qrCode) {
    const response = await fetch(`/api/public/qr/${qrCode}?redirect=false`);
    const data = await response.json();
    return data.tv_data;
}

// Отправка статистики клика
async function trackClick(tvId, linkId) {
    await fetch('/api/public/stats', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            tv_id: tvId,
            link_id: linkId,
            event_type: 'click'
        })
    });
}
```

### Веб-сайт (встраивание)

```html
<!-- Встраивание контента ТВ на веб-сайт -->
<div id="tv-content"></div>

<script>
async function loadTVContent(tvCode) {
    const response = await fetch(`/api/public/screen/${tvCode}`);
    const content = await response.json();
    
    const container = document.getElementById('tv-content');
    content.links.forEach(link => {
        const linkElement = document.createElement('a');
        linkElement.href = link.url;
        linkElement.textContent = link.title;
        container.appendChild(linkElement);
    });
}
</script>
```

---

## Омниканальность: Digital + Оффлайн

### Сценарий использования:

1. **Оффлайн**: Пользователь видит ТВ-экран в кофейне с QR-кодом
2. **Digital**: Пользователь сканирует QR-код → открывается страница `/tv/{code}`
3. **Омниканальность**: Пользователь видит рекламодателей, кликает → переход на сайт рекламодателя
4. **Аналитика**: Все действия отслеживаются через API статистики

### Преимущества:

- ✅ Единая точка входа для всех каналов
- ✅ Отслеживание конверсий (оффлайн → digital)
- ✅ Аналитика по всем каналам
- ✅ Гибкая интеграция с любыми системами

---

## Безопасность

- Публичный API не требует аутентификации
- Доступ только к активным ТВ (`is_active = True`)
- Rate limiting рекомендуется для продакшена
- Валидация всех входных данных

---

## Ограничения

- Максимальный размер ответа: 1MB
- Rate limit: рекомендуется 100 запросов/минуту на IP
- Кеширование: контент можно кешировать на стороне клиента по `content_version`
