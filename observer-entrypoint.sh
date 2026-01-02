#!/bin/bash

# GuardianShield Observer Container Entrypoint
# Initialize and start observer services with proper orchestration

set -euo pipefail

# Configuration
OBSERVER_USER="guardian"
CONFIG_DIR="/etc/guardian"
LOG_DIR="/var/log/guardian"
DATA_DIR="/home/guardian/blockchain-data"
SUPERVISOR_CONF="/etc/supervisor/supervisord.conf"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[OBSERVER]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OBSERVER]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[OBSERVER]${NC} $1"
}

log_error() {
    echo -e "${RED}[OBSERVER]${NC} $1"
}

# Initialize directories and permissions
initialize_directories() {
    log "Initializing directories and permissions..."
    
    # Create required directories
    mkdir -p "$LOG_DIR" "$DATA_DIR/blocks" "$DATA_DIR/transactions" "$DATA_DIR/index" "$DATA_DIR/cache"
    mkdir -p "/home/guardian/analytics/exports" "/home/guardian/analytics/reports"
    
    # Set proper ownership
    chown -R $OBSERVER_USER:$OBSERVER_USER "$LOG_DIR" "$DATA_DIR" "/home/guardian/analytics"
    
    # Set permissions
    chmod 755 "$LOG_DIR" "$DATA_DIR"
    chmod 700 "$DATA_DIR/blocks" "$DATA_DIR/transactions"  # Sensitive blockchain data
    
    log_success "Directory initialization complete"
}

# Validate configuration
validate_configuration() {
    log "Validating observer configuration..."
    
    if [ ! -f "$CONFIG_DIR/observer.json" ]; then
        log_error "Observer configuration file not found: $CONFIG_DIR/observer.json"
        exit 1
    fi
    
    # Validate JSON syntax
    if ! python3 -c "import json; json.load(open('$CONFIG_DIR/observer.json'))" 2>/dev/null; then
        log_error "Invalid JSON in observer configuration file"
        exit 1
    fi
    
    # Check required environment variables
    required_vars=("OBSERVER_REGION" "POSTGRES_HOST" "REDIS_HOST")
    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            log_error "Required environment variable not set: $var"
            exit 1
        fi
    done
    
    log_success "Configuration validation passed"
}

# Wait for dependencies to be ready
wait_for_dependencies() {
    log "Waiting for dependencies to be ready..."
    
    # Wait for PostgreSQL
    local postgres_host="${POSTGRES_HOST:-observer-postgres}"
    local postgres_port="${POSTGRES_PORT:-5432}"
    
    log "Waiting for PostgreSQL at $postgres_host:$postgres_port..."
    while ! timeout 1 bash -c "</dev/tcp/$postgres_host/$postgres_port"; do
        sleep 2
    done
    log_success "PostgreSQL is ready"
    
    # Wait for Redis
    local redis_host="${REDIS_HOST:-observer-redis}"
    local redis_port="${REDIS_PORT:-6379}"
    
    log "Waiting for Redis at $redis_host:$redis_port..."
    while ! timeout 1 bash -c "</dev/tcp/$redis_host/$redis_port"; do
        sleep 2
    done
    log_success "Redis is ready"
    
    # Wait for Elasticsearch (optional)
    local es_host="${ELASTICSEARCH_HOST:-observer-elasticsearch}"
    local es_port="9200"
    
    if [ -n "$es_host" ]; then
        log "Waiting for Elasticsearch at $es_host:$es_port..."
        local es_ready=false
        for i in {1..30}; do  # Wait up to 60 seconds
            if timeout 2 curl -sf "http://$es_host:$es_port/_cluster/health" > /dev/null 2>&1; then
                es_ready=true
                break
            fi
            sleep 2
        done
        
        if [ "$es_ready" = true ]; then
            log_success "Elasticsearch is ready"
        else
            log_warning "Elasticsearch not ready, continuing without search functionality"
        fi
    fi
}

