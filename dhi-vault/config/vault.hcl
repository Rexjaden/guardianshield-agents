# GuardianShield DHI-Vault Configuration
# High Availability Vault Configuration

# Cluster configuration
cluster_name = "dhi-vault-guardianshield"

# API listener
listener "tcp" {
  address = "0.0.0.0:8200"
  tls_disable = false
  tls_cert_file = "/vault/tls/tls.crt"
  tls_key_file = "/vault/tls/tls.key"
  tls_client_ca_file = "/vault/tls/ca.crt"
  tls_min_version = "tls12"
}

# Cluster listener for HA
listener "tcp" {
  address = "0.0.0.0:8201"
  cluster_address = "0.0.0.0:8201"
  tls_disable = false
  tls_cert_file = "/vault/tls/tls.crt"
  tls_key_file = "/vault/tls/tls.key"
  tls_client_ca_file = "/vault/tls/ca.crt"
}

# Storage backend (raft for HA)
storage "raft" {
  path = "/vault/data"
  node_id = "POD_NAME"
  
  retry_join {
    leader_api_addr = "http://dhi-vault-0.dhi-vault-headless.guardianshield.svc.cluster.local:8200"
  }
  retry_join {
    leader_api_addr = "http://dhi-vault-1.dhi-vault-headless.guardianshield.svc.cluster.local:8200"
  }
  retry_join {
    leader_api_addr = "http://dhi-vault-2.dhi-vault-headless.guardianshield.svc.cluster.local:8200"
  }
}

# Seal configuration (Auto-unseal with Kubernetes)
seal "kubernetes" {
  cluster_name = "dhi-vault-guardianshield"
  namespace = "guardianshield"
  service_account = "dhi-vault"
}

# UI
ui = true

# Logging
log_level = "INFO"
log_format = "json"

# Disable mlock for containers
disable_mlock = true

# API configuration
api_addr = "http://POD_IP:8200"
cluster_addr = "http://POD_IP:8201"

# Performance settings
default_lease_ttl = "768h"
max_lease_ttl = "8760h"

# Plugin directory
plugin_directory = "/vault/plugins"

# Enable raw endpoint (for health checks)
raw_storage_endpoint = true

# Telemetry
telemetry {
  prometheus_retention_time = "30s"
  disable_hostname = true
  unauthenticated_metrics_access = false
}

# Service registration for HA discovery
service_registration "kubernetes" {
  namespace = "guardianshield"
  pod_name = "POD_NAME"
}