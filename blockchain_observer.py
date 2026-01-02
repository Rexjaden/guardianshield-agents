#!/usr/bin/env python3

"""
GuardianShield Blockchain Observer Service
Real-time blockchain monitoring, analytics, and indexing
"""

import asyncio
import json
import logging
import time
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import aiohttp
import asyncpg
import redis.asyncio as redis
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from web3 import Web3
import os

# Prometheus metrics
BLOCKS_PROCESSED = Counter('observer_blocks_processed_total', 'Total blocks processed')
TRANSACTIONS_INDEXED = Counter('observer_transactions_indexed_total', 'Total transactions indexed')
INDEXING_LATENCY = Histogram('observer_indexing_duration_seconds', 'Time spent indexing blocks')
CURRENT_BLOCK_HEIGHT = Gauge('observer_current_block_height', 'Current block height')
INDEXING_LAG = Gauge('observer_indexing_lag_blocks', 'Blocks behind current tip')
DATABASE_CONNECTIONS = Gauge('observer_db_connections_active', 'Active database connections')
CACHE_HIT_RATE = Gauge('observer_cache_hit_rate', 'Cache hit rate percentage')

@dataclass
class BlockData:
    height: int
    hash: str
    timestamp: int
    transaction_count: int
    size: int
    gas_used: Optional[int] = None
    gas_limit: Optional[int] = None
    proposer: Optional[str] = None
    
@dataclass
class TransactionData:
    hash: str
    block_height: int
    index_in_block: int
    from_address: str
    to_address: Optional[str]
    value: int
    gas: Optional[int] = None
    gas_price: Optional[int] = None
    status: int = 1
    timestamp: int = 0

