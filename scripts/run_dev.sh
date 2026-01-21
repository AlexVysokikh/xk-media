#!/bin/bash
# ============================================
# XK Media - Development Server (Linux/Mac)
# ============================================

echo "🚀 Starting XK Media Development Server..."

# Change to backend directory
cd "$(dirname "$0")/.."

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt --quiet

# Run server
echo ""
echo "✅ Server starting at http://localhost:8000"
echo "📖 API docs: http://localhost:8000/docs"
echo "👤 Admin: admin@xk-media.ru / admin123"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
