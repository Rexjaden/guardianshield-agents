"""
dmer_blockchain_registry.py: Blockchain-based decentralized threat intelligence registry
Implements smart contract integration for immutable threat data storage and sharing
"""

import json
import time
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

try:
    from web3 import Web3
    from eth_account import Account
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    print("Warning: web3.py not available, blockchain features disabled")

logger = logging.getLogger(__name__)

class DMERBlockchainRegistry:
    """Decentralized threat intelligence registry using blockchain"""
    
    def __init__(self, rpc_url: str = None, private_key: str = None, contract_address: str = None):
        self.rpc_url = rpc_url or "https://rpc.ankr.com/eth"
        self.private_key = private_key
        self.contract_address = contract_address
        self.w3 = None
        self.account = None
        self.contract = None
        
        # Threat data cache
        self.threat_cache = {}
        self.reputation_scores = {}
        self.consensus_threshold = 3  # Number of confirmations needed
        
        if WEB3_AVAILABLE:
            self._initialize_web3()
        
        # DMER Smart Contract ABI (simplified)
        self.contract_abi = [
            {
                "inputs": [
                    {"name": "_threatHash", "type": "bytes32"},
                    {"name": "_threatData", "type": "string"},
                    {"name": "_severity", "type": "uint8"},
                    {"name": "_confidence", "type": "uint256"}
                ],
                "name": "reportThreat",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"name": "_threatHash", "type": "bytes32"}],
                "name": "getThreat",
                "outputs": [
                    {"name": "threatData", "type": "string"},
                    {"name": "severity", "type": "uint8"},
                    {"name": "confidence", "type": "uint256"},
                    {"name": "confirmations", "type": "uint256"},
                    {"name": "timestamp", "type": "uint256"}
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [{"name": "_threatHash", "type": "bytes32"}],
                "name": "confirmThreat",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
        
    def _initialize_web3(self):
        """Initialize Web3 connection and account"""
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            
            if self.w3.is_connected():
                logger.info("Connected to Ethereum network")
                
                if self.private_key:
                    self.account = Account.from_key(self.private_key)
                    logger.info(f"Initialized account: {self.account.address}")
                
                if self.contract_address and self.account:
                    self.contract = self.w3.eth.contract(
                        address=self.contract_address,
                        abi=self.contract_abi
                    )
                    logger.info("DMER smart contract initialized")
            else:
                logger.warning("Failed to connect to Ethereum network")
                
        except Exception as e:
            logger.error(f"Error initializing Web3: {e}")
    
    def generate_threat_hash(self, threat_data: Dict) -> str:
        """Generate unique hash for threat data"""
        # Create deterministic hash from key threat attributes
        threat_string = json.dumps({
            'type': threat_data.get('type', ''),
            'target': threat_data.get('target', ''),
            'pattern': threat_data.get('pattern', ''),
            'source': threat_data.get('source', '')
        }, sort_keys=True)
        
        return hashlib.sha256(threat_string.encode()).hexdigest()
    
    def report_threat_to_blockchain(self, threat_data: Dict) -> Optional[str]:
        """Report threat to blockchain registry"""
        if not self.contract or not self.account:
            logger.warning("Blockchain not available, storing locally")
            return self._store_local_threat(threat_data)
        
        try:
            threat_hash = self.generate_threat_hash(threat_data)
            
            # Prepare transaction data
            severity_map = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
            severity = severity_map.get(threat_data.get('severity', 'medium'), 2)
            confidence = int(threat_data.get('confidence', 0.5) * 100)
            
            # Build transaction
            transaction = self.contract.functions.reportThreat(
                Web3.keccak(text=threat_hash),
                json.dumps(threat_data),
                severity,
                confidence
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            # Sign and send transaction
            signed_txn = self.account.sign_transaction(transaction)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            logger.info(f"Threat reported to blockchain: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Error reporting to blockchain: {e}")
            return self._store_local_threat(threat_data)
    
    def _store_local_threat(self, threat_data: Dict) -> str:
        """Store threat locally when blockchain is unavailable"""
        threat_hash = self.generate_threat_hash(threat_data)
        
        self.threat_cache[threat_hash] = {
            **threat_data,
            'timestamp': time.time(),
            'confirmations': 1,
            'local_storage': True
        }
        
        logger.info(f"Threat stored locally: {threat_hash}")
        return threat_hash
    
    def get_threat_from_blockchain(self, threat_hash: str) -> Optional[Dict]:
        """Retrieve threat data from blockchain"""
        if not self.contract:
            return self.threat_cache.get(threat_hash)
        
        try:
            threat_bytes = Web3.keccak(text=threat_hash)
            result = self.contract.functions.getThreat(threat_bytes).call()
            
            if result[0]:  # threatData exists
                return {
                    'data': json.loads(result[0]),
                    'severity': ['', 'low', 'medium', 'high', 'critical'][result[1]],
                    'confidence': result[2] / 100.0,
                    'confirmations': result[3],
                    'timestamp': result[4],
                    'blockchain_verified': True
                }
                
        except Exception as e:
            logger.error(f"Error retrieving from blockchain: {e}")
            return self.threat_cache.get(threat_hash)
        
        return None
    
    def confirm_threat(self, threat_hash: str) -> bool:
        """Confirm a threat to increase its reputation"""
        if not self.contract or not self.account:
            # Local confirmation
            if threat_hash in self.threat_cache:
                self.threat_cache[threat_hash]['confirmations'] += 1
                return True
            return False
        
        try:
            threat_bytes = Web3.keccak(text=threat_hash)
            
            transaction = self.contract.functions.confirmThreat(
                threat_bytes
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            signed_txn = self.account.sign_transaction(transaction)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            logger.info(f"Threat confirmed on blockchain: {tx_hash.hex()}")
            return True
            
        except Exception as e:
            logger.error(f"Error confirming threat: {e}")
            return False
    
    def query_consensus_threats(self, min_confirmations: int = None) -> List[Dict]:
        """Query threats that have reached consensus threshold"""
        min_confirmations = min_confirmations or self.consensus_threshold
        consensus_threats = []
        
        # Check blockchain threats (simplified - would need event filtering in real implementation)
        for threat_hash, threat_data in self.threat_cache.items():
            if threat_data.get('confirmations', 0) >= min_confirmations:
                consensus_threats.append({
                    'hash': threat_hash,
                    'data': threat_data,
                    'consensus_level': threat_data['confirmations'] / min_confirmations
                })
        
        return sorted(consensus_threats, key=lambda x: x['consensus_level'], reverse=True)
    
    def calculate_reputation_score(self, reporter_address: str) -> float:
        """Calculate reputation score for threat reporter"""
        if reporter_address not in self.reputation_scores:
            self.reputation_scores[reporter_address] = {
                'total_reports': 0,
                'confirmed_reports': 0,
                'false_positives': 0,
                'reputation': 0.5  # Start with neutral reputation
            }
        
        stats = self.reputation_scores[reporter_address]
        
        if stats['total_reports'] == 0:
            return 0.5
        
        accuracy = stats['confirmed_reports'] / stats['total_reports']
        false_positive_rate = stats['false_positives'] / stats['total_reports']
        
        # Calculate reputation (0.0 to 1.0)
        reputation = max(0.0, min(1.0, accuracy - (false_positive_rate * 0.5)))
        
        self.reputation_scores[reporter_address]['reputation'] = reputation
        return reputation
    
    def update_reporter_reputation(self, reporter_address: str, confirmed: bool, false_positive: bool = False):
        """Update reputation score for a reporter"""
        if reporter_address not in self.reputation_scores:
            self.reputation_scores[reporter_address] = {
                'total_reports': 0,
                'confirmed_reports': 0,
                'false_positives': 0,
                'reputation': 0.5
            }
        
        stats = self.reputation_scores[reporter_address]
        stats['total_reports'] += 1
        
        if confirmed:
            stats['confirmed_reports'] += 1
        
        if false_positive:
            stats['false_positives'] += 1
        
        # Recalculate reputation
        self.calculate_reputation_score(reporter_address)
    
    def get_network_threat_intelligence(self) -> Dict:
        """Get aggregated threat intelligence from the network"""
        try:
            consensus_threats = self.query_consensus_threats()
            
            # Aggregate statistics
            severity_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
            threat_types = {}
            total_confirmations = 0
            
            for threat in consensus_threats:
                severity = threat['data'].get('severity', 'medium')
                threat_type = threat['data'].get('type', 'unknown')
                
                severity_counts[severity] += 1
                threat_types[threat_type] = threat_types.get(threat_type, 0) + 1
                total_confirmations += threat['data'].get('confirmations', 0)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'total_consensus_threats': len(consensus_threats),
                'severity_distribution': severity_counts,
                'threat_type_distribution': threat_types,
                'average_confirmations': total_confirmations / len(consensus_threats) if consensus_threats else 0,
                'network_health': self._calculate_network_health(),
                'top_threats': consensus_threats[:10]  # Top 10 by consensus
            }
            
        except Exception as e:
            logger.error(f"Error getting network intelligence: {e}")
            return {'error': str(e)}
    
    def _calculate_network_health(self) -> Dict:
        """Calculate overall network health metrics"""
        try:
            total_threats = len(self.threat_cache)
            consensus_threats = len(self.query_consensus_threats())
            
            # Calculate health score (0.0 to 1.0)
            if total_threats == 0:
                consensus_ratio = 1.0
            else:
                consensus_ratio = consensus_threats / total_threats
            
            # Network is healthier when more threats reach consensus
            health_score = min(1.0, consensus_ratio * 2)  # Scale to make it more meaningful
            
            return {
                'health_score': health_score,
                'consensus_ratio': consensus_ratio,
                'total_reporters': len(self.reputation_scores),
                'average_reputation': sum(
                    stats['reputation'] for stats in self.reputation_scores.values()
                ) / len(self.reputation_scores) if self.reputation_scores else 0.5
            }
            
        except Exception as e:
            logger.error(f"Error calculating network health: {e}")
            return {'health_score': 0.0, 'error': str(e)}
    
    def sync_with_network(self) -> Dict:
        """Synchronize local cache with blockchain network"""
        try:
            if not self.contract:
                return {'status': 'offline', 'message': 'Blockchain not available'}
            
            # In a real implementation, this would:
            # 1. Query recent events from the smart contract
            # 2. Update local cache with new threats
            # 3. Verify threat confirmations
            # 4. Update reputation scores
            
            sync_result = {
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'threats_synced': len(self.threat_cache),
                'confirmations_updated': 0,
                'reputation_updates': 0
            }
            
            logger.info("Network sync completed successfully")
            return sync_result
            
        except Exception as e:
            logger.error(f"Error syncing with network: {e}")
            return {'status': 'error', 'message': str(e)}

# Enhanced DMER integration
class EnhancedDMERSystem:
    """Complete DMER system with blockchain integration"""
    
    def __init__(self, blockchain_config: Dict = None):
        from agents.dmer_monitor_agent import DmerMonitorAgent
        
        # Initialize components
        self.monitor_agent = DmerMonitorAgent()
        
        # Initialize blockchain registry if config provided
        self.blockchain_registry = None
        if blockchain_config and WEB3_AVAILABLE:
            self.blockchain_registry = DMERBlockchainRegistry(
                rpc_url=blockchain_config.get('rpc_url'),
                private_key=blockchain_config.get('private_key'),
                contract_address=blockchain_config.get('contract_address')
            )
        
        logger.info("Enhanced DMER system initialized")
    
    def process_threat_intelligence(self, threat_data: Dict) -> Dict:
        """Process threat through complete DMER pipeline"""
        try:
            # 1. Run through ML classifier
            ml_result = self.monitor_agent._analyze_with_ml()
            
            # 2. Pattern matching
            pattern_matches = self.monitor_agent._pattern_match_threats()
            
            # 3. Store in blockchain if available
            blockchain_hash = None
            if self.blockchain_registry:
                blockchain_hash = self.blockchain_registry.report_threat_to_blockchain(threat_data)
            
            # 4. Execute response protocols
            self.monitor_agent._execute_threat_response([threat_data])
            
            return {
                'status': 'processed',
                'ml_analysis': ml_result,
                'pattern_matches': pattern_matches,
                'blockchain_hash': blockchain_hash,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing threat intelligence: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_comprehensive_report(self) -> Dict:
        """Generate comprehensive threat intelligence report"""
        try:
            # Agent monitoring report
            agent_report = self.monitor_agent._generate_realtime_report()
            
            # Network intelligence
            network_intel = {}
            if self.blockchain_registry:
                network_intel = self.blockchain_registry.get_network_threat_intelligence()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'agent_status': agent_report,
                'network_intelligence': network_intel,
                'system_health': 'optimal',
                'blockchain_enabled': self.blockchain_registry is not None
            }
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            return {'error': str(e)}