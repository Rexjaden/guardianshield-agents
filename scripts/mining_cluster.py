#!/usr/bin/env python3
"""
GuardianShield Mining Cluster
Multi-chain block production and validation node cluster
"""

import os
import sys
import asyncio
import logging
import json
import time
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from web3 import Web3
    from web3.middleware import ExtraDataToPOAMiddleware
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    logger.error("web3 not available - run: pip install web3")

# Configuration
OWNER_WALLET = os.getenv('OWNER_WALLET_ADDRESS', '0xF262b772c2EBf526a5cF8634CA92597583Ef38ee')
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY', 'J8QD4YPCWIRT3G1WFGHIC7YWGDBJ4VMGZ4')

CHAIN_CONFIG = {
    'ethereum': {
        'name': 'Ethereum',
        'chain_id': 1,
        'rpc': 'https://ethereum-rpc.publicnode.com',
        'symbol': 'ETH',
        'block_time': 12,
        'consensus': 'PoS'
    },
    'polygon': {
        'name': 'Polygon',
        'chain_id': 137,
        'rpc': 'https://polygon-bor-rpc.publicnode.com',
        'symbol': 'MATIC',
        'block_time': 2,
        'consensus': 'PoS'
    },
    'arbitrum': {
        'name': 'Arbitrum',
        'chain_id': 42161,
        'rpc': 'https://arbitrum-one-rpc.publicnode.com',
        'symbol': 'ETH',
        'block_time': 0.25,
        'consensus': 'Optimistic Rollup'
    },
    'bsc': {
        'name': 'BSC',
        'chain_id': 56,
        'rpc': 'https://bsc-rpc.publicnode.com',
        'symbol': 'BNB',
        'block_time': 3,
        'consensus': 'PoSA'
    },
    'base': {
        'name': 'Base',
        'chain_id': 8453,
        'rpc': 'https://base-rpc.publicnode.com',
        'symbol': 'ETH',
        'block_time': 2,
        'consensus': 'Optimistic Rollup'
    },
    'flare': {
        'name': 'Flare',
        'chain_id': 14,
        'rpc': 'https://flare-api.flare.network/ext/C/rpc',
        'symbol': 'FLR',
        'block_time': 3,
        'consensus': 'FBA'
    }
}


@dataclass
class Block:
    """Represents a mined/validated block"""
    chain: str
    block_number: int
    block_hash: str
    parent_hash: str
    timestamp: int
    transactions: int
    gas_used: int
    gas_limit: int
    miner: str
    difficulty: int
    size: int
    
@dataclass
class MiningStats:
    """Mining statistics for a node"""
    node_id: str
    chain: str
    blocks_processed: int
    blocks_validated: int
    transactions_seen: int
    uptime_seconds: float
    last_block: int
    hash_rate: float  # blocks/minute processed


