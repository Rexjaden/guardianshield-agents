#!/bin/bash
# GuardianShield Let's Encrypt SSL Certificate Setup
# Run this script on your production server

echo "🔒 Setting up SSL certificates for guardian-shield.io"

# Install Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx -y

# Stop nginx temporarily
sudo systemctl stop nginx

# Obtain SSL certificate
sudo certbot certonly --standalone \
    -d guardian-shield.io \
    -d www.guardian-shield.io \
    --email security@guardian-shield.io \
    --agree-tos \
    --non-interactive

# Install nginx configuration
sudo cp nginx_config/guardian-shield.io.conf /etc/nginx/sites-available/guardian-shield.io
sudo ln -s /etc/nginx/sites-available/guardian-shield.io /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Start nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Set up automatic certificate renewal
echo "0 0,12 * * * root python3 -c 'import random; import time; time.sleep(random.random() * 3600)' && certbot renew -q" | sudo tee -a /etc/crontab > /dev/null

echo "✅ SSL certificates installed successfully!"
echo "🔒 Your site is now secure at https://guardian-shield.io"

# Test SSL configuration
echo "🧪 Testing SSL configuration..."
curl -I https://guardian-shield.io || echo "⚠️ SSL test failed - check configuration"

echo "📊 SSL rating test (optional):"
echo "Visit: https://www.ssllabs.com/ssltest/analyze.html?d=guardian-shield.io"
