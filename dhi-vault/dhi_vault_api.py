# DHI-Vault API Server
# Web API interface for the Distributed HashiCorp Intelligence Vault

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import asdict

from aiohttp import web, ClientSession
from aiohttp_cors import setup as cors_setup, ResourceOptions
import aiofiles
from marshmallow import Schema, fields, ValidationError

from dhi_vault_core import DHIVaultAPIManager, ClientTier, APIKeyStatus

logger = logging.getLogger(__name__)

# Request/Response Schemas
class CreateAPIKeySchema(Schema):
    client_id = fields.Str(required=True)
    tier = fields.Str(missing='basic', validate=lambda x: x in ['basic', 'premium', 'enterprise', 'developer'])
    scopes = fields.List(fields.Str(), missing=['read'])
    expires_in = fields.Int(missing=None, allow_none=True)
    metadata = fields.Dict(missing={})

class CreateOAuth2ClientSchema(Schema):
    client_name = fields.Str(required=True)
    redirect_uris = fields.List(fields.Str(), required=True)
    scopes = fields.List(fields.Str(), required=True)
    tier = fields.Str(missing='basic', validate=lambda x: x in ['basic', 'premium', 'enterprise', 'developer'])

class GenerateJWTSchema(Schema):
    client_id = fields.Str(required=True)
    scopes = fields.List(fields.Str(), required=True)
    audience = fields.Str(missing='dhi-vault-api')
    expires_in = fields.Int(missing=3600)

