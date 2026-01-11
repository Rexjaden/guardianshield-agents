#!/bin/bash
# SSL Certificate Setup for guardian-shield.io
# Run this after DNS is configured and propagated

set -e

echo "🔒 SETTING UP SSL CERTIFICATES..."
echo "================================="

# Check if domain resolves to this server
echo "🌐 Checking DNS resolution..."
SERVER_IP=$(curl -s ifconfig.me)
DOMAIN_IP=$(dig +short guardian-shield.io)

echo "Server IP: $SERVER_IP"
echo "Domain IP: $DOMAIN_IP"

if [ "$SERVER_IP" != "$DOMAIN_IP" ]; then
    echo "⚠️ WARNING: DNS not fully propagated yet"
    echo "Please wait for DNS propagation before running SSL setup"
    echo "You can check with: dig +short guardian-shield.io"
    exit 1
fi

echo "✅ DNS properly configured!"

# Obtain SSL certificates
echo "📜 Obtaining SSL certificates..."
certbot --nginx -d guardian-shield.io -d www.guardian-shield.io -d agents.guardian-shield.io -d api.guardian-shield.io -d admin.guardian-shield.io -d token.guardian-shield.io --non-interactive --agree-tos --email admin@guardian-shield.io

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
echo "• https://guardian-shield.io"
echo "• https://agents.guardian-shield.io"  
echo "• https://api.guardian-shield.io"
echo "• https://admin.guardian-shield.io"
echo "• https://token.guardian-shield.io"
echo ""
echo "✅ Auto-renewal configured"
echo "🔄 Certificates will auto-renew every 90 days"
