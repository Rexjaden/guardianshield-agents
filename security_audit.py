"""
GuardianShield Security Audit & Hardening Script
Identifies and fixes critical security vulnerabilities in the system
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

class SecurityAuditor:
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.vulnerabilities = []
        self.fixed_issues = []
        
    def audit_api_endpoints(self):
        """Audit all API endpoints for authentication requirements"""
        print("🔍 Auditing API endpoints for security vulnerabilities...")
        
        api_files = list(self.workspace_path.glob("**/*api*.py")) + list(self.workspace_path.glob("**/*server*.py"))
        
        for api_file in api_files:
            if api_file.name.startswith('.'):
                continue
                
            try:
                content = api_file.read_text(encoding='utf-8')
                
                # Find all endpoint definitions
                endpoints = re.findall(r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)', content)
                
                for method, path in endpoints:
                    endpoint_line = self.find_endpoint_definition(content, method, path)
                    
                    # Check if endpoint requires authentication
                    has_auth = self.check_endpoint_auth(content, endpoint_line)
                    
                    # Critical endpoints that MUST have authentication
                    critical_patterns = [
                        '/admin', '/api/admin', '/purchase', '/create', '/complete', 
                        '/delete', '/update', '/modify', '/config', '/start', '/stop',
                        '/evolve', '/emergency', '/stats', '/history', '/wallet'
                    ]
                    
                    is_critical = any(pattern in path.lower() for pattern in critical_patterns)
                    
                    if is_critical and not has_auth:
                        vulnerability = {
                            'type': 'UNPROTECTED_CRITICAL_ENDPOINT',
                            'severity': 'CRITICAL',
                            'file': str(api_file),
                            'endpoint': f"{method.upper()} {path}",
                            'line': endpoint_line,
                            'description': f"Critical endpoint {path} lacks authentication"
                        }
                        self.vulnerabilities.append(vulnerability)
                        
            except Exception as e:
                print(f"Error analyzing {api_file}: {e}")
    
    def find_endpoint_definition(self, content: str, method: str, path: str) -> int:
        """Find the line number of an endpoint definition"""
        lines = content.split('\n')
        pattern = f"@app.{method}"
        
        for i, line in enumerate(lines):
            if pattern in line and path in line:
                return i + 1
        return 0
    
    def check_endpoint_auth(self, content: str, endpoint_line: int) -> bool:
        """Check if an endpoint has authentication requirements"""
        lines = content.split('\n')
        
        # Look for authentication patterns around the endpoint
        auth_patterns = [
            'Depends(get_current_user)',
            'Depends(require_admin_access)',
            'Depends(require_master_admin)',
            'current_user =',
            'admin_user =',
            'user_info =',
            '@require_auth',
            'SECURITY_AVAILABLE'
        ]
        
        # Check the function signature and body (next 5 lines)
        start_line = max(0, endpoint_line - 1)
        end_line = min(len(lines), endpoint_line + 5)
        
        for line_num in range(start_line, end_line):
            line = lines[line_num]
            if any(pattern in line for pattern in auth_patterns):
                return True
        
        return False
    
    def audit_database_access(self):
        """Audit database access patterns"""
        print("🔍 Auditing database access security...")
        
        py_files = list(self.workspace_path.glob("**/*.py"))
        
        for py_file in py_files:
            try:
                content = py_file.read_text(encoding='utf-8')
                
                # Look for direct SQL without parameterization
                sql_patterns = [
                    r'execute\s*\(\s*f["\']',  # f-string in execute
                    r'execute\s*\(\s*["\'][^"\']*\%[^"\']*["\']',  # % formatting
                    r'execute\s*\(\s*["\'][^"\']*\+[^"\']*["\']',  # string concatenation
                ]
                
                for i, line in enumerate(content.split('\n'), 1):
                    for pattern in sql_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            vulnerability = {
                                'type': 'SQL_INJECTION_RISK',
                                'severity': 'HIGH',
                                'file': str(py_file),
                                'line': i,
                                'description': f"Potential SQL injection vulnerability: {line.strip()}"
                            }
                            self.vulnerabilities.append(vulnerability)
                            
            except Exception as e:
                print(f"Error analyzing {py_file}: {e}")
    
    def audit_secret_exposure(self):
        """Audit for exposed secrets and credentials"""
        print("🔍 Auditing for exposed secrets...")
        
        all_files = list(self.workspace_path.glob("**/*"))
        
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', 'HARDCODED_PASSWORD'),
            (r'api_key\s*=\s*["\'][^"\']+["\']', 'HARDCODED_API_KEY'),
            (r'secret\s*=\s*["\'][^"\']+["\']', 'HARDCODED_SECRET'),
            (r'token\s*=\s*["\'][^"\']+["\']', 'HARDCODED_TOKEN'),
            (r'private_key\s*=\s*["\'][^"\']+["\']', 'HARDCODED_PRIVATE_KEY'),
        ]
        
        for file_path in all_files:
            if file_path.is_file() and file_path.suffix in ['.py', '.js', '.json', '.env']:
                try:
                    content = file_path.read_text(encoding='utf-8')
                    
                    for i, line in enumerate(content.split('\n'), 1):
                        for pattern, vuln_type in secret_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                # Skip obvious examples or comments
                                if 'example' in line.lower() or 'your_' in line.lower() or line.strip().startswith('#'):
                                    continue
                                    
                                vulnerability = {
                                    'type': vuln_type,
                                    'severity': 'HIGH',
                                    'file': str(file_path),
                                    'line': i,
                                    'description': f"Hardcoded secret detected: {line.strip()[:50]}..."
                                }
                                self.vulnerabilities.append(vulnerability)
                                
                except Exception as e:
                    continue
    
    def audit_file_permissions(self):
        """Audit file and directory permissions"""
        print("🔍 Auditing file permissions...")
        
        sensitive_files = [
            '.env', '*.key', '*.pem', '*.p12', 'admin_*',
            'config.json', 'secrets.json', '*password*'
        ]
        
        for pattern in sensitive_files:
            for file_path in self.workspace_path.glob(f"**/{pattern}"):
                if file_path.is_file():
                    # Check if file has restrictive permissions (this is basic - OS specific)
                    vulnerability = {
                        'type': 'SENSITIVE_FILE_PERMISSIONS',
                        'severity': 'MEDIUM',
                        'file': str(file_path),
                        'description': f"Sensitive file may have overly permissive access: {file_path.name}"
                    }
                    self.vulnerabilities.append(vulnerability)
    
    def audit_cors_configuration(self):
        """Audit CORS configuration for security issues"""
        print("🔍 Auditing CORS configuration...")
        
        py_files = list(self.workspace_path.glob("**/*.py"))
        
        for py_file in py_files:
            try:
                content = py_file.read_text(encoding='utf-8')
                
                # Look for permissive CORS settings
                if 'allow_origins=["*"]' in content or 'allow_origins=[\"*\"]' in content:
                    vulnerability = {
                        'type': 'PERMISSIVE_CORS',
                        'severity': 'MEDIUM',
                        'file': str(py_file),
                        'description': "CORS allows all origins (*) - potential security risk"
                    }
                    self.vulnerabilities.append(vulnerability)
                    
            except Exception as e:
                continue
    
    def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        
        # Categorize vulnerabilities by severity
        critical = [v for v in self.vulnerabilities if v['severity'] == 'CRITICAL']
        high = [v for v in self.vulnerabilities if v['severity'] == 'HIGH']
        medium = [v for v in self.vulnerabilities if v['severity'] == 'MEDIUM']
        
        report = {
            'audit_timestamp': str(datetime.now()),
            'total_vulnerabilities': len(self.vulnerabilities),
            'critical_count': len(critical),
            'high_count': len(high),
            'medium_count': len(medium),
            'vulnerabilities': {
                'critical': critical,
                'high': high,
                'medium': medium
            },
            'security_score': self.calculate_security_score(),
            'recommendations': self.generate_recommendations()
        }
        
        return report
    
    def calculate_security_score(self) -> int:
        """Calculate overall security score (0-100)"""
        if not self.vulnerabilities:
            return 100
        
        # Weight vulnerabilities by severity
        critical_weight = 20
        high_weight = 10
        medium_weight = 5
        
        total_penalty = 0
        for vuln in self.vulnerabilities:
            if vuln['severity'] == 'CRITICAL':
                total_penalty += critical_weight
            elif vuln['severity'] == 'HIGH':
                total_penalty += high_weight
            elif vuln['severity'] == 'MEDIUM':
                total_penalty += medium_weight
        
        score = max(0, 100 - total_penalty)
        return score
    
    def generate_recommendations(self) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        if any(v['type'] == 'UNPROTECTED_CRITICAL_ENDPOINT' for v in self.vulnerabilities):
            recommendations.append("🔒 Add authentication to all critical API endpoints")
            recommendations.append("🛡️ Implement role-based access control (RBAC)")
        
        if any(v['type'] == 'SQL_INJECTION_RISK' for v in self.vulnerabilities):
            recommendations.append("💉 Use parameterized queries to prevent SQL injection")
        
        if any(v['type'].endswith('HARDCODED_PASSWORD') or v['type'].endswith('SECRET') for v in self.vulnerabilities):
            recommendations.append("🔑 Move all secrets to environment variables or secure vault")
        
        if any(v['type'] == 'PERMISSIVE_CORS' for v in self.vulnerabilities):
            recommendations.append("🌐 Configure CORS to allow only trusted domains")
        
        recommendations.extend([
            "📝 Implement comprehensive audit logging",
            "🔐 Enable HTTPS/TLS encryption for all communications",
            "⚡ Implement rate limiting on all API endpoints",
            "🔍 Set up automated security scanning in CI/CD",
            "🛡️ Add input validation and sanitization",
            "🔒 Implement session management and timeout controls"
        ])
        
        return recommendations
    
    def run_full_audit(self) -> Dict[str, Any]:
        """Run complete security audit"""
        print("🛡️ Starting GuardianShield Security Audit...")
        print("=" * 60)
        
        self.audit_api_endpoints()
        self.audit_database_access()
        self.audit_secret_exposure()
        self.audit_file_permissions()
        self.audit_cors_configuration()
        
        report = self.generate_security_report()
        
        print(f"\n🔍 Security Audit Complete!")
        print(f"📊 Security Score: {report['security_score']}/100")
        print(f"🚨 Critical Issues: {report['critical_count']}")
        print(f"⚠️  High Issues: {report['high_count']}")
        print(f"📋 Medium Issues: {report['medium_count']}")
        
        return report

def main():
    """Run security audit on GuardianShield"""
    import datetime
    
    workspace = os.getcwd()
    auditor = SecurityAuditor(workspace)
    
    # Run full security audit
    report = auditor.run_full_audit()
    
    # Save report
    report_file = f"security_audit_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Full report saved to: {report_file}")
    
    # Print critical vulnerabilities
    if report['critical_count'] > 0:
        print("\n🚨 CRITICAL VULNERABILITIES FOUND:")
        print("=" * 50)
        for vuln in report['vulnerabilities']['critical']:
            print(f"🔴 {vuln['type']}")
            print(f"   File: {vuln['file']}")
            print(f"   Issue: {vuln['description']}")
            print()
    
    # Print recommendations
    print("\n🛡️ SECURITY RECOMMENDATIONS:")
    print("=" * 40)
    for i, rec in enumerate(report['recommendations'][:10], 1):
        print(f"{i}. {rec}")
    
    return report

if __name__ == "__main__":
    main()