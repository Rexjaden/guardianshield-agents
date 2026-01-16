# DHI-Vault: Distributed HashiCorp Intelligence Vault
# Advanced API Management System for GuardianShield

import asyncio
import json
import logging
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

import aioredis
import aiojobs
from aiohttp import web, ClientSession
import aiofiles
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import hvac
import kubernetes
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APIKeyStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    EXPIRED = "expired"

class ClientTier(Enum):
    BASIC = "basic"
    PREMIUM = "premium" 
    ENTERPRISE = "enterprise"
    DEVELOPER = "developer"

@dataclass
class APIKey:
    key_id: str
    client_id: str
    key_hash: str
    status: APIKeyStatus
    tier: ClientTier
    created_at: datetime
    expires_at: Optional[datetime]
    last_used: Optional[datetime]
    usage_count: int
    rate_limit: int
    scopes: List[str]
    metadata: Dict[str, Any]

@dataclass
class ClientCredentials:
    client_id: str
    client_secret: str
    client_name: str
    redirect_uris: List[str]
    scopes: List[str]
    tier: ClientTier
    created_at: datetime
    is_active: bool

class DHIVaultAPIManager:
    """
    Distributed HashiCorp Intelligence Vault API Manager
    Advanced API management system with comprehensive security features
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.vault_client = None
        self.redis_client = None
        self.k8s_client = None
        
        # Encryption
        self.encryption_key = self._generate_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        
        # RSA key pair for JWT signing
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
        
        # Metrics
        self.api_requests_total = Counter(
            'dhi_vault_api_requests_total', 
            'Total API requests', 
            ['method', 'endpoint', 'status']
        )
        self.api_request_duration = Histogram(
            'dhi_vault_api_request_duration_seconds',
            'API request duration'
        )
        self.active_api_keys = Gauge(
            'dhi_vault_active_api_keys_total',
            'Number of active API keys'
        )
        self.vault_operations = Counter(
            'dhi_vault_operations_total',
            'Total Vault operations',
            ['operation', 'status']
        )
        
        # Rate limiting
        self.rate_limit_windows = {}
        
    async def initialize(self):
        """Initialize all connections and services"""
        try:
            await self._init_vault_client()
            await self._init_redis_client()
            await self._init_kubernetes_client()
            await self._setup_vault_engines()
            await self._setup_auth_methods()
            await self._load_existing_data()
            
            logger.info("DHI-Vault API Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize DHI-Vault: {e}")
            raise
    
    async def _init_vault_client(self):
        """Initialize HashiCorp Vault client"""
        vault_config = self.config.get('vault', {})
        
        self.vault_client = hvac.Client(
            url=vault_config.get('url', 'https://vault.guardianshield.svc.cluster.local:8200'),
            token=vault_config.get('token'),
            verify=vault_config.get('verify_tls', True)
        )
        
        # Authenticate with Kubernetes if token not provided
        if not vault_config.get('token'):
            await self._authenticate_with_kubernetes()
        
        # Verify connection
        if not self.vault_client.is_authenticated():
            raise Exception("Failed to authenticate with Vault")
            
        logger.info("Vault client initialized successfully")
    
    async def _init_redis_client(self):
        """Initialize Redis client for caching and rate limiting"""
        redis_config = self.config.get('redis', {})
        
        self.redis_client = await aioredis.from_url(
            redis_config.get('url', 'redis://redis.guardianshield.svc.cluster.local:6379'),
            encoding='utf-8',
            decode_responses=True,
            max_connections=20
        )
        
        # Test connection
        await self.redis_client.ping()
        logger.info("Redis client initialized successfully")
    
    async def _init_kubernetes_client(self):
        """Initialize Kubernetes client"""
        try:
            kubernetes.config.load_incluster_config()
            self.k8s_client = kubernetes.client.ApiClient()
            logger.info("Kubernetes client initialized successfully")
        except:
            logger.warning("Failed to initialize Kubernetes client - running outside cluster")
    
    async def _setup_vault_engines(self):
        """Setup Vault secrets engines"""
        engines = [
            {
                'path': 'guardianshield/dhi-vault',
                'type': 'kv',
                'options': {'version': '2'},
                'description': 'DHI-Vault API secrets'
            },
            {
                'path': 'guardianshield/api-keys',
                'type': 'kv', 
                'options': {'version': '2'},
                'description': 'API key metadata storage'
            },
            {
                'path': 'guardianshield/oauth2',
                'type': 'kv',
                'options': {'version': '2'}, 
                'description': 'OAuth2 client credentials'
            },
            {
                'path': 'pki/dhi-vault',
                'type': 'pki',
                'config': {
                    'max_lease_ttl': '8760h',
                    'default_lease_ttl': '720h'
                },
                'description': 'DHI-Vault PKI engine'
            }
        ]
        
        for engine in engines:
            try:
                if not self.vault_client.sys.is_secret_backend_enabled(engine['path']):
                    self.vault_client.sys.enable_secrets_engine(
                        backend_type=engine['type'],
                        path=engine['path'],
                        description=engine['description'],
                        options=engine.get('options'),
                        config=engine.get('config')
                    )
                    logger.info(f"Enabled secrets engine: {engine['path']}")
                    
            except Exception as e:
                logger.error(f"Failed to setup engine {engine['path']}: {e}")
    
    async def _setup_auth_methods(self):
        """Setup Vault authentication methods"""
        auth_methods = [
            {
                'type': 'kubernetes',
                'path': 'kubernetes',
                'description': 'Kubernetes service account authentication'
            },
            {
                'type': 'jwt',
                'path': 'jwt',
                'description': 'JWT token authentication'
            },
            {
                'type': 'userpass',
                'path': 'userpass',
                'description': 'Username/password authentication'
            }
        ]
        
        for method in auth_methods:
            try:
                if not self.vault_client.sys.is_auth_method_enabled(method['path']):
                    self.vault_client.sys.enable_auth_method(
                        method_type=method['type'],
                        path=method['path'],
                        description=method['description']
                    )
                    logger.info(f"Enabled auth method: {method['path']}")
                    
            except Exception as e:
                logger.error(f"Failed to setup auth method {method['path']}: {e}")
    
    async def create_api_key(
        self, 
        client_id: str,
        tier: ClientTier = ClientTier.BASIC,
        scopes: List[str] = None,
        expires_in: Optional[int] = None,
        metadata: Dict[str, Any] = None
    ) -> Tuple[str, APIKey]:
        """
        Create a new API key for a client
        
        Args:
            client_id: Unique client identifier
            tier: Client tier for rate limiting
            scopes: List of allowed scopes
            expires_in: Expiration time in seconds
            metadata: Additional metadata
            
        Returns:
            Tuple of (api_key_string, APIKey object)
        """
        try:
            # Generate secure API key
            key_id = secrets.token_urlsafe(16)
            api_key = f"dhi_{key_id}_{secrets.token_urlsafe(32)}"
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Set expiration
            expires_at = None
            if expires_in:
                expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            # Create API key object
            api_key_obj = APIKey(
                key_id=key_id,
                client_id=client_id,
                key_hash=key_hash,
                status=APIKeyStatus.ACTIVE,
                tier=tier,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                last_used=None,
                usage_count=0,
                rate_limit=self._get_tier_rate_limit(tier),
                scopes=scopes or ['read'],
                metadata=metadata or {}
            )
            
            # Store in Vault
            await self._store_api_key(api_key_obj)
            
            # Cache in Redis
            await self._cache_api_key(api_key_obj)
            
            # Update metrics
            self.active_api_keys.inc()
            self.vault_operations.labels(operation='create_api_key', status='success').inc()
            
            logger.info(f"Created API key for client {client_id}")
            return api_key, api_key_obj
            
        except Exception as e:
            logger.error(f"Failed to create API key: {e}")
            self.vault_operations.labels(operation='create_api_key', status='error').inc()
            raise
    
    async def validate_api_key(self, api_key: str) -> Optional[APIKey]:
        """
        Validate an API key and return associated metadata
        
        Args:
            api_key: API key string to validate
            
        Returns:
            APIKey object if valid, None if invalid
        """
        try:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Check Redis cache first
            cached_key = await self._get_cached_api_key(key_hash)
            if cached_key:
                if await self._is_key_valid(cached_key):
                    await self._update_key_usage(cached_key)
                    return cached_key
                else:
                    await self._invalidate_cached_key(key_hash)
                    return None
            
            # Fallback to Vault
            api_key_obj = await self._load_api_key_from_vault(key_hash)
            if api_key_obj and await self._is_key_valid(api_key_obj):
                await self._cache_api_key(api_key_obj)
                await self._update_key_usage(api_key_obj)
                return api_key_obj
                
            return None
            
        except Exception as e:
            logger.error(f"Failed to validate API key: {e}")
            return None
    
    async def revoke_api_key(self, key_id: str) -> bool:
        """
        Revoke an API key
        
        Args:
            key_id: API key ID to revoke
            
        Returns:
            True if successfully revoked
        """
        try:
            # Load key from Vault
            api_key_obj = await self._load_api_key_by_id(key_id)
            if not api_key_obj:
                return False
                
            # Update status
            api_key_obj.status = APIKeyStatus.REVOKED
            
            # Store in Vault
            await self._store_api_key(api_key_obj)
            
            # Remove from cache
            await self._invalidate_cached_key(api_key_obj.key_hash)
            
            # Update metrics
            self.active_api_keys.dec()
            self.vault_operations.labels(operation='revoke_api_key', status='success').inc()
            
            logger.info(f"Revoked API key: {key_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke API key {key_id}: {e}")
            self.vault_operations.labels(operation='revoke_api_key', status='error').inc()
            return False
    
    async def create_oauth2_client(
        self,
        client_name: str,
        redirect_uris: List[str],
        scopes: List[str],
        tier: ClientTier = ClientTier.BASIC
    ) -> ClientCredentials:
        """
        Create OAuth2 client credentials
        
        Args:
            client_name: Human readable client name
            redirect_uris: List of allowed redirect URIs
            scopes: List of allowed scopes
            tier: Client tier
            
        Returns:
            ClientCredentials object
        """
        try:
            client_id = f"dhi_{secrets.token_urlsafe(16)}"
            client_secret = secrets.token_urlsafe(32)
            
            credentials = ClientCredentials(
                client_id=client_id,
                client_secret=client_secret,
                client_name=client_name,
                redirect_uris=redirect_uris,
                scopes=scopes,
                tier=tier,
                created_at=datetime.utcnow(),
                is_active=True
            )
            
            # Store in Vault
            await self._store_oauth2_client(credentials)
            
            # Cache in Redis
            await self._cache_oauth2_client(credentials)
            
            self.vault_operations.labels(operation='create_oauth2_client', status='success').inc()
            
            logger.info(f"Created OAuth2 client: {client_name}")
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to create OAuth2 client: {e}")
            self.vault_operations.labels(operation='create_oauth2_client', status='error').inc()
            raise
    
    async def generate_jwt_token(
        self,
        client_id: str,
        scopes: List[str],
        audience: str = "dhi-vault-api",
        expires_in: int = 3600
    ) -> str:
        """
        Generate JWT access token
        
        Args:
            client_id: Client identifier
            scopes: Granted scopes
            audience: Token audience
            expires_in: Token expiration in seconds
            
        Returns:
            JWT token string
        """
        try:
            now = datetime.utcnow()
            payload = {
                'iss': 'dhi-vault-api',
                'aud': audience,
                'sub': client_id,
                'iat': now,
                'exp': now + timedelta(seconds=expires_in),
                'scope': ' '.join(scopes),
                'jti': secrets.token_urlsafe(16)
            }
            
            # Sign with RSA private key
            token = jwt.encode(
                payload,
                self.private_key,
                algorithm='RS256',
                headers={'kid': 'dhi-vault-key-1'}
            )
            
            # Cache token metadata
            await self.redis_client.setex(
                f"jwt_token:{payload['jti']}",
                expires_in,
                json.dumps({
                    'client_id': client_id,
                    'scopes': scopes,
                    'created_at': now.isoformat()
                })
            )
            
            return token
            
        except Exception as e:
            logger.error(f"Failed to generate JWT token: {e}")
            raise
    
    async def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token and return payload
        
        Args:
            token: JWT token to verify
            
        Returns:
            Token payload if valid, None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=['RS256'],
                audience="dhi-vault-api",
                issuer="dhi-vault-api"
            )
            
            # Check if token is revoked
            token_info = await self.redis_client.get(f"jwt_token:{payload['jti']}")
            if not token_info:
                return None
                
            return payload
            
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to verify JWT token: {e}")
            return None
    
    async def check_rate_limit(self, client_id: str, tier: ClientTier) -> bool:
        """
        Check if client is within rate limits
        
        Args:
            client_id: Client identifier
            tier: Client tier
            
        Returns:
            True if within limits, False if exceeded
        """
        try:
            rate_limit = self._get_tier_rate_limit(tier)
            window_key = f"rate_limit:{client_id}:{int(datetime.utcnow().timestamp() // 3600)}"
            
            current_requests = await self.redis_client.get(window_key)
            if current_requests is None:
                await self.redis_client.setex(window_key, 3600, 1)
                return True
                
            if int(current_requests) >= rate_limit:
                return False
                
            await self.redis_client.incr(window_key)
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return False
    
    async def get_api_usage_stats(self, client_id: str) -> Dict[str, Any]:
        """
        Get API usage statistics for a client
        
        Args:
            client_id: Client identifier
            
        Returns:
            Dictionary with usage statistics
        """
        try:
            # Get all API keys for client
            api_keys = await self._load_client_api_keys(client_id)
            
            total_usage = sum(key.usage_count for key in api_keys)
            active_keys = len([key for key in api_keys if key.status == APIKeyStatus.ACTIVE])
            
            # Get current hour usage from Redis
            current_hour = int(datetime.utcnow().timestamp() // 3600)
            current_usage = await self.redis_client.get(f"rate_limit:{client_id}:{current_hour}")
            
            return {
                'client_id': client_id,
                'total_usage': total_usage,
                'active_keys': active_keys,
                'current_hour_usage': int(current_usage) if current_usage else 0,
                'api_keys': [
                    {
                        'key_id': key.key_id,
                        'status': key.status.value,
                        'created_at': key.created_at.isoformat(),
                        'last_used': key.last_used.isoformat() if key.last_used else None,
                        'usage_count': key.usage_count,
                        'scopes': key.scopes
                    }
                    for key in api_keys
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check
        
        Returns:
            Dictionary with health status
        """
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {}
        }
        
        # Check Vault connection
        try:
            vault_health = self.vault_client.sys.read_health_status()
            health_status['services']['vault'] = {
                'status': 'healthy' if vault_health['initialized'] else 'unhealthy',
                'sealed': vault_health.get('sealed', True),
                'initialized': vault_health.get('initialized', False)
            }
        except Exception as e:
            health_status['services']['vault'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['status'] = 'degraded'
        
        # Check Redis connection
        try:
            await self.redis_client.ping()
            health_status['services']['redis'] = {'status': 'healthy'}
        except Exception as e:
            health_status['services']['redis'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['status'] = 'degraded'
        
        # Check Kubernetes connection
        if self.k8s_client:
            try:
                v1 = kubernetes.client.CoreV1Api(self.k8s_client)
                v1.list_namespace(timeout_seconds=5)
                health_status['services']['kubernetes'] = {'status': 'healthy'}
            except Exception as e:
                health_status['services']['kubernetes'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
        
        return health_status
    
    async def get_metrics(self) -> str:
        """Get Prometheus metrics"""
        return generate_latest()
    
    # Private helper methods
    
    def _generate_encryption_key(self) -> bytes:
        """Generate encryption key for sensitive data"""
        password = self.config.get('encryption_password', 'default-password').encode()
        salt = self.config.get('encryption_salt', 'default-salt').encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return Fernet.generate_key()
    
    def _get_tier_rate_limit(self, tier: ClientTier) -> int:
        """Get rate limit for client tier"""
        limits = {
            ClientTier.BASIC: 1000,
            ClientTier.PREMIUM: 5000,
            ClientTier.ENTERPRISE: 20000,
            ClientTier.DEVELOPER: 10000
        }
        return limits.get(tier, 1000)
    
    async def _store_api_key(self, api_key: APIKey):
        """Store API key in Vault"""
        data = {
            'key_id': api_key.key_id,
            'client_id': api_key.client_id,
            'key_hash': api_key.key_hash,
            'status': api_key.status.value,
            'tier': api_key.tier.value,
            'created_at': api_key.created_at.isoformat(),
            'expires_at': api_key.expires_at.isoformat() if api_key.expires_at else None,
            'last_used': api_key.last_used.isoformat() if api_key.last_used else None,
            'usage_count': api_key.usage_count,
            'rate_limit': api_key.rate_limit,
            'scopes': api_key.scopes,
            'metadata': api_key.metadata
        }
        
        self.vault_client.secrets.kv.v2.create_or_update_secret(
            path=f'guardianshield/api-keys/{api_key.key_id}',
            secret=data
        )
    
    async def _cache_api_key(self, api_key: APIKey):
        """Cache API key in Redis"""
        data = {
            'key_id': api_key.key_id,
            'client_id': api_key.client_id,
            'status': api_key.status.value,
            'tier': api_key.tier.value,
            'expires_at': api_key.expires_at.isoformat() if api_key.expires_at else None,
            'rate_limit': api_key.rate_limit,
            'scopes': api_key.scopes
        }
        
        await self.redis_client.setex(
            f"api_key:{api_key.key_hash}",
            3600,  # 1 hour cache
            json.dumps(data, default=str)
        )
    
    async def _get_cached_api_key(self, key_hash: str) -> Optional[APIKey]:
        """Get API key from Redis cache"""
        cached_data = await self.redis_client.get(f"api_key:{key_hash}")
        if not cached_data:
            return None
            
        data = json.loads(cached_data)
        return APIKey(
            key_id=data['key_id'],
            client_id=data['client_id'],
            key_hash=key_hash,
            status=APIKeyStatus(data['status']),
            tier=ClientTier(data['tier']),
            created_at=datetime.utcnow(),  # Simplified for cache
            expires_at=datetime.fromisoformat(data['expires_at']) if data['expires_at'] else None,
            last_used=None,
            usage_count=0,
            rate_limit=data['rate_limit'],
            scopes=data['scopes'],
            metadata={}
        )
    
    async def _is_key_valid(self, api_key: APIKey) -> bool:
        """Check if API key is valid"""
        if api_key.status != APIKeyStatus.ACTIVE:
            return False
            
        if api_key.expires_at and datetime.utcnow() > api_key.expires_at:
            return False
            
        return True
    
    async def _update_key_usage(self, api_key: APIKey):
        """Update API key usage statistics"""
        # Increment usage in Redis (for quick updates)
        await self.redis_client.incr(f"usage:{api_key.key_id}")
        
        # Update last used timestamp every 5 minutes to reduce Vault writes
        last_update_key = f"last_update:{api_key.key_id}"
        last_update = await self.redis_client.get(last_update_key)
        
        if not last_update or (datetime.utcnow().timestamp() - float(last_update)) > 300:
            api_key.last_used = datetime.utcnow()
            api_key.usage_count += 1
            await self._store_api_key(api_key)
            await self.redis_client.set(last_update_key, datetime.utcnow().timestamp())
    
    async def _load_existing_data(self):
        """Load existing API keys and update metrics"""
        try:
            # Get list of API keys from Vault
            result = self.vault_client.secrets.kv.v2.list_secrets(
                path='guardianshield/api-keys'
            )
            
            if result and 'data' in result and 'keys' in result['data']:
                active_count = 0
                for key_id in result['data']['keys']:
                    key_data = self.vault_client.secrets.kv.v2.read_secret_version(
                        path=f'guardianshield/api-keys/{key_id}'
                    )
                    
                    if key_data and key_data['data']['data']['status'] == 'active':
                        active_count += 1
                
                self.active_api_keys.set(active_count)
                logger.info(f"Loaded {active_count} active API keys")
                
        except Exception as e:
            logger.error(f"Failed to load existing data: {e}")
    
    async def _authenticate_with_kubernetes(self):
        """Authenticate with Vault using Kubernetes service account"""
        try:
            # Read service account token
            with open('/var/run/secrets/kubernetes.io/serviceaccount/token', 'r') as f:
                jwt_token = f.read()
            
            # Authenticate with Vault
            response = self.vault_client.auth.kubernetes.login(
                role='dhi-vault-api',
                jwt=jwt_token
            )
            
            self.vault_client.token = response['auth']['client_token']
            logger.info("Authenticated with Vault using Kubernetes service account")
            
        except Exception as e:
            logger.error(f"Failed to authenticate with Kubernetes: {e}")
            raise

if __name__ == "__main__":
    import yaml
    
    # Load configuration
    config = {
        'vault': {
            'url': 'https://vault.guardianshield.svc.cluster.local:8200',
            'verify_tls': True
        },
        'redis': {
            'url': 'redis://redis.guardianshield.svc.cluster.local:6379'
        },
        'encryption_password': 'dhi-vault-secure-key',
        'encryption_salt': 'dhi-vault-salt'
    }
    
    # Initialize DHI-Vault
    vault_manager = DHIVaultAPIManager(config)
    
    async def main():
        await vault_manager.initialize()
        
        # Example usage
        api_key, key_obj = await vault_manager.create_api_key(
            client_id="example-client",
            tier=ClientTier.PREMIUM,
            scopes=['read', 'write'],
            expires_in=86400  # 24 hours
        )
        
        print(f"Created API key: {api_key}")
        
        # Validate the key
        validated_key = await vault_manager.validate_api_key(api_key)
        print(f"Validated key: {validated_key.key_id if validated_key else 'Invalid'}")
        
        # Health check
        health = await vault_manager.health_check()
        print(f"Health status: {health['status']}")
    
    asyncio.run(main())