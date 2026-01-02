#!/bin/bash

# GuardianShield Universal Health Check
# Adapts to different node types automatically

set -euo pipefail

# Configuration
HEALTH_CHECK_LOG="/var/log/guardian/health-check.log"
NODE_TYPE="${NODE_TYPE:-unknown}"
NODE_ID="${NODE_ID:-unknown}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$NODE_TYPE] $1" | tee -a "$HEALTH_CHECK_LOG"
}

check_process() {
    local process_name="$1"
    if pgrep -f "$process_name" > /dev/null; then
        log "✓ Process $process_name is running"
        return 0
    else
        log "✗ Process $process_name is not running"
        return 1
    fi
}

check_port() {
    local port="$1"
    local description="$2"
    if timeout 2 bash -c "</dev/tcp/localhost/$port" 2>/dev/null; then
        log "✓ $description (port $port) is responding"
        return 0
    else
        log "✗ $description (port $port) is not responding"
        return 1
    fi
}

check_network_connectivity() {
    local target="$1"
    local port="$2"
    local description="$3"
    if timeout 3 bash -c "</dev/tcp/$target/$port" 2>/dev/null; then
        log "✓ Network connectivity to $description ($target:$port)"
        return 0
    else
        log "✗ Cannot connect to $description ($target:$port)"
        return 1
    fi
}

# Node-specific health checks
check_validator_health() {
    local failed=0
    
    # Check validator process
    check_process "validator_service.py" || ((failed++))
    
    # Check P2P networking (connects to sentries only)
    check_port "${P2P_PORT:-26656}" "P2P networking" || ((failed++))
    
    # Check RPC (serves sentries only)
    check_port "${RPC_PORT:-26657}" "Validator RPC" || ((failed++))
    
    # Check metrics
    check_port "${METRICS_PORT:-9090}" "Prometheus metrics" || ((failed++))
    
    # Check key management service
    if [ -f "/home/guardian/keys/validator_key.json" ]; then
        log "✓ Validator key file exists"
    else
        log "✗ Validator key file missing"
        ((failed++))
    fi
    
    # Check sentry connectivity (multi-layer networking)
    if [ "${NETWORK_MODE:-}" = "multi-layer" ]; then
        check_network_connectivity "sentry-us-east-01" "26656" "US-East Sentry" || log "⚠ Sentry connectivity warning"
        check_network_connectivity "sentry-eu-west-01" "26656" "EU-West Sentry" || log "⚠ Sentry connectivity warning"
    fi
    
    return $failed
}

check_sentry_health() {
    local failed=0
    
    # Check sentry processes
    check_process "sentry_api_service.py" || ((failed++))
    check_process "sentry_shield_service.py" || ((failed++))
    check_process "nginx" || ((failed++))
    
    # Check API endpoints
    check_port "80" "HTTP API" || ((failed++))
    check_port "443" "HTTPS API" || ((failed++))
    check_port "${RPC_PORT:-26657}" "RPC endpoint" || ((failed++))
    check_port "${API_PORT:-8080}" "WebSocket API" || ((failed++))
    
    # Check P2P networking
    check_port "${P2P_PORT:-26656}" "P2P networking" || ((failed++))
    
    # Check metrics
    check_port "${METRICS_PORT:-9090}" "Prometheus metrics" || ((failed++))
    
    # Check Redis connectivity (for rate limiting)
    if [ -n "${REDIS_HOST:-}" ]; then
        check_network_connectivity "${REDIS_HOST}" "6379" "Redis rate limiter" || ((failed++))
    fi
    
    # Check validator connectivity (upstream)
    if [ "${NETWORK_MODE:-}" = "multi-layer" ]; then
        check_network_connectivity "validator-us-east" "26657" "US-East Validator" || log "⚠ Validator connectivity warning"
        check_network_connectivity "validator-eu-west" "26657" "EU-West Validator" || log "⚠ Validator connectivity warning"
        check_network_connectivity "validator-asia-pacific" "26657" "Asia-Pacific Validator" || log "⚠ Validator connectivity warning"
    fi
    
    # Check rate limiting functionality
    if timeout 5 curl -sf "http://localhost:80/health" > /dev/null 2>&1; then
        log "✓ HTTP health endpoint responding"
    else
        log "✗ HTTP health endpoint not responding"
        ((failed++))
    fi
    
    return $failed
}

