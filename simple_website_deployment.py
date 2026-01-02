#!/usr/bin/env python3
"""
Simple GuardianShield Website Deployment
Deploy just the website to a single DigitalOcean droplet
"""

import os
import subprocess
import time
from pathlib import Path

class SimpleWebsiteDeployment:
    def __init__(self):
        self.droplet_specs = {
            "name": "guardianshield-website",
            "size": "s-1vcpu-1gb",  # $6/month
            "image": "ubuntu-22-04-x64",
            "region": "nyc1",  # Choose region closest to your users
            "tags": ["guardianshield", "website"]
        }
        
        self.website_files = [
            "index.html",
            "condensed-frontend.html", 
            "frontend/",
            "static/",
            "assets/"
        ]
        
    def create_deployment_package(self):
        """Package website files for deployment"""
        print("📦 Creating website deployment package...")
        
        # Create deployment directory
        deploy_dir = Path("deploy_website")
        deploy_dir.mkdir(exist_ok=True)
        
        # Copy main website files
        import shutil
        
        # Copy main HTML files
        if os.path.exists("index.html"):
            shutil.copy("index.html", deploy_dir)
            print("✅ Copied index.html")
            
        if os.path.exists("condensed-frontend.html"):
            shutil.copy("condensed-frontend.html", deploy_dir)
            print("✅ Copied condensed-frontend.html")
            
        # Copy frontend directory
        if os.path.exists("frontend"):
            shutil.copytree("frontend", deploy_dir / "frontend", dirs_exist_ok=True)
            print("✅ Copied frontend/ directory")
            
        # Create simple nginx config
        nginx_config = """
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    root /var/www/guardianshield;
    index index.html condensed-frontend.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Serve static files efficiently
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
"""
        
        with open(deploy_dir / "nginx.conf", "w") as f:
            f.write(nginx_config)
            
        print("✅ Created nginx configuration")
        
        # Create deployment script
        deploy_script = """#!/bin/bash
# Simple website deployment script

# Update system
sudo apt update && sudo apt upgrade -y

# Install nginx
sudo apt install nginx -y

# Create website directory
sudo mkdir -p /var/www/guardianshield

# Copy website files
sudo cp -r ./* /var/www/guardianshield/

# Set permissions
sudo chown -R www-data:www-data /var/www/guardianshield
sudo chmod -R 755 /var/www/guardianshield

# Configure nginx
sudo cp nginx.conf /etc/nginx/sites-available/guardianshield
sudo ln -sf /etc/nginx/sites-available/guardianshield /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and restart nginx
sudo nginx -t && sudo systemctl restart nginx

# Enable firewall
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw --force enable

echo "Website deployed successfully!"
echo "Your site should be accessible at: http://your-droplet-ip"
"""
        
        with open(deploy_dir / "deploy.sh", "w", encoding='utf-8') as f:
            f.write(deploy_script)
            
        os.chmod(deploy_dir / "deploy.sh", 0o755)
        print("✅ Created deployment script")
        
        return deploy_dir
        
    def create_docker_version(self):
        """Optional: Create containerized version"""
        print("🐳 Creating Docker version...")
        
        dockerfile = """FROM nginx:alpine

# Copy website files
COPY . /usr/share/nginx/html/

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
"""
        
        with open("Dockerfile.website", "w") as f:
            f.write(dockerfile)
            
        docker_compose = """version: '3.8'
services:
  guardianshield-website:
    build: 
      context: .
      dockerfile: Dockerfile.website
    ports:
      - "80:80"
    restart: unless-stopped
    container_name: guardianshield-site
"""
        
        with open("docker-compose.website.yml", "w") as f:
            f.write(docker_compose)
            
        print("✅ Created Docker deployment files")
        
    def show_deployment_instructions(self):
        """Show simple deployment instructions"""
        instructions = """
🚀 SIMPLE WEBSITE DEPLOYMENT GUIDE

1️⃣ CREATE DIGITALOCEAN DROPLET:
   - Size: Basic ($6/month) - 1GB RAM, 1 vCPU  
   - Image: Ubuntu 22.04 LTS
   - Region: Choose closest to your users (NYC, SFO, AMS, etc.)
   - Add SSH key for secure access

2️⃣ UPLOAD FILES TO DROPLET:
   scp -r deploy_website/* root@YOUR_DROPLET_IP:/root/

3️⃣ SSH INTO DROPLET & DEPLOY:
   ssh root@YOUR_DROPLET_IP
   cd /root
   chmod +x deploy.sh
   ./deploy.sh

4️⃣ POINT YOUR DOMAIN:
   - In your domain registrar (GoDaddy, Namecheap, etc.)
   - Create A record: @ -> YOUR_DROPLET_IP
   - Create A record: www -> YOUR_DROPLET_IP

5️⃣ OPTIONAL - ADD SSL:
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

💰 TOTAL COST: ~$6/month + domain cost (~$12/year)

🌐 Your GuardianShield website will be live at your domain!
"""
        
        print(instructions)
        
        # Save instructions to file
        with open("WEBSITE_DEPLOYMENT_GUIDE.md", "w") as f:
            f.write(instructions)
            
        print("✅ Instructions saved to WEBSITE_DEPLOYMENT_GUIDE.md")

def main():
    print("🛡️ GuardianShield Simple Website Deployment")
    print("=" * 50)
    
    deployer = SimpleWebsiteDeployment()
    
    # Create deployment package
    deploy_dir = deployer.create_deployment_package()
    print(f"📁 Website package ready in: {deploy_dir}")
    
    # Create Docker version (optional)
    deployer.create_docker_version()
    
    # Show instructions
    deployer.show_deployment_instructions()
    
    print("\n🎉 Ready to deploy your GuardianShield website!")
    print("💡 Just follow the steps in WEBSITE_DEPLOYMENT_GUIDE.md")

if __name__ == "__main__":
    main()