#!/bin/bash

# GuardianShield Infrastructure Stop Script
# Gracefully stop all running blockchain infrastructure

set -euo pipefail

PROJECT_NAME="guardianshield-sentry-shield"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

stop_stack() {
    local stack_name="$1"
    local compose_file="$2"
    
    if [ -f "$compose_file" ]; then
        log_info "Stopping $stack_name stack..."
        docker-compose -f "$compose_file" -p "${PROJECT_NAME}-${stack_name}" down --remove-orphans
        log_success "$stack_name stack stopped"
    else
        log_warning "Compose file not found: $compose_file"
    fi
}

main() {
    log_info "Stopping GuardianShield infrastructure..."
    
    # Stop in reverse dependency order
    stop_stack "sentry-shield" "docker-compose.sentry-shield.yml"
    stop_stack "bootnodes" "docker-compose.bootnodes.yml" 
    stop_stack "validators" "docker-compose.validators.yml"
    
    # Clean up networks
    log_info "Cleaning up Docker networks..."
    docker network prune -f || log_warning "Network cleanup failed"
    
    # Optional: Clean up volumes (uncomment if needed)
    # log_info "Cleaning up Docker volumes..."
    # docker volume prune -f
    
    log_success "🛑 All GuardianShield infrastructure stopped"
}

case "${1:-stop}" in
    "stop")
        main
        ;;
    "clean")
        main
        log_warning "Removing all associated Docker images and volumes..."
        docker system prune -af --volumes
        log_success "Complete cleanup finished"
        ;;
    "help")
        echo "Usage: $0 [stop|clean|help]"
        echo "  stop   - Stop all services (default)"
        echo "  clean  - Stop services and remove all Docker artifacts"
        echo "  help   - Show this help"
        ;;
    *)
        log_error "Unknown command: $1"
        exit 1
        ;;
esac