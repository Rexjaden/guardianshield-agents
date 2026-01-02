#!/bin/bash
set -e

# Simple, clean entrypoint for GuardianShield nodes
# No chown commands - container runs as guardian user

log() {
    echo "[GUARDIAN] $1"
}

log_success() {
    echo "[GUARDIAN] ✅ $1"
}

log_warning() {
    echo "[GUARDIAN] ⚠️ $1"
}

log_error() {
    echo "[GUARDIAN] ❌ $1"
}

# Initialize directories with proper permissions
init_directories() {
    log "Initializing directories for ${NODE_TYPE:-unknown} node..."
    
    # Create directories
    mkdir -p /home/guardian/{blockchain-data,logs,config,keys,scripts,monitoring}
    
    # Set permissions (no chown needed - already running as guardian)
    chmod 755 /home/guardian/blockchain-data
    chmod 755 /home/guardian/logs
    chmod 755 /home/guardian/config
    chmod 700 /home/guardian/keys  # Private keys need restricted access
    
    log_success "Directories initialized successfully"
}

# Start node based on type
start_node() {
    local node_type="${NODE_TYPE:-validator}"
    
    log "🛡️ Starting GuardianShield ${node_type} Node"
    log "Region: ${REGION:-us-east}, Tier: ${TIER:-unknown}"
    log "Network Mode: ${NETWORK_MODE:-multi-layer}"
    
    init_directories
    
    # Generate node configuration
    python3 /home/guardian/guardian-node-manager.py --node-type="${node_type}" --init
    
    # Start the node service
    case "${node_type}" in
        "validator"|"sentry"|"observer"|"bootnode")
            log "Starting ${node_type} service..."
            python3 /home/guardian/universal_node_service.py
            ;;
        *)
            log_error "Unknown node type: ${node_type}"
            exit 1
            ;;
    esac
}

# Health check function
health_check() {
    bash /home/guardian/universal-healthcheck.sh
}

# Main execution
main() {
    case "${1:-start}" in
        "start")
            start_node
            ;;
        "health")
            health_check
            ;;
        *)
            log_error "Unknown command: $1"
            log "Usage: $0 [start|health]"
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"