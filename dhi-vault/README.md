# DHI-Vault: Distributed HashiCorp Intelligence Vault

## Overview

DHI-Vault is an advanced API management system built on top of HashiCorp Vault, designed specifically for the GuardianShield ecosystem. It provides comprehensive API key management, OAuth2 authentication, JWT token handling, and advanced security features.

## Key Features

### 🔐 API Key Management
- **Secure Key Generation**: Cryptographically secure API key generation with customizable prefixes
- **Tiered Access Control**: Multiple client tiers (Basic, Premium, Enterprise, Developer) with different rate limits
- **Granular Scopes**: Fine-grained permission control through scopes
- **Key Lifecycle Management**: Complete lifecycle from creation to revocation
- **Usage Analytics**: Detailed usage tracking and statistics

### 🛡️ Authentication & Authorization
- **Multiple Auth Methods**: API keys, JWT tokens, OAuth2 flows
- **JWT Support**: Complete JWT token generation, validation, and JWKS endpoint
- **OAuth2 Implementation**: Full OAuth2 server with client credentials flow
- **Kubernetes Integration**: Seamless authentication with Kubernetes service accounts
- **Rate Limiting**: Advanced rate limiting per client tier

### 📊 Monitoring & Observability
- **Prometheus Metrics**: Comprehensive metrics collection for monitoring
- **Health Checks**: Multi-service health monitoring
- **Real-time Events**: WebSocket support for real-time API events
- **Detailed Logging**: Structured logging with configurable levels
- **Performance Analytics**: Request duration and throughput tracking

### 🚀 High Availability
- **Redis Caching**: High-performance caching layer for API keys and tokens
- **Vault Integration**: Secure secret storage with HashiCorp Vault
- **Horizontal Scaling**: Stateless design for easy horizontal scaling
- **Load Balancing**: Built-in support for load balancers
- **Failover Support**: Graceful degradation and error handling

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │────│   DHI-Vault     │────│  HashiCorp      │
│                 │    │   API Server    │    │  Vault          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              │
                       ┌─────────────────┐
                       │   Redis Cache   │
                       │                 │
                       └─────────────────┘
```

## Quick Start

### Prerequisites
- HashiCorp Vault cluster
- Redis instance
- Kubernetes cluster (optional)
- Python 3.11+

### Installation

1. **Clone and Setup**
```bash
git clone <repository>
cd dhi-vault
pip install -r requirements.txt
```

2. **Configuration**
Create a configuration file or set environment variables:
```yaml
vault:
  url: "https://vault.example.com:8200"
  token: "your-vault-token"

redis:
  url: "redis://redis.example.com:6379"
```

3. **Run DHI-Vault**
```bash
python dhi_vault_api.py
```

### Docker Deployment

```bash
# Build image
docker build -t guardianshield/dhi-vault:latest .

# Run container
docker run -p 8080:8080 \
  -e VAULT_ADDR=https://vault.example.com:8200 \
  -e REDIS_URL=redis://redis.example.com:6379 \
  guardianshield/dhi-vault:latest
```

### Kubernetes Deployment

```bash
kubectl apply -f kubernetes.yaml
```

## API Documentation

### Authentication

DHI-Vault supports multiple authentication methods:

1. **API Key Authentication**
```bash
curl -H "X-API-Key: dhi_your_api_key_here" \
     https://dhi-vault.example.com/api/v1/usage/client-id
```

2. **JWT Bearer Token**
```bash
curl -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIs..." \
     https://dhi-vault.example.com/api/v1/keys
```

### Core Endpoints

#### Create API Key
```bash
POST /api/v1/keys
Content-Type: application/json

{
  "client_id": "my-client",
  "tier": "premium",
  "scopes": ["read", "write"],
  "expires_in": 86400,
  "metadata": {
    "application": "my-app",
    "environment": "production"
  }
}
```

Response:
```json
{
  "api_key": "dhi_abc123_def456...",
  "key_id": "abc123",
  "client_id": "my-client",
  "status": "active",
  "tier": "premium",
  "created_at": "2024-01-01T00:00:00Z",
  "expires_at": "2024-01-02T00:00:00Z",
  "scopes": ["read", "write"],
  "rate_limit": 5000
}
```

#### OAuth2 Token Endpoint
```bash
POST /api/v1/oauth2/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&client_id=your-client&client_secret=your-secret&scope=read write
```

#### JWT Generation
```bash
POST /api/v1/jwt/generate
Content-Type: application/json

