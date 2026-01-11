#!/bin/bash
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
