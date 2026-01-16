#!/usr/bin/env python3
"""
ERC-8055 Shield Token Processing Functions
Integrates with existing GuardianShield Docker infrastructure
"""

import azure.functions as func
import logging
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from web3 import Web3
import psycopg2
import redis
from prometheus_client import Counter, Histogram

# Import from parent function app
try:
    from .. import config, log_audit_event, shield_token_operations, function_execution_time
except ImportError:
    # Fallback for testing
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from function_app import config, log_audit_event, shield_token_operations, function_execution_time

logger = logging.getLogger('ERC8055-Processor')

# ERC-8055 Shield Token ABI (simplified)
ERC8055_ABI = [
    {
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "name": "burn",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "tokenId", "type": "uint256"},
            {"name": "serialNumber", "type": "string"}
        ],
        "name": "remint",
        "outputs": [],
        "stateMutability": "nonpayable", 
        "type": "function"
    },
    {
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "name": "getSerialNumber",
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "name": "exists",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    }
]

class ShieldTokenProcessor:
    """ERC-8055 Shield Token processing engine"""
    
    def __init__(self):
        self.db_pool = None
        self.redis_client = None
        self.web3 = config.web3 if hasattr(config, 'web3') else None
        self.shield_contract = None
        
        if self.web3 and config.shield_token_address:
            self.shield_contract = self.web3.eth.contract(
                address=config.shield_token_address,
                abi=ERC8055_ABI
            )
    
    async def init_connections(self):
        """Initialize database and Redis connections"""
        try:
            # PostgreSQL connection to existing infrastructure
            self.db_connection = config.get_database_connection('erc8055_tokens')
            logger.info("Connected to existing PostgreSQL database")
            
            # Redis connection to existing infrastructure
            redis_password = config.get_secret('REDIS_PASSWORD')
            self.redis_client = redis.Redis(
                host=config.database_host.replace('database', 'redis'),  # Use existing Redis
                port=6379,
                password=redis_password,
                decode_responses=True
            )
            
            # Test Redis connection
            await asyncio.to_thread(self.redis_client.ping)
            logger.info("Connected to existing Redis cache")
            
        except Exception as e:
            logger.error(f"Failed to initialize connections: {e}")
            raise
    
    def validate_shield_token(self, token_id: int) -> Dict[str, Any]:
        """Validate Shield Token against ERC-8055 standard"""
        try:
            if not self.shield_contract:
                return {'valid': False, 'error': 'Contract not initialized'}
            
            # Check if token exists
            exists = self.shield_contract.functions.exists(token_id).call()
            
            if not exists:
                return {'valid': False, 'error': 'Token does not exist'}
            
            # Get serial number
            serial_number = self.shield_contract.functions.getSerialNumber(token_id).call()
            
            # Validate serial number format (Shield Token specific)
            if not self._validate_serial_format(serial_number):
                return {
                    'valid': False,
                    'error': f'Invalid serial number format: {serial_number}'
                }
            
            # Check database for fraud flags
            fraud_check = self._check_fraud_database(token_id, serial_number)
            
            result = {
                'valid': True,
                'token_id': token_id,
                'serial_number': serial_number,
                'fraud_score': fraud_check.get('fraud_score', 0),
                'flags': fraud_check.get('flags', []),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # Log audit event
            log_audit_event(
                'shield_token_validation',
                result,
                ['ERC-8055', 'SHIELD_TOKEN', 'VALIDATION']
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Shield token validation failed: {e}")
            shield_token_operations.labels('validation', 'error').inc()
            return {'valid': False, 'error': str(e)}
    
    def _validate_serial_format(self, serial_number: str) -> bool:
        """Validate Shield Token serial number format"""
        # Shield Token format: SHIELD-YYYY-NNNNNN-CCC
        # Example: SHIELD-2026-000001-ABC
        import re
        pattern = r'^SHIELD-\d{4}-\d{6}-[A-Z]{3}$'
        return bool(re.match(pattern, serial_number))
    
    def _check_fraud_database(self, token_id: int, serial_number: str) -> Dict[str, Any]:
        """Check token against fraud database"""
        try:
            with self.db_connection.cursor() as cursor:
                # Check for fraud reports
                cursor.execute(
                    "SELECT fraud_score, flags, last_updated FROM shield_token_fraud WHERE token_id = %s",
                    (token_id,)
                )
                result = cursor.fetchone()
                
                if result:
                    fraud_score, flags_json, last_updated = result
                    return {
                        'fraud_score': fraud_score,
                        'flags': json.loads(flags_json) if flags_json else [],
                        'last_updated': last_updated.isoformat()
                    }
                else:
                    return {'fraud_score': 0, 'flags': []}
                    
        except Exception as e:
            logger.error(f"Fraud database check failed: {e}")
            return {'fraud_score': 0, 'flags': ['DATABASE_ERROR']}
    
    async def process_burn_request(self, token_id: int, requester_address: str) -> Dict[str, Any]:
        """Process Shield Token burn request"""
        with function_execution_time.labels('burn_request').time():
            try:
                # Validate token first
                validation = self.validate_shield_token(token_id)
                if not validation['valid']:
                    shield_token_operations.labels('burn', 'invalid_token').inc()
                    return {
                        'success': False,
                        'error': f'Token validation failed: {validation["error"]}'
                    }
                
                # Check authorization (simplified - would integrate with existing auth)
                if validation['fraud_score'] > 80:
                    shield_token_operations.labels('burn', 'fraud_prevention').inc()
                    return {
                        'success': False,
                        'error': 'Token flagged for fraud - burn request denied'
                    }
                
                # Store burn request in database
                with self.db_connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO shield_token_burn_requests 
                        (token_id, serial_number, requester_address, status, created_at)
                        VALUES (%s, %s, %s, 'pending', %s)
                        RETURNING id
                        """,
                        (token_id, validation['serial_number'], requester_address, datetime.now(timezone.utc))
                    )
                    request_id = cursor.fetchone()[0]
                    self.db_connection.commit()
                
                # Cache the request for fast lookup
                cache_key = f"burn_request:{request_id}"
                cache_data = {
                    'token_id': token_id,
                    'serial_number': validation['serial_number'],
                    'requester_address': requester_address,
                    'status': 'pending',
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
                
                await asyncio.to_thread(
                    self.redis_client.setex,
                    cache_key,
                    3600,  # 1 hour expiry
                    json.dumps(cache_data)
                )
                
                shield_token_operations.labels('burn', 'success').inc()
                
                result = {
                    'success': True,
                    'request_id': request_id,
                    'token_id': token_id,
                    'serial_number': validation['serial_number'],
                    'status': 'pending',
                    'estimated_processing_time': '5-10 minutes'
                }
                
                # Log audit event
                log_audit_event(
                    'shield_token_burn_request',
                    result,
                    ['ERC-8055', 'SHIELD_TOKEN', 'BURN_REQUEST', 'COMPLIANCE']
                )
                
                return result
                
            except Exception as e:
                logger.error(f"Burn request processing failed: {e}")
                shield_token_operations.labels('burn', 'error').inc()
                return {'success': False, 'error': str(e)}
    
    async def process_remint_request(self, to_address: str, original_token_id: int, new_serial: str) -> Dict[str, Any]:
        """Process Shield Token remint request"""
        with function_execution_time.labels('remint_request').time():
            try:
                # Validate new serial number format
                if not self._validate_serial_format(new_serial):
                    shield_token_operations.labels('remint', 'invalid_serial').inc()
                    return {
                        'success': False,
                        'error': f'Invalid serial number format: {new_serial}'
                    }
                
                # Check if original token was burned
                with self.db_connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT status FROM shield_token_burn_requests 
                        WHERE token_id = %s AND status = 'completed'
                        ORDER BY created_at DESC LIMIT 1
                        """,
                        (original_token_id,)
                    )
                    
                    if not cursor.fetchone():
                        shield_token_operations.labels('remint', 'token_not_burned').inc()
                        return {
                            'success': False,
                            'error': 'Original token must be burned before reminting'
                        }
                
                # Store remint request
                with self.db_connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO shield_token_remint_requests
                        (original_token_id, to_address, new_serial_number, status, created_at)
                        VALUES (%s, %s, %s, 'pending', %s)
                        RETURNING id
                        """,
                        (original_token_id, to_address, new_serial, datetime.now(timezone.utc))
                    )
                    request_id = cursor.fetchone()[0]
                    self.db_connection.commit()
                
                shield_token_operations.labels('remint', 'success').inc()
                
                result = {
                    'success': True,
                    'request_id': request_id,
                    'original_token_id': original_token_id,
                    'to_address': to_address,
                    'new_serial_number': new_serial,
                    'status': 'pending'
                }
                
                # Log audit event
                log_audit_event(
                    'shield_token_remint_request',
                    result,
                    ['ERC-8055', 'SHIELD_TOKEN', 'REMINT_REQUEST', 'COMPLIANCE']
                )
                
                return result
                
            except Exception as e:
                logger.error(f"Remint request processing failed: {e}")
                shield_token_operations.labels('remint', 'error').inc()
                return {'success': False, 'error': str(e)}

# Global processor instance
processor = ShieldTokenProcessor()

# Azure Function endpoints
@func.route(route="erc8055/validate/{token_id:int}", auth_level=func.AuthLevel.FUNCTION, methods=["GET"])
async def validate_shield_token(req: func.HttpRequest) -> func.HttpResponse:
    """Validate ERC-8055 Shield Token"""
    try:
        token_id = int(req.route_params.get('token_id'))
        
        await processor.init_connections()
        result = processor.validate_shield_token(token_id)
        
        return func.HttpResponse(
            json.dumps(result),
            status_code=200 if result['valid'] else 400,
            mimetype="application/json"
        )
    except Exception as e:
        logger.error(f"Token validation endpoint failed: {e}")
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@func.route(route="erc8055/burn", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
async def burn_shield_token(req: func.HttpRequest) -> func.HttpResponse:
    """Process Shield Token burn request"""
    try:
        req_data = req.get_json()
        token_id = req_data.get('token_id')
        requester_address = req_data.get('requester_address')
        
        if not token_id or not requester_address:
            return func.HttpResponse(
                json.dumps({'error': 'token_id and requester_address required'}),
                status_code=400,
                mimetype="application/json"
            )
        
        await processor.init_connections()
        result = await processor.process_burn_request(token_id, requester_address)
        
        return func.HttpResponse(
            json.dumps(result),
            status_code=200 if result['success'] else 400,
            mimetype="application/json"
        )
    except Exception as e:
        logger.error(f"Burn request endpoint failed: {e}")
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@func.route(route="erc8055/remint", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
async def remint_shield_token(req: func.HttpRequest) -> func.HttpResponse:
    """Process Shield Token remint request"""
    try:
        req_data = req.get_json()
        to_address = req_data.get('to_address')
        original_token_id = req_data.get('original_token_id')
        new_serial = req_data.get('new_serial_number')
        
        if not all([to_address, original_token_id, new_serial]):
            return func.HttpResponse(
                json.dumps({'error': 'to_address, original_token_id, and new_serial_number required'}),
                status_code=400,
                mimetype="application/json"
            )
        
        await processor.init_connections()
        result = await processor.process_remint_request(to_address, original_token_id, new_serial)
        
        return func.HttpResponse(
            json.dumps(result),
            status_code=200 if result['success'] else 400,
            mimetype="application/json"
        )
    except Exception as e:
        logger.error(f"Remint request endpoint failed: {e}")
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            status_code=500,
            mimetype="application/json"
        )