"""
GuardianShield Security Orchestration System
Unified management and monitoring for internal and external security agents
"""

import os
import sys
import json
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import sqlite3
from dataclasses import dataclass, asdict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from agents.internal_security_agent import InternalSecurityAgent
    from agents.external_security_agent import ExternalSecurityAgent
    from agents.threat_filing_system import ThreatFilingSystem
    SECURITY_AGENTS_AVAILABLE = True
except ImportError as e:
    SECURITY_AGENTS_AVAILABLE = False
    logger.error(f"Security agents not available: {e}")

@dataclass
class SecurityStatus:
    """Overall security system status"""
    timestamp: str
    internal_agent_status: str
    external_agent_status: str
    last_internal_audit: Optional[str]
    last_external_audit: Optional[str]
    total_threats_detected: int
    critical_threats: int
    system_risk_level: int
    next_scheduled_audit: str
    uptime_hours: float

class SecurityOrchestrator:
    """
    Security Orchestration System
    - Manages both internal and external security agents
    - Coordinates 24-hour audit cycles
    - Provides unified security reporting
    - Handles threat escalation and response
    """
    
    def __init__(self, workspace_path: str = "."):
        self.name = "SecurityOrchestrator"
        self.workspace_path = Path(workspace_path)
        self.start_time = datetime.now()
        
        # Initialize agents
        self.internal_agent = None
        self.external_agent = None
        self.threat_filing = None
        
        if SECURITY_AGENTS_AVAILABLE:
            self.init_security_agents()
        
        # Orchestration settings
        self.audit_coordination_enabled = True
        self.auto_escalation_enabled = True
        self.threat_response_enabled = True
        
        # Initialize orchestration database
        self.orchestration_db = "security_orchestration.db"
        self.init_orchestration_database()
        
        # Start orchestration monitoring
        self.is_orchestrating = False
        self.orchestration_thread = None
        self.start_orchestration()
        
        logger.info("Security Orchestration System initialized")
    
    def init_security_agents(self):
        """Initialize both security agents"""
        try:
            # Initialize internal security agent
            self.internal_agent = InternalSecurityAgent(self.workspace_path)
            logger.info("Internal security agent initialized")
            
            # Initialize external security agent
            self.external_agent = ExternalSecurityAgent()
            logger.info("External security agent initialized")
            
            # Initialize threat filing system
            self.threat_filing = ThreatFilingSystem()
            logger.info("Threat filing system initialized")
            
        except Exception as e:
            logger.error(f"Error initializing security agents: {e}")
    
    def init_orchestration_database(self):
        """Initialize orchestration database"""
        with sqlite3.connect(self.orchestration_db) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orchestration_status (
                    timestamp TEXT PRIMARY KEY,
                    internal_status TEXT,
                    external_status TEXT,
                    system_risk_level INTEGER,
                    total_threats INTEGER,
                    critical_threats INTEGER,
                    uptime_hours REAL,
                    status_json TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_coordination (
                    coordination_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    audit_type TEXT,
                    internal_audit_id TEXT,
                    external_audit_id TEXT,
                    combined_risk_level INTEGER,
                    threat_correlation TEXT,
                    response_actions TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS threat_escalations (
                    escalation_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    threat_source TEXT,
                    threat_type TEXT,
                    severity TEXT,
                    description TEXT,
                    escalated_to TEXT,
                    status TEXT DEFAULT 'open',
                    resolution_time TEXT
                )
            ''')
            
            conn.commit()
            logger.info("Orchestration database initialized")
    
    def get_security_status(self) -> SecurityStatus:
        """Get comprehensive security system status"""
        try:
            current_time = datetime.now()
            uptime = (current_time - self.start_time).total_seconds() / 3600
            
            # Get internal agent status
            internal_status = "unknown"
            last_internal_audit = None
            if self.internal_agent:
                if self.internal_agent.is_monitoring:
                    internal_status = "active"
                else:
                    internal_status = "inactive"
                
                latest_internal = self.internal_agent.get_latest_audit_result()
                if latest_internal:
                    last_internal_audit = latest_internal.get('timestamp')
            
            # Get external agent status
            external_status = "unknown"
            last_external_audit = None
            if self.external_agent:
                if self.external_agent.is_monitoring:
                    external_status = "active"
                else:
                    external_status = "inactive"
                
                latest_external = self.external_agent.get_latest_audit_result()
                if latest_external:
                    last_external_audit = latest_external.get('timestamp')
            
            # Get threat statistics
            total_threats = 0
            critical_threats = 0
            if self.threat_filing:
                stats = self.threat_filing.get_threat_statistics()
                total_threats = (stats.get('active_websites', 0) + 
                               stats.get('active_individuals', 0) + 
                               stats.get('active_ipos', 0))
                
                # Count critical threats (approximate)
                critical_threats = max(1, int(total_threats * 0.1))
            
            # Calculate system risk level
            system_risk = self.calculate_system_risk_level()
            
            # Calculate next audit time
            next_audit = current_time + timedelta(hours=24)
            
            return SecurityStatus(
                timestamp=current_time.isoformat(),
                internal_agent_status=internal_status,
                external_agent_status=external_status,
                last_internal_audit=last_internal_audit,
                last_external_audit=last_external_audit,
                total_threats_detected=total_threats,
                critical_threats=critical_threats,
                system_risk_level=system_risk,
                next_scheduled_audit=next_audit.isoformat(),
                uptime_hours=uptime
            )
            
        except Exception as e:
            logger.error(f"Error getting security status: {e}")
            return SecurityStatus(
                timestamp=datetime.now().isoformat(),
                internal_agent_status="error",
                external_agent_status="error",
                last_internal_audit=None,
                last_external_audit=None,
                total_threats_detected=0,
                critical_threats=0,
                system_risk_level=10,
                next_scheduled_audit=(datetime.now() + timedelta(hours=24)).isoformat(),
                uptime_hours=0.0
            )
    
    def calculate_system_risk_level(self) -> int:
        """Calculate overall system risk level"""
        try:
            risk_factors = []
            
            # Internal agent risk
            if self.internal_agent:
                latest_internal = self.internal_agent.get_latest_audit_result()
                if latest_internal:
                    risk_factors.append(latest_internal.get('risk_level', 5))
                else:
                    risk_factors.append(7)  # No audit = higher risk
            else:
                risk_factors.append(8)  # No agent = high risk
            
            # External agent risk
            if self.external_agent:
                latest_external = self.external_agent.get_latest_audit_result()
                if latest_external:
                    risk_factors.append(latest_external.get('risk_level', 5))
                else:
                    risk_factors.append(7)
            else:
                risk_factors.append(8)
            
            # Agent availability risk
            if not self.internal_agent or not self.external_agent:
                risk_factors.append(9)
            
            # Calculate weighted average
            if risk_factors:
                system_risk = min(10, max(1, sum(risk_factors) // len(risk_factors)))
            else:
                system_risk = 10
            
            return system_risk
            
        except Exception as e:
            logger.error(f"Error calculating system risk: {e}")
            return 10
    
    def coordinate_audits(self) -> Dict[str, Any]:
        """Coordinate simultaneous security audits"""
        coordination_id = f"coord_{int(time.time())}"
        logger.info(f"Starting coordinated security audit {coordination_id}")
        
        try:
            coordination_results = {
                "coordination_id": coordination_id,
                "timestamp": datetime.now().isoformat(),
                "internal_audit": None,
                "external_audit": None,
                "combined_risk": 10,
                "threat_correlations": [],
                "response_actions": []
            }
            
            # Execute internal audit
            if self.internal_agent:
                try:
                    internal_result = self.internal_agent.force_audit()
                    coordination_results["internal_audit"] = {
                        "audit_id": internal_result.audit_id,
                        "status": internal_result.status,
                        "risk_level": internal_result.risk_level,
                        "findings_count": len(internal_result.findings)
                    }
                    logger.info(f"Internal audit completed: {internal_result.status}")
                except Exception as e:
                    logger.error(f"Internal audit failed: {e}")
            
            # Execute external audit
            if self.external_agent:
                try:
                    external_result = self.external_agent.force_audit()
                    coordination_results["external_audit"] = {
                        "audit_id": external_result.audit_id,
                        "status": external_result.status,
                        "risk_level": external_result.risk_level,
                        "findings_count": len(external_result.findings)
                    }
                    logger.info(f"External audit completed: {external_result.status}")
                except Exception as e:
                    logger.error(f"External audit failed: {e}")
            
            # Analyze correlations and calculate combined risk
            combined_risk = self.analyze_audit_correlations(coordination_results)
            coordination_results["combined_risk"] = combined_risk
            
            # Generate response actions
            response_actions = self.generate_response_actions(coordination_results)
            coordination_results["response_actions"] = response_actions
            
            # Save coordination results
            self.save_coordination_results(coordination_results)
            
            logger.info(f"Coordinated audit completed - Combined risk: {combined_risk}/10")
            return coordination_results
            
        except Exception as e:
            logger.error(f"Error in audit coordination: {e}")
            return {
                "coordination_id": coordination_id,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "combined_risk": 10
            }
    
    def analyze_audit_correlations(self, coordination_results: Dict[str, Any]) -> int:
        """Analyze correlations between internal and external audit results"""
        try:
            internal_audit = coordination_results.get("internal_audit")
            external_audit = coordination_results.get("external_audit")
            
            if not internal_audit or not external_audit:
                return 8  # Missing audit = higher risk
            
            # Calculate combined risk based on both audits
            internal_risk = internal_audit.get("risk_level", 5)
            external_risk = external_audit.get("risk_level", 5)
            
            # Weighted combination (60% internal, 40% external)
            combined_risk = int((internal_risk * 0.6) + (external_risk * 0.4))
            
            # Check for correlated high-risk patterns
            if (internal_audit.get("status") == "critical" and 
                external_audit.get("status") == "critical"):
                combined_risk = min(10, combined_risk + 2)  # Both critical = escalate
            
            return min(10, max(1, combined_risk))
            
        except Exception as e:
            logger.error(f"Error analyzing correlations: {e}")
            return 8
    
    def generate_response_actions(self, coordination_results: Dict[str, Any]) -> List[str]:
        """Generate recommended response actions based on audit results"""
        actions = []
        
        try:
            combined_risk = coordination_results.get("combined_risk", 5)
            internal_audit = coordination_results.get("internal_audit", {})
            external_audit = coordination_results.get("external_audit", {})
            
            # Risk-based action generation
            if combined_risk >= 8:
                actions.append("CRITICAL: Immediate security review required")
                actions.append("Escalate to security team")
                actions.append("Consider system lockdown procedures")
            
            elif combined_risk >= 6:
                actions.append("HIGH: Enhanced monitoring recommended")
                actions.append("Review recent security events")
                actions.append("Update security policies")
            
            elif combined_risk >= 4:
                actions.append("MEDIUM: Routine security maintenance")
                actions.append("Schedule additional audits")
            
            else:
                actions.append("LOW: Continue standard monitoring")
            
            # Audit-specific actions
            if internal_audit.get("status") in ["critical", "error"]:
                actions.append("Review internal security findings")
                actions.append("Update file integrity monitoring")
            
            if external_audit.get("status") in ["critical", "error"]:
                actions.append("Review blockchain security findings")
                actions.append("Monitor suspicious contract activities")
            
            # Auto-escalation
            if self.auto_escalation_enabled and combined_risk >= 8:
                self.escalate_threat("coordinated_audit", combined_risk, coordination_results)
                actions.append("Auto-escalated to threat response team")
            
        except Exception as e:
            logger.error(f"Error generating response actions: {e}")
            actions.append("ERROR: Failed to generate response actions")
        
        return actions
    
    def escalate_threat(self, source: str, risk_level: int, details: Dict[str, Any]):
        """Escalate high-risk threats"""
        try:
            escalation_id = f"esc_{int(time.time())}"
            
            escalation_data = {
                "escalation_id": escalation_id,
                "timestamp": datetime.now().isoformat(),
                "threat_source": source,
                "threat_type": "coordinated_security_risk",
                "severity": "critical" if risk_level >= 8 else "high",
                "description": f"Coordinated audit detected risk level {risk_level}/10",
                "escalated_to": "security_team",
                "details": json.dumps(details)
            }
            
            # Save escalation to database
            with sqlite3.connect(self.orchestration_db) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO threat_escalations 
                    (escalation_id, timestamp, threat_source, threat_type, severity, 
                     description, escalated_to)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    escalation_id, escalation_data["timestamp"], escalation_data["threat_source"],
                    escalation_data["threat_type"], escalation_data["severity"],
                    escalation_data["description"], escalation_data["escalated_to"]
                ))
                conn.commit()
            
            logger.warning(f"Threat escalated: {escalation_id} - Risk level: {risk_level}/10")
            
        except Exception as e:
            logger.error(f"Error escalating threat: {e}")
    
    def save_coordination_results(self, results: Dict[str, Any]):
        """Save coordination results to database"""
        try:
            with sqlite3.connect(self.orchestration_db) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO audit_coordination 
                    (coordination_id, timestamp, audit_type, combined_risk_level, 
                     threat_correlation, response_actions)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    results["coordination_id"],
                    results["timestamp"],
                    "coordinated_security_audit",
                    results.get("combined_risk", 10),
                    json.dumps(results.get("threat_correlations", [])),
                    json.dumps(results.get("response_actions", []))
                ))
                
                conn.commit()
                logger.info(f"Coordination results saved: {results['coordination_id']}")
        
        except Exception as e:
            logger.error(f"Error saving coordination results: {e}")
    
    def get_coordination_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get audit coordination history"""
        try:
            with sqlite3.connect(self.orchestration_db) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                cursor.execute('''
                    SELECT * FROM audit_coordination 
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                ''', (cutoff_date,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting coordination history: {e}")
            return []
    
    def start_orchestration(self):
        """Start security orchestration monitoring"""
        if not self.is_orchestrating:
            self.is_orchestrating = True
            self.orchestration_thread = threading.Thread(target=self._orchestration_loop, daemon=True)
            self.orchestration_thread.start()
            logger.info("Security orchestration monitoring started")
    
    def stop_orchestration(self):
        """Stop security orchestration monitoring"""
        self.is_orchestrating = False
        if self.orchestration_thread:
            self.orchestration_thread.join(timeout=5)
        logger.info("Security orchestration monitoring stopped")
    
    def _orchestration_loop(self):
        """Main orchestration monitoring loop"""
        while self.is_orchestrating:
            try:
                # Get current status
                status = self.get_security_status()
                
                # Log status periodically
                logger.info(f"Security Status - Internal: {status.internal_agent_status}, "
                          f"External: {status.external_agent_status}, "
                          f"System Risk: {status.system_risk_level}/10")
                
                # Save status to database
                self.save_security_status(status)
                
                # Check if coordinated audit is needed (every 24 hours)
                if self.audit_coordination_enabled:
                    # Simple check - coordinate audits every 24 hours
                    coordination_history = self.get_coordination_history(days=1)
                    if not coordination_history:  # No audit in last 24 hours
                        logger.info("Triggering scheduled coordinated audit")
                        self.coordinate_audits()
                
                # Sleep for 1 hour before next status check
                time.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in orchestration loop: {e}")
                time.sleep(300)  # Wait 5 minutes before retry
    
    def save_security_status(self, status: SecurityStatus):
        """Save security status to database"""
        try:
            with sqlite3.connect(self.orchestration_db) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO orchestration_status 
                    (timestamp, internal_status, external_status, system_risk_level,
                     total_threats, critical_threats, uptime_hours, status_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    status.timestamp,
                    status.internal_agent_status,
                    status.external_agent_status,
                    status.system_risk_level,
                    status.total_threats_detected,
                    status.critical_threats,
                    status.uptime_hours,
                    json.dumps(asdict(status))
                ))
                
                conn.commit()
        
        except Exception as e:
            logger.error(f"Error saving security status: {e}")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        try:
            status = self.get_security_status()
            coordination_history = self.get_coordination_history(days=7)
            
            # Get recent escalations
            with sqlite3.connect(self.orchestration_db) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM threat_escalations 
                    ORDER BY timestamp DESC 
                    LIMIT 10
                ''')
                escalations = [dict(row) for row in cursor.fetchall()]
            
            return {
                "status": asdict(status),
                "coordination_history": coordination_history,
                "recent_escalations": escalations,
                "agents_available": SECURITY_AGENTS_AVAILABLE,
                "orchestrator_uptime": status.uptime_hours
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {
                "status": {"error": "Failed to get status"},
                "coordination_history": [],
                "recent_escalations": [],
                "agents_available": False,
                "orchestrator_uptime": 0.0
            }


if __name__ == "__main__":
    # Test the security orchestrator
    orchestrator = SecurityOrchestrator()
    
    print("🛡️ Security Orchestration System")
    print(f"Agents Available: {SECURITY_AGENTS_AVAILABLE}")
    
    # Get current status
    status = orchestrator.get_security_status()
    print(f"\n📊 Security Status:")
    print(f"Internal Agent: {status.internal_agent_status}")
    print(f"External Agent: {status.external_agent_status}")
    print(f"System Risk: {status.system_risk_level}/10")
    print(f"Total Threats: {status.total_threats_detected}")
    print(f"Critical Threats: {status.critical_threats}")
    print(f"Uptime: {status.uptime_hours:.2f} hours")
    
    # Run coordinated audit
    print(f"\n🔄 Running Coordinated Audit...")
    coordination_result = orchestrator.coordinate_audits()
    print(f"Coordination ID: {coordination_result['coordination_id']}")
    print(f"Combined Risk: {coordination_result['combined_risk']}/10")
    print(f"Response Actions: {len(coordination_result['response_actions'])}")
    
    if coordination_result.get("response_actions"):
        print("\n💡 Response Actions:")
        for action in coordination_result["response_actions"][:3]:
            print(f"  • {action}")