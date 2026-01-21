# Настройка GitHub репозитория

## Быстрый старт

### 1. Инициализация Git (если еще не сделано)

```powershell
cd c:/Users/avvys/Desktop/Cursor/xk-media/backend

# Запустите скрипт инициализации
.\init_git.ps1

# Или вручную:
git init
git add .
git commit -m "Initial commit: XK Media Backend"
```

### 2. Создайте репозиторий на GitHub

1. Перейдите на https://github.com/new
2. Название: `xk-media-backend` (или любое другое)
3. Выберите **Public** или **Private**
4. **НЕ** создавайте README, .gitignore или лицензию (они уже есть)
5. Нажмите **Create repository**

### 3. Подключите локальный репозиторий к GitHub

```powershell
# Добавьте remote (замените на ваш username и название репозитория)
git remote add origin https://github.com/ваш-username/xk-media-backend.git

# Или через SSH (если настроен)
git remote add origin git@github.com:ваш-username/xk-media-backend.git

# Проверьте
git remote -v
```

### 4. Первый push

```powershell
# Переименовать ветку в main (если нужно)
git branch -M main

# Push в GitHub
git push -u origin main
```

## Что уже настроено

✅ **GitHub Actions workflows:**
- `.github/workflows/deploy.yml` - автоматический деплой при push в main
- `.github/workflows/test.yml` - тесты и проверки при PR

✅ **Docker:**
- `Dockerfile` - образ для контейнеризации
- `docker-compose.yml` - оркестрация с PostgreSQL

✅ **.gitignore:**
- Игнорирует `.env`, базы данных, кеш и т.д.

✅ **Документация:**
- `README.md` - основная документация
- `DEPLOY.md` - инструкция по деплою

## Настройка GitHub Secrets (для деплоя)

После создания репозитория добавьте secrets:

1. Перейдите: **Settings** → **Secrets and variables** → **Actions**
2. Нажмите **New repository secret**
3. Добавьте:

| Secret | Описание | Пример |
|--------|----------|--------|
| `DEPLOY_HOST` | IP или домен сервера | `123.45.67.89` |
| `DEPLOY_USER` | SSH пользователь | `deploy` |
| `DEPLOY_SSH_KEY` | Приватный SSH ключ | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `DEPLOY_PATH` | Путь на сервере | `/var/www/xk-media-backend` |

## Структура файлов для Git

### Включено в репозиторий:
- ✅ Весь код приложения (`app/`)
- ✅ Конфигурационные файлы
- ✅ GitHub Actions workflows
- ✅ Docker файлы
- ✅ Документация

### Игнорируется (не попадет в Git):
- ❌ `.env` - переменные окружения
- ❌ `*.db`, `*.sqlite` - базы данных
- ❌ `__pycache__/` - кеш Python
- ❌ `venv/` - виртуальное окружение
- ❌ `app/static/uploads/*` - загруженные файлы

## Рабочий процесс

### Обычная разработка

```powershell
# Создать новую ветку
git checkout -b feature/new-feature

# Внести изменения
# ...

# Коммит
git add .
git commit -m "Описание изменений"

# Push
git push origin feature/new-feature

# Создать Pull Request на GitHub
```

### Деплой в продакшен

```powershell
# Смержить изменения в main
git checkout main
git merge feature/new-feature
git push origin main

# GitHub Actions автоматически задеплоит на сервер
```

## Проверка перед push

```powershell
# Проверить статус
git status

# Посмотреть что будет закоммичено
git diff --cached

# Проверить что .env не попадет в репозиторий
git check-ignore .env
# Должно вернуть: .env
```

## Полезные команды

```powershell
# Посмотреть историю
git log --oneline

# Отменить последний коммит (локально)
git reset --soft HEAD~1

# Обновить с GitHub
git pull origin main

# Посмотреть изменения
git diff
```

## Troubleshooting

### Ошибка "remote origin already exists"

```powershell
# Удалить старый remote
git remote remove origin

# Добавить заново
git remote add origin https://github.com/ваш-username/xk-media-backend.git
```

### Ошибка "failed to push"

```powershell
# Сначала pull
git pull origin main --rebase

# Затем push
git push origin main
```

### Откатить изменения

```powershell
# Отменить локальные изменения
git checkout -- .

# Откатить последний коммит
git reset --hard HEAD~1
```