# Initialize database schema
initialize_database() {
    log "Initializing database schema..."
    
    # Run database migrations/initialization
    if [ -f "/home/guardian/blockchain_observer.py" ]; then
        cd /home/guardian
        
        # Run as observer user
        su - $OBSERVER_USER -c "cd /home/guardian && python3 -c '
import asyncio
from blockchain_observer import BlockchainObserver

async def init_db():
    observer = BlockchainObserver()
    await observer.init_database()
    await observer.setup_database_schema()
    print(\"Database initialization complete\")
    
asyncio.run(init_db())
'" 2>/dev/null || log_warning "Database initialization skipped (may already be initialized)"
    fi
    
    log_success "Database initialization complete"
}

# Create supervisor configuration
setup_supervisor() {
    log "Setting up supervisor configuration..."
    
    cat > "$SUPERVISOR_CONF" << 'EOF'
[supervisord]
nodaemon=true
user=root
logfile=/var/log/guardian/supervisord.log
pidfile=/var/run/supervisord.pid
childlogdir=/var/log/guardian

[program:observer]
command=/home/guardian/analytics-venv/bin/python /home/guardian/blockchain_observer.py
directory=/home/guardian
user=guardian
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/guardian/observer.log
stdout_logfile_maxbytes=100MB
stdout_logfile_backups=5
environment=PYTHONUNBUFFERED=1

[program:indexer]
command=/home/guardian/analytics-venv/bin/python /home/guardian/blockchain_indexer.py
directory=/home/guardian
user=guardian
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/guardian/indexer.log
stdout_logfile_maxbytes=100MB
stdout_logfile_backups=5
environment=PYTHONUNBUFFERED=1

[program:analytics-api]
command=/home/guardian/analytics-venv/bin/python /home/guardian/analytics_api.py
directory=/home/guardian
user=guardian
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/guardian/analytics-api.log
stdout_logfile_maxbytes=100MB
stdout_logfile_backups=5
environment=PYTHONUNBUFFERED=1

[program:nginx]
command=/usr/sbin/nginx -g "daemon off;"
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/guardian/nginx.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=3

[unix_http_server]
file=/var/run/supervisor.sock
chmod=0700

[supervisorctl]
serverurl=unix:///var/run/supervisor.sock

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface
EOF
    
    log_success "Supervisor configuration created"
}

# Optimize system settings
optimize_system() {
    log "Applying system optimizations for analytics workload..."
    
    # File descriptor limits
    echo "guardian soft nofile 65536" >> /etc/security/limits.conf
    echo "guardian hard nofile 65536" >> /etc/security/limits.conf
    
    # Network optimizations
    sysctl -w net.core.rmem_max=134217728 2>/dev/null || true
    sysctl -w net.core.wmem_max=134217728 2>/dev/null || true
    sysctl -w net.ipv4.tcp_rmem="4096 65536 134217728" 2>/dev/null || true
    sysctl -w net.ipv4.tcp_wmem="4096 65536 134217728" 2>/dev/null || true
    
    # Disk I/O optimizations
    echo madvise > /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null || true
    
    log_success "System optimizations applied"
}

# Health check setup
setup_health_checks() {
    log "Setting up health check monitoring..."
    
    # Create health check cron job
    echo "*/2 * * * * /home/guardian/observer-healthcheck.sh > /dev/null 2>&1" | crontab -u $OBSERVER_USER -
    
    # Start cron service
    service cron start || log_warning "Could not start cron service"
    
    log_success "Health check monitoring configured"
}

# Signal handlers for graceful shutdown
cleanup() {
    log "Received shutdown signal, performing cleanup..."
    
    # Stop supervisor processes gracefully
    if pgrep supervisord > /dev/null; then
        supervisorctl stop all || true
        pkill -TERM supervisord || true
        
        # Wait for processes to terminate
        for i in {1..10}; do
            if ! pgrep supervisord > /dev/null; then
                break
            fi
            sleep 1
        done
        
        # Force kill if still running
        pkill -KILL supervisord 2>/dev/null || true
    fi
    
    log_success "Cleanup complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Main initialization
main() {
    log "🛡️  Starting GuardianShield Observer/Archive Node"
    log "Region: ${OBSERVER_REGION:-unknown}"
    log "Mode: ${OBSERVER_MODE:-archive}"
    
    # Run initialization steps
    initialize_directories
    validate_configuration
    wait_for_dependencies
    initialize_database
    setup_supervisor
    optimize_system
    setup_health_checks
    
    log_success "✅ Observer initialization complete"
    log "🚀 Starting observer services..."
    
    # Start services based on the command
    exec "$@"
}

# Execute main function with all arguments
main "$@"