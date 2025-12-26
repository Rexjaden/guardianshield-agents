"""
GuardianShield Internal Security Monitoring Agent
Advanced internal security monitoring with automated 24-hour audit cycles
"""

import os
import sys
import json
import time
import hashlib
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from pathlib import Path
import psutil
import sqlite3
from dataclasses import dataclass, asdict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from agents.threat_filing_system import ThreatFilingSystem
    THREAT_FILING_AVAILABLE = True
except ImportError:
    THREAT_FILING_AVAILABLE = False
    logger.warning("Threat filing system not available")

@dataclass
class SecurityAuditResult:
    """Structure for security audit results"""
    audit_id: str
    agent_name: str
    audit_type: str
    timestamp: str
    status: str  # success, warning, critical, error
    findings: List[Dict[str, Any]]
    risk_level: int  # 1-10 scale
    recommendations: List[str]
    affected_components: List[str]
    remediation_required: bool

class InternalSecurityAgent:
    """
    Internal Security Monitoring Agent
    - System file integrity monitoring
    - Log analysis for suspicious activities  
    - Configuration security audits
    - Process and service monitoring
    - Automated 24-hour security cycles
    """
    
    def __init__(self, workspace_path: str = "."):
        self.name = "InternalSecurityAgent"
        self.workspace_path = Path(workspace_path)
        self.audit_db_path = "internal_security_audits.db"
        
        # Security monitoring configuration
        self.monitored_files = set()
        self.file_checksums = {}
        self.security_baselines = {}
        self.last_audit_time = None
        self.audit_interval = timedelta(hours=24)  # 24-hour cycle
        self.is_monitoring = False
        
        # Initialize components
        self.init_audit_database()
        self.load_security_baselines()
        
        # Initialize threat filing if available
        if THREAT_FILING_AVAILABLE:
            self.threat_filing = ThreatFilingSystem()
            logger.info("Threat filing system connected")
        else:
            self.threat_filing = None
        
        # Start monitoring thread
        self.monitoring_thread = None
        self.start_monitoring()
        
        logger.info(f"Internal Security Agent initialized - monitoring {self.workspace_path}")
    
    def init_audit_database(self):
        """Initialize SQLite database for audit results"""
        with sqlite3.connect(self.audit_db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_audits (
                    audit_id TEXT PRIMARY KEY,
                    agent_name TEXT NOT NULL,
                    audit_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    status TEXT NOT NULL,
                    risk_level INTEGER NOT NULL,
                    findings_count INTEGER DEFAULT 0,
                    remediation_required BOOLEAN DEFAULT FALSE,
                    findings_json TEXT,
                    recommendations_json TEXT,
                    affected_components_json TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_integrity (
                    file_path TEXT PRIMARY KEY,
                    checksum TEXT NOT NULL,
                    last_modified TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    permissions TEXT,
                    first_seen TEXT NOT NULL,
                    last_checked TEXT NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_events (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    source_component TEXT,
                    description TEXT NOT NULL,
                    details_json TEXT,
                    resolved BOOLEAN DEFAULT FALSE
                )
            ''')
            
            conn.commit()
            logger.info("Internal security audit database initialized")
    
    def load_security_baselines(self):
        """Load or create security baseline configurations"""
        baseline_file = self.workspace_path / "security_baselines.json"
        
        default_baselines = {
            "critical_files": [
                "*.py", "*.json", "*.yaml", "*.yml", "*.env", 
                "requirements.txt", "package.json", "*.sol"
            ],
            "sensitive_patterns": [
                r"password\s*[:=]\s*['\"](.+)['\"]",
                r"api[_-]?key\s*[:=]\s*['\"](.+)['\"]",
                r"secret[_-]?key\s*[:=]\s*['\"](.+)['\"]",
                r"private[_-]?key\s*[:=]\s*['\"](.+)['\"]",
                r"token\s*[:=]\s*['\"](.+)['\"]"
            ],
            "max_file_size": 100 * 1024 * 1024,  # 100MB
            "allowed_extensions": [
                ".py", ".js", ".ts", ".json", ".yaml", ".yml", 
                ".md", ".txt", ".sol", ".html", ".css"
            ],
            "forbidden_patterns": [
                r"eval\s*\(", r"exec\s*\(", r"__import__\s*\(", r"subprocess\.call\s*\(",
                r"os\.system\s*\(", r"shell\s*=\s*True"
            ],
            "process_whitelist": [
                "python", "node", "uvicorn", "fastapi"
            ]
        }
        
        if baseline_file.exists():
            try:
                with open(baseline_file, 'r') as f:
                    self.security_baselines = json.load(f)
                logger.info("Security baselines loaded from file")
            except Exception as e:
                logger.error(f"Error loading security baselines: {e}")
                self.security_baselines = default_baselines
        else:
            self.security_baselines = default_baselines
            try:
                with open(baseline_file, 'w') as f:
                    json.dump(self.security_baselines, f, indent=2)
                logger.info("Default security baselines created")
            except Exception as e:
                logger.error(f"Error saving security baselines: {e}")
    
    def calculate_file_checksum(self, file_path: Path) -> Optional[str]:
        """Calculate SHA256 checksum for file"""
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating checksum for {file_path}: {e}")
            return None
    
    def scan_file_integrity(self) -> List[Dict[str, Any]]:
        """Scan for file integrity issues"""
        findings = []
        
        try:
            # Scan critical files
            for pattern in self.security_baselines["critical_files"]:
                for file_path in self.workspace_path.rglob(pattern):
                    if file_path.is_file():
                        try:
                            # Calculate current checksum
                            current_checksum = self.calculate_file_checksum(file_path)
                            if not current_checksum:
                                continue
                            
                            # Get file stats
                            stat = file_path.stat()
                            current_size = stat.st_size
                            current_modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
                            
                            # Check against database
                            with sqlite3.connect(self.audit_db_path) as conn:
                                cursor = conn.cursor()
                                cursor.execute(
                                    "SELECT checksum, size, last_modified FROM file_integrity WHERE file_path = ?",
                                    (str(file_path),)
                                )
                                result = cursor.fetchone()
                                
                                if result:
                                    stored_checksum, stored_size, stored_modified = result
                                    
                                    # Check for changes
                                    if current_checksum != stored_checksum:
                                        findings.append({
                                            "type": "file_integrity_change",
                                            "severity": "warning",
                                            "file": str(file_path),
                                            "description": f"File content changed: {file_path.name}",
                                            "details": {
                                                "previous_checksum": stored_checksum,
                                                "current_checksum": current_checksum,
                                                "size_change": current_size - stored_size
                                            }
                                        })
                                    
                                    # Update database
                                    cursor.execute('''
                                        UPDATE file_integrity 
                                        SET checksum = ?, last_modified = ?, size = ?, last_checked = ?
                                        WHERE file_path = ?
                                    ''', (current_checksum, current_modified, current_size, 
                                         datetime.now().isoformat(), str(file_path)))
                                else:
                                    # New file - add to database
                                    cursor.execute('''
                                        INSERT INTO file_integrity 
                                        (file_path, checksum, last_modified, size, first_seen, last_checked)
                                        VALUES (?, ?, ?, ?, ?, ?)
                                    ''', (str(file_path), current_checksum, current_modified, 
                                         current_size, datetime.now().isoformat(), datetime.now().isoformat()))
                                
                                conn.commit()
                        
                        except Exception as e:
                            logger.error(f"Error processing file {file_path}: {e}")
            
            logger.info(f"File integrity scan completed - {len(findings)} issues found")
        
        except Exception as e:
            logger.error(f"Error in file integrity scan: {e}")
            findings.append({
                "type": "scan_error",
                "severity": "error", 
                "description": f"File integrity scan failed: {str(e)}"
            })
        
        return findings
    
    def scan_sensitive_data(self) -> List[Dict[str, Any]]:
        """Scan for exposed sensitive data in files"""
        findings = []
        
        try:
            import re
            
            for pattern_desc, pattern in zip(
                ["Password", "API Key", "Secret Key", "Private Key", "Token"],
                self.security_baselines["sensitive_patterns"]
            ):
                compiled_pattern = re.compile(pattern, re.IGNORECASE)
                
                for file_path in self.workspace_path.rglob("*.py"):
                    if file_path.is_file():
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                
                            matches = compiled_pattern.finditer(content)
                            for match in matches:
                                # Don't report if it's in a comment or test file
                                line_start = content.rfind('\n', 0, match.start()) + 1
                                line_end = content.find('\n', match.end())
                                if line_end == -1:
                                    line_end = len(content)
                                line_content = content[line_start:line_end]
                                
                                if not (line_content.strip().startswith('#') or 
                                       'test' in str(file_path).lower() or
                                       'example' in line_content.lower()):
                                    findings.append({
                                        "type": "sensitive_data_exposure",
                                        "severity": "critical",
                                        "file": str(file_path),
                                        "description": f"Potential {pattern_desc} exposure in {file_path.name}",
                                        "details": {
                                            "pattern_type": pattern_desc,
                                            "line_content": line_content.strip()[:100],  # First 100 chars
                                            "position": match.start()
                                        }
                                    })
                        
                        except Exception as e:
                            logger.debug(f"Error scanning {file_path} for sensitive data: {e}")
            
            logger.info(f"Sensitive data scan completed - {len(findings)} issues found")
        
        except Exception as e:
            logger.error(f"Error in sensitive data scan: {e}")
            findings.append({
                "type": "scan_error",
                "severity": "error",
                "description": f"Sensitive data scan failed: {str(e)}"
            })
        
        return findings
    
    def scan_process_security(self) -> List[Dict[str, Any]]:
        """Scan running processes for security issues"""
        findings = []
        
        try:
            # Get running processes
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    proc_name = proc_info['name'].lower()
                    
                    # Check for suspicious processes
                    suspicious_names = ['netcat', 'nc', 'nmap', 'wireshark', 'tcpdump']
                    if any(susp in proc_name for susp in suspicious_names):
                        findings.append({
                            "type": "suspicious_process",
                            "severity": "warning",
                            "description": f"Suspicious process detected: {proc_info['name']}",
                            "details": {
                                "pid": proc_info['pid'],
                                "name": proc_info['name'],
                                "cmdline": proc_info['cmdline']
                            }
                        })
                    
                    # Check for high resource usage
                    if (proc_info['cpu_percent'] and proc_info['cpu_percent'] > 80 or 
                        proc_info['memory_percent'] and proc_info['memory_percent'] > 80):
                        findings.append({
                            "type": "high_resource_usage",
                            "severity": "warning",
                            "description": f"High resource usage: {proc_info['name']}",
                            "details": {
                                "pid": proc_info['pid'],
                                "cpu_percent": proc_info['cpu_percent'],
                                "memory_percent": proc_info['memory_percent']
                            }
                        })
                
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            logger.info(f"Process security scan completed - {len(findings)} issues found")
        
        except Exception as e:
            logger.error(f"Error in process security scan: {e}")
            findings.append({
                "type": "scan_error",
                "severity": "error",
                "description": f"Process security scan failed: {str(e)}"
            })
        
        return findings
    
    def scan_configuration_security(self) -> List[Dict[str, Any]]:
        """Scan configuration files for security issues"""
        findings = []
        
        try:
            # Check for insecure configurations
            config_files = list(self.workspace_path.rglob("*.json")) + \
                          list(self.workspace_path.rglob("*.yaml")) + \
                          list(self.workspace_path.rglob("*.yml")) + \
                          list(self.workspace_path.rglob(".env*"))
            
            for config_file in config_files:
                try:
                    with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().lower()
                    
                    # Check for insecure patterns
                    insecure_patterns = {
                        "debug=true": "Debug mode enabled in production",
                        "ssl_verify=false": "SSL verification disabled",
                        "cors_allow_all": "CORS allows all origins",
                        "password=\"\"": "Empty password configuration",
                        "auth_required=false": "Authentication disabled"
                    }
                    
                    for pattern, description in insecure_patterns.items():
                        if pattern in content:
                            findings.append({
                                "type": "insecure_configuration",
                                "severity": "warning",
                                "file": str(config_file),
                                "description": f"Insecure configuration: {description}",
                                "details": {
                                    "pattern": pattern,
                                    "file": config_file.name
                                }
                            })
                
                except Exception as e:
                    logger.debug(f"Error scanning config file {config_file}: {e}")
            
            logger.info(f"Configuration security scan completed - {len(findings)} issues found")
        
        except Exception as e:
            logger.error(f"Error in configuration security scan: {e}")
            findings.append({
                "type": "scan_error",
                "severity": "error",
                "description": f"Configuration security scan failed: {str(e)}"
            })
        
        return findings
    
    def perform_security_audit(self) -> SecurityAuditResult:
        """Perform comprehensive internal security audit"""
        audit_id = f"internal_{int(time.time())}"
        timestamp = datetime.now().isoformat()
        
        logger.info(f"Starting internal security audit {audit_id}")
        
        try:
            # Run all security scans
            all_findings = []
            
            all_findings.extend(self.scan_file_integrity())
            all_findings.extend(self.scan_sensitive_data())
            all_findings.extend(self.scan_process_security())
            all_findings.extend(self.scan_configuration_security())
            
            # Calculate risk level
            risk_level = self.calculate_risk_level(all_findings)
            
            # Generate recommendations
            recommendations = self.generate_recommendations(all_findings)
            
            # Determine status
            critical_count = len([f for f in all_findings if f.get('severity') == 'critical'])
            error_count = len([f for f in all_findings if f.get('severity') == 'error'])
            
            if critical_count > 0:
                status = "critical"
            elif error_count > 0:
                status = "error" 
            elif len(all_findings) > 0:
                status = "warning"
            else:
                status = "success"
            
            # Get affected components
            affected_components = list(set([
                f.get('file', 'system') for f in all_findings 
                if f.get('file')
            ]))
            
            # Create audit result
            audit_result = SecurityAuditResult(
                audit_id=audit_id,
                agent_name=self.name,
                audit_type="internal_security",
                timestamp=timestamp,
                status=status,
                findings=all_findings,
                risk_level=risk_level,
                recommendations=recommendations,
                affected_components=affected_components,
                remediation_required=critical_count > 0 or error_count > 0
            )
            
            # Save audit result
            self.save_audit_result(audit_result)
            
            # File critical threats to threat database
            if self.threat_filing and critical_count > 0:
                self.file_security_threats(all_findings)
            
            logger.info(f"Internal security audit {audit_id} completed - Status: {status}, Risk: {risk_level}/10")
            
            return audit_result
            
        except Exception as e:
            logger.error(f"Error performing security audit: {e}")
            return SecurityAuditResult(
                audit_id=audit_id,
                agent_name=self.name,
                audit_type="internal_security",
                timestamp=timestamp,
                status="error",
                findings=[{
                    "type": "audit_error",
                    "severity": "error",
                    "description": f"Security audit failed: {str(e)}"
                }],
                risk_level=10,
                recommendations=["Investigate audit system failure"],
                affected_components=["audit_system"],
                remediation_required=True
            )
    
    def calculate_risk_level(self, findings: List[Dict[str, Any]]) -> int:
        """Calculate overall risk level based on findings"""
        if not findings:
            return 1
        
        severity_weights = {
            "critical": 10,
            "error": 7,
            "warning": 4,
            "info": 1
        }
        
        total_weight = sum(severity_weights.get(f.get('severity', 'info'), 1) for f in findings)
        max_possible_weight = len(findings) * 10
        
        if max_possible_weight == 0:
            return 1
        
        risk_level = min(10, max(1, int((total_weight / max_possible_weight) * 10)))
        return risk_level
    
    def generate_recommendations(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Generate security recommendations based on findings"""
        recommendations = []
        
        # Group findings by type
        findings_by_type = {}
        for finding in findings:
            finding_type = finding.get('type', 'unknown')
            if finding_type not in findings_by_type:
                findings_by_type[finding_type] = []
            findings_by_type[finding_type].append(finding)
        
        # Generate type-specific recommendations
        if 'sensitive_data_exposure' in findings_by_type:
            recommendations.append("Review and encrypt exposed sensitive data")
            recommendations.append("Implement proper secret management system")
        
        if 'file_integrity_change' in findings_by_type:
            recommendations.append("Investigate unauthorized file modifications")
            recommendations.append("Implement file integrity monitoring alerts")
        
        if 'suspicious_process' in findings_by_type:
            recommendations.append("Investigate suspicious processes")
            recommendations.append("Implement process whitelisting")
        
        if 'insecure_configuration' in findings_by_type:
            recommendations.append("Review and harden configuration settings")
            recommendations.append("Disable debug modes in production")
        
        if 'high_resource_usage' in findings_by_type:
            recommendations.append("Monitor and optimize resource usage")
            recommendations.append("Investigate potential resource-based attacks")
        
        # General recommendations
        if len(findings) > 0:
            recommendations.append("Implement continuous security monitoring")
            recommendations.append("Schedule regular security audits")
        
        return recommendations
    
    def save_audit_result(self, audit_result: SecurityAuditResult):
        """Save audit result to database"""
        try:
            with sqlite3.connect(self.audit_db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO security_audits 
                    (audit_id, agent_name, audit_type, timestamp, status, risk_level,
                     findings_count, remediation_required, findings_json, recommendations_json, affected_components_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    audit_result.audit_id,
                    audit_result.agent_name,
                    audit_result.audit_type,
                    audit_result.timestamp,
                    audit_result.status,
                    audit_result.risk_level,
                    len(audit_result.findings),
                    audit_result.remediation_required,
                    json.dumps(audit_result.findings),
                    json.dumps(audit_result.recommendations),
                    json.dumps(audit_result.affected_components)
                ))
                
                conn.commit()
                logger.info(f"Audit result {audit_result.audit_id} saved to database")
        
        except Exception as e:
            logger.error(f"Error saving audit result: {e}")
    
    def file_security_threats(self, findings: List[Dict[str, Any]]):
        """File critical security findings as threats"""
        try:
            critical_findings = [f for f in findings if f.get('severity') == 'critical']
            
            for finding in critical_findings:
                if finding.get('type') == 'sensitive_data_exposure':
                    # File as malicious individual or website depending on context
                    self.threat_filing.add_malicious_individual(
                        name=f"Internal Security Risk - {finding.get('file', 'Unknown')}",
                        threat_type="insider",
                        severity=9,
                        description=f"Sensitive data exposure: {finding.get('description', '')}",
                        source="internal_security_audit"
                    )
                    
                logger.info(f"Filed critical security finding as threat: {finding.get('type')}")
        
        except Exception as e:
            logger.error(f"Error filing security threats: {e}")
    
    def start_monitoring(self):
        """Start continuous security monitoring"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            logger.info("Internal security monitoring started")
    
    def stop_monitoring(self):
        """Stop continuous security monitoring"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Internal security monitoring stopped")
    
    def _monitoring_loop(self):
        """Continuous monitoring loop with 24-hour audit cycles"""
        while self.is_monitoring:
            try:
                current_time = datetime.now()
                
                # Check if it's time for a scheduled audit
                if (not self.last_audit_time or 
                    current_time - self.last_audit_time >= self.audit_interval):
                    
                    logger.info("Starting scheduled 24-hour internal security audit")
                    audit_result = self.perform_security_audit()
                    self.last_audit_time = current_time
                    
                    # Log audit summary
                    logger.info(f"Audit completed - Status: {audit_result.status}, "
                              f"Risk: {audit_result.risk_level}/10, "
                              f"Findings: {len(audit_result.findings)}")
                
                # Sleep for 1 hour before next check
                time.sleep(3600)  # Check every hour
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(300)  # Wait 5 minutes before retry
    
    def get_latest_audit_result(self) -> Optional[Dict[str, Any]]:
        """Get the latest audit result"""
        try:
            with sqlite3.connect(self.audit_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM security_audits 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ''')
                
                result = cursor.fetchone()
                if result:
                    audit_data = dict(result)
                    audit_data['findings'] = json.loads(audit_data['findings_json'])
                    audit_data['recommendations'] = json.loads(audit_data['recommendations_json'])
                    audit_data['affected_components'] = json.loads(audit_data['affected_components_json'])
                    return audit_data
                
        except Exception as e:
            logger.error(f"Error getting latest audit result: {e}")
        
        return None
    
    def get_audit_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get audit history for specified number of days"""
        try:
            with sqlite3.connect(self.audit_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                cursor.execute('''
                    SELECT audit_id, agent_name, audit_type, timestamp, status, 
                           risk_level, findings_count, remediation_required
                    FROM security_audits 
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                ''', (cutoff_date,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting audit history: {e}")
            return []
    
    def force_audit(self) -> SecurityAuditResult:
        """Force an immediate security audit"""
        logger.info("Forcing immediate internal security audit")
        return self.perform_security_audit()


if __name__ == "__main__":
    # Test the internal security agent
    agent = InternalSecurityAgent()
    
    print("🛡️ Internal Security Agent initialized")
    print(f"Monitoring workspace: {agent.workspace_path}")
    print(f"Next audit scheduled in: {agent.audit_interval}")
    
    # Perform immediate audit for testing
    audit_result = agent.force_audit()
    print(f"\n📊 Audit Results:")
    print(f"Status: {audit_result.status}")
    print(f"Risk Level: {audit_result.risk_level}/10")
    print(f"Findings: {len(audit_result.findings)}")
    print(f"Remediation Required: {audit_result.remediation_required}")
    
    if audit_result.findings:
        print("\n🔍 Key Findings:")
        for finding in audit_result.findings[:3]:  # Show first 3
            print(f"  • {finding.get('severity', 'info').upper()}: {finding.get('description', 'No description')}")
    
    if audit_result.recommendations:
        print("\n💡 Recommendations:")
        for rec in audit_result.recommendations[:3]:  # Show first 3
            print(f"  • {rec}")