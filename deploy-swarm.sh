#!/bin/bash
# Deploy GuardianShield to Docker Swarm
# Advanced multi-node container orchestration

set -e

echo "🐳 GuardianShield Docker Swarm Deployment"
echo "=========================================="

# Configuration
SWARM_ADVERTISE_ADDR=$(hostname -I | awk '{print $1}')
STACK_NAME="guardianshield"
COMPOSE_FILE="docker-swarm-stack.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Docker availability
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        exit 1
    fi
    
    print_success "Docker is available and running"
}

# Initialize Docker Swarm
init_swarm() {
    print_status "Initializing Docker Swarm..."
    
    if docker info --format '{{.Swarm.LocalNodeState}}' | grep -q "active"; then
        print_success "Docker Swarm is already initialized"
    else
        print_status "Initializing new Swarm cluster..."
        docker swarm init --advertise-addr $SWARM_ADVERTISE_ADDR
        print_success "Docker Swarm initialized successfully"
    fi
    
    # Display join tokens
    print_status "Manager join token:"
    docker swarm join-token manager -q
    
    print_status "Worker join token:"
    docker swarm join-token worker -q
}

# Create secrets
create_secrets() {
    print_status "Creating secrets..."
    
    # PostgreSQL password
    if ! docker secret ls | grep -q postgres_password; then
        echo "$(openssl rand -base64 32)" | docker secret create postgres_password -
        print_success "Created postgres_password secret"
    else
        print_warning "postgres_password secret already exists"
    fi
    
    # API secret key
    if ! docker secret ls | grep -q api_secret_key; then
        echo "$(openssl rand -hex 64)" | docker secret create api_secret_key -
        print_success "Created api_secret_key secret"
    else
        print_warning "api_secret_key secret already exists"
    fi
}

# Create configs
create_configs() {
    print_status "Creating configurations..."
    
    # HAProxy configuration
    if ! docker config ls | grep -q haproxy_config; then
        cat > haproxy.cfg << EOF
global
    daemon
    log stdout local0
    
defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms
    
frontend guardianshield_frontend
    bind *:80
    bind *:443 ssl crt /etc/ssl/certs/guardianshield.pem
    redirect scheme https if !{ ssl_fc }
    default_backend guardianshield_backend
    
backend guardianshield_backend
    balance roundrobin
    server api1 guardianshield-api:8000 check
    server api2 guardianshield-api:8000 check
    server api3 guardianshield-api:8000 check
EOF
        docker config create haproxy_config haproxy.cfg
        rm haproxy.cfg
        print_success "Created haproxy_config"
    else
        print_warning "haproxy_config already exists"
    fi
}

# Create networks
create_networks() {
    print_status "Creating overlay networks..."
    
    if ! docker network ls | grep -q guardianshield-overlay; then
        docker network create --driver overlay --encrypted --attachable guardianshield-overlay
        print_success "Created guardianshield-overlay network"
    else
        print_warning "guardianshield-overlay network already exists"
    fi
}

# Add node labels
add_node_labels() {
    print_status "Adding node labels..."
    
    NODE_ID=$(docker node ls --filter role=manager -q | head -n1)
    
    # Label nodes for different agent types
    docker node update --label-add agent_type=learning $NODE_ID
    docker node update --label-add agent_type=behavioral $NODE_ID  
    docker node update --label-add agent_type=dmer $NODE_ID
    docker node update --label-add database=primary $NODE_ID
    
    print_success "Node labels added successfully"
}

# Deploy stack
deploy_stack() {
    print_status "Deploying GuardianShield stack..."
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "Compose file $COMPOSE_FILE not found"
        exit 1
    fi
    
    docker stack deploy -c $COMPOSE_FILE $STACK_NAME
    print_success "Stack deployed successfully"
}

# Wait for services
wait_for_services() {
    print_status "Waiting for services to become ready..."
    
    local timeout=300
    local count=0
    
    while [ $count -lt $timeout ]; do
        local running_services=$(docker service ls --filter name=${STACK_NAME} --format "table {{.Name}}\t{{.Replicas}}" | grep -v "0/")
        local total_services=$(docker stack services $STACK_NAME --format "{{.Name}}" | wc -l)
        local ready_services=$(echo "$running_services" | grep -c "/" 2>/dev/null || echo "0")
        
        if [ $ready_services -eq $total_services ]; then
            print_success "All services are running"
            break
        fi
        
        print_status "Waiting for services... ($ready_services/$total_services ready)"
        sleep 5
        count=$((count + 5))
    done
    
    if [ $count -ge $timeout ]; then
        print_warning "Timeout waiting for all services to be ready"
    fi
}

# Display cluster status
show_status() {
    print_status "Cluster Status:"
    echo "==============="
    
    echo -e "\n${BLUE}Swarm Nodes:${NC}"
    docker node ls
    
    echo -e "\n${BLUE}Stack Services:${NC}"
    docker stack services $STACK_NAME
    
    echo -e "\n${BLUE}Service Tasks:${NC}"
    docker stack ps $STACK_NAME --no-trunc
    
    echo -e "\n${BLUE}Network Information:${NC}"
    docker network ls | grep guardianshield
    
    echo -e "\n${BLUE}Secrets:${NC}"
    docker secret ls
    
    echo -e "\n${BLUE}Configs:${NC}"
    docker config ls
}

# Health check
health_check() {
    print_status "Performing health check..."
    
    # Check API health
    for i in {1..5}; do
        if curl -f http://localhost:8000/health &>/dev/null; then
            print_success "API health check passed"
            break
        else
            print_warning "API health check attempt $i failed, retrying..."
            sleep 10
        fi
    done
}

# Cleanup function
cleanup() {
    if [ "$1" = "--remove" ]; then
        print_warning "Removing GuardianShield stack..."
        docker stack rm $STACK_NAME
        sleep 10
        
        print_warning "Removing networks..."
        docker network rm guardianshield-overlay 2>/dev/null || true
        
        print_success "Cleanup completed"
    fi
}

# Main deployment process
main() {
    case "$1" in
        --remove|--cleanup)
            cleanup --remove
            exit 0
            ;;
        --status)
            show_status
            exit 0
            ;;
        --health)
            health_check
            exit 0
            ;;
    esac
    
    print_status "Starting GuardianShield Swarm deployment..."
    
    check_docker
    init_swarm
    create_secrets
    create_configs
    create_networks
    add_node_labels
    deploy_stack
    wait_for_services
    show_status
    health_check
    
    print_success "🎉 GuardianShield deployed successfully!"
    echo ""
    print_status "Access points:"
    echo "  • API: http://localhost:8000"
    echo "  • Load Balancer: http://localhost:80"
    echo "  • HAProxy Stats: http://localhost:8404/stats"
    echo ""
    print_status "Management commands:"
    echo "  • Scale service: docker service scale ${STACK_NAME}_guardianshield-api=5"
    echo "  • View logs: docker service logs ${STACK_NAME}_guardianshield-api"
    echo "  • Update service: docker service update ${STACK_NAME}_guardianshield-api"
    echo "  • Remove stack: $0 --remove"
}

# Handle script arguments
if [ "$#" -eq 0 ]; then
    main
else
    main "$@"
fi