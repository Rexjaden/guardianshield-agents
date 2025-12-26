#!/bin/bash
# GuardianShield Production Deployment Script
# Deploy to DigitalOcean with SSL certificates for both domains

set -e

echo "🛡️  GuardianShield Production Deployment Starting..."

# Configuration
DOMAIN1="www.guardian-shield.io"
DOMAIN2="guardianshield-eth.com"
EMAIL="claude@guardian-shield.io"
DB_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET=$(openssl rand -base64 64)

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)"
   exit 1
fi

echo "📋 Setting up directories and permissions..."
mkdir -p /opt/guardianshield/{logs,data,ssl,backups}
chmod 755 /opt/guardianshield
chmod 700 /opt/guardianshield/ssl

echo "🔧 Installing system dependencies..."
apt-get update
apt-get install -y docker.io docker-compose-plugin nginx certbot python3-certbot-nginx

# Enable and start Docker
systemctl enable docker
systemctl start docker

echo "🐳 Setting up Docker environment..."
# Copy application files
cp -r . /opt/guardianshield/
cd /opt/guardianshield

# Create production environment file
cat > .env.production << EOF
# GuardianShield Production Environment
ENVIRONMENT=production
DEBUG=False

# Database Configuration
DB_HOST=db
DB_PORT=5432
DB_NAME=guardianshield_prod
DB_USER=guardianshield
DB_PASSWORD=${DB_PASSWORD}

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Security Configuration
JWT_SECRET_KEY=${JWT_SECRET}
ENCRYPTION_KEY=$(openssl rand -base64 32)

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=claude@guardian-shield.io
SMTP_PASSWORD=your_app_password_here
EMAIL_FROM=claude@guardian-shield.io

# SSL Configuration
SSL_CERT_PATH=/app/ssl/fullchain.pem
SSL_KEY_PATH=/app/ssl/privkey.pem

# Domain Configuration
PRIMARY_DOMAIN=${DOMAIN1}
SECONDARY_DOMAIN=${DOMAIN2}

# API Configuration
API_VERSION=v1
RATE_LIMIT=100
MAX_WORKERS=4

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# Backup Configuration
BACKUP_RETENTION_DAYS=30
BACKUP_S3_BUCKET=guardianshield-backups
EOF

echo "🔒 Obtaining SSL certificates..."
# Stop nginx if running
systemctl stop nginx 2>/dev/null || true

# Get certificates for both domains
certbot certonly --standalone --non-interactive --agree-tos --email ${EMAIL} -d ${DOMAIN1}
certbot certonly --standalone --non-interactive --agree-tos --email ${EMAIL} -d ${DOMAIN2}

# Copy certificates to app directory
cp /etc/letsencrypt/live/${DOMAIN1}/fullchain.pem /opt/guardianshield/ssl/
cp /etc/letsencrypt/live/${DOMAIN1}/privkey.pem /opt/guardianshield/ssl/
chown -R 1000:1000 /opt/guardianshield/ssl/

echo "🚀 Starting GuardianShield services..."
docker compose -f docker-compose.production.yml up -d

echo "⏳ Waiting for services to initialize..."
sleep 30

echo "🔍 Checking service health..."
docker compose -f docker-compose.production.yml ps

# Test application endpoints
echo "🧪 Testing application endpoints..."
curl -f http://localhost:8000/api/health || echo "Warning: Health check failed"

echo "📊 Setting up monitoring..."
# Create Prometheus config
cat > prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'guardianshield'
    static_configs:
      - targets: ['app:8000']
    metrics_path: /api/metrics
EOF

echo "🔄 Setting up automatic certificate renewal..."
# Add cron job for certificate renewal
cat > /etc/cron.d/guardianshield-ssl << EOF
0 12 * * * root certbot renew --quiet && docker compose -f /opt/guardianshield/docker-compose.production.yml restart nginx
EOF

echo "📝 Creating backup script..."
cat > /opt/guardianshield/backup.sh << EOF
#!/bin/bash
# GuardianShield Backup Script
DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/guardianshield/backups"

# Database backup
docker compose -f /opt/guardianshield/docker-compose.production.yml exec -T db pg_dump -U guardianshield guardianshield_prod > \${BACKUP_DIR}/db_backup_\${DATE}.sql

# Compress and clean old backups
gzip \${BACKUP_DIR}/db_backup_\${DATE}.sql
find \${BACKUP_DIR} -name "*.gz" -mtime +30 -delete

echo "Backup completed: \${BACKUP_DIR}/db_backup_\${DATE}.sql.gz"
EOF

chmod +x /opt/guardianshield/backup.sh

# Add daily backup cron job
echo "0 2 * * * root /opt/guardianshield/backup.sh" >> /etc/cron.d/guardianshield-ssl

echo "🔧 Final system configuration..."
# Configure firewall
ufw allow 22/tcp
ufw allow 80/tcp  
ufw allow 443/tcp
ufw --force enable

# Set up log rotation
cat > /etc/logrotate.d/guardianshield << EOF
/opt/guardianshield/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    copytruncate
}
EOF

echo "✅ GuardianShield Production Deployment Complete!"
echo ""
echo "🌐 Your GuardianShield instance is now running on:"
echo "   Primary: https://${DOMAIN1}"
echo "   Web3:    https://${DOMAIN2}"
echo ""
echo "📊 Management URLs:"
echo "   Health Check: https://${DOMAIN1}/api/health"
echo "   API Docs:     https://${DOMAIN1}/docs"
echo "   Admin Panel:  https://${DOMAIN1}/admin"
echo ""
echo "🔑 Important Information:"
echo "   Database Password: ${DB_PASSWORD}"
echo "   JWT Secret: ${JWT_SECRET}"
echo "   SSL Certificates: Auto-renewing via certbot"
echo "   Backups: Daily at 2:00 AM in /opt/guardianshield/backups"
echo ""
echo "⚠️  Please save the database password and update the SMTP password in .env.production"
echo "📧 Don't forget to configure the email app password for claude@guardian-shield.io"
echo ""
echo "🔍 To monitor:"
echo "   docker compose -f /opt/guardianshield/docker-compose.production.yml logs -f"