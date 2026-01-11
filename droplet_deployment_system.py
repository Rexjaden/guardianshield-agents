#!/usr/bin/env python3
"""
GuardianShield DigitalOcean Droplet Deployment System
Complete automated setup for guardian-shield.io on DigitalOcean
"""

import json
import os
from pathlib import Path
import datetime

class GuardianShieldDropletDeployer:
    """Complete DigitalOcean droplet deployment for GuardianShield"""
    
    def __init__(self):
        self.domain = "guardian-shield.io"
        self.droplet_specs = {
            "name": "guardianshield-production",
            "size": "s-2vcpu-2gb",  # $18/month - Perfect for production
            "image": "ubuntu-22-04-x64",
            "region": "nyc1",  # Choose closest to your users
            "tags": ["guardianshield", "production", "web3", "security"],
            "ssh_keys": [],  # Add your SSH key IDs here
            "backups": True,  # Automatic backups
            "monitoring": True
        }
        
        self.services = {
            "agent_gallery": {"port": 8889, "name": "Agent Gallery"},
            "api_server": {"port": 8000, "name": "API Server"},
            "admin_console": {"port": 8001, "name": "Admin Console"},
            "main_site": {"port": 3000, "name": "Main Website"}
        }
        
    def create_droplet_setup_script(self):
        """Create comprehensive droplet setup script"""
        print("🚀 CREATING DROPLET SETUP SCRIPT")
        
        setup_script = f'''#!/bin/bash
# GuardianShield DigitalOcean Droplet Setup Script
# Complete automated deployment for guardian-shield.io

set -e  # Exit on any error

echo "🛡️ GUARDIANSHIELD DROPLET SETUP STARTING..."
echo "=============================================="
echo "Domain: {self.domain}"
echo "Date: $(date)"
echo ""

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install essential packages
echo "🔧 Installing essential packages..."
apt install -y \\
    nginx \\
    certbot \\
    python3-certbot-nginx \\
    python3-pip \\
    python3-venv \\
    nodejs \\
    npm \\
    git \\
    curl \\
    wget \\
    unzip \\
    htop \\
    ufw \\
    fail2ban \\
    redis-server \\
    postgresql \\
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
sudo -u guardianshield /var/www/guardian-shield.io/venv/bin/pip install \\
    fastapi \\
    uvicorn \\
    websockets \\
    python-multipart \\
    jinja2 \\
    psutil \\
    redis \\
    psycopg2-binary \\
    sqlalchemy \\
    alembic \\
    python-jose \\
    passlib \\
    bcrypt \\
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
'''

        with open("droplet_setup.sh", "w", encoding='utf-8') as f:
            f.write(setup_script)
            
        # Make executable
        os.chmod("droplet_setup.sh", 0o755)
        
        print("✅ Droplet setup script saved to: droplet_setup.sh")
        return setup_script
        
    def create_application_deployment_script(self):
        """Create script to deploy GuardianShield applications"""
        print("🚀 CREATING APPLICATION DEPLOYMENT SCRIPT")
        
        app_deploy_script = f'''#!/bin/bash
# GuardianShield Application Deployment Script
# Run this after uploading your application files

set -e
cd /var/www/guardian-shield.io

echo "🛡️ DEPLOYING GUARDIANSHIELD APPLICATIONS..."
echo "============================================="

# Ensure correct permissions
chown -R guardianshield:guardianshield /var/www/guardian-shield.io
chmod +x *.py

# Create systemd service files
echo "⚙️ Creating systemd services..."

# Agent Gallery Service
cat > /etc/systemd/system/guardianshield-gallery.service << EOF
[Unit]
Description=GuardianShield Agent Gallery
After=network.target

[Service]
Type=simple
User=guardianshield
WorkingDirectory=/var/www/guardian-shield.io
Environment=PATH=/var/www/guardian-shield.io/venv/bin
ExecStart=/var/www/guardian-shield.io/venv/bin/python simple_gallery_server.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# API Server Service
cat > /etc/systemd/system/guardianshield-api.service << EOF
[Unit]
Description=GuardianShield API Server
After=network.target

[Service]
Type=simple
User=guardianshield
WorkingDirectory=/var/www/guardian-shield.io
Environment=PATH=/var/www/guardian-shield.io/venv/bin
ExecStart=/var/www/guardian-shield.io/venv/bin/python api_server.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Admin Console Service
cat > /etc/systemd/system/guardianshield-admin.service << EOF
[Unit]
Description=GuardianShield Admin Console
After=network.target

[Service]
Type=simple
User=guardianshield
WorkingDirectory=/var/www/guardian-shield.io
Environment=PATH=/var/www/guardian-shield.io/venv/bin
ExecStart=/var/www/guardian-shield.io/venv/bin/python admin_console.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable services
systemctl daemon-reload
systemctl enable guardianshield-gallery
systemctl enable guardianshield-api
systemctl enable guardianshield-admin

# Configure nginx
echo "🌐 Configuring nginx..."
cp guardian-shield-nginx.conf /etc/nginx/sites-available/guardian-shield.io
ln -sf /etc/nginx/sites-available/guardian-shield.io /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# Start services
echo "🚀 Starting GuardianShield services..."
systemctl start guardianshield-gallery
systemctl start guardianshield-api
systemctl start guardianshield-admin

# Start nginx
systemctl restart nginx
systemctl enable nginx

echo ""
echo "✅ GUARDIANSHIELD APPLICATIONS DEPLOYED!"
echo "========================================"
echo "Services Status:"
systemctl is-active guardianshield-gallery && echo "✅ Agent Gallery: Running" || echo "❌ Agent Gallery: Failed"
systemctl is-active guardianshield-api && echo "✅ API Server: Running" || echo "❌ API Server: Failed"  
systemctl is-active guardianshield-admin && echo "✅ Admin Console: Running" || echo "❌ Admin Console: Failed"
systemctl is-active nginx && echo "✅ Nginx: Running" || echo "❌ Nginx: Failed"

echo ""
echo "📋 Next Steps:"
echo "1. Configure DNS in GoDaddy (point to this server's IP)"
echo "2. Wait for DNS propagation (5-30 minutes)"
echo "3. Run SSL setup: sudo ./ssl_setup.sh"
echo ""
'''

        with open("deploy_applications.sh", "w", encoding='utf-8') as f:
            f.write(app_deploy_script)
            
        os.chmod("deploy_applications.sh", 0o755)
        
        print("✅ Application deployment script saved to: deploy_applications.sh")
        return app_deploy_script
        
    def create_ssl_setup_script(self):
        """Create SSL certificate setup script"""
        print("🔒 CREATING SSL SETUP SCRIPT")
        
        ssl_script = f'''#!/bin/bash
# SSL Certificate Setup for guardian-shield.io
# Run this after DNS is configured and propagated

set -e

echo "🔒 SETTING UP SSL CERTIFICATES..."
echo "================================="

# Check if domain resolves to this server
echo "🌐 Checking DNS resolution..."
SERVER_IP=$(curl -s ifconfig.me)
DOMAIN_IP=$(dig +short {self.domain})

echo "Server IP: $SERVER_IP"
echo "Domain IP: $DOMAIN_IP"

if [ "$SERVER_IP" != "$DOMAIN_IP" ]; then
    echo "⚠️ WARNING: DNS not fully propagated yet"
    echo "Please wait for DNS propagation before running SSL setup"
    echo "You can check with: dig +short {self.domain}"
    exit 1
fi

echo "✅ DNS properly configured!"

# Obtain SSL certificates
echo "📜 Obtaining SSL certificates..."
certbot --nginx -d {self.domain} -d www.{self.domain} -d agents.{self.domain} -d api.{self.domain} -d admin.{self.domain} -d token.{self.domain} --non-interactive --agree-tos --email admin@{self.domain}

# Test certificate renewal
echo "🔄 Testing certificate auto-renewal..."
certbot renew --dry-run

# Set up automatic renewal
echo "⏰ Setting up automatic renewal..."
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -

# Restart nginx with SSL
systemctl reload nginx

echo ""
echo "🎉 SSL CERTIFICATES INSTALLED!"
echo "============================="
echo "Your sites are now secured with HTTPS:"
echo "• https://{self.domain}"
echo "• https://agents.{self.domain}"  
echo "• https://api.{self.domain}"
echo "• https://admin.{self.domain}"
echo "• https://token.{self.domain}"
echo ""
echo "✅ Auto-renewal configured"
echo "🔄 Certificates will auto-renew every 90 days"
'''

        with open("ssl_setup.sh", "w", encoding='utf-8') as f:
            f.write(ssl_script)
            
        os.chmod("ssl_setup.sh", 0o755)
        
        print("✅ SSL setup script saved to: ssl_setup.sh")
        return ssl_script
        
    def create_upload_script(self):
        """Create script to upload files to droplet"""
        print("📤 CREATING FILE UPLOAD SCRIPT")
        
        upload_script = '''#!/bin/bash
# Upload GuardianShield files to DigitalOcean droplet
# Run this from your local machine

# Configuration
DROPLET_IP="YOUR_DROPLET_IP_HERE"
DROPLET_USER="root"

echo "📤 UPLOADING GUARDIANSHIELD FILES TO DROPLET..."
echo "==============================================="

if [ "$DROPLET_IP" = "YOUR_DROPLET_IP_HERE" ]; then
    echo "❌ Please edit this script and set your DROPLET_IP"
    exit 1
fi

echo "Droplet IP: $DROPLET_IP"

# Upload main application files
echo "📁 Uploading application files..."
scp -r *.py $DROPLET_USER@$DROPLET_IP:/var/www/guardian-shield.io/

# Upload configuration files
echo "⚙️ Uploading configuration files..."
scp guardian-shield-nginx.conf $DROPLET_USER@$DROPLET_IP:/var/www/guardian-shield.io/
scp deploy_applications.sh $DROPLET_USER@$DROPLET_IP:/var/www/guardian-shield.io/
scp ssl_setup.sh $DROPLET_USER@$DROPLET_IP:/var/www/guardian-shield.io/

# Upload directories
echo "📂 Uploading directories..."
scp -r agent_assets/ $DROPLET_USER@$DROPLET_IP:/var/www/guardian-shield.io/ 2>/dev/null || echo "📁 agent_assets not found, skipping"
scp -r token_assets/ $DROPLET_USER@$DROPLET_IP:/var/www/guardian-shield.io/ 2>/dev/null || echo "🪙 token_assets not found, skipping"
scp -r frontend/ $DROPLET_USER@$DROPLET_IP:/var/www/guardian-shield.io/ 2>/dev/null || echo "🎨 frontend not found, skipping"
scp -r templates/ $DROPLET_USER@$DROPLET_IP:/var/www/guardian-shield.io/ 2>/dev/null || echo "📄 templates not found, skipping"

echo ""
echo "✅ UPLOAD COMPLETE!"
echo "=================="
echo "Next steps on your droplet:"
echo "1. SSH into droplet: ssh $DROPLET_USER@$DROPLET_IP"
echo "2. Run: cd /var/www/guardian-shield.io"
echo "3. Run: sudo ./deploy_applications.sh"
echo "4. Configure DNS in GoDaddy"
echo "5. Run: sudo ./ssl_setup.sh"
'''

        with open("upload_to_droplet.sh", "w", encoding='utf-8') as f:
            f.write(upload_script)
            
        os.chmod("upload_to_droplet.sh", 0o755)
        
        print("✅ Upload script saved to: upload_to_droplet.sh")
        return upload_script
        
    def create_monitoring_script(self):
        """Create monitoring and maintenance script"""
        print("📊 CREATING MONITORING SCRIPT")
        
        monitoring_script = f'''#!/bin/bash
# GuardianShield Monitoring and Maintenance Script

echo "📊 GUARDIANSHIELD SYSTEM STATUS"
echo "==============================="
echo "Date: $(date)"
echo "Server: $(hostname)"
echo ""

# Check system resources
echo "💾 SYSTEM RESOURCES:"
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{{print $2 + $4}}')%"
echo "Memory: $(free -m | awk 'NR==2{{printf "%.1f%%", $3*100/$2 }}')"
echo "Disk: $(df -h / | awk 'NR==2{{print $5}}') used"
echo ""

# Check services status
echo "🔧 SERVICE STATUS:"
services=("guardianshield-gallery" "guardianshield-api" "guardianshield-admin" "nginx" "postgresql" "redis-server")
for service in "${{services[@]}}"; do
    if systemctl is-active --quiet $service; then
        echo "✅ $service: Running"
    else
        echo "❌ $service: Not running"
    fi
done
echo ""

# Check SSL certificate expiration
echo "🔒 SSL CERTIFICATE STATUS:"
if command -v certbot &> /dev/null; then
    certbot certificates 2>/dev/null | grep -A1 "Certificate Name: {self.domain}" | tail -1 || echo "No certificates found"
else
    echo "Certbot not installed"
fi
echo ""

# Check domain connectivity
echo "🌐 DOMAIN CONNECTIVITY:"
domains=("{self.domain}" "agents.{self.domain}" "api.{self.domain}" "admin.{self.domain}")
for domain in "${{domains[@]}}"; do
    if curl -s -o /dev/null -w "%{{http_code}}" https://$domain | grep -q "200\\|301\\|302"; then
        echo "✅ $domain: Accessible"
    else
        echo "❌ $domain: Not accessible"
    fi
done
echo ""

# Show recent logs
echo "📝 RECENT ERRORS (last 24h):"
journalctl --since "24 hours ago" --priority=3 --no-pager | tail -5 || echo "No recent errors"
echo ""

# Disk usage warning
DISK_USAGE=$(df / | tail -1 | awk '{{print $5}}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "⚠️ WARNING: Disk usage is ${{DISK_USAGE}}%"
    echo "Consider cleaning up or expanding storage"
fi

echo "📊 Monitoring complete. Run 'sudo systemctl status SERVICE_NAME' for detailed service info."
'''

        with open("monitor_system.sh", "w", encoding='utf-8') as f:
            f.write(monitoring_script)
            
        os.chmod("monitor_system.sh", 0o755)
        
        print("✅ Monitoring script saved to: monitor_system.sh")
        return monitoring_script
        
    def create_deployment_guide(self):
        """Create complete deployment guide"""
        guide_content = f'''# 🚀 GuardianShield DigitalOcean Deployment Guide

## 📋 Complete Step-by-Step Deployment

### **STEP 1: Create DigitalOcean Droplet**

1. **Login to DigitalOcean**
2. **Create Droplet:**
   - **Image:** Ubuntu 22.04 LTS
   - **Size:** Basic $18/month (2 vCPU, 2GB RAM) - Recommended
   - **Region:** Choose closest to your users (NYC, SFO, AMS)
   - **Authentication:** Add your SSH key
   - **Hostname:** guardianshield-production
   - **Tags:** guardianshield, production
   - **Enable:** Backups, Monitoring

### **STEP 2: Initial Server Setup**

```bash
# SSH into your droplet
ssh root@YOUR_DROPLET_IP

# Upload and run setup script
wget https://your-transfer-service.com/droplet_setup.sh
chmod +x droplet_setup.sh
./droplet_setup.sh
```

### **STEP 3: Upload Application Files**

From your local machine:
```bash
# Edit upload script with your droplet IP
nano upload_to_droplet.sh
# Set DROPLET_IP="your.droplet.ip.here"

# Run upload
./upload_to_droplet.sh
```

### **STEP 4: Configure GoDaddy DNS**

In your GoDaddy control panel for **{self.domain}**:

| Type  | Name   | Value            | TTL   |
|-------|--------|------------------|-------|
| A     | @      | YOUR_DROPLET_IP  | 1 Hour|
| CNAME | www    | {self.domain}    | 1 Hour|
| CNAME | agents | {self.domain}    | 1 Hour|
| CNAME | api    | {self.domain}    | 1 Hour|
| CNAME | admin  | {self.domain}    | 1 Hour|
| CNAME | token  | {self.domain}    | 1 Hour|

⏰ **Wait 5-30 minutes for DNS propagation**

### **STEP 5: Deploy Applications**

SSH into your droplet:
```bash
ssh root@YOUR_DROPLET_IP
cd /var/www/guardian-shield.io
./deploy_applications.sh
```

### **STEP 6: Setup SSL Certificates**

After DNS has propagated:
```bash
# Check DNS first
dig +short {self.domain}
# Should return your droplet IP

# Setup SSL
./ssl_setup.sh
```

## 🎉 **DEPLOYMENT COMPLETE!**

Your GuardianShield system will be live at:

- **🏠 Main Site:** https://{self.domain}
- **🤖 Agent Gallery:** https://agents.{self.domain}
- **⚡ API Server:** https://api.{self.domain}
- **🔧 Admin Console:** https://admin.{self.domain}
- **🪙 Token System:** https://token.{self.domain}

## 📊 **Monitoring & Maintenance**

```bash
# Check system status
./monitor_system.sh

# View service logs
journalctl -u guardianshield-gallery -f
journalctl -u guardianshield-api -f
journalctl -u guardianshield-admin -f

# Restart services if needed
systemctl restart guardianshield-gallery
systemctl restart guardianshield-api
systemctl restart guardianshield-admin
```

## 💰 **Monthly Costs**

- **DigitalOcean Droplet:** $18/month (2GB RAM, 2 vCPU)
- **Domain:** ~$1/month ({self.domain})
- **SSL Certificate:** FREE (Let's Encrypt)
- **Backups:** Included
- **Total:** ~$19/month

## 🔧 **Troubleshooting**

**Service won't start:**
```bash
systemctl status guardianshield-SERVICE_NAME
journalctl -u guardianshield-SERVICE_NAME
```

**SSL issues:**
```bash
certbot certificates
certbot renew --dry-run
```

**DNS not working:**
```bash
dig +short {self.domain}
nslookup {self.domain}
```

Your professional GuardianShield ecosystem is ready for production! 🛡️🚀
'''

        with open("DROPLET_DEPLOYMENT_GUIDE.md", "w", encoding='utf-8') as f:
            f.write(guide_content)
            
        print("✅ Complete deployment guide saved to: DROPLET_DEPLOYMENT_GUIDE.md")
        return guide_content

