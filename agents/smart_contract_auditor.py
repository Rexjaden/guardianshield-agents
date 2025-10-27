"""
smart_contract_auditor.py: Continuous smart contract security analysis and vulnerability detection
"""

import json
import time
import logging
import hashlib
import re
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests not available, HTTP features disabled")

try:
    from web3 import Web3
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    print("Warning: web3 not available, blockchain features disabled")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartContractAuditor:
    """Continuous smart contract security analysis agent"""
    
    def __init__(self, name: str = "SmartContractAuditor"):
        self.name = name
        self.unlimited_evolution = True
        self.autonomous_decisions = True
        
        # Vulnerability patterns
        self.vulnerability_patterns = {
            'reentrancy': [
                r'\.call\s*\(',
                r'\.send\s*\(',
                r'\.transfer\s*\(',
                r'external.*payable'
            ],
            'integer_overflow': [
                r'\+\+|\-\-',
                r'unchecked\s*\{',
                r'SafeMath'
            ],
            'access_control': [
                r'onlyOwner',
                r'require\s*\(\s*msg\.sender',
                r'modifier.*owner'
            ],
            'oracle_manipulation': [
                r'getPrice\s*\(',
                r'oracle\.',
                r'price.*feed'
            ],
            'flash_loan_vulnerable': [
                r'flashLoan',
                r'borrow.*repay',
                r'liquidity.*check'
            ]
        }
        
        # Contract monitoring state
        self.monitored_contracts = {}
        self.vulnerability_history = []
        self.audit_results = {}
        self.bytecode_analysis = {}
        
        # Risk scoring weights
        self.risk_weights = {
            'reentrancy': 0.9,
            'integer_overflow': 0.7,
            'access_control': 0.8,
            'oracle_manipulation': 0.8,
            'flash_loan_vulnerable': 0.6,
            'unverified_source': 0.5,
            'proxy_pattern': 0.4,
            'large_value_locked': 0.3
        }
    
    def autonomous_cycle(self):
        """Main autonomous auditing cycle"""
        try:
            logger.info(f"[{self.name}] Starting smart contract audit cycle")
            
            # Real-time contract vulnerability scanning
            self.scan_new_contracts()
            
            # Bytecode analysis and pattern matching
            self.analyze_contract_bytecode()
            
            # Proxy contract upgrade monitoring
            self.monitor_proxy_upgrades()
            
            # Access control verification
            self.verify_access_controls()
            
            # Economic security model validation
            self.validate_economic_security()
            
        except Exception as e:
            logger.error(f"[{self.name}] Autonomous cycle error: {e}")
    
    def scan_new_contracts(self) -> List[Dict]:
        """Scan newly deployed contracts for vulnerabilities"""
        vulnerabilities = []
        
        try:
            # Get recently deployed contracts
            new_contracts = self.get_recent_deployments()
            
            for contract in new_contracts:
                audit_result = self.audit_contract(contract)
                
                if audit_result['risk_score'] > 0.6:
                    vulnerabilities.append({
                        'type': 'high_risk_contract',
                        'contract_address': contract['address'],
                        'deployer': contract.get('deployer'),
                        'risk_score': audit_result['risk_score'],
                        'vulnerabilities': audit_result['vulnerabilities'],
                        'severity': 'HIGH' if audit_result['risk_score'] > 0.8 else 'MEDIUM',
                        'timestamp': time.time()
                    })
                
                # Store audit result
                self.audit_results[contract['address']] = audit_result
            
            if vulnerabilities:
                self.log_action("vulnerability_scan", f"Found {len(vulnerabilities)} high-risk contracts")
            
        except Exception as e:
            logger.error(f"Contract scanning error: {e}")
        
        return vulnerabilities
    
    def audit_contract(self, contract: Dict) -> Dict:
        """Perform comprehensive audit of a smart contract"""
        audit_result = {
            'contract_address': contract['address'],
            'risk_score': 0.0,
            'vulnerabilities': [],
            'recommendations': [],
            'analysis_timestamp': time.time()
        }
        
        try:
            # Source code analysis (if available)
            source_code = contract.get('source_code')
            if source_code:
                source_vulnerabilities = self.analyze_source_code(source_code)
                audit_result['vulnerabilities'].extend(source_vulnerabilities)
            else:
                audit_result['vulnerabilities'].append({
                    'type': 'unverified_source',
                    'severity': 'MEDIUM',
                    'description': 'Contract source code not verified'
                })
            
            # Bytecode analysis
            bytecode = contract.get('bytecode')
            if bytecode:
                bytecode_analysis = self.analyze_bytecode(bytecode)
                audit_result['vulnerabilities'].extend(bytecode_analysis)
            
            # Calculate overall risk score
            audit_result['risk_score'] = self.calculate_risk_score(audit_result['vulnerabilities'])
            
            # Generate recommendations
            audit_result['recommendations'] = self.generate_recommendations(audit_result['vulnerabilities'])
            
        except Exception as e:
            logger.error(f"Contract audit error: {e}")
            audit_result['error'] = str(e)
        
        return audit_result
    
    def analyze_source_code(self, source_code: str) -> List[Dict]:
        """Analyze source code for vulnerability patterns"""
        vulnerabilities = []
        
        try:
            for vuln_type, patterns in self.vulnerability_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, source_code, re.IGNORECASE)
                    if matches:
                        vulnerabilities.append({
                            'type': vuln_type,
                            'pattern': pattern,
                            'matches': len(matches),
                            'severity': self.get_vulnerability_severity(vuln_type),
                            'description': self.get_vulnerability_description(vuln_type)
                        })
            
            # Additional static analysis
            additional_checks = self.perform_additional_checks(source_code)
            vulnerabilities.extend(additional_checks)
            
        except Exception as e:
            logger.error(f"Source code analysis error: {e}")
        
        return vulnerabilities
    
    def analyze_bytecode(self, bytecode: str) -> List[Dict]:
        """Analyze contract bytecode for suspicious patterns"""
        vulnerabilities = []
        
        try:
            # Check for suspicious opcodes
            suspicious_opcodes = ['SELFDESTRUCT', 'DELEGATECALL', 'CALLCODE']
            
            for opcode in suspicious_opcodes:
                if opcode.lower() in bytecode.lower():
                    vulnerabilities.append({
                        'type': 'suspicious_opcode',
                        'opcode': opcode,
                        'severity': 'MEDIUM',
                        'description': f'Contains potentially dangerous {opcode} opcode'
                    })
            
            # Check bytecode size (large contracts might be more complex/risky)
            if len(bytecode) > 100000:  # Arbitrary threshold
                vulnerabilities.append({
                    'type': 'large_contract',
                    'size': len(bytecode),
                    'severity': 'LOW',
                    'description': 'Large contract size may indicate complexity'
                })
            
            # Check for proxy patterns
            if self.detect_proxy_pattern(bytecode):
                vulnerabilities.append({
                    'type': 'proxy_pattern',
                    'severity': 'MEDIUM',
                    'description': 'Contract uses proxy pattern - monitor for upgrades'
                })
            
        except Exception as e:
            logger.error(f"Bytecode analysis error: {e}")
        
        return vulnerabilities
    
    def monitor_proxy_upgrades(self) -> List[Dict]:
        """Monitor proxy contract upgrades"""
        upgrade_alerts = []
        
        try:
            proxy_contracts = self.get_proxy_contracts()
            
            for proxy in proxy_contracts:
                # Check for recent upgrades
                recent_upgrades = self.check_proxy_upgrades(proxy['address'])
                
                for upgrade in recent_upgrades:
                    # Analyze new implementation
                    implementation_audit = self.audit_contract({
                        'address': upgrade['new_implementation'],
                        'source_code': upgrade.get('source_code'),
                        'bytecode': upgrade.get('bytecode')
                    })
                    
                    if implementation_audit['risk_score'] > 0.7:
                        upgrade_alerts.append({
                            'type': 'risky_proxy_upgrade',
                            'proxy_address': proxy['address'],
                            'new_implementation': upgrade['new_implementation'],
                            'risk_score': implementation_audit['risk_score'],
                            'vulnerabilities': implementation_audit['vulnerabilities'],
                            'severity': 'HIGH',
                            'timestamp': time.time()
                        })
            
        except Exception as e:
            logger.error(f"Proxy monitoring error: {e}")
        
        return upgrade_alerts
    
    def verify_access_controls(self) -> List[Dict]:
        """Verify access control implementations"""
        access_issues = []
        
        try:
            contracts = self.get_monitored_contracts()
            
            for contract in contracts:
                access_analysis = self.analyze_access_controls(contract)
                
                if access_analysis['risk_level'] > 0.6:
                    access_issues.append({
                        'type': 'access_control_issue',
                        'contract_address': contract['address'],
                        'issues': access_analysis['issues'],
                        'risk_level': access_analysis['risk_level'],
                        'severity': 'HIGH' if access_analysis['risk_level'] > 0.8 else 'MEDIUM',
                        'timestamp': time.time()
                    })
            
        except Exception as e:
            logger.error(f"Access control verification error: {e}")
        
        return access_issues
    
    def validate_economic_security(self) -> List[Dict]:
        """Validate economic security models"""
        economic_issues = []
        
        try:
            protocols = self.get_defi_protocols()
            
            for protocol in protocols:
                economic_analysis = self.analyze_economic_model(protocol)
                
                if economic_analysis['risk_score'] > 0.7:
                    economic_issues.append({
                        'type': 'economic_security_risk',
                        'protocol': protocol['name'],
                        'issues': economic_analysis['issues'],
                        'risk_score': economic_analysis['risk_score'],
                        'severity': 'HIGH',
                        'timestamp': time.time()
                    })
            
        except Exception as e:
            logger.error(f"Economic security validation error: {e}")
        
        return economic_issues
    
    # Helper methods
    def get_recent_deployments(self) -> List[Dict]:
        """Get recently deployed contracts"""
        # Simulate recent deployments - in production, would monitor blockchain
        return [
            {
                'address': '0xnewcontract123',
                'deployer': '0xdeployer123',
                'source_code': 'contract Example { function withdraw() public { ... } }',
                'bytecode': '0x608060405234801561001057600080fd5b50...'
            }
        ]
    
    def perform_additional_checks(self, source_code: str) -> List[Dict]:
        """Perform additional security checks"""
        checks = []
        
        # Check for unsafe external calls
        if re.search(r'\.call\s*\([^)]*\)', source_code):
            checks.append({
                'type': 'unsafe_external_call',
                'severity': 'HIGH',
                'description': 'Unsafe external call detected'
            })
        
        # Check for missing input validation
        if not re.search(r'require\s*\(', source_code):
            checks.append({
                'type': 'missing_validation',
                'severity': 'MEDIUM',
                'description': 'No input validation detected'
            })
        
        return checks
    
    def get_vulnerability_severity(self, vuln_type: str) -> str:
        """Get severity level for vulnerability type"""
        severity_map = {
            'reentrancy': 'HIGH',
            'integer_overflow': 'MEDIUM',
            'access_control': 'HIGH',
            'oracle_manipulation': 'HIGH',
            'flash_loan_vulnerable': 'MEDIUM'
        }
        return severity_map.get(vuln_type, 'LOW')
    
    def get_vulnerability_description(self, vuln_type: str) -> str:
        """Get description for vulnerability type"""
        descriptions = {
            'reentrancy': 'Potential reentrancy vulnerability detected',
            'integer_overflow': 'Potential integer overflow/underflow',
            'access_control': 'Access control mechanisms detected',
            'oracle_manipulation': 'Oracle price feed usage detected',
            'flash_loan_vulnerable': 'Flash loan functionality detected'
        }
        return descriptions.get(vuln_type, 'Unknown vulnerability')
    
    def calculate_risk_score(self, vulnerabilities: List[Dict]) -> float:
        """Calculate overall risk score"""
        score = 0.0
        
        for vuln in vulnerabilities:
            vuln_type = vuln.get('type', '')
            weight = self.risk_weights.get(vuln_type, 0.1)
            
            severity_multiplier = {
                'HIGH': 1.0,
                'MEDIUM': 0.6,
                'LOW': 0.3
            }.get(vuln.get('severity', 'LOW'), 0.1)
            
            score += weight * severity_multiplier
        
        return min(score, 1.0)  # Cap at 1.0
    
    def generate_recommendations(self, vulnerabilities: List[Dict]) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        vuln_types = [v.get('type') for v in vulnerabilities]
        
        if 'reentrancy' in vuln_types:
            recommendations.append('Implement reentrancy guards')
        if 'access_control' in vuln_types:
            recommendations.append('Review access control mechanisms')
        if 'oracle_manipulation' in vuln_types:
            recommendations.append('Use multiple oracle sources')
        
        return recommendations
    
    def detect_proxy_pattern(self, bytecode: str) -> bool:
        """Detect if contract uses proxy pattern"""
        # Simplified detection
        proxy_patterns = ['delegatecall', 'implementation']
        return any(pattern in bytecode.lower() for pattern in proxy_patterns)
    
    def get_proxy_contracts(self) -> List[Dict]:
        """Get known proxy contracts"""
        return [
            {
                'address': '0xproxy123',
                'implementation': '0ximpl123'
            }
        ]
    
    def check_proxy_upgrades(self, proxy_address: str) -> List[Dict]:
        """Check for recent proxy upgrades"""
        return [
            {
                'new_implementation': '0xnewimpl123',
                'timestamp': time.time() - 3600
            }
        ]
    
    def get_monitored_contracts(self) -> List[Dict]:
        """Get contracts being monitored"""
        return [
            {
                'address': '0xcontract123',
                'source_code': 'contract Test { ... }'
            }
        ]
    
    def analyze_access_controls(self, contract: Dict) -> Dict:
        """Analyze access control implementation"""
        return {
            'risk_level': 0.3,
            'issues': ['centralized_control']
        }
    
    def get_defi_protocols(self) -> List[Dict]:
        """Get DeFi protocols for economic analysis"""
        return [
            {
                'name': 'ExampleDeFi',
                'contracts': ['0xprotocol123']
            }
        ]
    
    def analyze_economic_model(self, protocol: Dict) -> Dict:
        """Analyze economic security model"""
        return {
            'risk_score': 0.2,
            'issues': ['minor_economic_risk']
        }
    
    def log_action(self, action: str, details: str):
        """Log agent actions"""
        try:
            from admin_console import AdminConsole
            console = AdminConsole()
            console.log_action(self.name, action, details)
        except Exception as e:
            logger.error(f"Logging error: {e}")

if __name__ == "__main__":
    auditor = SmartContractAuditor()
    auditor.autonomous_cycle()