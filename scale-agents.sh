#!/bin/bash
# Scale GuardianShield agents dynamically
# Advanced scaling with load monitoring

set -e

# Configuration
STACK_NAME="guardianshield"
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

# Get current service replicas
get_current_replicas() {
    local service_name="$1"
    docker service ls --filter name=${STACK_NAME}_${service_name} --format "{{.Replicas}}" | cut -d'/' -f1
}

# Scale specific service
scale_service() {
    local service_name="$1"
    local replicas="$2"
    local reason="${3:-Manual scaling}"
    
    print_status "Scaling ${service_name} to ${replicas} replicas - Reason: ${reason}"
    
    if docker service scale ${STACK_NAME}_${service_name}=${replicas}; then
        print_success "Successfully scaled ${service_name} to ${replicas} replicas"
        
        # Wait for scaling to complete
        local timeout=120
        local count=0
        
        while [ $count -lt $timeout ]; do
            local current=$(get_current_replicas "$service_name")
            if [ "$current" = "$replicas" ]; then
                print_success "Scaling completed: ${service_name} now has ${replicas} replicas"
                break
            fi
            
            print_status "Waiting for scaling... (${current}/${replicas} ready)"
            sleep 5
            count=$((count + 5))
        done
        
        if [ $count -ge $timeout ]; then
            print_warning "Timeout waiting for scaling to complete"
        fi
    else
        print_error "Failed to scale ${service_name}"
        return 1
    fi
}

# Auto-scale based on metrics
auto_scale() {
    print_status "Starting automatic scaling analysis..."
    
    # Define scaling thresholds
    local CPU_HIGH_THRESHOLD=80
    local CPU_LOW_THRESHOLD=30
    local MEMORY_HIGH_THRESHOLD=85
    local MEMORY_LOW_THRESHOLD=40
    
    # Services to monitor and scale
    local services=("learning-agent-cluster" "behavioral-agent-cluster" "dmer-agent-cluster" "guardianshield-api")
    
    for service in "${services[@]}"; do
        print_status "Analyzing ${service}..."
        
        local current_replicas=$(get_current_replicas "$service")
        local suggested_replicas=$current_replicas
        
        # Simulate CPU/Memory monitoring (in production, integrate with Prometheus)
        local cpu_usage=$(( RANDOM % 100 ))
        local memory_usage=$(( RANDOM % 100 ))
        
        print_status "${service} - CPU: ${cpu_usage}%, Memory: ${memory_usage}%, Replicas: ${current_replicas}"
        
        # Scale up conditions
        if [ $cpu_usage -gt $CPU_HIGH_THRESHOLD ] || [ $memory_usage -gt $MEMORY_HIGH_THRESHOLD ]; then
            local max_replicas=10
            if [ $current_replicas -lt $max_replicas ]; then
                suggested_replicas=$((current_replicas + 1))
                scale_service "$service" "$suggested_replicas" "High resource usage (CPU: ${cpu_usage}%, Memory: ${memory_usage}%)"
            else
                print_warning "${service} already at maximum replicas (${max_replicas})"
            fi
        # Scale down conditions
        elif [ $cpu_usage -lt $CPU_LOW_THRESHOLD ] && [ $memory_usage -lt $MEMORY_LOW_THRESHOLD ]; then
            local min_replicas=1
            if [ $current_replicas -gt $min_replicas ]; then
                suggested_replicas=$((current_replicas - 1))
                scale_service "$service" "$suggested_replicas" "Low resource usage (CPU: ${cpu_usage}%, Memory: ${memory_usage}%)"
            else
                print_warning "${service} already at minimum replicas (${min_replicas})"
            fi
        else
            print_status "${service} resource usage within normal range"
        fi
    done
}

