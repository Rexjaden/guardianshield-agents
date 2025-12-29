"""
🔍 GUARDIAN SHIELD COMPREHENSIVE AUDIT & SECURITY MONITORING SYSTEM
Complete audit trail with threat detection and real-time security monitoring
"""

import json
import time
import hashlib
import sqlite3
import logging
import logging.handlers
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import geoip2.database
import psutil
import socket
from cryptography.fernet import Fernet
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class EventCategory(Enum):
    """Event categories for better organization"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization" 
    SYSTEM_ACCESS = "system_access"
    DATA_ACCESS = "data_access"
    CONFIGURATION = "configuration"
    SECURITY = "security"
    NETWORK = "network"
    ERROR = "error"
    PERFORMANCE = "performance"

@dataclass 
class AuditEvent:
    """Comprehensive audit event structure"""
    event_id: str
    timestamp: datetime
    category: EventCategory
    event_type: str
    user_id: str
    user_role: str
    source_ip: str
    user_agent: str
    resource: str
    action: str
    outcome: str  # SUCCESS, FAILURE, ERROR
    details: Dict[str, Any]
    risk_score: int  # 0-100
    alert_level: AlertLevel
    session_id: str
    geolocation: Optional[Dict[str, str]] = None
    system_info: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['category'] = self.category.value
        data['alert_level'] = self.alert_level.value
        return data

@dataclass
class SecurityAlert:
    """Security alert structure"""
    alert_id: str
    timestamp: datetime
    alert_type: str
    severity: AlertLevel
    description: str
    affected_user: str
    source_events: List[str]  # Event IDs that triggered this alert
    remediation_steps: List[str]
    auto_resolved: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None


class GuardianAuditSystem:
    """
    🔍 COMPREHENSIVE AUDIT & SECURITY MONITORING SYSTEM
    
    Features:
    - Complete audit trail for all system activities
    - Real-time threat detection and alerting
    - Behavioral analysis and anomaly detection  
    - Encrypted audit log storage
    - Automatic security incident response
    - Comprehensive reporting and analytics
    - Integration with external SIEM systems
    """
    
    def __init__(self, db_path: str = "guardian_audit.db", encrypt_logs: bool = True):
        self.db_path = db_path
        self.encrypt_logs = encrypt_logs
        self.encryption_key = None
        
        # Initialize database and encryption
        self._initialize_database()
        if self.encrypt_logs:
            self._setup_encryption()
            
        # Initialize monitoring components
        self._setup_logging()
        self._initialize_threat_detection()
        self._start_background_monitoring()
        
        # Event queues and caches
        self.event_queue = []
        self.alert_queue = []
        self.user_behavior_cache = {}
        self.ip_reputation_cache = {}
        
        # Security thresholds
        self.security_thresholds = {
            'failed_login_threshold': 3,
            'failed_login_window': 300,  # 5 minutes
            'suspicious_ip_threshold': 5,
            'unusual_activity_threshold': 10,
            'data_access_threshold': 100,
            'privilege_escalation_threshold': 2
        }
        
    def _initialize_database(self):
        """Initialize SQLite database for audit logs"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    category TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    user_role TEXT,
                    source_ip TEXT,
                    user_agent TEXT,
                    resource TEXT,
                    action TEXT,
                    outcome TEXT NOT NULL,
                    details TEXT,
                    risk_score INTEGER,
                    alert_level TEXT,
                    session_id TEXT,
                    geolocation TEXT,
                    system_info TEXT,
                    encrypted INTEGER DEFAULT 0
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS security_alerts (
                    alert_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT NOT NULL,
                    affected_user TEXT,
                    source_events TEXT,
                    remediation_steps TEXT,
                    auto_resolved INTEGER DEFAULT 0,
                    acknowledged_by TEXT,
                    acknowledged_at TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    source_ip TEXT,
                    user_agent TEXT,
                    events_count INTEGER DEFAULT 0,
                    risk_score INTEGER DEFAULT 0
                )
            ''')
            
            # Create indices for better performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_events(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON audit_events(user_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_source_ip ON audit_events(source_ip)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_event_type ON audit_events(event_type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_risk_score ON audit_events(risk_score)')
            
    def _setup_encryption(self):
        """Setup encryption for sensitive audit data"""
        key_file = "audit_encryption.key"
        
        if Path(key_file).exists():
            with open(key_file, 'rb') as f:
                self.encryption_key = f.read()
        else:
            self.encryption_key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(self.encryption_key)
                
        self.cipher_suite = Fernet(self.encryption_key)
        
    def _setup_logging(self):
        """Setup comprehensive logging"""
        self.logger = logging.getLogger('GuardianAudit')
        self.logger.setLevel(logging.INFO)
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            'guardian_audit.log',
            maxBytes=50*1024*1024,  # 50MB
            backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - AUDIT - %(levelname)s - %(message)s')
        )
        
        self.logger.addHandler(file_handler)
        
    def _initialize_threat_detection(self):
        """Initialize threat detection rules and patterns"""
        self.threat_patterns = {
            'brute_force': {
                'pattern': 'multiple_failed_logins',
                'threshold': 5,
                'window': 300,  # 5 minutes
                'severity': AlertLevel.HIGH
            },
            'privilege_escalation': {
                'pattern': 'unauthorized_admin_access',
                'threshold': 1,
                'window': 0,
                'severity': AlertLevel.CRITICAL
            },
            'data_exfiltration': {
                'pattern': 'excessive_data_access',
                'threshold': 100,
                'window': 3600,  # 1 hour
                'severity': AlertLevel.HIGH
            },
            'suspicious_location': {
                'pattern': 'login_from_new_location',
                'threshold': 1,
                'window': 0,
                'severity': AlertLevel.MEDIUM
            },
            'off_hours_access': {
                'pattern': 'access_outside_business_hours',
                'threshold': 1,
                'window': 0,
                'severity': AlertLevel.LOW
            }
        }
        
    def _start_background_monitoring(self):
        """Start background monitoring threads"""
        # Real-time event processing thread
        self.processing_thread = threading.Thread(
            target=self._process_event_queue, daemon=True
        )
        self.processing_thread.start()
        
        # Alert processing thread
        self.alert_thread = threading.Thread(
            target=self._process_alert_queue, daemon=True
        )
        self.alert_thread.start()
        
        # Periodic analysis thread
        self.analysis_thread = threading.Thread(
            target=self._periodic_analysis, daemon=True
        )
        self.analysis_thread.start()
        
    def log_event(self, category: EventCategory, event_type: str, user_id: str,
                  user_role: str, source_ip: str, resource: str, action: str,
                  outcome: str, details: Dict[str, Any], session_id: str = None,
                  user_agent: str = None) -> str:
        """
        📝 LOG COMPREHENSIVE AUDIT EVENT
        """
        
        # Generate unique event ID
        event_id = hashlib.sha256(
            f"{time.time()}_{user_id}_{event_type}_{resource}".encode()
        ).hexdigest()[:16]
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(
            category, event_type, user_id, source_ip, outcome, details
        )
        
        # Determine alert level
        alert_level = self._determine_alert_level(risk_score, event_type, outcome)
        
        # Get geolocation if available
        geolocation = self._get_geolocation(source_ip)
        
        # Get system information
        system_info = self._get_system_info()
        
        # Create audit event
        event = AuditEvent(
            event_id=event_id,
            timestamp=datetime.now(),
            category=category,
            event_type=event_type,
            user_id=user_id,
            user_role=user_role,
            source_ip=source_ip,
            user_agent=user_agent or "Unknown",
            resource=resource,
            action=action,
            outcome=outcome,
            details=details,
            risk_score=risk_score,
            alert_level=alert_level,
            session_id=session_id or self._generate_session_id(user_id, source_ip),
            geolocation=geolocation,
            system_info=system_info
        )
        
        # Add to processing queue
        self.event_queue.append(event)
        
        # Log to standard logger
        self.logger.info(
            f"EVENT: {event_type} | User: {user_id} | IP: {source_ip} | "
            f"Resource: {resource} | Action: {action} | Outcome: {outcome} | "
            f"Risk: {risk_score}/100"
        )
        
        return event_id
        
    def _calculate_risk_score(self, category: EventCategory, event_type: str,
                            user_id: str, source_ip: str, outcome: str,
                            details: Dict[str, Any]) -> int:
        """Calculate risk score for an event (0-100)"""
        
        base_score = 10  # Base risk score
        
        # Category-based scoring
        category_scores = {
            EventCategory.AUTHENTICATION: 20,
            EventCategory.AUTHORIZATION: 30,
            EventCategory.SECURITY: 40,
            EventCategory.CONFIGURATION: 35,
            EventCategory.DATA_ACCESS: 25,
            EventCategory.SYSTEM_ACCESS: 30,
            EventCategory.NETWORK: 15,
            EventCategory.ERROR: 10,
            EventCategory.PERFORMANCE: 5
        }
        
        base_score += category_scores.get(category, 10)
        
        # Outcome-based scoring
        if outcome == "FAILURE":
            base_score += 20
        elif outcome == "ERROR":
            base_score += 15
            
        # Event type specific scoring
        high_risk_events = [
            'login_failed', 'unauthorized_access', 'privilege_escalation',
            'security_violation', 'emergency_lockdown', 'admin_created',
            'contract_deployed', 'token_minted'
        ]
        
        if event_type in high_risk_events:
            base_score += 25
            
        # User behavior analysis
        recent_events = self._get_recent_user_events(user_id, 3600)  # 1 hour
        if len(recent_events) > 50:  # Excessive activity
            base_score += 20
            
        # IP reputation check
        if self._is_suspicious_ip(source_ip):
            base_score += 30
            
        # Time-based analysis
        if self._is_off_hours():
            base_score += 15
            
        # Geographic analysis
        if self._is_new_location(user_id, source_ip):
            base_score += 20
            
        # Details-based analysis
        if details.get('admin_operation', False):
            base_score += 15
            
        if details.get('sensitive_data_access', False):
            base_score += 20
            
        return min(base_score, 100)  # Cap at 100
        
    def _determine_alert_level(self, risk_score: int, event_type: str, outcome: str) -> AlertLevel:
        """Determine alert level based on risk score and context"""
        
        # Critical events always get critical alert
        critical_events = ['emergency_lockdown', 'security_breach', 'unauthorized_admin_access']
        if event_type in critical_events:
            return AlertLevel.CRITICAL
            
        # Risk score-based determination
        if risk_score >= 80:
            return AlertLevel.CRITICAL
        elif risk_score >= 60:
            return AlertLevel.HIGH
        elif risk_score >= 40:
            return AlertLevel.MEDIUM
        elif risk_score >= 20:
            return AlertLevel.LOW
        else:
            return AlertLevel.INFO
            
    def _get_geolocation(self, ip_address: str) -> Optional[Dict[str, str]]:
        """Get geolocation information for IP address"""
        try:
            # In production, use a proper GeoIP database
            # For now, return mock data for local IPs
            if ip_address.startswith(('127.', '192.168.', '10.', '172.')):
                return {
                    'country': 'Local',
                    'city': 'Localhost',
                    'region': 'Local Network'
                }
            else:
                # Would use actual GeoIP service here
                return {
                    'country': 'Unknown',
                    'city': 'Unknown',
                    'region': 'Unknown'
                }
        except Exception:
            return None
            
    def _get_system_info(self) -> Dict[str, Any]:
        """Get current system information"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent if psutil.disk_usage('/') else 0,
                'hostname': socket.gethostname(),
                'process_count': len(psutil.pids())
            }
        except Exception:
            return {}
            
    def _generate_session_id(self, user_id: str, source_ip: str) -> str:
        """Generate session ID for user"""
        return hashlib.sha256(f"{user_id}_{source_ip}_{time.time()}".encode()).hexdigest()[:16]
        
    def _get_recent_user_events(self, user_id: str, time_window: int) -> List[AuditEvent]:
        """Get recent events for a user within time window (seconds)"""
        cutoff_time = datetime.now() - timedelta(seconds=time_window)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT * FROM audit_events 
                WHERE user_id = ? AND timestamp > ?
                ORDER BY timestamp DESC
            ''', (user_id, cutoff_time.isoformat()))
            
            events = []
            for row in cursor.fetchall():
                # Convert row to AuditEvent (simplified)
                events.append(row)
                
            return events
            
    def _is_suspicious_ip(self, ip_address: str) -> bool:
        """Check if IP address is suspicious"""
        # Check cache first
        if ip_address in self.ip_reputation_cache:
            cached_result = self.ip_reputation_cache[ip_address]
            if cached_result['expires'] > time.time():
                return cached_result['suspicious']
                
        # Simple suspicious IP detection (extend with threat intelligence)
        suspicious = False
        
        # Check for multiple failed attempts from this IP
        recent_failures = self._count_recent_failures_by_ip(ip_address, 3600)
        if recent_failures >= 10:
            suspicious = True
            
        # Cache result for 1 hour
        self.ip_reputation_cache[ip_address] = {
            'suspicious': suspicious,
            'expires': time.time() + 3600
        }
        
        return suspicious
        
    def _count_recent_failures_by_ip(self, ip_address: str, time_window: int) -> int:
        """Count recent failed events from an IP"""
        cutoff_time = datetime.now() - timedelta(seconds=time_window)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT COUNT(*) FROM audit_events 
                WHERE source_ip = ? AND outcome = 'FAILURE' AND timestamp > ?
            ''', (ip_address, cutoff_time.isoformat()))
            
            return cursor.fetchone()[0]
            
    def _is_off_hours(self) -> bool:
        """Check if current time is outside business hours"""
        current_hour = datetime.now().hour
        # Assuming business hours are 9 AM to 6 PM
        return current_hour < 9 or current_hour > 18
        
    def _is_new_location(self, user_id: str, source_ip: str) -> bool:
        """Check if user is accessing from a new location"""
        # Get user's recent IP addresses (last 30 days)
        cutoff_time = datetime.now() - timedelta(days=30)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT DISTINCT source_ip FROM audit_events 
                WHERE user_id = ? AND timestamp > ?
            ''', (user_id, cutoff_time.isoformat()))
            
            known_ips = [row[0] for row in cursor.fetchall()]
            
        return source_ip not in known_ips
        
    def _process_event_queue(self):
        """Background thread to process audit events"""
        while True:
            try:
                if self.event_queue:
                    event = self.event_queue.pop(0)
                    self._store_event(event)
                    self._analyze_event_for_threats(event)
                    
                time.sleep(0.1)  # Small delay to prevent CPU spinning
                
            except Exception as e:
                self.logger.error(f"Error processing event queue: {e}")
                time.sleep(1)
                
    def _store_event(self, event: AuditEvent):
        """Store audit event in database"""
        try:
            details_json = json.dumps(event.details)
            geolocation_json = json.dumps(event.geolocation) if event.geolocation else None
            system_info_json = json.dumps(event.system_info) if event.system_info else None
            
            # Encrypt sensitive data if encryption is enabled
            encrypted = 0
            if self.encrypt_logs and event.alert_level in [AlertLevel.HIGH, AlertLevel.CRITICAL]:
                details_json = self.cipher_suite.encrypt(details_json.encode()).decode()
                encrypted = 1
                
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO audit_events (
                        event_id, timestamp, category, event_type, user_id, user_role,
                        source_ip, user_agent, resource, action, outcome, details,
                        risk_score, alert_level, session_id, geolocation, system_info, encrypted
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event.event_id, event.timestamp.isoformat(), event.category.value,
                    event.event_type, event.user_id, event.user_role, event.source_ip,
                    event.user_agent, event.resource, event.action, event.outcome,
                    details_json, event.risk_score, event.alert_level.value,
                    event.session_id, geolocation_json, system_info_json, encrypted
                ))
                
        except Exception as e:
            self.logger.error(f"Error storing event {event.event_id}: {e}")
            
    def _analyze_event_for_threats(self, event: AuditEvent):
        """Analyze event for potential security threats"""
        
        # Check each threat pattern
        for threat_type, pattern_config in self.threat_patterns.items():
            if self._matches_threat_pattern(event, threat_type, pattern_config):
                self._create_security_alert(threat_type, event, pattern_config)
                
    def _matches_threat_pattern(self, event: AuditEvent, threat_type: str, 
                               pattern_config: Dict[str, Any]) -> bool:
        """Check if event matches a threat pattern"""
        
        pattern = pattern_config['pattern']
        
        if pattern == 'multiple_failed_logins':
            if event.event_type == 'login_failed':
                recent_failures = self._count_recent_failures_by_user(
                    event.user_id, pattern_config['window']
                )
                return recent_failures >= pattern_config['threshold']
                
        elif pattern == 'unauthorized_admin_access':
            return (event.event_type == 'unauthorized_access' and 
                    'admin' in event.resource.lower())
                    
        elif pattern == 'excessive_data_access':
            if 'data_access' in event.event_type:
                recent_access_count = self._count_recent_data_access(
                    event.user_id, pattern_config['window']
                )
                return recent_access_count >= pattern_config['threshold']
                
        elif pattern == 'login_from_new_location':
            return (event.event_type == 'login_success' and 
                    self._is_new_location(event.user_id, event.source_ip))
                    
        elif pattern == 'access_outside_business_hours':
            return (event.event_type in ['login_success', 'system_access'] and 
                    self._is_off_hours())
                    
        return False
        
    def _count_recent_failures_by_user(self, user_id: str, time_window: int) -> int:
        """Count recent failed login attempts by user"""
        cutoff_time = datetime.now() - timedelta(seconds=time_window)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT COUNT(*) FROM audit_events 
                WHERE user_id = ? AND event_type = 'login_failed' AND timestamp > ?
            ''', (user_id, cutoff_time.isoformat()))
            
            return cursor.fetchone()[0]
            
    def _count_recent_data_access(self, user_id: str, time_window: int) -> int:
        """Count recent data access events by user"""
        cutoff_time = datetime.now() - timedelta(seconds=time_window)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT COUNT(*) FROM audit_events 
                WHERE user_id = ? AND event_type LIKE '%data_access%' AND timestamp > ?
            ''', (user_id, cutoff_time.isoformat()))
            
            return cursor.fetchone()[0]
            
    def _create_security_alert(self, threat_type: str, event: AuditEvent,
                             pattern_config: Dict[str, Any]):
        """Create a security alert based on threat detection"""
        
        alert_id = hashlib.sha256(
            f"{threat_type}_{event.user_id}_{time.time()}".encode()
        ).hexdigest()[:16]
        
        # Generate description and remediation steps
        description = self._generate_alert_description(threat_type, event)
        remediation_steps = self._generate_remediation_steps(threat_type, event)
        
        alert = SecurityAlert(
            alert_id=alert_id,
            timestamp=datetime.now(),
            alert_type=threat_type,
            severity=pattern_config['severity'],
            description=description,
            affected_user=event.user_id,
            source_events=[event.event_id],
            remediation_steps=remediation_steps
        )
        
        self.alert_queue.append(alert)
        
    def _generate_alert_description(self, threat_type: str, event: AuditEvent) -> str:
        """Generate human-readable alert description"""
        descriptions = {
            'brute_force': f"Multiple failed login attempts detected for user {event.user_id} from IP {event.source_ip}",
            'privilege_escalation': f"Unauthorized admin access attempt by user {event.user_id}",
            'data_exfiltration': f"Excessive data access pattern detected for user {event.user_id}",
            'suspicious_location': f"Login from new geographic location for user {event.user_id}",
            'off_hours_access': f"System access outside business hours by user {event.user_id}"
        }
        
        return descriptions.get(threat_type, f"Security threat detected: {threat_type}")
        
    def _generate_remediation_steps(self, threat_type: str, event: AuditEvent) -> List[str]:
        """Generate remediation steps for security alerts"""
        remediation = {
            'brute_force': [
                "Temporarily lock user account",
                "Block source IP address",
                "Force password reset",
                "Enable additional MFA"
            ],
            'privilege_escalation': [
                "Immediately suspend user account",
                "Review user permissions",
                "Audit recent admin actions",
                "Contact security team"
            ],
            'data_exfiltration': [
                "Monitor user data access",
                "Review accessed data sensitivity",
                "Check for data export/download",
                "Consider temporary access restriction"
            ],
            'suspicious_location': [
                "Verify user identity",
                "Require additional authentication",
                "Monitor user activity closely",
                "Consider geographic restrictions"
            ],
            'off_hours_access': [
                "Verify business justification",
                "Monitor user activity",
                "Review access patterns",
                "Consider access time restrictions"
            ]
        }
        
        return remediation.get(threat_type, ["Review and investigate the incident"])
        
    def _process_alert_queue(self):
        """Background thread to process security alerts"""
        while True:
            try:
                if self.alert_queue:
                    alert = self.alert_queue.pop(0)
                    self._store_alert(alert)
                    self._handle_alert(alert)
                    
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Error processing alert queue: {e}")
                time.sleep(1)
                
    def _store_alert(self, alert: SecurityAlert):
        """Store security alert in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO security_alerts (
                        alert_id, timestamp, alert_type, severity, description,
                        affected_user, source_events, remediation_steps,
                        auto_resolved, acknowledged_by, acknowledged_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    alert.alert_id, alert.timestamp.isoformat(), alert.alert_type,
                    alert.severity.value, alert.description, alert.affected_user,
                    json.dumps(alert.source_events), json.dumps(alert.remediation_steps),
                    alert.auto_resolved, alert.acknowledged_by,
                    alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
                ))
                
        except Exception as e:
            self.logger.error(f"Error storing alert {alert.alert_id}: {e}")
            
    def _handle_alert(self, alert: SecurityAlert):
        """Handle security alert with appropriate response"""
        
        self.logger.warning(
            f"SECURITY ALERT: {alert.alert_type} | Severity: {alert.severity.value} | "
            f"User: {alert.affected_user} | Description: {alert.description}"
        )
        
        # Automatic response based on severity
        if alert.severity == AlertLevel.CRITICAL:
            self._handle_critical_alert(alert)
        elif alert.severity == AlertLevel.HIGH:
            self._handle_high_alert(alert)
            
    def _handle_critical_alert(self, alert: SecurityAlert):
        """Handle critical security alerts with immediate response"""
        
        # Log critical alert
        self.logger.critical(f"CRITICAL ALERT: {alert.alert_type} - {alert.description}")
        
        # Send immediate notification (implement email/SMS/webhook)
        self._send_emergency_notification(alert)
        
        # Auto-remediation for certain types
        if alert.alert_type == 'privilege_escalation':
            # Could trigger account suspension
            pass
            
    def _handle_high_alert(self, alert: SecurityAlert):
        """Handle high-severity alerts"""
        
        self.logger.error(f"HIGH ALERT: {alert.alert_type} - {alert.description}")
        
        # Send notification to security team
        self._send_security_notification(alert)
        
    def _send_emergency_notification(self, alert: SecurityAlert):
        """Send emergency notification for critical alerts"""
        # Implementation would send email/SMS/webhook notifications
        print(f"🚨 EMERGENCY ALERT: {alert.description}")
        
    def _send_security_notification(self, alert: SecurityAlert):
        """Send security notification for high-priority alerts"""
        # Implementation would send notifications to security team
        print(f"⚠️ SECURITY ALERT: {alert.description}")
        
    def _periodic_analysis(self):
        """Periodic analysis and cleanup"""
        while True:
            try:
                # Run every hour
                time.sleep(3600)
                
                # Cleanup old events (keep last 90 days)
                self._cleanup_old_events(90)
                
                # Generate periodic reports
                self._generate_periodic_reports()
                
                # Update threat detection patterns
                self._update_threat_patterns()
                
            except Exception as e:
                self.logger.error(f"Error in periodic analysis: {e}")
                
    def _cleanup_old_events(self, retention_days: int):
        """Clean up old audit events"""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                DELETE FROM audit_events WHERE timestamp < ?
            ''', (cutoff_date.isoformat(),))
            
            deleted_count = cursor.rowcount
            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old audit events")
                
    def get_security_dashboard(self, time_range: int = 24) -> Dict[str, Any]:
        """Get comprehensive security dashboard data"""
        
        cutoff_time = datetime.now() - timedelta(hours=time_range)
        
        with sqlite3.connect(self.db_path) as conn:
            # Total events
            cursor = conn.execute('''
                SELECT COUNT(*) FROM audit_events WHERE timestamp > ?
            ''', (cutoff_time.isoformat(),))
            total_events = cursor.fetchone()[0]
            
            # Events by category
            cursor = conn.execute('''
                SELECT category, COUNT(*) FROM audit_events 
                WHERE timestamp > ? GROUP BY category
            ''', (cutoff_time.isoformat(),))
            events_by_category = dict(cursor.fetchall())
            
            # Risk distribution
            cursor = conn.execute('''
                SELECT alert_level, COUNT(*) FROM audit_events 
                WHERE timestamp > ? GROUP BY alert_level
            ''', (cutoff_time.isoformat(),))
            risk_distribution = dict(cursor.fetchall())
            
            # Top users by activity
            cursor = conn.execute('''
                SELECT user_id, COUNT(*) as activity_count FROM audit_events 
                WHERE timestamp > ? GROUP BY user_id ORDER BY activity_count DESC LIMIT 10
            ''', (cutoff_time.isoformat(),))
            top_users = cursor.fetchall()
            
            # Top IPs by activity
            cursor = conn.execute('''
                SELECT source_ip, COUNT(*) as activity_count FROM audit_events 
                WHERE timestamp > ? GROUP BY source_ip ORDER BY activity_count DESC LIMIT 10
            ''', (cutoff_time.isoformat(),))
            top_ips = cursor.fetchall()
            
            # Active alerts
            cursor = conn.execute('''
                SELECT severity, COUNT(*) FROM security_alerts 
                WHERE timestamp > ? AND acknowledged_by IS NULL GROUP BY severity
            ''', (cutoff_time.isoformat(),))
            active_alerts = dict(cursor.fetchall())
            
        return {
            'total_events': total_events,
            'events_by_category': events_by_category,
            'risk_distribution': risk_distribution,
            'top_users': top_users,
            'top_ips': top_ips,
            'active_alerts': active_alerts,
            'time_range_hours': time_range,
            'generated_at': datetime.now().isoformat()
        }
        

def main():
    """Test the audit system"""
    print("\n🔍 TESTING GUARDIAN SHIELD AUDIT SYSTEM")
    print("=" * 50)
    
    # Initialize audit system
    audit = GuardianAuditSystem()
    
    # Test various events
    print("\n📝 Logging test events...")
    
    # Successful login
    audit.log_event(
        EventCategory.AUTHENTICATION, 'login_success', 'admin_user', 'ADMIN',
        '192.168.1.100', 'admin_console', 'login', 'SUCCESS',
        {'browser': 'Chrome', 'platform': 'Windows'}, 'session_123'
    )
    
    # Failed login attempts (should trigger brute force alert)
    for i in range(6):
        audit.log_event(
            EventCategory.AUTHENTICATION, 'login_failed', 'test_user', 'USER',
            '192.168.1.200', 'admin_console', 'login', 'FAILURE',
            {'reason': 'invalid_password', 'attempt': i+1}, f'session_{200+i}'
        )
        
    # Unauthorized admin access
    audit.log_event(
        EventCategory.AUTHORIZATION, 'unauthorized_access', 'regular_user', 'USER',
        '192.168.1.150', 'admin_panel', 'access_attempt', 'FAILURE',
        {'requested_resource': 'admin_functions', 'admin_operation': True}
    )
    
    # Wait a moment for background processing
    time.sleep(2)
    
    # Get dashboard
    dashboard = audit.get_security_dashboard(24)
    
    print(f"\n📊 SECURITY DASHBOARD (Last 24 hours):")
    print(f"   Total Events: {dashboard['total_events']}")
    print(f"   Events by Category: {dashboard['events_by_category']}")
    print(f"   Risk Distribution: {dashboard['risk_distribution']}")
    print(f"   Active Alerts: {dashboard['active_alerts']}")
    
    print("\n🎉 Audit system test completed!")
    

if __name__ == "__main__":
    main()