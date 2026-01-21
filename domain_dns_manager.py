"""
GuardianShield Domain DNS Management
Automated DNS record management for guardianshield.io
"""

import os
import subprocess
import json
from typing import Dict, List
import time

class GuardianShieldDNS:
    """Manages DNS records for GuardianShield domain"""
    
    def __init__(self, domain: str = "guardianshield.io"):
        self.domain = domain
        self.dns_records = {}
        self.load_dns_config()
    
    def load_dns_config(self):
        """Load DNS configuration from file"""
        self.dns_records = {
            # Main website and services
            "www": {"type": "CNAME", "value": "guardianshield.github.io", "proxied": True},
            "api": {"type": "A", "value": "YOUR_SERVER_IP", "proxied": True},
            "app": {"type": "A", "value": "YOUR_SERVER_IP", "proxied": True},
            "dashboard": {"type": "A", "value": "YOUR_SERVER_IP", "proxied": True},
            
            # AI Agent services (internal)
            "agents": {"type": "A", "value": "YOUR_SERVER_IP", "proxied": False},
            "learning": {"type": "A", "value": "YOUR_SERVER_IP", "proxied": False},
            "analytics": {"type": "A", "value": "YOUR_SERVER_IP", "proxied": False},
            "evolution": {"type": "A", "value": "YOUR_SERVER_IP", "proxied": False},
            "ingestion": {"type": "A", "value": "YOUR_SERVER_IP", "proxied": False},
            "monitor": {"type": "A", "value": "YOUR_SERVER_IP", "proxied": False},
            "blockchain": {"type": "A", "value": "YOUR_SERVER_IP", "proxied": False},
            
            # Infrastructure
            "mesh": {"type": "A", "value": "YOUR_SERVER_IP", "proxied": False},
            "dns": {"type": "A", "value": "YOUR_SERVER_IP", "proxied": False},
            "vault": {"type": "A", "value": "YOUR_SERVER_IP", "proxied": True},
            "logs": {"type": "A", "value": "YOUR_SERVER_IP", "proxied": False},
            
            # Development
            "dev": {"type": "A", "value": "YOUR_DEV_IP", "proxied": True},
            "staging": {"type": "A", "value": "YOUR_STAGING_IP", "proxied": True},
            "test": {"type": "A", "value": "YOUR_TEST_IP", "proxied": True},
            
            # Documentation
            "docs": {"type": "CNAME", "value": "guardianshield-docs.netlify.app", "proxied": True},
            "support": {"type": "A", "value": "YOUR_SERVER_IP", "proxied": True},
            "status": {"type": "CNAME", "value": "guardianshield.statuspage.io", "proxied": True},
            
            # Security (restricted)
            "admin": {"type": "A", "value": "YOUR_SERVER_IP", "proxied": True},
            "security": {"type": "A", "value": "YOUR_SERVER_IP", "proxied": True},
            "emergency": {"type": "A", "value": "YOUR_SERVER_IP", "proxied": True},
        }
    
    def create_external_dns_annotations(self, service_name: str, subdomain: str, port: int = None):
        """Create External DNS annotations for Kubernetes/Docker services"""
        annotations = {
            "external-dns.alpha.kubernetes.io/hostname": f"{subdomain}.{self.domain}",
            "external-dns.alpha.kubernetes.io/ttl": "300"
        }
        
        if port:
            annotations["external-dns.alpha.kubernetes.io/target"] = f"YOUR_SERVER_IP:{port}"
        
        return annotations
    
    def update_docker_compose_with_dns(self):
        """Update Docker Compose with DNS annotations"""
        dns_services = {
            "guardianshield-api": {
                "subdomain": "api", 
                "port": 8000,
                "labels": [
                    "external-dns.alpha.kubernetes.io/hostname=api.guardianshield.io",
                    "external-dns.alpha.kubernetes.io/ttl=300"
                ]
            },
            "learning-agent": {
                "subdomain": "learning",
                "port": 8001, 
                "labels": [
                    "external-dns.alpha.kubernetes.io/hostname=learning.guardianshield.io",
                    "external-dns.alpha.kubernetes.io/ttl=300"
                ]
            },
            "behavioral-analytics": {
                "subdomain": "analytics",
                "port": 8081,  # Professional website service
                "labels": [
                    "external-dns.alpha.kubernetes.io/hostname=analytics.guardianshield.io",
                    "external-dns.alpha.kubernetes.io/ttl=300"
                ]
            },
            "genetic-evolver": {
                "subdomain": "evolution", 
                "port": 8003,
                "labels": [
                    "external-dns.alpha.kubernetes.io/hostname=evolution.guardianshield.io",
                    "external-dns.alpha.kubernetes.io/ttl=300"
                ]
            },
            "guardianshield-postgres": {
                "subdomain": "db",
                "port": 5432,
                "internal": True,  # No external access
                "labels": [
                    "external-dns.alpha.kubernetes.io/hostname=db.internal.guardianshield.io",
                    "external-dns.alpha.kubernetes.io/ttl=300"
                ]
            }
        }
        
        return dns_services
    
    def generate_cloudflare_config(self):
        """Generate Cloudflare configuration for External DNS"""
        config = {
            "cloudflare": {
                "apiEmail": "YOUR_CLOUDFLARE_EMAIL",
                "apiKey": "YOUR_CLOUDFLARE_API_KEY", 
                "zoneId": "YOUR_ZONE_ID",
                "domain": self.domain,
                "proxied": True,
                "ttl": 300
            },
            "external_dns": {
                "provider": "cloudflare",
                "domain_filter": self.domain,
                "policy": "upsert-only",
                "txt_owner_id": "guardianshield-cluster",
                "txt_prefix": "guardianshield-",
                "interval": "30s",
                "log_level": "info"
            }
        }
        
        # Save configuration
        with open("cloudflare-dns-config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        return config
    
    def create_nginx_proxy_config(self):
        """Create NGINX proxy configuration for subdomains"""
        nginx_config = f"""
# GuardianShield Domain Proxy Configuration

# Main website
server {{
    listen 80;
    server_name www.{self.domain} {self.domain};
    
    location / {{
        return 301 https://$server_name$request_uri;
    }}
}}

server {{
    listen 443 ssl;
    server_name www.{self.domain} {self.domain};
    
    ssl_certificate /etc/ssl/certs/guardianshield.crt;
    ssl_certificate_key /etc/ssl/private/guardianshield.key;
    
    location / {{
        proxy_pass http://localhost:3000;  # Your website
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}
}}

# API Gateway
server {{
    listen 443 ssl;
    server_name api.{self.domain};
    
    ssl_certificate /etc/ssl/certs/guardianshield.crt;
    ssl_certificate_key /etc/ssl/private/guardianshield.key;
    
    location / {{
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
    }}
}}

# Dashboard
server {{
    listen 443 ssl;
    server_name dashboard.{self.domain};
    
    ssl_certificate /etc/ssl/certs/guardianshield.crt;
    ssl_certificate_key /etc/ssl/private/guardianshield.key;
    
    location / {{
        proxy_pass http://localhost:8000/dashboard;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}
}}

# AI Agent Services (requires authentication)
server {{
    listen 443 ssl;
    server_name agents.{self.domain};
    
    ssl_certificate /etc/ssl/certs/guardianshield.crt;
    ssl_certificate_key /etc/ssl/private/guardianshield.key;
    
    # Basic authentication for agents
    auth_basic "GuardianShield Agents";
    auth_basic_user_file /etc/nginx/.htpasswd;
    
    location /learning {{
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
    }}
    
    location /analytics {{
        # Redirect to new professional website on 8081
        proxy_pass http://localhost:8081;
        proxy_set_header Host $host;
    }}
    
    location /evolution {{
        proxy_pass http://localhost:8003;
        proxy_set_header Host $host;
    }}
}}

# Admin Panel (master key required)
server {{
    listen 443 ssl;
    server_name admin.{self.domain};
    
    ssl_certificate /etc/ssl/certs/guardianshield.crt;
    ssl_certificate_key /etc/ssl/private/guardianshield.key;
    
    location / {{
        # Check for emergency admin session
        access_by_lua_block {{
            local file = io.open("/app/.emergency_admin_session", "r")
            if not file then
                ngx.status = 503
                ngx.say("Emergency lockdown active. Access denied.")
                ngx.exit(503)
            end
            file:close()
        }}
        
        proxy_pass http://localhost:8000/admin;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}
}}
"""
        
        with open("nginx-guardianshield-proxy.conf", "w") as f:
            f.write(nginx_config)
        
        return nginx_config
    
    def setup_domain_dns(self):
        """Complete domain DNS setup"""
        print(f"🌐 Setting up DNS for {self.domain}")
        print("=" * 50)
        
        # Generate configurations
        cloudflare_config = self.generate_cloudflare_config()
        nginx_config = self.create_nginx_proxy_config()
        dns_services = self.update_docker_compose_with_dns()
        
        print("✅ Generated Cloudflare configuration")
        print("✅ Generated NGINX proxy configuration") 
        print("✅ Generated Docker service DNS annotations")
        
        print(f"\n🔧 Configuration files created:")
        print("   📄 cloudflare-dns-config.json")
        print("   📄 nginx-guardianshield-proxy.conf")
        print("   📄 guardianshield-dns.conf")
        
        print(f"\n🌍 Your domain structure:")
        for subdomain, config in self.dns_records.items():
            print(f"   {subdomain}.{self.domain} -> {config['value']}")
        
        print(f"\n⚡ Next steps:")
        print("1. Update YOUR_SERVER_IP with your actual server IP")
        print("2. Add Cloudflare API credentials to environment") 
        print("3. Deploy NGINX configuration")
        print("4. Restart External DNS with domain config")
        
        return True

if __name__ == "__main__":
    dns_manager = GuardianShieldDNS("guardianshield.io")
    dns_manager.setup_domain_dns()