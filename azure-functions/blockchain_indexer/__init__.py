#!/usr/bin/env python3
"""
Blockchain Indexer Functions
Real-time blockchain data processing integrated with existing GuardianShield infrastructure
"""

import azure.functions as func
import logging
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from web3 import Web3
import psycopg2
import redis
from prometheus_client import Counter, Histogram, Gauge

# Import from parent function app
try:
    from .. import config, log_audit_event, blockchain_blocks_processed, function_execution_time
except ImportError:
    # Fallback for testing
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from function_app import config, log_audit_event, blockchain_blocks_processed, function_execution_time

logger = logging.getLogger('Blockchain-Indexer')

# Additional metrics
last_indexed_block = Gauge('blockchain_last_indexed_block', 'Last successfully indexed block number')
indexing_lag = Gauge('blockchain_indexing_lag_blocks', 'Number of blocks behind current blockchain head')
transaction_indexing_rate = Counter('blockchain_transactions_indexed_total', 'Total transactions indexed')
contract_events_processed = Counter('blockchain_contract_events_total', 'Contract events processed', ['contract', 'event_type'])

class BlockchainIndexer:
    """Real-time blockchain indexing engine"""
    
    def __init__(self):
        self.db_connection = None
        self.redis_client = None
        self.web3 = config.web3 if hasattr(config, 'web3') else None
        self.last_processed_block = 0
        self.batch_size = 100
        
        # Contract addresses to monitor
        self.monitored_contracts = {
            'shield_token': config.shield_token_address,
            'guard_token': config.guard_token_address
        }
    
    async def init_connections(self):
        """Initialize database and Redis connections to existing infrastructure"""
        try:
            # Connect to existing PostgreSQL blockchain_data database
            self.db_connection = config.get_database_connection('blockchain_data')
            logger.info("Connected to existing blockchain PostgreSQL database")
            
            # Connect to existing Redis
            redis_password = config.get_secret('REDIS_PASSWORD')
            self.redis_client = redis.Redis(
                host=config.database_host.replace('database', 'redis'),  # Use existing Redis
                port=6379,
                password=redis_password,
                decode_responses=True
            )
            
            await asyncio.to_thread(self.redis_client.ping)
            logger.info("Connected to existing Redis cache")
            
            # Get last processed block from database
            await self._get_last_processed_block()
            
        except Exception as e:
            logger.error(f"Failed to initialize connections: {e}")
            raise
    
    async def _get_last_processed_block(self):
        """Get last processed block number from database"""
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(
                    "SELECT MAX(block_number) FROM indexed_blocks WHERE status = 'completed'"
                )
                result = cursor.fetchone()
                self.last_processed_block = result[0] if result[0] else 0
                
            logger.info(f"Last processed block: {self.last_processed_block}")
            last_indexed_block.set(self.last_processed_block)
            
        except Exception as e:
            logger.error(f"Failed to get last processed block: {e}")
            self.last_processed_block = 0
    
    async def index_block_range(self, start_block: int, end_block: int) -> Dict[str, Any]:
        """Index a range of blocks"""
        with function_execution_time.labels('index_block_range').time():
            try:
                if not self.web3 or not self.web3.is_connected():
                    return {'success': False, 'error': 'Blockchain not connected'}
                
                indexed_count = 0
                failed_blocks = []
                
                for block_num in range(start_block, end_block + 1):
                    try:
                        success = await self._index_single_block(block_num)
                        if success:
                            indexed_count += 1
                            blockchain_blocks_processed.inc()
                            last_indexed_block.set(block_num)
                        else:
                            failed_blocks.append(block_num)
                    except Exception as e:
                        logger.error(f"Failed to index block {block_num}: {e}")
                        failed_blocks.append(block_num)
                
                # Update indexing lag
                current_block = self.web3.eth.block_number
                lag = current_block - end_block
                indexing_lag.set(lag)
                
                result = {
                    'success': True,
                    'blocks_processed': indexed_count,
                    'failed_blocks': failed_blocks,
                    'start_block': start_block,
                    'end_block': end_block,
                    'current_blockchain_head': current_block,
                    'indexing_lag': lag
                }
                
                # Log audit event
                log_audit_event(
                    'blockchain_indexing',
                    result,
                    ['BLOCKCHAIN', 'INDEXING', 'BATCH_PROCESSING']
                )
                
                return result
                
            except Exception as e:
                logger.error(f"Block range indexing failed: {e}")
                return {'success': False, 'error': str(e)}
    
    async def _index_single_block(self, block_number: int) -> bool:
        """Index a single block with all transactions"""
        try:
            # Get block data from blockchain
            block = self.web3.eth.get_block(block_number, full_transactions=True)
            
            # Start database transaction
            with self.db_connection.cursor() as cursor:
                # Insert block record
                cursor.execute(
                    """
                    INSERT INTO indexed_blocks 
                    (block_number, block_hash, parent_hash, timestamp, gas_used, gas_limit, 
                     transaction_count, miner, size, status, indexed_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (block_number) DO UPDATE SET
                    status = 'completed', indexed_at = %s
                    """,
                    (
                        block['number'],
                        block['hash'].hex(),
                        block['parentHash'].hex(),
                        datetime.fromtimestamp(block['timestamp'], timezone.utc),
                        block['gasUsed'],
                        block['gasLimit'],
                        len(block['transactions']),
                        block['miner'],
                        block['size'],
                        'completed',
                        datetime.now(timezone.utc),
                        datetime.now(timezone.utc)
                    )
                )
                
                # Index all transactions in the block
                for tx in block['transactions']:
                    await self._index_transaction(cursor, tx, block)
                
                self.db_connection.commit()
            
            # Cache block summary in Redis for fast access
            cache_key = f"block:{block_number}"
            block_summary = {
                'number': block['number'],
                'hash': block['hash'].hex(),
                'timestamp': block['timestamp'],
                'transaction_count': len(block['transactions']),
                'gas_used': block['gasUsed'],
                'indexed_at': datetime.now(timezone.utc).isoformat()
            }
            
            await asyncio.to_thread(
                self.redis_client.setex,
                cache_key,
                3600,  # 1 hour cache
                json.dumps(block_summary)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to index block {block_number}: {e}")
            # Rollback transaction
            try:
                self.db_connection.rollback()
            except:
                pass
            return False
    
    async def _index_transaction(self, cursor, transaction, block):
        """Index a single transaction"""
        try:
            tx_hash = transaction['hash'].hex()
            
            # Insert transaction record
            cursor.execute(
                """
                INSERT INTO indexed_transactions
                (tx_hash, block_number, transaction_index, from_address, to_address,
                 value, gas, gas_price, gas_used, status, contract_created, input_data, indexed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tx_hash) DO NOTHING
                """,
                (
                    tx_hash,
                    block['number'],
                    transaction['transactionIndex'],
                    transaction['from'],
                    transaction['to'],
                    int(transaction['value']),
                    int(transaction['gas']),
                    int(transaction['gasPrice']),
                    0,  # gas_used - would need receipt to get this
                    'pending',  # Would need receipt to get actual status
                    transaction['to'] is None,  # Contract creation
                    transaction['input'][:1000] if transaction['input'] else None,  # Truncate input
                    datetime.now(timezone.utc)
                )
            )
            
            # Check if transaction involves monitored contracts
            await self._process_contract_interactions(cursor, transaction, block)
            
            transaction_indexing_rate.inc()
            
        except Exception as e:
            logger.error(f"Failed to index transaction {transaction['hash'].hex()}: {e}")
            raise
    
    async def _process_contract_interactions(self, cursor, transaction, block):
        """Process interactions with monitored contracts"""
        try:
            to_address = transaction['to']
            if not to_address:
                return
            
            # Check if transaction is to a monitored contract
            for contract_name, contract_address in self.monitored_contracts.items():
                if contract_address and to_address.lower() == contract_address.lower():
                    # Store contract interaction
                    cursor.execute(
                        """
                        INSERT INTO contract_interactions
                        (tx_hash, block_number, contract_name, contract_address, 
                         from_address, input_data, value, indexed_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (tx_hash, contract_address) DO NOTHING
                        """,
                        (
                            transaction['hash'].hex(),
                            block['number'],
                            contract_name,
                            contract_address,
                            transaction['from'],
                            transaction['input'][:1000] if transaction['input'] else None,
                            int(transaction['value']),
                            datetime.now(timezone.utc)
                        )
                    )
                    
                    contract_events_processed.labels(contract_name, 'interaction').inc()
                    logger.debug(f"Recorded {contract_name} interaction: {transaction['hash'].hex()}")
                    
        except Exception as e:
            logger.error(f"Failed to process contract interactions: {e}")
    
    async def get_indexing_status(self) -> Dict[str, Any]:
        """Get current indexing status"""
        try:
            current_block = self.web3.eth.block_number if self.web3 else 0
            
            with self.db_connection.cursor() as cursor:
                # Get indexing statistics
                cursor.execute(
                    """
                    SELECT 
                        COUNT(*) as total_blocks,
                        MIN(block_number) as first_block,
                        MAX(block_number) as last_block,
                        COUNT(DISTINCT CASE WHEN status = 'completed' THEN block_number END) as completed_blocks
                    FROM indexed_blocks
                    """
                )
                block_stats = cursor.fetchone()
                
                cursor.execute(
                    "SELECT COUNT(*) FROM indexed_transactions WHERE indexed_at > %s",
                    (datetime.now(timezone.utc) - timedelta(hours=24),)
                )
                recent_tx_count = cursor.fetchone()[0]
                
                cursor.execute(
                    "SELECT contract_name, COUNT(*) FROM contract_interactions GROUP BY contract_name"
                )
                contract_stats = dict(cursor.fetchall())
            
            status = {
                'current_blockchain_head': current_block,
                'last_indexed_block': self.last_processed_block,
                'indexing_lag': current_block - self.last_processed_block,
                'total_indexed_blocks': block_stats[0] if block_stats[0] else 0,
                'completed_blocks': block_stats[3] if block_stats[3] else 0,
                'first_indexed_block': block_stats[1] if block_stats[1] else 0,
                'transactions_last_24h': recent_tx_count,
                'contract_interactions': contract_stats,
                'indexing_rate_blocks_per_minute': 0,  # Could calculate from recent data
                'status': 'healthy' if current_block - self.last_processed_block < 100 else 'lagging',
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get indexing status: {e}")
            return {'error': str(e)}
    
    async def search_transactions(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Search indexed transactions with filters"""
        try:
            conditions = []
            params = []
            
            # Build dynamic query based on filters
            if filters.get('from_address'):
                conditions.append("from_address = %s")
                params.append(filters['from_address'])
            
            if filters.get('to_address'):
                conditions.append("to_address = %s")
                params.append(filters['to_address'])
            
            if filters.get('block_range'):
                start_block, end_block = filters['block_range']
                conditions.append("block_number BETWEEN %s AND %s")
                params.extend([start_block, end_block])
            
            if filters.get('min_value'):
                conditions.append("value >= %s")
                params.append(int(filters['min_value']))
            
            # Base query
            query = """
                SELECT tx_hash, block_number, from_address, to_address, value, 
                       gas, gas_price, indexed_at
                FROM indexed_transactions
            """
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY block_number DESC LIMIT %s"
            params.append(filters.get('limit', 100))
            
            with self.db_connection.cursor() as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                transactions = []
                for row in results:
                    transactions.append({
                        'tx_hash': row[0],
                        'block_number': row[1],
                        'from_address': row[2],
                        'to_address': row[3],
                        'value': str(row[4]),  # Convert to string for large numbers
                        'gas': row[5],
                        'gas_price': row[6],
                        'indexed_at': row[7].isoformat()
                    })
                
                return {
                    'success': True,
                    'transactions': transactions,
                    'count': len(transactions),
                    'filters_applied': filters
                }
                
        except Exception as e:
            logger.error(f"Transaction search failed: {e}")
            return {'success': False, 'error': str(e)}

# Global indexer instance
indexer = BlockchainIndexer()

# Azure Function endpoints
@func.route(route="blockchain/index/range", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
async def index_block_range(req: func.HttpRequest) -> func.HttpResponse:
    """Index a range of blockchain blocks"""
    try:
        req_data = req.get_json()
        start_block = req_data.get('start_block')
        end_block = req_data.get('end_block')
        
        if not start_block or not end_block:
            return func.HttpResponse(
                json.dumps({'error': 'start_block and end_block required'}),
                status_code=400,
                mimetype="application/json"
            )
        
        if end_block - start_block > 1000:
            return func.HttpResponse(
                json.dumps({'error': 'Maximum range is 1000 blocks'}),
                status_code=400,
                mimetype="application/json"
            )
        
        await indexer.init_connections()
        result = await indexer.index_block_range(start_block, end_block)
        
        return func.HttpResponse(
            json.dumps(result),
            status_code=200 if result['success'] else 400,
            mimetype="application/json"
        )
    except Exception as e:
        logger.error(f"Block range indexing endpoint failed: {e}")
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@func.route(route="blockchain/status", auth_level=func.AuthLevel.FUNCTION, methods=["GET"])
async def get_indexing_status(req: func.HttpRequest) -> func.HttpResponse:
    """Get blockchain indexing status"""
    try:
        await indexer.init_connections()
        status = await indexer.get_indexing_status()
        
        return func.HttpResponse(
            json.dumps(status),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logger.error(f"Indexing status endpoint failed: {e}")
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@func.route(route="blockchain/search/transactions", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
async def search_transactions(req: func.HttpRequest) -> func.HttpResponse:
    """Search indexed transactions"""
    try:
        filters = req.get_json() or {}
        
        await indexer.init_connections()
        result = await indexer.search_transactions(filters)
        
        return func.HttpResponse(
            json.dumps(result),
            status_code=200 if result['success'] else 400,
            mimetype="application/json"
        )
    except Exception as e:
        logger.error(f"Transaction search endpoint failed: {e}")
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            status_code=500,
            mimetype="application/json"
        )

# Timer function for continuous indexing
@func.timer_trigger(schedule="0 */5 * * * *", arg_name="timer", run_on_startup=False)
async def continuous_blockchain_indexing(timer: func.TimerRequest) -> None:
    """Continuously index new blockchain blocks every 5 minutes"""
    try:
        if timer.past_due:
            logger.warning('Blockchain indexing timer is past due!')
        
        await indexer.init_connections()
        
        if not indexer.web3 or not indexer.web3.is_connected():
            logger.error("Blockchain not connected, skipping indexing")
            return
        
        current_block = indexer.web3.eth.block_number
        start_block = indexer.last_processed_block + 1
        
        if start_block <= current_block:
            # Process up to 100 blocks at a time
            end_block = min(start_block + 99, current_block)
            
            logger.info(f"Auto-indexing blocks {start_block} to {end_block}")
            result = await indexer.index_block_range(start_block, end_block)
            
            if result['success']:
                indexer.last_processed_block = end_block
                logger.info(f"Successfully indexed {result['blocks_processed']} blocks")
            else:
                logger.error(f"Auto-indexing failed: {result.get('error')}")
        
    except Exception as e:
        logger.error(f"Continuous blockchain indexing failed: {e}")