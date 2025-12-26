#!/bin/bash
# GuardianShield Production Maintenance Script
# Manage, monitor, and maintain the production deployment

set -e

SCRIPT_DIR="/opt/guardianshield"
COMPOSE_FILE="docker-compose.production.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_help() {
    echo "🛡️  GuardianShield Production Maintenance"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  status          Show service status and health"
    echo "  logs [service]  Show logs (optional service name)"
    echo "  restart [service] Restart services (optional service name)"
    echo "  update          Update application code and restart"
    echo "  backup          Create manual backup"
    echo "  restore [file]  Restore from backup file"
    echo "  ssl-renew       Manually renew SSL certificates"
    echo "  monitor         Show real-time monitoring dashboard"
    echo "  scale [n]       Scale app service to n instances"
    echo "  security-scan   Run security checks"
    echo "  cleanup         Clean up old logs and temporary files"
    echo "  help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 status"
    echo "  $0 logs app"
    echo "  $0 restart nginx"
    echo "  $0 scale 6"
    echo "  $0 backup"
}

check_production() {
    if [ ! -f "$SCRIPT_DIR/$COMPOSE_FILE" ]; then
        echo -e "${RED}Error: Production environment not found. Run deploy_production.sh first.${NC}"
        exit 1
    fi
    cd "$SCRIPT_DIR"
}

show_status() {
    echo -e "${BLUE}🔍 GuardianShield Service Status${NC}"
    echo "======================================="
    
    # Docker compose status
    docker compose -f $COMPOSE_FILE ps
    
    echo ""
    echo -e "${BLUE}💾 Resource Usage${NC}"
    echo "=================="
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
    
    echo ""
    echo -e "${BLUE}🌐 Health Checks${NC}"
    echo "================"
    
    # Health check for main application
    if curl -s -f http://localhost:8000/api/health > /dev/null; then
        echo -e "API Server: ${GREEN}✅ Healthy${NC}"
    else
        echo -e "API Server: ${RED}❌ Unhealthy${NC}"
    fi
    
    # Database check
    if docker compose -f $COMPOSE_FILE exec -T db pg_isready -U guardianshield > /dev/null 2>&1; then
        echo -e "Database: ${GREEN}✅ Connected${NC}"
    else
        echo -e "Database: ${RED}❌ Connection Failed${NC}"
    fi
    
    # Redis check
    if docker compose -f $COMPOSE_FILE exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo -e "Redis: ${GREEN}✅ Connected${NC}"
    else
        echo -e "Redis: ${RED}❌ Connection Failed${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}📊 System Metrics${NC}"
    echo "================="
    echo "Disk Usage: $(df -h /opt/guardianshield | awk 'NR==2 {print $5}')"
    echo "Memory Usage: $(free | grep Mem | awk '{printf "%.1f%%\n", $3/$2 * 100.0}')"
    echo "Load Average: $(cat /proc/loadavg | awk '{print $1, $2, $3}')"
    echo "Uptime: $(uptime -p)"
}

show_logs() {
    local service=$1
    echo -e "${BLUE}📋 GuardianShield Logs${NC}"
    echo "====================="
    
    if [ -z "$service" ]; then
        docker compose -f $COMPOSE_FILE logs --tail=100 -f
    else
        docker compose -f $COMPOSE_FILE logs --tail=100 -f $service
    fi
}

restart_services() {
    local service=$1
    echo -e "${YELLOW}🔄 Restarting Services${NC}"
    
    if [ -z "$service" ]; then
        echo "Restarting all services..."
        docker compose -f $COMPOSE_FILE restart
    else
        echo "Restarting $service..."
        docker compose -f $COMPOSE_FILE restart $service
    fi
    
    echo -e "${GREEN}✅ Restart complete${NC}"
}

update_application() {
    echo -e "${BLUE}🚀 Updating GuardianShield${NC}"
    echo "=========================="
    
    # Create backup before update
    echo "Creating pre-update backup..."
    create_backup "pre-update"
    
    # Pull latest code (assuming git repo)
    if [ -d ".git" ]; then
        echo "Pulling latest code..."
        git pull
    else
        echo -e "${YELLOW}Warning: Not a git repository. Manual code update required.${NC}"
    fi
    
    # Rebuild and restart services
    echo "Rebuilding application..."
    docker compose -f $COMPOSE_FILE build --no-cache app
    
    echo "Restarting services..."
    docker compose -f $COMPOSE_FILE up -d
    
    echo -e "${GREEN}✅ Update complete${NC}"
    
    # Wait a bit and check health
    sleep 10
    show_status
}

