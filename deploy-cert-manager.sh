#!/bin/bash

# GuardianShield Cert-Manager Deployment Script
# Integrates automated certificate management with existing security containers

set -euo pipefail

# Configuration
NAMESPACE="${GUARDIAN_NAMESPACE:-guardian-shield}"
CHART_PATH="./charts/dhi-cert-manager-chart"
DOMAIN="${GUARDIAN_DOMAIN:-guardian-shield.io}"
EMAIL="${GUARDIAN_EMAIL:-admin@guardian-shield.io}"
DNS_PROVIDER="${DNS_PROVIDER:-cloudflare}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is required but not installed"
        exit 1
    fi
    
    # Check if helm is available
    if ! command -v helm &> /dev/null; then
        error "helm is required but not installed"
        exit 1
    fi
    
    # Check kubernetes connectivity
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Install cert-manager CRDs if not present
install_cert_manager_crds() {
    log "Checking cert-manager CRDs..."
    
    if ! kubectl get crd certificates.cert-manager.io &> /dev/null; then
        log "Installing cert-manager CRDs..."
        kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.4/cert-manager.crds.yaml
        
        # Wait for CRDs to be ready
        log "Waiting for CRDs to be established..."
        kubectl wait --for condition=established --timeout=60s crd/certificates.cert-manager.io
        kubectl wait --for condition=established --timeout=60s crd/certificaterequests.cert-manager.io
        kubectl wait --for condition=established --timeout=60s crd/clusterissuers.cert-manager.io
        kubectl wait --for condition=established --timeout=60s crd/issuers.cert-manager.io
        
        success "Cert-manager CRDs installed"
    else
        success "Cert-manager CRDs already present"
    fi
}

# Create namespace if it doesn't exist
create_namespace() {
    log "Ensuring namespace exists: ${NAMESPACE}"
    
    if ! kubectl get namespace "${NAMESPACE}" &> /dev/null; then
        kubectl create namespace "${NAMESPACE}"
        kubectl label namespace "${NAMESPACE}" name="${NAMESPACE}"
        success "Namespace ${NAMESPACE} created"
    else
        success "Namespace ${NAMESPACE} already exists"
    fi
}

# Install cert-manager core components
install_cert_manager() {
    log "Installing cert-manager..."
    
    # Add cert-manager helm repository
    helm repo add jetstack https://charts.jetstack.io
    helm repo update
    
    # Install or upgrade cert-manager
    helm upgrade --install cert-manager jetstack/cert-manager \
        --namespace cert-manager \
        --create-namespace \
        --version v1.14.4 \
        --set installCRDs=false \
        --set global.leaderElection.namespace=cert-manager \
        --set extraArgs='{--dns01-recursive-nameservers-only,--dns01-recursive-nameservers=8.8.8.8:53\,1.1.1.1:53}' \
        --set securityContext.runAsNonRoot=true \
        --set securityContext.runAsUser=65532 \
        --set securityContext.runAsGroup=65532 \
        --set containerSecurityContext.allowPrivilegeEscalation=false \
        --set containerSecurityContext.readOnlyRootFilesystem=true \
        --set containerSecurityContext.runAsNonRoot=true \
        --set containerSecurityContext.capabilities.drop[0]=ALL \
        --wait
    
    # Wait for cert-manager pods to be ready
    log "Waiting for cert-manager pods to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager -n cert-manager --timeout=300s
    
    success "Cert-manager core components installed"
}

