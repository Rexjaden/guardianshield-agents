#!/bin/bash

# GuardianShield Universal Node Entrypoint
# Configures and starts any node type based on environment variables

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[GUARDIAN]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[GUARDIAN]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[GUARDIAN]${NC} $1"
}

log_error() {
    echo -e "${RED}[GUARDIAN]${NC} $1"
}

# Initialize directories and permissions
initialize_directories() {
    log "Initializing directories for ${NODE_TYPE:-unknown} node..."
    
    # Create all necessary directories
    mkdir -p /home/guardian/{blockchain-data,logs,config,keys,scripts,monitoring,networking}
    mkdir -p /home/guardian/guardian-configs/{validator,sentry,observer,bootnode,shared}
    
    # Note: No need for chown since container runs as guardian user
    
    # Set permissions based on node type
    case "${NODE_TYPE:-}" in
        "validator")
            chmod 700 /home/guardian/keys  # Sensitive key material
            chmod 750 /home/guardian/blockchain-data
            ;;
        "sentry")
            chmod 755 /home/guardian/blockchain-data  # Less restrictive for API access
            chmod 755 /home/guardian/logs
            ;;
        "observer")
            chmod 755 /home/guardian/blockchain-data
            mkdir -p /home/guardian/analytics/{exports,reports,cache}
            chmod 755 /home/guardian/analytics  # No chown needed, already guardian user
            ;;
        "bootnode")
            chmod 755 /home/guardian/blockchain-data
            # Minimal permissions for bootnode
            ;;
    esac
    
    log_success "Directory initialization complete"
}

# Wait for dependencies based on node type
wait_for_dependencies() {
    log "Waiting for dependencies..."
    
    # Common dependencies
    dependencies=()
    
    case "${NODE_TYPE:-}" in
        "validator")
            # Validators need minimal external dependencies
            log "Validator node requires minimal dependencies"
            ;;
        "sentry")
            # Sentries need Redis for rate limiting
            dependencies+=("${REDIS_HOST:-redis}:${REDIS_PORT:-6379}")
            ;;
        "observer")
            # Observers need database systems
            dependencies+=("${POSTGRES_HOST:-observer-postgres}:${POSTGRES_PORT:-5432}")
            dependencies+=("${REDIS_HOST:-observer-redis}:${REDIS_PORT:-6379}")
            if [ -n "${ELASTICSEARCH_HOST:-}" ]; then
                dependencies+=("${ELASTICSEARCH_HOST}:9200")
            fi
            ;;
        "bootnode")
            # Bootnodes are self-contained
            log "Bootnode requires no external dependencies"
            ;;
    esac
    
    # Wait for each dependency
    for dep in "${dependencies[@]}"; do
        IFS=':' read -r host port <<< "$dep"
        log "Waiting for $host:$port..."
        
        local max_attempts=30
        local attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            if timeout 2 bash -c "</dev/tcp/$host/$port" 2>/dev/null; then
                log_success "$host:$port is ready"
                break
            fi
            
            if [ $attempt -eq $max_attempts ]; then
                log_warning "$host:$port is not available after $max_attempts attempts"
                break
            fi
            
            sleep 2
            ((attempt++))
        done
    done
}

