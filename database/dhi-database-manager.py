#!/usr/bin/env python3
"""
GuardianShield Enterprise Database Manager
Management tool for CloudNative PostgreSQL clusters with compliance and monitoring

Features:
- Database cluster lifecycle management
- Backup and recovery operations
- Performance monitoring and optimization
- Compliance reporting and audit trails
- ERC-8055 token database schema management
- Disaster recovery testing
"""

import subprocess
import json
import yaml
import datetime
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import psycopg2
import boto3
from kubernetes import client, config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database-manager.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('GuardianShield-DatabaseManager')

@dataclass
class DatabaseCluster:
    """Database cluster configuration"""
    name: str
    namespace: str
    instances: int
    database_name: str
    username: str
    storage_size: str
    backup_enabled: bool
    compliance_level: str

class GuardianShieldDatabaseManager:
    """Enterprise database management for GuardianShield ecosystem"""
    
    def __init__(self):
        self.namespace = os.getenv('DATABASE_NAMESPACE', 'guardianshield-database')
        self.backup_bucket = os.getenv('BACKUP_BUCKET', 'guardianshield-backups')
        self.aws_region = os.getenv('AWS_REGION', 'us-west-2')
        
        # Initialize Kubernetes client
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()
        
        self.k8s_client = client.ApiClient()
        self.k8s_apps = client.AppsV1Api()
        self.k8s_core = client.CoreV1Api()
        
        # Initialize AWS S3 client
        self.s3_client = boto3.client('s3', region_name=self.aws_region)
        
        # Database cluster configurations
        self.clusters = {
            'erc8055-tokens': DatabaseCluster(
                name='erc8055-tokens-cluster',
                namespace=self.namespace,
                instances=3,
                database_name='erc8055_tokens',
                username='guardian_tokens',
                storage_size='500Gi',
                backup_enabled=True,
                compliance_level='critical'
            ),
            'blockchain-data': DatabaseCluster(
                name='blockchain-data-cluster',
                namespace=self.namespace,
                instances=3,
                database_name='blockchain_data',
                username='blockchain_indexer',
                storage_size='2Ti',
                backup_enabled=True,
                compliance_level='high'
            ),
            'analytics': DatabaseCluster(
                name='analytics-cluster',
                namespace=self.namespace,
                instances=2,
                database_name='guardianshield_analytics',
                username='analytics_user',
                storage_size='1Ti',
                backup_enabled=True,
                compliance_level='medium'
            )
        }
    
    def run_kubectl_command(self, cmd: List[str]) -> Tuple[bool, str]:
        """Execute kubectl command with error handling"""
        try:
            result = subprocess.run(
                ['kubectl'] + cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr
    
    def get_cluster_status(self, cluster_name: str) -> Optional[Dict]:
        """Get detailed cluster status"""
        success, output = self.run_kubectl_command([
            'get', 'cluster', cluster_name,
            '-n', self.namespace,
            '-o', 'json'
        ])
        
        if success:
            return json.loads(output)
        else:
            logger.error(f"Failed to get cluster status for {cluster_name}: {output}")
            return None
    
    def get_cluster_health(self, cluster_name: str) -> Dict:
        """Get comprehensive cluster health information"""
        health_info = {
            'cluster_name': cluster_name,
            'overall_status': 'unknown',
            'instances': [],
            'backup_status': 'unknown',
            'replication_status': 'unknown',
            'performance_metrics': {}
        }
        
        # Get cluster status
        cluster_status = self.get_cluster_status(cluster_name)
        if cluster_status:
            health_info['overall_status'] = cluster_status.get('status', {}).get('phase', 'unknown')
            health_info['instances'] = cluster_status.get('status', {}).get('instances', [])
        
        # Get pod status
        success, output = self.run_kubectl_command([
            'get', 'pods',
            '-n', self.namespace,
            '-l', f'cnpg.io/cluster={cluster_name}',
            '-o', 'json'
        ])
        
        if success:
            pods = json.loads(output)
            health_info['pod_count'] = len(pods.get('items', []))
            health_info['ready_pods'] = sum(
                1 for pod in pods.get('items', [])
                if pod.get('status', {}).get('phase') == 'Running'
            )
        
        return health_info
    
    def connect_to_database(self, cluster_name: str, database: str = None) -> Optional[psycopg2.extensions.connection]:
        """Create database connection using port-forwarding"""
        cluster_config = None
        for name, config in self.clusters.items():
            if config.name == cluster_name:
                cluster_config = config
                break
        
        if not cluster_config:
            logger.error(f"Unknown cluster: {cluster_name}")
            return None
        
        try:
            # Get database password from secret
            success, output = self.run_kubectl_command([
                'get', 'secret', f'{name}-credentials',
                '-n', self.namespace,
                '-o', 'jsonpath={.data.password}'
            ])
            
            if not success:
                logger.error(f"Failed to get database password: {output}")
                return None
            
            # Decode base64 password
            import base64
            password = base64.b64decode(output).decode('utf-8')
            
            # Use port-forwarding for connection (simplified for demo)
            conn = psycopg2.connect(
                host='localhost',  # Assumes port-forward is active
                port=5432,
                database=database or cluster_config.database_name,
                user=cluster_config.username,
                password=password
            )
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return None
    
    def run_sql_query(self, cluster_name: str, query: str, database: str = None) -> Optional[List]:
        """Execute SQL query on specified cluster"""
        conn = self.connect_to_database(cluster_name, database)
        if not conn:
            return None
        
        try:
            with conn.cursor() as cursor:
                cursor.execute(query)
                if cursor.description:
                    return cursor.fetchall()
                else:
                    conn.commit()
                    return []
        except Exception as e:
            logger.error(f"SQL query failed: {e}")
            return None
        finally:
            conn.close()
    
    def get_erc8055_token_statistics(self) -> Dict:
        """Get ERC-8055 token database statistics"""
        queries = {
            'total_shield_tokens': "SELECT COUNT(*) FROM shield_tokens;",
            'active_tokens': "SELECT COUNT(*) FROM shield_tokens WHERE status = 'active';",
            'burned_tokens': "SELECT COUNT(*) FROM shield_tokens WHERE status = 'burned';",
            'reminted_tokens': "SELECT COUNT(*) FROM shield_tokens WHERE status = 'reminted';",
            'recent_burns': """SELECT COUNT(*) FROM shield_tokens 
                               WHERE burn_timestamp > NOW() - INTERVAL '24 hours';""",
            'recent_guard_transfers': """SELECT COUNT(*), SUM(amount) FROM guard_token_transfers 
                                          WHERE timestamp > NOW() - INTERVAL '1 hour';""",
            'fraud_detections': "SELECT COUNT(*) FROM fraud_detection_logs WHERE created_at > NOW() - INTERVAL '24 hours';"
        }
        
        stats = {}
        for stat_name, query in queries.items():
            result = self.run_sql_query('erc8055-tokens-cluster', query)
            if result:
                stats[stat_name] = result[0][0] if len(result[0]) == 1 else result[0]
            else:
                stats[stat_name] = 'error'
        
        return stats
    
    def create_backup(self, cluster_name: str, backup_type: str = 'full') -> bool:
        """Create manual backup for specified cluster"""
        logger.info(f"Creating {backup_type} backup for {cluster_name}...")
        
        # Create backup job
        backup_job_name = f"manual-backup-{cluster_name}-{int(time.time())}"
        
        success, output = self.run_kubectl_command([
            'create', 'job', backup_job_name,
            '--from=cronjob/backup-validation',
            '-n', self.namespace
        ])
        
        if not success:
            logger.error(f"Failed to create backup job: {output}")
            return False
        
        # Wait for job completion
        logger.info(f"Waiting for backup job {backup_job_name} to complete...")
        success, output = self.run_kubectl_command([
            'wait', '--for=condition=complete',
            f'job/{backup_job_name}',
            '-n', self.namespace,
            '--timeout=600s'
        ])
        
        if success:
            logger.info(f"Backup completed successfully: {backup_job_name}")
            return True
        else:
            logger.error(f"Backup failed: {output}")
            return False
    
    def list_backups(self, cluster_name: str) -> List[Dict]:
        """List available backups for cluster"""
        backups = []
        
        try:
            # List S3 objects in backup path
            cluster_path = f"{cluster_name.replace('-cluster', '')}/"
            response = self.s3_client.list_objects_v2(
                Bucket=self.backup_bucket,
                Prefix=cluster_path
            )
            
            for obj in response.get('Contents', []):
                backups.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'storage_class': obj.get('StorageClass', 'STANDARD')
                })
        
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
        
        return backups
    
    def test_disaster_recovery(self, cluster_name: str) -> bool:
        """Test disaster recovery for specified cluster"""
        logger.info(f"Starting disaster recovery test for {cluster_name}...")
        
        # Create test namespace
        test_namespace = 'guardianshield-dr-test'
        success, output = self.run_kubectl_command([
            'create', 'namespace', test_namespace
        ])
        
        if not success and 'already exists' not in output:
            logger.error(f"Failed to create test namespace: {output}")
            return False
        
        try:
            # Create recovery cluster configuration
            recovery_config = {
                'apiVersion': 'postgresql.cnpg.io/v1',
                'kind': 'Cluster',
                'metadata': {
                    'name': f'{cluster_name}-dr-test',
                    'namespace': test_namespace
                },
                'spec': {
                    'instances': 1,
                    'storage': {
                        'size': '100Gi',
                        'storageClass': 'standard-ssd'
                    },
                    'bootstrap': {
                        'recovery': {
                            'backup': {'name': 'latest'},
                            'source': cluster_name
                        }
                    },
                    'externalClusters': [{
                        'name': cluster_name,
                        'barmanObjectStore': {
                            'destinationPath': f's3://{self.backup_bucket}/{cluster_name.replace("-cluster", "")}',
                            'endpointURL': 'https://s3.amazonaws.com',
                            's3Credentials': {
                                'accessKeyId': {
                                    'name': 's3-backup-credentials',
                                    'key': 'ACCESS_KEY_ID'
                                },
                                'secretAccessKey': {
                                    'name': 's3-backup-credentials',
                                    'key': 'SECRET_ACCESS_KEY'
                                }
                            }
                        }
                    }]
                }
            }
            
            # Apply recovery cluster
            with open(f'/tmp/{cluster_name}-dr-test.yaml', 'w') as f:
                yaml.dump(recovery_config, f)
            
            success, output = self.run_kubectl_command([
                'apply', '-f', f'/tmp/{cluster_name}-dr-test.yaml'
            ])
            
            if not success:
                logger.error(f"Failed to create recovery cluster: {output}")
                return False
            
            # Wait for cluster to be ready
            logger.info("Waiting for recovery cluster to be ready...")
            success, output = self.run_kubectl_command([
                'wait', '--for=condition=ready',
                f'cluster/{cluster_name}-dr-test',
                '-n', test_namespace,
                '--timeout=600s'
            ])
            
            if success:
                logger.info("Disaster recovery test completed successfully")
                return True
            else:
                logger.error(f"Recovery cluster failed to become ready: {output}")
                return False
        
        finally:
            # Cleanup test resources
            logger.info("Cleaning up disaster recovery test resources...")
            self.run_kubectl_command(['delete', 'namespace', test_namespace])
            try:
                os.remove(f'/tmp/{cluster_name}-dr-test.yaml')
            except:
                pass
    
    def generate_compliance_report(self) -> Dict:
        """Generate comprehensive compliance report"""
        report = {
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'clusters': {},
            'backup_compliance': {},
            'security_compliance': {},
            'performance_metrics': {}
        }
        
        # Cluster health and compliance
        for cluster_key, cluster_config in self.clusters.items():
            cluster_health = self.get_cluster_health(cluster_config.name)
            report['clusters'][cluster_key] = {
                'name': cluster_config.name,
                'compliance_level': cluster_config.compliance_level,
                'health': cluster_health,
                'backup_enabled': cluster_config.backup_enabled
            }
        
        # Backup compliance
        for cluster_key, cluster_config in self.clusters.items():
            backups = self.list_backups(cluster_config.name)
            report['backup_compliance'][cluster_key] = {
                'total_backups': len(backups),
                'latest_backup': max(backups, key=lambda x: x['last_modified'])['last_modified'] if backups else None,
                'retention_compliant': len([b for b in backups if 
                    (datetime.datetime.now() - datetime.datetime.fromisoformat(b['last_modified'].replace('Z', '+00:00'))).days < 30
                ]) > 0
            }
        
        # ERC-8055 specific metrics
        if 'erc8055-tokens' in self.clusters:
            report['erc8055_metrics'] = self.get_erc8055_token_statistics()
        
        return report

