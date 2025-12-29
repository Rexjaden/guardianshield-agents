#!/bin/bash
# Comprehensive GuardianShield System Backup
# Backup databases, configurations, logs, and container states

set -e

# Configuration
STACK_NAME="guardianshield"
BACKUP_ROOT="/backup/guardianshield"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_ROOT}/${TIMESTAMP}"
RETENTION_DAYS=30

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

# Create backup directory structure
create_backup_structure() {
    print_status "Creating backup directory structure..."
    
    mkdir -p "$BACKUP_DIR"/{databases,configurations,logs,secrets,images,volumes,monitoring}
    
    print_success "Backup directory created: $BACKUP_DIR"
}

# Backup databases
backup_databases() {
    print_status "Backing up databases..."
    
    # PostgreSQL backup
    if docker service ls --filter name=${STACK_NAME}_postgres-primary -q | grep -q .; then
        print_status "Backing up PostgreSQL database..."
        
        # Get container ID for PostgreSQL
        local postgres_container=$(docker ps --filter name=${STACK_NAME}_postgres-primary --format "{{.ID}}" | head -1)
        
        if [ -n "$postgres_container" ]; then
            docker exec "$postgres_container" pg_dump -U postgres guardianshield > "$BACKUP_DIR/databases/postgresql_guardianshield.sql"
            docker exec "$postgres_container" pg_dumpall -U postgres > "$BACKUP_DIR/databases/postgresql_all.sql"
            print_success "PostgreSQL backup completed"
        else
            print_warning "PostgreSQL container not found"
        fi
    fi
    
    # Redis backup
    if docker service ls --filter name=${STACK_NAME}_redis-cluster -q | grep -q .; then
        print_status "Backing up Redis data..."
        
        local redis_container=$(docker ps --filter name=${STACK_NAME}_redis-cluster --format "{{.ID}}" | head -1)
        
        if [ -n "$redis_container" ]; then
            docker exec "$redis_container" redis-cli BGSAVE
            sleep 5  # Wait for background save to complete
            docker cp "$redis_container":/data/dump.rdb "$BACKUP_DIR/databases/redis_dump.rdb"
            print_success "Redis backup completed"
        else
            print_warning "Redis container not found"
        fi
    fi
    
    # SQLite databases (if any)
    if [ -d "./databases" ]; then
        print_status "Backing up SQLite databases..."
        cp -r ./databases "$BACKUP_DIR/databases/sqlite/"
        print_success "SQLite databases backed up"
    fi
}

# Backup configurations
backup_configurations() {
    print_status "Backing up configurations..."
    
    # Docker Compose files
    cp docker-compose*.yml "$BACKUP_DIR/configurations/" 2>/dev/null || true
    cp docker-swarm-stack.yml "$BACKUP_DIR/configurations/" 2>/dev/null || true
    
    # Dockerfiles
    cp Dockerfile* "$BACKUP_DIR/configurations/" 2>/dev/null || true
    
    # Environment files
    cp .env* "$BACKUP_DIR/configurations/" 2>/dev/null || true
    
    # Configuration directories
    [ -d "monitoring" ] && cp -r monitoring "$BACKUP_DIR/configurations/"
    [ -d "scaling" ] && cp -r scaling "$BACKUP_DIR/configurations/"
    [ -d "security" ] && cp -r security "$BACKUP_DIR/configurations/"
    
    # Application configurations
    cp *.py "$BACKUP_DIR/configurations/python_files/" 2>/dev/null || true
    cp *.json "$BACKUP_DIR/configurations/json_configs/" 2>/dev/null || true
    
    print_success "Configurations backed up"
}

# Backup logs and data
backup_logs() {
    print_status "Backing up logs and runtime data..."
    
    # Agent logs
    cp agent_*.jsonl "$BACKUP_DIR/logs/" 2>/dev/null || true
    
    # Docker service logs
    local services=$(docker service ls --filter name=${STACK_NAME} --format "{{.Name}}")
    
    for service in $services; do
        print_status "Backing up logs for $service..."
        docker service logs "$service" > "$BACKUP_DIR/logs/${service}_service.log" 2>&1 || true
    done
    
    # System logs from containers
    [ -d "/var/log/guardianshield" ] && cp -r /var/log/guardianshield "$BACKUP_DIR/logs/system/"
    
    print_success "Logs backed up"
}

