# GuardianShield Production Deployment Guide

## 🚀 Production Deployment Overview

This guide covers deploying GuardianShield to DigitalOcean with professional-grade configuration, SSL certificates, monitoring, and automated maintenance.

### 🎯 Deployment Features

- **Multi-Domain SSL**: Automatic certificates for `www.guardian-shield.io` and `guardianshield-eth.com`
- **Production Security**: Non-root containers, encrypted communications, secure headers
- **High Availability**: Load balancing, health checks, auto-restart policies
- **Professional Email**: Integrated SMTP with `claude@guardian-shield.io`
- **Automated Backups**: Daily database and data backups with retention policy
- **Monitoring**: Health checks, metrics, and real-time system monitoring
- **Auto-Scaling**: Docker Compose scaling with load balancing

## 📋 Prerequisites

### DigitalOcean Droplet Requirements
- **Minimum**: 4 GB RAM, 2 vCPUs, 80 GB SSD
- **Recommended**: 8 GB RAM, 4 vCPUs, 160 GB SSD
- **OS**: Ubuntu 22.04 LTS
- **Network**: Static IP address assigned

### Domain Configuration
Before deployment, configure DNS records:

```dns
# www.guardian-shield.io
A     www.guardian-shield.io      → YOUR_DROPLET_IP
CNAME guardian-shield.io         → www.guardian-shield.io

# guardianshield-eth.com  
A     guardianshield-eth.com     → YOUR_DROPLET_IP
CNAME www.guardianshield-eth.com → guardianshield-eth.com
```

### Email Setup
1. Create `claude@guardian-shield.io` Gmail account
2. Enable 2FA and generate App Password
3. Note the App Password for deployment configuration

## 🛠️ Quick Deployment

### 1. Server Preparation
```bash
# Connect to your DigitalOcean droplet
ssh root@YOUR_DROPLET_IP

# Update system
apt update && apt upgrade -y

# Clone GuardianShield repository
git clone https://github.com/your-org/guardianshield-agents.git
cd guardianshield-agents
```

### 2. Run Deployment Script
```bash
# Make deployment script executable
chmod +x deploy_production.sh

# Run deployment (will prompt for confirmation)
sudo ./deploy_production.sh
```

### 3. Configure Email
After deployment, update the email configuration:
```bash
# Edit production environment file
nano /opt/guardianshield/.env.production

# Update this line with your actual App Password:
SMTP_PASSWORD=your_gmail_app_password_here

# Restart services to apply changes
cd /opt/guardianshield
docker compose -f docker-compose.production.yml restart app
```

## 🔧 Manual Deployment Steps

If you prefer manual control over the deployment process:

### 1. System Dependencies
```bash
# Install Docker and Docker Compose
apt update
apt install -y docker.io docker-compose-plugin nginx certbot python3-certbot-nginx

# Enable Docker service
systemctl enable docker
systemctl start docker
```

### 2. SSL Certificate Setup
```bash
# Stop nginx if running
systemctl stop nginx

# Obtain certificates for both domains
certbot certonly --standalone --agree-tos --email claude@guardian-shield.io -d www.guardian-shield.io
certbot certonly --standalone --agree-tos --email claude@guardian-shield.io -d guardianshield-eth.com
```

### 3. Application Setup
```bash
# Create application directory
mkdir -p /opt/guardianshield/{logs,data,ssl,backups}

# Copy application files
cp -r . /opt/guardianshield/
cd /opt/guardianshield

# Copy SSL certificates
cp /etc/letsencrypt/live/www.guardian-shield.io/fullchain.pem ssl/
cp /etc/letsencrypt/live/www.guardian-shield.io/privkey.pem ssl/
chown -R 1000:1000 ssl/

# Create production environment file (copy from template)
cp .env.production.template .env.production
```

### 4. Configure Environment
Edit `/opt/guardianshield/.env.production`:
```bash
# Generate secure passwords
DB_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET=$(openssl rand -base64 64)
ENCRYPTION_KEY=$(openssl rand -base64 32)

# Update environment file with generated values
# Set your Gmail App Password for SMTP_PASSWORD
```

### 5. Start Services
```bash
# Start all services
docker compose -f docker-compose.production.yml up -d

# Check status
docker compose -f docker-compose.production.yml ps
```

## 📊 Production Management

### Daily Operations
Use the management script for common tasks:

```bash
# Make management script executable
chmod +x /opt/guardianshield/manage_production.sh

# Check system status
sudo /opt/guardianshield/manage_production.sh status

# View real-time logs
sudo /opt/guardianshield/manage_production.sh logs

# Create manual backup
sudo /opt/guardianshield/manage_production.sh backup

# Scale application (increase performance)
sudo /opt/guardianshield/manage_production.sh scale 6
```

### Monitoring Commands
```bash
# Real-time monitoring dashboard
sudo /opt/guardianshield/manage_production.sh monitor

# Security scan
sudo /opt/guardianshield/manage_production.sh security-scan

# System cleanup
sudo /opt/guardianshield/manage_production.sh cleanup
```

### Update Process
```bash
# Update application code and restart
sudo /opt/guardianshield/manage_production.sh update

# Manual update process:
cd /opt/guardianshield
git pull
docker compose -f docker-compose.production.yml build --no-cache
docker compose -f docker-compose.production.yml up -d
```

## 🔒 Security Configuration

### Firewall Setup
```bash
# Configure UFW firewall
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP (redirects to HTTPS)
ufw allow 443/tcp   # HTTPS
ufw --force enable
```

