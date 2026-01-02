#!/usr/bin/env python3

"""
GuardianShield Blockchain Indexer Service
Advanced indexing with search capabilities and data exports
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import asyncpg
import redis.asyncio as redis
from elasticsearch import AsyncElasticsearch
from prometheus_client import Counter, Histogram, Gauge
import hashlib
import os

# Prometheus metrics for indexer
EVENTS_INDEXED = Counter('indexer_events_indexed_total', 'Total events indexed')
SEARCH_QUERIES = Counter('indexer_search_queries_total', 'Total search queries processed')
EXPORT_OPERATIONS = Counter('indexer_export_operations_total', 'Total export operations')
INDEX_SIZE = Gauge('indexer_index_size_bytes', 'Current index size in bytes')

@dataclass
class ContractEvent:
    transaction_hash: str
    block_height: int
    log_index: int
    contract_address: str
    event_name: str
    event_data: Dict[str, Any]
    timestamp: int

@dataclass 
class AddressTag:
    address: str
    tag: str
    source: str
    confidence: float
    timestamp: int

class BlockchainIndexer:
    def __init__(self, config_path: str = "/etc/guardian/indexer.json"):
        self.config = self.load_config(config_path)
        self.running = False
        self.db_pool = None
        self.redis_client = None
        self.elasticsearch = None
        self.indexed_contracts = set()
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, self.config.get("log_level", "INFO").upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("BlockchainIndexer")
        
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load indexer configuration"""
        default_config = {
            "database": {
                "host": "observer-postgres",
                "port": 5432,
                "database": "guardian_analytics",
                "username": "observer",
                "password": os.getenv("POSTGRES_PASSWORD", "observer123")
            },
            "redis": {
                "host": "observer-redis", 
                "port": 6379,
                "db": 1,
                "password": os.getenv("REDIS_PASSWORD", "redis123")
            },
            "elasticsearch": {
                "hosts": ["http://observer-elasticsearch:9200"],
                "username": "elastic",
                "password": os.getenv("ELASTIC_PASSWORD", "elastic123"),
                "max_retries": 3
            },
            "indexing": {
                "batch_size": 1000,
                "worker_count": 2,
                "contract_events": True,
                "address_tagging": True,
                "full_text_search": True,
                "export_formats": ["csv", "json", "parquet"]
            },
            "search": {
                "max_results": 10000,
                "cache_duration": 600,
                "fuzzy_search": True,
                "autocomplete": True
            },
            "contracts": {
                "abi_sources": [
                    "https://api.etherscan.io/api",
                    "https://sourcify.dev/server"
                ],
                "known_contracts": {}
            }
        }
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
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
        """Initialize indexer services"""
        self.logger.info("Initializing GuardianShield Blockchain Indexer...")
        
        # Initialize database connection
        await self.init_database()
        
        # Initialize Redis
        await self.init_redis()
        
        # Initialize Elasticsearch
        await self.init_elasticsearch()
        
        # Setup database schema for advanced indexing
        await self.setup_indexer_schema()
        
        # Setup Elasticsearch indices
        await self.setup_elasticsearch_indices()
        
        self.logger.info("Indexer initialization complete")
    
    async def init_database(self):
        """Initialize PostgreSQL connection"""
        db_config = self.config["database"]
        dsn = f"postgresql://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        
        self.db_pool = await asyncpg.create_pool(dsn, min_size=2, max_size=10)
        self.logger.info("Database connection established")
    
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
        await self.redis_client.ping()
        self.logger.info("Redis connection established")
    
    async def init_elasticsearch(self):
        """Initialize Elasticsearch connection"""
        es_config = self.config["elasticsearch"]
        
        self.elasticsearch = AsyncElasticsearch(
            es_config["hosts"],
            http_auth=(es_config["username"], es_config["password"]) if es_config.get("username") else None,
            max_retries=es_config["max_retries"],
            retry_on_timeout=True
        )
        
        try:
            info = await self.elasticsearch.info()
            self.logger.info(f"Elasticsearch connection established: {info['version']['number']}")
        except Exception as e:
            self.logger.warning(f"Elasticsearch connection failed: {e}")
            self.elasticsearch = None
    
    async def setup_indexer_schema(self):
        """Create advanced indexing tables"""
        schema_sql = """
        -- Contract events table
        CREATE TABLE IF NOT EXISTS contract_events (
            id SERIAL PRIMARY KEY,
            transaction_hash VARCHAR(66) NOT NULL,
            block_height BIGINT NOT NULL,
            log_index INTEGER NOT NULL,
            contract_address VARCHAR(42) NOT NULL,
            event_name VARCHAR(100) NOT NULL,
            event_signature VARCHAR(66),
            event_data JSONB NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(transaction_hash, log_index),
            INDEX (contract_address),
            INDEX (event_name),
            INDEX (block_height),
            INDEX (timestamp)
        );
        
        -- Address tags and labels
        CREATE TABLE IF NOT EXISTS address_tags (
            address VARCHAR(42) NOT NULL,
            tag VARCHAR(100) NOT NULL,
            source VARCHAR(50) NOT NULL,
            confidence DECIMAL(3,2) NOT NULL DEFAULT 1.0,
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            PRIMARY KEY (address, tag, source),
            INDEX (tag),
            INDEX (source)
        );
        
        -- Contract ABIs and metadata
        CREATE TABLE IF NOT EXISTS contract_metadata (
            address VARCHAR(42) PRIMARY KEY,
            name VARCHAR(200),
            symbol VARCHAR(20),
            decimals INTEGER,
            contract_type VARCHAR(50),
            abi JSONB,
            source_code TEXT,
            compiler_version VARCHAR(50),
            verified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Search queries log for analytics
        CREATE TABLE IF NOT EXISTS search_queries (
            id SERIAL PRIMARY KEY,
            query_text TEXT NOT NULL,
            query_type VARCHAR(50) NOT NULL,
            result_count INTEGER NOT NULL,
            execution_time_ms INTEGER NOT NULL,
            user_agent TEXT,
            ip_address INET,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Export jobs tracking
        CREATE TABLE IF NOT EXISTS export_jobs (
            id SERIAL PRIMARY KEY,
            job_type VARCHAR(50) NOT NULL,
            query_params JSONB NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            file_path TEXT,
            file_size BIGINT,
            record_count BIGINT,
            error_message TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            completed_at TIMESTAMP WITH TIME ZONE
        );
        """
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(schema_sql)
        
        self.logger.info("Advanced indexer schema setup complete")
    
    async def setup_elasticsearch_indices(self):
        """Setup Elasticsearch indices for full-text search"""
        if not self.elasticsearch:
            return
        
        # Transaction search index
        transaction_mapping = {
            "mappings": {
                "properties": {
                    "hash": {"type": "keyword"},
                    "block_height": {"type": "long"},
                    "from_address": {"type": "keyword"},
                    "to_address": {"type": "keyword"},
                    "value": {"type": "scaled_float", "scaling_factor": 1000000000000000000},
                    "timestamp": {"type": "date"},
                    "input_data": {"type": "text"},
                    "tags": {"type": "keyword"},
                    "annotations": {"type": "text"}
                }
            }
        }
        
        # Address search index
        address_mapping = {
            "mappings": {
                "properties": {
                    "address": {"type": "keyword"},
                    "tags": {"type": "keyword"},
                    "labels": {"type": "text"},
                    "transaction_count": {"type": "long"},
                    "balance": {"type": "scaled_float", "scaling_factor": 1000000000000000000},
                    "first_seen": {"type": "date"},
                    "last_seen": {"type": "date"},
                    "risk_score": {"type": "float"},
                    "categories": {"type": "keyword"}
                }
            }
        }
        
        # Contract events search index
        events_mapping = {
            "mappings": {
                "properties": {
                    "transaction_hash": {"type": "keyword"},
                    "contract_address": {"type": "keyword"},
                    "event_name": {"type": "keyword"},
                    "event_data": {"type": "object", "dynamic": True},
                    "timestamp": {"type": "date"},
                    "block_height": {"type": "long"},
                    "decoded_data": {"type": "text"}
                }
            }
        }
        
        indices = [
            ("guardian_transactions", transaction_mapping),
            ("guardian_addresses", address_mapping),
            ("guardian_events", events_mapping)
        ]
        
        for index_name, mapping in indices:
            try:
                if not await self.elasticsearch.indices.exists(index=index_name):
                    await self.elasticsearch.indices.create(index=index_name, body=mapping)
                    self.logger.info(f"Created Elasticsearch index: {index_name}")
            except Exception as e:
                self.logger.error(f"Failed to create index {index_name}: {e}")
    
    async def index_contract_events(self, start_block: int, end_block: int):
        """Index contract events for block range"""
        if not self.config["indexing"]["contract_events"]:
            return
        
        self.logger.info(f"Indexing contract events for blocks {start_block}-{end_block}")
        
        async with self.db_pool.acquire() as conn:
            # Get transactions with contract interactions
            transactions = await conn.fetch("""
                SELECT hash, block_height, to_address, timestamp
                FROM transactions 
                WHERE block_height BETWEEN $1 AND $2 
                AND to_address IS NOT NULL
                ORDER BY block_height, index_in_block
            """, start_block, end_block)
            
            events_batch = []
            
            for tx in transactions:
                # Extract events from transaction logs (simplified)
                # In real implementation, this would parse actual blockchain logs
                events = await self.extract_transaction_events(tx)
                events_batch.extend(events)
                
                if len(events_batch) >= self.config["indexing"]["batch_size"]:
                    await self.store_contract_events(events_batch)
                    EVENTS_INDEXED.inc(len(events_batch))
                    events_batch = []
            
            if events_batch:
                await self.store_contract_events(events_batch)
                EVENTS_INDEXED.inc(len(events_batch))
    
    async def extract_transaction_events(self, transaction) -> List[ContractEvent]:
        """Extract events from transaction (placeholder implementation)"""
        # This would typically parse actual blockchain transaction logs
        # For now, return empty list as this requires blockchain-specific logic
        return []
    
    async def store_contract_events(self, events: List[ContractEvent]):
        """Store contract events in database and Elasticsearch"""
        if not events:
            return
        
        # Store in PostgreSQL
        async with self.db_pool.acquire() as conn:
            await conn.executemany("""
                INSERT INTO contract_events (
                    transaction_hash, block_height, log_index, contract_address, 
                    event_name, event_data, timestamp
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (transaction_hash, log_index) DO NOTHING
            """, [
                (event.transaction_hash, event.block_height, event.log_index,
                 event.contract_address, event.event_name, json.dumps(event.event_data),
                 datetime.fromtimestamp(event.timestamp, timezone.utc))
                for event in events
            ])
        
        # Index in Elasticsearch for search
        if self.elasticsearch:
            bulk_data = []
            for event in events:
                bulk_data.extend([
                    {"index": {"_index": "guardian_events", "_id": f"{event.transaction_hash}_{event.log_index}"}},
                    {
                        "transaction_hash": event.transaction_hash,
                        "contract_address": event.contract_address,
                        "event_name": event.event_name,
                        "event_data": event.event_data,
                        "timestamp": datetime.fromtimestamp(event.timestamp, timezone.utc).isoformat(),
                        "block_height": event.block_height,
                        "decoded_data": json.dumps(event.event_data)  # For full-text search
                    }
                ])
            
            if bulk_data:
                try:
                    await self.elasticsearch.bulk(body=bulk_data)
                except Exception as e:
                    self.logger.error(f"Elasticsearch bulk indexing failed: {e}")
    
    async def tag_addresses(self, addresses: List[str]):
        """Apply automatic address tagging"""
        if not self.config["indexing"]["address_tagging"]:
            return
        
        tags_batch = []
        
        for address in addresses:
            # Get transaction patterns for address
            patterns = await self.analyze_address_patterns(address)
            
            # Apply heuristic tagging
            for tag, confidence in patterns.items():
                if confidence > 0.7:  # Only high-confidence tags
                    tags_batch.append(AddressTag(
                        address=address,
                        tag=tag,
                        source="heuristic",
                        confidence=confidence,
                        timestamp=int(datetime.now().timestamp())
                    ))
        
        if tags_batch:
            await self.store_address_tags(tags_batch)
    
    async def analyze_address_patterns(self, address: str) -> Dict[str, float]:
        """Analyze transaction patterns to infer address type"""
        patterns = {}
        
        async with self.db_pool.acquire() as conn:
            # Get transaction statistics
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as tx_count,
                    COUNT(DISTINCT to_address) as unique_recipients,
                    AVG(value) as avg_value,
                    MAX(value) as max_value,
                    COUNT(CASE WHEN value = 0 THEN 1 END) as zero_value_txs
                FROM transactions 
                WHERE from_address = $1
            """, address)
            
            if stats and stats['tx_count'] > 0:
                # Exchange pattern: high volume, many recipients
                if stats['unique_recipients'] > 100 and stats['tx_count'] > 1000:
                    patterns['exchange'] = 0.9
                
                # Contract pattern: many zero-value transactions
                if stats['zero_value_txs'] / stats['tx_count'] > 0.8:
                    patterns['contract'] = 0.85
                
                # Whale pattern: high value transactions
                if stats['max_value'] > 1000 * 10**18:  # >1000 ETH equivalent
                    patterns['whale'] = 0.8
        
        return patterns
    
    async def store_address_tags(self, tags: List[AddressTag]):
        """Store address tags in database"""
        async with self.db_pool.acquire() as conn:
            await conn.executemany("""
                INSERT INTO address_tags (address, tag, source, confidence)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (address, tag, source) DO UPDATE SET
                    confidence = EXCLUDED.confidence,
                    updated_at = NOW()
            """, [
                (tag.address, tag.tag, tag.source, tag.confidence)
                for tag in tags
            ])
    
    async def search_transactions(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Search transactions with various filters"""
        SEARCH_QUERIES.inc()
        start_time = datetime.now()
        
        # Build search query
        conditions = []
        params = []
        param_counter = 1
        
        if query.get('address'):
            conditions.append(f"(from_address = ${param_counter} OR to_address = ${param_counter})")
            params.append(query['address'])
            param_counter += 1
        
        if query.get('block_range'):
            start_block, end_block = query['block_range']
            conditions.append(f"block_height BETWEEN ${param_counter} AND ${param_counter + 1}")
            params.extend([start_block, end_block])
            param_counter += 2
        
        if query.get('min_value'):
            conditions.append(f"value >= ${param_counter}")
            params.append(query['min_value'])
            param_counter += 1
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        limit = min(query.get('limit', 100), self.config["search"]["max_results"])
        
        sql = f"""
            SELECT hash, block_height, from_address, to_address, value, timestamp
            FROM transactions 
            {where_clause}
            ORDER BY timestamp DESC 
            LIMIT {limit}
        """
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            
            result = {
                "transactions": [dict(row) for row in rows],
                "count": len(rows),
                "execution_time_ms": int((datetime.now() - start_time).total_seconds() * 1000)
            }
            
            # Log search query for analytics
            await conn.execute("""
                INSERT INTO search_queries (query_text, query_type, result_count, execution_time_ms)
                VALUES ($1, $2, $3, $4)
            """, json.dumps(query), 'transaction_search', len(rows), result["execution_time_ms"])
            
            return result
    
    async def export_data(self, export_config: Dict[str, Any]) -> str:
        """Export blockchain data in various formats"""
        EXPORT_OPERATIONS.inc()
        
        job_id = hashlib.md5(json.dumps(export_config, sort_keys=True).encode()).hexdigest()
        
        # Record export job
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO export_jobs (id, job_type, query_params, status)
                VALUES ($1, $2, $3, 'running')
                ON CONFLICT (id) DO UPDATE SET status = 'running', created_at = NOW()
            """, job_id, export_config.get('type', 'transactions'), json.dumps(export_config))
        
        try:
            if export_config['type'] == 'transactions':
                file_path = await self.export_transactions(export_config, job_id)
            elif export_config['type'] == 'events':
                file_path = await self.export_events(export_config, job_id)
            else:
                raise ValueError(f"Unknown export type: {export_config['type']}")
            
            # Update job status
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE export_jobs 
                    SET status = 'completed', file_path = $2, file_size = $3, completed_at = NOW()
                    WHERE id = $1
                """, job_id, file_path, file_size)
            
            return file_path
            
        except Exception as e:
            # Update job with error
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE export_jobs 
                    SET status = 'failed', error_message = $2, completed_at = NOW()
                    WHERE id = $1
                """, job_id, str(e))
            raise
    
    async def export_transactions(self, config: Dict[str, Any], job_id: str) -> str:
        """Export transaction data to file"""
        output_format = config.get('format', 'csv')
        output_dir = '/home/guardian/analytics/exports'
        os.makedirs(output_dir, exist_ok=True)
        
        file_path = f"{output_dir}/transactions_{job_id}.{output_format}"
        
        # Build query based on filters
        conditions = []
        params = []
        
        if config.get('date_range'):
            start_date, end_date = config['date_range']
            conditions.append("timestamp BETWEEN $1 AND $2")
            params.extend([start_date, end_date])
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        async with self.db_pool.acquire() as conn:
            if output_format == 'csv':
                query = f"""
                    COPY (
                        SELECT hash, block_height, from_address, to_address, value, timestamp
                        FROM transactions {where_clause}
                        ORDER BY timestamp
                    ) TO STDOUT WITH CSV HEADER
                """
                
                with open(file_path, 'w') as f:
                    await conn.copy_to_table('transactions', output=f, format='csv')
            
            elif output_format == 'json':
                rows = await conn.fetch(f"""
                    SELECT hash, block_height, from_address, to_address, value, timestamp
                    FROM transactions {where_clause}
                    ORDER BY timestamp
                """, *params)
                
                with open(file_path, 'w') as f:
                    json.dump([dict(row) for row in rows], f, default=str, indent=2)
        
        return file_path
    
    async def export_events(self, config: Dict[str, Any], job_id: str) -> str:
        """Export contract events to file"""
        # Similar implementation to export_transactions but for events
        output_format = config.get('format', 'csv')
        output_dir = '/home/guardian/analytics/exports'
        os.makedirs(output_dir, exist_ok=True)
        
        file_path = f"{output_dir}/events_{job_id}.{output_format}"
        
        # Implementation would export contract events data
        # Placeholder for now
        with open(file_path, 'w') as f:
            f.write("contract_address,event_name,timestamp,data\n")
        
        return file_path
    
    async def run_indexing_worker(self):
        """Main indexing worker loop"""
        while self.running:
            try:
                # Get latest indexed block
                async with self.db_pool.acquire() as conn:
                    last_indexed = await conn.fetchval("""
                        SELECT MAX(block_height) 
                        FROM contract_events
                    """) or 0
                    
                    # Get current blockchain height
                    current_height = await conn.fetchval("""
                        SELECT MAX(height) FROM blocks
                    """) or 0
                
                if current_height > last_indexed:
                    # Index next batch of blocks
                    batch_end = min(last_indexed + self.config["indexing"]["batch_size"], current_height)
                    await self.index_contract_events(last_indexed + 1, batch_end)
                    
                    # Extract unique addresses for tagging
                    async with self.db_pool.acquire() as conn:
                        addresses = await conn.fetch("""
                            SELECT DISTINCT from_address as addr FROM transactions 
                            WHERE block_height BETWEEN $1 AND $2
                            UNION
                            SELECT DISTINCT to_address as addr FROM transactions 
                            WHERE block_height BETWEEN $1 AND $2 AND to_address IS NOT NULL
                        """, last_indexed + 1, batch_end)
                    
                    unique_addresses = [row['addr'] for row in addresses]
                    if unique_addresses:
                        await self.tag_addresses(unique_addresses)
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Indexing worker error: {e}")
                await asyncio.sleep(30)
    
    async def run(self):
        """Run the indexer service"""
        self.running = True
        
        try:
            await self.initialize()
            
            # Start indexing workers
            tasks = []
            for i in range(self.config["indexing"]["worker_count"]):
                tasks.append(asyncio.create_task(self.run_indexing_worker()))
            
            self.logger.info("GuardianShield Blockchain Indexer is running...")
            await asyncio.gather(*tasks)
            
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        finally:
            self.running = False
            if self.db_pool:
                await self.db_pool.close()
            if self.redis_client:
                await self.redis_client.close()
            if self.elasticsearch:
                await self.elasticsearch.close()

if __name__ == "__main__":
    indexer = BlockchainIndexer()
    asyncio.run(indexer.run())