#!/usr/bin/env python3
"""
GuardianShield Cert-Manager Security Integration
Demonstrates how automated certificate management enhances the existing security container team
"""

import json
import logging
import asyncio
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CertificateSecurityIntegrator:
    """
    Integrates cert-manager with existing GuardianShield security containers
    """
    
    def __init__(self):
        self.namespace = "guardian-shield"
        self.cert_secrets = {
            "main": "guardian-shield-main-tls",
            "token": "guardian-shield-token-tls", 
            "internal": "guardian-shield-internal-tls"
        }
        self.security_containers = [
            "agent-orchestrator",
            "api-server", 
            "analytics-dashboard",
            "admin-console",
            "blockchain-indexer",
            "data-ingestion",
            "threat-intelligence"
        ]
    
    async def check_certificate_status(self) -> Dict[str, Dict]:
        """Check status of all managed certificates"""
        logger.info("Checking certificate status...")
        
        cert_status = {}
        
        for cert_name, secret_name in self.cert_secrets.items():
            try:
                # Check certificate readiness
                cmd = ["kubectl", "get", "certificate", secret_name, "-n", self.namespace, "-o", "json"]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                cert_info = json.loads(result.stdout)
                
                status = cert_info.get("status", {})
                conditions = status.get("conditions", [])
                
                cert_status[cert_name] = {
                    "secret_name": secret_name,
                    "ready": any(c.get("type") == "Ready" and c.get("status") == "True" for c in conditions),
                    "expiration": status.get("notAfter"),
                    "renewal_time": status.get("renewalTime"),
                    "issuer": cert_info.get("spec", {}).get("issuerRef", {}).get("name"),
                    "domains": cert_info.get("spec", {}).get("dnsNames", [])
                }
                
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to check certificate {cert_name}: {e}")
                cert_status[cert_name] = {"error": str(e)}
        
        return cert_status
    
    async def update_container_configurations(self, cert_status: Dict[str, Dict]):
        """Update security container configurations with new certificates"""
        logger.info("Updating security container configurations...")
        
        updates = []
        
        for container in self.security_containers:
            if container == "api-server":
                # Update API server with main domain certificate
                config = {
                    "container": container,
                    "certificate_config": {
                        "tls_cert_path": f"/etc/ssl/certs/{self.cert_secrets['main']}/tls.crt",
                        "tls_key_path": f"/etc/ssl/certs/{self.cert_secrets['main']}/tls.key",
                        "ca_cert_path": f"/etc/ssl/certs/{self.cert_secrets['internal']}/ca.crt",
                        "domains": cert_status.get("main", {}).get("domains", []),
                        "auto_reload": True
                    }
                }
                updates.append(config)
                
            elif container == "agent-orchestrator":
                # Configure agent orchestrator with internal certificates
                config = {
                    "container": container,
                    "certificate_config": {
                        "internal_tls_cert": f"/etc/ssl/internal/{self.cert_secrets['internal']}/tls.crt",
                        "internal_tls_key": f"/etc/ssl/internal/{self.cert_secrets['internal']}/tls.key",
                        "client_ca_cert": f"/etc/ssl/internal/{self.cert_secrets['internal']}/ca.crt",
                        "mutual_tls_enabled": True,
                        "verify_client_certs": True
                    }
                }
                updates.append(config)
                
            elif container == "admin-console":
                # Configure admin console with main certificate and enhanced security
                config = {
                    "container": container,
                    "certificate_config": {
                        "https_cert_path": f"/etc/ssl/certs/{self.cert_secrets['main']}/tls.crt",
                        "https_key_path": f"/etc/ssl/certs/{self.cert_secrets['main']}/tls.key", 
                        "hsts_enabled": True,
                        "ssl_protocols": ["TLSv1.2", "TLSv1.3"],
                        "ssl_ciphers": "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS"
                    }
                }
                updates.append(config)
                
            else:
                # Standard internal certificate configuration
                config = {
                    "container": container,
                    "certificate_config": {
                        "tls_cert_path": f"/etc/ssl/internal/{self.cert_secrets['internal']}/tls.crt",
                        "tls_key_path": f"/etc/ssl/internal/{self.cert_secrets['internal']}/tls.key",
                        "ca_cert_path": f"/etc/ssl/internal/{self.cert_secrets['internal']}/ca.crt"
                    }
                }
                updates.append(config)
        
        # Write configuration updates
        config_file = Path("certificate-integration-config.json")
        with open(config_file, 'w') as f:
            json.dump({
                "timestamp": datetime.utcnow().isoformat(),
                "certificate_updates": updates,
                "security_improvements": await self.generate_security_improvements()
            }, f, indent=2)
        
        logger.info(f"Configuration updates written to {config_file}")
        return updates
    
    async def generate_security_improvements(self) -> List[Dict]:
        """Generate list of security improvements from cert-manager integration"""
        return [
            {
                "improvement": "Automated Certificate Renewal",
                "description": "Certificates automatically renewed 15 days before expiration",
                "impact": "Eliminates manual certificate management and prevents outages",
                "security_level": "Critical"
            },
            {
                "improvement": "Let's Encrypt Integration", 
                "description": "Free, trusted certificates from Let's Encrypt CA",
                "impact": "Reduces certificate costs and ensures browser trust",
                "security_level": "High"
            },
            {
                "improvement": "Internal Service Encryption",
                "description": "Self-signed certificates for internal service communication",
                "impact": "Encrypts all inter-service communication within cluster",
                "security_level": "High"
            },
            {
                "improvement": "DNS Challenge Automation",
                "description": "Automated DNS-01 challenges for wildcard certificates",
                "impact": "Enables wildcard certs without exposing internal services",
                "security_level": "Medium"
            },
            {
                "improvement": "Certificate Monitoring",
                "description": "Prometheus metrics and alerts for certificate health",
                "impact": "Proactive notification of certificate issues",
                "security_level": "Medium"
            },
            {
                "improvement": "RBAC Security Controls",
                "description": "Minimal required permissions for certificate management",
                "impact": "Reduces attack surface and follows principle of least privilege",
                "security_level": "High"
            },
            {
                "improvement": "Network Policy Isolation",
                "description": "Restricted network access for cert-manager components",
                "impact": "Prevents unauthorized access to certificate operations",
                "security_level": "High"
            },
            {
                "improvement": "Non-Root Execution",
                "description": "All cert-manager components run as non-privileged users",
                "impact": "Reduces container escape attack vectors",
                "security_level": "Medium"
            }
        ]
    
    async def create_security_dashboard_integration(self):
        """Create integration points for existing security dashboard"""
        dashboard_config = {
            "certificate_panels": [
                {
                    "title": "Certificate Expiration Status",
                    "type": "stat",
                    "query": "(certmanager_certificate_expiration_timestamp_seconds - time()) / 86400",
                    "unit": "days",
                    "thresholds": [
                        {"color": "red", "value": 7},
                        {"color": "yellow", "value": 30},
                        {"color": "green", "value": 60}
                    ]
                },
                {
                    "title": "Certificate Readiness",
                    "type": "stat", 
                    "query": "certmanager_certificate_ready_status",
                    "unit": "bool",
                    "displayName": "Ready Certificates"
                },
                {
                    "title": "ACME Challenge Success Rate",
                    "type": "graph",
                    "query": "rate(certmanager_acme_client_request_count{status=~\"2..\"}[5m])",
                    "unit": "percent"
                },
                {
                    "title": "Certificate Renewal Events",
                    "type": "table",
                    "query": "increase(certmanager_certificate_renewal_count[24h])"
                }
            ],
            "alerts": [
                {
                    "name": "CertificateExpiringSoon",
                    "condition": "Certificate expires in < 30 days",
                    "severity": "warning",
                    "notification_channel": "guardian-security-alerts"
                },
                {
                    "name": "CertificateNotReady", 
                    "condition": "Certificate not ready",
                    "severity": "critical",
                    "notification_channel": "guardian-security-alerts"
                },
                {
                    "name": "CertManagerDown",
                    "condition": "Cert-manager controller unavailable",
                    "severity": "critical", 
                    "notification_channel": "guardian-security-alerts"
                }
            ]
        }
        
        # Write dashboard configuration
        dashboard_file = Path("certificate-dashboard-integration.json")
        with open(dashboard_file, 'w') as f:
            json.dump(dashboard_config, f, indent=2)
        
        logger.info(f"Dashboard integration config written to {dashboard_file}")
        return dashboard_config
    
    async def demonstrate_certificate_benefits(self):
        """Demonstrate the security benefits of the cert-manager integration"""
        logger.info("🛡️  GuardianShield Certificate Management Integration Benefits")
        logger.info("=" * 70)
        
        # Check current certificate status
        cert_status = await self.check_certificate_status()
        
        logger.info("\n📋 Current Certificate Status:")
        for cert_name, status in cert_status.items():
            if "error" not in status:
                ready_status = "✅ Ready" if status.get("ready") else "❌ Not Ready"
                domains = ", ".join(status.get("domains", [])[:3])  # Show first 3 domains
                logger.info(f"  {cert_name.title()}: {ready_status} | Domains: {domains}")
            else:
                logger.info(f"  {cert_name.title()}: ❌ Error - {status['error']}")
        
        # Update container configurations
        updates = await self.update_container_configurations(cert_status)
        logger.info(f"\n🔧 Updated {len(updates)} security container configurations")
        
        # Create dashboard integration
        await self.create_security_dashboard_integration()
        logger.info("📊 Created dashboard integration configuration")
        
        # Show security improvements
        improvements = await self.generate_security_improvements()
        logger.info(f"\n🚀 Security Improvements ({len(improvements)} total):")
        for improvement in improvements[:5]:  # Show top 5
            level_emoji = {"Critical": "🔴", "High": "🟠", "Medium": "🟡"}.get(improvement["security_level"], "⚪")
            logger.info(f"  {level_emoji} {improvement['improvement']}: {improvement['description']}")
        
        logger.info("\n💡 Integration Summary:")
        logger.info("  • Automated certificate lifecycle management")
        logger.info("  • Enhanced security for all container communications") 
        logger.info("  • Proactive monitoring and alerting")
        logger.info("  • Zero-downtime certificate renewals")
        logger.info("  • Cost reduction through Let's Encrypt automation")
        logger.info("  • Compliance with security best practices")
        
        logger.info("\n🎯 Next Steps:")
        logger.info("  1. Deploy the cert-manager chart: ./deploy-cert-manager.sh")
        logger.info("  2. Update container configurations with new certificate paths")
        logger.info("  3. Configure monitoring dashboard with certificate metrics")
        logger.info("  4. Test certificate renewal and container reloading")
        logger.info("  5. Verify all services are using HTTPS with valid certificates")

async def main():
    """Main integration demonstration"""
    integrator = CertificateSecurityIntegrator()
    await integrator.demonstrate_certificate_benefits()

if __name__ == "__main__":
    asyncio.run(main())