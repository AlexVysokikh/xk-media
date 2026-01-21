# Скрипт для инициализации Git репозитория

Write-Host "🚀 Инициализация Git репозитория..." -ForegroundColor Cyan

# Инициализация Git
git init
Write-Host "✅ Git инициализирован" -ForegroundColor Green

# Добавление всех файлов
git add .
Write-Host "✅ Файлы добавлены" -ForegroundColor Green

# Первый коммит
git commit -m "Initial commit: XK Media Backend with OAuth, YooKassa, and Public API"
Write-Host "✅ Первый коммит создан" -ForegroundColor Green

Write-Host ""
Write-Host "📝 Следующие шаги:" -ForegroundColor Yellow
Write-Host "1. Создайте репозиторий на GitHub" -ForegroundColor White
Write-Host "2. Добавьте remote:" -ForegroundColor White
Write-Host "   git remote add origin https://github.com/ваш-username/xk-media-backend.git" -ForegroundColor Gray
Write-Host "3. Push в GitHub:" -ForegroundColor White
Write-Host "   git branch -M main" -ForegroundColor Gray
Write-Host "   git push -u origin main" -ForegroundColor Gray
Write-Host ""
