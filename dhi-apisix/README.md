# DHI-APISIX API Security Gateway

Apache APISIX-based API security gateway for GuardianShield ecosystem providing comprehensive API protection, traffic management, and threat detection.

## Features

### 🛡️ **API Security**
- **Authentication & Authorization**: JWT, OAuth2, API Key, mTLS
- **Rate Limiting**: Advanced rate limiting with Redis backend
- **Web Application Firewall (WAF)**: SQL injection, XSS, CSRF protection
- **SSL/TLS Termination**: Automatic certificate management
- **IP Whitelisting/Blacklisting**: Geo-blocking and threat IP filtering

### 🔍 **Threat Detection**
- **Real-time Monitoring**: API traffic analysis and anomaly detection
- **DDoS Protection**: Intelligent traffic filtering and mitigation
- **Bot Detection**: Advanced bot filtering and CAPTCHA integration
- **Threat Intelligence Integration**: Real-time threat feed integration
- **Security Headers**: HSTS, CSP, CSRF protection headers

### 📊 **Observability**
- **Prometheus Metrics**: Comprehensive API metrics and security events
- **Grafana Dashboards**: Real-time security monitoring
- **Distributed Tracing**: OpenTelemetry integration
- **Audit Logging**: Detailed security event logging
- **Health Checks**: Multi-layer health monitoring

### ⚡ **Performance**
- **Load Balancing**: Intelligent traffic distribution
- **Caching**: Multi-tier caching with Redis
- **Compression**: Gzip, Brotli compression
- **Connection Pooling**: Optimized upstream connections
- **Circuit Breaker**: Automatic failure detection and recovery

## Architecture

```
Internet → Ingress → APISIX Gateway → Backend Services
                        ↓
                   Security Plugins
                        ↓
                   Threat Detection
                        ↓
                   Monitoring & Logs
```

## Components

- **APISIX Core**: API gateway engine with Lua scripting
- **etcd**: Configuration and service discovery
- **Dashboard**: Web-based management interface
- **Prometheus Plugin**: Metrics collection
- **Security Plugins**: WAF, rate limiting, authentication
- **Custom Plugins**: GuardianShield-specific security features

## Integration

- **GuardianShield Agents**: Real-time threat intelligence
- **DHI-ClamAV**: Malware scanning for uploaded files
- **Threat Intelligence APIs**: External threat feed integration
- **Redis**: Shared caching and rate limiting
- **PostgreSQL**: Configuration and audit log storage

## Quick Start

```bash
# Deploy DHI-APISIX
kubectl apply -f kubernetes.yaml

# Configure routes
kubectl apply -f routes/

# Monitor dashboard
kubectl port-forward svc/dhi-apisix-dashboard 9000:9000
```

## Security Plugins

### Core Security
- `limit-req`: Rate limiting
- `limit-conn`: Connection limiting  
- `ip-restriction`: IP filtering
- `jwt-auth`: JWT authentication
- `key-auth`: API key authentication
- `oauth`: OAuth2 integration

### Web Application Firewall
- `waf`: Core WAF functionality
- `csrf`: CSRF protection
- `cors`: CORS policy enforcement
- `referer-restriction`: Referer validation

### Custom GuardianShield Plugins
- `guardianshield-threat-intel`: Real-time threat detection
- `guardianshield-web3-security`: Web3-specific security rules
- `guardianshield-malware-scan`: Integration with DHI-ClamAV

## Configuration

See `config/` directory for:
- `apisix.yaml`: Main APISIX configuration
- `plugins/`: Custom plugin configurations
- `routes/`: API route definitions
- `upstreams/`: Backend service configurations

## Monitoring

- **Dashboard**: `https://apisix-admin.guardianshield.io`
- **Metrics**: `https://apisix.guardianshield.io/apisix/prometheus/metrics`
- **Health**: `https://apisix.guardianshield.io/apisix/status`

## Documentation

- [Installation Guide](docs/installation.md)
- [Security Configuration](docs/security.md)
- [Custom Plugins](docs/plugins.md)
- [Monitoring Setup](docs/monitoring.md)
- [Troubleshooting](docs/troubleshooting.md)