#!/usr/bin/env python3
"""
GuardianShield OpenSearch Dashboards Integration
Manages dashboard deployment, configuration, and monitoring.
"""

import os
import json
import yaml
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import subprocess
import requests
from kubernetes import client, config

class GuardianShieldDashboards:
    """Manages OpenSearch Dashboards for GuardianShield threat intelligence."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.charts_dir = self.project_root / "charts" / "opensearch-dashboards"
        self.namespace = "guardianshield-system"
        self.release_name = "guardianshield-dashboards"
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Load Kubernetes config
        try:
            config.load_incluster_config()
        except:
            try:
                config.load_kube_config()
            except:
                self.logger.warning("Kubernetes config not available - running in standalone mode")
    
    async def validate_chart(self) -> bool:
        """Validate the Helm chart configuration."""
        self.logger.info("Validating OpenSearch Dashboards chart...")
        
        try:
            # Check if required files exist
            required_files = [
                self.charts_dir / "Chart.yaml",
                self.charts_dir / "values.yaml",
                self.charts_dir / "templates" / "_helpers.tpl",
                self.charts_dir / "templates" / "configmap.yaml"
            ]
            
            for file_path in required_files:
                if not file_path.exists():
                    self.logger.error(f"Required file missing: {file_path}")
                    return False
            
            # Validate Chart.yaml
            with open(self.charts_dir / "Chart.yaml", 'r') as f:
                chart_data = yaml.safe_load(f)
            
            if not all(key in chart_data for key in ['name', 'version', 'appVersion']):
                self.logger.error("Chart.yaml missing required fields")
                return False
            
            # Validate values.yaml
            with open(self.charts_dir / "values.yaml", 'r') as f:
                values_data = yaml.safe_load(f)
            
            if not values_data.get('opensearch-dashboards', {}).get('enabled', False):
                self.logger.error("OpenSearch Dashboards not enabled in values")
                return False
            
            self.logger.info("Chart validation successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Chart validation failed: {str(e)}")
            return False
    
    async def deploy_dashboards(self, dry_run: bool = False) -> bool:
        """Deploy OpenSearch Dashboards using Helm."""
        self.logger.info("Deploying GuardianShield OpenSearch Dashboards...")
        
        try:
            # Prepare Helm command
            helm_cmd = [
                "helm", "upgrade", "--install",
                self.release_name,
                str(self.charts_dir),
                "--namespace", self.namespace,
                "--create-namespace"
            ]
            
            if dry_run:
                helm_cmd.extend(["--dry-run", "--debug"])
            
            # Add custom values
            custom_values = self._generate_runtime_values()
            values_file = self.charts_dir / "runtime-values.yaml"
            
            with open(values_file, 'w') as f:
                yaml.dump(custom_values, f, default_flow_style=False)
            
            helm_cmd.extend(["-f", str(values_file)])
            
            # Execute Helm command
            self.logger.info(f"Running: {' '.join(helm_cmd)}")
            result = subprocess.run(
                helm_cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            
            if result.returncode == 0:
                self.logger.info("Dashboards deployed successfully")
                if not dry_run:
                    await self._wait_for_deployment()
                return True
            else:
                self.logger.error(f"Deployment failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Deployment error: {str(e)}")
            return False
    
    def _generate_runtime_values(self) -> Dict[str, Any]:
        """Generate runtime values for the Helm chart."""
        return {
            "opensearch-dashboards": {
                "extraEnvs": [
                    {
                        "name": "OPENSEARCH_USERNAME",
                        "valueFrom": {
                            "secretKeyRef": {
                                "name": "opensearch-credentials",
                                "key": "username"
                            }
                        }
                    },
                    {
                        "name": "OPENSEARCH_PASSWORD",
                        "valueFrom": {
                            "secretKeyRef": {
                                "name": "opensearch-credentials",
                                "key": "password"
                            }
                        }
                    }
                ],
                "ingress": {
                    "hosts": [
                        {
                            "host": f"dashboards.{self._get_domain()}",
                            "paths": [{"path": "/", "pathType": "Prefix"}]
                        }
                    ],
                    "tls": [
                        {
                            "secretName": "guardianshield-dashboards-tls",
                            "hosts": [f"dashboards.{self._get_domain()}"]
                        }
                    ]
                }
            },
            "guardianshield": {
                "analytics": {
                    "threatIntel": {
                        "alerting": {
                            "webhookUrl": f"https://api.{self._get_domain()}/v1/alerts"
                        }
                    }
                }
            }
        }
    
    def _get_domain(self) -> str:
        """Get the domain for the GuardianShield deployment."""
        return os.getenv("GUARDIANSHIELD_DOMAIN", "guardianshield.local")
    
    async def _wait_for_deployment(self, timeout: int = 300):
        """Wait for the deployment to be ready."""
        self.logger.info("Waiting for dashboards to be ready...")
        
        try:
            v1 = client.AppsV1Api()
            
            for _ in range(timeout // 10):
                try:
                    deployment = v1.read_namespaced_deployment(
                        name=f"{self.release_name}-opensearch-dashboards",
                        namespace=self.namespace
                    )
                    
                    if (deployment.status.ready_replicas and 
                        deployment.status.ready_replicas == deployment.spec.replicas):
                        self.logger.info("Dashboards deployment is ready")
                        return
                        
                except client.exceptions.ApiException:
                    pass
                
                await asyncio.sleep(10)
            
            self.logger.warning("Deployment readiness check timed out")
            
        except Exception as e:
            self.logger.error(f"Error waiting for deployment: {str(e)}")
    
    async def configure_dashboards(self) -> bool:
        """Configure dashboards with GuardianShield-specific settings."""
        self.logger.info("Configuring GuardianShield dashboards...")
        
        try:
            # Dashboard configurations for threat intelligence
            dashboard_configs = {
                "threat-intelligence": {
                    "title": "GuardianShield Threat Intelligence",
                    "description": "Real-time threat monitoring and analytics",
                    "visualizations": [
                        "threat-timeline",
                        "attack-patterns",
                        "geographic-threats",
                        "severity-distribution"
                    ]
                },
                "web3-security": {
                    "title": "Web3 Security Monitor",
                    "description": "Blockchain and DeFi security monitoring",
                    "visualizations": [
                        "transaction-anomalies",
                        "smart-contract-risks",
                        "dmer-alerts",
                        "network-activity"
                    ]
                },
                "compliance": {
                    "title": "Compliance & Audit",
                    "description": "Regulatory compliance and audit trails",
                    "visualizations": [
                        "audit-events",
                        "compliance-status",
                        "policy-violations",
                        "access-logs"
                    ]
                }
            }
            
            # Save dashboard configurations
            config_dir = self.project_root / "dashboards" / "configs"
            config_dir.mkdir(parents=True, exist_ok=True)
            
            for name, config in dashboard_configs.items():
                config_file = config_dir / f"{name}-dashboard.json"
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)
            
            self.logger.info("Dashboard configurations saved")
            
            # Create index patterns
            await self._create_index_patterns()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Dashboard configuration failed: {str(e)}")
            return False
    
    async def _create_index_patterns(self):
        """Create index patterns for GuardianShield data."""
        index_patterns = [
            {
                "title": "guardianshield-threats-*",
                "timeFieldName": "@timestamp",
                "description": "GuardianShield threat intelligence data"
            },
            {
                "title": "guardianshield-web3-*", 
                "timeFieldName": "@timestamp",
                "description": "Web3 and blockchain security data"
            },
            {
                "title": "guardianshield-audit-*",
                "timeFieldName": "@timestamp", 
                "description": "Audit and compliance logs"
            }
        ]
        
        # Save index patterns for import
        patterns_dir = self.project_root / "dashboards" / "index-patterns"
        patterns_dir.mkdir(parents=True, exist_ok=True)
        
        for pattern in index_patterns:
            pattern_file = patterns_dir / f"{pattern['title'].replace('*', 'pattern')}.json"
            with open(pattern_file, 'w') as f:
                json.dump(pattern, f, indent=2)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the dashboards deployment."""
        self.logger.info("Performing health check...")
        
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "deployment_ready": False,
            "service_accessible": False,
            "dashboards_configured": False,
            "issues": []
        }
        
        try:
            # Check deployment status
            v1 = client.AppsV1Api()
            try:
                deployment = v1.read_namespaced_deployment(
                    name=f"{self.release_name}-opensearch-dashboards",
                    namespace=self.namespace
                )
                
                if (deployment.status.ready_replicas and 
                    deployment.status.ready_replicas == deployment.spec.replicas):
                    health_status["deployment_ready"] = True
                else:
                    health_status["issues"].append("Deployment not ready")
            except:
                health_status["issues"].append("Deployment not found")
            
            # Check service accessibility
            try:
                core_v1 = client.CoreV1Api()
                service = core_v1.read_namespaced_service(
                    name=f"{self.release_name}-opensearch-dashboards",
                    namespace=self.namespace
                )
                health_status["service_accessible"] = True
            except:
                health_status["issues"].append("Service not accessible")
            
            # Check dashboard configurations
            config_dir = self.project_root / "dashboards" / "configs"
            if config_dir.exists() and list(config_dir.glob("*.json")):
                health_status["dashboards_configured"] = True
            else:
                health_status["issues"].append("Dashboard configurations missing")
            
            self.logger.info(f"Health check completed: {len(health_status['issues'])} issues found")
            return health_status
            
        except Exception as e:
            health_status["issues"].append(f"Health check error: {str(e)}")
            return health_status
    
    async def cleanup(self) -> bool:
        """Clean up the dashboards deployment."""
        self.logger.info("Cleaning up dashboards deployment...")
        
        try:
            helm_cmd = [
                "helm", "uninstall",
                self.release_name,
                "--namespace", self.namespace
            ]
            
            result = subprocess.run(helm_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("Dashboards cleaned up successfully")
                return True
            else:
                self.logger.error(f"Cleanup failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}")
            return False


async def main():
    """Main function for dashboard management."""
    dashboards = GuardianShieldDashboards()
    
    # Validate chart
    if not await dashboards.validate_chart():
        print("❌ Chart validation failed")
        return
    
    print("✅ Chart validation successful")
    
    # Deploy dashboards
    if await dashboards.deploy_dashboards(dry_run=True):
        print("✅ Dry run deployment successful")
        
        # Ask for confirmation
        response = input("Deploy dashboards for real? (y/N): ")
        if response.lower() == 'y':
            if await dashboards.deploy_dashboards(dry_run=False):
                print("✅ Dashboards deployed successfully")
                
                # Configure dashboards
                if await dashboards.configure_dashboards():
                    print("✅ Dashboards configured successfully")
                    
                    # Health check
                    health = await dashboards.health_check()
                    print(f"📊 Health status: {health}")
    else:
        print("❌ Deployment failed")


if __name__ == "__main__":
    asyncio.run(main())