def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GuardianShield Enterprise Database Manager')
    parser.add_argument('action', choices=[
        'status', 'health', 'backup', 'list-backups', 'dr-test', 'compliance-report', 'erc8055-stats'
    ], help='Action to perform')
    parser.add_argument('--cluster', help='Cluster name (erc8055-tokens, blockchain-data, analytics)')
    parser.add_argument('--format', choices=['json', 'table'], default='table', help='Output format')
    
    args = parser.parse_args()
    
    manager = GuardianShieldDatabaseManager()
    
    if args.action == 'status':
        if args.cluster:
            cluster_config = manager.clusters.get(args.cluster)
            if cluster_config:
                status = manager.get_cluster_status(cluster_config.name)
                if args.format == 'json':
                    print(json.dumps(status, indent=2))
                else:
                    print(f"Cluster: {cluster_config.name}")
                    print(f"Status: {status.get('status', {}).get('phase', 'Unknown') if status else 'Error'}")
            else:
                print(f"Unknown cluster: {args.cluster}")
        else:
            for cluster_key, cluster_config in manager.clusters.items():
                status = manager.get_cluster_status(cluster_config.name)
                phase = status.get('status', {}).get('phase', 'Unknown') if status else 'Error'
                print(f"{cluster_key}: {phase}")
    
    elif args.action == 'health':
        if args.cluster:
            cluster_config = manager.clusters.get(args.cluster)
            if cluster_config:
                health = manager.get_cluster_health(cluster_config.name)
                if args.format == 'json':
                    print(json.dumps(health, indent=2))
                else:
                    print(f"Cluster Health: {cluster_config.name}")
                    print(f"Overall Status: {health['overall_status']}")
                    print(f"Pod Count: {health.get('pod_count', 'Unknown')}")
                    print(f"Ready Pods: {health.get('ready_pods', 'Unknown')}")
        else:
            for cluster_key, cluster_config in manager.clusters.items():
                health = manager.get_cluster_health(cluster_config.name)
                print(f"{cluster_key}: {health['overall_status']} ({health.get('ready_pods', 0)}/{health.get('pod_count', 0)} ready)")
    
    elif args.action == 'backup':
        if not args.cluster:
            print("--cluster required for backup operation")
            return
        
        cluster_config = manager.clusters.get(args.cluster)
        if cluster_config:
            success = manager.create_backup(cluster_config.name)
            print(f"Backup {'successful' if success else 'failed'}")
    
    elif args.action == 'list-backups':
        if not args.cluster:
            print("--cluster required for list-backups operation")
            return
        
        cluster_config = manager.clusters.get(args.cluster)
        if cluster_config:
            backups = manager.list_backups(cluster_config.name)
            if args.format == 'json':
                print(json.dumps(backups, indent=2))
            else:
                print(f"Backups for {cluster_config.name}:")
                for backup in backups:
                    print(f"  {backup['key']} ({backup['size']} bytes, {backup['last_modified']})")
    
    elif args.action == 'dr-test':
        if not args.cluster:
            print("--cluster required for disaster recovery test")
            return
        
        cluster_config = manager.clusters.get(args.cluster)
        if cluster_config:
            success = manager.test_disaster_recovery(cluster_config.name)
            print(f"Disaster recovery test {'passed' if success else 'failed'}")
    
    elif args.action == 'compliance-report':
        report = manager.generate_compliance_report()
        if args.format == 'json':
            print(json.dumps(report, indent=2))
        else:
            print("GuardianShield Database Compliance Report")
            print(f"Generated: {report['timestamp']}")
            print("\nCluster Status:")
            for cluster_key, cluster_info in report['clusters'].items():
                print(f"  {cluster_key}: {cluster_info['health']['overall_status']} (Level: {cluster_info['compliance_level']})")
    
    elif args.action == 'erc8055-stats':
        stats = manager.get_erc8055_token_statistics()
        if args.format == 'json':
            print(json.dumps(stats, indent=2))
        else:
            print("ERC-8055 Token Statistics:")
            for stat_name, value in stats.items():
                print(f"  {stat_name.replace('_', ' ').title()}: {value}")

if __name__ == '__main__':
    main()