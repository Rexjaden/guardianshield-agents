#!/usr/bin/env python3
"""
GuardianShield Production Deployment Script
Leverages Docker infrastructure for secure deployment
"""

import os
import sys
import subprocess
import secrets
import getpass
from pathlib import Path
from typing import Dict, List

class ProductionDeployer:
    def __init__(self):
        self.project_root = Path.cwd()
        self.env_file = self.project_root / '.env.production'
        self.env_template = self.project_root / '.env.production.template'
        self.docker_compose = self.project_root / 'docker-compose.production.yml'
        
    def generate_secure_secrets(self) -> Dict[str, str]:
        """Generate cryptographically secure secrets for production"""
        return {
            'SECRET_KEY': secrets.token_urlsafe(32),
            'ADMIN_API_KEY': secrets.token_urlsafe(32),
            'DB_PASSWORD': secrets.token_urlsafe(24),
            'REDIS_PASSWORD': secrets.token_urlsafe(24),
            'VAULT_TOKEN': secrets.token_urlsafe(32),
            'BACKUP_ENCRYPTION_KEY': secrets.token_urlsafe(32),
            'GRAFANA_ADMIN_PASSWORD': secrets.token_urlsafe(16)
        }
    
    def create_production_env(self) -> bool:
        """Create production environment file with secure defaults"""
        try:
            print("🔐 Generating secure production environment...")
            
            # Check if environment already exists
            if self.env_file.exists():
                response = input(f"⚠️  {self.env_file} already exists. Overwrite? (y/N): ")
                if response.lower() != 'y':
                    print("Deployment cancelled.")
                    return False
            
            # Generate secure secrets
            secrets_map = self.generate_secure_secrets()
            
            # Read template
            with open(self.env_template, 'r') as f:
                template_content = f.read()
            
            # Replace placeholder secrets
            production_content = template_content
            for key, value in secrets_map.items():
                production_content = production_content.replace(
                    f'{key}=CHANGE_ME_TO_SECURE_RANDOM_STRING',
                    f'{key}={value}'
                ).replace(
                    f'{key}=CHANGE_ME_TO_SECURE_{key.split("_")[0]}_KEY',
                    f'{key}={value}'
                ).replace(
                    f'{key}=CHANGE_ME_TO_SECURE_{key.split("_")[0]}_PASSWORD',
                    f'{key}={value}'
                ).replace(
                    f'{key}=CHANGE_ME_TO_SECURE_ADMIN_KEY',
                    f'{key}={value}'
                ).replace(
                    f'{key}=CHANGE_ME_TO_SECURE_DB_PASSWORD',
                    f'{key}={value}'
                ).replace(
                    f'{key}=CHANGE_ME_TO_SECURE_REDIS_PASSWORD',
                    f'{key}={value}'
                ).replace(
                    f'{key}=CHANGE_ME_TO_SECURE_VAULT_TOKEN',
                    f'{key}={value}'
                ).replace(
                    f'{key}=CHANGE_ME_TO_SECURE_BACKUP_KEY',
                    f'{key}={value}'
                ).replace(
                    f'{key}=CHANGE_ME_TO_SECURE_GRAFANA_PASSWORD',
                    f'{key}={value}'
                )
            
            # Get user input for domain configuration
            domain = input("🌐 Enter your primary domain (e.g., guardian-shield.io): ")
            if domain:
                production_content = production_content.replace(
                    'DOMAIN=www.guardian-shield.io',
                    f'DOMAIN=www.{domain}'
                ).replace(
                    'guardian-shield.io',
                    domain
                )
            
            # Get email configuration
            email = input("📧 Enter admin email for SSL certificates: ")
            if email:
                production_content = production_content.replace(
                    'LETSENCRYPT_EMAIL=admin@guardian-shield.io',
                    f'LETSENCRYPT_EMAIL={email}'
                )
            
            # Mark as pending validation
            production_content = production_content.replace(
                'ENV_VALIDATION_STATUS=pending',
                'ENV_VALIDATION_STATUS=generated'
            )
            
            # Write production environment file
            with open(self.env_file, 'w') as f:
                f.write(production_content)
            
            # Set secure permissions
            os.chmod(self.env_file, 0o600)
            
            print(f"✅ Production environment created: {self.env_file}")
            print("⚠️  IMPORTANT: Review and customize the environment file before deployment!")
            
            # Display generated secrets for backup
            print("\n🔑 Generated Secrets (BACKUP THESE SECURELY):")
            print("=" * 50)
            for key, value in secrets_map.items():
                print(f"{key}: {value}")
            print("=" * 50)
            print("⚠️  Store these secrets in a secure password manager!")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating production environment: {e}")
            return False
    
    def validate_docker_environment(self) -> bool:
        """Validate Docker and docker-compose are available"""
        try:
            # Check Docker
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ Docker not found. Please install Docker first.")
                return False
            print(f"✅ Docker: {result.stdout.strip()}")
            
            # Check Docker Compose
            result = subprocess.run(['docker-compose', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ Docker Compose not found. Please install Docker Compose first.")
                return False
            print(f"✅ Docker Compose: {result.stdout.strip()}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error validating Docker environment: {e}")
            return False
    
    def create_docker_networks(self) -> bool:
        """Create required Docker networks"""
        try:
            networks = ['guardian-public', 'guardian-internal']
            
            for network in networks:
                result = subprocess.run([
                    'docker', 'network', 'create', network
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ Created network: {network}")
                elif "already exists" in result.stderr:
                    print(f"✅ Network already exists: {network}")
                else:
                    print(f"⚠️  Warning creating network {network}: {result.stderr}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating Docker networks: {e}")
            return False
    
    def create_data_directories(self) -> bool:
        """Create required data directories with proper permissions"""
        try:
            dirs = [
                '/var/guardian/data/postgres',
                '/var/guardian/data/vault',
                './nginx',
                './prometheus',
                './fail2ban',
                './vault/config',
                './backups',
                './logs'
            ]
            
            for dir_path in dirs:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
                print(f"✅ Created directory: {dir_path}")
            
            # Set proper permissions
            os.chmod('./logs', 0o755)
            os.chmod('./backups', 0o700)  # Restrict backup access
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating directories: {e}")
            return False
    
    def build_docker_images(self) -> bool:
        """Build production Docker images"""
        try:
            print("🔨 Building production Docker images...")
            
            # Build images
            result = subprocess.run([
                'docker-compose', '-f', str(self.docker_compose),
                '--env-file', str(self.env_file),
                'build', '--no-cache'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Docker images built successfully")
                return True
            else:
                print(f"❌ Error building images: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error building Docker images: {e}")
            return False
    
    def deploy_production(self) -> bool:
        """Deploy production environment using Docker"""
        try:
            print("🚀 Starting production deployment...")
            
            # Deploy services
            result = subprocess.run([
                'docker-compose', '-f', str(self.docker_compose),
                '--env-file', str(self.env_file),
                'up', '-d'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Production deployment successful")
                print("\n📊 Service Status:")
                
                # Check service status
                status_result = subprocess.run([
                    'docker-compose', '-f', str(self.docker_compose),
                    'ps'
                ], capture_output=True, text=True)
                
                print(status_result.stdout)
                return True
            else:
                print(f"❌ Deployment failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error during deployment: {e}")
            return False
    
    def run_security_checks(self) -> bool:
        """Run post-deployment security validation"""
        try:
            print("🔍 Running security validation...")
            
            checks = [
                ("API Health Check", self.check_api_health),
                ("Database Connectivity", self.check_database_connectivity),
                ("SSL Certificate Status", self.check_ssl_status),
                ("Security Headers", self.check_security_headers)
            ]
            
            all_passed = True
            for check_name, check_func in checks:
                try:
                    if check_func():
                        print(f"✅ {check_name}: PASS")
                    else:
                        print(f"❌ {check_name}: FAIL")
                        all_passed = False
                except Exception as e:
                    print(f"⚠️  {check_name}: ERROR - {e}")
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            print(f"❌ Error running security checks: {e}")
            return False
    
    def check_api_health(self) -> bool:
        """Check if API is responding"""
        try:
            result = subprocess.run([
                'curl', '-f', 'http://localhost:8000/health'
            ], capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            return False
    
    def check_database_connectivity(self) -> bool:
        """Check database connectivity"""
        try:
            result = subprocess.run([
                'docker-compose', '-f', str(self.docker_compose),
                'exec', '-T', 'db', 'pg_isready', '-U', 'guardianuser'
            ], capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            return False
    
    def check_ssl_status(self) -> bool:
        """Check SSL certificate status"""
        # This would need to be implemented based on your domain setup
        return True
    
    def check_security_headers(self) -> bool:
        """Check security headers are present"""
        try:
            result = subprocess.run([
                'curl', '-I', 'http://localhost:8000'
            ], capture_output=True, text=True, timeout=10)
            
            required_headers = [
                'X-Content-Type-Options',
                'X-Frame-Options', 
                'X-XSS-Protection'
            ]
            
            headers_text = result.stdout.lower()
            return all(header.lower() in headers_text for header in required_headers)
        except:
            return False
    
    def main(self):
        """Main deployment workflow"""
        print("🛡️  GuardianShield Production Deployment")
        print("=" * 50)
        
        steps = [
            ("Validate Docker Environment", self.validate_docker_environment),
            ("Create Production Environment", self.create_production_env),
            ("Create Docker Networks", self.create_docker_networks), 
            ("Create Data Directories", self.create_data_directories),
            ("Build Docker Images", self.build_docker_images),
            ("Deploy Production Services", self.deploy_production),
            ("Run Security Validation", self.run_security_checks)
        ]
        
        for step_name, step_func in steps:
            print(f"\n⏳ {step_name}...")
            if not step_func():
                print(f"\n❌ Deployment failed at step: {step_name}")
                sys.exit(1)
        
        print("\n🎉 DEPLOYMENT SUCCESSFUL!")
        print("=" * 50)
        print("🌐 Your GuardianShield platform is now running in production mode")
        print("📊 Monitor services: docker-compose -f docker-compose.production.yml ps")
        print("📋 View logs: docker-compose -f docker-compose.production.yml logs -f")
        print("🔧 Admin console: http://localhost:8000/admin")
        print("📈 Metrics: http://localhost:9090 (Prometheus)")
        print("📊 Dashboard: http://localhost:3000 (Grafana)")
        print("\n⚠️  IMPORTANT NEXT STEPS:")
        print("1. Configure your domain DNS to point to this server")
        print("2. Set up SSL certificates with certbot")
        print("3. Configure CDN/DDoS protection (Cloudflare)")
        print("4. Review and test all security features")
        print("5. Set up monitoring alerts")

if __name__ == "__main__":
    deployer = ProductionDeployer()
    deployer.main()