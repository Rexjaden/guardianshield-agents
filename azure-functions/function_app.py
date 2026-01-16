#!/usr/bin/env python3
"""
GuardianShield Azure Functions Application
Enterprise-grade serverless functions for ERC-8055 token ecosystem

Functions:
- ERC-8055 Shield Token processing
- Blockchain transaction indexing
- Fraud detection and compliance
- Real-time analytics and monitoring
- Regulatory reporting
"""

import azure.functions as func
import logging
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import asyncio
import aiohttp
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from azure.cosmos import CosmosClient
import psycopg2
from web3 import Web3
import pandas as pd
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Configure enterprise logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger('GuardianShield-AzureFunctions')

# Initialize Azure Function App
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Prometheus metrics
shield_token_operations = Counter('shield_token_operations_total', 'Total Shield Token operations', ['operation_type', 'status'])
blockchain_blocks_processed = Counter('blockchain_blocks_processed_total', 'Total blockchain blocks processed')
fraud_detections = Counter('fraud_detections_total', 'Total fraud detections', ['severity'])
function_execution_time = Histogram('function_execution_seconds', 'Function execution time', ['function_name'])
active_connections = Gauge('database_active_connections', 'Active database connections')

# Global configuration
class GuardianShieldConfig:
    """Centralized configuration management"""
    
    def __init__(self):
        # Azure services
        self.subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
        self.resource_group = os.getenv('AZURE_RESOURCE_GROUP', 'guardianshield-rg')
        self.key_vault_url = os.getenv('AZURE_KEY_VAULT_URL')
        
        # Database configuration
        self.database_host = os.getenv('DATABASE_HOST', 'guardianshield-database')
        self.database_port = int(os.getenv('DATABASE_PORT', '5432'))
        
        # Blockchain configuration
        self.ethereum_rpc_url = os.getenv('ETHEREUM_RPC_URL')
        self.shield_token_address = os.getenv('SHIELD_TOKEN_CONTRACT_ADDRESS')
        self.guard_token_address = os.getenv('GUARD_TOKEN_CONTRACT_ADDRESS')
        
        # Compliance settings
        self.compliance_mode = os.getenv('COMPLIANCE_MODE', 'STRICT')
        self.audit_log_retention_days = int(os.getenv('AUDIT_LOG_RETENTION_DAYS', '2555'))  # 7 years
        
        # Initialize Azure clients
        self._init_azure_clients()
        
        # Initialize blockchain connection
        self._init_blockchain_connection()
    
    def _init_azure_clients(self):
        """Initialize Azure SDK clients"""
        try:
            self.credential = DefaultAzureCredential()
            
            if self.key_vault_url:
                self.key_vault_client = SecretClient(
                    vault_url=self.key_vault_url,
                    credential=self.credential
                )
            
            # Storage account for backup and logging
            storage_account_url = os.getenv('AZURE_STORAGE_ACCOUNT_URL')
            if storage_account_url:
                self.blob_client = BlobServiceClient(
                    account_url=storage_account_url,
                    credential=self.credential
                )
            
            # Service Bus for message queuing
            service_bus_namespace = os.getenv('AZURE_SERVICE_BUS_NAMESPACE')
            if service_bus_namespace:
                self.service_bus_client = ServiceBusClient(
                    fully_qualified_namespace=service_bus_namespace,
                    credential=self.credential
                )
            
            # Cosmos DB for analytics
            cosmos_endpoint = os.getenv('AZURE_COSMOS_ENDPOINT')
            if cosmos_endpoint:
                self.cosmos_client = CosmosClient(
                    url=cosmos_endpoint,
                    credential=self.credential
                )
            
            logger.info("Azure clients initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Azure clients: {e}")
            raise
    
    def _init_blockchain_connection(self):
        """Initialize blockchain connection"""
        try:
            if self.ethereum_rpc_url:
                self.web3 = Web3(Web3.HTTPProvider(self.ethereum_rpc_url))
                if self.web3.is_connected():
                    logger.info("Blockchain connection established")
                else:
                    logger.warning("Blockchain connection failed")
            else:
                logger.warning("No Ethereum RPC URL configured")
        except Exception as e:
            logger.error(f"Failed to initialize blockchain connection: {e}")
    
    def get_secret(self, secret_name: str) -> Optional[str]:
        """Retrieve secret from Azure Key Vault"""
        try:
            if hasattr(self, 'key_vault_client'):
                secret = self.key_vault_client.get_secret(secret_name)
                return secret.value
            else:
                logger.warning("Key Vault client not initialized")
                return os.getenv(secret_name)
        except Exception as e:
            logger.error(f"Failed to retrieve secret {secret_name}: {e}")
            return os.getenv(secret_name)
    
    def get_database_connection(self, database_name: str = 'erc8055_tokens'):
        """Get database connection with connection pooling"""
        try:
            password = self.get_secret(f'DATABASE_{database_name.upper()}_PASSWORD')
            username = self.get_secret(f'DATABASE_{database_name.upper()}_USERNAME')
            
            conn = psycopg2.connect(
                host=self.database_host,
                port=self.database_port,
                database=database_name,
                user=username,
                password=password,
                sslmode='require',
                connect_timeout=10
            )
            
            active_connections.inc()
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