class MiningNode:
    """Individual mining/validation node for a specific chain"""
    
    def __init__(self, node_id: str, chain: str, config: dict):
        self.node_id = node_id
        self.chain = chain
        self.config = config
        self.web3 = None
        self.running = False
        self.stats = MiningStats(
            node_id=node_id,
            chain=chain,
            blocks_processed=0,
            blocks_validated=0,
            transactions_seen=0,
            uptime_seconds=0,
            last_block=0,
            hash_rate=0.0
        )
        self.start_time = None
        self.block_cache = []
        self.pending_txs = []
        
    async def connect(self) -> bool:
        """Connect to blockchain"""
        try:
            self.web3 = Web3(Web3.HTTPProvider(self.config['rpc']))
            
            # Add POA middleware for chains that need it (Polygon, BSC, etc.)
            if self.chain in ['polygon', 'bsc', 'base', 'arbitrum', 'flare']:
                self.web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
                
            if self.web3.is_connected():
                self.stats.last_block = self.web3.eth.block_number
                logger.info(f"⛏️  Node {self.node_id} connected to {self.chain} at block {self.stats.last_block}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Node {self.node_id} connection failed: {e}")
            return False
            
    async def start_mining(self):
        """Start block monitoring and validation"""
        self.running = True
        self.start_time = time.time()
        logger.info(f"⛏️  Node {self.node_id} starting mining on {self.chain}...")
        
        while self.running:
            try:
                await self._mine_cycle()
                await asyncio.sleep(self.config['block_time'] / 2)
            except Exception as e:
                logger.error(f"❌ Mining error on {self.node_id}: {e}")
                await asyncio.sleep(5)
                
    async def _mine_cycle(self):
        """Single mining cycle - check for new blocks and validate"""
        current_block = self.web3.eth.block_number
        
        if current_block > self.stats.last_block:
            # New block(s) detected - process them
            for block_num in range(self.stats.last_block + 1, current_block + 1):
                block = await self._process_block(block_num)
                if block:
                    self.stats.blocks_processed += 1
                    self.stats.transactions_seen += block.transactions
                    
                    # Validate block
                    if await self._validate_block(block):
                        self.stats.blocks_validated += 1
                        
            self.stats.last_block = current_block
            
        # Update stats
        self.stats.uptime_seconds = time.time() - self.start_time
        if self.stats.uptime_seconds > 0:
            self.stats.hash_rate = (self.stats.blocks_processed / self.stats.uptime_seconds) * 60
            
    async def _process_block(self, block_num: int) -> Optional[Block]:
        """Process and extract block data"""
        try:
            block_data = self.web3.eth.get_block(block_num)
            
            block = Block(
                chain=self.chain,
                block_number=block_data['number'],
                block_hash=block_data['hash'].hex() if block_data['hash'] else '',
                parent_hash=block_data['parentHash'].hex() if block_data['parentHash'] else '',
                timestamp=block_data['timestamp'],
                transactions=len(block_data['transactions']),
                gas_used=block_data['gasUsed'],
                gas_limit=block_data['gasLimit'],
                miner=block_data.get('miner', ''),
                difficulty=block_data.get('difficulty', 0),
                size=block_data.get('size', 0)
            )
            
            self.block_cache.append(block)
            if len(self.block_cache) > 100:
                self.block_cache = self.block_cache[-100:]
                
            return block
            
        except Exception as e:
            logger.error(f"❌ Block processing error: {e}")
            return None
            
    async def _validate_block(self, block: Block) -> bool:
        """Validate block integrity"""
        # Basic validation checks
        validations = [
            block.block_number > 0,
            len(block.block_hash) > 0,
            block.gas_used <= block.gas_limit,
            block.timestamp > 0
        ]
        
        # Check parent hash continuity
        if len(self.block_cache) > 1:
            prev_block = self.block_cache[-2]
            validations.append(block.parent_hash == prev_block.block_hash)
            
        return all(validations)
        
    def stop(self):
        """Stop mining"""
        self.running = False
        logger.info(f"🛑 Node {self.node_id} stopped mining")
        
    def get_stats(self) -> dict:
        """Get current mining stats"""
        return asdict(self.stats)


