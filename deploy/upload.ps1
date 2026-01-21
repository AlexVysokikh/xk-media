# =============================================================================
# XK Media Upload Script for Windows
# Uploads files to Beget VPS via SCP
# =============================================================================

$SERVER = "212.8.229.68"
$USER = "root"
$REMOTE_DIR = "/opt/xk-media"
$LOCAL_DIR = Split-Path -Parent $PSScriptRoot

Write-Host "🚀 XK Media Deployment Upload" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Server: $USER@$SERVER" -ForegroundColor Yellow
Write-Host "Remote: $REMOTE_DIR" -ForegroundColor Yellow
Write-Host "Local:  $LOCAL_DIR" -ForegroundColor Yellow
Write-Host ""

# Check if ssh is available
if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
    Write-Host "❌ SSH not found. Please install OpenSSH." -ForegroundColor Red
    exit 1
}

# Create remote directory
Write-Host "📁 Creating remote directory..." -ForegroundColor Green
ssh "$USER@$SERVER" "mkdir -p $REMOTE_DIR"

# Upload files (excluding venv, __pycache__, .db, .env)
Write-Host "📤 Uploading application files..." -ForegroundColor Green

# Create a temporary exclude file
$excludeFile = "$env:TEMP\rsync_exclude.txt"
@"
.venv/
__pycache__/
*.pyc
*.pyo
*.db
.env
.git/
*.log
"@ | Out-File -FilePath $excludeFile -Encoding UTF8

# Use SCP to upload (rsync would be better but not always available on Windows)
# We'll upload folder by folder

# Upload app folder
Write-Host "  -> app/" -ForegroundColor Gray
scp -r "$LOCAL_DIR\app" "$USER@$SERVER`:$REMOTE_DIR/"

# Upload deploy folder
Write-Host "  -> deploy/" -ForegroundColor Gray
scp -r "$LOCAL_DIR\deploy" "$USER@$SERVER`:$REMOTE_DIR/"

# Upload requirements.txt
Write-Host "  -> requirements.txt" -ForegroundColor Gray
scp "$LOCAL_DIR\requirements.txt" "$USER@$SERVER`:$REMOTE_DIR/"

# Upload scripts folder if exists
if (Test-Path "$LOCAL_DIR\scripts") {
    Write-Host "  -> scripts/" -ForegroundColor Gray
    scp -r "$LOCAL_DIR\scripts" "$USER@$SERVER`:$REMOTE_DIR/"
}

Write-Host ""
Write-Host "✅ Upload complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Now run the deployment script on the server:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  ssh $USER@$SERVER" -ForegroundColor Cyan
Write-Host "  cd $REMOTE_DIR" -ForegroundColor Cyan
Write-Host "  chmod +x deploy/deploy.sh" -ForegroundColor Cyan
Write-Host "  ./deploy/deploy.sh" -ForegroundColor Cyan
Write-Host ""
