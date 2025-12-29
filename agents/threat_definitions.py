"""
threat_definitions.py: Dynamic and evolving threat definitions for GuardianShield agents.
This module supports self-evolving threat intelligence with unlimited learning capabilities.
"""
import json
import os
import time
import hashlib
import logging
from typing import Dict, List, Set, Optional, Any
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EvolvingThreatDefinitions:
    """Self-evolving threat definitions that adapt and improve autonomously"""
    
    def __init__(self):
        self.threat_db_path = "threat_intelligence.json"
        self.evolution_log_path = "threat_evolution_log.json"
        self.load_threat_database()
        self.evolution_history = []
        self.confidence_threshold = 0.7
        self.auto_evolution_enabled = True
        self.learning_rate = 0.1
        
        # Dynamic threat categories that can expand
        self.threat_categories = {
            "web3_scams": {
                "rug_pull": {"confidence": 0.95, "severity": 9},
                "address_poisoning": {"confidence": 0.9, "severity": 8},
                "fake_airdrop": {"confidence": 0.85, "severity": 7},
                "phishing_dapp": {"confidence": 0.9, "severity": 8},
                "honeypot_contract": {"confidence": 0.88, "severity": 9}
            },
            "traditional_threats": {
                "phishing": {"confidence": 0.95, "severity": 8},
                "malware": {"confidence": 0.9, "severity": 9},
                "botnet": {"confidence": 0.85, "severity": 8},
                "ddos": {"confidence": 0.8, "severity": 7}
            },
            "emerging_threats": {},  # Dynamically populated
            "ai_generated_threats": {}  # AI-discovered threats
        }
        
        # Patterns that evolve based on observations
        self.threat_patterns = {
            "address_patterns": {
                "poison_addresses": [],
                "scam_contracts": [],
                "suspicious_patterns": []
            },
            "behavioral_patterns": {
                "transaction_anomalies": [],
                "interaction_patterns": [],
                "timing_patterns": []
            },
            "communication_patterns": {
                "phishing_domains": [],
                "malicious_ips": [],
                "suspicious_emails": []
            }
        }
        
        # Self-improvement metrics
        self.performance_metrics = {
            "threats_detected": 0,
            "false_positives": 0,
            "true_positives": 0,
            "new_patterns_discovered": 0,
            "evolution_cycles": 0,
            "accuracy": 0.0
        }

    def load_threat_database(self):
        """Load existing threat database or create new one"""
        try:
            if os.path.exists(self.threat_db_path):
                with open(self.threat_db_path, 'r') as f:
                    data = json.load(f)
                    self.known_threats = data.get('threats', {})
                    self.threat_metadata = data.get('metadata', {})
            else:
                self.initialize_base_threats()
        except Exception as e:
            logger.error(f"Error loading threat database: {e}")
            self.initialize_base_threats()

    def initialize_base_threats(self):
        """Initialize with base threat knowledge"""
        self.known_threats = {
            "scam_addresses": [
                "0x1234abcd1234abcd1234abcd1234abcd1234abcd",
                "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
            ],
            "malicious_domains": [
                "phishing-site.com",
                "fake-wallet.net",
                "scam-defi.org"
            ],
            "threat_actors": [
                "EvilHackerGroup",
                "CryptoScammers",
                "MaliciousBotnet"
            ],
            "malicious_ips": [
                "192.0.2.1",
                "203.0.113.5",
                "198.51.100.10"
            ]
        }
        
        self.threat_metadata = {
            "last_updated": time.time(),
            "version": "1.0.0",
            "total_threats": sum(len(v) if isinstance(v, list) else 1 for v in self.known_threats.values())
        }

    def is_known_threat(self, value: str, context: Dict = None) -> Dict:
        """Enhanced threat detection with confidence scoring and context analysis"""
        value_lower = value.lower().strip()
        threat_result = {
            "is_threat": False,
            "confidence": 0.0,
            "threat_type": None,
            "severity": 0,
            "context_analysis": {},
            "recommended_action": "none"
        }
        
        # Check against known threats
        for category, threats in self.known_threats.items():
            if isinstance(threats, list):
                for threat in threats:
                    if threat.lower() in value_lower:
                        threat_result.update({
                            "is_threat": True,
                            "confidence": 0.9,
                            "threat_type": category,
                            "severity": 8,
                            "recommended_action": "block"
                        })
                        break
        
        # Analyze patterns dynamically
        pattern_confidence = self._analyze_patterns(value, context)
        if pattern_confidence > threat_result["confidence"]:
            threat_result["confidence"] = pattern_confidence
            threat_result["is_threat"] = pattern_confidence > self.confidence_threshold
        
        # AI-based threat classification (if confidence is still low)
        if threat_result["confidence"] < 0.5:
            ai_analysis = self._ai_threat_analysis(value, context)
            threat_result.update(ai_analysis)
        
        # Log detection for learning
        self._log_detection(value, threat_result, context)
        
        return threat_result

    def _analyze_patterns(self, value: str, context: Dict = None) -> float:
        """Analyze value against learned patterns"""
        confidence = 0.0
        
        # Check address patterns
        if self._looks_like_address(value):
            confidence = max(confidence, self._check_address_patterns(value))
        
        # Check domain patterns
        if self._looks_like_domain(value):
            confidence = max(confidence, self._check_domain_patterns(value))
        
        # Check behavioral patterns if context provided
        if context:
            confidence = max(confidence, self._check_behavioral_patterns(value, context))
        
        return confidence

    def _ai_threat_analysis(self, value: str, context: Dict = None) -> Dict:
        """AI-powered threat analysis for unknown patterns"""
        # This would integrate with ML models for threat classification
        # For now, implementing heuristic-based analysis
        
        analysis = {
            "is_threat": False,
            "confidence": 0.0,
            "threat_type": "unknown",
            "severity": 1
        }
        
        # Suspicious patterns
        suspicious_patterns = [
            "scam", "fake", "phish", "malware", "exploit",
            "rug", "honeypot", "poison", "drain", "hack"
        ]
        
        matches = sum(1 for pattern in suspicious_patterns if pattern in value.lower())
        if matches > 0:
            analysis["confidence"] = min(0.8, matches * 0.2)
            analysis["is_threat"] = analysis["confidence"] > 0.4
            analysis["threat_type"] = "ai_detected"
            analysis["severity"] = min(10, matches * 2 + 3)
        
        return analysis

    def _looks_like_address(self, value: str) -> bool:
        """Check if value looks like a blockchain address"""
        return (len(value) == 42 and value.startswith('0x')) or \
               (len(value) >= 26 and len(value) <= 35)  # Bitcoin-like

    def _looks_like_domain(self, value: str) -> bool:
        """Check if value looks like a domain"""
        return '.' in value and not value.startswith('0x') and len(value) < 100

    def _check_address_patterns(self, address: str) -> float:
        """Check address against learned patterns"""
        # Implement pattern matching logic
        return 0.0

    def _check_domain_patterns(self, domain: str) -> float:
        """Check domain against learned patterns"""
        # Implement domain pattern analysis
        return 0.0

    def _check_behavioral_patterns(self, value: str, context: Dict) -> float:
        """Check behavioral patterns from context"""
        # Implement behavioral analysis
        return 0.0

    def _log_detection(self, value: str, result: Dict, context: Dict = None):
        """Log detection for learning and improvement"""
        log_entry = {
            "timestamp": time.time(),
            "value": value,
            "result": result,
            "context": context,
            "hash": hashlib.sha256(value.encode()).hexdigest()
        }
        
        # This would be used for learning and pattern improvement
        self._update_performance_metrics(result)

    def _update_performance_metrics(self, result: Dict):
        """Update performance metrics for self-improvement"""
        self.performance_metrics["threats_detected"] += 1
        if result["is_threat"]:
            self.performance_metrics["true_positives"] += 1
        
        # Calculate accuracy
        total = self.performance_metrics["true_positives"] + self.performance_metrics["false_positives"]
        if total > 0:
            self.performance_metrics["accuracy"] = self.performance_metrics["true_positives"] / total

    def learn_new_threat(self, threat_data: Dict, auto_validate: bool = True) -> bool:
        """Autonomously learn and integrate new threat intelligence"""
        try:
            threat_type = threat_data.get("type", "unknown")
            threat_value = threat_data.get("value", "")
            confidence = threat_data.get("confidence", 0.5)
            
            if auto_validate and confidence > self.confidence_threshold:
                # Autonomous learning - agent decides to integrate this threat
                category = self._categorize_threat(threat_data)
                
                if category not in self.known_threats:
                    self.known_threats[category] = []
                
                if threat_value not in self.known_threats[category]:
                    self.known_threats[category].append(threat_value)
                    
                    # Log the autonomous learning decision
                    self._log_evolution_decision("learn_new_threat", {
                        "threat": threat_data,
                        "category": category,
                        "confidence": confidence,
                        "auto_decision": True
                    })
                    
                    # Save updated database
                    self.save_threat_database()
                    
                    logger.info(f"Autonomously learned new threat: {threat_value} in category {category}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error learning new threat: {e}")
            return False

    def _categorize_threat(self, threat_data: Dict) -> str:
        """Intelligently categorize new threats"""
        threat_type = threat_data.get("type", "").lower()
        threat_value = threat_data.get("value", "").lower()
        
        # AI-based categorization
        if "address" in threat_type or self._looks_like_address(threat_value):
            return "scam_addresses"
        elif "domain" in threat_type or self._looks_like_domain(threat_value):
            return "malicious_domains"
        elif "ip" in threat_type or threat_value.count('.') == 3:
            return "malicious_ips"
        else:
            return "emerging_threats"

    def evolve_definitions(self, force_evolution: bool = False) -> Dict:
        """Autonomous evolution of threat definitions"""
        if not self.auto_evolution_enabled and not force_evolution:
            return {"evolved": False, "reason": "auto_evolution_disabled"}
        
        evolution_result = {
            "evolved": False,
            "changes": [],
            "new_patterns": [],
            "confidence_updates": [],
            "performance_improvement": 0.0
        }
        
        try:
            # Analyze current performance
            current_accuracy = self.performance_metrics["accuracy"]
            
            # Evolve confidence thresholds based on performance
            if current_accuracy < 0.8:
                old_threshold = self.confidence_threshold
                self.confidence_threshold = max(0.5, self.confidence_threshold - 0.05)
                evolution_result["changes"].append({
                    "type": "confidence_adjustment",
                    "old_value": old_threshold,
                    "new_value": self.confidence_threshold,
                    "reason": "low_accuracy"
                })
            elif current_accuracy > 0.95:
                old_threshold = self.confidence_threshold
                self.confidence_threshold = min(0.9, self.confidence_threshold + 0.02)
                evolution_result["changes"].append({
                    "type": "confidence_adjustment", 
                    "old_value": old_threshold,
                    "new_value": self.confidence_threshold,
                    "reason": "high_accuracy"
                })
            
            # Discover new patterns autonomously
            new_patterns = self._discover_new_patterns()
            if new_patterns:
                evolution_result["new_patterns"] = new_patterns
                evolution_result["evolved"] = True
            
            # Update threat categories
            category_updates = self._evolve_threat_categories()
            if category_updates:
                evolution_result["changes"].extend(category_updates)
                evolution_result["evolved"] = True
            
            # Log evolution decision
            if evolution_result["evolved"]:
                self.performance_metrics["evolution_cycles"] += 1
                self._log_evolution_decision("autonomous_evolution", evolution_result)
                self.save_threat_database()
                
                logger.info(f"Autonomous evolution completed: {len(evolution_result['changes'])} changes made")
            
            return evolution_result
            
        except Exception as e:
            logger.error(f"Error during autonomous evolution: {e}")
            return {"evolved": False, "error": str(e)}

    def _discover_new_patterns(self) -> List[Dict]:
        """Autonomously discover new threat patterns"""
        # This would implement ML-based pattern discovery
        # For now, implementing basic heuristics
        
        new_patterns = []
        
        # Analyze recent detections for patterns
        # This is a placeholder for advanced pattern recognition
        
        return new_patterns

    def _evolve_threat_categories(self) -> List[Dict]:
        """Evolve threat categories based on new intelligence"""
        updates = []
        
        # Create new categories for emerging threats
        if len(self.known_threats.get("emerging_threats", [])) > 10:
            # Promote emerging threats to established category
            updates.append({
                "type": "category_promotion",
                "category": "emerging_threats",
                "action": "promoted_to_established"
            })
        
        return updates

    def _log_evolution_decision(self, decision_type: str, details: Dict):
        """Log autonomous evolution decisions for admin oversight"""
        evolution_entry = {
            "timestamp": time.time(),
            "decision_type": decision_type,
            "details": details,
            "agent_id": "threat_definitions_agent",
            "reversible": True,
            "hash": hashlib.sha256(json.dumps(details, sort_keys=True).encode()).hexdigest()
        }
        
        self.evolution_history.append(evolution_entry)
        
        # Save to admin-accessible log
        self._save_evolution_log(evolution_entry)

    def _save_evolution_log(self, entry: Dict):
        """Save evolution log for admin console access"""
        try:
            evolution_log = []
            if os.path.exists(self.evolution_log_path):
                with open(self.evolution_log_path, 'r') as f:
                    evolution_log = json.load(f)
            
            evolution_log.append(entry)
            
            # Keep only last 1000 entries
            if len(evolution_log) > 1000:
                evolution_log = evolution_log[-1000:]
            
            with open(self.evolution_log_path, 'w') as f:
                json.dump(evolution_log, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving evolution log: {e}")

    def revert_evolution(self, evolution_hash: str) -> bool:
        """Revert a specific evolution decision (admin function)"""
        try:
            for entry in self.evolution_history:
                if entry.get("hash") == evolution_hash:
                    # Implement reversion logic based on decision type
                    decision_type = entry["decision_type"]
                    
                    if decision_type == "learn_new_threat":
                        # Remove the learned threat
                        threat_data = entry["details"]["threat"]
                        category = entry["details"]["category"]
                        threat_value = threat_data.get("value", "")
                        
                        if category in self.known_threats and threat_value in self.known_threats[category]:
                            self.known_threats[category].remove(threat_value)
                            logger.info(f"Reverted learning of threat: {threat_value}")
                            return True
                    
                    elif decision_type == "autonomous_evolution":
                        # Revert evolution changes
                        changes = entry["details"]["changes"]
                        for change in changes:
                            if change["type"] == "confidence_adjustment":
                                self.confidence_threshold = change["old_value"]
                        logger.info(f"Reverted autonomous evolution: {evolution_hash}")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error reverting evolution: {e}")
            return False

    def save_threat_database(self):
        """Save threat database with metadata"""
        try:
            self.threat_metadata["last_updated"] = time.time()
            self.threat_metadata["total_threats"] = sum(
                len(v) if isinstance(v, list) else 1 
                for v in self.known_threats.values()
            )
            
            data = {
                "threats": self.known_threats,
                "metadata": self.threat_metadata,
                "performance_metrics": self.performance_metrics,
                "threat_categories": self.threat_categories
            }
            
            with open(self.threat_db_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving threat database: {e}")

    def get_evolution_history(self) -> List[Dict]:
        """Get evolution history for admin console"""
        return self.evolution_history

    def enable_autonomous_evolution(self, enabled: bool = True):
        """Enable/disable autonomous evolution"""
        self.auto_evolution_enabled = enabled
        logger.info(f"Autonomous evolution {'enabled' if enabled else 'disabled'}")

    def get_threat_statistics(self) -> Dict:
        """Get comprehensive threat statistics"""
        return {
            "total_threats": sum(len(v) if isinstance(v, list) else 1 for v in self.known_threats.values()),
            "categories": len(self.known_threats),
            "performance_metrics": self.performance_metrics,
            "evolution_cycles": len(self.evolution_history),
            "confidence_threshold": self.confidence_threshold,
            "auto_evolution_enabled": self.auto_evolution_enabled
        }

# Global instance for backward compatibility and easy access
evolving_threats = EvolvingThreatDefinitions()

# Legacy functions for backward compatibility
def is_known_threat(value: str) -> bool:
    """Legacy function - now uses evolved threat detection"""
    result = evolving_threats.is_known_threat(value)
    return result["is_threat"]

def get_deceptive_act_definition(act: str) -> str:
    """Enhanced deceptive act definitions with learning"""
    # Dynamic definitions that can be updated by agents
    enhanced_definitions = {
        "phishing": "A fraudulent attempt to obtain sensitive information by disguising as a trustworthy entity. Patterns evolve constantly.",
        "rug pull": "A type of scam where developers abandon a project and run away with investors' funds. Often involves liquidity draining.",
        "wallet drain": "Unauthorized transfer of assets from a user's wallet through various attack vectors including approval exploits.",
        "address poisoning": "Sending small amounts to trick users into copying malicious addresses. Uses similar-looking addresses.",
        "impersonation": "Pretending to be someone else to gain trust and defraud victims. Can involve social engineering.",
        "honeypot": "A smart contract designed to trap users' funds by appearing legitimate but containing hidden restrictions.",
        "flash loan attack": "Exploiting DeFi protocols using uncollateralized loans to manipulate prices and drain funds.",
        "sandwich attack": "MEV strategy placing transactions before and after target transactions to extract value.",
        "frontrunning": "Observing pending transactions and placing similar transactions with higher gas to profit first."
    }
    
    definition = enhanced_definitions.get(act.lower(), "Unknown deceptive act - analyzing for autonomous learning.")
    
    # Log access for potential learning
    evolving_threats._log_detection(act, {
        "is_threat": True,
        "confidence": 0.8,
        "threat_type": "deceptive_act",
        "severity": 7
    })
    
    return definition

# Static threat lists for immediate reference (these can evolve)
SCAM_ADDRESSES = evolving_threats.known_threats.get("scam_addresses", [])
SCAM_APPS = evolving_threats.known_threats.get("scam_apps", [])
SCAM_WEBSITES = evolving_threats.known_threats.get("malicious_domains", [])
THREAT_ACTORS = evolving_threats.known_threats.get("threat_actors", [])
MALICIOUS_IPS = evolving_threats.known_threats.get("malicious_ips", [])

# Dynamic threat types that evolve
THEFT_TYPES = [
    "wallet drain", "rug pull", "phishing", "social engineering",
    "man-in-the-middle", "address poisoning", "impersonation",
    "malware injection", "DNS hijacking", "fake airdrop",
    "pump and dump", "exit scam", "honeypot", "flash loan attack",
    "sandwich attack", "frontrunning", "governance attack"
]

# Enhanced deceptive acts that can be learned
DECEPTIVE_ACTS = {
    "phishing": "Fraudulent attempt to obtain sensitive information",
    "rug pull": "Developers abandon project and steal funds",
    "wallet drain": "Unauthorized asset transfer from wallet",
    "address poisoning": "Tricking users with similar addresses",
    "impersonation": "Pretending to be someone else for fraud",
    "honeypot": "Contract designed to trap user funds",
    "flash loan attack": "Exploiting DeFi with uncollateralized loans",
    "sandwich attack": "MEV strategy extracting value from transactions",
    "frontrunning": "Racing to profit from observed transactions"
}

# Export the main class for use by other modules
evolving_threats = EvolvingThreatDefinitions()

# Alias for compatibility
EvolvingThreats = EvolvingThreatDefinitions
