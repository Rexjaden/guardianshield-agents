#!/bin/bash

# GuardianShield Sentry Shield Deployment Script
# Deploy multi-region sentry node infrastructure with attack protection

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="guardianshield-sentry-shield"
DOCKER_COMPOSE_FILES=(
    "docker-compose.sentry-shield.yml"
    "docker-compose.validators.yml"
    "docker-compose.bootnodes.yml"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    log_success "All prerequisites satisfied"
}

# Create necessary directories and permissions
setup_directories() {
    log_info "Setting up directories and permissions..."
    
    local dirs=(
        "./validator-keys"
        "./validator-config"
        "./bootnode-config"
        "./sentry-config"
        "./nginx-config"
        "./prometheus-config"
        "./logs/nginx"
        "./logs/prometheus"
        "./logs/sentry"
        "./data/redis"
        "./data/prometheus"
        "./ssl-certificates"
    )
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_info "Created directory: $dir"
        fi
    done
    
    # Set appropriate permissions
    chmod 700 ./validator-keys
    chmod 755 ./nginx-config
    chmod 755 ./prometheus-config
    chmod 755 ./logs
    
    log_success "Directory setup complete"
}

# Generate SSL certificates for testing (self-signed)
generate_ssl_certificates() {
    log_info "Generating SSL certificates..."
    
    if [ ! -f "./ssl-certificates/guardian.crt" ]; then
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ./ssl-certificates/guardian.key \
            -out ./ssl-certificates/guardian.crt \
            -subj "/C=US/ST=Global/L=Blockchain/O=GuardianShield/CN=guardian-sentry.internal" \
            2>/dev/null || {
            log_warning "OpenSSL not available, using dummy certificates"
            echo "dummy-cert" > ./ssl-certificates/guardian.crt
            echo "dummy-key" > ./ssl-certificates/guardian.key
        }
        
        chmod 600 ./ssl-certificates/guardian.key
        chmod 644 ./ssl-certificates/guardian.crt
        
        log_success "SSL certificates generated"
    else
        log_info "SSL certificates already exist"
    fi
}

