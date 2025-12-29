# 🌐 Domain Deployment Guide - GuardianShield Agents

## Complete Step-by-Step Production Deployment

### Prerequisites ✅
- Domain name purchased (e.g., yourdomain.com)
- Server/VPS with Ubuntu 20.04+ (DigitalOcean, AWS, etc.)
- Root access to your server
- Current local system working (http://localhost:3000)

---

## 🚀 **Phase 1: Server Setup & Environment**

### 1.1 Connect to Your Server
```bash
# SSH into your server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install essential tools
apt install -y curl wget git nginx certbot python3-certbot-nginx ufw
```

### 1.2 Install Node.js & npm
```bash
# Install Node.js 20.x
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
apt install -y nodejs

# Verify installation
node --version
npm --version
```

### 1.3 Install Docker (for full system)
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Verify Docker
docker --version
docker-compose --version
```

### 1.4 Setup Firewall
```bash
# Configure UFW firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw --force enable
```

---

## 🎯 **Phase 2: Deploy Your Application**

### 2.1 Clone Your Repository
```bash
# Create project directory
mkdir -p /var/www/guardianshield
cd /var/www/guardianshield

# Clone your project (replace with your actual repo)
git clone https://github.com/your-username/guardianshield-agents.git .

# Install dependencies
npm install

# Install PM2 for process management
npm install -g pm2
```

### 2.2 Environment Configuration
```bash
# Copy environment file
cp .env.example .env

# Edit environment variables
nano .env
```

**Update these variables in .env:**
```env
NODE_ENV=production
PORT=3000
HOST=0.0.0.0

# Your domain
DOMAIN=yourdomain.com

# Database (if using)
DATABASE_URL=postgresql://user:password@localhost:5432/guardianshield

# Security
JWT_SECRET=your-super-secret-jwt-key
ENCRYPTION_KEY=your-32-char-encryption-key

# Web3 Configuration  
RPC_URL=https://eth-mainnet.g.alchemy.com/v2/your-key
PRIVATE_KEY=your-deployment-private-key

# Contract Addresses (from your local deployment)
GUARDIAN_TOKEN_SALE_ADDRESS=0x...
CHAINLINK_PRICE_ORACLE_ADDRESS=0x...
GUARDIAN_SHIELD_NFT_ADDRESS=0x...
```

### 2.3 Build Production Assets
```bash
# Build frontend assets (if needed)
npm run build

# Test the application
npm test

# Start with PM2
pm2 start ecosystem.config.js --env production
pm2 save
pm2 startup
```

---

## 🔒 **Phase 3: Domain & SSL Configuration**

### 3.1 Point Domain to Server
**In your domain registrar (GoDaddy, Namecheap, etc.):**

1. **Create A Record:**
   - Type: A
   - Name: @ (for yourdomain.com)
   - Value: your-server-ip
   - TTL: 1 hour

2. **Create WWW Record:**
   - Type: CNAME  
   - Name: www
   - Value: yourdomain.com
   - TTL: 1 hour

**Wait 5-30 minutes for DNS propagation**

### 3.2 Configure Nginx
```bash
# Create Nginx configuration
nano /etc/nginx/sites-available/guardianshield
```

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Serve static files
    location /static/ {
        alias /var/www/guardianshield/public/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Proxy to Node.js app
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header Origin "";
    }
}
```

### 3.3 Enable Nginx Configuration
```bash
# Enable site
ln -s /etc/nginx/sites-available/guardianshield /etc/nginx/sites-enabled/

# Remove default site
rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

# Restart Nginx
systemctl restart nginx
systemctl enable nginx
```

### 3.4 Install SSL Certificate
```bash
# Install Let's Encrypt SSL certificate
certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
certbot renew --dry-run
```

**Your site should now be live at https://yourdomain.com! 🎉**

---

## 🔧 **Phase 4: Production Optimization**

### 4.1 Performance Monitoring
```bash
# Install monitoring tools
npm install -g @pm2/io

# Setup PM2 monitoring
pm2 install pm2-server-monit

# View logs
pm2 logs
pm2 monit
```

### 4.2 Automatic Backups
```bash
# Create backup script
nano /home/backup-script.sh
```

```bash
#!/bin/bash
# Backup script
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/backups"
PROJECT_DIR="/var/www/guardianshield"

mkdir -p $BACKUP_DIR

# Backup application files
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz $PROJECT_DIR

# Backup database (if using)
# pg_dump guardianshield > $BACKUP_DIR/db_backup_$DATE.sql

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

```bash
# Make executable
chmod +x /home/backup-script.sh

# Add to crontab (daily backups at 3 AM)
crontab -e
# Add: 0 3 * * * /home/backup-script.sh
```

### 4.3 Auto-Update System
```bash
# Create update script
nano /home/update-script.sh
```

```bash
#!/bin/bash
cd /var/www/guardianshield

# Pull latest changes
git pull origin main

# Install dependencies
npm install

# Restart application
pm2 restart all

echo "Application updated: $(date)"
```

---

## 📊 **Phase 5: Health Checks & Monitoring**

### 5.1 Application Health Check
```bash
# Test your deployed application
curl -I https://yourdomain.com
curl -I https://yourdomain.com/health

# Check PM2 status
pm2 status
pm2 logs --lines 50
```

### 5.2 SSL Certificate Check
```bash
# Check SSL certificate
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Check certificate expiration
echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates
```

---

## 🎯 **Phase 6: Final Integration Steps**

### 6.1 Update Frontend Configuration
Update your local frontend files to point to production:

**In wallet-manager.js:**
```javascript
// Update RPC URLs to mainnet
const CONFIG = {
    RPC_URL: 'https://eth-mainnet.g.alchemy.com/v2/your-key',
    CHAIN_ID: 1, // Mainnet
    DOMAIN: 'https://yourdomain.com',
    // ... other config
};
```

### 6.2 Deploy Contracts to Mainnet
```bash
# Local machine - deploy to mainnet
npm run deploy:mainnet

# Upload contract addresses to server
scp contract-addresses.json root@your-server-ip:/var/www/guardianshield/
```

### 6.3 Update Frontend with Production Contracts
```bash
# On server - update frontend with mainnet addresses
cd /var/www/guardianshield
node scripts/update-frontend.js
pm2 restart all
```

---

## ✅ **Deployment Checklist**

- [ ] Server setup and secured
- [ ] Domain DNS configured  
- [ ] SSL certificate installed
- [ ] Application deployed and running
- [ ] Nginx configured and optimized
- [ ] PM2 process manager setup
- [ ] Monitoring and logging active
- [ ] Backup system configured
- [ ] Contracts deployed to mainnet
- [ ] Frontend updated with production contracts
- [ ] Performance testing completed
- [ ] Security audit performed

---

## 🚨 **Troubleshooting Guide**

### Common Issues:

**1. "Site can't be reached"**
```bash
# Check DNS propagation
dig yourdomain.com
# Check Nginx status
systemctl status nginx
# Check firewall
ufw status
```

**2. "ERR_TOO_MANY_REDIRECTS"**
```bash
# Check Nginx SSL configuration
nginx -t
# Check Certbot certificates
certbot certificates
```

**3. "Application not starting"**
```bash
# Check PM2 logs
pm2 logs
# Check Node.js version
node --version
# Check environment variables
cat .env
```

**4. "Smart contract connection failed"**
```bash
# Verify RPC URL
curl -X POST -H "Content-Type: application/json" --data '{"jsonrpc":"2.0","method":"web3_clientVersion","params":[],"id":67}' YOUR_RPC_URL

# Check contract addresses
node -e "console.log(require('./contract-addresses.json'))"
```

---

## 🎉 **Success! Your Application is Live**

Your GuardianShield token sale system is now live at:
- **🌐 Website**: https://yourdomain.com
- **🔒 SSL**: Secured with Let's Encrypt
- **⚡ Performance**: Optimized with Nginx + PM2
- **📊 Monitoring**: Real-time with PM2 dashboard

### Next Steps:
1. **Marketing**: Announce your launch
2. **Analytics**: Setup Google Analytics/tracking
3. **Social**: Update social media links
4. **Community**: Launch Discord/Telegram
5. **Documentation**: Update all links to production domain

**🚀 Congratulations on your successful deployment!**