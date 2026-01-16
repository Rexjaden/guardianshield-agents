#!/usr/bin/env python3
"""
GuardianShield Enterprise ArgoCD CLI Tool
Automated GitOps deployment with compliance and audit trails

Features:
- ERC-8055 application deployment
- Blockchain infrastructure management
- Website deployment automation
- Compliance monitoring and reporting
- Audit trail generation
- Security policy enforcement
"""

import subprocess
import json
import yaml
import datetime
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

# Configure logging for audit trail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('argocd-audit.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('GuardianShield-ArgoCD')

@dataclass
class DeploymentConfig:
    """Configuration for GuardianShield deployments"""
    name: str
    namespace: str
    repo_url: str
    path: str
    target_revision: str
    sync_policy: Dict
    compliance_level: str
    audit_required: bool

class GuardianShieldArgoCD:
    """Enterprise ArgoCD CLI for GuardianShield ecosystem"""
    
    def __init__(self):
        self.argocd_server = os.getenv('ARGOCD_SERVER', 'argocd-server.guardianshield.io')
        self.argocd_auth_token = os.getenv('ARGOCD_AUTH_TOKEN', '')
        self.compliance_mode = os.getenv('COMPLIANCE_MODE', 'STRICT')
        self.audit_log_file = 'guardianshield-deployment-audit.jsonl'
        
        # Deployment configurations
        self.deployments = {
            'erc8055-shield-token': DeploymentConfig(
                name='erc8055-shield-token',
                namespace='guardianshield-tokens',
                repo_url='https://github.com/Rexjaden/guardianshield-agents',
                path='charts/shield-token-chart',
                target_revision='main',
                sync_policy={'automated': {'prune': True, 'selfHeal': True}},
                compliance_level='CRITICAL',
                audit_required=True
            ),
            'blockchain-infrastructure': DeploymentConfig(
                name='blockchain-infrastructure',
                namespace='guardianshield-blockchain',
                repo_url='https://github.com/Rexjaden/guardianshield-agents',
                path='charts/blockchain-chart',
                target_revision='main',
                sync_policy={'automated': {'prune': False, 'selfHeal': True}},
                compliance_level='HIGH',
                audit_required=True
            ),
            'monitoring-stack': DeploymentConfig(
                name='monitoring-stack',
                namespace='guardianshield-monitoring',
                repo_url='https://github.com/Rexjaden/guardianshield-agents',
                path='charts/dhi-alertmanager-chart',
                target_revision='main',
                sync_policy={'automated': {'prune': True, 'selfHeal': True}},
                compliance_level='HIGH',
                audit_required=True
            ),
            'website-platform': DeploymentConfig(
                name='website-platform',
                namespace='guardianshield-web',
                repo_url='https://github.com/Rexjaden/guardianshield-agents',
                path='charts/website-chart',
                target_revision='main',
                sync_policy={'automated': {'prune': True, 'selfHeal': False}},
                compliance_level='MEDIUM',
                audit_required=False
            )
        }
    
    def log_audit_event(self, event_type: str, details: Dict):
        """Log deployment events for compliance audit trail"""
        audit_entry = {
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'event_type': event_type,
            'user': os.getenv('USER', 'system'),
            'compliance_mode': self.compliance_mode,
            'details': details
        }
        
        with open(self.audit_log_file, 'a') as f:
            f.write(json.dumps(audit_entry) + '\n')
        
        logger.info(f"Audit Event: {event_type} - {details.get('application', 'unknown')}")
    
    def run_argocd_command(self, cmd: List[str]) -> Dict:
        """Execute ArgoCD CLI command with error handling"""
        full_cmd = ['argocd'] + cmd + ['--server', self.argocd_server]
        
        if self.argocd_auth_token:
            full_cmd.extend(['--auth-token', self.argocd_auth_token])
        
        try:
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return {'success': True, 'output': result.stdout, 'error': None}
        except subprocess.CalledProcessError as e:
            return {'success': False, 'output': None, 'error': e.stderr}
    
    def compliance_check(self, deployment_config: DeploymentConfig) -> bool:
        """Perform compliance validation before deployment"""
        logger.info(f"Running compliance check for {deployment_config.name}")
        
        checks = {
            'repo_security': self._check_repo_security(deployment_config.repo_url),
            'namespace_policies': self._check_namespace_policies(deployment_config.namespace),
            'sync_policy_compliance': self._check_sync_policy(deployment_config.sync_policy),
            'audit_requirements': self._check_audit_requirements(deployment_config)
        }
        
        all_passed = all(checks.values())
        
        self.log_audit_event('COMPLIANCE_CHECK', {
            'application': deployment_config.name,
            'checks': checks,
            'result': 'PASSED' if all_passed else 'FAILED',
            'compliance_level': deployment_config.compliance_level
        })
        
        return all_passed
    
    def _check_repo_security(self, repo_url: str) -> bool:
        """Validate repository security settings"""
        # Check if repo is HTTPS and from approved organization
        approved_orgs = ['Rexjaden', 'guardianshield-org']
        return (repo_url.startswith('https://') and 
                any(org in repo_url for org in approved_orgs))
    
    def _check_namespace_policies(self, namespace: str) -> bool:
        """Validate namespace security policies"""
        # Check if namespace follows GuardianShield naming convention
        return namespace.startswith('guardianshield-')
    
    def _check_sync_policy(self, sync_policy: Dict) -> bool:
        """Validate sync policy compliance"""
        # Ensure automated sync is configured properly
        if 'automated' in sync_policy:
            return 'prune' in sync_policy['automated'] and 'selfHeal' in sync_policy['automated']
        return False
    
    def _check_audit_requirements(self, config: DeploymentConfig) -> bool:
        """Check if audit requirements are met"""
        if config.audit_required:
            return config.compliance_level in ['CRITICAL', 'HIGH']
        return True
    
    def create_application(self, deployment_name: str) -> bool:
        """Create ArgoCD application with compliance validation"""
        if deployment_name not in self.deployments:
            logger.error(f"Unknown deployment: {deployment_name}")
            return False
        
        config = self.deployments[deployment_name]
        
        # Compliance check
        if not self.compliance_check(config):
            logger.error(f"Compliance check failed for {deployment_name}")
            return False
        
        # Create application
        app_spec = {
            'apiVersion': 'argoproj.io/v1alpha1',
            'kind': 'Application',
            'metadata': {
                'name': config.name,
                'namespace': 'argocd',
                'labels': {
                    'app.kubernetes.io/managed-by': 'guardianshield-argocli',
                    'guardianshield.io/compliance-level': config.compliance_level.lower(),
                    'guardianshield.io/audit-required': str(config.audit_required).lower()
                }
            },
            'spec': {
                'project': 'guardianshield',
                'source': {
                    'repoURL': config.repo_url,
                    'path': config.path,
                    'targetRevision': config.target_revision
                },
                'destination': {
                    'server': 'https://kubernetes.default.svc',
                    'namespace': config.namespace
                },
                'syncPolicy': config.sync_policy
            }
        }
        
        # Write application spec to file
        app_file = f"applications/{config.name}.yaml"
        os.makedirs(os.path.dirname(app_file), exist_ok=True)
        with open(app_file, 'w') as f:
            yaml.dump(app_spec, f)
        
        # Apply application
        result = self.run_argocd_command(['app', 'create', '-f', app_file])
        
        if result['success']:
            self.log_audit_event('APPLICATION_CREATED', {
                'application': config.name,
                'namespace': config.namespace,
                'compliance_level': config.compliance_level,
                'result': 'SUCCESS'
            })
            logger.info(f"Successfully created application: {config.name}")
            return True
        else:
            self.log_audit_event('APPLICATION_CREATE_FAILED', {
                'application': config.name,
                'error': result['error'],
                'result': 'FAILED'
            })
            logger.error(f"Failed to create application {config.name}: {result['error']}")
            return False
    
    def sync_application(self, deployment_name: str, wait: bool = True) -> bool:
        """Sync application with compliance logging"""
        if deployment_name not in self.deployments:
            logger.error(f"Unknown deployment: {deployment_name}")
            return False
        
        config = self.deployments[deployment_name]
        
        sync_cmd = ['app', 'sync', config.name]
        if wait:
            sync_cmd.append('--wait')
        
        result = self.run_argocd_command(sync_cmd)
        
        if result['success']:
            self.log_audit_event('APPLICATION_SYNCED', {
                'application': config.name,
                'result': 'SUCCESS',
                'waited': wait
            })
            logger.info(f"Successfully synced application: {config.name}")
            return True
        else:
            self.log_audit_event('APPLICATION_SYNC_FAILED', {
                'application': config.name,
                'error': result['error'],
                'result': 'FAILED'
            })
            logger.error(f"Failed to sync application {config.name}: {result['error']}")
            return False
    
    def get_application_status(self, deployment_name: str) -> Optional[Dict]:
        """Get application health and sync status"""
        if deployment_name not in self.deployments:
            return None
        
        config = self.deployments[deployment_name]
        result = self.run_argocd_command(['app', 'get', config.name, '-o', 'json'])
        
        if result['success']:
            return json.loads(result['output'])
        return None
    
    def deploy_full_stack(self) -> bool:
        """Deploy entire GuardianShield stack with compliance"""
        logger.info("Starting full stack deployment with compliance validation")
        
        # Deployment order for dependencies
        deployment_order = [
            'monitoring-stack',
            'blockchain-infrastructure', 
            'erc8055-shield-token',
            'website-platform'
        ]
        
        success_count = 0
        for deployment in deployment_order:
            logger.info(f"Deploying {deployment}...")
            
            if self.create_application(deployment):
                if self.sync_application(deployment, wait=True):
                    success_count += 1
                    logger.info(f"✅ {deployment} deployed successfully")
                else:
                    logger.error(f"❌ Failed to sync {deployment}")
            else:
                logger.error(f"❌ Failed to create {deployment}")
        
        total_deployments = len(deployment_order)
        success_rate = (success_count / total_deployments) * 100
        
        self.log_audit_event('FULL_STACK_DEPLOYMENT', {
            'total_deployments': total_deployments,
            'successful_deployments': success_count,
            'success_rate': success_rate,
            'deployment_order': deployment_order,
            'result': 'SUCCESS' if success_count == total_deployments else 'PARTIAL_SUCCESS'
        })
        
        logger.info(f"Full stack deployment completed: {success_count}/{total_deployments} successful ({success_rate:.1f}%)")
        return success_count == total_deployments
    
    def generate_compliance_report(self) -> Dict:
        """Generate compliance report for audit purposes"""
        report = {
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'compliance_mode': self.compliance_mode,
            'applications': {},
            'summary': {
                'total_applications': len(self.deployments),
                'critical_applications': 0,
                'high_compliance_applications': 0,
                'audit_required_applications': 0
            }
        }
        
        for name, config in self.deployments.items():
            status = self.get_application_status(name)
            
            app_report = {
                'compliance_level': config.compliance_level,
                'audit_required': config.audit_required,
                'namespace': config.namespace,
                'sync_status': None,
                'health_status': None
            }
            
            if status:
                app_report['sync_status'] = status.get('status', {}).get('sync', {}).get('status')
                app_report['health_status'] = status.get('status', {}).get('health', {}).get('status')
            
            report['applications'][name] = app_report
            
            # Update summary
            if config.compliance_level == 'CRITICAL':
                report['summary']['critical_applications'] += 1
            elif config.compliance_level == 'HIGH':
                report['summary']['high_compliance_applications'] += 1
            
            if config.audit_required:
                report['summary']['audit_required_applications'] += 1
        
        # Save report
        report_file = f"compliance-report-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Compliance report generated: {report_file}")
        return report

