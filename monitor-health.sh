#!/bin/bash
# GuardianShield Cluster Health Monitoring
# Comprehensive health checks and monitoring

set -e

# Configuration
STACK_NAME="guardianshield"
HEALTH_CHECK_INTERVAL=30
ALERT_THRESHOLD_CPU=80
ALERT_THRESHOLD_MEMORY=85
ALERT_THRESHOLD_DISK=90

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Icons
CHECK="✅"
WARN="⚠️"
ERROR="❌"
INFO="ℹ️"
FIRE="🔥"

print_header() {
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  🛡️  GuardianShield Cluster Health Monitor  🛡️             ${BLUE}║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}"
}

print_section() {
    echo -e "\n${CYAN}▶ $1${NC}"
    echo -e "${CYAN}$(printf '%.0s─' {1..50})${NC}"
}

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_critical() {
    echo -e "${RED}${FIRE}[CRITICAL]${NC} $1"
}

# Check Docker daemon health
check_docker_health() {
    print_section "Docker Daemon Health"
    
    if docker info >/dev/null 2>&1; then
        print_success "Docker daemon is running"
        
        local docker_version=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
        print_status "Docker version: $docker_version"
        
        # Check Docker daemon configuration
        local docker_info=$(docker system df --format "table {{.Type}}\t{{.Total}}\t{{.Active}}\t{{.Size}}\t{{.Reclaimable}}")
        echo "$docker_info"
        
    else
        print_critical "Docker daemon is not running or accessible"
        return 1
    fi
}

# Check Swarm cluster health
check_swarm_health() {
    print_section "Docker Swarm Cluster Health"
    
    local swarm_state=$(docker info --format '{{.Swarm.LocalNodeState}}')
    
    if [ "$swarm_state" = "active" ]; then
        print_success "Swarm cluster is active"
        
        # Node status
        print_status "Cluster nodes:"
        docker node ls --format "table {{.Hostname}}\t{{.Status}}\t{{.Availability}}\t{{.ManagerStatus}}" | while read line; do
            if echo "$line" | grep -q "Down\|Drain"; then
                print_warning "  $line"
            else
                print_success "  $line"
            fi
        done
        
        # Check for unhealthy nodes
        local unhealthy_nodes=$(docker node ls --filter status=down -q | wc -l)
        if [ $unhealthy_nodes -gt 0 ]; then
            print_warning "$unhealthy_nodes node(s) are down"
        fi
        
    else
        print_error "Swarm cluster is not active (state: $swarm_state)"
        return 1
    fi
}

# Check service health
check_service_health() {
    print_section "Service Health Status"
    
    local services=$(docker service ls --filter name=$STACK_NAME --format "{{.Name}}")
    local total_services=0
    local healthy_services=0
    local warning_services=0
    local critical_services=0
    
    for service in $services; do
        total_services=$((total_services + 1))
        
        local replicas=$(docker service ls --filter name="$service" --format "{{.Replicas}}")
        local desired=$(echo "$replicas" | cut -d'/' -f2)
        local running=$(echo "$replicas" | cut -d'/' -f1)
        
        if [ "$running" = "$desired" ] && [ "$desired" != "0" ]; then
            print_success "$service: $replicas (Healthy)"
            healthy_services=$((healthy_services + 1))
        elif [ "$running" -lt "$desired" ] && [ "$running" -gt 0 ]; then
            print_warning "$service: $replicas (Degraded)"
            warning_services=$((warning_services + 1))
        else
            print_error "$service: $replicas (Critical)"
            critical_services=$((critical_services + 1))
        fi
    done
    
    # Service health summary
    echo ""
    print_status "Service Health Summary:"
    echo "  Total Services: $total_services"
    echo "  ${CHECK} Healthy: $healthy_services"
    echo "  ${WARN} Warning: $warning_services"
    echo "  ${ERROR} Critical: $critical_services"
    
    # Overall service health percentage
    if [ $total_services -gt 0 ]; then
        local health_percentage=$((healthy_services * 100 / total_services))
        
        if [ $health_percentage -ge 90 ]; then
            print_success "Overall service health: $health_percentage%"
        elif [ $health_percentage -ge 70 ]; then
            print_warning "Overall service health: $health_percentage%"
        else
            print_critical "Overall service health: $health_percentage%"
        fi
    fi
}

