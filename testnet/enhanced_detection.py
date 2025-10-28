# Enhanced ERC-8055 Threat Detection Engine
import json
import time
import hashlib
import statistics
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
from collections import defaultdict, deque

@dataclass 
class TransactionPattern:
    timestamp: float
    from_address: str
    to_address: str
    token_id: int
    amount: float
    gas_price: float
    transaction_hash: str

@dataclass
class ThreatIndicator:
    indicator_type: str
    severity: float  # 0-1 scale
    confidence: float  # 0-1 scale
    description: str
    evidence: Dict[str, Any]

class AdvancedThreatDetector:
    def __init__(self):
        # Threat intelligence databases
        self.known_malicious_addresses = set([
            "0x1234567890123456789012345678901234567890",
            "0x0000000000000000000000000000000000000000", 
            "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
            "0x000000000000000000000000000000000000dead",
        ])
        
        self.mixer_addresses = set([
            "0x2e8c5dc9b7ff6d4bb6f6c5b5c1bc6b5b3b5c1bc6",  # Tornado Cash
            "0x1234567890abcdef1234567890abcdef12345678",  # Other mixers
        ])
        
        self.exchange_addresses = set([
            "0x3e8c5dc9b7ff6d4bb6f6c5b5c1bc6b5b3b5c1bc7",  # Binance
            "0x4e8c5dc9b7ff6d4bb6f6c5b5c1bc6b5b3b5c1bc8",  # Coinbase
        ])
        
        # Pattern tracking
        self.transaction_history = deque(maxlen=10000)  # Last 10k transactions
        self.address_patterns = defaultdict(list)  # Address -> transaction patterns
        self.token_movement_chains = defaultdict(list)  # Token ID -> movement history
        
        # ML-like pattern recognition
        self.suspicious_patterns = {
            "rapid_fire_transfers": {"threshold": 5, "time_window": 300},  # 5 transfers in 5 minutes
            "round_number_amounts": {"threshold": 0.8},  # 80% round numbers indicates bot
            "gas_price_anomalies": {"std_dev_threshold": 2.5},
            "time_pattern_regularity": {"variance_threshold": 0.1},
        }
        
        # Advanced detection algorithms
        self.detection_algorithms = [
            self.detect_private_key_compromise,
            self.detect_smart_contract_exploits,
            self.detect_social_engineering,
            self.detect_exchange_exploits,
            self.detect_money_laundering,
            self.detect_mev_attacks,
            self.detect_insider_threats,
            self.detect_coordinated_attacks,
            self.detect_zero_day_exploits,
        ]
    
    def analyze_transaction(self, pattern: TransactionPattern) -> List[ThreatIndicator]:
        """Comprehensive transaction analysis using multiple detection algorithms"""
        threats = []
        
        # Add to history
        self.transaction_history.append(pattern)
        self.address_patterns[pattern.from_address].append(pattern)
        self.token_movement_chains[pattern.token_id].append(pattern)
        
        # Run all detection algorithms
        for algorithm in self.detection_algorithms:
            try:
                threat_indicators = algorithm(pattern)
                threats.extend(threat_indicators)
            except Exception as e:
                print(f"Detection algorithm {algorithm.__name__} failed: {e}")
        
        return threats
    
    def detect_private_key_compromise(self, pattern: TransactionPattern) -> List[ThreatIndicator]:
        """Detect signs of private key compromise"""
        threats = []
        
        # Check for immediate transfers to known bad addresses
        if pattern.to_address.lower() in [addr.lower() for addr in self.known_malicious_addresses]:
            threats.append(ThreatIndicator(
                indicator_type="private_key_compromise",
                severity=0.9,
                confidence=0.95,
                description="Transfer to known malicious address",
                evidence={"malicious_address": pattern.to_address}
            ))
        
        # Check for unusual gas prices (hackers often overpay to ensure fast execution)
        recent_transactions = list(self.transaction_history)[-50:]
        if recent_transactions:
            avg_gas = statistics.mean([t.gas_price for t in recent_transactions])
            if pattern.gas_price > avg_gas * 3:  # 3x higher than average
                threats.append(ThreatIndicator(
                    indicator_type="private_key_compromise", 
                    severity=0.6,
                    confidence=0.7,
                    description="Unusually high gas price suggesting urgency",
                    evidence={"gas_price": pattern.gas_price, "average": avg_gas}
                ))
        
        # Check for rapid succession of transfers from same address
        address_history = self.address_patterns[pattern.from_address]
        if len(address_history) >= 3:
            recent_transfers = [t for t in address_history[-5:] 
                             if pattern.timestamp - t.timestamp < 600]  # 10 minutes
            if len(recent_transfers) >= 3:
                threats.append(ThreatIndicator(
                    indicator_type="private_key_compromise",
                    severity=0.8,
                    confidence=0.8,
                    description="Rapid successive transfers from compromised address",
                    evidence={"transfer_count": len(recent_transfers), "time_window": 600}
                ))
        
        return threats
    
    def detect_smart_contract_exploits(self, pattern: TransactionPattern) -> List[ThreatIndicator]:
        """Detect smart contract exploitation patterns"""
        threats = []
        
        # Check for contract interaction patterns
        if self._is_contract_address(pattern.to_address):
            # Look for repeated interactions (potential reentrancy)
            contract_interactions = [t for t in self.transaction_history 
                                   if t.to_address == pattern.to_address and 
                                   pattern.timestamp - t.timestamp < 60]  # 1 minute
            
            if len(contract_interactions) > 10:  # More than 10 interactions per minute
                threats.append(ThreatIndicator(
                    indicator_type="smart_contract_exploit",
                    severity=0.85,
                    confidence=0.8,
                    description="Potential reentrancy attack detected",
                    evidence={"interaction_count": len(contract_interactions)}
                ))
        
        # Check for flash loan patterns (large amounts, same block return)
        if pattern.amount > 1000000:  # Large amount threshold
            threats.append(ThreatIndicator(
                indicator_type="smart_contract_exploit",
                severity=0.7,
                confidence=0.6,
                description="Large transaction potentially involving flash loans",
                evidence={"amount": pattern.amount}
            ))
        
        return threats
    
    def detect_social_engineering(self, pattern: TransactionPattern) -> List[ThreatIndicator]:
        """Detect social engineering attack patterns"""
        threats = []
        
        # Check for approval-related transactions to suspicious addresses
        if pattern.to_address.lower() in [addr.lower() for addr in self.known_malicious_addresses]:
            threats.append(ThreatIndicator(
                indicator_type="social_engineering",
                severity=0.75,
                confidence=0.9,
                description="Potential phishing approval to malicious contract",
                evidence={"suspicious_address": pattern.to_address}
            ))
        
        # Check for unusual approval amounts (unlimited approvals are suspicious)
        if pattern.amount == float('inf') or pattern.amount > 10**18:
            threats.append(ThreatIndicator(
                indicator_type="social_engineering",
                severity=0.6,
                confidence=0.7,
                description="Unlimited or very large approval amount",
                evidence={"approval_amount": pattern.amount}
            ))
        
        return threats
    
    def detect_exchange_exploits(self, pattern: TransactionPattern) -> List[ThreatIndicator]:
        """Detect exchange-related exploitation"""
        threats = []
        
        # Check for mass withdrawals from exchange addresses
        if pattern.from_address.lower() in [addr.lower() for addr in self.exchange_addresses]:
            recent_withdrawals = [t for t in self.transaction_history
                                if t.from_address == pattern.from_address and
                                pattern.timestamp - t.timestamp < 3600]  # 1 hour
            
            if len(recent_withdrawals) > 100:  # Mass withdrawal
                threats.append(ThreatIndicator(
                    indicator_type="exchange_exploit",
                    severity=0.9,
                    confidence=0.85,
                    description="Mass withdrawal pattern from exchange",
                    evidence={"withdrawal_count": len(recent_withdrawals)}
                ))
        
        return threats
    
    def detect_money_laundering(self, pattern: TransactionPattern) -> List[ThreatIndicator]:
        """Detect money laundering patterns"""
        threats = []
        
        # Check for mixer usage
        if pattern.to_address.lower() in [addr.lower() for addr in self.mixer_addresses]:
            threats.append(ThreatIndicator(
                indicator_type="money_laundering",
                severity=0.8,
                confidence=0.9,
                description="Transaction to known crypto mixer",
                evidence={"mixer_address": pattern.to_address}
            ))
        
        # Check for layered transactions (multiple hops)
        token_chain = self.token_movement_chains[pattern.token_id]
        if len(token_chain) > 5:  # More than 5 hops
            unique_addresses = set([t.to_address for t in token_chain])
            if len(unique_addresses) == len(token_chain):  # Each hop to different address
                threats.append(ThreatIndicator(
                    indicator_type="money_laundering",
                    severity=0.7,
                    confidence=0.75,
                    description="Layered transaction pattern suggesting laundering",
                    evidence={"hop_count": len(token_chain)}
                ))
        
        return threats
    
    def detect_mev_attacks(self, pattern: TransactionPattern) -> List[ThreatIndicator]:
        """Detect MEV (Maximum Extractable Value) attacks"""
        threats = []
        
        # Check for sandwich attack patterns (high gas, quick succession)
        if pattern.gas_price > 100:  # High gas price
            similar_gas_transactions = [t for t in self.transaction_history[-10:]
                                      if abs(t.gas_price - pattern.gas_price) < 10 and
                                      abs(t.timestamp - pattern.timestamp) < 30]
            
            if len(similar_gas_transactions) >= 3:
                threats.append(ThreatIndicator(
                    indicator_type="mev_attack",
                    severity=0.6,
                    confidence=0.7,
                    description="Potential sandwich attack pattern",
                    evidence={"high_gas_transactions": len(similar_gas_transactions)}
                ))
        
        return threats
    
    def detect_insider_threats(self, pattern: TransactionPattern) -> List[ThreatIndicator]:
        """Detect insider threat patterns"""
        threats = []
        
        # Check for gradual extraction patterns
        address_history = self.address_patterns[pattern.from_address]
        if len(address_history) > 20:  # Sufficient history
            amounts = [t.amount for t in address_history[-20:]]
            if all(amount < 1000 for amount in amounts):  # Small amounts
                time_intervals = [address_history[i].timestamp - address_history[i-1].timestamp 
                                for i in range(1, len(address_history))]
                if statistics.variance(time_intervals) < 3600:  # Regular intervals
                    threats.append(ThreatIndicator(
                        indicator_type="insider_threat",
                        severity=0.65,
                        confidence=0.6,
                        description="Regular small withdrawals suggesting insider theft",
                        evidence={"pattern_regularity": statistics.variance(time_intervals)}
                    ))
        
        return threats
    
    def detect_coordinated_attacks(self, pattern: TransactionPattern) -> List[ThreatIndicator]:
        """Detect coordinated attack patterns"""
        threats = []
        
        # Check for simultaneous transactions from multiple addresses
        similar_time_transactions = [t for t in self.transaction_history
                                   if abs(t.timestamp - pattern.timestamp) < 60 and
                                   t.from_address != pattern.from_address]
        
        if len(similar_time_transactions) > 10:  # Many simultaneous transactions
            unique_addresses = set([t.from_address for t in similar_time_transactions])
            if len(unique_addresses) > 5:  # From different addresses
                threats.append(ThreatIndicator(
                    indicator_type="coordinated_attack",
                    severity=0.8,
                    confidence=0.75,
                    description="Coordinated attack from multiple addresses",
                    evidence={"simultaneous_count": len(similar_time_transactions)}
                ))
        
        return threats
    
    def detect_zero_day_exploits(self, pattern: TransactionPattern) -> List[ThreatIndicator]:
        """Detect novel/zero-day exploitation patterns"""
        threats = []
        
        # Check for anomalous patterns that don't fit known categories
        anomaly_score = self._calculate_anomaly_score(pattern)
        
        if anomaly_score > 0.8:  # High anomaly
            threats.append(ThreatIndicator(
                indicator_type="zero_day_exploit",
                severity=0.7,
                confidence=0.5,  # Lower confidence for unknown patterns
                description="Anomalous transaction pattern suggesting novel exploit",
                evidence={"anomaly_score": anomaly_score}
            ))
        
        return threats
    
    def _is_contract_address(self, address: str) -> bool:
        """Check if address is a contract (simplified)"""
        # In real implementation, check if address has code
        return len(address) == 42 and address.startswith('0x')
    
    def _calculate_anomaly_score(self, pattern: TransactionPattern) -> float:
        """Calculate anomaly score for unknown patterns"""
        score = 0.0
        
        # Check against historical patterns
        if len(self.transaction_history) > 100:
            recent_amounts = [t.amount for t in self.transaction_history[-100:]]
            recent_gas = [t.gas_price for t in self.transaction_history[-100:]]
            
            # Amount anomaly
            avg_amount = statistics.mean(recent_amounts)
            if pattern.amount > avg_amount * 10:  # 10x larger than average
                score += 0.3
            
            # Gas price anomaly  
            avg_gas = statistics.mean(recent_gas)
            if pattern.gas_price > avg_gas * 5:  # 5x higher than average
                score += 0.3
            
            # Time pattern anomaly
            time_intervals = []
            for i in range(1, min(len(self.transaction_history), 50)):
                interval = self.transaction_history[-i].timestamp - self.transaction_history[-i-1].timestamp
                time_intervals.append(interval)
            
            if time_intervals:
                avg_interval = statistics.mean(time_intervals)
                if avg_interval > 0:
                    current_interval = pattern.timestamp - self.transaction_history[-1].timestamp
                    if current_interval < avg_interval / 10:  # Much faster than usual
                        score += 0.4
        
        return min(1.0, score)
    
    def assess_overall_threat_level(self, threats: List[ThreatIndicator]) -> Tuple[float, str]:
        """Assess overall threat level from multiple indicators"""
        if not threats:
            return 0.0, "NO_THREAT"
        
        # Calculate weighted threat score
        total_score = 0.0
        total_weight = 0.0
        
        for threat in threats:
            weight = threat.confidence
            score = threat.severity * weight
            total_score += score
            total_weight += weight
        
        if total_weight == 0:
            return 0.0, "NO_THREAT"
        
        overall_score = total_score / total_weight
        
        # Determine threat level
        if overall_score >= 0.8:
            return overall_score, "CRITICAL"
        elif overall_score >= 0.6:
            return overall_score, "HIGH"
        elif overall_score >= 0.4:
            return overall_score, "MEDIUM"
        elif overall_score >= 0.2:
            return overall_score, "LOW"
        else:
            return overall_score, "MINIMAL"