def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GuardianShield Enterprise ArgoCD CLI')
    parser.add_argument('action', choices=[
        'create', 'sync', 'status', 'deploy-all', 'compliance-report'
    ], help='Action to perform')
    parser.add_argument('--app', help='Application name')
    parser.add_argument('--wait', action='store_true', help='Wait for sync completion')
    
    args = parser.parse_args()
    
    cli = GuardianShieldArgoCD()
    
    if args.action == 'create':
        if not args.app:
            print("Available applications:")
            for name in cli.deployments.keys():
                print(f"  - {name}")
        else:
            cli.create_application(args.app)
    
    elif args.action == 'sync':
        if args.app:
            cli.sync_application(args.app, wait=args.wait)
        else:
            print("Please specify --app")
    
    elif args.action == 'status':
        if args.app:
            status = cli.get_application_status(args.app)
            if status:
                print(json.dumps(status, indent=2))
        else:
            for name in cli.deployments.keys():
                status = cli.get_application_status(name)
                if status:
                    sync_status = status.get('status', {}).get('sync', {}).get('status', 'Unknown')
                    health_status = status.get('status', {}).get('health', {}).get('status', 'Unknown')
                    print(f"{name}: Sync={sync_status}, Health={health_status}")
    
    elif args.action == 'deploy-all':
        cli.deploy_full_stack()
    
    elif args.action == 'compliance-report':
        report = cli.generate_compliance_report()
        print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()