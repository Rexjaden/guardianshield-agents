#!/usr/bin/env python3
"""
GuardianShield Database & Web Services Deployment Manager
Deploys CloudNativePG PostgreSQL clusters and OpenResty web servers

This module handles the deployment and management of:
- PostgreSQL clusters with high availability and automated backups
- OpenResty web servers with advanced Lua scripting and threat intelligence
"""

import asyncio
import json
import subprocess
import yaml
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import psycopg2
from kubernetes import client, config as k8s_config
from kubernetes.client.rest import ApiException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deployment_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseWebServicesManager:
    """Manages deployment and monitoring of PostgreSQL databases and OpenResty web servers"""
    
    def __init__(self, namespace: str = "guardianshield"):
        self.namespace = namespace
        self.charts_dir = Path("charts")
        self.postgres_chart = self.charts_dir / "cloudnative-pg"
        self.openresty_chart = self.charts_dir / "openresty"
        
        # Initialize Kubernetes client
        try:
            k8s_config.load_incluster_config()
        except k8s_config.ConfigException:
            k8s_config.load_kube_config()
        
        self.k8s_client = client.ApiClient()
        self.apps_v1 = client.AppsV1Api()
        self.core_v1 = client.CoreV1Api()
        
        # Deployment status
        self.postgres_clusters = {}
        self.openresty_instances = {}
        
        logger.info(f"DatabaseWebServicesManager initialized for namespace: {namespace}")
    
    async def deploy_postgresql_cluster(
        self, 
        cluster_name: str = "guardianshield-postgres",
        values_override: Dict = None
    ) -> Dict:
        """Deploy PostgreSQL cluster using CloudNativePG"""
        try:
            logger.info(f"Starting PostgreSQL cluster deployment: {cluster_name}")
            
            # Prepare Helm values
            values = {
                'cluster': {
                    'name': cluster_name,
                    'instances': 3,
                    'description': f'GuardianShield PostgreSQL cluster - {cluster_name}'
                },
                'global': {
                    'projectName': 'GuardianShield',
                    'environment': 'production'
                },
                'storage': {
                    'size': '100Gi',
                    'storageClass': 'fast-ssd'
                },
                'backup': {
                    'enabled': True,
                    'schedule': '0 2 * * *',  # Daily at 2 AM
                    's3': {
                        'bucket': 'guardianshield-pg-backups',
                        'region': 'us-east-1'
                    }
                },
                'monitoring': {
                    'enabled': True
                }
            }
            
            # Apply overrides
            if values_override:
                self._deep_update(values, values_override)
            
            # Create values file
            values_file = self.postgres_chart / f"values-{cluster_name}.yaml"
            with open(values_file, 'w') as f:
                yaml.dump(values, f, default_flow_style=False)
            
            # Deploy using Helm
            helm_cmd = [
                'helm', 'upgrade', '--install',
                f'postgres-{cluster_name}',
                str(self.postgres_chart),
                '-n', self.namespace,
                '--create-namespace',
                '-f', str(values_file),
                '--wait',
                '--timeout', '600s'
            ]
            
            result = await self._run_command(helm_cmd)
            
            if result['success']:
                logger.info(f"PostgreSQL cluster {cluster_name} deployed successfully")
                
                # Wait for cluster to be ready
                await self._wait_for_postgres_ready(cluster_name)
                
                # Initialize databases and schemas
                await self._initialize_postgres_databases(cluster_name)
                
                self.postgres_clusters[cluster_name] = {
                    'status': 'running',
                    'deployed_at': datetime.utcnow().isoformat(),
                    'values': values
                }
                
                return {
                    'success': True,
                    'cluster_name': cluster_name,
                    'connection_info': await self._get_postgres_connection_info(cluster_name)
                }
            else:
                logger.error(f"Failed to deploy PostgreSQL cluster: {result['error']}")
                return {'success': False, 'error': result['error']}
                
        except Exception as e:
            logger.error(f"Error deploying PostgreSQL cluster {cluster_name}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def deploy_openresty_instance(
        self,
        instance_name: str = "guardianshield-web",
        values_override: Dict = None
    ) -> Dict:
        """Deploy OpenResty web server instance"""
        try:
            logger.info(f"Starting OpenResty deployment: {instance_name}")
            
            # Prepare Helm values
            values = {
                'replicaCount': 3,
                'image': {
                    'repository': 'openresty/openresty',
                    'tag': '1.25.3.1-alpine',
                    'pullPolicy': 'IfNotPresent'
                },
                'global': {
                    'projectName': 'GuardianShield',
                    'environment': 'production'
                },
                'service': {
                    'type': 'LoadBalancer',
                    'port': 80,
                    'httpsPort': 443
                },
                'ingress': {
                    'enabled': True,
                    'hosts': [
                        'api.guardianshield.io',
                        'admin.guardianshield.io',
                        'web.guardianshield.io'
                    ]
                },
                'ssl': {
                    'enabled': True
                },
                'security': {
                    'rateLimiting': {
                        'enabled': True,
                        'zones': {
                            'api_limit': {
                                'key': '$binary_remote_addr',
                                'size': '10m',
                                'rate': '10r/s'
                            }
                        }
                    },
                    'headers': {
                        'enabled': True,
                        'contentSecurityPolicy': "default-src 'self'; script-src 'self' 'unsafe-inline'"
                    }
                },
                'monitoring': {
                    'enabled': True
                }
            }
            
            # Apply overrides
            if values_override:
                self._deep_update(values, values_override)
            
            # Create values file
            values_file = self.openresty_chart / f"values-{instance_name}.yaml"
            with open(values_file, 'w') as f:
                yaml.dump(values, f, default_flow_style=False)
            
            # Deploy using Helm
            helm_cmd = [
                'helm', 'upgrade', '--install',
                f'openresty-{instance_name}',
                str(self.openresty_chart),
                '-n', self.namespace,
                '--create-namespace',
                '-f', str(values_file),
                '--wait',
                '--timeout', '300s'
            ]
            
            result = await self._run_command(helm_cmd)
            
            if result['success']:
                logger.info(f"OpenResty instance {instance_name} deployed successfully")
                
                # Wait for deployment to be ready
                await self._wait_for_openresty_ready(instance_name)
                
                # Perform health checks
                health_status = await self._check_openresty_health(instance_name)
                
                self.openresty_instances[instance_name] = {
                    'status': 'running',
                    'deployed_at': datetime.utcnow().isoformat(),
                    'values': values,
                    'health': health_status
                }
                
                return {
                    'success': True,
                    'instance_name': instance_name,
                    'endpoints': await self._get_openresty_endpoints(instance_name)
                }
            else:
                logger.error(f"Failed to deploy OpenResty instance: {result['error']}")
                return {'success': False, 'error': result['error']}
                
        except Exception as e:
            logger.error(f"Error deploying OpenResty instance {instance_name}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _wait_for_postgres_ready(self, cluster_name: str, timeout: int = 600):
        """Wait for PostgreSQL cluster to be ready"""
        logger.info(f"Waiting for PostgreSQL cluster {cluster_name} to be ready...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Check cluster status using kubectl
                cmd = [
                    'kubectl', 'get', 'cluster', cluster_name,
                    '-n', self.namespace,
                    '-o', 'jsonpath={.status.phase}'
                ]
                
                result = await self._run_command(cmd)
                if result['success'] and 'Cluster in healthy state' in result['output']:
                    logger.info(f"PostgreSQL cluster {cluster_name} is ready")
                    return True
                    
            except Exception as e:
                logger.debug(f"Postgres readiness check failed: {e}")
            
            await asyncio.sleep(10)
        
        raise TimeoutError(f"PostgreSQL cluster {cluster_name} did not become ready within {timeout} seconds")
    
    async def _wait_for_openresty_ready(self, instance_name: str, timeout: int = 300):
        """Wait for OpenResty deployment to be ready"""
        logger.info(f"Waiting for OpenResty instance {instance_name} to be ready...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                deployment_name = f"openresty-{instance_name}"
                deployment = self.apps_v1.read_namespaced_deployment(
                    name=deployment_name, 
                    namespace=self.namespace
                )
                
                if (deployment.status.ready_replicas and 
                    deployment.status.ready_replicas == deployment.spec.replicas):
                    logger.info(f"OpenResty instance {instance_name} is ready")
                    return True
                    
            except Exception as e:
                logger.debug(f"OpenResty readiness check failed: {e}")
            
            await asyncio.sleep(10)
        
        raise TimeoutError(f"OpenResty instance {instance_name} did not become ready within {timeout} seconds")
    
    async def _initialize_postgres_databases(self, cluster_name: str):
        """Initialize PostgreSQL databases with GuardianShield schema"""
        try:
            logger.info(f"Initializing databases for cluster {cluster_name}")
            
            # Get connection info
            conn_info = await self._get_postgres_connection_info(cluster_name)
            
            # Connect and create databases
            conn = psycopg2.connect(
                host=conn_info['host'],
                port=conn_info['port'],
                database='postgres',
                user=conn_info['user'],
                password=conn_info['password']
            )
            
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Create databases if they don't exist
            databases = [
                'threat_intelligence',
                'user_management', 
                'analytics',
                'blockchain_data',
                'agent_logs'
            ]
            
            for db in databases:
                cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db}'")
                if not cursor.fetchone():
                    cursor.execute(f"CREATE DATABASE {db}")
                    logger.info(f"Created database: {db}")
            
            cursor.close()
            conn.close()
            
            logger.info(f"Database initialization completed for cluster {cluster_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize databases: {str(e)}")
            raise
    
    async def _get_postgres_connection_info(self, cluster_name: str) -> Dict:
        """Get PostgreSQL connection information"""
        try:
            # Get service information
            service_name = f"{cluster_name}-rw"
            service = self.core_v1.read_namespaced_service(
                name=service_name,
                namespace=self.namespace
            )
            
            # Get credentials from secret
            secret_name = f"{cluster_name}-credentials"
            secret = self.core_v1.read_namespaced_secret(
                name=secret_name,
                namespace=self.namespace
            )
            
            import base64
            
            return {
                'host': f"{service_name}.{self.namespace}.svc.cluster.local",
                'port': 5432,
                'database': 'guardianshield',
                'user': base64.b64decode(secret.data['username']).decode(),
                'password': base64.b64decode(secret.data['password']).decode()
            }
            
        except Exception as e:
            logger.error(f"Failed to get connection info: {str(e)}")
            raise
    
    async def _check_openresty_health(self, instance_name: str) -> Dict:
        """Check OpenResty instance health"""
        try:
            # Get service endpoint
            service_name = f"openresty-{instance_name}"
            service = self.core_v1.read_namespaced_service(
                name=service_name,
                namespace=self.namespace
            )
            
            # Perform health check
            import aiohttp
            
            health_url = f"http://{service.spec.cluster_ip}/health"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(health_url, timeout=10) as response:
                    if response.status == 200:
                        return {
                            'status': 'healthy',
                            'response_time': response.headers.get('X-Response-Time', 'unknown'),
                            'checked_at': datetime.utcnow().isoformat()
                        }
                    else:
                        return {
                            'status': 'unhealthy',
                            'status_code': response.status,
                            'checked_at': datetime.utcnow().isoformat()
                        }
                        
        except Exception as e:
            logger.error(f"Health check failed for {instance_name}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'checked_at': datetime.utcnow().isoformat()
            }
    
    async def _get_openresty_endpoints(self, instance_name: str) -> List[str]:
        """Get OpenResty service endpoints"""
        try:
            service_name = f"openresty-{instance_name}"
            service = self.core_v1.read_namespaced_service(
                name=service_name,
                namespace=self.namespace
            )
            
            endpoints = []
            
            # Add cluster IP endpoint
            if service.spec.cluster_ip:
                endpoints.append(f"http://{service.spec.cluster_ip}")
            
            # Add load balancer endpoints
            if service.status.load_balancer and service.status.load_balancer.ingress:
                for ingress in service.status.load_balancer.ingress:
                    if ingress.ip:
                        endpoints.append(f"http://{ingress.ip}")
                    elif ingress.hostname:
                        endpoints.append(f"http://{ingress.hostname}")
            
            return endpoints
            
        except Exception as e:
            logger.error(f"Failed to get endpoints for {instance_name}: {str(e)}")
            return []
    
    async def get_deployment_status(self) -> Dict:
        """Get overall deployment status"""
        return {
            'namespace': self.namespace,
            'postgres_clusters': self.postgres_clusters,
            'openresty_instances': self.openresty_instances,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def scale_postgres_cluster(self, cluster_name: str, instances: int) -> bool:
        """Scale PostgreSQL cluster"""
        try:
            logger.info(f"Scaling PostgreSQL cluster {cluster_name} to {instances} instances")
            
            # Update cluster specification
            cmd = [
                'kubectl', 'patch', 'cluster', cluster_name,
                '-n', self.namespace,
                '--type', 'merge',
                '-p', f'{{"spec": {{"instances": {instances}}}}}'
            ]
            
            result = await self._run_command(cmd)
            
            if result['success']:
                logger.info(f"PostgreSQL cluster {cluster_name} scaled to {instances} instances")
                return True
            else:
                logger.error(f"Failed to scale cluster: {result['error']}")
                return False
                
        except Exception as e:
            logger.error(f"Error scaling cluster {cluster_name}: {str(e)}")
            return False
    
    async def scale_openresty_instance(self, instance_name: str, replicas: int) -> bool:
        """Scale OpenResty deployment"""
        try:
            logger.info(f"Scaling OpenResty instance {instance_name} to {replicas} replicas")
            
            deployment_name = f"openresty-{instance_name}"
            
            # Update deployment replica count
            self.apps_v1.patch_namespaced_deployment_scale(
                name=deployment_name,
                namespace=self.namespace,
                body={'spec': {'replicas': replicas}}
            )
            
            logger.info(f"OpenResty instance {instance_name} scaled to {replicas} replicas")
            return True
            
        except Exception as e:
            logger.error(f"Error scaling OpenResty instance {instance_name}: {str(e)}")
            return False
    
    async def _run_command(self, cmd: List[str]) -> Dict:
        """Run shell command asynchronously"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                'success': process.returncode == 0,
                'output': stdout.decode(),
                'error': stderr.decode(),
                'returncode': process.returncode
            }
            
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'returncode': -1
            }
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict):
        """Deep update dictionary"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value

async def main():
    """Main deployment orchestrator"""
    manager = DatabaseWebServicesManager()
    
    logger.info("Starting GuardianShield Database & Web Services deployment")
    
    # Deploy PostgreSQL cluster
    postgres_result = await manager.deploy_postgresql_cluster(
        cluster_name="guardianshield-main",
        values_override={
            'storage': {'size': '200Gi'},
            'cluster': {'instances': 3}
        }
    )
    
    if postgres_result['success']:
        logger.info("PostgreSQL cluster deployed successfully")
        logger.info(f"Connection info: {postgres_result['connection_info']}")
    else:
        logger.error(f"PostgreSQL deployment failed: {postgres_result['error']}")
        return
    
    # Deploy OpenResty web server
    openresty_result = await manager.deploy_openresty_instance(
        instance_name="guardianshield-api",
        values_override={
            'replicaCount': 5,
            'resources': {
                'requests': {'cpu': '500m', 'memory': '512Mi'},
                'limits': {'cpu': '1', 'memory': '1Gi'}
            }
        }
    )
    
    if openresty_result['success']:
        logger.info("OpenResty instance deployed successfully")
        logger.info(f"Endpoints: {openresty_result['endpoints']}")
    else:
        logger.error(f"OpenResty deployment failed: {openresty_result['error']}")
        return
    
    # Get deployment status
    status = await manager.get_deployment_status()
    logger.info("Deployment Status:")
    logger.info(json.dumps(status, indent=2))
    
    logger.info("GuardianShield Database & Web Services deployment completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())