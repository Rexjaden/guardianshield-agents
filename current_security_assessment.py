#!/usr/bin/env python3
"""
Current Security Implementation Assessment
Check exactly what security measures are actually implemented
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

class SecurityImplementationChecker:
    def __init__(self):
        self.project_root = Path.cwd()
        self.security_assets = {}
        self.security_score = 0
        self.max_score = 0
        
    def check_docker_security_assets(self):
        """Check Docker security implementation"""
        print("🐳 Checking Docker Security Assets...")
        
        docker_assets = {
            'docker-compose.production.yml': 'Production orchestration with security services',
            'Dockerfile.api.production': 'Hardened API container',
            'Dockerfile.security.monitor': 'Security monitoring container',
            'Dockerfile.backup': 'Automated backup service',
            'Dockerfile.threat-intel': 'Threat intelligence collector',
            'nginx/nginx.conf': 'Reverse proxy with security headers',
            'nginx/security.conf': 'Security headers configuration',
            'database/postgresql.conf': 'Database security configuration'
        }
        
        implemented = {}
        for asset, description in docker_assets.items():
            asset_path = self.project_root / asset
            if asset_path.exists():
                implemented[asset] = {
                    'status': '✅ IMPLEMENTED',
                    'description': description,
                    'size': asset_path.stat().st_size
                }
                self.security_score += 1
            else:
                implemented[asset] = {
                    'status': '❌ MISSING',
                    'description': description,
                    'size': 0
                }
            
            self.max_score += 1
        
        self.security_assets['docker_security'] = implemented
        return implemented
    
    def check_environment_security(self):
        """Check environment and configuration security"""
        print("🔧 Checking Environment Security...")
        
        env_assets = {
            '.env.production.template': 'Production environment template',
            'deploy_production.py': 'Automated secure deployment script',
            'production_security_assessment.py': 'Security assessment tool',
            'achieve_perfect_security.py': '10/10 security implementation plan',
            'DOCKER_SECURITY_DEPLOYMENT.md': 'Security deployment guide'
        }
        
        implemented = {}
        for asset, description in env_assets.items():
            asset_path = self.project_root / asset
            if asset_path.exists():
                implemented[asset] = {
                    'status': '✅ IMPLEMENTED', 
                    'description': description,
                    'size': asset_path.stat().st_size
                }
                self.security_score += 1
            else:
                implemented[asset] = {
                    'status': '❌ MISSING',
                    'description': description,
                    'size': 0
                }
            
            self.max_score += 1
        
        self.security_assets['environment_security'] = implemented
        return implemented
    
    def check_api_security_implementation(self):
        """Check API security implementations"""
        print("🔌 Checking API Security Implementation...")
        
        api_security_files = [
            'api_server.py',
            'ip_protection_manager.py',
            'manage_ip_protection.py',
            'ssl_security_setup.py'
        ]
        
        implemented = {}
        for file in api_security_files:
            file_path = self.project_root / file
            if file_path.exists():
                # Check for security features in the file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                security_features = []
                if 'IPProtectionMiddleware' in content:
                    security_features.append('IP Protection')
                if 'rate_limit' in content.lower():
                    security_features.append('Rate Limiting')
                if 'ssl' in content.lower() or 'https' in content.lower():
                    security_features.append('SSL/HTTPS')
                if 'authentication' in content.lower():
                    security_features.append('Authentication')
                if 'cors' in content.lower():
                    security_features.append('CORS Protection')
                
                implemented[file] = {
                    'status': '✅ IMPLEMENTED',
                    'features': security_features,
                    'size': len(content)
                }
                self.security_score += len(security_features)
                self.max_score += 5  # Max possible features per file
            else:
                implemented[file] = {
                    'status': '❌ MISSING',
                    'features': [],
                    'size': 0
                }
                self.max_score += 5
        
        self.security_assets['api_security'] = implemented
        return implemented
    
    def check_advanced_security_assets(self):
        """Check for advanced security implementations"""
        print("🛡️ Checking Advanced Security Assets...")
        
        advanced_assets = {
            'docker-compose.siem.yml': 'SIEM system configuration',
            'docker-compose.zero-trust.yml': 'Zero trust architecture',
            'Dockerfile.advanced-auth': 'Advanced authentication (2FA)',
            'Dockerfile.disaster-recovery': 'Disaster recovery system',
            'cloudflare_waf_config.json': 'WAF configuration',
            'compliance_framework.json': 'Compliance framework',
            'security_documentation.json': 'Security documentation',
            '.github/workflows/security-testing.yml': 'Automated security testing'
        }
        
        implemented = {}
        for asset, description in advanced_assets.items():
            asset_path = self.project_root / asset
            if asset_path.exists():
                implemented[asset] = {
                    'status': '✅ IMPLEMENTED',
                    'description': description,
                    'size': asset_path.stat().st_size
                }
                self.security_score += 2  # Advanced features worth more
            else:
                implemented[asset] = {
                    'status': '⚠️ PLANNED',
                    'description': description,
                    'size': 0
                }
            
            self.max_score += 2
        
        self.security_assets['advanced_security'] = implemented
        return implemented
    
    def check_compliance_readiness(self):
        """Check compliance and legal readiness"""
        print("⚖️ Checking Compliance Readiness...")
        
        compliance_items = {
            'privacy_policy': 'Privacy policy for GDPR compliance',
            'terms_of_service': 'Terms of service',
            'security_policy': 'Information security policy',
            'incident_response_plan': 'Security incident response plan',
            'data_retention_policy': 'Data retention and deletion policy',
            'cookie_policy': 'Cookie consent and policy'
        }
        
        compliance_status = {}
        for item, description in compliance_items.items():
            # Check if compliance documentation exists
            compliance_files = list(self.project_root.glob(f"*{item}*"))
            if compliance_files:
                compliance_status[item] = {
                    'status': '✅ DOCUMENTED',
                    'description': description,
                    'files': [f.name for f in compliance_files]
                }
                self.security_score += 1
            else:
                compliance_status[item] = {
                    'status': '❌ MISSING',
                    'description': description,
                    'files': []
                }
            
            self.max_score += 1
        
        self.security_assets['compliance'] = compliance_status
        return compliance_status
    
    def calculate_security_maturity(self):
        """Calculate overall security maturity level"""
        if self.max_score == 0:
            return 0, "Not Assessed"
        
        percentage = (self.security_score / self.max_score) * 100
        
        if percentage >= 90:
            maturity = "Advanced (9-10/10)"
        elif percentage >= 80:
            maturity = "High (8/10)"
        elif percentage >= 70:
            maturity = "Medium (7/10)"
        elif percentage >= 60:
            maturity = "Basic (6/10)"
        elif percentage >= 50:
            maturity = "Developing (5/10)"
        else:
            maturity = "Initial (1-4/10)"
        
        return percentage, maturity
    
    def generate_security_report(self):
        """Generate comprehensive security implementation report"""
        print("\n" + "="*60)
        print("🛡️ GUARDIANSHIELD SECURITY IMPLEMENTATION REPORT")
        print("="*60)
        
        # Run all checks
        docker_assets = self.check_docker_security_assets()
        env_assets = self.check_environment_security()
        api_assets = self.check_api_security_implementation()
        advanced_assets = self.check_advanced_security_assets()
        compliance_assets = self.check_compliance_readiness()
        
        # Calculate maturity
        percentage, maturity = self.calculate_security_maturity()
        
        print(f"\n📊 OVERALL SECURITY SCORE: {self.security_score}/{self.max_score} ({percentage:.1f}%)")
        print(f"🎯 SECURITY MATURITY LEVEL: {maturity}")
        
        # Detailed breakdown
        print(f"\n📋 IMPLEMENTATION BREAKDOWN:")
        print(f"🐳 Docker Security Assets: {len([k for k,v in docker_assets.items() if v['status'] == '✅ IMPLEMENTED'])}/{len(docker_assets)}")
        print(f"🔧 Environment Security: {len([k for k,v in env_assets.items() if v['status'] == '✅ IMPLEMENTED'])}/{len(env_assets)}")
        print(f"🔌 API Security Features: {sum(len(v.get('features', [])) for v in api_assets.values())}")
        print(f"🛡️ Advanced Security: {len([k for k,v in advanced_assets.items() if v['status'] == '✅ IMPLEMENTED'])}/{len(advanced_assets)}")
        print(f"⚖️ Compliance Items: {len([k for k,v in compliance_assets.items() if v['status'] == '✅ DOCUMENTED'])}/{len(compliance_assets)}")
        
        # Show what's implemented
        print(f"\n✅ IMPLEMENTED SECURITY MEASURES:")
        for category, assets in self.security_assets.items():
            implemented_count = 0
            for asset_name, asset_info in assets.items():
                if asset_info['status'] == '✅ IMPLEMENTED' or asset_info['status'] == '✅ DOCUMENTED':
                    implemented_count += 1
            
            if implemented_count > 0:
                print(f"  {category}: {implemented_count} items")
                for asset_name, asset_info in assets.items():
                    if asset_info['status'] == '✅ IMPLEMENTED' or asset_info['status'] == '✅ DOCUMENTED':
                        description = asset_info.get('description', 'Security feature implemented')
                        print(f"    • {asset_name}: {description}")
        # Show what's missing for 10/10
        print(f"\n❌ MISSING FOR 10/10 SECURITY:")
        missing_items = []
        for category, assets in self.security_assets.items():
            for asset_name, asset_info in assets.items():
                if asset_info['status'] in ['❌ MISSING', '⚠️ PLANNED']:
                    description = asset_info.get('description', 'Security measure needed')
                    missing_items.append(f"{asset_name}: {description}")
        
        for item in missing_items[:10]:  # Show top 10 missing items
            print(f"  • {item}")
        
        if len(missing_items) > 10:
            print(f"  ... and {len(missing_items) - 10} more items")
        
        # Next steps
        print(f"\n🎯 NEXT STEPS TO IMPROVE SECURITY:")
        if percentage < 80:
            print("  1. 🚀 Run: python deploy_production.py")
            print("  2. 🛡️ Implement missing Docker security services")
            print("  3. 🔧 Configure SSL/HTTPS certificates")
            print("  4. 📊 Set up monitoring and alerting")
        else:
            print("  1. 🎯 Run: python achieve_perfect_security.py")
            print("  2. 🛡️ Implement advanced threat protection")
            print("  3. ⚖️ Complete compliance documentation")
            print("  4. 🧪 Set up automated security testing")
        
        # Save report
        report = {
            'timestamp': datetime.now().isoformat(),
            'security_score': self.security_score,
            'max_score': self.max_score,
            'percentage': percentage,
            'maturity_level': maturity,
            'assets': self.security_assets,
            'missing_items': missing_items
        }
        
        with open('security_implementation_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved: security_implementation_report.json")
        
        return report

if __name__ == "__main__":
    checker = SecurityImplementationChecker()
    report = checker.generate_security_report()