def main():
    """Create complete droplet deployment system"""
    print("🌊 DIGITALOCEAN DROPLET DEPLOYMENT SYSTEM")
    print("=" * 60)
    
    deployer = GuardianShieldDropletDeployer()
    
    # Create all deployment scripts and files
    deployer.create_droplet_setup_script()
    print()
    deployer.create_application_deployment_script()
    print()
    deployer.create_ssl_setup_script()
    print()
    deployer.create_upload_script()
    print()
    deployer.create_monitoring_script()
    print()
    deployer.create_deployment_guide()
    
    print("\n" + "=" * 60)
    print("🎉 DROPLET DEPLOYMENT SYSTEM READY!")
    print("=" * 60)
    
    files_created = [
        "droplet_setup.sh",
        "deploy_applications.sh", 
        "ssl_setup.sh",
        "upload_to_droplet.sh",
        "monitor_system.sh",
        "DROPLET_DEPLOYMENT_GUIDE.md"
    ]
    
    print("\n📁 FILES CREATED:")
    for file in files_created:
        print(f"  ✅ {file}")
    
    print(f"\n💰 ESTIMATED MONTHLY COST: $19")
    print("  • DigitalOcean Droplet: $18/month")
    print("  • Domain cost: ~$1/month")
    print("  • SSL Certificate: FREE")
    
    print(f"\n🎯 IMMEDIATE NEXT STEPS:")
    print("1. 🌊 Create DigitalOcean droplet ($18/month)")
    print("2. 📤 Upload files using upload_to_droplet.sh")
    print("3. 🌐 Configure DNS in GoDaddy") 
    print("4. 🚀 Deploy applications on droplet")
    print("5. 🔒 Setup SSL certificates")
    
    print(f"\n🌟 Your guardian-shield.io will be live in ~30 minutes!")

if __name__ == "__main__":
    main()