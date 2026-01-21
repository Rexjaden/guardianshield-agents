#!/bin/bash
# SSL Certificate Setup Script for GuardianShield
# Run this when you're ready to enable HTTPS

DOMAIN="guardian-shield.io"
EMAIL="security@guardian-shield.io"
WEBROOT="/var/www/certbot"

echo "🔐 GuardianShield SSL Certificate Setup"
echo "========================================"

# Create webroot directory
mkdir -p $WEBROOT

# Step 1: Test with staging certificates first (recommended)
echo ""
echo "Step 1: Testing with Let's Encrypt staging server..."
docker run --rm \
  -v "$(pwd)/ssl:/etc/letsencrypt" \
  -v "$(pwd)/ssl_certificates:/var/lib/letsencrypt" \
  -v "$WEBROOT:/var/www/certbot" \
  certbot/certbot:latest certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email $EMAIL \
  --agree-tos \
  --no-eff-email \
  --staging \
  -d $DOMAIN \
  -d www.$DOMAIN \
  -d api.$DOMAIN \
  -d dashboard.$DOMAIN

# Step 2: If staging works, get real certificates
echo ""
echo "Step 2: If staging succeeded, run this for production certificates:"
echo ""
echo "docker run --rm \\"
echo "  -v \"\$(pwd)/ssl:/etc/letsencrypt\" \\"
echo "  -v \"\$(pwd)/ssl_certificates:/var/lib/letsencrypt\" \\"
echo "  -v \"$WEBROOT:/var/www/certbot\" \\"
echo "  certbot/certbot:latest certonly \\"
echo "  --webroot \\"
echo "  --webroot-path=/var/www/certbot \\"
echo "  --email $EMAIL \\"
echo "  --agree-tos \\"
echo "  --no-eff-email \\"
echo "  --force-renewal \\"
echo "  -d $DOMAIN \\"
echo "  -d www.$DOMAIN \\"
echo "  -d api.$DOMAIN \\"
echo "  -d dashboard.$DOMAIN"

echo ""
echo "Step 3: After certificates are obtained:"
echo "  1. Uncomment SSL server blocks in nginx-config/ssl-ready.conf"
echo "  2. Restart nginx: docker restart guardian-nginx-proxy"
echo ""
echo "Step 4: Set up auto-renewal (add to crontab):"
echo "  0 0 * * * docker run --rm -v /path/to/ssl:/etc/letsencrypt certbot/certbot renew --quiet"
