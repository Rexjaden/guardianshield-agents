#!/usr/bin/env python3
"""
GuardianShield Vault CSI Provider API Management System
Manages HashiCorp Vault with CSI provider for secure API key management, 
OAuth2 authentication, and policy-based access control

This module provides:
- Vault cluster deployment and management
- API key rotation and lifecycle management
- JWT token generation and validation
- OAuth2 flow implementation
- Policy-based access control
- Secret injection via CSI provider
"""

import asyncio
import json
import subprocess
import yaml
import time
import logging
import hvac
import jwt as jwt_lib
import secrets
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from kubernetes import client, config as k8s_config
from kubernetes.client.rest import ApiException
import aiohttp
import redis.asyncio as aioredis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vault_api_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class APIKeyMetadata:
    """Metadata for API keys"""
    key_id: str
    api_key: str
    secret_key: str
    created_at: datetime
    expires_at: Optional[datetime]
    rate_limit_tier: str
    permissions: List[str]
    last_used: Optional[datetime]

@dataclass
class JWTToken:
    """JWT token structure"""
    token: str
    expires_at: datetime
    refresh_token: str
    user_id: str
    scopes: List[str]

class VaultAPIManager:
    """Manages Vault-based API management system for GuardianShield"""
    
    def __init__(
        self, 
        namespace: str = "guardianshield",
        vault_url: str = None,
        redis_url: str = None
    ):
        self.namespace = namespace
        self.vault_url = vault_url or f"https://vault.{namespace}.svc.cluster.local:8200"
        self.redis_url = redis_url or f"redis://redis.{namespace}.svc.cluster.local:6379"
        
        self.charts_dir = Path("charts")
        self.vault_chart = self.charts_dir / "vault-csi-provider"
        
        # Initialize clients
        try:
            k8s_config.load_incluster_config()
        except k8s_config.ConfigException:
            k8s_config.load_kube_config()
        
        self.k8s_client = client.ApiClient()
        self.apps_v1 = client.AppsV1Api()
        self.core_v1 = client.CoreV1Api()
        
        # Vault client
        self.vault_client = None
        self.redis_client = None
        
        # API management configuration
        self.api_keys = {}
        self.active_tokens = {}
        self.rate_limits = {
            'default': {'requests': 1000, 'period': 3600},
            'premium': {'requests': 10000, 'period': 3600},
            'enterprise': {'requests': 100000, 'period': 3600}
        }
        
        logger.info(f"VaultAPIManager initialized for namespace: {namespace}")
    
    async def initialize_connections(self):
        """Initialize Vault and Redis connections"""
        try:
            # Initialize Vault client
            self.vault_client = hvac.Client(url=self.vault_url)
            
            # Get Vault token from Kubernetes service account
            await self._authenticate_vault()
            
            # Initialize Redis client
            self.redis_client = aioredis.from_url(
                self.redis_url, 
                decode_responses=True,
                socket_keepalive=True,
                socket_keepalive_options={}
            )
            
            # Test connections
            if not self.vault_client.is_authenticated():
                raise Exception("Failed to authenticate with Vault")
            
            await self.redis_client.ping()
            logger.info("Successfully connected to Vault and Redis")
            
        except Exception as e:
            logger.error(f"Failed to initialize connections: {str(e)}")
            raise
    
    async def deploy_vault_cluster(self, values_override: Dict = None) -> Dict:
        """Deploy Vault cluster with CSI provider"""
        try:
            logger.info("Starting Vault cluster deployment with CSI provider")
            
            # Prepare Helm values
            values = {
                'global': {
                    'projectName': 'GuardianShield',
                    'environment': 'production',
                    'tlsDisable': False
                },
                'vault': {
                    'enabled': True,
                    'server': {
                        'ha': {
                            'enabled': True,
                            'replicas': 3,
                            'raft': {'enabled': True}
                        },
                        'dataStorage': {
                            'enabled': True,
                            'size': '20Gi',
                            'storageClass': 'fast-ssd'
                        },
                        'auditStorage': {
                            'enabled': True,
                            'size': '10Gi'
                        }
                    },
                    'csi': {'enabled': True},
                    'injector': {'enabled': True}
                },
                'apiManagement': {
                    'enabled': True,
                    'jwt': {
                        'expiration': 3600,
                        'issuer': 'guardianshield.io',
                        'audience': 'guardianshield-api'
                    }
                },
                'monitoring': {'enabled': True},
                'security': {
                    'networkPolicy': {'enabled': True}
                }
            }
            
            # Apply overrides
            if values_override:
                self._deep_update(values, values_override)
            
            # Create values file
            values_file = self.vault_chart / "values-deployment.yaml"
            with open(values_file, 'w') as f:
                yaml.dump(values, f, default_flow_style=False)
            
            # Deploy using Helm
            helm_cmd = [
                'helm', 'upgrade', '--install',
                'guardianshield-vault',
                str(self.vault_chart),
                '-n', self.namespace,
                '--create-namespace',
                '-f', str(values_file),
                '--wait',
                '--timeout', '900s'
            ]
            
            result = await self._run_command(helm_cmd)
            
            if result['success']:
                logger.info("Vault cluster deployed successfully")
                
                # Wait for Vault to be ready
                await self._wait_for_vault_ready()
                
                # Initialize Vault with GuardianShield configuration
                await self._initialize_vault_configuration()
                
                return {
                    'success': True,
                    'vault_url': self.vault_url,
                    'status': 'deployed'
                }
            else:
                logger.error(f"Failed to deploy Vault cluster: {result['error']}")
                return {'success': False, 'error': result['error']}
                
        except Exception as e:
            logger.error(f"Error deploying Vault cluster: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def create_api_key(
        self,
        user_id: str,
        tier: str = "default",
        permissions: List[str] = None,
        expires_days: Optional[int] = None
    ) -> APIKeyMetadata:
        """Create a new API key with specified permissions"""
        try:
            logger.info(f"Creating API key for user: {user_id}, tier: {tier}")
            
            # Generate API key and secret
            api_key = f"gk_{secrets.token_urlsafe(32)}"
            secret_key = secrets.token_urlsafe(64)
            key_id = f"key_{secrets.token_urlsafe(16)}"
            
            # Set expiration
            expires_at = None
            if expires_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_days)
            
            # Default permissions based on tier
            if permissions is None:
                permissions = self._get_default_permissions(tier)
            
            # Create metadata
            metadata = APIKeyMetadata(
                key_id=key_id,
                api_key=api_key,
                secret_key=secret_key,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                rate_limit_tier=tier,
                permissions=permissions,
                last_used=None
            )
            
            # Store in Vault
            vault_data = {
                'api_key': api_key,
                'secret_key': secret_key,
                'user_id': user_id,
                'tier': tier,
                'permissions': permissions,
                'created_at': metadata.created_at.isoformat(),
                'expires_at': expires_at.isoformat() if expires_at else None
            }
            
            vault_path = f"guardianshield/api/keys/{key_id}"
            self.vault_client.secrets.kv.v2.create_or_update_secret(
                path=vault_path,
                secret=vault_data
            )
            
            # Store in Redis for quick access
            redis_key = f"apikey:{api_key}"
            redis_data = {
                'key_id': key_id,
                'user_id': user_id,
                'tier': tier,
                'permissions': json.dumps(permissions),
                'created_at': metadata.created_at.isoformat()
            }
            
            await self.redis_client.hmset(redis_key, redis_data)
            if expires_at:
                await self.redis_client.expire(redis_key, int(expires_days * 24 * 3600))
            
            # Add to local cache
            self.api_keys[key_id] = metadata
            
            logger.info(f"API key created successfully: {key_id}")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to create API key: {str(e)}")
            raise
    
    async def validate_api_key(self, api_key: str, required_permission: str = None) -> Dict:
        """Validate API key and check permissions"""
        try:
            # Check Redis cache first
            redis_key = f"apikey:{api_key}"
            cached_data = await self.redis_client.hgetall(redis_key)
            
            if not cached_data:
                # Check Vault as fallback
                key_data = await self._get_api_key_from_vault(api_key)
                if not key_data:
                    return {'valid': False, 'error': 'Invalid API key'}
            else:
                key_data = cached_data
            
            # Check expiration
            if 'expires_at' in key_data and key_data['expires_at']:
                expires_at = datetime.fromisoformat(key_data['expires_at'])
                if datetime.utcnow() > expires_at:
                    return {'valid': False, 'error': 'API key expired'}
            
            # Check rate limiting
            if not await self._check_rate_limit(api_key, key_data['tier']):
                return {'valid': False, 'error': 'Rate limit exceeded'}
            
            # Check permissions
            if required_permission:
                permissions = json.loads(key_data.get('permissions', '[]'))
                if required_permission not in permissions:
                    return {'valid': False, 'error': 'Insufficient permissions'}
            
            # Update last used
            await self._update_api_key_usage(api_key)
            
            return {
                'valid': True,
                'user_id': key_data['user_id'],
                'tier': key_data['tier'],
                'permissions': json.loads(key_data.get('permissions', '[]'))
            }
            
        except Exception as e:
            logger.error(f"Failed to validate API key: {str(e)}")
            return {'valid': False, 'error': 'Validation error'}
    
    async def generate_jwt_token(
        self,
        user_id: str,
        scopes: List[str] = None,
        custom_claims: Dict = None
    ) -> JWTToken:
        """Generate JWT token with specified scopes"""
        try:
            logger.info(f"Generating JWT token for user: {user_id}")
            
            # Get JWT secret from Vault
            jwt_secret = await self._get_jwt_secret()
            
            # Set default scopes
            if scopes is None:
                scopes = ['api:read', 'threat-intel:read']
            
            # Token expiration
            expires_at = datetime.utcnow() + timedelta(seconds=3600)
            
            # Create token payload
            payload = {
                'sub': user_id,
                'iss': 'guardianshield.io',
                'aud': 'guardianshield-api',
                'exp': int(expires_at.timestamp()),
                'iat': int(datetime.utcnow().timestamp()),
                'scopes': scopes,
                'jti': secrets.token_urlsafe(16)
            }
            
            # Add custom claims
            if custom_claims:
                payload.update(custom_claims)
            
            # Generate token
            token = jwt_lib.encode(payload, jwt_secret, algorithm='HS256')
            
            # Generate refresh token
            refresh_token = secrets.token_urlsafe(64)
            
            # Store refresh token in Redis
            refresh_key = f"refresh:{refresh_token}"\n            refresh_data = {\n                'user_id': user_id,\n                'token_id': payload['jti'],\n                'scopes': json.dumps(scopes),\n                'created_at': datetime.utcnow().isoformat()\n            }\n            \n            await self.redis_client.hmset(refresh_key, refresh_data)\n            await self.redis_client.expire(refresh_key, 7 * 24 * 3600)  # 7 days\n            \n            # Create JWT token object\n            jwt_token = JWTToken(\n                token=token,\n                expires_at=expires_at,\n                refresh_token=refresh_token,\n                user_id=user_id,\n                scopes=scopes\n            )\n            \n            logger.info(f\"JWT token generated successfully for user: {user_id}\")\n            return jwt_token\n            \n        except Exception as e:\n            logger.error(f\"Failed to generate JWT token: {str(e)}\")\n            raise\n    \n    async def validate_jwt_token(self, token: str) -> Dict:\n        \"\"\"Validate JWT token and extract claims\"\"\"\n        try:\n            # Get JWT secret from Vault\n            jwt_secret = await self._get_jwt_secret()\n            \n            # Decode and validate token\n            payload = jwt_lib.decode(\n                token, \n                jwt_secret, \n                algorithms=['HS256'],\n                audience='guardianshield-api',\n                issuer='guardianshield.io'\n            )\n            \n            # Check if token is blacklisted\n            blacklist_key = f\"blacklist:{payload['jti']}\"\n            if await self.redis_client.exists(blacklist_key):\n                return {'valid': False, 'error': 'Token blacklisted'}\n            \n            return {\n                'valid': True,\n                'user_id': payload['sub'],\n                'scopes': payload.get('scopes', []),\n                'expires_at': datetime.fromtimestamp(payload['exp']),\n                'token_id': payload['jti']\n            }\n            \n        except jwt_lib.ExpiredSignatureError:\n            return {'valid': False, 'error': 'Token expired'}\n        except jwt_lib.InvalidTokenError as e:\n            return {'valid': False, 'error': f'Invalid token: {str(e)}'}\n        except Exception as e:\n            logger.error(f\"Failed to validate JWT token: {str(e)}\")\n            return {'valid': False, 'error': 'Validation error'}\n    \n    async def refresh_jwt_token(self, refresh_token: str) -> Optional[JWTToken]:\n        \"\"\"Refresh JWT token using refresh token\"\"\"\n        try:\n            refresh_key = f\"refresh:{refresh_token}\"\n            refresh_data = await self.redis_client.hgetall(refresh_key)\n            \n            if not refresh_data:\n                logger.warning(\"Invalid refresh token\")\n                return None\n            \n            user_id = refresh_data['user_id']\n            scopes = json.loads(refresh_data['scopes'])\n            \n            # Generate new JWT token\n            new_token = await self.generate_jwt_token(user_id, scopes)\n            \n            # Invalidate old refresh token\n            await self.redis_client.delete(refresh_key)\n            \n            logger.info(f\"JWT token refreshed for user: {user_id}\")\n            return new_token\n            \n        except Exception as e:\n            logger.error(f\"Failed to refresh JWT token: {str(e)}\")\n            return None\n    \n    async def revoke_api_key(self, key_id: str) -> bool:\n        \"\"\"Revoke an API key\"\"\"\n        try:\n            logger.info(f\"Revoking API key: {key_id}\")\n            \n            # Get API key data from Vault\n            vault_path = f\"guardianshield/api/keys/{key_id}\"\n            key_data = self.vault_client.secrets.kv.v2.read_secret_version(path=vault_path)\n            \n            if not key_data:\n                return False\n            \n            api_key = key_data['data']['data']['api_key']\n            \n            # Remove from Vault\n            self.vault_client.secrets.kv.v2.delete_metadata_and_all_versions(path=vault_path)\n            \n            # Remove from Redis\n            redis_key = f\"apikey:{api_key}\"\n            await self.redis_client.delete(redis_key)\n            \n            # Remove from local cache\n            if key_id in self.api_keys:\n                del self.api_keys[key_id]\n            \n            logger.info(f\"API key revoked successfully: {key_id}\")\n            return True\n            \n        except Exception as e:\n            logger.error(f\"Failed to revoke API key: {str(e)}\")\n            return False\n    \n    async def rotate_api_keys(self, days_before_expiration: int = 7) -> List[str]:\n        \"\"\"Rotate API keys that are close to expiration\"\"\"\n        try:\n            logger.info(\"Starting API key rotation\")\n            \n            rotated_keys = []\n            \n            # Get all API keys from Vault\n            keys_list = self.vault_client.secrets.kv.v2.list_secrets(path=\"guardianshield/api/keys\")\n            \n            for key_id in keys_list['data']['keys']:\n                vault_path = f\"guardianshield/api/keys/{key_id}\"\n                key_data = self.vault_client.secrets.kv.v2.read_secret_version(path=vault_path)\n                \n                expires_at_str = key_data['data']['data'].get('expires_at')\n                if not expires_at_str:\n                    continue\n                \n                expires_at = datetime.fromisoformat(expires_at_str)\n                days_until_expiry = (expires_at - datetime.utcnow()).days\n                \n                if days_until_expiry <= days_before_expiration:\n                    # Rotate the key\n                    user_id = key_data['data']['data']['user_id']\n                    tier = key_data['data']['data']['tier']\n                    permissions = key_data['data']['data']['permissions']\n                    \n                    # Create new key\n                    new_key = await self.create_api_key(\n                        user_id=user_id,\n                        tier=tier,\n                        permissions=permissions,\n                        expires_days=30\n                    )\n                    \n                    # Revoke old key\n                    await self.revoke_api_key(key_id)\n                    \n                    rotated_keys.append(new_key.key_id)\n                    logger.info(f\"Rotated API key for user {user_id}: {key_id} -> {new_key.key_id}\")\n            \n            logger.info(f\"API key rotation completed. Rotated {len(rotated_keys)} keys\")\n            return rotated_keys\n            \n        except Exception as e:\n            logger.error(f\"Failed to rotate API keys: {str(e)}\")\n            return []\n    \n    async def get_api_usage_stats(self) -> Dict:\n        \"\"\"Get API usage statistics\"\"\"\n        try:\n            stats = {\n                'total_requests': 0,\n                'requests_by_tier': {},\n                'requests_by_endpoint': {},\n                'error_rate': 0,\n                'average_response_time': 0,\n                'active_keys': 0\n            }\n            \n            # Get stats from Redis\n            keys = await self.redis_client.keys(\"stats:*\")\n            \n            for key in keys:\n                key_type = key.split(':')[1]\n                data = await self.redis_client.hgetall(key)\n                \n                if key_type == 'requests':\n                    stats['total_requests'] = int(data.get('total', 0))\n                elif key_type == 'tiers':\n                    stats['requests_by_tier'] = {k: int(v) for k, v in data.items()}\n                elif key_type == 'endpoints':\n                    stats['requests_by_endpoint'] = {k: int(v) for k, v in data.items()}\n                elif key_type == 'errors':\n                    total_errors = int(data.get('total', 0))\n                    if stats['total_requests'] > 0:\n                        stats['error_rate'] = total_errors / stats['total_requests']\n            \n            # Count active keys\n            active_keys = await self.redis_client.keys(\"apikey:*\")\n            stats['active_keys'] = len(active_keys)\n            \n            return stats\n            \n        except Exception as e:\n            logger.error(f\"Failed to get API usage stats: {str(e)}\")\n            return {}\n    \n    async def _wait_for_vault_ready(self, timeout: int = 600):\n        \"\"\"Wait for Vault cluster to be ready\"\"\"\n        logger.info(\"Waiting for Vault cluster to be ready...\")\n        \n        start_time = time.time()\n        while time.time() - start_time < timeout:\n            try:\n                # Check if Vault is accessible\n                async with aiohttp.ClientSession() as session:\n                    async with session.get(f\"{self.vault_url}/v1/sys/health\") as response:\n                        if response.status == 200:\n                            health_data = await response.json()\n                            if not health_data.get('sealed', True):\n                                logger.info(\"Vault cluster is ready\")\n                                return True\n                            \n            except Exception as e:\n                logger.debug(f\"Vault readiness check failed: {e}\")\n            \n            await asyncio.sleep(10)\n        \n        raise TimeoutError(f\"Vault cluster did not become ready within {timeout} seconds\")\n    \n    async def _initialize_vault_configuration(self):\n        \"\"\"Initialize Vault with GuardianShield-specific configuration\"\"\"\n        try:\n            logger.info(\"Initializing Vault configuration for GuardianShield\")\n            \n            # Initialize connections\n            await self.initialize_connections()\n            \n            # Enable required secrets engines\n            try:\n                self.vault_client.sys.enable_secrets_engine(\n                    backend_type='kv-v2',\n                    path='guardianshield'\n                )\n            except Exception:\n                pass  # Engine might already exist\n            \n            # Enable auth methods\n            try:\n                self.vault_client.sys.enable_auth_method(\n                    method_type='kubernetes',\n                    path='kubernetes'\n                )\n                self.vault_client.sys.enable_auth_method(\n                    method_type='jwt',\n                    path='jwt'\n                )\n            except Exception:\n                pass  # Auth methods might already exist\n            \n            # Create initial API keys and secrets\n            await self._create_initial_secrets()\n            \n            logger.info(\"Vault configuration initialization completed\")\n            \n        except Exception as e:\n            logger.error(f\"Failed to initialize Vault configuration: {str(e)}\")\n            raise\n    \n    async def _authenticate_vault(self):\n        \"\"\"Authenticate with Vault using Kubernetes service account\"\"\"\n        try:\n            # Read service account token\n            with open('/var/run/secrets/kubernetes.io/serviceaccount/token', 'r') as f:\n                jwt_token = f.read().strip()\n            \n            # Authenticate with Vault\n            self.vault_client.auth.kubernetes.login(\n                role='guardianshield-admin',\n                jwt=jwt_token\n            )\n            \n            logger.info(\"Successfully authenticated with Vault\")\n            \n        except Exception as e:\n            logger.error(f\"Failed to authenticate with Vault: {str(e)}\")\n            # Fallback to token-based auth for development\n            vault_token = os.getenv('VAULT_TOKEN')\n            if vault_token:\n                self.vault_client.token = vault_token\n            else:\n                raise\n    \n    async def _create_initial_secrets(self):\n        \"\"\"Create initial secrets in Vault\"\"\"\n        try:\n            # Generate initial API management secrets\n            initial_secrets = {\n                'guardianshield/api/keys': {\n                    'master_key': secrets.token_urlsafe(64),\n                    'jwt_secret': secrets.token_urlsafe(64),\n                    'encryption_key': secrets.token_urlsafe(32)\n                },\n                'guardianshield/database/credentials': {\n                    'username': 'guardianshield_admin',\n                    'password': secrets.token_urlsafe(32)\n                },\n                'guardianshield/redis/credentials': {\n                    'password': secrets.token_urlsafe(32)\n                },\n                'guardianshield/oauth2/client': {\n                    'client_id': secrets.token_urlsafe(16),\n                    'client_secret': secrets.token_urlsafe(32)\n                }\n            }\n            \n            for path, secret_data in initial_secrets.items():\n                self.vault_client.secrets.kv.v2.create_or_update_secret(\n                    path=path,\n                    secret=secret_data\n                )\n                logger.info(f\"Created initial secret: {path}\")\n            \n        except Exception as e:\n            logger.error(f\"Failed to create initial secrets: {str(e)}\")\n            raise\n    \n    async def _get_jwt_secret(self) -> str:\n        \"\"\"Get JWT secret from Vault\"\"\"\n        try:\n            secret = self.vault_client.secrets.kv.v2.read_secret_version(\n                path='guardianshield/api/keys'\n            )\n            return secret['data']['data']['jwt_secret']\n        except Exception as e:\n            logger.error(f\"Failed to get JWT secret: {str(e)}\")\n            raise\n    \n    async def _get_api_key_from_vault(self, api_key: str) -> Optional[Dict]:\n        \"\"\"Get API key data from Vault\"\"\"\n        try:\n            # Search through all keys (this is inefficient - consider indexing)\n            keys_list = self.vault_client.secrets.kv.v2.list_secrets(\n                path=\"guardianshield/api/keys\"\n            )\n            \n            for key_id in keys_list['data']['keys']:\n                vault_path = f\"guardianshield/api/keys/{key_id}\"\n                key_data = self.vault_client.secrets.kv.v2.read_secret_version(path=vault_path)\n                \n                if key_data['data']['data']['api_key'] == api_key:\n                    return key_data['data']['data']\n            \n            return None\n            \n        except Exception as e:\n            logger.error(f\"Failed to get API key from Vault: {str(e)}\")\n            return None\n    \n    async def _check_rate_limit(self, api_key: str, tier: str) -> bool:\n        \"\"\"Check if API key is within rate limits\"\"\"\n        try:\n            rate_limit_key = f\"rate_limit:{api_key}\"\n            current_time = int(time.time())\n            window_start = current_time - 3600  # 1 hour window\n            \n            # Get current request count\n            pipe = self.redis_client.pipeline()\n            pipe.zcount(rate_limit_key, window_start, current_time)\n            pipe.zadd(rate_limit_key, {current_time: current_time})\n            pipe.zremrangebyscore(rate_limit_key, 0, window_start)\n            pipe.expire(rate_limit_key, 3600)\n            \n            results = await pipe.execute()\n            current_requests = results[0]\n            \n            # Check against tier limits\n            tier_limit = self.rate_limits.get(tier, self.rate_limits['default'])\n            \n            return current_requests < tier_limit['requests']\n            \n        except Exception as e:\n            logger.error(f\"Failed to check rate limit: {str(e)}\")\n            return False\n    \n    async def _update_api_key_usage(self, api_key: str):\n        \"\"\"Update API key last used timestamp\"\"\"\n        try:\n            redis_key = f\"apikey:{api_key}\"\n            await self.redis_client.hset(\n                redis_key, \n                'last_used', \n                datetime.utcnow().isoformat()\n            )\n        except Exception as e:\n            logger.error(f\"Failed to update API key usage: {str(e)}\")\n    \n    def _get_default_permissions(self, tier: str) -> List[str]:\n        \"\"\"Get default permissions based on tier\"\"\"\n        permission_map = {\n            'default': ['api:read', 'threat-intel:read'],\n            'premium': ['api:read', 'api:write', 'threat-intel:read', 'analytics:read'],\n            'enterprise': [\n                'api:read', 'api:write', 'api:admin',\n                'threat-intel:read', 'threat-intel:write',\n                'analytics:read', 'analytics:write',\n                'blockchain:read'\n            ]\n        }\n        return permission_map.get(tier, permission_map['default'])\n    \n    async def _run_command(self, cmd: List[str]) -> Dict:\n        \"\"\"Run shell command asynchronously\"\"\"\n        try:\n            process = await asyncio.create_subprocess_exec(\n                *cmd,\n                stdout=asyncio.subprocess.PIPE,\n                stderr=asyncio.subprocess.PIPE\n            )\n            \n            stdout, stderr = await process.communicate()\n            \n            return {\n                'success': process.returncode == 0,\n                'output': stdout.decode(),\n                'error': stderr.decode(),\n                'returncode': process.returncode\n            }\n            \n        except Exception as e:\n            return {\n                'success': False,\n                'output': '',\n                'error': str(e),\n                'returncode': -1\n            }\n    \n    def _deep_update(self, base_dict: Dict, update_dict: Dict):\n        \"\"\"Deep update dictionary\"\"\"\n        for key, value in update_dict.items():\n            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):\n                self._deep_update(base_dict[key], value)\n            else:\n                base_dict[key] = value\n\nasync def main():\n    \"\"\"Main API management orchestrator\"\"\"\n    manager = VaultAPIManager()\n    \n    logger.info(\"Starting GuardianShield Vault CSI Provider API Management deployment\")\n    \n    # Deploy Vault cluster with CSI provider\n    vault_result = await manager.deploy_vault_cluster({\n        'vault': {\n            'server': {\n                'ha': {'replicas': 3},\n                'dataStorage': {'size': '50Gi'},\n                'resources': {\n                    'requests': {'cpu': '500m', 'memory': '1Gi'},\n                    'limits': {'cpu': '1', 'memory': '2Gi'}\n                }\n            }\n        },\n        'monitoring': {'enabled': True}\n    })\n    \n    if vault_result['success']:\n        logger.info(\"Vault cluster deployed successfully\")\n        logger.info(f\"Vault URL: {vault_result['vault_url']}\")\n    else:\n        logger.error(f\"Vault deployment failed: {vault_result['error']}\")\n        return\n    \n    # Initialize API management\n    await manager.initialize_connections()\n    \n    # Create sample API keys for different tiers\n    sample_keys = []\n    for tier in ['default', 'premium', 'enterprise']:\n        api_key = await manager.create_api_key(\n            user_id=f\"test_user_{tier}\",\n            tier=tier,\n            expires_days=90\n        )\n        sample_keys.append(api_key)\n        logger.info(f\"Created {tier} API key: {api_key.api_key[:20]}...\")\n    \n    # Generate JWT tokens for testing\n    for key in sample_keys[:2]:  # Only for default and premium\n        jwt_token = await manager.generate_jwt_token(\n            user_id=f\"test_user_{key.rate_limit_tier}\",\n            scopes=key.permissions\n        )\n        logger.info(f\"Generated JWT token for {key.rate_limit_tier} user\")\n    \n    # Get usage statistics\n    stats = await manager.get_api_usage_stats()\n    logger.info(f\"API Usage Stats: {json.dumps(stats, indent=2)}\")\n    \n    logger.info(\"GuardianShield Vault CSI Provider API Management deployment completed successfully!\")\n\nif __name__ == \"__main__\":\n    asyncio.run(main())