# Deploy specific service stack
deploy_stack() {
    local stack_name="$1"
    local compose_file="$2"
    
    log_info "Deploying $stack_name stack..."
    
    if [ ! -f "$compose_file" ]; then
        log_error "Docker Compose file not found: $compose_file"
        return 1
    fi
    
    # Pull images first
    log_info "Pulling Docker images for $stack_name..."
    docker-compose -f "$compose_file" -p "${PROJECT_NAME}-${stack_name}" pull || {
        log_warning "Some images may need to be built locally"
    }
    
    # Build any local images
    log_info "Building local images for $stack_name..."
    docker-compose -f "$compose_file" -p "${PROJECT_NAME}-${stack_name}" build
    
    # Deploy with rolling update
    log_info "Starting $stack_name services..."
    docker-compose -f "$compose_file" -p "${PROJECT_NAME}-${stack_name}" up -d
    
    # Wait for health checks
    log_info "Waiting for $stack_name services to become healthy..."
    sleep 10
    
    # Check service status
    local failed_services=()
    while IFS= read -r line; do
        local service=$(echo "$line" | awk '{print $1}')
        local status=$(echo "$line" | awk '{print $2}')
        
        if [[ "$status" != "running" ]]; then
            failed_services+=("$service")
        fi
    done < <(docker-compose -f "$compose_file" -p "${PROJECT_NAME}-${stack_name}" ps --format "table {{.Service}}\t{{.State}}" | tail -n +2)
    
    if [ ${#failed_services[@]} -eq 0 ]; then
        log_success "$stack_name stack deployed successfully"
    else
        log_error "Failed services in $stack_name: ${failed_services[*]}"
        return 1
    fi
}

# Main deployment orchestration
deploy_infrastructure() {
    log_info "Starting GuardianShield Sentry Shield deployment..."
    
    # Deploy in dependency order
    log_info "Phase 1: Deploying validator nodes (secure core infrastructure)..."
    if deploy_stack "validators" "docker-compose.validators.yml"; then
        log_success "Validator nodes deployed"
    else
        log_error "Validator deployment failed"
        exit 1
    fi
    
    # Wait for validators to stabilize
    log_info "Allowing validators to initialize..."
    sleep 30
    
    log_info "Phase 2: Deploying bootnode discovery layer..."
    if deploy_stack "bootnodes" "docker-compose.bootnodes.yml"; then
        log_success "Bootnode discovery layer deployed"
    else
        log_error "Bootnode deployment failed"
        exit 1
    fi
    
    # Wait for bootnodes
    log_info "Allowing bootnodes to establish network..."
    sleep 20
    
    log_info "Phase 3: Deploying sentry shield protection layer..."
    if deploy_stack "sentry-shield" "docker-compose.sentry-shield.yml"; then
        log_success "Sentry shield protection deployed"
    else
        log_error "Sentry shield deployment failed"
        exit 1
    fi
    
    log_success "All infrastructure stacks deployed successfully!"
}

# Health check and status report
health_check() {
    log_info "Performing comprehensive health check..."
    
    local healthy=true
    
    # Check each stack
    for stack in "validators" "bootnodes" "sentry-shield"; do
        log_info "Checking $stack stack health..."
        
        local compose_file="docker-compose.${stack}.yml"
        if [ "$stack" = "sentry-shield" ]; then
            compose_file="docker-compose.sentry-shield.yml"
        fi
        
        local unhealthy_services=()
        while IFS= read -r line; do
            local service=$(echo "$line" | awk '{print $1}')
            local status=$(echo "$line" | awk '{print $2}')
            
            if [[ "$status" != "running" ]]; then
                unhealthy_services+=("$service")
                healthy=false
            fi
        done < <(docker-compose -f "$compose_file" -p "${PROJECT_NAME}-${stack}" ps --format "table {{.Service}}\t{{.State}}" | tail -n +2)
        
        if [ ${#unhealthy_services[@]} -eq 0 ]; then
            log_success "$stack: All services healthy"
        else
            log_error "$stack: Unhealthy services: ${unhealthy_services[*]}"
        fi
    done
    
    # Test key endpoints
    log_info "Testing key service endpoints..."
    
    # Test load balancer (if accessible)
    if curl -s -f http://localhost:80/health > /dev/null; then
        log_success "Load balancer health endpoint responding"
    else
        log_warning "Load balancer health endpoint not accessible (may be expected if not port-forwarded)"
    fi
    
    # Test Prometheus metrics (if accessible)
    if curl -s -f http://localhost:9090/-/ready > /dev/null; then
        log_success "Prometheus metrics system online"
    else
        log_warning "Prometheus metrics not accessible (may be expected if not port-forwarded)"
    fi
    
    if [ "$healthy" = true ]; then
        log_success "Overall health check PASSED"
        return 0
    else
        log_error "Overall health check FAILED"
        return 1
    fi
}

# Show deployment status and next steps
show_status() {
    echo ""
    log_info "=== DEPLOYMENT STATUS ==="
    
    echo ""
    echo "🛡️  GuardianShield Multi-Region Sentry Shield Infrastructure"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📍 DEPLOYED REGIONS:"
    echo "   • US-East (Virginia)     - 2 sentry nodes + 1 validator"
    echo "   • EU-West (Ireland)      - 2 sentry nodes + 1 validator"
    echo "   • Asia-Pacific (Singapore) - 2 sentry nodes + 1 validator"
    echo ""
    echo "🔧 INFRASTRUCTURE COMPONENTS:"
    echo "   • 6 Sentry Shield Nodes  - Attack protection & API serving"
    echo "   • 3 Validator Nodes      - Blockchain consensus (private)"
    echo "   • 3 Bootnode Nodes       - Peer discovery (P2P only)"
    echo "   • 1 Nginx Load Balancer  - Geographic routing"
    echo "   • 1 Redis Rate Limiter   - Advanced rate limiting"
    echo "   • 1 Prometheus Monitor   - Comprehensive metrics"
    echo ""
    echo "🚀 KEY FEATURES ACTIVE:"
    echo "   • Geographic load balancing with automatic failover"
    echo "   • Advanced DDoS protection and attack absorption"
    echo "   • Multi-tier rate limiting (IP, region, global)"
    echo "   • Real-time threat detection and IP banning"
    echo "   • HSM-like validator key management"
    echo "   • Comprehensive monitoring and alerting"
    echo ""
    echo "🔍 MONITORING ENDPOINTS:"
    echo "   • Health Check:     http://localhost:80/health"
    echo "   • Nginx Status:     http://localhost:8081/nginx_status"
    echo "   • Prometheus:       http://localhost:9090"
    echo "   • Grafana (if deployed): http://localhost:3000"
    echo ""
    echo "⚡ NEXT STEPS:"
    echo "   1. Configure DNS to point to your load balancer"
    echo "   2. Update SSL certificates with real certificates"
    echo "   3. Set up external monitoring and log aggregation"
    echo "   4. Configure backup and disaster recovery"
    echo "   5. Tune rate limiting based on traffic patterns"
    echo ""
    echo "📚 MANAGEMENT COMMANDS:"
    echo "   • View logs:        docker-compose -p ${PROJECT_NAME}-<stack> logs -f"
    echo "   • Scale sentry:     docker-compose -p ${PROJECT_NAME}-sentry-shield up -d --scale sentry-us-east-01=2"
    echo "   • Update config:    Edit configs and run: docker-compose -p ${PROJECT_NAME}-<stack> up -d"
    echo "   • Stop all:         ./deployment-scripts/stop-all.sh"
    echo ""
}

# Main execution
main() {
    log_info "GuardianShield Sentry Shield Deployment v1.0"
    log_info "Multi-region blockchain infrastructure with attack protection"
    echo ""
    
    # Run deployment phases
    check_prerequisites
    setup_directories
    generate_ssl_certificates
    deploy_infrastructure
    
    # Final health check
    if health_check; then
        show_status
        log_success "🎉 GuardianShield Sentry Shield deployment completed successfully!"
        echo ""
        log_info "Your blockchain infrastructure is now protected by a multi-region sentry shield."
        log_info "All services are running with advanced attack protection and monitoring."
    else
        log_error "❌ Deployment completed but some services are unhealthy."
        log_info "Check logs with: docker-compose logs"
        exit 1
    fi
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "health")
        health_check
        ;;
    "status")
        show_status
        ;;
    "help")
        echo "Usage: $0 [deploy|health|status|help]"
        echo "  deploy  - Full deployment (default)"
        echo "  health  - Health check only"
        echo "  status  - Show deployment status"
        echo "  help    - Show this help"
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac