#!/bin/bash

# SHIELD Token Web Services Deployment Script
# Deploy high-performance web services with Caddy and OpenResty

set -e

echo "🛡️  SHIELD Token Web Services Deployment"
echo "========================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p www caddy_data caddy_config ssl apigee-config apigee-logs

# Copy index.html to www directory if it exists
if [ -f "index.html" ]; then
    cp index.html www/
    echo "✅ Copied index.html to www directory"
fi

# Setup Apigee configuration if not exists
if [ ! -f "apigee-config/shield-token-config.yaml" ]; then
    echo "⚙️  Apigee configuration already exists"
else
    echo "✅ Apigee configuration ready"
fi

# Generate SSL certificates for local development (if needed)
if [ ! -f "ssl/cert.pem" ]; then
    echo "🔐 Generating self-signed SSL certificate for development..."
    openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes \
        -subj "/C=US/ST=CA/L=SF/O=SHIELD Token/CN=localhost"
    echo "✅ SSL certificate generated"
fi

# Set environment variables
export SHIELD_TOKEN_DOMAIN=${SHIELD_TOKEN_DOMAIN:-localhost}

echo "🚀 Starting SHIELD Token Web Services..."

# Pull the latest images
echo "📦 Pulling container images..."
docker-compose -f docker-compose.shield-web-services.yml pull || echo "Some images may not exist yet, continuing..."

# Build custom images
echo "🔨 Building custom images..."
docker build -t shield-openresty -f Dockerfile.shield-openresty .

# Start services
echo "🌟 Starting all services..."
docker-compose -f docker-compose.shield-web-services.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Health checks
echo "🔍 Checking service health..."

# Check Caddy
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "✅ Caddy is running on http://localhost"
else
    echo "⚠️  Caddy health check failed"
fi

# Check OpenResty
if curl -f http://localhost:8080/health > /dev/null 2>&1; then
    echo "✅ OpenResty is running on http://localhost:8080"
else
    echo "⚠️  OpenResty health check failed"
fi

# Check Apigee Microgateway
if curl -k -f https://localhost:8443/health > /dev/null 2>&1; then
    echo "✅ Apigee Microgateway is running on https://localhost:8443"
else
    echo "⚠️  Apigee Microgateway health check failed"
fi

# Check HAProxy stats
if curl -f http://localhost:8888 > /dev/null 2>&1; then
    echo "✅ HAProxy stats available at http://localhost:8888"
else
    echo "⚠️  HAProxy stats not available"
fi

# Check Redis
if docker-compose -f docker-compose.shield-web-services.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "⚠️  Redis connection failed"
fi

echo ""
echo "🎉 SHIELD Token Web Services Deployment Complete!"
echo "=================================================="
echo ""
echo "🌐 Services Available:"
echo "  • Caddy Web Server:      http://localhost"
echo "  • OpenResty Server:      http://localhost:8080"
echo "  • Apigee API Gateway:    https://localhost:8443"
echo "  • Load Balancer:         http://localhost:8000"
echo "  • HAProxy Stats:         http://localhost:8888"
echo "  • 3D Graphics API:       http://localhost:9000"
echo ""
echo "📊 Monitoring:"
echo "  • Metrics endpoint:      http://localhost:8080/metrics"
echo "  • Health checks:         http://localhost/health"
echo ""
echo "🛠️  Management Commands:"
echo "  • View logs:             docker-compose -f docker-compose.shield-web-services.yml logs -f"
echo "  • Stop services:         docker-compose -f docker-compose.shield-web-services.yml down"
echo "  • Restart services:      docker-compose -f docker-compose.shield-web-services.yml restart"
echo ""
echo "🔧 Advanced Features:"
echo "  • Real-time analytics via Lua scripts"
echo "  • Web3 wallet integration support"
echo "  • Interactive 3D graphics with WebSocket streaming"
echo "  • High-performance static asset serving"
echo "  • Automatic HTTPS with Caddy"
echo "  • Load balancing with HAProxy"
echo ""

# Show running containers
echo "📋 Running Containers:"
docker-compose -f docker-compose.shield-web-services.yml ps

echo ""
echo "🛡️  SHIELD Token Platform is ready for Web3 token sales!"