#!/bin/bash
# =============================================================================
# XK Media Deployment Script for Beget VPS
# Server: 212.8.229.68
# Domain: xk-media.ru
# =============================================================================

set -e

echo "🚀 Starting XK Media deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Variables
APP_DIR="/opt/xk-media"
DOMAIN="xk-media.ru"

# =============================================================================
# Step 1: Update system and install dependencies
# =============================================================================
echo -e "${YELLOW}📦 Step 1: Installing system dependencies...${NC}"

apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx git curl

# =============================================================================
# Step 2: Create application directory
# =============================================================================
echo -e "${YELLOW}📁 Step 2: Setting up application directory...${NC}"

mkdir -p $APP_DIR
cd $APP_DIR

# =============================================================================
# Step 3: Copy application files (run this after uploading files)
# =============================================================================
echo -e "${YELLOW}📂 Step 3: Application files should be uploaded to $APP_DIR${NC}"

# =============================================================================
# Step 4: Create virtual environment and install dependencies
# =============================================================================
echo -e "${YELLOW}🐍 Step 4: Setting up Python environment...${NC}"

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# =============================================================================
# Step 5: Create .env file
# =============================================================================
echo -e "${YELLOW}⚙️ Step 5: Creating environment configuration...${NC}"

if [ ! -f .env ]; then
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    cat > .env << EOF
# XK Media Production Configuration
APP_NAME=XK Media
DEBUG=False

# Database (SQLite for now, can be changed to PostgreSQL)
DATABASE_URL=sqlite:///./xk_media.db

# Security
SECRET_KEY=$SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ALGORITHM=HS256

# Admin credentials
ADMIN_EMAIL=admin@xk-media.ru
ADMIN_PASSWORD=XkMedia2024!Secure

# PayKeeper (update with real credentials)
PAYKEEPER_BASE_URL=https://demo.paykeeper.ru
PAYKEEPER_USER=demo
PAYKEEPER_PASSWORD=demo
PAYKEEPER_SECRET_WORD=your_secret_word
PAYKEEPER_RETURN_URL=https://xk-media.ru/advertiser/payments

# Base URL
BASE_URL=https://xk-media.ru
EOF
    echo -e "${GREEN}✅ .env file created${NC}"
else
    echo -e "${YELLOW}⚠️ .env file already exists, skipping...${NC}"
fi

# =============================================================================
# Step 6: Set permissions
# =============================================================================
echo -e "${YELLOW}🔒 Step 6: Setting permissions...${NC}"

chown -R www-data:www-data $APP_DIR
chmod -R 755 $APP_DIR
chmod 600 $APP_DIR/.env

# =============================================================================
# Step 7: Configure Nginx
# =============================================================================
echo -e "${YELLOW}🌐 Step 7: Configuring Nginx...${NC}"

# Remove default site
rm -f /etc/nginx/sites-enabled/default

# Copy nginx config
cp $APP_DIR/deploy/nginx.conf /etc/nginx/sites-available/xk-media.conf

# Create symlink (without SSL first for certbot)
cat > /etc/nginx/sites-available/xk-media-temp.conf << 'EOF'
server {
    listen 80;
    server_name xk-media.ru www.xk-media.ru;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/xk-media-temp.conf /etc/nginx/sites-enabled/xk-media.conf

# Create certbot directory
mkdir -p /var/www/certbot

# Test nginx config
nginx -t

# Restart nginx
systemctl restart nginx

# =============================================================================
# Step 8: Setup systemd service
# =============================================================================
echo -e "${YELLOW}⚡ Step 8: Setting up systemd service...${NC}"

cp $APP_DIR/deploy/xk-media.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable xk-media
systemctl start xk-media

# Wait for service to start
sleep 3

# Check service status
systemctl status xk-media --no-pager

# =============================================================================
# Step 9: Get SSL certificate
# =============================================================================
echo -e "${YELLOW}🔐 Step 9: Obtaining SSL certificate...${NC}"

certbot --nginx -d xk-media.ru -d www.xk-media.ru --non-interactive --agree-tos --email id1@xk-media.ru

# Now use full nginx config with SSL
ln -sf /etc/nginx/sites-available/xk-media.conf /etc/nginx/sites-enabled/xk-media.conf
nginx -t && systemctl reload nginx

# =============================================================================
# Step 10: Setup auto-renewal for SSL
# =============================================================================
echo -e "${YELLOW}🔄 Step 10: Setting up SSL auto-renewal...${NC}"

# Certbot usually sets this up automatically, but let's make sure
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -

# =============================================================================
# Done!
# =============================================================================
echo -e "${GREEN}"
echo "=============================================="
echo "  🎉 XK Media deployed successfully!"
echo "=============================================="
echo ""
echo "  URL: https://xk-media.ru"
echo ""
echo "  Admin credentials:"
echo "    Email: admin@xk-media.ru"
echo "    Password: XkMedia2024!Secure"
echo ""
echo "  Commands:"
echo "    Status:  systemctl status xk-media"
echo "    Logs:    journalctl -u xk-media -f"
echo "    Restart: systemctl restart xk-media"
echo ""
echo "=============================================="
echo -e "${NC}"
