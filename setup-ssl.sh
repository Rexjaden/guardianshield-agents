#!/bin/bash

# GuardianShield SSL Certificate Setup Script
# This script will properly set up Let's Encrypt certificates

set -e

echo "🔐 Starting GuardianShield SSL Certificate Setup..."

# Stop any existing containers that might interfere
echo "Stopping existing containers..."
docker stop guardianshield-proxy guardianshield-certbot 2>/dev/null || true
docker rm guardianshield-proxy guardianshield-certbot 2>/dev/null || true

# Create necessary directories
echo "Creating certificate directories..."
mkdir -p ./certbot/conf
mkdir -p ./certbot/www
mkdir -p ./certbot/logs

# Start nginx with HTTP-only configuration
echo "Starting HTTP-only nginx for certificate validation..."
docker run -d \
  --name guardianshield-proxy-temp \
  --network guardianshield-network \
  -p 80:80 \
  -v "$(pwd)/nginx-temp.conf:/etc/nginx/nginx.conf:ro" \
  -v "$(pwd)/certbot/www:/var/www/certbot:ro" \
  nginx:alpine

# Wait for nginx to start
sleep 5

# Check if nginx is running
if ! docker ps | grep -q guardianshield-proxy-temp; then
  echo "❌ Failed to start temporary nginx server"
  exit 1
fi

echo "✅ Temporary nginx server started"

# Test domain accessibility
echo "🌐 Testing domain accessibility..."
DOMAINS="guardian-shield.io www.guardian-shield.io guardianshield.io www.guardianshield.io"

for domain in $DOMAINS; do
  echo "Testing $domain..."
  if curl -s -o /dev/null -w "%{http_code}" "http://$domain" | grep -q "200\|301\|302"; then
    echo "✅ $domain is accessible"
  else
    echo "⚠️ $domain may not be accessible"
  fi
done

# Generate certificates using certbot
echo "🔐 Generating SSL certificates..."
docker run --rm \
  --name guardianshield-certbot-temp \
  --network guardianshield-network \
  -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
  -v "$(pwd)/certbot/www:/var/www/certbot" \
  -v "$(pwd)/certbot/logs:/var/log/letsencrypt" \
  certbot/certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email admin@guardian-shield.io \
  --agree-tos \
  --no-eff-email \
  --force-renewal \
  -d guardian-shield.io \
  -d www.guardian-shield.io \
  -d guardianshield.io \
  -d www.guardianshield.io \
  --verbose

# Check if certificates were generated successfully
if [ -f "./certbot/conf/live/guardian-shield.io/fullchain.pem" ]; then
  echo "✅ SSL certificates generated successfully!"
  
  # Stop temporary nginx
  docker stop guardianshield-proxy-temp
  docker rm guardianshield-proxy-temp
  
  # Update nginx configuration to use SSL
  echo "📝 Updating nginx configuration for SSL..."
  cp nginx.conf nginx.conf.backup
  
  # Replace the SSL paths in nginx.conf
  sed -i 's|/etc/ssl/certs/live/|./certbot/conf/live/|g' nginx.conf
  
  # Start the full nginx server with SSL
  echo "🚀 Starting production nginx with SSL..."
  docker run -d \
    --name guardianshield-proxy \
    --network guardianshield-network \
    -p 80:80 -p 443:443 \
    -v "$(pwd)/nginx.conf:/etc/nginx/nginx.conf:ro" \
    -v "$(pwd)/certbot/conf:/etc/ssl/certs:ro" \
    -v "$(pwd)/certbot/www:/var/www/certbot:ro" \
    nginx:alpine

  echo "✅ GuardianShield is now running with SSL certificates!"
  echo "🌐 Your sites should now be accessible at:"
  echo "   https://guardian-shield.io"
  echo "   https://www.guardian-shield.io"
  echo "   https://guardianshield.io" 
  echo "   https://www.guardianshield.io"
  
else
  echo "❌ SSL certificate generation failed!"
  echo "Please check the logs above for details."
  
  # Show recent certbot logs
  echo "Recent certbot logs:"
  tail -20 ./certbot/logs/letsencrypt.log 2>/dev/null || echo "No log file found"
  
  exit 1
fi

# Set up certificate renewal
echo "⏰ Setting up automatic certificate renewal..."
cat > renew-certs.sh << 'EOF'
#!/bin/bash
docker run --rm \
  --name guardianshield-certbot-renew \
  --network guardianshield-network \
  -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
  -v "$(pwd)/certbot/www:/var/www/certbot" \
  -v "$(pwd)/certbot/logs:/var/log/letsencrypt" \
  certbot/certbot renew --quiet

# Reload nginx
docker exec guardianshield-proxy nginx -s reload
EOF

chmod +x renew-certs.sh

echo "🎉 SSL setup complete!"
echo "💡 Run ./renew-certs.sh to renew certificates"
echo "📅 Consider setting up a cron job to run renewal automatically"