check_observer_health() {
    local failed=0
    
    # Check observer processes
    check_process "blockchain_observer_service.py" || ((failed++))
    check_process "blockchain_indexer_service.py" || ((failed++))
    check_process "analytics_api_service.py" || ((failed++))
    
    # Check API endpoints
    check_port "8545" "JSON-RPC API" || ((failed++))
    check_port "${API_PORT:-8080}" "Analytics API" || ((failed++))
    
    # Check metrics
    check_port "${METRICS_PORT:-9090}" "Prometheus metrics" || ((failed++))
    
    # Check database connectivity
    if [ -n "${POSTGRES_HOST:-}" ]; then
        check_network_connectivity "${POSTGRES_HOST}" "${POSTGRES_PORT:-5432}" "PostgreSQL database" || ((failed++))
    fi
    
    # Check Redis connectivity
    if [ -n "${REDIS_HOST:-}" ]; then
        check_network_connectivity "${REDIS_HOST}" "${REDIS_PORT:-6379}" "Redis cache" || ((failed++))
    fi
    
    # Check Elasticsearch connectivity
    if [ -n "${ELASTICSEARCH_HOST:-}" ]; then
        check_network_connectivity "${ELASTICSEARCH_HOST}" "9200" "Elasticsearch search" || log "⚠ Elasticsearch not available"
    fi
    
    # Check sentry connectivity (data source)
    if [ "${NETWORK_MODE:-}" = "multi-layer" ]; then
        check_network_connectivity "sentry-us-east-01" "26657" "US-East Sentry (data source)" || log "⚠ Sentry connectivity warning"
    fi
    
    # Check recent data ingestion
    if command -v psql > /dev/null 2>&1 && [ -n "${POSTGRES_HOST:-}" ]; then
        local recent_blocks
        recent_blocks=$(psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER:-observer}" -d "${POSTGRES_DB:-guardian_analytics}" -t -c \
            "SELECT COUNT(*) FROM blocks WHERE timestamp > NOW() - INTERVAL '10 minutes';" 2>/dev/null | tr -d ' ' || echo "0")
        
        if [ "${recent_blocks}" -gt 0 ]; then
            log "✓ Recent data ingestion active ($recent_blocks blocks in last 10 minutes)"
        else
            log "⚠ No recent data ingestion detected"
        fi
    fi
    
    return $failed
}

check_bootnode_health() {
    local failed=0
    
    # Check bootnode process
    check_process "bootnode_service.py" || ((failed++))
    
    # Check P2P networking (discovery only)
    check_port "${P2P_PORT:-26656}" "P2P discovery" || ((failed++))
    
    # Check metrics
    check_port "${METRICS_PORT:-9090}" "Prometheus metrics" || ((failed++))
    
    # Check peer discovery functionality
    if [ -f "/home/guardian/blockchain-data/addrbook.json" ]; then
        local peer_count
        peer_count=$(jq '.addrs | length' /home/guardian/blockchain-data/addrbook.json 2>/dev/null || echo "0")
        if [ "$peer_count" -gt 0 ]; then
            log "✓ Peer discovery active ($peer_count known peers)"
        else
            log "⚠ No peers discovered yet"
        fi
    fi
    
    return $failed
}

# System-level health checks (common to all nodes)
check_system_health() {
    local failed=0
    
    # Check disk space
    local usage
    usage=$(df /home/guardian/blockchain-data | awk 'NR==2 {print $5}' | sed 's/%//' 2>/dev/null || echo "0")
    if [ "$usage" -lt 90 ]; then
        log "✓ Disk space usage: ${usage}%"
    else
        log "✗ Disk space critical: ${usage}%"
        ((failed++))
    fi
    
    # Check memory usage
    local mem_usage
    mem_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2 }' 2>/dev/null || echo "0")
    if [ "$mem_usage" -lt 95 ]; then
        log "✓ Memory usage: ${mem_usage}%"
    else
        log "✗ Memory usage critical: ${mem_usage}%"
        ((failed++))
    fi
    
    # Check supervisor status
    if pgrep supervisord > /dev/null; then
        log "✓ Supervisor daemon is running"
    else
        log "✗ Supervisor daemon not running"
        ((failed++))
    fi
    
    return $failed
}

# Main health check execution
main() {
    log "Starting health check for $NODE_TYPE node: $NODE_ID"
    
    local total_failed=0
    
    # System-level checks first
    check_system_health || total_failed=$((total_failed + $?))
    
    # Node-specific checks
    case "$NODE_TYPE" in
        "validator")
            check_validator_health || total_failed=$((total_failed + $?))
            ;;
        "sentry")
            check_sentry_health || total_failed=$((total_failed + $?))
            ;;
        "observer")
            check_observer_health || total_failed=$((total_failed + $?))
            ;;
        "bootnode")
            check_bootnode_health || total_failed=$((total_failed + $?))
            ;;
        *)
            log "⚠ Unknown node type: $NODE_TYPE"
            total_failed=1
            ;;
    esac
    
    # Final status
    if [ $total_failed -eq 0 ]; then
        log "✅ Health check PASSED for $NODE_TYPE node"
        exit 0
    else
        log "❌ Health check FAILED for $NODE_TYPE node ($total_failed issues)"
        exit 1
    fi
}

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$HEALTH_CHECK_LOG")"

# Execute main function
main "$@"