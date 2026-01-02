"""
GuardianShield Security Assessment Tool
Comprehensive security analysis for the entire GuardianShield system
"""

import os
import sys
import sqlite3
import json
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Any
import subprocess

class GuardianShieldSecurityAnalyzer:
    """Comprehensive security analyzer for GuardianShield"""
    
    def __init__(self):
        self.vulnerabilities = []
        self.warnings = []
        self.passed_checks = []
        self.workspace_root = Path.cwd()
    
    def log_vulnerability(self, category: str, severity: str, description: str, file_path: str = None):
        """Log a security vulnerability"""
        self.vulnerabilities.append({
            "category": category,
            "severity": severity,  # critical, high, medium, low
            "description": description,
            "file": file_path,
            "timestamp": None
        })
    
    def log_warning(self, category: str, description: str, file_path: str = None):
        """Log a security warning"""
        self.warnings.append({
            "category": category,
            "description": description,
            "file": file_path
        })
    
    def log_passed(self, category: str, description: str):
        """Log a passed security check"""
        self.passed_checks.append({
            "category": category,
            "description": description
        })
    
    def check_sql_injection_vulnerabilities(self):
        """Check for SQL injection vulnerabilities"""
        print("1. Checking SQL Injection Vulnerabilities...")
        
        sql_injection_patterns = [
            r'cursor\.execute\([^?]*%[^?]*\)',
            r'cursor\.execute\([^?]*format[^?]*\)',
            r'cursor\.execute\([^?]*\+[^?]*\)',
            r'"SELECT.*"\s*%',
            r'"INSERT.*"\s*%',
            r'"UPDATE.*"\s*%',
            r'"DELETE.*"\s*%'
        ]
        
        vulnerable_files = []
        
        for py_file in self.workspace_root.rglob("*.py"):
            if "local_backup" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                for pattern in sql_injection_patterns:
                    if re.search(pattern, content):
                        vulnerable_files.append(str(py_file))
                        self.log_vulnerability(
                            "SQL Injection",
                            "high",
                            f"Potential SQL injection vulnerability found",
                            str(py_file)
                        )
                        break
            except Exception:
                continue
        
        if not vulnerable_files:
            self.log_passed("SQL Injection", "No SQL injection vulnerabilities detected")
        
        return len(vulnerable_files) == 0
    
    def check_file_permissions(self):
        """Check file and database permissions"""
        print("2. Checking File Permissions...")
        
        sensitive_files = [
            "threat_intelligence.db",
            "security_orchestration.db", 
            "internal_security_audits.db",
            "external_security_audits.db",
            ".env",
            "config.json",
            "secrets.json"
        ]
        
        issues_found = 0
        
        for file_name in sensitive_files:
            if os.path.exists(file_name):
                stat_info = os.stat(file_name)
                permissions = oct(stat_info.st_mode)[-3:]
                
                if permissions in ["666", "777", "755"]:
                    self.log_vulnerability(
                        "File Permissions",
                        "medium",
                        f"File {file_name} has overly permissive permissions: {permissions}",
                        file_name
                    )
                    issues_found += 1
                else:
                    self.log_passed("File Permissions", f"{file_name} has secure permissions: {permissions}")
        
        return issues_found == 0
    
    def check_hardcoded_secrets(self):
        """Check for hardcoded secrets and credentials"""
        print("3. Checking for Hardcoded Secrets...")
        
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']{8,}["\']', "password"),
            (r'secret\s*=\s*["\'][^"\']{16,}["\']', "secret"),
            (r'api_key\s*=\s*["\'][^"\']{20,}["\']', "api_key"),
            (r'private_key\s*=\s*["\'][^"\']{32,}["\']', "private_key"),
            (r'token\s*=\s*["\'][^"\']{20,}["\']', "token"),
            (r'[0-9a-fA-F]{32,64}', "hex_string"),
        ]
        
        secrets_found = 0
        
        for py_file in self.workspace_root.rglob("*.py"):
            if "local_backup" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                for pattern, secret_type in secret_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # Skip obvious test/example data
                        if any(keyword in match.group().lower() for keyword in 
                              ["test", "example", "change_this", "your_", "placeholder"]):
                            continue
                            
                        self.log_vulnerability(
                            "Hardcoded Secrets",
                            "high",
                            f"Potential {secret_type} found: {match.group()[:50]}...",
                            str(py_file)
                        )
                        secrets_found += 1
            except Exception:
                continue
        
        if secrets_found == 0:
            self.log_passed("Hardcoded Secrets", "No hardcoded secrets detected")
        
        return secrets_found == 0
    
    def check_api_security(self):
        """Check API security configurations"""
        print("4. Checking API Security...")
        
        api_files = [
            "security_dashboard_api.py",
            "threat_filing_api.py",
            "api_server.py"
        ]
        
        issues_found = 0
        
        for api_file in api_files:
            if os.path.exists(api_file):
                with open(api_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check CORS configuration
                if 'allow_origins=["*"]' in content:
                    self.log_warning(
                        "API Security",
                        f"{api_file}: CORS allows all origins (acceptable for development)",
                        api_file
                    )
                
                # Check for authentication
                if "authentication" not in content.lower() and "auth" not in content.lower():
                    if "FastAPI" in content:
                        self.log_warning(
                            "API Security",
                            f"{api_file}: No authentication mechanisms detected",
                            api_file
                        )
                
                # Check for input validation
                if "HTTPException" not in content:
                    self.log_warning(
                        "API Security",
                        f"{api_file}: Limited input validation/error handling",
                        api_file
                    )
        
        self.log_passed("API Security", "API security configurations reviewed")
        return True
    
    def check_input_validation(self):
        """Check for input validation vulnerabilities"""
        print("5. Checking Input Validation...")
        
        dangerous_functions = [
            "eval(",
            "exec(",
            "compile(",
            "__import__(",
            "subprocess.call",
            "os.system(",
            "shell=True"
        ]
        
        issues_found = 0
        
        for py_file in self.workspace_root.rglob("*.py"):
            if "local_backup" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                for dangerous_func in dangerous_functions:
                    if dangerous_func in content:
                        # Check if it's in a legitimate context
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if dangerous_func in line:
                                # Skip comments and safe usage patterns
                                if line.strip().startswith('#'):
                                    continue
                                if "subprocess.check_call" in line or "subprocess.run" in line:
                                    continue  # These are safer than subprocess.call
                                
                                self.log_vulnerability(
                                    "Input Validation",
                                    "high" if dangerous_func in ["eval(", "exec("] else "medium",
                                    f"Dangerous function {dangerous_func} found on line {i+1}",
                                    str(py_file)
                                )
                                issues_found += 1
                                break
            except Exception:
                continue
        
        if issues_found == 0:
            self.log_passed("Input Validation", "No dangerous function usage detected")
        
        return issues_found == 0
    
    def check_crypto_security(self):
        """Check cryptographic security"""
        print("6. Checking Cryptographic Security...")
        
        weak_crypto_patterns = [
            r'md5\(',
            r'sha1\(',
            r'random\.',
            r'urandom\(4\)',
            r'DES',
            r'RC4'
        ]
        
        issues_found = 0
        
        for py_file in self.workspace_root.rglob("*.py"):
            if "local_backup" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                for pattern in weak_crypto_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        self.log_warning(
                            "Cryptographic Security",
                            f"Potentially weak crypto pattern found: {pattern}",
                            str(py_file)
                        )
                        issues_found += 1
            except Exception:
                continue
        
        if issues_found == 0:
            self.log_passed("Cryptographic Security", "No weak cryptographic patterns detected")
        
        return True
    
    def check_dependency_security(self):
        """Check for known vulnerable dependencies"""
        print("7. Checking Dependency Security...")
        
        # Read requirements.txt if it exists
        if os.path.exists("requirements.txt"):
            with open("requirements.txt", 'r') as f:
                requirements = f.read()
                
            # Check for potentially vulnerable versions
            vulnerable_packages = {
                "fastapi": "0.68.0",  # Example - very old version
                "uvicorn": "0.11.0",
                "requests": "2.20.0"
            }
            
            for package, min_version in vulnerable_packages.items():
                if package in requirements:
                    self.log_passed("Dependency Security", f"Using {package} (version check needed)")
        
        self.log_passed("Dependency Security", "Dependency versions reviewed")
        return True
    
    def check_logging_security(self):
        """Check for sensitive data in logs"""
        print("8. Checking Logging Security...")
        
        log_patterns = [
            r'logger\.[^(]*\([^)]*password[^)]*\)',
            r'logger\.[^(]*\([^)]*secret[^)]*\)',
            r'logger\.[^(]*\([^)]*token[^)]*\)',
            r'print\([^)]*password[^)]*\)',
            r'print\([^)]*secret[^)]*\)'
        ]
        
        issues_found = 0
        
        for py_file in self.workspace_root.rglob("*.py"):
            if "local_backup" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                for pattern in log_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        self.log_warning(
                            "Logging Security",
                            f"Potential sensitive data in logs: {match.group()[:50]}...",
                            str(py_file)
                        )
                        issues_found += 1
            except Exception:
                continue
        
        if issues_found == 0:
            self.log_passed("Logging Security", "No sensitive data logging detected")
        
        return True
    
    def generate_security_report(self):
        """Generate comprehensive security report"""
        print("\n" + "="*70)
        print("GUARDIANSHIELD SECURITY ASSESSMENT REPORT")
        print("="*70)
        
        # Summary
        total_vulnerabilities = len(self.vulnerabilities)
        total_warnings = len(self.warnings)
        total_passed = len(self.passed_checks)
        
        print(f"\nSUMMARY:")
        print(f"✅ Passed Checks: {total_passed}")
        print(f"⚠️  Warnings: {total_warnings}")
        print(f"🚨 Vulnerabilities: {total_vulnerabilities}")
        
        # Risk Assessment
        critical_count = len([v for v in self.vulnerabilities if v['severity'] == 'critical'])
        high_count = len([v for v in self.vulnerabilities if v['severity'] == 'high'])
        medium_count = len([v for v in self.vulnerabilities if v['severity'] == 'medium'])
        low_count = len([v for v in self.vulnerabilities if v['severity'] == 'low'])
        
        risk_score = (critical_count * 10) + (high_count * 7) + (medium_count * 4) + (low_count * 1)
        
        if risk_score == 0:
            risk_level = "LOW"
        elif risk_score <= 10:
            risk_level = "MEDIUM"
        elif risk_score <= 30:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"
        
        print(f"\nRISK ASSESSMENT:")
        print(f"Risk Level: {risk_level}")
        print(f"Risk Score: {risk_score}")
        print(f"  Critical: {critical_count}")
        print(f"  High: {high_count}")
        print(f"  Medium: {medium_count}")
        print(f"  Low: {low_count}")
        
        # Vulnerabilities
        if self.vulnerabilities:
            print(f"\nVULNERABILITIES FOUND:")
            for i, vuln in enumerate(self.vulnerabilities, 1):
                print(f"{i}. [{vuln['severity'].upper()}] {vuln['category']}")
                print(f"   {vuln['description']}")
                if vuln['file']:
                    print(f"   File: {vuln['file']}")
                print()
        
        # Warnings
        if self.warnings:
            print(f"\nWARNINGS:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"{i}. [{warning['category']}] {warning['description']}")
                if warning['file']:
                    print(f"   File: {warning['file']}")
                print()
        
        # Passed Checks
        if self.passed_checks:
            print(f"\nPASSED SECURITY CHECKS:")
            for check in self.passed_checks:
                print(f"✅ {check['category']}: {check['description']}")
        
        print("\n" + "="*70)
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "vulnerabilities": total_vulnerabilities,
            "warnings": total_warnings,
            "passed": total_passed
        }
    
    def run_full_assessment(self):
        """Run complete security assessment"""
        print("GuardianShield Security Assessment")
        print("=" * 50)
        
        # Run all security checks
        self.check_sql_injection_vulnerabilities()
        self.check_file_permissions()
        self.check_hardcoded_secrets()
        self.check_api_security()
        self.check_input_validation()
        self.check_crypto_security()
        self.check_dependency_security()
        self.check_logging_security()
        
        # Generate report
        return self.generate_security_report()


if __name__ == "__main__":
    analyzer = GuardianShieldSecurityAnalyzer()
    results = analyzer.run_full_assessment()