class BlockchainObserver:
    def __init__(self, config_path: str = "/etc/guardian/observer.json"):
        self.config = self.load_config(config_path)
        self.running = False
        self.db_pool = None
        self.redis_client = None
        self.web3_client = None
        self.current_block = 0
        self.indexing_queue = asyncio.Queue(maxsize=1000)
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, self.config.get("log_level", "INFO").upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("BlockchainObserver")
        
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load observer configuration"""
        default_config = {
            "blockchain": {
                "rpc_url": "http://validator-us-east:26657",
                "websocket_url": "ws://validator-us-east:26657/websocket",
                "network_id": "guardian-mainnet",
                "start_block": 0
            },
            "database": {
                "host": "observer-postgres",
                "port": 5432,
                "database": "guardian_analytics",
                "username": "observer",
                "password": os.getenv("POSTGRES_PASSWORD", "observer123"),
                "max_connections": 20
            },
            "redis": {
                "host": "observer-redis",
                "port": 6379,
                "db": 0,
                "password": os.getenv("REDIS_PASSWORD", "redis123")
            },
            "indexing": {
                "batch_size": 100,
                "worker_count": 4,
                "max_retries": 3,
                "retry_delay": 5,
                "enable_transaction_indexing": True,
                "enable_state_indexing": False,
                "enable_event_indexing": True
            },
            "analytics": {
                "enable_real_time": True,
                "aggregation_intervals": [300, 3600, 86400],  # 5min, 1hour, 1day
                "cache_duration": 300
            },
            "monitoring": {
                "prometheus_port": 9090,
                "health_check_interval": 30
            }
        }
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults
                return self.deep_merge(default_config, config)
        except FileNotFoundError:
            self.logger.warning(f"Config file not found: {config_path}, using defaults")
            return default_config
    
    def deep_merge(self, dict1: Dict, dict2: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = dict1.copy()
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    async def initialize(self):
        """Initialize all connections and services"""
        self.logger.info("Initializing GuardianShield Blockchain Observer...")
        
        # Start Prometheus metrics server
        start_http_server(self.config["monitoring"]["prometheus_port"])
        self.logger.info(f"Prometheus metrics server started on port {self.config['monitoring']['prometheus_port']}")
        
        # Initialize database connection pool
        await self.init_database()
        
        # Initialize Redis connection
        await self.init_redis()
        
        # Initialize blockchain client
        await self.init_blockchain_client()
        
        # Setup database schema
        await self.setup_database_schema()
        
        # Get starting block height
        self.current_block = await self.get_last_indexed_block()
        
        self.logger.info("Observer initialization complete")
    
    async def init_database(self):
        """Initialize PostgreSQL connection pool"""
        db_config = self.config["database"]
        dsn = f"postgresql://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        
        try:
            self.db_pool = await asyncpg.create_pool(
                dsn,
                min_size=5,
                max_size=db_config["max_connections"],
                command_timeout=60
            )
            self.logger.info("Database connection pool established")
            DATABASE_CONNECTIONS.set(5)
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def init_redis(self):
        """Initialize Redis connection"""
        redis_config = self.config["redis"]
        self.redis_client = redis.Redis(
            host=redis_config["host"],
            port=redis_config["port"],
            db=redis_config["db"],
            password=redis_config.get("password"),
            decode_responses=True
        )
        
        try:
            await self.redis_client.ping()
            self.logger.info("Redis connection established")
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def init_blockchain_client(self):
        """Initialize blockchain RPC client"""
        blockchain_config = self.config["blockchain"]
        
        # Initialize Web3 client for Ethereum-compatible chains
        if blockchain_config["rpc_url"].startswith("http"):
            self.web3_client = Web3(Web3.HTTPProvider(blockchain_config["rpc_url"]))
            
            if self.web3_client.is_connected():
                self.logger.info("Web3 blockchain client connected")
            else:
                self.logger.warning("Web3 client connection failed, will retry")
    
    async def setup_database_schema(self):
        """Create database tables if they don't exist"""
        schema_sql = """
        -- Blocks table
        CREATE TABLE IF NOT EXISTS blocks (
            height BIGINT PRIMARY KEY,
            hash VARCHAR(64) UNIQUE NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            transaction_count INTEGER NOT NULL DEFAULT 0,
            size_bytes INTEGER NOT NULL DEFAULT 0,
            gas_used BIGINT DEFAULT 0,
            gas_limit BIGINT DEFAULT 0,
            proposer VARCHAR(64),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            INDEX (timestamp),
            INDEX (proposer)
        );
        
        -- Transactions table
        CREATE TABLE IF NOT EXISTS transactions (
            hash VARCHAR(64) PRIMARY KEY,
            block_height BIGINT NOT NULL REFERENCES blocks(height),
            index_in_block INTEGER NOT NULL,
            from_address VARCHAR(64) NOT NULL,
            to_address VARCHAR(64),
            value NUMERIC(78,0) NOT NULL DEFAULT 0,
            gas_limit BIGINT DEFAULT 0,
            gas_price BIGINT DEFAULT 0,
            gas_used BIGINT DEFAULT 0,
            status INTEGER NOT NULL DEFAULT 1,
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            INDEX (block_height),
            INDEX (from_address),
            INDEX (to_address),
            INDEX (timestamp)
        );
        
        -- Address analytics table
        CREATE TABLE IF NOT EXISTS address_analytics (
            address VARCHAR(64) PRIMARY KEY,
            transaction_count BIGINT NOT NULL DEFAULT 0,
            total_received NUMERIC(78,0) NOT NULL DEFAULT 0,
            total_sent NUMERIC(78,0) NOT NULL DEFAULT 0,
            first_seen TIMESTAMP WITH TIME ZONE,
            last_seen TIMESTAMP WITH TIME ZONE,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Block analytics aggregations
        CREATE TABLE IF NOT EXISTS block_analytics (
            interval_start TIMESTAMP WITH TIME ZONE NOT NULL,
            interval_seconds INTEGER NOT NULL,
            block_count BIGINT NOT NULL DEFAULT 0,
            transaction_count BIGINT NOT NULL DEFAULT 0,
            total_gas_used BIGINT NOT NULL DEFAULT 0,
            avg_block_time DOUBLE PRECISION NOT NULL DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            PRIMARY KEY (interval_start, interval_seconds)
        );
        """
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(schema_sql)
        
        self.logger.info("Database schema setup complete")
    
    async def get_last_indexed_block(self) -> int:
        """Get the last successfully indexed block height"""
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchval("SELECT MAX(height) FROM blocks")
                return result if result is not None else self.config["blockchain"]["start_block"]
        except Exception as e:
            self.logger.warning(f"Could not get last indexed block: {e}")
            return self.config["blockchain"]["start_block"]
    
    async def fetch_block_data(self, height: int) -> Optional[BlockData]:
        """Fetch block data from blockchain RPC"""
        try:
            # Try Web3 client first
            if self.web3_client and self.web3_client.is_connected():
                block = self.web3_client.eth.get_block(height, full_transactions=False)
                return BlockData(
                    height=block.number,
                    hash=block.hash.hex(),
                    timestamp=block.timestamp,
                    transaction_count=len(block.transactions),
                    size=block.size,
                    gas_used=block.gasUsed,
                    gas_limit=block.gasLimit,
                    proposer=block.miner
                )
            
            # Fallback to direct RPC call
            async with aiohttp.ClientSession() as session:
                rpc_data = {
                    "jsonrpc": "2.0",
                    "method": "eth_getBlockByNumber",
                    "params": [hex(height), False],
                    "id": 1
                }
                
                async with session.post(
                    self.config["blockchain"]["rpc_url"], 
                    json=rpc_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if "result" in result and result["result"]:
                            block = result["result"]
                            return BlockData(
                                height=int(block["number"], 16),
                                hash=block["hash"],
                                timestamp=int(block["timestamp"], 16),
                                transaction_count=len(block["transactions"]),
                                size=int(block["size"], 16) if block.get("size") else 0,
                                gas_used=int(block["gasUsed"], 16) if block.get("gasUsed") else 0,
                                gas_limit=int(block["gasLimit"], 16) if block.get("gasLimit") else 0,
                                proposer=block.get("miner")
                            )
        
        except Exception as e:
            self.logger.error(f"Failed to fetch block {height}: {e}")
            return None
    
    async def fetch_transaction_data(self, block: BlockData) -> List[TransactionData]:
        """Fetch transaction data for a block"""
        if not self.config["indexing"]["enable_transaction_indexing"]:
            return []
        
        transactions = []
        try:
            if self.web3_client and self.web3_client.is_connected():
                full_block = self.web3_client.eth.get_block(block.height, full_transactions=True)
                
                for i, tx in enumerate(full_block.transactions):
                    transactions.append(TransactionData(
                        hash=tx.hash.hex(),
                        block_height=block.height,
                        index_in_block=i,
                        from_address=tx['from'],
                        to_address=tx.get('to'),
                        value=tx.value,
                        gas=tx.gas,
                        gas_price=tx.gasPrice,
                        timestamp=block.timestamp
                    ))
            
        except Exception as e:
            self.logger.error(f"Failed to fetch transactions for block {block.height}: {e}")
        
        return transactions
    
    async def index_block(self, block_data: BlockData, transactions: List[TransactionData]):
        """Index block and transaction data to database"""
        with INDEXING_LATENCY.time():
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    # Insert block
                    await conn.execute("""
                        INSERT INTO blocks (height, hash, timestamp, transaction_count, size_bytes, gas_used, gas_limit, proposer)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        ON CONFLICT (height) DO UPDATE SET
                            hash = EXCLUDED.hash,
                            timestamp = EXCLUDED.timestamp,
                            transaction_count = EXCLUDED.transaction_count,
                            size_bytes = EXCLUDED.size_bytes,
                            gas_used = EXCLUDED.gas_used,
                            gas_limit = EXCLUDED.gas_limit,
                            proposer = EXCLUDED.proposer
                    """, 
                    block_data.height,
                    block_data.hash,
                    datetime.fromtimestamp(block_data.timestamp, timezone.utc),
                    block_data.transaction_count,
                    block_data.size,
                    block_data.gas_used,
                    block_data.gas_limit,
                    block_data.proposer
                    )
                    
                    # Insert transactions
                    if transactions:
                        await conn.executemany("""
                            INSERT INTO transactions (hash, block_height, index_in_block, from_address, to_address, value, gas_limit, gas_price, timestamp)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                            ON CONFLICT (hash) DO NOTHING
                        """, [
                            (tx.hash, tx.block_height, tx.index_in_block, tx.from_address, tx.to_address, 
                             tx.value, tx.gas, tx.gas_price, datetime.fromtimestamp(tx.timestamp, timezone.utc))
                            for tx in transactions
                        ])
        
        # Update metrics
        BLOCKS_PROCESSED.inc()
        TRANSACTIONS_INDEXED.inc(len(transactions))
        CURRENT_BLOCK_HEIGHT.set(block_data.height)
        
        # Cache recent block data
        await self.cache_block_data(block_data, transactions)
    
    async def cache_block_data(self, block: BlockData, transactions: List[TransactionData]):
        """Cache block data in Redis for fast API access"""
        try:
            # Cache block summary
            block_key = f"block:{block.height}"
            await self.redis_client.setex(
                block_key, 
                self.config["analytics"]["cache_duration"],
                json.dumps(asdict(block))
            )
            
            # Cache transaction hashes
            tx_key = f"block_txs:{block.height}"
            await self.redis_client.setex(
                tx_key,
                self.config["analytics"]["cache_duration"],
                json.dumps([tx.hash for tx in transactions])
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to cache block data: {e}")
    
    async def process_indexing_queue(self):
        """Process blocks from the indexing queue"""
        while self.running:
            try:
                block_height = await asyncio.wait_for(self.indexing_queue.get(), timeout=1.0)
                
                # Fetch block data
                block_data = await self.fetch_block_data(block_height)
                if not block_data:
                    continue
                
                # Fetch transactions
                transactions = await self.fetch_transaction_data(block_data)
                
                # Index to database
                await self.index_block(block_data, transactions)
                
                self.current_block = max(self.current_block, block_height)
                self.logger.debug(f"Indexed block {block_height} with {len(transactions)} transactions")
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error processing indexing queue: {e}")
                await asyncio.sleep(1)
    
    async def monitor_blockchain(self):
        """Monitor blockchain for new blocks"""
        while self.running:
            try:
                # Get current blockchain height
                if self.web3_client and self.web3_client.is_connected():
                    latest_block = self.web3_client.eth.block_number
                else:
                    # Fallback RPC call
                    async with aiohttp.ClientSession() as session:
                        rpc_data = {
                            "jsonrpc": "2.0",
                            "method": "eth_blockNumber",
                            "params": [],
                            "id": 1
                        }
                        async with session.post(
                            self.config["blockchain"]["rpc_url"],
                            json=rpc_data,
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:
                            if response.status == 200:
                                result = await response.json()
                                latest_block = int(result["result"], 16)
                            else:
                                await asyncio.sleep(5)
                                continue
                
                # Update lag metric
                lag = latest_block - self.current_block
                INDEXING_LAG.set(max(0, lag))
                
                # Queue missing blocks for indexing
                for block_height in range(self.current_block + 1, latest_block + 1):
                    try:
                        await self.indexing_queue.put_nowait(block_height)
                    except asyncio.QueueFull:
                        self.logger.warning("Indexing queue is full, skipping block")
                        break
                
                await asyncio.sleep(5)  # Check for new blocks every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Error monitoring blockchain: {e}")
                await asyncio.sleep(10)
    
    async def run_analytics_aggregations(self):
        """Run periodic analytics aggregations"""
        while self.running:
            try:
                await self.update_analytics_aggregations()
                await asyncio.sleep(300)  # Run every 5 minutes
            except Exception as e:
                self.logger.error(f"Error running analytics: {e}")
                await asyncio.sleep(60)
    
    async def update_analytics_aggregations(self):
        """Update analytics aggregation tables"""
        async with self.db_pool.acquire() as conn:
            # Update block analytics for different intervals
            for interval_seconds in self.config["analytics"]["aggregation_intervals"]:
                await conn.execute("""
                    INSERT INTO block_analytics (interval_start, interval_seconds, block_count, transaction_count, total_gas_used, avg_block_time)
                    SELECT 
                        date_trunc($2, timestamp) as interval_start,
                        $1 as interval_seconds,
                        COUNT(*) as block_count,
                        SUM(transaction_count) as transaction_count,
                        SUM(gas_used) as total_gas_used,
                        AVG(EXTRACT(EPOCH FROM (timestamp - LAG(timestamp) OVER (ORDER BY height)))) as avg_block_time
                    FROM blocks 
                    WHERE timestamp >= NOW() - INTERVAL $3
                    GROUP BY date_trunc($2, timestamp)
                    ON CONFLICT (interval_start, interval_seconds) DO UPDATE SET
                        block_count = EXCLUDED.block_count,
                        transaction_count = EXCLUDED.transaction_count,
                        total_gas_used = EXCLUDED.total_gas_used,
                        avg_block_time = EXCLUDED.avg_block_time
                """, 
                interval_seconds,
                'hour' if interval_seconds >= 3600 else 'minute',
                f'{interval_seconds * 2} seconds'
                )
    
    async def health_check(self):
        """Perform health checks"""
        while self.running:
            try:
                # Check database connection
                async with self.db_pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                
                # Check Redis connection
                await self.redis_client.ping()
                
                # Check blockchain connection
                if self.web3_client:
                    self.web3_client.is_connected()
                
                await asyncio.sleep(self.config["monitoring"]["health_check_interval"])
                
            except Exception as e:
                self.logger.error(f"Health check failed: {e}")
                await asyncio.sleep(30)
    
    async def run(self):
        """Main observer service loop"""
        self.running = True
        
        try:
            await self.initialize()
            
            # Start background tasks
            tasks = [
                asyncio.create_task(self.monitor_blockchain()),
                asyncio.create_task(self.process_indexing_queue()),
                asyncio.create_task(self.run_analytics_aggregations()),
                asyncio.create_task(self.health_check())
            ]
            
            # Start multiple indexing workers
            for i in range(self.config["indexing"]["worker_count"]):
                tasks.append(asyncio.create_task(self.process_indexing_queue()))
            
            self.logger.info("GuardianShield Blockchain Observer is running...")
            
            # Wait for all tasks
            await asyncio.gather(*tasks)
            
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        except Exception as e:
            self.logger.error(f"Observer crashed: {e}")
        finally:
            self.running = False
            if self.db_pool:
                await self.db_pool.close()
            if self.redis_client:
                await self.redis_client.close()

if __name__ == "__main__":
    observer = BlockchainObserver()
    asyncio.run(observer.run())