# Global configuration instance
config = GuardianShieldConfig()

# Utility functions
def log_audit_event(event_type: str, details: Dict[str, Any], compliance_flags: List[str] = None):
    """Log audit event for compliance tracking"""
    audit_entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'event_type': event_type,
        'details': details,
        'compliance_flags': compliance_flags or [],
        'function_name': 'azure-functions',
        'compliance_mode': config.compliance_mode
    }
    
    logger.info(f"AUDIT: {json.dumps(audit_entry)}")
    
    # Store in Cosmos DB for long-term retention
    try:
        if hasattr(config, 'cosmos_client'):
            database = config.cosmos_client.get_database_client('guardianshield')
            container = database.get_container_client('audit_logs')
            container.create_item(audit_entry)
    except Exception as e:
        logger.warning(f"Failed to store audit log in Cosmos DB: {e}")

# Health check endpoint
@app.route(route="health", auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint for monitoring"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': '2.0.0',
        'services': {
            'database': 'unknown',
            'blockchain': 'unknown',
            'key_vault': 'unknown'
        }
    }
    
    # Check database connectivity
    try:
        conn = config.get_database_connection()
        with conn.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        conn.close()
        active_connections.dec()
        health_status['services']['database'] = 'healthy'
    except Exception as e:
        health_status['services']['database'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'degraded'
    
    # Check blockchain connectivity
    try:
        if hasattr(config, 'web3') and config.web3.is_connected():
            block_number = config.web3.eth.block_number
            health_status['services']['blockchain'] = f'healthy (block: {block_number})'
        else:
            health_status['services']['blockchain'] = 'disconnected'
    except Exception as e:
        health_status['services']['blockchain'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'degraded'
    
    # Check Key Vault connectivity
    try:
        if hasattr(config, 'key_vault_client'):
            # Test Key Vault access
            test_secret = config.get_secret('test-connection')
            health_status['services']['key_vault'] = 'healthy'
        else:
            health_status['services']['key_vault'] = 'not_configured'
    except Exception as e:
        health_status['services']['key_vault'] = f'unhealthy: {str(e)}'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return func.HttpResponse(
        json.dumps(health_status),
        status_code=status_code,
        mimetype="application/json"
    )

# Metrics endpoint for Prometheus
@app.route(route="metrics", auth_level=func.AuthLevel.ANONYMOUS)
def metrics(req: func.HttpRequest) -> func.HttpResponse:
    """Prometheus metrics endpoint"""
    try:
        metrics_data = generate_latest()
        return func.HttpResponse(
            metrics_data,
            status_code=200,
            mimetype="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        logger.error(f"Failed to generate metrics: {e}")
        return func.HttpResponse("Error generating metrics", status_code=500)

# Import specialized function modules
try:
    from .erc8055_processor import *  # ERC-8055 token processing functions
    from .blockchain_indexer import *  # Blockchain indexing functions
    from .fraud_detector import *  # Fraud detection functions
    from .compliance_reporter import *  # Compliance reporting functions
    from .analytics_processor import *  # Analytics functions
except ImportError as e:
    logger.warning(f"Some function modules not available: {e}")

if __name__ == '__main__':
    # Development server (not used in production)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7071)