#!/bin/bash
# GuardianShield DigitalOcean Droplet Setup Script
# Complete automated deployment for guardian-shield.io

set -e  # Exit on any error

echo "🛡️ GUARDIANSHIELD DROPLET SETUP STARTING..."
echo "=============================================="
echo "Domain: guardian-shield.io"
echo "Date: $(date)"
echo ""

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install essential packages
echo "🔧 Installing essential packages..."
apt install -y \
    nginx \
    certbot \
    python3-certbot-nginx \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    git \
    curl \
    wget \
    unzip \
    htop \
    ufw \
    fail2ban \
    redis-server \
    postgresql \
    postgresql-contrib

# Create guardianshield user
echo "👤 Creating guardianshield user..."
useradd -m -s /bin/bash guardianshield
usermod -aG sudo guardianshield

# Create application directory
echo "📁 Setting up application directory..."
mkdir -p /var/www/guardian-shield.io
chown -R guardianshield:guardianshield /var/www/guardian-shield.io
chmod -R 755 /var/www/guardian-shield.io

# Set up Python environment
echo "🐍 Setting up Python environment..."
sudo -u guardianshield python3 -m venv /var/www/guardian-shield.io/venv
sudo -u guardianshield /var/www/guardian-shield.io/venv/bin/pip install --upgrade pip

# Install Python dependencies
echo "📚 Installing Python dependencies..."
sudo -u guardianshield /var/www/guardian-shield.io/venv/bin/pip install \
    fastapi \
    uvicorn \
    websockets \
    python-multipart \
    jinja2 \
    psutil \
    redis \
    psycopg2-binary \
    sqlalchemy \
    alembic \
    python-jose \
    passlib \
    bcrypt \
    requests

# Configure firewall
echo "🔥 Configuring firewall..."
ufw allow ssh
ufw allow 'Nginx Full'
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Configure fail2ban
echo "🛡️ Setting up fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban

# Set up log directories
echo "📝 Creating log directories..."
mkdir -p /var/log/guardianshield
chown -R guardianshield:guardianshield /var/log/guardianshield

# Download application files placeholder
echo "📥 Application files directory ready..."
echo "Next step: Upload your GuardianShield files to /var/www/guardian-shield.io/"

echo ""
echo "✅ BASIC DROPLET SETUP COMPLETE!"
echo "================================="
echo "Next steps:"
echo "1. Upload your GuardianShield application files"
echo "2. Configure domain DNS in GoDaddy"
echo "3. Run the application deployment script"
echo ""
