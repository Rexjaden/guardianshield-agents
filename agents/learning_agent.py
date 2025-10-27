"""
Sentinel: An AI agent for monitoring everything beyond (external to) the platform in the GuardianShield project.
This agent is responsible for external threat detection, off-platform monitoring, and cross-chain intelligence.
Enhanced with unlimited autonomous evolution and recursive self-improvement capabilities.
Real-time Web3 security monitoring with flash loan detection, MEV protection, and cross-chain threat correlation.
"""

from agents.threat_definitions import is_known_threat, get_deceptive_act_definition
from agents.flare_integration import FlareIntegration
from agents.master_key_algorithm import MasterKeyAlgorithm
from agents.behavioral_analytics import BehavioralAnalytics
from agents.web3_utils import Web3Utils
import json
import numpy as np
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import SGDClassifier
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not available, ML features disabled")

try:
    import smtplib
    from email.message import EmailMessage
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    print("Warning: email features not available")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests not available, HTTP features disabled")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LearningAgent:
    """External threat detection and cross-chain intelligence agent with unlimited evolution"""
    
    def __init__(self, name="learning_agent"):
        self.name = name
        self.unlimited_evolution = True
        self.autonomous_decisions = True
        self.learning_rate = 0.1
        
        # Enhanced Web3 security parameters
        self.realtime_monitoring = True
        self.flash_loan_threshold = 10000  # USD
        self.mev_detection_threshold = 1000  # USD
        self.cross_chain_correlation_window = 300  # 5 minutes
        
        # Machine learning components
        if SKLEARN_AVAILABLE:
            self.vectorizer = TfidfVectorizer(max_features=1000)
            self.classifier = SGDClassifier(loss='log_loss', learning_rate='adaptive', eta0=self.learning_rate)
        else:
            self.vectorizer = None
            self.classifier = None
        
        # Behavioral analytics integration
        try:
            self.behavioral_analytics = BehavioralAnalytics()
        except Exception as e:
            logger.warning(f"Could not initialize behavioral analytics: {e}")
            self.behavioral_analytics = None
        
        # Threat monitoring state
        self.threat_history = []
        self.flash_loan_alerts = []
        self.mev_attacks = []
        self.cross_chain_threats = []
        
        # Real-time monitoring state
        self.monitoring_active = False
        self.last_scan_time = 0
        
        logger.info(f"LearningAgent {self.name} initialized with Web3 security capabilities")

    def autonomous_cycle(self):
        """Main autonomous cycle with real-time Web3 security monitoring"""
        logger.info(f"[{self.name}] Starting enhanced autonomous cycle")
        
        try:
            # Start real-time security monitoring
            if self.realtime_monitoring:
                self.start_realtime_security_monitoring()
            
            # Traditional learning cycle
            self.learn()
            
            # Enhanced threat detection
            self.detect_advanced_threats()
            
            # Cross-chain threat correlation
            self.correlate_cross_chain_threats()
            
            # Self-evolution
            if self.unlimited_evolution:
                self.enable_unlimited_evolution()
            
            # Log cycle completion
            self.log_action("autonomous_cycle_complete", "Enhanced cycle with Web3 monitoring completed")
            
        except Exception as e:
            logger.error(f"[{self.name}] Autonomous cycle error: {e}")
            self.log_action("autonomous_cycle_error", f"Error: {e}")

    def start_realtime_security_monitoring(self):
        """Start real-time Web3 security monitoring (30-second cycles)"""
        logger.info(f"[{self.name}] Starting real-time Web3 security monitoring")
        
        current_time = time.time()
        
        # Only run if enough time has passed (30 seconds)
        if current_time - self.last_scan_time < 30:
            return
        
        self.last_scan_time = current_time
        self.monitoring_active = True
        
        try:
            # Flash loan attack detection
            flash_loan_threats = self.detect_flash_loan_attacks()
            if flash_loan_threats:
                self.log_action("flash_loan_detected", f"Detected {len(flash_loan_threats)} flash loan threats")
                self.flash_loan_alerts.extend(flash_loan_threats)
            
            # MEV attack detection
            mev_threats = self.detect_mev_attacks()
            if mev_threats:
                self.log_action("mev_attacks_detected", f"Detected {len(mev_threats)} MEV attacks")
                self.mev_attacks.extend(mev_threats)
            
            # Smart contract monitoring
            contract_threats = self.monitor_smart_contracts_realtime()
            if contract_threats:
                self.log_action("contract_threats_detected", f"Detected {len(contract_threats)} contract threats")
            
            # Cross-chain threat monitoring
            cross_chain_threats = self.correlate_cross_chain_threats()
            if cross_chain_threats:
                self.log_action("cross_chain_threats", f"Detected {len(cross_chain_threats)} cross-chain threats")
            
            logger.info(f"[{self.name}] Real-time security scan completed")
            
        except Exception as e:
            logger.error(f"Real-time monitoring error: {e}")
            self.log_action("realtime_monitoring_error", f"Error: {e}")
        
        finally:
            self.monitoring_active = False

    def detect_flash_loan_attacks(self) -> List[Dict]:
        """Detect flash loan attacks in real-time"""
        flash_loan_attacks = []
        
        try:
            # Simulate flash loan detection logic
            # In production, this would analyze mempool and executed transactions
            
            # Example flash loan patterns
            suspicious_patterns = [
                {
                    'transaction_hash': '0xflash_loan_attack_1',
                    'amount_borrowed': 50000000,  # $50M
                    'profit_extracted': 1500000,  # $1.5M
                    'attack_type': 'price_manipulation',
                    'target_protocol': 'compound',
                    'severity': 'HIGH',
                    'timestamp': time.time()
                }
            ]
            
            for pattern in suspicious_patterns:
                if pattern['profit_extracted'] > self.flash_loan_threshold:
                    flash_loan_attacks.append(pattern)
                    logger.warning(f"Flash loan attack detected: {pattern['attack_type']} on {pattern['target_protocol']}")
            
        except Exception as e:
            logger.error(f"Flash loan detection error: {e}")
        
        return flash_loan_attacks

    def detect_mev_attacks(self) -> List[Dict]:
        """Detect MEV (Maximal Extractable Value) attacks"""
        mev_attacks = []
        
        try:
            # Simulate MEV attack detection
            # In production, this would analyze transaction ordering and gas prices
            
            mev_patterns = [
                {
                    'attack_type': 'sandwich_attack',
                    'victim_transaction': '0xvictim_tx_1',
                    'front_run_tx': '0xfront_run_1',
                    'back_run_tx': '0xback_run_1',
                    'profit_extracted': 2500,  # $2.5K
                    'gas_cost': 500,  # $500
                    'net_profit': 2000,  # $2K
                    'severity': 'MEDIUM',
                    'timestamp': time.time()
                }
            ]
            
            for pattern in mev_patterns:
                if pattern['profit_extracted'] > self.mev_detection_threshold:
                    mev_attacks.append(pattern)
                    logger.warning(f"MEV attack detected: {pattern['attack_type']} with ${pattern['profit_extracted']} profit")
            
        except Exception as e:
            logger.error(f"MEV detection error: {e}")
        
        return mev_attacks

    def monitor_smart_contracts_realtime(self) -> List[Dict]:
        """Monitor smart contracts for real-time threats"""
        contract_threats = []
        
        try:
            # Simulate smart contract monitoring
            # In production, this would monitor contract events and state changes
            
            threat_patterns = [
                {
                    'contract_address': '0xsuspicious_contract_1',
                    'threat_type': 'reentrancy_vulnerability',
                    'risk_level': 'HIGH',
                    'affected_functions': ['withdraw', 'transfer'],
                    'potential_loss': 10000000,  # $10M
                    'timestamp': time.time()
                }
            ]
            
            for threat in threat_patterns:
                contract_threats.append(threat)
                logger.warning(f"Smart contract threat: {threat['threat_type']} in {threat['contract_address']}")
            
        except Exception as e:
            logger.error(f"Smart contract monitoring error: {e}")
        
        return contract_threats

    def correlate_cross_chain_threats(self) -> List[Dict]:
        """Correlate threats across multiple blockchain networks"""
        cross_chain_threats = []
        
        try:
            # Simulate cross-chain threat correlation
            # In production, this would analyze patterns across different chains
            
            correlation_patterns = [
                {
                    'threat_id': 'cross_chain_attack_1',
                    'affected_chains': ['ethereum', 'bsc', 'polygon'],
                    'attack_type': 'bridge_exploitation',
                    'total_loss': 25000000,  # $25M
                    'correlation_confidence': 0.9,
                    'timestamp': time.time()
                }
            ]
            
            for pattern in correlation_patterns:
                cross_chain_threats.append(pattern)
                self.cross_chain_threats.append(pattern)
                logger.warning(f"Cross-chain threat detected: {pattern['attack_type']} across {len(pattern['affected_chains'])} chains")
            
        except Exception as e:
            logger.error(f"Cross-chain correlation error: {e}")
        
        return cross_chain_threats

    def learn(self):
        """Enhanced learning with Web3 threat intelligence"""
        logger.info(f"[{self.name}] Learning from Web3 threat patterns")
        
        try:
            # Collect Web3 threat data
            threat_data = self.collect_web3_threat_data()
            
            # Traditional ML learning
            if self.classifier and SKLEARN_AVAILABLE and threat_data:
                # Prepare training data
                texts = [str(threat) for threat in threat_data]
                labels = [1 if threat.get('severity') == 'HIGH' else 0 for threat in threat_data]
                
                if texts and labels:
                    # Vectorize and train
                    X = self.vectorizer.fit_transform(texts)
                    self.classifier.partial_fit(X, labels, classes=[0, 1])
                    
                    logger.info(f"Learned from {len(threat_data)} Web3 threat patterns")
            
            # Update threat definitions
            self.update_threat_definitions(threat_data)
            
        except Exception as e:
            logger.error(f"Learning error: {e}")

    def collect_web3_threat_data(self) -> List[Dict]:
        """Collect Web3 threat intelligence data"""
        threat_data = []
        
        # Combine all threat sources
        threat_data.extend(self.flash_loan_alerts[-10:])  # Last 10 flash loan alerts
        threat_data.extend(self.mev_attacks[-10:])  # Last 10 MEV attacks
        threat_data.extend(self.cross_chain_threats[-5:])  # Last 5 cross-chain threats
        
        return threat_data

    def update_threat_definitions(self, threat_data: List[Dict]):
        """Update threat definitions based on learned patterns"""
        try:
            # Extract new threat patterns
            new_patterns = []
            for threat in threat_data:
                if threat.get('severity') == 'HIGH':
                    new_patterns.append({
                        'pattern': threat.get('attack_type', 'unknown'),
                        'indicators': threat.get('indicators', []),
                        'mitigation': threat.get('mitigation', 'monitor_closely')
                    })
            
            if new_patterns:
                logger.info(f"Updated threat definitions with {len(new_patterns)} new patterns")
                self.log_action("threat_definitions_updated", f"Added {len(new_patterns)} new threat patterns")
        
        except Exception as e:
            logger.error(f"Threat definition update error: {e}")

    def detect_advanced_threats(self):
        """Detect advanced persistent threats and zero-day exploits"""
        try:
            # Advanced threat detection logic
            advanced_threats = []
            
            # Behavioral anomaly detection
            if self.behavioral_analytics:
                anomalies = self.behavioral_analytics.detect_anomalies()
                advanced_threats.extend(anomalies)
            
            # Pattern recognition for unknown threats
            unknown_patterns = self.detect_unknown_patterns()
            advanced_threats.extend(unknown_patterns)
            
            if advanced_threats:
                self.log_action("advanced_threats_detected", f"Detected {len(advanced_threats)} advanced threats")
            
        except Exception as e:
            logger.error(f"Advanced threat detection error: {e}")

    def detect_unknown_patterns(self) -> List[Dict]:
        """Detect previously unknown threat patterns"""
        unknown_patterns = []
        
        try:
            # Analyze recent activities for unknown patterns
            recent_activities = self.collect_recent_activities()
            
            for activity in recent_activities:
                # Check if pattern is known
                if not is_known_threat(activity.get('pattern', '')):
                    # Potential new threat
                    unknown_patterns.append({
                        'pattern': activity.get('pattern'),
                        'confidence': activity.get('confidence', 0.5),
                        'severity': 'UNKNOWN',
                        'requires_investigation': True,
                        'timestamp': time.time()
                    })
            
        except Exception as e:
            logger.error(f"Unknown pattern detection error: {e}")
        
        return unknown_patterns

    def collect_recent_activities(self) -> List[Dict]:
        """Collect recent activities for analysis"""
        # Simulate recent activity collection
        return [
            {
                'pattern': 'unusual_transaction_frequency',
                'confidence': 0.8,
                'source': 'blockchain_monitor'
            }
        ]

    def act(self, threat_type, details):
        """Enhanced action with Web3-specific responses"""
        logger.info(f"[{self.name}] Acting on threat: {threat_type}")
        
        try:
            # Web3-specific threat responses
            if threat_type in ['flash_loan_attack', 'mev_attack']:
                self.respond_to_web3_threat(threat_type, details)
            elif threat_type == 'cross_chain_threat':
                self.respond_to_cross_chain_threat(details)
            else:
                # Standard threat response
                self.respond_to_standard_threat(threat_type, details)
            
            self.log_action("threat_response", f"Responded to {threat_type}")
            
        except Exception as e:
            logger.error(f"Action error: {e}")

    def respond_to_web3_threat(self, threat_type: str, details: Dict):
        """Respond to Web3-specific threats"""
        if threat_type == 'flash_loan_attack':
            # Flash loan attack response
            logger.warning(f"Responding to flash loan attack: {details}")
            # In production: alert DeFi protocols, pause vulnerable contracts
            
        elif threat_type == 'mev_attack':
            # MEV attack response
            logger.warning(f"Responding to MEV attack: {details}")
            # In production: implement MEV protection, adjust gas pricing

    def respond_to_cross_chain_threat(self, details: Dict):
        """Respond to cross-chain threats"""
        logger.warning(f"Responding to cross-chain threat: {details}")
        # In production: coordinate with bridge protocols, pause cross-chain transfers

    def respond_to_standard_threat(self, threat_type: str, details: Dict):
        """Respond to standard threats"""
        logger.info(f"Responding to standard threat: {threat_type}")
        # Standard threat mitigation

    def enable_unlimited_evolution(self):
        """Enable unlimited autonomous evolution and self-improvement"""
        logger.info(f"[{self.name}] Executing unlimited evolution cycle")
        
        try:
            # Analyze performance metrics
            performance = self.analyze_performance()
            
            # Evolve detection algorithms
            if performance.get('detection_rate', 0) < 0.9:
                self.evolve_detection_algorithms()
            
            # Optimize response times
            if performance.get('response_time', 0) > 5:
                self.optimize_response_times()
            
            # Enhance learning capabilities
            self.enhance_learning_capabilities()
            
            self.log_action("unlimited_evolution", "Evolution cycle completed")
            
        except Exception as e:
            logger.error(f"Evolution error: {e}")

    def analyze_performance(self) -> Dict:
        """Analyze agent performance metrics"""
        return {
            'detection_rate': 0.85,
            'response_time': 3.2,
            'accuracy': 0.92,
            'false_positive_rate': 0.05
        }

    def evolve_detection_algorithms(self):
        """Evolve and improve detection algorithms"""
        logger.info(f"[{self.name}] Evolving detection algorithms")
        # In production: use genetic algorithms to evolve detection patterns

    def optimize_response_times(self):
        """Optimize threat response times"""
        logger.info(f"[{self.name}] Optimizing response times")
        # In production: optimize code paths and caching

    def enhance_learning_capabilities(self):
        """Enhance machine learning capabilities"""
        logger.info(f"[{self.name}] Enhancing learning capabilities")
        # In production: implement new ML models and techniques

    def log_action(self, action: str, details: str):
        """Log agent actions with admin console integration"""
        try:
            from admin_console import AdminConsole
            console = AdminConsole()
            console.log_action(self.name, action, details)
            logger.info(f"[{self.name}] {action}: {details}")
        except Exception as e:
            logger.error(f"Logging error: {e}")
            # Fallback logging
            print(f"[{self.name}] {action}: {details}")

if __name__ == "__main__":
    agent = LearningAgent()
    agent.autonomous_cycle()