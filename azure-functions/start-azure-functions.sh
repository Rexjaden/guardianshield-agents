#!/bin/bash
# GuardianShield Azure Functions Startup Script
# Integrates with existing Docker infrastructure

set -e

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

print_status "🚀 Starting GuardianShield Azure Functions Integration"
echo "============================================================"

# Check if existing GuardianShield infrastructure is running
check_infrastructure() {
    print_status "Checking existing GuardianShield infrastructure..."
    
    # Check for existing networks
    if ! docker network ls | grep -q guardianshield-network; then
        print_error "GuardianShield network not found. Please start main infrastructure first."
        exit 1
    fi
    
    if ! docker network ls | grep -q cilium-mesh; then
        print_warning "Cilium mesh network not found. Creating..."
        docker network create cilium-mesh --driver bridge
    fi
    
    # Check for existing services
    local required_services=("guardianshield-postgres" "guardianshield-redis")
    local missing_services=()
    
    for service in "${required_services[@]}"; do
        if ! docker ps --format "table {{.Names}}" | grep -q "$service"; then
            missing_services+=("$service")
        fi
    done
    
    if [ ${#missing_services[@]} -gt 0 ]; then
        print_warning "Missing required services: ${missing_services[*]}"
        print_status "Starting required infrastructure..."
        
        # Start basic infrastructure if not running
        if [ -f "../docker-compose.production.yml" ]; then
            docker-compose -f ../docker-compose.production.yml up -d db redis
        elif [ -f "../docker-compose.yml" ]; then
            docker-compose -f ../docker-compose.yml up -d db redis  
        else
            print_error "No Docker Compose file found for infrastructure"
            exit 1
        fi
        
        print_status "Waiting for services to be ready..."
        sleep 10
    fi
    
    print_success "Infrastructure check completed"
}

# Verify database schemas
setup_databases() {
    print_status "Setting up Azure Functions databases..."
    
    # Wait for PostgreSQL to be ready
    local postgres_ready=false
    local attempts=0
    local max_attempts=30
    
    while [ $postgres_ready = false ] && [ $attempts -lt $max_attempts ]; do
        if docker exec guardianshield-postgres pg_isready -U postgres >/dev/null 2>&1; then
            postgres_ready=true
        else
            print_status "Waiting for PostgreSQL to be ready... ($((attempts+1))/$max_attempts)"
            sleep 2
            attempts=$((attempts+1))
        fi
    done
    
    if [ $postgres_ready = false ]; then
        print_error "PostgreSQL is not ready after $max_attempts attempts"
        exit 1
    fi
    
    # Create required databases and tables
    print_status "Creating Azure Functions database schemas..."
    
    docker exec guardianshield-postgres psql -U postgres -c "
    -- Create databases if they don't exist
    CREATE DATABASE IF NOT EXISTS erc8055_tokens;
    CREATE DATABASE IF NOT EXISTS blockchain_data;
    CREATE DATABASE IF NOT EXISTS analytics;
    "
    
    # Create ERC-8055 tables
    docker exec guardianshield-postgres psql -U postgres -d erc8055_tokens -c "
    CREATE TABLE IF NOT EXISTS shield_token_fraud (
        id SERIAL PRIMARY KEY,
        token_id INTEGER UNIQUE NOT NULL,
        fraud_score INTEGER DEFAULT 0,
        flags JSONB,
        last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    CREATE TABLE IF NOT EXISTS shield_token_burn_requests (
        id SERIAL PRIMARY KEY,
        token_id INTEGER NOT NULL,
        serial_number VARCHAR(255) NOT NULL,
        requester_address VARCHAR(42) NOT NULL,
        status VARCHAR(50) DEFAULT 'pending',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        processed_at TIMESTAMP WITH TIME ZONE
    );
    
    CREATE TABLE IF NOT EXISTS shield_token_remint_requests (
        id SERIAL PRIMARY KEY,
        original_token_id INTEGER NOT NULL,
        to_address VARCHAR(42) NOT NULL,
        new_serial_number VARCHAR(255) NOT NULL,
        status VARCHAR(50) DEFAULT 'pending',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        processed_at TIMESTAMP WITH TIME ZONE
    );
    
    CREATE INDEX IF NOT EXISTS idx_burn_requests_token_id ON shield_token_burn_requests(token_id);
    CREATE INDEX IF NOT EXISTS idx_remint_requests_original_token ON shield_token_remint_requests(original_token_id);
    "
    
    # Create blockchain indexing tables
    docker exec guardianshield-postgres psql -U postgres -d blockchain_data -c "
    CREATE TABLE IF NOT EXISTS indexed_blocks (
        id SERIAL PRIMARY KEY,
        block_number BIGINT UNIQUE NOT NULL,
        block_hash VARCHAR(66) NOT NULL,
        parent_hash VARCHAR(66) NOT NULL,
        timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
        gas_used BIGINT,
        gas_limit BIGINT,
        transaction_count INTEGER DEFAULT 0,
        miner VARCHAR(42),
        size INTEGER,
        status VARCHAR(50) DEFAULT 'pending',
        indexed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    CREATE TABLE IF NOT EXISTS indexed_transactions (
        id SERIAL PRIMARY KEY,
        tx_hash VARCHAR(66) UNIQUE NOT NULL,
        block_number BIGINT NOT NULL,
        transaction_index INTEGER,
        from_address VARCHAR(42) NOT NULL,
        to_address VARCHAR(42),
        value NUMERIC(78, 0) DEFAULT 0,
        gas BIGINT,
        gas_price BIGINT,
        gas_used BIGINT,
        status VARCHAR(50) DEFAULT 'pending',
        contract_created BOOLEAN DEFAULT FALSE,
        input_data TEXT,
        indexed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    CREATE TABLE IF NOT EXISTS contract_interactions (
        id SERIAL PRIMARY KEY,
        tx_hash VARCHAR(66) NOT NULL,
        block_number BIGINT NOT NULL,
        contract_name VARCHAR(100) NOT NULL,
        contract_address VARCHAR(42) NOT NULL,
        from_address VARCHAR(42) NOT NULL,
        input_data TEXT,
        value NUMERIC(78, 0) DEFAULT 0,
        indexed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        UNIQUE(tx_hash, contract_address)
    );
    
    CREATE INDEX IF NOT EXISTS idx_blocks_number ON indexed_blocks(block_number DESC);
    CREATE INDEX IF NOT EXISTS idx_transactions_block ON indexed_transactions(block_number DESC);
    CREATE INDEX IF NOT EXISTS idx_transactions_from ON indexed_transactions(from_address);
    CREATE INDEX IF NOT EXISTS idx_transactions_to ON indexed_transactions(to_address);
    CREATE INDEX IF NOT EXISTS idx_contract_interactions_contract ON contract_interactions(contract_address);
    "
    
    print_success "Database schemas created successfully"
}

# Build Azure Functions Docker image
build_functions() {
    print_status "Building Azure Functions Docker image..."
    
    # Build the Azure Functions container
    docker build -t guardianshield/azure-functions:latest -f Dockerfile.azure-functions .
    
    if [ $? -eq 0 ]; then
        print_success "Azure Functions image built successfully"
    else
        print_error "Failed to build Azure Functions image"
        exit 1
    fi
}

# Start Azure Functions services
start_services() {
    print_status "Starting Azure Functions services..."
    
    # Use the integrated Docker Compose configuration
    docker-compose -f docker-compose.azure-functions.yml up -d
    
    if [ $? -eq 0 ]; then
        print_success "Azure Functions services started"
    else
        print_error "Failed to start Azure Functions services"
        exit 1
    fi
    
    # Wait for services to be healthy
    print_status "Waiting for services to be ready..."
    
    local services=("guardianshield-azure-functions" "erc8055-processor" "blockchain-indexer")
    local all_healthy=false
    local attempts=0
    local max_attempts=60
    
    while [ $all_healthy = false ] && [ $attempts -lt $max_attempts ]; do
        local healthy_count=0
        
        for service in "${services[@]}"; do
            local health=$(docker inspect --format='{{.State.Health.Status}}' "$service" 2>/dev/null || echo "unknown")
            if [ "$health" = "healthy" ] || [ "$health" = "unknown" ]; then
                healthy_count=$((healthy_count+1))
            fi
        done
        
        if [ $healthy_count -eq ${#services[@]} ]; then
            all_healthy=true
        else
            print_status "Waiting for services to be healthy... ($((attempts+1))/$max_attempts)"
            sleep 5
            attempts=$((attempts+1))
        fi
    done
    
    if [ $all_healthy = true ]; then
        print_success "All services are healthy"
    else
        print_warning "Some services may not be fully ready yet"
    fi
}

# Test Azure Functions endpoints
test_functions() {
    print_status "Testing Azure Functions endpoints..."
    
    # Wait a bit more for functions to fully initialize
    sleep 10
    
    # Test health endpoint
    print_status "Testing health endpoint..."
    local health_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:7071/api/health 2>/dev/null || echo "000")
    
    if [ "$health_response" = "200" ]; then
        print_success "Health endpoint is responding"
    else
        print_warning "Health endpoint returned status: $health_response"
    fi
    
    # Test metrics endpoint
    print_status "Testing metrics endpoint..."
    local metrics_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:7071/api/metrics 2>/dev/null || echo "000")
    
    if [ "$metrics_response" = "200" ]; then
        print_success "Metrics endpoint is responding"
    else
        print_warning "Metrics endpoint returned status: $metrics_response"
    fi
}

# Display service information
show_service_info() {
    print_success "🎉 GuardianShield Azure Functions Integration Complete!"
    echo ""
    echo "📋 Service Information:"
    echo "════════════════════════════════════════════════════════"
    echo "Azure Functions Runtime:    http://localhost:7071"
    echo "Health Check:               http://localhost:7071/api/health"
    echo "Prometheus Metrics:         http://localhost:7071/api/metrics"
    echo ""
    echo "🔧 ERC-8055 Token Processing:"
    echo "Validate Token:             POST http://localhost:7071/api/erc8055/validate/{token_id}"
    echo "Burn Request:               POST http://localhost:7071/api/erc8055/burn"
    echo "Remint Request:             POST http://localhost:7071/api/erc8055/remint"
    echo ""
    echo "⛓️  Blockchain Indexing:"
    echo "Index Block Range:          POST http://localhost:7071/api/blockchain/index/range"
    echo "Indexing Status:            GET  http://localhost:7071/api/blockchain/status"
    echo "Search Transactions:        POST http://localhost:7071/api/blockchain/search/transactions"
    echo ""
    echo "🐳 Docker Services:"
    docker-compose -f docker-compose.azure-functions.yml ps
    echo ""
    echo "📊 Monitoring Integration:"
    echo "Grafana Dashboard:          http://localhost:3000"
    echo "Prometheus:                 http://localhost:9090"
    echo "AlertManager:               http://localhost:9093"
    echo ""
    echo "📝 Logs:"
    echo "View Azure Functions logs:  docker logs guardianshield-azure-functions -f"
    echo "View ERC-8055 logs:         docker logs erc8055-processor -f"
    echo "View Indexer logs:          docker logs blockchain-indexer -f"
    echo ""
    print_success "All services are integrated with existing GuardianShield infrastructure!"
}

# Main execution
main() {
    check_infrastructure
    setup_databases
    build_functions
    start_services
    test_functions
    show_service_info
}

# Run main function
main

print_success "🛡️ GuardianShield Azure Functions are now running and integrated!"
echo "Use 'docker-compose -f docker-compose.azure-functions.yml logs -f' to view all logs"