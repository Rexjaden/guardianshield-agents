# GuardianShield Enterprise AlertManager Helm Chart
# Complete monitoring solution for ERC-8055, blockchain, and website infrastructure

## Overview

This chart deploys a comprehensive AlertManager configuration that monitors your entire GuardianShield ecosystem:

- **ERC-8055 Shield Token System**: Burn/remint operations, fraud detection, serial number tracking
- **Blockchain Infrastructure**: Nodes, validators, consensus, transaction pools
- **Website & API**: Performance, uptime, error rates, user experience
- **Infrastructure**: Kubernetes, storage, networking, security

## Features

### 🛡️ ERC-8055 Monitoring
- Shield Token burn/remint failure detection
- Serial number collision alerts
- Guard Token transfer rate monitoring
- Anti-fraud system surveillance

### ⛓️ Blockchain Monitoring
- Multi-node health and sync status
- Validator balance and performance
- Transaction pool congestion detection
- Cross-chain bridge monitoring

### 🌐 Website Monitoring
- Response time and uptime tracking
- Error rate and performance alerts
- Conversion rate monitoring
- API gateway health checks

### 🏗️ Infrastructure Monitoring
- Kubernetes cluster health
- Node resource utilization
- Storage and networking alerts
- Security and compliance monitoring

## Installation

### Prerequisites
- Kubernetes 1.20+
- Helm 3.8+
- Prometheus Operator (optional but recommended)
- Cert-Manager for TLS (optional)

### Quick Start

```bash
# Add the repository (if published)
helm repo add guardianshield https://charts.guardianshield.io
helm repo update

# Install with default values
helm install guardianshield-alerts guardianshield/dhi-alertmanager-chart \
  --namespace guardianshield-monitoring \
  --create-namespace

# Install with custom values
helm install guardianshield-alerts ./charts/dhi-alertmanager-chart \
  --namespace guardianshield-monitoring \
  --create-namespace \
  --values custom-values.yaml
```

### Custom Values Example

```yaml
# custom-values.yaml
global:
  environment: production
  clusterName: guardianshield-mainnet

alertmanager:
  replicaCount: 3
  
  resources:
    requests:
      memory: "512Mi"
      cpu: "200m"
    limits:
      memory: "2Gi"
      cpu: "1000m"

  config:
    global:
      smtp_smarthost: 'your-smtp-server:587'
      smtp_from: 'alerts@yourdomain.com'
    
    receivers:
      - name: 'erc8055-critical-team'
        email_configs:
          - to: 'your-erc8055-team@yourdomain.com'
        slack_configs:
          - api_url: 'your-slack-webhook-url'
            channel: '#erc8055-alerts'

ingress:
  enabled: true
  hosts:
    - host: alerts.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
```

## Configuration

### Alert Routing

The chart comes with pre-configured alert routing for different teams:

- **ERC-8055 Critical Team**: Handles Shield Token and Guard Token alerts
- **Blockchain Ops Team**: Manages blockchain infrastructure alerts
- **Website Ops Team**: Monitors website and API performance
- **Infrastructure Team**: Oversees Kubernetes and system health

### Notification Channels

Supports multiple notification channels:
- Email notifications with HTML templates
- Slack integration with custom channels
- PagerDuty for critical alerts
- Webhook endpoints for custom integrations

### Security

- RBAC enabled by default
- Network policies for pod communication
- TLS encryption for web interface
- Authentication via ingress annotations

## Monitoring Targets

### Default Targets

The chart monitors these services by default:

```yaml
# ERC-8055 Services
- shield-token-api:8080
- guard-token-api:8081

# Blockchain Nodes
- blockchain-node-1:8545
- blockchain-node-2:8545
- validator-node-1:9000

# Website Services
- guardianshield-website:3000
- api-gateway:8080

# Infrastructure
- kubernetes-apiserver
- etcd-cluster
```

### Custom Targets

Add your own monitoring targets in the values file:

```yaml
monitoring:
  targets:
    custom:
      enabled: true
      endpoints:
        - my-service:8080
        - another-service:9090
      metrics:
        - custom_metric_name
        - another_custom_metric
```

## Alert Rules

### Critical Alerts (Immediate Response)
- ERC-8055 Shield Token burn/remint failures
- Blockchain node outages
- Website complete downtime
- Kubernetes API server failures

### Warning Alerts (Investigation Required)
- High transaction rates
- Performance degradation
- Resource utilization spikes
- Security anomalies

### Info Alerts (Awareness)
- Scheduled maintenance
- Configuration changes
- Performance baselines

## Troubleshooting

### Common Issues

1. **Alerts not firing**: Check Prometheus scrape targets
2. **High memory usage**: Increase resource limits
3. **Notification failures**: Verify SMTP/webhook configurations
4. **Storage issues**: Ensure PVC is properly provisioned

### Useful Commands

```bash
# Check AlertManager status
kubectl get pods -n guardianshield-monitoring
kubectl logs alertmanager-pod-name -n guardianshield-monitoring

# View current alerts
kubectl port-forward svc/guardianshield-alerts 9093:9093
# Open http://localhost:9093

# Test configuration
helm template ./charts/dhi-alertmanager-chart --debug

# Upgrade deployment
helm upgrade guardianshield-alerts ./charts/dhi-alertmanager-chart
```

## Customization

### Adding New Alert Rules

1. Create a new ConfigMap in `templates/`
2. Add the ConfigMap to the deployment volumes
3. Reference in your custom values

### Integrating with External Systems

The chart supports webhook integrations for:
- Custom dashboards
- Incident management systems
- Automated remediation tools
- Compliance reporting

## Support

For issues and questions:
- GitHub: https://github.com/Rexjaden/guardianshield-agents
- Documentation: https://docs.guardianshield.io
- Community: https://discord.gg/guardianshield

## License

This chart is part of the GuardianShield project and follows the same licensing terms.