# Check container health
check_container_health() {
    print_section "Container Health Checks"
    
    # Get containers related to our stack
    local containers=$(docker ps --filter name=$STACK_NAME --format "{{.Names}}\t{{.Status}}\t{{.Ports}}")
    
    if [ -n "$containers" ]; then
        echo "$containers" | while IFS=$'\t' read -r name status ports; do
            if echo "$status" | grep -q "Up.*healthy"; then
                print_success "$name: Healthy ($status)"
            elif echo "$status" | grep -q "Up.*unhealthy"; then
                print_error "$name: Unhealthy ($status)"
            elif echo "$status" | grep -q "Up"; then
                print_warning "$name: Running but no health check ($status)"
            else
                print_critical "$name: Not running ($status)"
            fi
        done
    else
        print_warning "No containers found for stack: $STACK_NAME"
    fi
    
    # Check for containers consuming too many resources
    print_status "Resource usage by container:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" | head -10
}

# Check network connectivity
check_network_health() {
    print_section "Network Connectivity"
    
    # Check overlay networks
    local networks=$(docker network ls --filter driver=overlay --format "{{.Name}}")
    
    for network in $networks; do
        if docker network inspect "$network" >/dev/null 2>&1; then
            print_success "Network '$network' is accessible"
        else
            print_error "Network '$network' has issues"
        fi
    done
    
    # Test API connectivity
    print_status "Testing API connectivity:"
    
    local api_endpoints=("http://localhost:8000/health" "http://localhost:80/health")
    
    for endpoint in "${api_endpoints[@]}"; do
        if curl -f -s -m 5 "$endpoint" >/dev/null 2>&1; then
            print_success "API endpoint reachable: $endpoint"
        else
            print_warning "API endpoint unreachable: $endpoint"
        fi
    done
}

# Check storage and volumes
check_storage_health() {
    print_section "Storage and Volume Health"
    
    # Docker volumes
    local volumes=$(docker volume ls --filter name=$STACK_NAME --format "{{.Name}}")
    
    for volume in $volumes; do
        if docker volume inspect "$volume" >/dev/null 2>&1; then
            local size=$(docker system df -v | grep "$volume" | awk '{print $3}' || echo "Unknown")
            print_success "Volume '$volume': $size"
        else
            print_error "Volume '$volume' has issues"
        fi
    done
    
    # Disk space check
    print_status "Disk space usage:"
    df -h | grep -E "/$|/var|/tmp" | while read line; do
        local usage=$(echo "$line" | awk '{print $5}' | sed 's/%//')
        local filesystem=$(echo "$line" | awk '{print $6}')
        
        if [ "$usage" -gt $ALERT_THRESHOLD_DISK ]; then
            print_critical "Disk usage critical: $line"
        elif [ "$usage" -gt 70 ]; then
            print_warning "Disk usage high: $line"
        else
            print_success "Disk usage normal: $line"
        fi
    done
}