class DHIVaultAPIServer:
    """
    Web API server for DHI-Vault
    Provides REST API and WebSocket endpoints for API management
    """
    
    def __init__(self, vault_manager: DHIVaultAPIManager, config: Dict[str, Any]):
        self.vault_manager = vault_manager
        self.config = config
        self.app = web.Application(middlewares=[
            self._error_middleware,
            self._auth_middleware,
            self._rate_limit_middleware,
            self._metrics_middleware
        ])
        
        self._setup_routes()
        self._setup_cors()
        
    def _setup_routes(self):
        """Setup API routes"""
        
        # Health and metrics
        self.app.router.add_get('/health', self._health_check)
        self.app.router.add_get('/metrics', self._metrics)
        
        # API Key management
        self.app.router.add_post('/api/v1/keys', self._create_api_key)
        self.app.router.add_get('/api/v1/keys/{key_id}', self._get_api_key)
        self.app.router.add_delete('/api/v1/keys/{key_id}', self._revoke_api_key)
        self.app.router.add_post('/api/v1/keys/{key_id}/refresh', self._refresh_api_key)
        
        # OAuth2 endpoints
        self.app.router.add_post('/api/v1/oauth2/clients', self._create_oauth2_client)
        self.app.router.add_get('/api/v1/oauth2/clients/{client_id}', self._get_oauth2_client)
        self.app.router.add_post('/api/v1/oauth2/token', self._oauth2_token)
        self.app.router.add_post('/api/v1/oauth2/introspect', self._oauth2_introspect)
        self.app.router.add_post('/api/v1/oauth2/revoke', self._oauth2_revoke)
        
        # JWT endpoints  
        self.app.router.add_post('/api/v1/jwt/generate', self._generate_jwt)
        self.app.router.add_post('/api/v1/jwt/verify', self._verify_jwt)
        self.app.router.add_get('/.well-known/jwks.json', self._jwks)
        
        # Usage and analytics
        self.app.router.add_get('/api/v1/usage/{client_id}', self._get_usage_stats)
        self.app.router.add_get('/api/v1/analytics/overview', self._get_analytics_overview)
        
        # Admin endpoints
        self.app.router.add_get('/api/v1/admin/clients', self._list_clients)
        self.app.router.add_get('/api/v1/admin/keys', self._list_api_keys)
        self.app.router.add_post('/api/v1/admin/keys/{key_id}/suspend', self._suspend_api_key)
        self.app.router.add_post('/api/v1/admin/keys/{key_id}/activate', self._activate_api_key)
        
        # WebSocket endpoint for real-time updates
        self.app.router.add_get('/ws/events', self._websocket_handler)
        
        # Documentation
        self.app.router.add_get('/api/docs', self._api_documentation)
        self.app.router.add_static('/docs', 'static/docs')
    
    def _setup_cors(self):
        """Setup CORS configuration"""
        cors_config = self.config.get('cors', {})
        
        cors = cors_setup(self.app, defaults={
            "*": ResourceOptions(
                allow_credentials=cors_config.get('allow_credentials', True),
                expose_headers="*",
                allow_headers="*",
                allow_methods=cors_config.get('allowed_methods', ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
            )
        })
        
        # Add CORS to all routes
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    @web.middleware
    async def _error_middleware(self, request, handler):
        """Global error handling middleware"""
        try:
            return await handler(request)
        except ValidationError as e:
            return web.json_response({
                'error': 'validation_error',
                'message': 'Request validation failed',
                'details': e.messages
            }, status=400)
        except web.HTTPException as e:
            raise
        except Exception as e:
            logger.error(f"Unhandled error in {request.path}: {e}", exc_info=True)
            return web.json_response({
                'error': 'internal_error',
                'message': 'Internal server error'
            }, status=500)
    
    @web.middleware
    async def _auth_middleware(self, request, handler):
        """Authentication middleware"""
        
        # Skip auth for health, metrics, and docs
        if request.path in ['/health', '/metrics', '/api/docs', '/.well-known/jwks.json']:
            return await handler(request)
        
        # Extract authorization header
        auth_header = request.headers.get('Authorization', '')
        api_key_header = request.headers.get('X-API-Key', '')
        
        authenticated = False
        client_info = None
        
        # Check API key authentication
        if api_key_header:
            api_key_obj = await self.vault_manager.validate_api_key(api_key_header)
            if api_key_obj:
                authenticated = True
                client_info = {
                    'client_id': api_key_obj.client_id,
                    'tier': api_key_obj.tier,
                    'scopes': api_key_obj.scopes,
                    'auth_method': 'api_key'
                }
        
        # Check Bearer token authentication
        elif auth_header.startswith('Bearer '):
            token = auth_header[7:]
            payload = await self.vault_manager.verify_jwt_token(token)
            if payload:
                authenticated = True
                client_info = {
                    'client_id': payload['sub'],
                    'scopes': payload.get('scope', '').split(),
                    'auth_method': 'jwt'
                }
        
        if not authenticated:
            return web.json_response({
                'error': 'authentication_required',
                'message': 'Valid API key or JWT token required'
            }, status=401)
        
        # Add client info to request
        request['client_info'] = client_info
        return await handler(request)
    
    @web.middleware
    async def _rate_limit_middleware(self, request, handler):
        """Rate limiting middleware"""
        
        # Skip rate limiting for certain endpoints
        if request.path in ['/health', '/metrics']:
            return await handler(request)
        
        client_info = request.get('client_info')
        if not client_info:
            return await handler(request)
        
        # Check rate limits
        client_id = client_info['client_id']
        tier = client_info.get('tier', ClientTier.BASIC)
        
        if not await self.vault_manager.check_rate_limit(client_id, tier):
            return web.json_response({
                'error': 'rate_limit_exceeded',
                'message': 'API rate limit exceeded'
            }, status=429)
        
        return await handler(request)
    
    @web.middleware
    async def _metrics_middleware(self, request, handler):
        """Metrics collection middleware"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            response = await handler(request)
            status = response.status
        except web.HTTPException as e:
            status = e.status
            raise
        finally:
            duration = asyncio.get_event_loop().time() - start_time
            
            self.vault_manager.api_requests_total.labels(
                method=request.method,
                endpoint=request.path,
                status=status
            ).inc()
            
            self.vault_manager.api_request_duration.observe(duration)
        
        return response
    
    # API Endpoints
    
    async def _health_check(self, request):
        """Health check endpoint"""
        health_status = await self.vault_manager.health_check()
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return web.json_response(health_status, status=status_code)
    
    async def _metrics(self, request):
        """Prometheus metrics endpoint"""
        metrics = await self.vault_manager.get_metrics()
        return web.Response(text=metrics, content_type='text/plain')
    
    async def _create_api_key(self, request):
        """Create new API key"""
        schema = CreateAPIKeySchema()
        
        try:
            json_data = await request.json()
            data = schema.load(json_data)
        except Exception as e:
            raise ValidationError({'json': ['Invalid JSON data']})
        
        api_key, key_obj = await self.vault_manager.create_api_key(
            client_id=data['client_id'],
            tier=ClientTier(data['tier']),
            scopes=data['scopes'],
            expires_in=data['expires_in'],
            metadata=data['metadata']
        )
        
        return web.json_response({
            'api_key': api_key,
            'key_id': key_obj.key_id,
            'client_id': key_obj.client_id,
            'status': key_obj.status.value,
            'tier': key_obj.tier.value,
            'created_at': key_obj.created_at.isoformat(),
            'expires_at': key_obj.expires_at.isoformat() if key_obj.expires_at else None,
            'scopes': key_obj.scopes,
            'rate_limit': key_obj.rate_limit
        }, status=201)
    
    async def _get_api_key(self, request):
        """Get API key information"""
        key_id = request.match_info['key_id']
        
        # Load key from Vault (admin operation)
        api_key_obj = await self.vault_manager._load_api_key_by_id(key_id)
        if not api_key_obj:
            return web.json_response({
                'error': 'not_found',
                'message': 'API key not found'
            }, status=404)
        
        return web.json_response({
            'key_id': api_key_obj.key_id,
            'client_id': api_key_obj.client_id,
            'status': api_key_obj.status.value,
            'tier': api_key_obj.tier.value,
            'created_at': api_key_obj.created_at.isoformat(),
            'expires_at': api_key_obj.expires_at.isoformat() if api_key_obj.expires_at else None,
            'last_used': api_key_obj.last_used.isoformat() if api_key_obj.last_used else None,
            'usage_count': api_key_obj.usage_count,
            'scopes': api_key_obj.scopes,
            'rate_limit': api_key_obj.rate_limit,
            'metadata': api_key_obj.metadata
        })
    
    async def _revoke_api_key(self, request):
        """Revoke API key"""
        key_id = request.match_info['key_id']
        
        success = await self.vault_manager.revoke_api_key(key_id)
        if not success:
            return web.json_response({
                'error': 'not_found',
                'message': 'API key not found'
            }, status=404)
        
        return web.json_response({
            'message': 'API key revoked successfully',
            'key_id': key_id
        })
    
    async def _create_oauth2_client(self, request):
        """Create OAuth2 client"""
        schema = CreateOAuth2ClientSchema()
        
        try:
            json_data = await request.json()
            data = schema.load(json_data)
        except Exception as e:
            raise ValidationError({'json': ['Invalid JSON data']})
        
        credentials = await self.vault_manager.create_oauth2_client(
            client_name=data['client_name'],
            redirect_uris=data['redirect_uris'],
            scopes=data['scopes'],
            tier=ClientTier(data['tier'])
        )
        
        return web.json_response({
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'client_name': credentials.client_name,
            'redirect_uris': credentials.redirect_uris,
            'scopes': credentials.scopes,
            'tier': credentials.tier.value,
            'created_at': credentials.created_at.isoformat()
        }, status=201)
    
    async def _generate_jwt(self, request):
        """Generate JWT token"""
        schema = GenerateJWTSchema()
        
        try:
            json_data = await request.json()
            data = schema.load(json_data)
        except Exception as e:
            raise ValidationError({'json': ['Invalid JSON data']})
        
        token = await self.vault_manager.generate_jwt_token(
            client_id=data['client_id'],
            scopes=data['scopes'],
            audience=data['audience'],
            expires_in=data['expires_in']
        )
        
        return web.json_response({
            'access_token': token,
            'token_type': 'Bearer',
            'expires_in': data['expires_in'],
            'scope': ' '.join(data['scopes'])
        })
    
    async def _verify_jwt(self, request):
        """Verify JWT token"""
        try:
            json_data = await request.json()
            token = json_data.get('token')
            
            if not token:
                raise ValidationError({'token': ['Token is required']})
                
        except Exception as e:
            raise ValidationError({'json': ['Invalid JSON data']})
        
        payload = await self.vault_manager.verify_jwt_token(token)
        if not payload:
            return web.json_response({
                'valid': False,
                'error': 'invalid_token'
            }, status=400)
        
        return web.json_response({
            'valid': True,
            'payload': payload
        })
    
    async def _jwks(self, request):
        """JSON Web Key Set endpoint"""
        # Get public key in JWK format
        public_key_pem = self.vault_manager.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Convert to JWK format (simplified)
        jwk = {
            'kty': 'RSA',
            'kid': 'dhi-vault-key-1',
            'use': 'sig',
            'alg': 'RS256',
            'n': '',  # Would need proper conversion from PEM
            'e': 'AQAB'
        }
        
        return web.json_response({
            'keys': [jwk]
        })
    
    async def _get_usage_stats(self, request):
        """Get API usage statistics"""
        client_id = request.match_info['client_id']
        
        # Verify client access (can only view own stats unless admin)
        request_client_id = request['client_info']['client_id']
        if client_id != request_client_id:
            # Check admin permissions
            return web.json_response({
                'error': 'forbidden',
                'message': 'Access denied'
            }, status=403)
        
        stats = await self.vault_manager.get_api_usage_stats(client_id)
        return web.json_response(stats)
    
    async def _websocket_handler(self, request):
        """WebSocket endpoint for real-time events"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        try:
            # Send initial connection message
            await ws.send_str(json.dumps({
                'type': 'connection',
                'message': 'Connected to DHI-Vault events',
                'timestamp': datetime.utcnow().isoformat()
            }))
            
            # Keep connection alive and handle messages
            async for msg in ws:
                if msg.type == web.MsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        # Handle client requests
                        if data.get('type') == 'subscribe':
                            await ws.send_str(json.dumps({
                                'type': 'subscribed',
                                'events': data.get('events', [])
                            }))
                    except json.JSONDecodeError:
                        await ws.send_str(json.dumps({
                            'type': 'error',
                            'message': 'Invalid JSON'
                        }))
                elif msg.type == web.MsgType.ERROR:
                    logger.error(f'WebSocket error: {ws.exception()}')
                    break
                    
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        
        return ws
    
    async def _api_documentation(self, request):
        """API documentation endpoint"""
        docs = {
            'title': 'DHI-Vault API Documentation',
            'version': '1.0.0',
            'description': 'Distributed HashiCorp Intelligence Vault API',
            'base_url': f"http://{request.host}",
            'endpoints': {
                'health': {
                    'method': 'GET',
                    'path': '/health',
                    'description': 'Health check endpoint',
                    'auth_required': False
                },
                'create_api_key': {
                    'method': 'POST',
                    'path': '/api/v1/keys',
                    'description': 'Create new API key',
                    'auth_required': True,
                    'body': {
                        'client_id': 'string (required)',
                        'tier': 'string (basic|premium|enterprise|developer)',
                        'scopes': 'array of strings',
                        'expires_in': 'integer (seconds)',
                        'metadata': 'object'
                    }
                },
                'oauth2_token': {
                    'method': 'POST',
                    'path': '/api/v1/oauth2/token',
                    'description': 'OAuth2 token endpoint',
                    'auth_required': False,
                    'body': {
                        'grant_type': 'string (client_credentials)',
                        'client_id': 'string (required)',
                        'client_secret': 'string (required)',
                        'scope': 'string'
                    }
                }
            }
        }
        
        return web.json_response(docs)

async def create_app(config: Dict[str, Any]) -> web.Application:
    """Create and initialize the web application"""
    
    # Initialize vault manager
    vault_manager = DHIVaultAPIManager(config)
    await vault_manager.initialize()
    
    # Create API server
    api_server = DHIVaultAPIServer(vault_manager, config)
    
    return api_server.app

async def main():
    """Main server entry point"""
    config = {
        'vault': {
            'url': 'https://vault.guardianshield.svc.cluster.local:8200',
            'verify_tls': True
        },
        'redis': {
            'url': 'redis://redis.guardianshield.svc.cluster.local:6379'
        },
        'cors': {
            'allowed_methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
            'allow_credentials': True
        },
        'server': {
            'host': '0.0.0.0',
            'port': 8080
        }
    }
    
    app = await create_app(config)
    
    # Start server
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(
        runner,
        host=config['server']['host'],
        port=config['server']['port']
    )
    
    await site.start()
    
    logger.info(f"DHI-Vault API server started on {config['server']['host']}:{config['server']['port']}")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        await runner.cleanup()

if __name__ == '__main__':
    asyncio.run(main())