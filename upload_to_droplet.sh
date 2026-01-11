#!/bin/bash
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