### SSL Certificate Auto-Renewal
Certificates automatically renew via cron job:
```cron
# /etc/cron.d/guardianshield-ssl
0 12 * * * root certbot renew --quiet && docker compose -f /opt/guardianshield/docker-compose.production.yml restart nginx
```

### Backup Strategy
- **Automatic**: Daily backups at 2:00 AM
- **Retention**: 30 days
- **Location**: `/opt/guardianshield/backups/`
- **Contents**: Database dump + application data

Manual backup:
```bash
sudo /opt/guardianshield/manage_production.sh backup
```

Restore from backup:
```bash
sudo /opt/guardianshield/manage_production.sh restore /opt/guardianshield/backups/db_backup_20241213_120000.sql.gz
```

## 🌐 Service Architecture

### Service Composition
- **app**: Main GuardianShield application (4 workers)
- **db**: PostgreSQL 15 database with persistent storage
- **redis**: Redis cache and message broker
- **nginx**: Reverse proxy with SSL termination
- **certbot**: Automatic SSL certificate renewal

### Network Configuration
- **Internal**: Services communicate via Docker network
- **External**: Nginx exposes ports 80/443 only
- **SSL**: End-to-end encryption with HTTP/2 support

### Health Monitoring
- Application: `https://www.guardian-shield.io/api/health`
- Database: Automated connection testing
- Redis: Ping/pong health checks
- SSL: Certificate expiration monitoring

## 📧 Email Integration

### Notification Types
- **Security Alerts**: Real-time threat notifications
- **Training Reports**: Weekly AI agent improvement summaries  
- **System Status**: Deployment and maintenance updates
- **Emergency Alerts**: Critical system events

### Email Configuration
```python
# Configured in .env.production
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=claude@guardian-shield.io
SMTP_PASSWORD=your_app_password
EMAIL_FROM=claude@guardian-shield.io
```

### Testing Email
```bash
# Test email functionality
curl -X POST https://www.guardian-shield.io/api/test-email \
  -H "Content-Type: application/json" \
  -d '{"recipient": "test@example.com", "type": "system_status"}'
```

## 🚨 Troubleshooting

### Common Issues

#### 1. SSL Certificate Problems
```bash
# Check certificate status
sudo /opt/guardianshield/manage_production.sh security-scan

# Manual renewal
sudo /opt/guardianshield/manage_production.sh ssl-renew
```

#### 2. Application Won't Start
```bash
# Check logs
sudo /opt/guardianshield/manage_production.sh logs app

# Check environment configuration
cat /opt/guardianshield/.env.production

# Restart services
sudo /opt/guardianshield/manage_production.sh restart
```

#### 3. Database Connection Issues
```bash
# Check database status
docker compose -f /opt/guardianshield/docker-compose.production.yml exec db pg_isready -U guardianshield

# View database logs
sudo /opt/guardianshield/manage_production.sh logs db
```

#### 4. High Memory Usage
```bash
# Check resource usage
sudo /opt/guardianshield/manage_production.sh status

# Scale down if needed
sudo /opt/guardianshield/manage_production.sh scale 2

# Clear system cache
sudo /opt/guardianshield/manage_production.sh cleanup
```

### Log Locations
- **Application**: `/opt/guardianshield/logs/`
- **Nginx**: Docker container logs
- **SSL**: `/var/log/letsencrypt/`
- **System**: `journalctl -u docker`

### Emergency Recovery
```bash
# Stop all services
docker compose -f /opt/guardianshield/docker-compose.production.yml down

# Restore from latest backup
sudo /opt/guardianshield/manage_production.sh restore $(ls -t /opt/guardianshield/backups/db_backup_*.gz | head -1)

# Restart with clean state
docker compose -f /opt/guardianshield/docker-compose.production.yml up -d --force-recreate
```

## 📈 Performance Optimization

### Scaling Configuration
```bash
# Scale based on load:
# Light load (< 100 concurrent users)
sudo /opt/guardianshield/manage_production.sh scale 2

# Medium load (100-500 concurrent users)  
sudo /opt/guardianshield/manage_production.sh scale 4

# High load (500+ concurrent users)
sudo /opt/guardianshield/manage_production.sh scale 8
```

### Resource Monitoring
- **CPU**: Target < 80% average
- **Memory**: Target < 85% usage  
- **Disk**: Monitor `/opt/guardianshield` partition
- **Network**: Monitor bandwidth utilization

### Database Optimization
- **Connection Pooling**: Configured in application
- **Query Optimization**: Automatic indexing
- **Backup Performance**: Incremental backups for large datasets

## 🎉 Post-Deployment Checklist

- [ ] Both domains resolve to correct IP
- [ ] SSL certificates valid for both domains  
- [ ] Health check endpoints responding
- [ ] Email notifications configured and tested
- [ ] Backup system operational
- [ ] Monitoring dashboard accessible
- [ ] Firewall rules configured
- [ ] Auto-renewal cron jobs active
- [ ] Application logs clean of errors
- [ ] Performance metrics within acceptable ranges

## 📞 Support

For deployment issues or questions:
- **Documentation**: This guide and inline comments
- **Logs**: Use management script for detailed logging
- **Monitoring**: Built-in health checks and status monitoring
- **Email**: `claude@guardian-shield.io` (automated notifications)

## 🔄 Maintenance Schedule

- **Daily**: Automated backups and log rotation
- **Weekly**: Security updates and system cleanup  
- **Monthly**: SSL certificate renewal (automated)
- **Quarterly**: Full system review and optimization