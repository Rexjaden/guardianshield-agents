# GuardianShield Cert-Manager Chart

This Helm chart provides automated certificate management for the GuardianShield security platform using cert-manager with comprehensive SSL/TLS automation.

## Features

### 🔐 Automated Certificate Management
- **Let's Encrypt Integration**: Production and staging ACME certificates
- **Multi-Domain Support**: Wildcard and individual domain certificates
- **Internal Service Certificates**: Self-signed certificates for internal communication
- **Auto-Renewal**: Certificates automatically renewed before expiration

### 🛡️ Security Hardening
- **RBAC Controls**: Minimal required permissions for cert-manager components
- **Network Policies**: Restricted network access for certificate management
- **Pod Security Policies**: Enforced security contexts and restrictions
- **Non-Root Execution**: All components run as non-privileged users

### 📊 Monitoring & Alerting
- **Prometheus Integration**: Certificate expiration and health metrics
- **Alert Rules**: Proactive notification for certificate issues
- **Service Monitoring**: Real-time visibility into certificate status

### 🌐 DNS Challenge Support
- **Cloudflare**: DNS-01 challenge automation
- **AWS Route53**: DNS challenge with IAM credentials
- **Google Cloud DNS**: GCP service account integration
- **HTTP-01 Fallback**: Ingress-based challenges when DNS unavailable

## Quick Start

### Prerequisites
- Kubernetes cluster (1.19+)
- Helm 3.0+
- cert-manager CRDs installed

### Installation

1. **Add chart repository** (if external):
   ```bash
   helm repo add guardianshield https://charts.guardian-shield.io
   helm repo update
   ```

2. **Install cert-manager CRDs**:
   ```bash
   kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.4/cert-manager.crds.yaml
   ```

3. **Install the chart**:
   ```bash
   helm install guardian-certs ./charts/dhi-cert-manager-chart \
     --namespace guardian-shield \
     --create-namespace \
     --set global.domain=guardian-shield.io \
     --set letsEncrypt.production.email=admin@guardian-shield.io
   ```

### DNS Provider Configuration

#### Cloudflare
```bash
helm install guardian-certs ./charts/dhi-cert-manager-chart \
  --set dnsProviders.cloudflare.enabled=true \
  --set dnsProviders.cloudflare.email=your@email.com \
  --set dnsProviders.cloudflare.apiToken=YOUR_API_TOKEN
```

#### AWS Route53
```bash
helm install guardian-certs ./charts/dhi-cert-manager-chart \
  --set dnsProviders.route53.enabled=true \
  --set dnsProviders.route53.region=us-east-1 \
  --set dnsProviders.route53.accessKeyId=YOUR_ACCESS_KEY \
  --set dnsProviders.route53.secretAccessKey=YOUR_SECRET_KEY
```

## Certificate Types

### Main Application Certificate
```yaml
certificates:
  guardianShieldMain:
    enabled: true
```
Covers:
- `guardian-shield.io`
- `www.guardian-shield.io`
- `api.guardian-shield.io`
- `admin.guardian-shield.io`
- `agents.guardian-shield.io`
- `*.guardian-shield.io`

### Token Service Certificate
```yaml
certificates:
  guardianShieldToken:
    enabled: true
```
Covers:
- `token.guardian-shield.io`
- `token-api.guardian-shield.io`
- `staking.guardian-shield.io`

### Internal Service Certificate
```yaml
certificates:
  guardianShieldInternal:
    enabled: true
```
Covers internal Kubernetes services:
- Agent orchestrator
- API server
- Analytics dashboard
- Admin console
- Blockchain indexer

## Configuration

### Core Settings
```yaml
global:
  domain: guardian-shield.io

letsEncrypt:
  production:
    enabled: true
    email: admin@guardian-shield.io
  staging:
    enabled: true
    email: admin@guardian-shield.io

certificates:
  duration: 2160h    # 90 days
  renewBefore: 360h  # 15 days
```

### Security Configuration
```yaml
security:
  serviceAccount:
    create: true
    automount: false
  podSecurityPolicy:
    enabled: true
  networkPolicies:
    enabled: true
  podDisruptionBudget:
    enabled: true
    minAvailable: 1
```

### Monitoring Configuration
```yaml
monitoring:
  enabled: true
  scrapeInterval: 30s
  alertRuleInterval: 30s
  alertFor: 5m
```

## Advanced Features

### Custom Certificate Templates
```yaml
certificates:
  custom:
    - name: custom-service-cert
      secretName: custom-service-tls
      dnsNames:
        - custom.guardian-shield.io
        - api.custom.guardian-shield.io
      duration: 720h
      renewBefore: 240h
```

### High Availability
```yaml
certManager:
  controller:
    replicaCount: 2
  webhook:
    replicaCount: 2
    
security:
  podDisruptionBudget:
    enabled: true
    minAvailable: 1
```

## Monitoring & Troubleshooting

### Certificate Status
```bash
# Check certificate status
kubectl get certificates -n guardian-shield

# Describe certificate for details
kubectl describe certificate guardian-shield-main-tls -n guardian-shield

# Check certificate events
kubectl get events --field-selector involvedObject.kind=Certificate -n guardian-shield
```

### Monitoring Queries
```promql
# Certificate expiration time (days)
(certmanager_certificate_expiration_timestamp_seconds - time()) / 86400

# Certificate readiness status
certmanager_certificate_ready_status

# ACME challenge success rate
rate(certmanager_acme_client_request_count{status=~"2.."}[5m])
```

### Common Issues

#### Certificate Not Ready
1. Check cert-manager logs: `kubectl logs -n cert-manager deployment/cert-manager`
2. Verify DNS configuration and credentials
3. Check ACME challenge status: `kubectl describe challenge -A`

#### DNS Challenge Failures
1. Verify DNS provider credentials
2. Check network policies allow ACME server access
3. Validate DNS propagation: `nslookup _acme-challenge.your-domain.com`

## Upgrade Strategy

### Rolling Updates
```bash
# Upgrade with zero downtime
helm upgrade guardian-certs ./charts/dhi-cert-manager-chart \
  --namespace guardian-shield \
  --wait \
  --timeout=10m
```

### Backup Certificates
```bash
# Backup certificate secrets
kubectl get secrets -l cert-manager.io/certificate-name \
  -o yaml > certificate-backup.yaml
```

## Integration with GuardianShield

### Agent Communication
- Internal certificates enable encrypted agent-to-agent communication
- Mutual TLS for API server connections
- Secure database connections with client certificates

### Token Service Integration
- Dedicated certificates for staking and token operations
- High-security key rotation for financial operations
- Multi-region certificate deployment

### Monitoring Integration
- Certificate status integrated with GuardianShield dashboard
- Automated alerts to admin console
- Performance metrics for security analytics

## Security Considerations

### Best Practices
- Use DNS challenges for internal services
- Implement certificate pinning for critical services
- Regular certificate rotation (90-day max)
- Monitor certificate transparency logs

### Compliance
- SOC2 Type II compatible certificate management
- PCI DSS compliant for payment processing certificates
- GDPR compliant certificate storage and rotation

## Support & Maintenance

### Automated Maintenance
- Daily certificate status checks
- Automated renewal 15 days before expiration
- Self-healing certificate re-issuance
- Proactive alert notifications

### Manual Operations
```bash
# Force certificate renewal
kubectl annotate certificate guardian-shield-main-tls \
  cert-manager.io/issue-temporary-certificate="true"

# Check cert-manager status
kubectl get pods -n cert-manager
kubectl logs -n cert-manager -l app=cert-manager
```