# Integration with adversarial testing
class EnhancedAdversarialTester:
    def __init__(self):
        self.threat_detector = AdvancedThreatDetector()
        
    def test_detection_against_attack(self, attack_scenario, attack_steps) -> Dict[str, Any]:
        """Test enhanced detection against specific attack"""
        detection_results = []
        
        for step in attack_steps:
            # Convert attack step to transaction pattern
            pattern = self._attack_step_to_pattern(step)
            
            # Run enhanced detection
            threats = self.threat_detector.analyze_transaction(pattern)
            overall_score, threat_level = self.threat_detector.assess_overall_threat_level(threats)
            
            detection_results.append({
                "step": step,
                "threats_detected": len(threats),
                "threat_score": overall_score,
                "threat_level": threat_level,
                "should_burn": threat_level in ["CRITICAL", "HIGH"]
            })
        
        return {
            "attack_scenario": attack_scenario,
            "detection_results": detection_results,
            "max_threat_score": max([r["threat_score"] for r in detection_results]),
            "would_neutralize": any([r["should_burn"] for r in detection_results])
        }
    
    def _attack_step_to_pattern(self, step: Dict[str, Any]) -> TransactionPattern:
        """Convert attack step to transaction pattern for analysis"""
        return TransactionPattern(
            timestamp=time.time(),
            from_address=step.get("from", "0x1111111111111111111111111111111111111111"),
            to_address=step.get("to", "0x2222222222222222222222222222222222222222"),
            token_id=step.get("token_id", 1),
            amount=step.get("amount", 1000),
            gas_price=step.get("gas_price", 20),
            transaction_hash=f"0x{step.get('action', 'unknown')}"
        )