{
  "client_id": "my-client",
  "scopes": ["read", "write"],
  "expires_in": 3600
}
```

#### Usage Statistics
```bash
GET /api/v1/usage/{client_id}
```

Response:
```json
{
  "client_id": "my-client",
  "total_usage": 15420,
  "active_keys": 3,
  "current_hour_usage": 142,
  "api_keys": [
    {
      "key_id": "abc123",
      "status": "active",
      "created_at": "2024-01-01T00:00:00Z",
      "last_used": "2024-01-01T12:30:00Z",
      "usage_count": 5140,
      "scopes": ["read", "write"]
    }
  ]
}
```

## Client Tiers and Rate Limits

| Tier       | Requests/Hour | Features                    |
|------------|---------------|-----------------------------|
| Basic      | 1,000         | Standard API access         |
| Premium    | 5,000         | Priority support, analytics |
| Enterprise | 20,000        | Custom integrations, SLA    |
| Developer  | 10,000        | Development features        |

## Security Features

### Encryption
- **At Rest**: All sensitive data encrypted using Fernet encryption
- **In Transit**: TLS encryption for all communications
- **Key Management**: Secure key derivation using PBKDF2

### Access Control
- **Scoped Permissions**: Fine-grained access control through scopes
- **Time-based Expiration**: Configurable key and token expiration
- **Revocation**: Immediate key and token revocation
- **Rate Limiting**: Per-client and global rate limiting

### Monitoring
- **Audit Logging**: Comprehensive audit trail
- **Anomaly Detection**: Unusual usage pattern detection
- **Real-time Alerts**: Configurable security alerts
- **Metrics Collection**: Detailed security metrics

## Monitoring and Metrics

### Prometheus Metrics

DHI-Vault exposes the following metrics:

- `dhi_vault_api_requests_total`: Total API requests by method, endpoint, and status
- `dhi_vault_api_request_duration_seconds`: Request duration histogram
- `dhi_vault_active_api_keys_total`: Number of active API keys
- `dhi_vault_operations_total`: Total Vault operations by type and status

### Health Checks

```bash
GET /health
```

Returns comprehensive health status including:
- Vault connectivity and status
- Redis connectivity
- Kubernetes integration
- Service dependencies

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VAULT_ADDR` | Vault server URL | `https://vault.guardianshield.svc.cluster.local:8200` |
| `REDIS_URL` | Redis connection URL | `redis://redis.guardianshield.svc.cluster.local:6379` |
| `SERVER_HOST` | Server bind address | `0.0.0.0` |
| `SERVER_PORT` | Server port | `8080` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Configuration File

DHI-Vault supports YAML configuration files:

```yaml
vault:
  url: "https://vault.example.com:8200"
  verify_tls: true
  auth_method: "kubernetes"
  role: "dhi-vault-api"

redis:
  url: "redis://redis.example.com:6379"
  database: 0
  max_connections: 20

server:
  host: "0.0.0.0"
  port: 8080

security:
  encryption_password: "your-secure-password"
  jwt_signing_key: "your-jwt-signing-key"

rate_limiting:
  enabled: true
  global_limit: 10000
  tier_limits:
    basic: 1000
    premium: 5000
    enterprise: 20000
    developer: 10000
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone <repository>
cd dhi-vault

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-asyncio black isort flake8 mypy
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=dhi_vault

# Run specific test
pytest tests/test_api.py::test_create_api_key
```

### Code Quality

```bash
# Format code
black dhi_vault_*.py
isort dhi_vault_*.py

# Lint code
flake8 dhi_vault_*.py

# Type checking
mypy dhi_vault_*.py
```

## Troubleshooting

### Common Issues

1. **Vault Connection Issues**
   - Verify Vault URL and token
   - Check network connectivity
   - Ensure Vault is unsealed

2. **Redis Connection Issues**
   - Verify Redis URL and credentials
   - Check Redis server status
   - Ensure network connectivity

3. **Authentication Failures**
   - Verify API key format and validity
   - Check JWT token expiration
   - Ensure proper scopes

4. **Rate Limiting**
   - Check client tier and limits
   - Monitor usage patterns
   - Consider upgrading tier

### Debugging

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python dhi_vault_api.py
```

Or set in configuration:
```yaml
logging:
  level: "DEBUG"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run code quality checks
5. Submit a pull request

## License

[Add appropriate license information]

## Support

For support and questions:
- GitHub Issues: [Repository Issues]
- Documentation: [Documentation URL]
- Security Issues: [Security Contact]