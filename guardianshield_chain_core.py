#!/usr/bin/env python3
"""
GuardianShield Chain - Core Blockchain Client
The foundation of the GuardianShield blockchain network
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import threading
import socket
import struct

@dataclass
class Transaction:
    """GuardianShield Chain transaction structure"""
    from_address: str
    to_address: str
    amount: float
    fee: float
    timestamp: float
    signature: str
    security_score: Optional[float] = None  # AI security assessment
    threat_flags: Optional[List[str]] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def hash(self) -> str:
        """Generate transaction hash"""
        tx_string = f"{self.from_address}{self.to_address}{self.amount}{self.fee}{self.timestamp}"
        return hashlib.sha256(tx_string.encode()).hexdigest()
    
    def validate_security(self) -> bool:
        """Validate transaction using AI security checks"""
        # Placeholder for AI security validation
        if self.threat_flags:
            return len(self.threat_flags) == 0
        return True

@dataclass
class Block:
    """GuardianShield Chain block structure"""
    index: int
    timestamp: float
    transactions: List[Transaction]
    previous_hash: str
    nonce: int
    validator_address: str
    security_attestation: Dict[str, Any]  # AI security validation
    merkle_root: str
    stake_proof: Dict[str, Any]  # Proof of Guardian Stake data
    
    def calculate_merkle_root(self) -> str:
        """Calculate Merkle root of transactions"""
        if not self.transactions:
            return hashlib.sha256("".encode()).hexdigest()
        
        tx_hashes = [tx.hash() for tx in self.transactions]
        
        while len(tx_hashes) > 1:
            if len(tx_hashes) % 2 == 1:
                tx_hashes.append(tx_hashes[-1])
            
            next_level = []
            for i in range(0, len(tx_hashes), 2):
                combined = tx_hashes[i] + tx_hashes[i + 1]
                next_level.append(hashlib.sha256(combined.encode()).hexdigest())
            
            tx_hashes = next_level
        
        return tx_hashes[0]
    
    def hash(self) -> str:
        """Generate block hash"""
        block_string = f"{self.index}{self.timestamp}{self.previous_hash}{self.merkle_root}{self.nonce}{self.validator_address}"
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def to_dict(self) -> Dict:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "validator_address": self.validator_address,
            "security_attestation": self.security_attestation,
            "merkle_root": self.merkle_root,
            "stake_proof": self.stake_proof,
            "hash": self.hash()
        }

class ProofOfGuardianStake:
    """Proof of Guardian Stake consensus mechanism"""
    
    def __init__(self):
        self.validators = {}  # address -> stake_amount
        self.security_scores = {}  # address -> security_contribution_score
        self.slashing_conditions = [
            "double_signing",
            "extended_downtime",
            "malicious_behavior",
            "failed_security_validation"
        ]
    
    def add_validator(self, address: str, stake: float, security_score: float = 0.0):
        """Add a validator to the network"""
        self.validators[address] = stake
        self.security_scores[address] = security_score
    
    def calculate_validator_weight(self, address: str) -> float:
        """Calculate validator selection weight based on stake + security score"""
        base_stake = self.validators.get(address, 0)
        security_bonus = self.security_scores.get(address, 0) * 0.5  # 50% bonus for security
        return base_stake + security_bonus
    
    def select_validator(self, previous_hash: str) -> Optional[str]:
        """Select next block validator using weighted random selection"""
        if not self.validators:
            return None
        
        # Use previous block hash as randomness source
        random_seed = int(previous_hash[:8], 16)
        
        total_weight = sum(self.calculate_validator_weight(addr) for addr in self.validators)
        if total_weight == 0:
            return None
        
        selection_point = (random_seed % int(total_weight * 1000)) / 1000
        current_weight = 0
        
        for address in self.validators:
            current_weight += self.calculate_validator_weight(address)
            if current_weight >= selection_point:
                return address
        
        return list(self.validators.keys())[0]  # Fallback
    
    def validate_block(self, block: Block) -> bool:
        """Validate block according to PoGS rules"""
        # Check if validator has sufficient stake
        validator_stake = self.validators.get(block.validator_address, 0)
        min_stake_required = 10000  # Minimum GSHIELD stake
        
        if validator_stake < min_stake_required:
            return False
        
        # Validate security attestation
        if not block.security_attestation or not self._validate_security_attestation(block):
            return False
        
        return True
    
    def _validate_security_attestation(self, block: Block) -> bool:
        """Validate the security attestation from AI agents"""
        attestation = block.security_attestation
        
        # Check required fields
        required_fields = ["threat_scan_complete", "malicious_tx_count", "security_score"]
        for field in required_fields:
            if field not in attestation:
                return False
        
        # Security score must be above threshold
        if attestation["security_score"] < 0.8:
            return False
        
        return True

class GuardianShieldNode:
    """Core GuardianShield Chain node implementation"""
    
    def __init__(self, node_id: str, node_type: str = "validator"):
        self.node_id = node_id
        self.node_type = node_type  # genesis, validator, bridge, governance
        self.blockchain = []
        self.mempool = []  # Pending transactions
        self.consensus = ProofOfGuardianStake()
        self.peers = []
        self.is_running = False
        self.mining_active = False
        
        # Node-specific configurations
        self.stake_amount = self._get_stake_requirement()
        self.security_integration = True
        
        # Network configuration
        self.host = "0.0.0.0"
        self.port = 8333 + hash(node_id) % 1000  # Dynamic port assignment
        
        print(f"🚀 GuardianShield {node_type.title()} Node initialized: {node_id}")
        print(f"   Stake Requirement: {self.stake_amount:,} GSHIELD")
        print(f"   Network Port: {self.port}")
    
    def _get_stake_requirement(self) -> int:
        """Get stake requirement based on node type"""
        stakes = {
            "genesis": 100000,
            "validator": 50000,
            "bridge": 25000,
            "governance": 10000
        }
        return stakes.get(self.node_type, 50000)
    
    def create_genesis_block(self) -> Block:
        """Create the genesis block"""
        genesis_tx = Transaction(
            from_address="genesis",
            to_address="treasury",
            amount=1000000000,  # 1B GSHIELD initial supply
            fee=0,
            timestamp=time.time(),
            signature="genesis_signature",
            security_score=1.0,
            threat_flags=[]
        )
        
        genesis_block = Block(
            index=0,
            timestamp=time.time(),
            transactions=[genesis_tx],
            previous_hash="0" * 64,
            nonce=0,
            validator_address="genesis_validator",
            security_attestation={
                "threat_scan_complete": True,
                "malicious_tx_count": 0,
                "security_score": 1.0,
                "ai_agents_consensus": True
            },
            merkle_root="",
            stake_proof={
                "validator_stake": self.stake_amount,
                "security_contribution": 0,
                "governance_weight": 1
            }
        )
        
        genesis_block.merkle_root = genesis_block.calculate_merkle_root()
        return genesis_block
    
    def add_transaction(self, transaction: Transaction) -> bool:
        """Add transaction to mempool after validation"""
        # Validate transaction security
        if not transaction.validate_security():
            print(f"⚠️  Transaction rejected due to security concerns")
            return False
        
        # AI security assessment (placeholder)
        security_assessment = self._assess_transaction_security(transaction)
        transaction.security_score = security_assessment["score"]
        transaction.threat_flags = security_assessment["threats"]
        
        if security_assessment["score"] > 0.7:  # Security threshold
            self.mempool.append(transaction)
            print(f"✅ Transaction added to mempool: {transaction.hash()[:8]}...")
            return True
        else:
            print(f"❌ Transaction rejected by AI security: {security_assessment['threats']}")
            return False
    
    def _assess_transaction_security(self, tx: Transaction) -> Dict:
        """AI-powered transaction security assessment"""
        # Placeholder for actual AI security integration
        threats = []
        score = 0.9  # Default high score
        
        # Check for suspicious patterns
        if tx.amount > 1000000:  # Large transaction
            threats.append("large_amount")
            score -= 0.1
        
        if tx.fee < tx.amount * 0.001:  # Suspiciously low fee
            threats.append("low_fee")
            score -= 0.05
        
        return {
            "score": max(0, score),
            "threats": threats,
            "ai_confidence": 0.95
        }
    
    def create_block(self) -> Optional[Block]:
        """Create a new block from mempool transactions"""
        if not self.mempool:
            return None
        
        # Select transactions from mempool (up to 1000 per block)
        selected_txs = self.mempool[:1000]
        
        # Get previous block
        previous_block = self.blockchain[-1] if self.blockchain else None
        previous_hash = previous_block.hash() if previous_block else "0" * 64
        
        # AI security validation for the entire block
        security_attestation = self._validate_block_security(selected_txs)
        
        new_block = Block(
            index=len(self.blockchain),
            timestamp=time.time(),
            transactions=selected_txs,
            previous_hash=previous_hash,
            nonce=0,  # Will be set during mining
            validator_address=self.node_id,
            security_attestation=security_attestation,
            merkle_root="",
            stake_proof={
                "validator_stake": self.stake_amount,
                "security_contribution": len([tx for tx in selected_txs if tx.security_score > 0.9]),
                "governance_weight": 1 if self.node_type == "governance" else 0
            }
        )
        
        new_block.merkle_root = new_block.calculate_merkle_root()
        return new_block
    
    def _validate_block_security(self, transactions: List[Transaction]) -> Dict:
        """AI security validation for block of transactions"""
        total_score = sum(tx.security_score or 0.5 for tx in transactions) / len(transactions) if transactions else 1.0
        malicious_count = len([tx for tx in transactions if (tx.threat_flags and len(tx.threat_flags) > 0)])
        
        return {
            "threat_scan_complete": True,
            "malicious_tx_count": malicious_count,
            "security_score": total_score,
            "ai_agents_consensus": total_score > 0.8,
            "scan_timestamp": time.time()
        }
    
    def mine_block(self, block: Block, target_difficulty: int = 4) -> bool:
        """Simple proof-of-work mining for block finalization"""
        target = "0" * target_difficulty
        
        for nonce in range(1000000):  # Limit mining attempts
            block.nonce = nonce
            block_hash = block.hash()
            
            if block_hash.startswith(target):
                print(f"⛏️  Block mined! Hash: {block_hash}")
                return True
        
        return False
    
    def add_block(self, block: Block) -> bool:
        """Add block to blockchain after validation"""
        # Validate block using consensus mechanism
        if not self.consensus.validate_block(block):
            print(f"❌ Block validation failed")
            return False
        
        # Add block to chain
        self.blockchain.append(block)
        
        # Remove mined transactions from mempool
        mined_tx_hashes = {tx.hash() for tx in block.transactions}
        self.mempool = [tx for tx in self.mempool if tx.hash() not in mined_tx_hashes]
        
        print(f"✅ Block #{block.index} added to blockchain")
        print(f"   Transactions: {len(block.transactions)}")
        print(f"   Security Score: {block.security_attestation['security_score']:.2f}")
        print(f"   Validator: {block.validator_address}")
        
        return True
    
    async def start_node(self):
        """Start the blockchain node"""
        print(f"🌟 Starting GuardianShield {self.node_type.title()} Node...")
        
        # Initialize with genesis block if first node
        if not self.blockchain:
            genesis = self.create_genesis_block()
            self.blockchain.append(genesis)
            print(f"🏆 Genesis block created: {genesis.hash()[:8]}...")
        
        self.is_running = True
        
        # Start mining/validation loop
        if self.node_type in ["genesis", "validator"]:
            await self.start_mining()
    
    async def start_mining(self):
        """Start the mining/validation process"""
        print(f"⛏️  Starting {self.node_type} mining process...")
        self.mining_active = True
        
        while self.is_running:
            if self.mempool:
                # Create new block
                new_block = self.create_block()
                if new_block:
                    # Mine the block
                    if self.mine_block(new_block):
                        # Add to blockchain
                        self.add_block(new_block)
            
            await asyncio.sleep(3)  # 3-second block time
    
    def get_chain_info(self) -> Dict:
        """Get blockchain status information"""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "chain_length": len(self.blockchain),
            "mempool_size": len(self.mempool),
            "stake_amount": self.stake_amount,
            "is_mining": self.mining_active,
            "latest_block_hash": self.blockchain[-1].hash()[:8] if self.blockchain else None,
            "total_transactions": sum(len(block.transactions) for block in self.blockchain),
            "security_integration": self.security_integration
        }

class GuardianShieldNetwork:
    """GuardianShield Chain network manager"""
    
    def __init__(self):
        self.nodes = {}
        self.network_stats = {
            "total_nodes": 0,
            "genesis_miners": 0,
            "validator_miners": 0,
            "bridge_miners": 0,
            "governance_miners": 0,
            "total_blocks": 0,
            "total_transactions": 0,
            "network_hash_rate": "0 H/s",
            "security_score": 0.0
        }
    
    def create_node(self, node_id: str, node_type: str) -> GuardianShieldNode:
        """Create a new network node"""
        node = GuardianShieldNode(node_id, node_type)
        self.nodes[node_id] = node
        self.network_stats["total_nodes"] += 1
        self.network_stats[f"{node_type}_miners"] += 1
        
        # Add validator to consensus mechanism
        node.consensus.add_validator(node_id, node.stake_amount)
        
        return node
    
    async def start_network(self, node_configs: List[Dict]):
        """Start the GuardianShield network with multiple nodes"""
        print("🌐 Starting GuardianShield Chain Network...")
        print("=" * 50)
        
        # Create nodes
        tasks = []
        for config in node_configs:
            node = self.create_node(config["id"], config["type"])
            tasks.append(asyncio.create_task(node.start_node()))
        
        print(f"✅ Network started with {len(self.nodes)} nodes")
        
        # Run all nodes concurrently
        await asyncio.gather(*tasks)
    
    def get_network_status(self) -> Dict:
        """Get comprehensive network status"""
        if not self.nodes:
            return self.network_stats
        
        # Update stats from active nodes
        total_blocks = max(len(node.blockchain) for node in self.nodes.values())
        total_transactions = sum(
            sum(len(block.transactions) for block in node.blockchain)
            for node in self.nodes.values()
        ) // len(self.nodes)  # Average to avoid double counting
        
        avg_security_score = sum(
            node.blockchain[-1].security_attestation.get("security_score", 0)
            for node in self.nodes.values() if node.blockchain
        ) / len([n for n in self.nodes.values() if n.blockchain])
        
        self.network_stats.update({
            "total_blocks": total_blocks,
            "total_transactions": total_transactions,
            "security_score": avg_security_score,
            "active_nodes": len([n for n in self.nodes.values() if n.is_running]),
            "mining_nodes": len([n for n in self.nodes.values() if n.mining_active])
        })
        
        return self.network_stats

# Example usage and testing
async def launch_guardianshield_testnet():
    """Launch a small GuardianShield testnet"""
    network = GuardianShieldNetwork()
    
    # Define initial node configuration
    initial_nodes = [
        {"id": "genesis_1", "type": "genesis"},
        {"id": "validator_1", "type": "validator"},
        {"id": "validator_2", "type": "validator"},
        {"id": "bridge_1", "type": "bridge"},
        {"id": "governance_1", "type": "governance"}
    ]
    
    print("🚀 Launching GuardianShield Chain Testnet...")
    
    # Start network (this would run indefinitely in production)
    try:
        await asyncio.wait_for(network.start_network(initial_nodes), timeout=30)
    except asyncio.TimeoutError:
        print("\n⏰ Testnet demo completed (30 seconds)")
        
        # Show final network status
        status = network.get_network_status()
        print("\n📊 Network Status:")
        print("=" * 30)
        for key, value in status.items():
            print(f"{key.replace('_', ' ').title()}: {value}")

if __name__ == "__main__":
    asyncio.run(launch_guardianshield_testnet())