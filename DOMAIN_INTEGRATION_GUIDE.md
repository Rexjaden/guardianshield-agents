# GuardianShield Domain Integration - Step by Step Guide

## 🎯 **STEP 1: CHOOSE AND REGISTER YOUR DOMAIN**

### Recommended Domain Options (in priority order):
1. **guardianshield.io** ⭐ BEST CHOICE
2. **guardianshield.ai** 
3. **guardianshield.tech**
4. **guardianshield.security**

### Domain Registration Process:
```bash
# Check domain availability at:
- Namecheap.com
- GoDaddy.com  
- Cloudflare.com (cheapest + best DNS)
- Google Domains
```

**Estimated Cost**: $12-25/year

---

## 🏗️ **STEP 2: CHOOSE HOSTING PROVIDER**

### **RECOMMENDED: DigitalOcean Droplets**
- **Plan**: Basic Droplet $6/month (1GB RAM, 1 vCPU)
- **Location**: Choose nearest to your target users
- **OS**: Ubuntu 22.04 LTS

### **ALTERNATIVE OPTIONS:**
- **AWS EC2**: t3.micro (free tier eligible)
- **Linode**: Nanode 1GB ($5/month)
- **Vultr**: Regular Performance ($6/month)
- **Hetzner**: CPX11 ($4.15/month)

---

## 🚀 **STEP 3: SERVER SETUP & PREPARATION**

### Connect to your server:
```bash
# SSH into your server
ssh root@YOUR_SERVER_IP

# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y docker.io docker-compose nginx certbot python3-certbot-nginx git
```

### Configure Docker:
```bash
# Start Docker service
systemctl start docker
systemctl enable docker

# Add user to docker group (if not root)
usermod -aG docker $USER
```

---

## 📁 **STEP 4: DEPLOY GUARDIANSHIELD TO SERVER**

### Clone your repository:
```bash
# Navigate to web directory
cd /var/www

# Clone GuardianShield
git clone https://github.com/YOUR_USERNAME/guardianshield-agents.git
cd guardianshield-agents

# Set permissions
chown -R www-data:www-data /var/www/guardianshield-agents
chmod -R 755 /var/www/guardianshield-agents
```

### Configure environment:
```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

**Required Environment Variables:**
```env
# Domain Configuration
DOMAIN=guardianshield.io
API_URL=https://api.guardianshield.io
FRONTEND_URL=https://app.guardianshield.io

# Security
JWT_SECRET=your-super-secure-jwt-secret-here
API_KEY=your-api-key-here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/guardianshield

# Blockchain
WEB3_PROVIDER_URL=https://mainnet.infura.io/v3/YOUR_PROJECT_ID
PRIVATE_KEY=your-private-key-for-contract-deployment
```

---

## 🌐 **STEP 5: CONFIGURE DNS SETTINGS**

### At your domain registrar (Cloudflare/Namecheap):

```dns
# A Records (point to your server IP)
Type    Name                    Value               TTL
A       @                       YOUR_SERVER_IP      300
A       www                     YOUR_SERVER_IP      300
A       app                     YOUR_SERVER_IP      300  
A       api                     YOUR_SERVER_IP      300
A       admin                   YOUR_SERVER_IP      300
A       docs                    YOUR_SERVER_IP      300
A       monitor                 YOUR_SERVER_IP      300

# CNAME Records (optional)
CNAME   staking                 guardianshield.io   300
CNAME   demo                    guardianshield.io   300
```

**DNS Propagation**: Takes 15-60 minutes

---

## 🔧 **STEP 6: CONFIGURE NGINX REVERSE PROXY**

### Create Nginx configuration:
```bash
# Remove default config
rm /etc/nginx/sites-enabled/default