# Configure DNS provider credentials
configure_dns_provider() {
    log "Configuring DNS provider: ${DNS_PROVIDER}"
    
    case ${DNS_PROVIDER} in
        cloudflare)
            if [[ -z "${CLOUDFLARE_API_TOKEN:-}" ]]; then
                error "CLOUDFLARE_API_TOKEN environment variable is required"
                exit 1
            fi
            DNS_CONFIG="--set dnsProviders.cloudflare.enabled=true --set dnsProviders.cloudflare.apiToken=${CLOUDFLARE_API_TOKEN} --set dnsProviders.cloudflare.email=${EMAIL}"
            ;;
        route53)
            if [[ -z "${AWS_ACCESS_KEY_ID:-}" ]] || [[ -z "${AWS_SECRET_ACCESS_KEY:-}" ]]; then
                error "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables are required"
                exit 1
            fi
            DNS_CONFIG="--set dnsProviders.route53.enabled=true --set dnsProviders.route53.accessKeyId=${AWS_ACCESS_KEY_ID} --set dnsProviders.route53.secretAccessKey=${AWS_SECRET_ACCESS_KEY} --set dnsProviders.route53.region=${AWS_DEFAULT_REGION:-us-east-1}"
            ;;
        google)
            if [[ -z "${GOOGLE_CLOUD_DNS_SERVICE_ACCOUNT:-}" ]]; then
                error "GOOGLE_CLOUD_DNS_SERVICE_ACCOUNT environment variable is required"
                exit 1
            fi
            DNS_CONFIG="--set dnsProviders.googleCloudDNS.enabled=true --set dnsProviders.googleCloudDNS.serviceAccountKey=${GOOGLE_CLOUD_DNS_SERVICE_ACCOUNT} --set dnsProviders.googleCloudDNS.project=${GOOGLE_CLOUD_PROJECT}"
            ;;
        *)
            warn "Unknown DNS provider: ${DNS_PROVIDER}. Using HTTP-01 challenge"
            DNS_CONFIG=""
            ;;
    esac
    
    success "DNS provider configuration prepared"
}

# Deploy GuardianShield cert-manager configuration
deploy_guardian_cert_config() {
    log "Deploying GuardianShield certificate configuration..."
    
    # Prepare helm values
    HELM_VALUES="--set global.domain=${DOMAIN}"
    HELM_VALUES="${HELM_VALUES} --set letsEncrypt.production.email=${EMAIL}"
    HELM_VALUES="${HELM_VALUES} --set letsEncrypt.staging.email=${EMAIL}"
    HELM_VALUES="${HELM_VALUES} --set letsEncrypt.production.enabled=true"
    HELM_VALUES="${HELM_VALUES} --set monitoring.enabled=true"
    HELM_VALUES="${HELM_VALUES} --set security.networkPolicies.enabled=true"
    HELM_VALUES="${HELM_VALUES} --set security.podSecurityPolicy.enabled=true"
    HELM_VALUES="${HELM_VALUES} --set certificates.guardianShieldMain.enabled=true"
    HELM_VALUES="${HELM_VALUES} --set certificates.guardianShieldToken.enabled=true"
    HELM_VALUES="${HELM_VALUES} --set certificates.guardianShieldInternal.enabled=true"
    
    # Add DNS configuration if available
    if [[ -n "${DNS_CONFIG:-}" ]]; then
        HELM_VALUES="${HELM_VALUES} ${DNS_CONFIG}"
    fi
    
    # Install or upgrade the chart
    helm upgrade --install guardian-certs ${CHART_PATH} \
        --namespace ${NAMESPACE} \
        --create-namespace \
        ${HELM_VALUES} \
        --wait \
        --timeout=10m
    
    success "GuardianShield certificate configuration deployed"
}

# Verify certificate issuance
verify_certificates() {
    log "Verifying certificate issuance..."
    
    # Wait for certificates to be ready
    local certificates=(
        "guardian-shield-main-tls"
        "guardian-shield-token-tls"
        "guardian-shield-internal-tls"
    )
    
    for cert in "${certificates[@]}"; do
        log "Waiting for certificate: ${cert}"
        
        # Wait up to 5 minutes for certificate to be ready
        if kubectl wait --for=condition=ready certificate "${cert}" -n "${NAMESPACE}" --timeout=300s; then
            success "Certificate ${cert} is ready"
        else
            warn "Certificate ${cert} is not ready yet, checking status..."
            kubectl describe certificate "${cert}" -n "${NAMESPACE}"
        fi
    done
}