# Create node-specific configuration
create_node_config() {
    log "Creating configuration for ${NODE_TYPE:-unknown} node..."
    
    # Create base configuration
    cat > /home/guardian/guardian-configs/node-config.json << EOF
{
    "node_type": "${NODE_TYPE:-}",
    "node_id": "${NODE_ID:-guardian-${NODE_TYPE:-unknown}-${NODE_REGION:-unknown}}",
    "region": "${NODE_REGION:-us-east}",
    "tier": "${NODE_TIER:-primary}",
    "network_mode": "${NETWORK_MODE:-multi-layer}",
    "security_mode": "${SECURITY_MODE:-standard}",
    "bind_address": "${BIND_ADDRESS:-0.0.0.0}",
    "p2p_port": ${P2P_PORT:-26656},
    "rpc_port": ${RPC_PORT:-26657},
    "api_port": ${API_PORT:-8080},
    "metrics_port": ${METRICS_PORT:-9090}
}
EOF
    
    # Create node-specific configuration directory and files
    case "${NODE_TYPE:-}" in
        "validator")
            mkdir -p /home/guardian/guardian-configs/validator
            cat > /home/guardian/guardian-configs/validator/config.json << EOF
{
    "consensus": {
        "timeout_propose": "3s",
        "timeout_propose_delta": "500ms",
        "timeout_prevote": "1s",
        "timeout_prevote_delta": "500ms",
        "timeout_precommit": "1s",
        "timeout_precommit_delta": "500ms",
        "timeout_commit": "5s"
    },
    "security": {
        "private_key_file": "/home/guardian/keys/validator_key.json",
        "keyring_backend": "file",
        "allow_duplicate_ip": false
    },
    "networking": {
        "max_num_inbound_peers": 10,
        "max_num_outbound_peers": 10,
        "persistent_peers_max_dial_period": "0s",
        "pex": false,
        "seed_mode": false,
        "addr_book_strict": true
    }
}
EOF
            ;;
        "sentry")
            mkdir -p /home/guardian/guardian-configs/sentry
            cat > /home/guardian/guardian-configs/sentry/config.json << EOF
{
    "api_gateway": {
        "rate_limits": {
            "requests_per_minute": ${RATE_LIMIT_RPM:-1000},
            "requests_per_ip_per_minute": ${RATE_LIMIT_IP_RPM:-100},
            "concurrent_connections_per_ip": ${MAX_CONN_PER_IP:-20}
        },
        "ddos_protection": {
            "max_request_size": ${MAX_REQUEST_SIZE:-2097152},
            "timeout_seconds": ${REQUEST_TIMEOUT:-30},
            "ban_threshold": ${BAN_THRESHOLD:-100},
            "ban_duration_minutes": ${BAN_DURATION:-60}
        }
    },
    "networking": {
        "max_num_inbound_peers": 100,
        "max_num_outbound_peers": 50,
        "pex": true,
        "seed_mode": false
    },
    "load_balancer_tier": "${LOAD_BALANCER_TIER:-primary}"
}
EOF
            ;;
        "observer")
            mkdir -p /home/guardian/guardian-configs/observer
            cat > /home/guardian/guardian-configs/observer/config.json << EOF
{
    "database": {
        "host": "${POSTGRES_HOST:-observer-postgres}",
        "port": ${POSTGRES_PORT:-5432},
        "database": "${POSTGRES_DB:-guardian_analytics}",
        "username": "${POSTGRES_USER:-observer}",
        "max_connections": ${DB_MAX_CONN:-20}
    },
    "redis": {
        "host": "${REDIS_HOST:-observer-redis}",
        "port": ${REDIS_PORT:-6379},
        "db": ${REDIS_DB:-0}
    },
    "elasticsearch": {
        "hosts": ["${ELASTICSEARCH_HOST:-observer-elasticsearch}:9200"]
    },
    "indexing": {
        "batch_size": ${INDEXING_BATCH_SIZE:-500},
        "worker_count": ${INDEXING_WORKERS:-4},
        "enable_transaction_indexing": ${ENABLE_TX_INDEXING:-true},
        "enable_event_indexing": ${ENABLE_EVENT_INDEXING:-true}
    },
    "performance": {
        "max_block_cache": ${MAX_BLOCK_CACHE:-50000},
        "max_transaction_cache": ${MAX_TX_CACHE:-200000}
    }
}
EOF
            ;;
        "bootnode")
            mkdir -p /home/guardian/guardian-configs/bootnode
            cat > /home/guardian/guardian-configs/bootnode/config.json << EOF
{
    "networking": {
        "max_num_inbound_peers": 200,
        "max_num_outbound_peers": 50,
        "pex": true,
        "seed_mode": true,
        "addr_book_strict": false
    },
    "discovery": {
        "enable_upnp": false,
        "external_address": "${EXTERNAL_ADDRESS:-}",
        "bootstrap_peers": []
    }
}
EOF
            ;;
    esac
    
    log_success "Node configuration created"
}