# Create GuardianShield config
nano /etc/nginx/sites-available/guardianshield
```

### Nginx Configuration File:
```nginx
# Main domain - Landing page
server {
    listen 80;
    server_name guardianshield.io www.guardianshield.io;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# App subdomain - Main application
server {
    listen 80;
    server_name app.guardianshield.io;
    
    location / {
        proxy_pass http://localhost:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# API subdomain - Backend API
server {
    listen 80;
    server_name api.guardianshield.io;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket support
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}

# Admin subdomain
server {
    listen 80;
    server_name admin.guardianshield.io;
    
    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Enable the configuration:
```bash
# Link configuration
ln -s /etc/nginx/sites-available/guardianshield /etc/nginx/sites-enabled/

# Test configuration
nginx -t

# Restart Nginx
systemctl restart nginx
```

---

## 🔒 **STEP 7: INSTALL SSL CERTIFICATES**

### Using Let's Encrypt (FREE SSL):
```bash
# Install SSL for all subdomains
certbot --nginx -d guardianshield.io \
                -d www.guardianshield.io \
                -d app.guardianshield.io \
                -d api.guardianshield.io \
                -d admin.guardianshield.io

# Set up automatic renewal
crontab -e
# Add this line:
0 12 * * * /usr/bin/certbot renew --quiet
```

---

## 🐳 **STEP 8: DEPLOY WITH DOCKER COMPOSE**

### Start the services:
```bash
cd /var/www/guardianshield-agents

# Build and start all services
docker-compose -f docker-compose.production.yml up -d

# Check if services are running
docker-compose ps
```

### Expected Services:
```
NAME                    STATUS     PORTS
guardianshield-api      Up         0.0.0.0:8000->8000/tcp
guardianshield-app      Up         0.0.0.0:3001->3000/tcp
guardianshield-admin    Up         0.0.0.0:8001->8001/tcp
guardianshield-db       Up         5432/tcp
guardianshield-redis    Up         6379/tcp
```

---

## 🔍 **STEP 9: VERIFY DEPLOYMENT**

### Test each service:
```bash
# Check API health
curl https://api.guardianshield.io/health

# Check main app
curl https://app.guardianshield.io

# Check admin panel  
curl https://admin.guardianshield.io

# View logs
docker-compose -f docker-compose.production.yml logs -f
```

---

## 🚦 **STEP 10: FINAL CONFIGURATION**

### Configure monitoring:
```bash
# Start monitoring services
docker-compose -f docker-compose.monitoring.yml up -d

# Access monitoring at: https://monitor.guardianshield.io
```

### Configure backups:
```bash
# Create backup script
nano /root/backup-guardianshield.sh
```

```bash
#!/bin/bash
# Backup script
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p /backups
docker exec guardianshield-db pg_dump -U postgres guardianshield > /backups/db_$DATE.sql
tar -czf /backups/app_$DATE.tar.gz /var/www/guardianshield-agents
find /backups -name "*.sql" -mtime +7 -delete
find /backups -name "*.tar.gz" -mtime +7 -delete
```

```bash
# Make executable and add to cron
chmod +x /root/backup-guardianshield.sh
crontab -e
# Add: 0 2 * * * /root/backup-guardianshield.sh
```

---

## ✅ **VERIFICATION CHECKLIST**

- [ ] Domain registered and DNS configured
- [ ] Server provisioned and secured
- [ ] Docker and Docker Compose installed
- [ ] Repository cloned and configured
- [ ] Environment variables set
- [ ] Nginx reverse proxy configured
- [ ] SSL certificates installed
- [ ] All services running via Docker Compose
- [ ] Health checks passing
- [ ] Backups configured

---

## 🎉 **SUCCESS! YOUR GUARDIANSHIELD IS NOW LIVE AT:**

- **Main Site**: https://guardianshield.io
- **Web App**: https://app.guardianshield.io  
- **API**: https://api.guardianshield.io
- **Admin**: https://admin.guardianshield.io

**Total Setup Time**: 2-4 hours  
**Monthly Cost**: $6-12 (server) + domain cost

---

## 🆘 **TROUBLESHOOTING COMMON ISSUES**

### Service won't start:
```bash
# Check logs
docker-compose logs service-name

# Restart specific service
docker-compose restart service-name
```

### SSL certificate issues:
```bash
# Renew certificates
certbot renew --nginx

# Check certificate status  
certbot certificates
```

### DNS not propagating:
```bash
# Check DNS propagation
dig guardianshield.io
nslookup guardianshield.io
```

**Need help?** The deployment is automated - just follow each step in order! 🚀