# Backup Docker secrets and configs
backup_secrets_configs() {
    print_status "Backing up Docker secrets and configs..."
    
    # List secrets and configs (values are encrypted, so we just save metadata)
    docker secret ls --format "{{.ID}} {{.Name}} {{.CreatedAt}}" > "$BACKUP_DIR/secrets/secrets_list.txt" 2>/dev/null || true
    docker config ls --format "{{.ID}} {{.Name}} {{.CreatedAt}}" > "$BACKUP_DIR/secrets/configs_list.txt" 2>/dev/null || true
    
    # Backup config files if they exist locally
    [ -f "haproxy.cfg" ] && cp haproxy.cfg "$BACKUP_DIR/secrets/"
    
    print_success "Secrets and configs metadata backed up"
}

# Backup container images
backup_images() {
    print_status "Backing up container images..."
    
    # Save custom images
    local images=("guardianshield/api:latest" "guardianshield/agent:latest")
    
    for image in "${images[@]}"; do
        if docker images -q "$image" | grep -q .; then
            print_status "Saving image: $image"
            local image_file=$(echo "$image" | sed 's/[:\/]/_/g')
            docker save "$image" | gzip > "$BACKUP_DIR/images/${image_file}.tar.gz"
            print_success "Saved: $image"
        else
            print_warning "Image not found: $image"
        fi
    done
}

# Backup Docker volumes
backup_volumes() {
    print_status "Backing up Docker volumes..."
    
    # Get volumes used by the stack
    local volumes=$(docker volume ls --filter name=${STACK_NAME} --format "{{.Name}}")
    
    for volume in $volumes; do
        print_status "Backing up volume: $volume"
        
        # Create a temporary container to access volume data
        docker run --rm -v "$volume":/volume -v "$BACKUP_DIR/volumes":/backup alpine tar czf "/backup/${volume}.tar.gz" -C /volume .
        
        print_success "Volume backed up: $volume"
    done
}

# Backup monitoring data
backup_monitoring() {
    print_status "Backing up monitoring data..."
    
    # Prometheus data
    if docker service ls --filter name=${STACK_NAME}_prometheus -q | grep -q .; then
        print_status "Backing up Prometheus data..."
        
        local prometheus_container=$(docker ps --filter name=prometheus --format "{{.ID}}" | head -1)
        
        if [ -n "$prometheus_container" ]; then
            docker cp "$prometheus_container":/prometheus "$BACKUP_DIR/monitoring/prometheus_data"
        fi
    fi
    
    # Grafana dashboards and settings
    if docker service ls --filter name=${STACK_NAME}_grafana -q | grep -q .; then
        print_status "Backing up Grafana data..."
        
        local grafana_container=$(docker ps --filter name=grafana --format "{{.ID}}" | head -1)
        
        if [ -n "$grafana_container" ]; then
            docker cp "$grafana_container":/var/lib/grafana "$BACKUP_DIR/monitoring/grafana_data"
        fi
    fi
    
    print_success "Monitoring data backed up"
}

# Create backup manifest
create_manifest() {
    print_status "Creating backup manifest..."
    
    cat > "$BACKUP_DIR/backup_manifest.json" << EOF
{
  "backup_timestamp": "$TIMESTAMP",
  "backup_date": "$(date -Iseconds)",
  "stack_name": "$STACK_NAME",
  "backup_type": "full",
  "components": {
    "databases": {
      "postgresql": $([ -f "$BACKUP_DIR/databases/postgresql_guardianshield.sql" ] && echo "true" || echo "false"),
      "redis": $([ -f "$BACKUP_DIR/databases/redis_dump.rdb" ] && echo "true" || echo "false"),
      "sqlite": $([ -d "$BACKUP_DIR/databases/sqlite" ] && echo "true" || echo "false")
    },
    "configurations": $([ -d "$BACKUP_DIR/configurations" ] && echo "true" || echo "false"),
    "logs": $([ -d "$BACKUP_DIR/logs" ] && echo "true" || echo "false"),
    "images": $([ -d "$BACKUP_DIR/images" ] && echo "true" || echo "false"),
    "volumes": $([ -d "$BACKUP_DIR/volumes" ] && echo "true" || echo "false"),
    "monitoring": $([ -d "$BACKUP_DIR/monitoring" ] && echo "true" || echo "false")
  },
  "backup_size": "$(du -sh "$BACKUP_DIR" | cut -f1)",
  "docker_version": "$(docker --version)",
  "system_info": "$(uname -a)"
}
EOF
    
    print_success "Backup manifest created"
}

