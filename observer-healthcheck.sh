#!/bin/bash

# GuardianShield Observer Health Check Script
# Comprehensive health monitoring for observer nodes

set -euo pipefail

# Configuration
OBSERVER_CONFIG="/etc/guardian/observer.json"
HEALTH_CHECK_LOG="/var/log/guardian/health-check.log"
ERROR_COUNT_FILE="/tmp/observer-health-errors"
MAX_CONSECUTIVE_ERRORS=3

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$HEALTH_CHECK_LOG"
}

# Error counting
increment_error_count() {
    local count=0
    if [ -f "$ERROR_COUNT_FILE" ]; then
        count=$(cat "$ERROR_COUNT_FILE")
    fi
    count=$((count + 1))
    echo "$count" > "$ERROR_COUNT_FILE"
    return "$count"
}

reset_error_count() {
    echo "0" > "$ERROR_COUNT_FILE"
}

# Health check functions
check_observer_process() {
    if pgrep -f "blockchain_observer.py" > /dev/null; then
        log "✓ Observer process is running"
        return 0
    else
        log "✗ Observer process is not running"
        return 1
    fi
}

check_indexer_process() {
    if pgrep -f "blockchain_indexer.py" > /dev/null; then
        log "✓ Indexer process is running"
        return 0
    else
        log "✗ Indexer process is not running"
        return 1
    fi
}

check_database_connection() {
    local db_host="observer-postgres"
    local db_port="5432"
    local db_name="guardian_analytics"
    
    if timeout 5 pg_isready -h "$db_host" -p "$db_port" -d "$db_name" > /dev/null 2>&1; then
        log "✓ Database connection is healthy"
        return 0
    else
        log "✗ Database connection failed"
        return 1
    fi
}

check_redis_connection() {
    local redis_host="observer-redis"
    local redis_port="6379"
    
    if timeout 3 redis-cli -h "$redis_host" -p "$redis_port" ping > /dev/null 2>&1; then
        log "✓ Redis connection is healthy"
        return 0
    else
        log "✗ Redis connection failed"
        return 1
    fi
}

check_elasticsearch_connection() {
    local es_host="observer-elasticsearch"
    local es_port="9200"
    
    if timeout 5 curl -sf "http://$es_host:$es_port/_cluster/health" > /dev/null 2>&1; then
        log "✓ Elasticsearch connection is healthy"
        return 0
    else
        log "✗ Elasticsearch connection failed"
        return 1
    fi
}

check_api_endpoint() {
    local api_port="8080"
    
    if timeout 5 curl -sf "http://localhost:$api_port/health" > /dev/null 2>&1; then
        log "✓ Analytics API is responding"
        return 0
    else
        log "✗ Analytics API is not responding"
        return 1
    fi
}

check_metrics_endpoint() {
    local metrics_port="9090"
    
    if timeout 5 curl -sf "http://localhost:$metrics_port/metrics" > /dev/null 2>&1; then
        log "✓ Metrics endpoint is responding"
        return 0
    else
        log "✗ Metrics endpoint is not responding"
        return 1
    fi
}

check_disk_space() {
    local usage
    usage=$(df /home/guardian/blockchain-data | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$usage" -lt 90 ]; then
        log "✓ Disk space usage is healthy ($usage%)"
        return 0
    else
        log "✗ Disk space usage is critical ($usage%)"
        return 1
    fi
}

check_memory_usage() {
    local usage
    usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2 }')
    
    if [ "$usage" -lt 95 ]; then
        log "✓ Memory usage is healthy ($usage%)"
        return 0
    else
        log "✗ Memory usage is critical ($usage%)"
        return 1
    fi
}

check_recent_blocks() {
    local last_block_time
    
    # Check if we've processed blocks recently (within last 5 minutes)
    if command -v psql > /dev/null 2>&1; then
        last_block_time=$(psql -h observer-postgres -U observer -d guardian_analytics -t -c \
            "SELECT EXTRACT(EPOCH FROM (NOW() - MAX(timestamp))) FROM blocks;" 2>/dev/null | tr -d ' ' || echo "999999")
        
        if [ "${last_block_time%.*}" -lt 300 ]; then  # Less than 5 minutes ago
            log "✓ Recent blocks are being processed"
            return 0
        else
            log "✗ No recent blocks processed (${last_block_time%.*}s ago)"
            return 1
        fi
    else
        log "⚠ Cannot check recent blocks (psql not available)"
        return 0  # Don't fail if we can't check
    fi
}

# Main health check execution
main() {
    log "Starting GuardianShield Observer health check..."
    
    local failed_checks=0
    local total_checks=0
    
    # Core service checks
    checks=(
        "check_observer_process"
        "check_indexer_process"
        "check_database_connection"
        "check_redis_connection"
        "check_elasticsearch_connection"
        "check_api_endpoint"
        "check_metrics_endpoint"
        "check_disk_space"
        "check_memory_usage"
        "check_recent_blocks"
    )
    
    for check in "${checks[@]}"; do
        total_checks=$((total_checks + 1))
        if ! "$check"; then
            failed_checks=$((failed_checks + 1))
        fi
    done
    
    # Determine overall health status
    if [ "$failed_checks" -eq 0 ]; then
        log "✅ All health checks passed ($total_checks/$total_checks)"
        reset_error_count
        exit 0
    else
        log "❌ Health check failed: $failed_checks/$total_checks checks failed"
        
        # Increment error count and check if we should alert
        error_count=$(increment_error_count)
        
        if [ "$error_count" -ge "$MAX_CONSECUTIVE_ERRORS" ]; then
            log "🚨 CRITICAL: $error_count consecutive health check failures"
            # Could send alert here
        fi
        
        exit 1
    fi
}

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$HEALTH_CHECK_LOG")"

# Run main function
main "$@"