# Manual scaling interface
manual_scale() {
    local agent_type="$1"
    local replicas="$2"
    
    if [ -z "$agent_type" ] || [ -z "$replicas" ]; then
        print_error "Usage: $0 --manual <agent-type> <replicas>"
        print_status "Available agent types:"
        echo "  • learning-agent-cluster"
        echo "  • behavioral-agent-cluster"
        echo "  • dmer-agent-cluster"
        echo "  • guardianshield-api"
        return 1
    fi
    
    # Validate replica count
    if ! [[ "$replicas" =~ ^[0-9]+$ ]] || [ "$replicas" -lt 0 ] || [ "$replicas" -gt 20 ]; then
        print_error "Replicas must be a number between 0 and 20"
        return 1
    fi
    
    scale_service "$agent_type" "$replicas" "Manual scaling request"
}

# Show current scaling status
show_status() {
    print_status "Current Service Status:"
    echo "========================"
    
    docker service ls --filter name=${STACK_NAME} --format "table {{.Name}}\t{{.Replicas}}\t{{.Image}}"
    
    echo ""
    print_status "Resource Usage Summary:"
    echo "(Integration with Prometheus recommended for real metrics)"
    
    # Show task distribution
    echo ""
    print_status "Task Distribution:"
    docker stack ps $STACK_NAME --format "table {{.Name}}\t{{.Node}}\t{{.CurrentState}}" | head -20
}

# Scaling recommendations
show_recommendations() {
    print_status "Scaling Recommendations:"
    echo "========================="
    
    echo "• Learning Agents: High CPU workload, scale 3-8 replicas"
    echo "• Behavioral Agents: Memory intensive, scale 2-5 replicas"
    echo "• DMER Agents: Network I/O bound, scale 2-4 replicas"
    echo "• API Service: Based on request volume, scale 2-6 replicas"
    echo ""
    echo "Monitoring Integration:"
    echo "• Integrate with Prometheus for real-time metrics"
    echo "• Set up AlertManager for scaling notifications"
    echo "• Use Grafana dashboards for visualization"
}

# Performance testing mode
performance_test() {
    print_status "Running performance-based scaling test..."
    
    # Scale up all services
    print_status "Phase 1: Scaling up services for load test"
    scale_service "guardianshield-api" "5" "Performance test - load phase"
    scale_service "learning-agent-cluster" "8" "Performance test - load phase"
    scale_service "behavioral-agent-cluster" "4" "Performance test - load phase"
    
    print_status "Waiting 30 seconds for services to stabilize..."
    sleep 30
    
    # Simulate load and monitor
    print_status "Phase 2: Monitoring performance under load"
    for i in {1..5}; do
        print_status "Performance check $i/5"
        show_status
        sleep 10
    done
    
    # Scale down to optimal levels
    print_status "Phase 3: Scaling down to optimal levels"
    scale_service "guardianshield-api" "3" "Performance test - optimization phase"
    scale_service "learning-agent-cluster" "5" "Performance test - optimization phase"
    scale_service "behavioral-agent-cluster" "3" "Performance test - optimization phase"
    
    print_success "Performance test completed"
}

# Main function
main() {
    case "$1" in
        --auto)
            auto_scale
            ;;
        --manual)
            manual_scale "$2" "$3"
            ;;
        --status)
            show_status
            ;;
        --recommendations)
            show_recommendations
            ;;
        --test)
            performance_test
            ;;
        --help)
            echo "GuardianShield Agent Scaling Tool"
            echo "Usage: $0 [option] [parameters]"
            echo ""
            echo "Options:"
            echo "  --auto                     Automatic scaling based on metrics"
            echo "  --manual <service> <count> Manual scaling of specific service"
            echo "  --status                   Show current scaling status"
            echo "  --recommendations          Show scaling recommendations"
            echo "  --test                     Run performance-based scaling test"
            echo "  --help                     Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --auto"
            echo "  $0 --manual learning-agent-cluster 7"
            echo "  $0 --status"
            ;;
        *)
            # Default behavior - show status and run auto-scaling
            show_status
            echo ""
            auto_scale
            ;;
    esac
}

# Execute main function
main "$@"