# Check database health
check_database_health() {
    print_section "Database Health"
    
    # PostgreSQL health
    local postgres_container=$(docker ps --filter name=${STACK_NAME}_postgres --format "{{.ID}}" | head -1)
    
    if [ -n "$postgres_container" ]; then
        if docker exec "$postgres_container" pg_isready -U postgres >/dev/null 2>&1; then
            print_success "PostgreSQL is ready and accepting connections"
            
            # Check database size
            local db_size=$(docker exec "$postgres_container" psql -U postgres -c "SELECT pg_size_pretty(pg_database_size('guardianshield'));" -t 2>/dev/null | xargs)
            print_status "Database size: $db_size"
            
        else
            print_error "PostgreSQL is not ready"
        fi
    else
        print_warning "PostgreSQL container not found"
    fi
    
    # Redis health
    local redis_container=$(docker ps --filter name=${STACK_NAME}_redis --format "{{.ID}}" | head -1)
    
    if [ -n "$redis_container" ]; then
        if docker exec "$redis_container" redis-cli ping | grep -q "PONG"; then
            print_success "Redis is responding to ping"
            
            # Check Redis memory usage
            local redis_memory=$(docker exec "$redis_container" redis-cli info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
            print_status "Redis memory usage: $redis_memory"
            
        else
            print_error "Redis is not responding"
        fi
    else
        print_warning "Redis container not found"
    fi
}

# Check monitoring stack health
check_monitoring_health() {
    print_section "Monitoring Stack Health"
    
    # Prometheus health
    if curl -f -s -m 5 "http://localhost:9090/-/healthy" >/dev/null 2>&1; then
        print_success "Prometheus is healthy"
    else
        print_warning "Prometheus health check failed"
    fi
    
    # Grafana health
    if curl -f -s -m 5 "http://localhost:3000/api/health" >/dev/null 2>&1; then
        print_success "Grafana is healthy"
    else
        print_warning "Grafana health check failed"
    fi
    
    # ElasticSearch health
    if curl -f -s -m 5 "http://localhost:9200/_cluster/health" >/dev/null 2>&1; then
        print_success "ElasticSearch is healthy"
    else
        print_warning "ElasticSearch health check failed"
    fi
}

# Generate health score
generate_health_score() {
    print_section "Health Score Calculation"
    
    local total_checks=0
    local passed_checks=0
    local health_score=0
    
    # This is a simplified scoring system
    # In production, you'd want more sophisticated health scoring
    
    # Docker daemon (weight: 20)
    total_checks=$((total_checks + 20))
    if docker info >/dev/null 2>&1; then
        passed_checks=$((passed_checks + 20))
    fi
    
    # Swarm cluster (weight: 15)
    total_checks=$((total_checks + 15))
    if [ "$(docker info --format '{{.Swarm.LocalNodeState}}')" = "active" ]; then
        passed_checks=$((passed_checks + 15))
    fi
    
    # Services (weight: 30)
    total_checks=$((total_checks + 30))
    local healthy_ratio=$(docker service ls --filter name=$STACK_NAME --format "{{.Replicas}}" | awk -F'/' 'BEGIN{total=0; healthy=0} {total+=$2; healthy+=$1} END{if(total>0) print int((healthy/total)*100); else print 0}')
    passed_checks=$((passed_checks + healthy_ratio * 30 / 100))
    
    # API connectivity (weight: 20)
    total_checks=$((total_checks + 20))
    if curl -f -s -m 5 "http://localhost:8000/health" >/dev/null 2>&1; then
        passed_checks=$((passed_checks + 20))
    fi
    
    # Database (weight: 15)
    total_checks=$((total_checks + 15))
    local postgres_container=$(docker ps --filter name=${STACK_NAME}_postgres --format "{{.ID}}" | head -1)
    if [ -n "$postgres_container" ] && docker exec "$postgres_container" pg_isready -U postgres >/dev/null 2>&1; then
        passed_checks=$((passed_checks + 15))
    fi
    
    # Calculate final score
    if [ $total_checks -gt 0 ]; then
        health_score=$((passed_checks * 100 / total_checks))
    fi
    
    # Display health score with appropriate color
    if [ $health_score -ge 90 ]; then
        print_success "🏆 System Health Score: $health_score/100 (Excellent)"
    elif [ $health_score -ge 80 ]; then
        print_success "✅ System Health Score: $health_score/100 (Good)"
    elif [ $health_score -ge 70 ]; then
        print_warning "⚡ System Health Score: $health_score/100 (Fair)"
    elif [ $health_score -ge 50 ]; then
        print_error "⚠️ System Health Score: $health_score/100 (Poor)"
    else
        print_critical "💀 System Health Score: $health_score/100 (Critical)"
    fi
    
    return $health_score
}

# Continuous monitoring mode
continuous_monitoring() {
    print_status "Starting continuous monitoring (interval: ${HEALTH_CHECK_INTERVAL}s)"
    print_status "Press Ctrl+C to stop monitoring"
    
    local iteration=0
    
    while true; do
        iteration=$((iteration + 1))
        
        clear
        print_header
        echo -e "${PURPLE}Monitoring Iteration: $iteration${NC}"
        echo -e "${PURPLE}Timestamp: $(date)${NC}"
        
        # Quick health checks for continuous mode
        check_docker_health >/dev/null 2>&1 && echo "${CHECK} Docker" || echo "${ERROR} Docker"
        check_swarm_health >/dev/null 2>&1 && echo "${CHECK} Swarm" || echo "${ERROR} Swarm"
        check_service_health >/dev/null 2>&1 && echo "${CHECK} Services" || echo "${ERROR} Services"
        check_network_health >/dev/null 2>&1 && echo "${CHECK} Network" || echo "${ERROR} Network"
        check_database_health >/dev/null 2>&1 && echo "${CHECK} Database" || echo "${ERROR} Database"
        
        generate_health_score >/dev/null
        
        sleep $HEALTH_CHECK_INTERVAL
    done
}

# Quick health check
quick_check() {
    print_header
    
    # Essential checks only
    local issues=0
    
    # Docker daemon
    if ! docker info >/dev/null 2>&1; then
        print_critical "Docker daemon is down"
        issues=$((issues + 1))
    fi
    
    # Stack services
    local unhealthy_services=$(docker service ls --filter name=$STACK_NAME --format "{{.Replicas}}" | awk -F'/' '$1 != $2 {count++} END {print count+0}')
    if [ $unhealthy_services -gt 0 ]; then
        print_error "$unhealthy_services services are unhealthy"
        issues=$((issues + 1))
    fi
    
    # API connectivity
    if ! curl -f -s -m 5 "http://localhost:8000/health" >/dev/null 2>&1; then
        print_error "API is unreachable"
        issues=$((issues + 1))
    fi
    
    if [ $issues -eq 0 ]; then
        print_success "🎉 All quick checks passed!"
    else
        print_critical "❗ $issues issues found"
    fi
    
    return $issues
}

# Main function
main() {
    case "$1" in
        --continuous)
            continuous_monitoring
            ;;
        --quick)
            quick_check
            ;;
        --json)
            # JSON output for programmatic consumption
            generate_health_score >/dev/null
            echo '{"timestamp":"'$(date -Iseconds)'","health_score":'$?',"status":"ok"}'
            ;;
        --help)
            echo "GuardianShield Health Monitor"
            echo "Usage: $0 [option]"
            echo ""
            echo "Options:"
            echo "  (no option)     Comprehensive health check"
            echo "  --continuous    Continuous monitoring mode"
            echo "  --quick         Quick essential checks only"
            echo "  --json          JSON output format"
            echo "  --help          Show this help message"
            ;;
        *)
            # Full comprehensive health check
            print_header
            echo -e "${PURPLE}Comprehensive Health Check - $(date)${NC}\n"
            
            check_docker_health
            check_swarm_health
            check_service_health
            check_container_health
            check_network_health
            check_storage_health
            check_database_health
            check_monitoring_health
            generate_health_score
            
            echo -e "\n${BLUE}Health check completed at $(date)${NC}"
            ;;
    esac
}

# Trap for graceful exit in continuous mode
trap 'echo -e "\n\n${YELLOW}Monitoring stopped by user${NC}"; exit 0' INT

# Execute main function
main "$@"