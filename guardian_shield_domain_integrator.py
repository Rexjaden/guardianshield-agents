#!/usr/bin/env python3
"""
Guardian-Shield.io Domain Integration System
Complete setup for connecting your existing GoDaddy domain to GuardianShield
"""

import json
import os
from pathlib import Path
import datetime

class GuardianShieldDomainIntegrator:
    """Complete domain integration for guardian-shield.io"""
    
    def __init__(self):
        self.domain = "guardian-shield.io"
        self.subdomains = {
            "main": "guardian-shield.io",
            "app": "app.guardian-shield.io",
            "api": "api.guardian-shield.io", 
            "admin": "admin.guardian-shield.io",
            "agents": "agents.guardian-shield.io",
            "token": "token.guardian-shield.io",
            "docs": "docs.guardian-shield.io"
        }
        
        self.services = {
            "agent_gallery": "agents.guardian-shield.io",
            "token_system": "token.guardian-shield.io",
            "api_server": "api.guardian-shield.io",
            "admin_console": "admin.guardian-shield.io"
        }
        
    def generate_godaddy_dns_config(self):
        """Generate DNS configuration for GoDaddy"""
        print("🌐 GENERATING GODADDY DNS CONFIGURATION")
        print("=" * 50)
        
        dns_records = [
            {
                "type": "A",
                "name": "@",
                "value": "YOUR_SERVER_IP",
                "ttl": 3600,
                "purpose": "Main domain (guardian-shield.io)"
            },
            {
                "type": "CNAME",
                "name": "www",
                "value": "guardian-shield.io",
                "ttl": 3600,
                "purpose": "www redirect"
            },
            {
                "type": "CNAME",
                "name": "app",
                "value": "guardian-shield.io",
                "ttl": 3600,
                "purpose": "Web application"
            },
            {
                "type": "CNAME",
                "name": "api",
                "value": "guardian-shield.io",
                "ttl": 3600,
                "purpose": "API endpoints"
            },
            {
                "type": "CNAME",
                "name": "agents",
                "value": "guardian-shield.io",
                "ttl": 3600,
                "purpose": "Agent gallery"
            },
            {
                "type": "CNAME",
                "name": "token",
                "value": "guardian-shield.io",
                "ttl": 3600,
                "purpose": "Token system"
            },
            {
                "type": "CNAME",
                "name": "admin",
                "value": "guardian-shield.io",
                "ttl": 3600,
                "purpose": "Admin console"
            },
            {
                "type": "CNAME",
                "name": "docs",
                "value": "guardian-shield.io",
                "ttl": 3600,
                "purpose": "Documentation"
            }
        ]
        
        # Save DNS configuration
        with open("godaddy_dns_config.json", "w") as f:
            json.dump(dns_records, f, indent=2)
        
        print("📋 DNS RECORDS TO ADD IN GODADDY:")
        print("-" * 40)
        for record in dns_records:
            print(f"Type: {record['type']:<6} | Name: {record['name']:<8} | Value: {record['value']}")
            print(f"Purpose: {record['purpose']}")
            print()
            
        return dns_records
        
    def create_nginx_config(self):
        """Create Nginx configuration for domain"""
        print("⚙️ CREATING NGINX CONFIGURATION")
        
        nginx_config = f"""
# Main site configuration for guardian-shield.io
server {{
    listen 80;
    server_name guardian-shield.io www.guardian-shield.io;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name guardian-shield.io www.guardian-shield.io;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/guardian-shield.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/guardian-shield.io/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Main site
    location / {{
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}

# Agent Gallery - agents.guardian-shield.io
server {{
    listen 443 ssl http2;
    server_name agents.guardian-shield.io;
    
    ssl_certificate /etc/letsencrypt/live/guardian-shield.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/guardian-shield.io/privkey.pem;
    
    location / {{
        proxy_pass http://localhost:8889;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}

# API Server - api.guardian-shield.io
server {{
    listen 443 ssl http2;
    server_name api.guardian-shield.io;
    
    ssl_certificate /etc/letsencrypt/live/guardian-shield.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/guardian-shield.io/privkey.pem;
    
    location / {{
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
    
    # WebSocket support
    location /ws {{
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }}
}}

# Admin Console - admin.guardian-shield.io
server {{
    listen 443 ssl http2;
    server_name admin.guardian-shield.io;
    
    ssl_certificate /etc/letsencrypt/live/guardian-shield.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/guardian-shield.io/privkey.pem;
    
    location / {{
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}

# Token System - token.guardian-shield.io
server {{
    listen 443 ssl http2;
    server_name token.guardian-shield.io;
    
    ssl_certificate /etc/letsencrypt/live/guardian-shield.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/guardian-shield.io/privkey.pem;
    
    location / {{
        proxy_pass http://localhost:8889/token/profile;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""
        
        # Save Nginx configuration
        with open("guardian-shield-nginx.conf", "w") as f:
            f.write(nginx_config)
            
        print("✅ Nginx configuration saved to: guardian-shield-nginx.conf")
        return nginx_config
        
    def create_deployment_script(self):
        """Create deployment script for the domain"""
        print("🚀 CREATING DEPLOYMENT SCRIPT")
        
        deploy_script = f"""#!/bin/bash