# Setup networking based on multi-layer architecture
setup_networking() {
    log "Setting up networking for ${NODE_TYPE:-unknown} node..."
    
    # Configure hosts for service discovery
    cat >> /etc/hosts << EOF

# GuardianShield Service Discovery
# Validator Nodes
172.20.10.10 validator-us-east
172.20.10.11 validator-eu-west  
172.20.10.12 validator-asia-pacific

# Sentry Nodes
172.20.20.10 sentry-us-east-01
172.20.20.11 sentry-us-east-02
172.20.20.20 sentry-eu-west-01
172.20.20.21 sentry-eu-west-02
172.20.20.30 sentry-asia-pacific-01
172.20.20.31 sentry-asia-pacific-02

# Observer Nodes
172.20.30.10 observer-us-east
172.20.30.20 observer-eu-central
172.20.30.30 observer-asia-southeast

# Bootnode Nodes
172.20.40.10 bootnode-us-east
172.20.40.20 bootnode-eu-west
172.20.40.30 bootnode-asia-pacific

# Infrastructure Services
172.20.50.10 observer-postgres
172.20.50.11 observer-redis
172.20.50.12 observer-elasticsearch
EOF
    
    log_success "Networking configuration complete"
}

# Apply security hardening
apply_security_hardening() {
    log "Applying security hardening for ${NODE_TYPE:-unknown} node..."
    
    # Basic security for all nodes
    
    # Disable unnecessary services
    systemctl stop apache2 2>/dev/null || true
    systemctl disable apache2 2>/dev/null || true
    systemctl stop sendmail 2>/dev/null || true
    systemctl disable sendmail 2>/dev/null || true
    
    # Configure basic firewall rules (node-specific rules applied by node manager)
    iptables -F
    iptables -A INPUT -i lo -j ACCEPT
    iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
    
    # SSH access (if enabled)
    if [ "${ENABLE_SSH:-false}" = "true" ]; then
        iptables -A INPUT -p tcp --dport 22 -j ACCEPT
    fi
    
    # Configure fail2ban based on node type
    if [ "${NODE_TYPE:-}" = "sentry" ] || [ "${NODE_TYPE:-}" = "observer" ]; then
        systemctl enable fail2ban || log_warning "fail2ban not available"
        systemctl start fail2ban || log_warning "fail2ban failed to start"
    fi
    
    log_success "Basic security hardening applied"
}

# Configure monitoring
setup_monitoring() {
    log "Setting up monitoring for ${NODE_TYPE:-unknown} node..."
    
    # Create Prometheus configuration
    mkdir -p /home/guardian/metrics
    chmod 644 /home/guardian/metrics  # No chown needed, already guardian user
    
    # Enable metrics collection based on configuration
    if [ "${PROMETHEUS_ENABLED:-true}" = "true" ]; then
        log "Prometheus metrics enabled on port ${METRICS_PORT:-9090}"
    fi
    
    # Setup log rotation
    cat > /home/guardian/logs/logrotate-${NODE_TYPE:-unknown}.conf << EOF
/home/guardian/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    create 644 guardian guardian
    postrotate
        supervisorctl restart all || true
    endscript
}
EOF
    
    log_success "Monitoring setup complete"
}

# Run the node configuration manager
configure_node() {
    log "Running GuardianShield node configuration manager..."
    
    # Switch to guardian user and run configuration
    su - guardian -c "cd /home/guardian && /home/guardian/guardian-venv/bin/python /home/guardian/guardian-node-manager.py"
    
    if [ $? -eq 0 ]; then
        log_success "Node configuration completed successfully"
    else
        log_error "Node configuration failed"
        exit 1
    fi
}

# Main initialization function
main() {
    log "🛡️  Starting GuardianShield ${NODE_TYPE:-Unknown} Node"
    log "Region: ${NODE_REGION:-unknown}, Tier: ${NODE_TIER:-unknown}"
    log "Network Mode: ${NETWORK_MODE:-multi-layer}"
    
    # Validate required environment variables
    if [ -z "${NODE_TYPE:-}" ]; then
        log_error "NODE_TYPE environment variable is required"
        log "Valid types: validator, sentry, observer, bootnode"
        exit 1
    fi
    
    # Run initialization steps
    initialize_directories
    create_node_config
    setup_networking
    wait_for_dependencies
    apply_security_hardening
    setup_monitoring
    configure_node
    
    log_success "✅ GuardianShield ${NODE_TYPE} node initialization complete"
    log "🚀 Starting node services..."
    
    # Execute the command passed to the container
    exec "$@"
}

# Signal handlers for graceful shutdown
cleanup() {
    log "Received shutdown signal, performing cleanup..."
    
    if pgrep supervisord > /dev/null; then
        supervisorctl stop all || true
        pkill -TERM supervisord || true
        
        # Wait for graceful shutdown
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

# Execute main function
main "$@"