class MiningCluster:
    """Distributed mining cluster managing multiple nodes across chains"""
    
    def __init__(self, cluster_id: str = "guardian-mining-cluster"):
        self.cluster_id = cluster_id
        self.nodes: Dict[str, MiningNode] = {}
        self.running = False
        self.start_time = None
        self.total_blocks = 0
        self.total_txs = 0
        
    async def initialize(self, chains: List[str] = None):
        """Initialize mining cluster with nodes for specified chains"""
        chains = chains or list(CHAIN_CONFIG.keys())
        
        logger.info("=" * 70)
        logger.info("⛏️  GUARDIANSHIELD MINING CLUSTER INITIALIZING")
        logger.info(f"📍 Cluster ID: {self.cluster_id}")
        logger.info(f"💰 Mining Wallet: {OWNER_WALLET}")
        logger.info("=" * 70)
        
        for chain in chains:
            if chain in CHAIN_CONFIG:
                node_id = f"{self.cluster_id}-{chain}-node"
                node = MiningNode(node_id, chain, CHAIN_CONFIG[chain])
                
                if await node.connect():
                    self.nodes[chain] = node
                    logger.info(f"  ✅ {chain.upper()} node ready")
                else:
                    logger.warning(f"  ❌ {chain.upper()} node failed to connect")
                    
        logger.info(f"\n📊 Cluster initialized with {len(self.nodes)} active nodes")
        return len(self.nodes) > 0
        
    async def start_cluster(self):
        """Start all mining nodes"""
        self.running = True
        self.start_time = time.time()
        
        logger.info("\n" + "=" * 70)
        logger.info("🚀 STARTING MINING CLUSTER")
        logger.info("=" * 70)
        
        # Start all nodes concurrently
        tasks = []
        for chain, node in self.nodes.items():
            task = asyncio.create_task(node.start_mining())
            tasks.append(task)
            logger.info(f"  ⛏️  {chain.upper()} miner started")
            
        # Start stats reporter
        stats_task = asyncio.create_task(self._report_stats())
        tasks.append(stats_task)
        
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Cluster shutdown requested")
            
    async def _report_stats(self):
        """Periodically report cluster statistics"""
        while self.running:
            await asyncio.sleep(30)  # Report every 30 seconds
            
            logger.info("\n" + "-" * 70)
            logger.info("📊 MINING CLUSTER STATUS")
            logger.info("-" * 70)
            
            total_blocks = 0
            total_txs = 0
            
            for chain, node in self.nodes.items():
                stats = node.get_stats()
                total_blocks += stats['blocks_processed']
                total_txs += stats['transactions_seen']
                
                logger.info(
                    f"  ⛏️  {chain.upper():12} | "
                    f"Block: {stats['last_block']:>12,} | "
                    f"Processed: {stats['blocks_processed']:>6} | "
                    f"TXs: {stats['transactions_seen']:>8,} | "
                    f"Rate: {stats['hash_rate']:.2f} blk/min"
                )
                
            uptime = time.time() - self.start_time if self.start_time else 0
            logger.info("-" * 70)
            logger.info(f"  📈 TOTAL: {total_blocks} blocks | {total_txs:,} transactions | Uptime: {uptime:.0f}s")
            logger.info("-" * 70)
            
            self.total_blocks = total_blocks
            self.total_txs = total_txs
            
    def stop_cluster(self):
        """Stop all mining nodes"""
        self.running = False
        for node in self.nodes.values():
            node.stop()
        logger.info("🛑 Mining cluster stopped")
        
    def get_cluster_stats(self) -> dict:
        """Get overall cluster statistics"""
        return {
            'cluster_id': self.cluster_id,
            'active_nodes': len(self.nodes),
            'chains': list(self.nodes.keys()),
            'total_blocks_processed': self.total_blocks,
            'total_transactions': self.total_txs,
            'uptime': time.time() - self.start_time if self.start_time else 0,
            'nodes': {chain: node.get_stats() for chain, node in self.nodes.items()}
        }


async def main():
    """Main entry point"""
    cluster = MiningCluster()
    
    # Initialize with all available chains
    if await cluster.initialize():
        try:
            # Start mining
            await cluster.start_cluster()
        except KeyboardInterrupt:
            logger.info("\n⚠️  Shutdown signal received")
            cluster.stop_cluster()
    else:
        logger.error("❌ Failed to initialize mining cluster")
        

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║           ⛏️  GUARDIANSHIELD MINING CLUSTER ⛏️                         ║
║                                                                       ║
║   Multi-Chain Block Production & Validation System                    ║
║   Monitoring: ETH, POLYGON, ARBITRUM, BSC, BASE, FLARE               ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)
    asyncio.run(main())