# Guardian-Shield.io Deployment Script

echo "🛡️ Deploying GuardianShield to guardian-shield.io"
echo "================================================="

# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install nginx certbot python3-certbot-nginx -y

# Install Node.js (for frontend)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# Create web directory
sudo mkdir -p /var/www/guardian-shield.io
sudo chown -R $USER:$USER /var/www/guardian-shield.io

# Copy your GuardianShield files
echo "📁 Copying application files..."
# You'll need to upload your files to the server first

# Install Python dependencies
cd /path/to/your/guardianshield
pip install -r requirements.txt

# Copy Nginx configuration
sudo cp guardian-shield-nginx.conf /etc/nginx/sites-available/guardian-shield.io
sudo ln -sf /etc/nginx/sites-available/guardian-shield.io /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Obtain SSL certificate
sudo certbot --nginx -d guardian-shield.io -d www.guardian-shield.io -d agents.guardian-shield.io -d api.guardian-shield.io -d admin.guardian-shield.io -d token.guardian-shield.io -d docs.guardian-shield.io

# Start services
echo "🚀 Starting GuardianShield services..."

# Start agent gallery (background)
nohup python simple_gallery_server.py > gallery.log 2>&1 &

# Start API server (background)  
nohup python api_server.py > api.log 2>&1 &

# Start admin console (background)
nohup python admin_console.py > admin.log 2>&1 &

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx

# Enable firewall
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw --force enable

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================================"
echo "🌐 Main site: https://guardian-shield.io"
echo "🤖 Agent Gallery: https://agents.guardian-shield.io"
echo "⚡ API Server: https://api.guardian-shield.io"
echo "🔧 Admin Console: https://admin.guardian-shield.io"
echo "🪙 Token System: https://token.guardian-shield.io"
echo ""
echo "📋 Next steps:"
echo "1. Test all subdomains"
echo "2. Monitor logs for any issues"
echo "3. Set up monitoring and backups"
"""

        with open("deploy_guardian_shield.sh", "w", encoding='utf-8') as f:
            f.write(deploy_script)
            
        # Make executable
        os.chmod("deploy_guardian_shield.sh", 0o755)
        
        print("✅ Deployment script saved to: deploy_guardian_shield.sh")
        return deploy_script
        
    def create_service_files(self):
        """Create systemd service files for auto-startup"""
        print("⚙️ CREATING SYSTEMD SERVICE FILES")
        
        services = {
            "guardianshield-gallery": {
                "description": "GuardianShield Agent Gallery",
                "command": "python simple_gallery_server.py",
                "port": 8889
            },
            "guardianshield-api": {
                "description": "GuardianShield API Server", 
                "command": "python api_server.py",
                "port": 8000
            },
            "guardianshield-admin": {
                "description": "GuardianShield Admin Console",
                "command": "python admin_console.py", 
                "port": 8001
            }
        }
        
        service_dir = Path("systemd_services")
        service_dir.mkdir(exist_ok=True)
        
        for service_name, config in services.items():
            service_content = f"""[Unit]
Description={config['description']}
After=network.target

[Service]
Type=simple
User=guardianshield
WorkingDirectory=/var/www/guardian-shield.io
ExecStart={config['command']}
Restart=always
RestartSec=5
Environment=PORT={config['port']}