create_backup() {
    local backup_type=${1:-"manual"}
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_dir="/opt/guardianshield/backups"
    
    echo -e "${BLUE}💾 Creating Backup ($backup_type)${NC}"
    echo "========================="
    
    mkdir -p $backup_dir
    
    # Database backup
    echo "Backing up database..."
    docker compose -f $COMPOSE_FILE exec -T db pg_dump -U guardianshield guardianshield_prod > "$backup_dir/db_backup_${backup_type}_${timestamp}.sql"
    
    # Application data backup
    echo "Backing up application data..."
    tar -czf "$backup_dir/data_backup_${backup_type}_${timestamp}.tar.gz" -C /opt/guardianshield data logs
    
    # Compress database backup
    gzip "$backup_dir/db_backup_${backup_type}_${timestamp}.sql"
    
    echo -e "${GREEN}✅ Backup created:${NC}"
    echo "   Database: $backup_dir/db_backup_${backup_type}_${timestamp}.sql.gz"
    echo "   Data: $backup_dir/data_backup_${backup_type}_${timestamp}.tar.gz"
}

restore_backup() {
    local backup_file=$1
    
    if [ -z "$backup_file" ]; then
        echo -e "${RED}Error: Please specify backup file to restore${NC}"
        echo "Available backups:"
        ls -la /opt/guardianshield/backups/
        exit 1
    fi
    
    echo -e "${YELLOW}⚠️  Restoring from backup: $backup_file${NC}"
    echo "This will overwrite current data. Are you sure? (y/N)"
    read -r confirm
    
    if [[ $confirm =~ ^[Yy]$ ]]; then
        echo "Stopping application..."
        docker compose -f $COMPOSE_FILE stop app
        
        echo "Restoring database..."
        if [[ $backup_file == *.gz ]]; then
            gunzip -c "$backup_file" | docker compose -f $COMPOSE_FILE exec -T db psql -U guardianshield -d guardianshield_prod
        else
            docker compose -f $COMPOSE_FILE exec -T db psql -U guardianshield -d guardianshield_prod < "$backup_file"
        fi
        
        echo "Restarting services..."
        docker compose -f $COMPOSE_FILE up -d
        
        echo -e "${GREEN}✅ Restore complete${NC}"
    else
        echo "Restore cancelled."
    fi
}

renew_ssl() {
    echo -e "${BLUE}🔒 Renewing SSL Certificates${NC}"
    echo "============================"
    
    docker compose -f $COMPOSE_FILE stop nginx
    certbot renew --standalone
    docker compose -f $COMPOSE_FILE start nginx
    
    echo -e "${GREEN}✅ SSL certificates renewed${NC}"
}

show_monitor() {
    echo -e "${BLUE}📊 Real-time Monitoring${NC}"
    echo "======================="
    echo "Press Ctrl+C to exit"
    echo ""
    
    while true; do
        clear
        show_status
        sleep 5
    done
}

scale_app() {
    local instances=$1
    
    if [ -z "$instances" ] || ! [[ "$instances" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}Error: Please specify number of instances (integer)${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}⚖️  Scaling application to $instances instances${NC}"
    docker compose -f $COMPOSE_FILE up -d --scale app=$instances
    echo -e "${GREEN}✅ Scaling complete${NC}"
    
    show_status
}

security_scan() {
    echo -e "${BLUE}🔒 Security Scan${NC}"
    echo "==============="
    
    echo "Checking for security updates..."
    apt list --upgradable 2>/dev/null | grep -i security || echo "No security updates available"
    
    echo ""
    echo "Checking SSL certificates..."
    for domain in "www.guardian-shield.io" "guardianshield-eth.com"; do
        cert_info=$(openssl s_client -connect $domain:443 -servername $domain </dev/null 2>/dev/null | openssl x509 -noout -dates 2>/dev/null || echo "Unable to check $domain")
        echo "$domain: $cert_info"
    done
    
    echo ""
    echo "Checking file permissions..."
    find /opt/guardianshield -type f -perm /o+w -ls 2>/dev/null || echo "No world-writable files found"
    
    echo ""
    echo "Checking running processes..."
    ps aux | grep -E "(nginx|python|postgres|redis)" | grep -v grep
}

cleanup_system() {
    echo -e "${BLUE}🧹 System Cleanup${NC}"
    echo "================="
    
    echo "Cleaning old logs..."
    find /opt/guardianshield/logs -name "*.log" -mtime +7 -delete
    
    echo "Cleaning old Docker images..."
    docker image prune -f
    
    echo "Cleaning old backups..."
    find /opt/guardianshield/backups -name "*.gz" -mtime +30 -delete
    
    echo "Cleaning temporary files..."
    find /tmp -name "*guardianshield*" -mtime +1 -delete 2>/dev/null || true
    
    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

# Main command handling
check_production

case "${1:-help}" in
    status)
        show_status
        ;;
    logs)
        show_logs $2
        ;;
    restart)
        restart_services $2
        ;;
    update)
        update_application
        ;;
    backup)
        create_backup
        ;;
    restore)
        restore_backup $2
        ;;
    ssl-renew)
        renew_ssl
        ;;
    monitor)
        show_monitor
        ;;
    scale)
        scale_app $2
        ;;
    security-scan)
        security_scan
        ;;
    cleanup)
        cleanup_system
        ;;
    help|*)
        show_help
        ;;
esac