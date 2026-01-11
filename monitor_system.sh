#!/bin/bash
# GuardianShield Monitoring and Maintenance Script

echo "📊 GUARDIANSHIELD SYSTEM STATUS"
echo "==============================="
echo "Date: $(date)"
echo "Server: $(hostname)"
echo ""

# Check system resources
echo "💾 SYSTEM RESOURCES:"
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4}')%"
echo "Memory: $(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2 }')"
echo "Disk: $(df -h / | awk 'NR==2{print $5}') used"
echo ""

# Check services status
echo "🔧 SERVICE STATUS:"
services=("guardianshield-gallery" "guardianshield-api" "guardianshield-admin" "nginx" "postgresql" "redis-server")
for service in "${services[@]}"; do
    if systemctl is-active --quiet $service; then
        echo "✅ $service: Running"
    else
        echo "❌ $service: Not running"
    fi
done
echo ""

# Check SSL certificate expiration
echo "🔒 SSL CERTIFICATE STATUS:"
if command -v certbot &> /dev/null; then
    certbot certificates 2>/dev/null | grep -A1 "Certificate Name: guardian-shield.io" | tail -1 || echo "No certificates found"
else
    echo "Certbot not installed"
fi
echo ""

# Check domain connectivity
echo "🌐 DOMAIN CONNECTIVITY:"
domains=("guardian-shield.io" "agents.guardian-shield.io" "api.guardian-shield.io" "admin.guardian-shield.io")
for domain in "${domains[@]}"; do
    if curl -s -o /dev/null -w "%{http_code}" https://$domain | grep -q "200\|301\|302"; then
        echo "✅ $domain: Accessible"
    else
        echo "❌ $domain: Not accessible"
    fi
done
echo ""

# Show recent logs
echo "📝 RECENT ERRORS (last 24h):"
journalctl --since "24 hours ago" --priority=3 --no-pager | tail -5 || echo "No recent errors"
echo ""

# Disk usage warning
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "⚠️ WARNING: Disk usage is ${DISK_USAGE}%"
    echo "Consider cleaning up or expanding storage"
fi

echo "📊 Monitoring complete. Run 'sudo systemctl status SERVICE_NAME' for detailed service info."
