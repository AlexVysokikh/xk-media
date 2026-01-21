# ============================================
# XK Media - Development Server (Windows)
# ============================================

Write-Host "🚀 Starting XK Media Development Server..." -ForegroundColor Cyan

# Change to backend directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Split-Path -Parent $scriptPath)

# Check if .venv exists
if (-not (Test-Path ".venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate venv
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& ".venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet

# Run server
Write-Host ""
Write-Host "✅ Server starting at http://localhost:8000" -ForegroundColor Green
Write-Host "📖 API docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "👤 Admin: admin@xk-media.ru / admin123" -ForegroundColor Green
Write-Host ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
