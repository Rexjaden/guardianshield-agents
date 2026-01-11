#!/bin/bash
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
