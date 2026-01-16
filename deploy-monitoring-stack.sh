#!/bin/bash
# GuardianShield ERC-8055 Complete Monitoring Stack Deployment
# AlertManager + Prometheus + Grafana for enterprise-grade monitoring

echo "🚨 Deploying GuardianShield ERC-8055 Complete Monitoring Stack..."

# Create required networks
echo "🌐 Setting up networking..."
docker network create guardianshield-network 2>/dev/null || echo "Network already exists"

# Deploy the complete monitoring stack
echo "📊 Deploying monitoring services..."
docker-compose -f docker-compose.monitoring-stack.yml up -d

# Wait for services to start
echo "⏳ Waiting for services to initialize..."
sleep 30

# Check service health
echo "🔍 Checking service health..."

services=(
    "guardianshield-alertmanager:9093"
    "guardianshield-prometheus-enhanced:9090"  
    "guardianshield-grafana-enhanced:3000"
)

for service in "${services[@]}"; do
    name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    
    if docker ps | grep -q $name; then
        echo "✅ $name is running"
    else
        echo "❌ $name failed to start"
    fi
done

# Display access information
echo ""
echo "🎉 ===== GUARDIANSHIELD ERC-8055 MONITORING DEPLOYED! ====="
echo ""
echo "🚨 AlertManager Dashboard:"
echo "   URL: http://localhost:9093"
echo "   Features: ERC-8055 alert management, notification routing"
echo ""
echo "📊 Prometheus Metrics:"
echo "   URL: http://localhost:9090"
echo "   Features: Shield Token metrics, Guard Token monitoring"
echo ""
echo "📈 Grafana Dashboards:"
echo "   URL: http://localhost:3000"
echo "   Login: admin / guardianshield2026"
echo "   Features: ERC-8055 visualizations, real-time monitoring"
echo ""
echo "🔔 Notification Gateway:"
echo "   URL: http://localhost:8060"
echo "   Features: Alert routing, webhook integrations"
echo ""
echo "🎯 Key Monitoring Features:"
echo "   ✅ ERC-8055 Shield Token burn/remint monitoring"
echo "   ✅ Guard Token (ERC-20) transaction tracking"  
echo "   ✅ Website performance and uptime monitoring"
echo "   ✅ Container and infrastructure health checks"
echo "   ✅ Automated alert routing and notifications"
echo ""
echo "🛡️ Your ERC-8055 system now has ENTERPRISE-GRADE MONITORING!"
echo ""
echo "📋 Quick Commands:"
echo "   View logs: docker logs guardianshield-alertmanager"
echo "   Restart:   docker-compose -f docker-compose.monitoring-stack.yml restart"
echo "   Stop:      docker-compose -f docker-compose.monitoring-stack.yml down"