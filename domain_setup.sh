#!/bin/bash
"""
GuardianShield Automated Domain Setup Script
============================================

This script automates the domain integration process for GuardianShield.
Run this on your fresh Ubuntu server after purchasing your domain.

Usage: bash domain_setup.sh your-domain.com your-server-ip

Author: GitHub Copilot
Date: December 29, 2025
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN=${1:-"guardianshield.io"}
SERVER_IP=${2:-$(curl -s ifconfig.me)}
PROJECT_DIR="/var/www/guardianshield-agents"

echo -e "${BLUE}🚀 GuardianShield Domain Integration Setup${NC}"
echo -e "${BLUE}===========================================${NC}"
echo -e "${GREEN}Domain: ${DOMAIN}${NC}"
echo -e "${GREEN}Server IP: ${SERVER_IP}${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: System Update and Dependencies
print_status "Step 1: Updating system and installing dependencies..."
apt update && apt upgrade -y
apt install -y docker.io docker-compose nginx certbot python3-certbot-nginx git curl wget unzip

# Start Docker
systemctl start docker
systemctl enable docker
print_success "System updated and dependencies installed"

# Step 2: Configure Firewall
print_status "Step 2: Configuring firewall..."
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw --force enable
print_success "Firewall configured"

# Step 3: Clone GuardianShield Repository
print_status "Step 3: Setting up GuardianShield project..."
if [ -d "$PROJECT_DIR" ]; then
    print_warning "Project directory exists, pulling latest changes..."
    cd $PROJECT_DIR
    git pull
else
    mkdir -p /var/www
    cd /var/www
    print_status "Please enter your GitHub repository URL:"
    read -p "Repository URL (https://github.com/username/guardianshield-agents.git): " REPO_URL
    git clone $REPO_URL guardianshield-agents
    cd guardianshield-agents
fi

# Set permissions
chown -R www-data:www-data $PROJECT_DIR
chmod -R 755 $PROJECT_DIR
print_success "GuardianShield project setup complete"

# Step 4: Environment Configuration
print_status "Step 4: Configuring environment variables..."
if [ ! -f .env ]; then
    cp .env.example .env
    
    # Generate secure secrets
    JWT_SECRET=$(openssl rand -base64 32)
    API_KEY=$(openssl rand -hex 16)
    DB_PASSWORD=$(openssl rand -base64 16)
    
    # Update .env file
    sed -i "s/DOMAIN=.*/DOMAIN=$DOMAIN/" .env
    sed -i "s|API_URL=.*|API_URL=https://api.$DOMAIN|" .env
    sed -i "s|FRONTEND_URL=.*|FRONTEND_URL=https://app.$DOMAIN|" .env
    sed -i "s/JWT_SECRET=.*/JWT_SECRET=$JWT_SECRET/" .env
    sed -i "s/API_KEY=.*/API_KEY=$API_KEY/" .env
    sed -i "s/DB_PASSWORD=.*/DB_PASSWORD=$DB_PASSWORD/" .env
    
    print_success "Environment configured with secure secrets"
else
    print_warning ".env file already exists, skipping..."
fi

# Step 5: Nginx Configuration
print_status "Step 5: Configuring Nginx reverse proxy..."
rm -f /etc/nginx/sites-enabled/default

cat > /etc/nginx/sites-available/guardianshield << EOF
# Main domain - Landing page
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

# App subdomain - Main application
server {
    listen 80;
    server_name app.$DOMAIN;
    
    location / {
        proxy_pass http://localhost:3001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

# API subdomain - Backend API
server {
    listen 80;
    server_name api.$DOMAIN;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}

# Admin subdomain
server {
    listen 80;
    server_name admin.$DOMAIN;
    
    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/guardianshield /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
print_success "Nginx configured successfully"

# Step 6: Deploy with Docker Compose
print_status "Step 6: Deploying GuardianShield services..."
cd $PROJECT_DIR

# Check if production compose file exists
if [ -f docker-compose.production.yml ]; then
    COMPOSE_FILE="docker-compose.production.yml"
elif [ -f docker-compose.prod.yml ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
else
    COMPOSE_FILE="docker-compose.yml"
    print_warning "Using default docker-compose.yml file"
fi

docker-compose -f $COMPOSE_FILE up -d
sleep 10  # Wait for services to start

print_success "GuardianShield services deployed"

# Step 7: SSL Certificate Installation
print_status "Step 7: Installing SSL certificates..."
print_warning "Make sure your domain DNS is pointing to $SERVER_IP before continuing!"
read -p "Press Enter when DNS is configured and propagated..."

certbot --nginx --non-interactive --agree-tos --email admin@$DOMAIN \
    -d $DOMAIN \
    -d www.$DOMAIN \
    -d app.$DOMAIN \
    -d api.$DOMAIN \
    -d admin.$DOMAIN

# Set up automatic renewal
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
print_success "SSL certificates installed and auto-renewal configured"

# Step 8: Setup Backup System
print_status "Step 8: Setting up backup system..."
cat > /root/backup-guardianshield.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
mkdir -p $BACKUP_DIR

# Database backup
if docker ps | grep -q guardianshield-db; then
    docker exec guardianshield-db pg_dump -U postgres guardianshield > $BACKUP_DIR/db_$DATE.sql
fi

# Application backup
tar -czf $BACKUP_DIR/app_$DATE.tar.gz /var/www/guardianshield-agents --exclude=node_modules --exclude=.git

# Clean old backups (keep 7 days)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /root/backup-guardianshield.sh
(crontab -l 2>/dev/null; echo "0 2 * * * /root/backup-guardianshield.sh") | crontab -
print_success "Backup system configured"

# Step 9: Health Check
print_status "Step 9: Performing health checks..."
sleep 5

echo "Checking services..."
docker-compose -f $COMPOSE_FILE ps

echo ""
echo "Testing endpoints..."
curl -s -o /dev/null -w "Main site (%{url_effective}): %{http_code}\n" http://localhost:3000/ || echo "Main site: Not responding"
curl -s -o /dev/null -w "API (%{url_effective}): %{http_code}\n" http://localhost:8000/health || echo "API: Not responding"
curl -s -o /dev/null -w "Admin (%{url_effective}): %{http_code}\n" http://localhost:8001/ || echo "Admin: Not responding"

# Step 10: Final Instructions
echo ""
echo -e "${GREEN}🎉 GUARDIANSHIELD DOMAIN INTEGRATION COMPLETE! 🎉${NC}"
echo -e "${GREEN}=================================================${NC}"
echo ""
echo -e "${BLUE}Your GuardianShield is now live at:${NC}"
echo -e "${GREEN}• Main Site: https://$DOMAIN${NC}"
echo -e "${GREEN}• Web App:   https://app.$DOMAIN${NC}"
echo -e "${GREEN}• API:       https://api.$DOMAIN${NC}"
echo -e "${GREEN}• Admin:     https://admin.$DOMAIN${NC}"
echo ""
echo -e "${YELLOW}DNS Configuration Required:${NC}"
echo "Set these A records at your domain registrar:"
echo -e "${BLUE}@        A    $SERVER_IP${NC}"
echo -e "${BLUE}www      A    $SERVER_IP${NC}"
echo -e "${BLUE}app      A    $SERVER_IP${NC}"
echo -e "${BLUE}api      A    $SERVER_IP${NC}"
echo -e "${BLUE}admin    A    $SERVER_IP${NC}"
echo ""
echo -e "${YELLOW}Useful Commands:${NC}"
echo -e "${BLUE}• View logs: docker-compose -f $COMPOSE_FILE logs -f${NC}"
echo -e "${BLUE}• Restart:   docker-compose -f $COMPOSE_FILE restart${NC}"
echo -e "${BLUE}• Stop:      docker-compose -f $COMPOSE_FILE down${NC}"
echo -e "${BLUE}• Backup:    /root/backup-guardianshield.sh${NC}"
echo ""
echo -e "${GREEN}Setup completed successfully! 🚀${NC}"