# Show certificate status
show_certificate_status() {
    log "Certificate Status Summary:"
    echo
    
    # Show all certificates
    kubectl get certificates -n "${NAMESPACE}" -o wide
    echo
    
    # Show certificate secrets
    log "Certificate Secrets:"
    kubectl get secrets -l cert-manager.io/certificate-name -n "${NAMESPACE}" -o wide
    echo
    
    # Show cluster issuers
    log "Cluster Issuers:"
    kubectl get clusterissuers -o wide
    echo
}

# Integration with existing GuardianShield containers
integrate_with_security_containers() {
    log "Integrating with existing GuardianShield security containers..."
    
    # Update container configurations to use new certificates
    local config_updates=(
        "nginx-ssl-config.conf"
        "api-server-tls.yaml"
        "agent-orchestrator-certs.yaml"
        "admin-console-https.conf"
    )
    
    for config in "${config_updates[@]}"; do
        if [[ -f "${config}" ]]; then
            log "Updating ${config} with new certificate paths..."
            # Here you would update your existing container configs
            # to reference the new Kubernetes secrets
        fi
    done
    
    # Create certificate update notification for containers
    cat > /tmp/cert-update-notification.json <<EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "event": "certificate_deployment",
    "certificates": [
        {
            "name": "guardian-shield-main-tls",
            "domains": ["${DOMAIN}", "*.${DOMAIN}"],
            "secret": "guardian-shield-main-tls",
            "namespace": "${NAMESPACE}"
        },
        {
            "name": "guardian-shield-token-tls",
            "domains": ["token.${DOMAIN}", "staking.${DOMAIN}"],
            "secret": "guardian-shield-token-tls",
            "namespace": "${NAMESPACE}"
        },
        {
            "name": "guardian-shield-internal-tls",
            "domains": ["*.${NAMESPACE}.svc.cluster.local"],
            "secret": "guardian-shield-internal-tls",
            "namespace": "${NAMESPACE}"
        }
    ],
    "actions": [
        "reload_nginx",
        "restart_api_server",
        "update_agent_configs",
        "refresh_admin_console"
    ]
}
EOF
    
    # If agent notification system exists, send the notification
    if command -v guardian-agent-notify &> /dev/null; then
        guardian-agent-notify --config /tmp/cert-update-notification.json
        success "Certificate update notification sent to security containers"
    fi
}

# Main deployment function
main() {
    log "Starting GuardianShield Cert-Manager deployment"
    log "Configuration:"
    log "  - Namespace: ${NAMESPACE}"
    log "  - Domain: ${DOMAIN}"
    log "  - Email: ${EMAIL}"
    log "  - DNS Provider: ${DNS_PROVIDER}"
    echo
    
    check_prerequisites
    install_cert_manager_crds
    create_namespace
    install_cert_manager
    configure_dns_provider
    deploy_guardian_cert_config
    verify_certificates
    show_certificate_status
    integrate_with_security_containers
    
    success "GuardianShield Cert-Manager deployment completed!"
    echo
    log "Next steps:"
    log "1. Verify certificates are working: curl -I https://${DOMAIN}"
    log "2. Check monitoring dashboard for certificate metrics"
    log "3. Update your application configs to use new certificate secrets"
    log "4. Test certificate renewal: kubectl annotate certificate guardian-shield-main-tls cert-manager.io/issue-temporary-certificate=true -n ${NAMESPACE}"
    echo
    log "Certificate secrets are available at:"
    log "  - Main application: guardian-shield-main-tls"
    log "  - Token service: guardian-shield-token-tls"
    log "  - Internal services: guardian-shield-internal-tls"
    echo
    log "For troubleshooting, check:"
    log "  - Certificate status: kubectl describe certificate <name> -n ${NAMESPACE}"
    log "  - Cert-manager logs: kubectl logs -n cert-manager -l app=cert-manager"
    log "  - ACME challenges: kubectl get challenges -A"
}

# Run main function
main "$@"