[Install]
WantedBy=multi-user.target
"""
            
            service_file = service_dir / f"{service_name}.service"
            with open(service_file, "w") as f:
                f.write(service_content)
                
        print(f"✅ Service files created in: {service_dir}")
        return service_dir
        
    def generate_domain_integration_guide(self):
        """Generate complete integration guide"""
        guide_content = f"""
# 🌐 Guardian-Shield.io Domain Integration Guide

## 📋 STEP 1: GODADDY DNS CONFIGURATION

Login to your GoDaddy account and navigate to DNS Management for **guardian-shield.io**

Add these DNS records:

### A Record (Main Domain):
- **Type**: A
- **Name**: @ 
- **Value**: YOUR_SERVER_IP
- **TTL**: 1 Hour

### CNAME Records (Subdomains):
- **www** → guardian-shield.io
- **app** → guardian-shield.io  
- **api** → guardian-shield.io
- **agents** → guardian-shield.io
- **token** → guardian-shield.io
- **admin** → guardian-shield.io
- **docs** → guardian-shield.io

⏰ **DNS propagation takes 5-30 minutes**

## 📋 STEP 2: SERVER SETUP

### Option A: DigitalOcean Droplet ($12/month)
1. Create Ubuntu 22.04 droplet
2. Point your DNS to droplet IP
3. Run deployment script

### Option B: Vercel + Railway (Modern)
1. Deploy frontend to Vercel
2. Deploy backend to Railway  
3. Configure custom domains

## 📋 STEP 3: DEPLOYMENT

Upload your GuardianShield files and run:
```bash
chmod +x deploy_guardian_shield.sh
./deploy_guardian_shield.sh
```

## 📋 STEP 4: SSL CERTIFICATE

Automatic SSL setup with Let's Encrypt:
```bash
sudo certbot --nginx -d guardian-shield.io -d www.guardian-shield.io -d agents.guardian-shield.io
```

## 🌟 FINAL RESULT

After setup, your sites will be live at:

- **🏠 Main Site**: https://guardian-shield.io
- **🤖 Agent Gallery**: https://agents.guardian-shield.io  
- **⚡ API Server**: https://api.guardian-shield.io
- **🔧 Admin Console**: https://admin.guardian-shield.io
- **🪙 Token System**: https://token.guardian-shield.io

## 💡 RECOMMENDED NEXT STEPS

1. **Set up monitoring** (UptimeRobot)
2. **Configure backups** (automated)
3. **Add Google Analytics** 
4. **Create professional email** (admin@guardian-shield.io)
5. **Set up CI/CD pipeline** (GitHub Actions)

Your GuardianShield ecosystem will be professionally deployed! 🚀
"""

        with open("GUARDIAN_SHIELD_DOMAIN_GUIDE.md", "w", encoding='utf-8') as f:
            f.write(guide_content)
            
        print("✅ Complete integration guide saved to: GUARDIAN_SHIELD_DOMAIN_GUIDE.md")
        return guide_content

def main():
    """Run the complete domain integration setup"""
    print("🛡️ GUARDIAN-SHIELD.IO DOMAIN INTEGRATION")
    print("=" * 60)
    
    integrator = GuardianShieldDomainIntegrator()
    
    # Generate all configuration files
    integrator.generate_godaddy_dns_config()
    print()
    integrator.create_nginx_config()
    print()
    integrator.create_deployment_script()
    print()
    integrator.create_service_files()
    print()
    integrator.generate_domain_integration_guide()
    
    print("\n" + "=" * 60)
    print("🎉 GUARDIAN-SHIELD.IO INTEGRATION READY!")
    print("=" * 60)
    
    print("\n📁 FILES CREATED:")
    files_created = [
        "godaddy_dns_config.json",
        "guardian-shield-nginx.conf", 
        "deploy_guardian_shield.sh",
        "systemd_services/",
        "GUARDIAN_SHIELD_DOMAIN_GUIDE.md"
    ]
    
    for file in files_created:
        print(f"  ✅ {file}")
    
    print(f"\n🎯 IMMEDIATE NEXT STEPS:")
    print("1. 🌐 Configure DNS records in GoDaddy")
    print("2. 🖥️ Set up hosting server (DigitalOcean/VPS)")
    print("3. 🚀 Run deployment script")
    print("4. 🔒 Configure SSL certificates")
    print("5. 🧪 Test all subdomains")
    
    print(f"\n🌟 Your guardian-shield.io domain is ready for deployment!")
    
if __name__ == "__main__":
    main()