# Cleanup old backups
cleanup_old_backups() {
    if [ -n "$RETENTION_DAYS" ] && [ "$RETENTION_DAYS" -gt 0 ]; then
        print_status "Cleaning up backups older than $RETENTION_DAYS days..."
        
        find "$BACKUP_ROOT" -type d -name "20*" -mtime +"$RETENTION_DAYS" -exec rm -rf {} + 2>/dev/null || true
        
        print_success "Old backups cleaned up"
    fi
}

# Verify backup integrity
verify_backup() {
    print_status "Verifying backup integrity..."
    
    local errors=0
    
    # Check if critical files exist
    [ ! -f "$BACKUP_DIR/backup_manifest.json" ] && print_warning "Manifest file missing" && errors=$((errors + 1))
    [ ! -d "$BACKUP_DIR/configurations" ] && print_warning "Configurations backup missing" && errors=$((errors + 1))
    
    # Check database backups
    if [ -f "$BACKUP_DIR/databases/postgresql_guardianshield.sql" ]; then
        local sql_size=$(stat -f%z "$BACKUP_DIR/databases/postgresql_guardianshield.sql" 2>/dev/null || stat -c%s "$BACKUP_DIR/databases/postgresql_guardianshield.sql" 2>/dev/null)
        [ "$sql_size" -lt 1000 ] && print_warning "PostgreSQL backup seems too small" && errors=$((errors + 1))
    fi
    
    if [ $errors -eq 0 ]; then
        print_success "Backup verification passed"
    else
        print_warning "Backup verification completed with $errors warnings"
    fi
    
    return $errors
}

# Display backup summary
show_summary() {
    print_status "Backup Summary:"
    echo "==============="
    echo "Backup Location: $BACKUP_DIR"
    echo "Backup Size: $(du -sh "$BACKUP_DIR" | cut -f1)"
    echo "Timestamp: $TIMESTAMP"
    echo ""
    echo "Components backed up:"
    [ -d "$BACKUP_DIR/databases" ] && echo "  ✅ Databases"
    [ -d "$BACKUP_DIR/configurations" ] && echo "  ✅ Configurations"
    [ -d "$BACKUP_DIR/logs" ] && echo "  ✅ Logs"
    [ -d "$BACKUP_DIR/images" ] && echo "  ✅ Container Images"
    [ -d "$BACKUP_DIR/volumes" ] && echo "  ✅ Docker Volumes"
    [ -d "$BACKUP_DIR/monitoring" ] && echo "  ✅ Monitoring Data"
    echo ""
    echo "Restore command:"
    echo "  ./restore-system.sh $TIMESTAMP"
}

# Main backup process
main() {
    case "$1" in
        --list)
            print_status "Available backups:"
            ls -la "$BACKUP_ROOT" 2>/dev/null | grep "^d" | awk '{print $9}' | grep "^20" | sort -r
            exit 0
            ;;
        --verify)
            if [ -n "$2" ]; then
                BACKUP_DIR="${BACKUP_ROOT}/$2"
                verify_backup
            else
                print_error "Usage: $0 --verify <timestamp>"
                exit 1
            fi
            exit 0
            ;;
        --cleanup)
            cleanup_old_backups
            exit 0
            ;;
        --help)
            echo "GuardianShield System Backup Tool"
            echo "Usage: $0 [option]"
            echo ""
            echo "Options:"
            echo "  (no option)     Perform full system backup"
            echo "  --list          List available backups"
            echo "  --verify <ts>   Verify backup integrity"
            echo "  --cleanup       Remove old backups"
            echo "  --help          Show this help message"
            exit 0
            ;;
    esac
    
    print_status "🔄 Starting GuardianShield System Backup..."
    print_status "Timestamp: $TIMESTAMP"
    
    create_backup_structure
    backup_databases
    backup_configurations
    backup_logs
    backup_secrets_configs
    backup_images
    backup_volumes
    backup_monitoring
    create_manifest
    verify_backup
    cleanup_old_backups
    show_summary
    
    print_success "🎉 Backup completed successfully!"
}

# Execute main function
main "$@"