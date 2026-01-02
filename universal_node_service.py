#!/usr/bin/env python3
"""
GuardianShield Universal Node Service Framework
Unified service implementation for all node types using base image
"""

import asyncio
import json
import logging
import os
import signal
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import aiohttp
from aiohttp import web
import websockets
from node_interaction_protocol import initialize_node_protocol, NodeInteractionProtocol

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ServiceConfig:
    """Configuration for node services"""
    node_type: str
    node_id: str
    http_port: int = 8080
    websocket_port: int = 8081
    p2p_port: int = 26656
    rpc_port: int = 26657
    metrics_port: int = 9090
    region: str = "unknown"
    enable_api: bool = True
    enable_websocket: bool = True
    enable_p2p: bool = True
    enable_metrics: bool = True

class UniversalNodeService(ABC):
    """
    Abstract base class for all node services
    Provides common functionality while allowing specialization
    """
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.protocol: Optional[NodeInteractionProtocol] = None
        self.running = False
        self.http_server: Optional[aiohttp.web.Application] = None
        self.websocket_server = None
        self.metrics_server = None
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        
    async def initialize(self):
        """Initialize the node service"""
        logger.info(f"Initializing {self.config.node_type} service: {self.config.node_id}")
        
        # Initialize interaction protocol
        self.protocol = await initialize_node_protocol(
            self.config.node_type,
            self.config.node_id
        )
        
        # Node-specific initialization
        await self._node_specific_initialization()
        
        # Setup HTTP API server
        if self.config.enable_api:
            await self._setup_http_server()
        
        # Setup WebSocket server
        if self.config.enable_websocket:
            await self._setup_websocket_server()
            
        # Setup metrics server
        if self.config.enable_metrics:
            await self._setup_metrics_server()
        
        logger.info(f"{self.config.node_type} service initialized successfully")
        
    @abstractmethod
    async def _node_specific_initialization(self):
        """Node-specific initialization logic"""
        pass
    
    async def _setup_http_server(self):
        """Setup HTTP API server"""
        self.http_server = web.Application()
        
        # Common routes
        self.http_server.router.add_post('/guardian/message', self._handle_http_message)
        self.http_server.router.add_get('/health', self._handle_health_check)
        self.http_server.router.add_get('/status', self._handle_status)
        
        # Node-specific routes
        await self._setup_node_specific_routes()
        
        # CORS middleware
        self.http_server.middlewares.append(self._cors_middleware)
        
    async def _setup_websocket_server(self):
        """Setup WebSocket server"""
        async def websocket_handler(websocket, path):
            try:
                async for message in websocket:
                    data = json.loads(message)
                    response = await self.protocol.handle_incoming_message(data)
                    await websocket.send(json.dumps(response))
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
        
        self.websocket_server = websockets.serve(
            websocket_handler,
            '0.0.0.0',
            self.config.websocket_port
        )
        
    async def _setup_metrics_server(self):
        """Setup Prometheus metrics server"""
        from prometheus_client import start_http_server, Counter, Histogram, Gauge
        
        # Define common metrics
        self.request_counter = Counter(
            'guardian_node_requests_total',
            'Total requests processed',
            ['node_type', 'node_id', 'endpoint']
        )
        
        self.request_duration = Histogram(
            'guardian_node_request_duration_seconds',
            'Request duration',
            ['node_type', 'node_id', 'endpoint']
        )
        
        self.active_connections = Gauge(
            'guardian_node_active_connections',
            'Active connections',
            ['node_type', 'node_id']
        )
        
        # Start metrics server
        start_http_server(self.config.metrics_port)
        logger.info(f"Metrics server started on port {self.config.metrics_port}")
        
    @abstractmethod
    async def _setup_node_specific_routes(self):
        """Setup node-specific HTTP routes"""
        pass
    
    async def _cors_middleware(self, request, handler):
        """CORS middleware for HTTP requests"""
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    async def _handle_http_message(self, request):
        """Handle HTTP messages from other nodes"""
        try:
            data = await request.json()
            response = await self.protocol.handle_incoming_message(data)
            return web.json_response(response)
        except Exception as e:
            logger.error(f"HTTP message handling error: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def _handle_health_check(self, request):
        """Handle health check requests"""
        health_status = await self._get_health_status()
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return web.json_response(health_status, status=status_code)
    
    async def _handle_status(self, request):
        """Handle status requests"""
        status = await self._get_node_status()
        return web.json_response(status)
    
    @abstractmethod
    async def _get_health_status(self) -> Dict[str, Any]:
        """Get node health status"""
        pass
    
    @abstractmethod
    async def _get_node_status(self) -> Dict[str, Any]:
        """Get detailed node status"""
        pass
    
    async def run(self):
        """Run the node service"""
        self.running = True
        
        # Start all servers
        tasks = []
        
        if self.http_server:
            runner = web.AppRunner(self.http_server)
            await runner.setup()
            site = web.TCPSite(runner, '0.0.0.0', self.config.http_port)
            await site.start()
            logger.info(f"HTTP server started on port {self.config.http_port}")
        
        if self.websocket_server:
            tasks.append(asyncio.create_task(self.websocket_server))
            logger.info(f"WebSocket server started on port {self.config.websocket_port}")
        
        # Start node-specific services
        node_tasks = await self._start_node_specific_services()
        tasks.extend(node_tasks)
        
        # Start main service loop
        tasks.append(asyncio.create_task(self._service_loop()))
        
        # Wait for shutdown
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("Service interrupted")
        finally:
            await self._cleanup()
    
    @abstractmethod
    async def _start_node_specific_services(self) -> List[asyncio.Task]:
        """Start node-specific background services"""
        pass
    
    async def _service_loop(self):
        """Main service loop"""
        while self.running:
            try:
                # Node-specific service loop logic
                await self._node_specific_service_loop()
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Service loop error: {e}")
                await asyncio.sleep(5)
    
    @abstractmethod
    async def _node_specific_service_loop(self):
        """Node-specific service loop logic"""
        pass
    
    async def _cleanup(self):
        """Cleanup resources before shutdown"""
        logger.info("Cleaning up resources...")
        await self._node_specific_cleanup()

    @abstractmethod
    async def _node_specific_cleanup(self):
        """Node-specific cleanup logic"""
        pass

class ValidatorNodeService(UniversalNodeService):
    """Validator node service implementation"""
    
    def __init__(self, config: ServiceConfig):
        super().__init__(config)
        self.consensus_state = {
            'current_height': 0,
            'current_round': 0,
            'current_step': 'propose'
        }
        self.validator_key = None
        
    async def _node_specific_initialization(self):
        """Initialize validator-specific components"""
        # Load validator key
        key_path = os.environ.get('VALIDATOR_KEY_PATH', '/home/guardian/keys/validator_key.json')
        if os.path.exists(key_path):
            with open(key_path, 'r') as f:
                self.validator_key = json.load(f)
            logger.info("Validator key loaded")
        else:
            logger.warning(f"Validator key not found at {key_path}")
        
        # Initialize consensus components
        await self._initialize_consensus()
        
    async def _initialize_consensus(self):
        """Initialize consensus algorithm components"""
        logger.info("Initializing consensus components...")
        # Consensus initialization logic here
        
    async def _setup_node_specific_routes(self):
        """Setup validator-specific HTTP routes"""
        self.http_server.router.add_get('/validator/status', self._handle_validator_status)
        self.http_server.router.add_post('/validator/vote', self._handle_consensus_vote)
        self.http_server.router.add_get('/validator/height', self._handle_current_height)
        
    async def _handle_validator_status(self, request):
        """Handle validator status requests"""
        status = {
            'validator_id': self.config.node_id,
            'consensus_state': self.consensus_state,
            'has_validator_key': self.validator_key is not None,
            'uptime': 'calculation_needed'
        }
        return web.json_response(status)
        
    async def _handle_consensus_vote(self, request):
        """Handle consensus vote submissions"""
        try:
            vote_data = await request.json()
            # Process vote
            result = await self._process_consensus_vote(vote_data)
            return web.json_response(result)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=400)
    
    async def _handle_current_height(self, request):
        """Handle current blockchain height requests"""
        return web.json_response({
            'height': self.consensus_state['current_height'],
            'validator_id': self.config.node_id
        })
    
    async def _process_consensus_vote(self, vote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a consensus vote"""
        logger.info(f"Processing consensus vote: {vote_data}")
        # Vote processing logic here
        return {'status': 'vote_processed', 'vote_hash': vote_data.get('hash')}
    
    async def _get_health_status(self) -> Dict[str, Any]:
        """Get validator health status"""
        is_healthy = (
            self.validator_key is not None and
            self.running and
            self.consensus_state['current_height'] > 0
        )
        
        return {
            'status': 'healthy' if is_healthy else 'unhealthy',
            'node_type': self.config.node_type,
            'node_id': self.config.node_id,
            'has_validator_key': self.validator_key is not None,
            'consensus_height': self.consensus_state['current_height']
        }
    
    async def _get_node_status(self) -> Dict[str, Any]:
        """Get detailed validator status"""
        return {
            'node_type': self.config.node_type,
            'node_id': self.config.node_id,
            'region': self.config.region,
            'consensus_state': self.consensus_state,
            'validator_key_loaded': self.validator_key is not None,
            'services': {
                'http_api': self.config.enable_api,
                'websocket': self.config.enable_websocket,
                'metrics': self.config.enable_metrics
            },
            'ports': {
                'http': self.config.http_port,
                'websocket': self.config.websocket_port,
                'p2p': self.config.p2p_port,
                'rpc': self.config.rpc_port,
                'metrics': self.config.metrics_port
            }
        }
    
    async def _start_node_specific_services(self) -> List[asyncio.Task]:
        """Start validator-specific services"""
        tasks = []
        
        # Start consensus service
        tasks.append(asyncio.create_task(self._consensus_service()))
        
        # Start block production service
        tasks.append(asyncio.create_task(self._block_production_service()))
        
        return tasks
    
    async def _consensus_service(self):
        """Consensus algorithm service"""
        while self.running:
            try:
                # Consensus round logic
                await self._run_consensus_round()
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Consensus service error: {e}")
                await asyncio.sleep(5)
    
    async def _block_production_service(self):
        """Block production service"""
        while self.running:
            try:
                # Block production logic
                if self.consensus_state['current_step'] == 'propose':
                    await self._produce_block()
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Block production error: {e}")
                await asyncio.sleep(10)
    
    async def _run_consensus_round(self):
        """Run a single consensus round"""
        # Simplified consensus logic
        if self.consensus_state['current_step'] == 'propose':
            self.consensus_state['current_step'] = 'prevote'
        elif self.consensus_state['current_step'] == 'prevote':
            self.consensus_state['current_step'] = 'precommit'
        elif self.consensus_state['current_step'] == 'precommit':
            self.consensus_state['current_step'] = 'propose'
            self.consensus_state['current_height'] += 1
    
    async def _produce_block(self):
        """Produce a new block"""
        logger.info(f"Producing block at height {self.consensus_state['current_height']}")
        # Block production logic here
    
    async def _node_specific_service_loop(self):
        """Validator-specific service loop"""
        # Update consensus state, sync with peers, etc.
        pass
    
    async def _node_specific_cleanup(self):
        """Validator-specific cleanup"""
        logger.info("Cleaning up validator resources...")

class SentryNodeService(UniversalNodeService):
    """Sentry node service with attack protection"""
    
    def __init__(self, config: ServiceConfig):
        super().__init__(config)
        self.rate_limiters = {}
        self.attack_detector = None
        self.blocked_ips = set()
        
    async def _node_specific_initialization(self):
        """Initialize sentry-specific components"""
        # Initialize attack detection
        await self._initialize_attack_detection()
        
        # Setup rate limiting
        await self._initialize_rate_limiting()
        
    async def _initialize_attack_detection(self):
        """Initialize attack detection systems"""
        logger.info("Initializing attack detection systems...")
        # Attack detection initialization
        
    async def _initialize_rate_limiting(self):
        """Initialize rate limiting systems"""
        logger.info("Initializing rate limiting systems...")
        # Rate limiting initialization
        
    async def _setup_node_specific_routes(self):
        """Setup sentry-specific routes"""
        # API proxy routes
        self.http_server.router.add_get('/api/{path:.*}', self._handle_api_proxy)
        self.http_server.router.add_post('/api/{path:.*}', self._handle_api_proxy)
        
        # Sentry management routes
        self.http_server.router.add_get('/sentry/blocked', self._handle_blocked_ips)
        self.http_server.router.add_post('/sentry/block', self._handle_block_ip)
        self.http_server.router.add_post('/sentry/unblock', self._handle_unblock_ip)
        
    async def _handle_api_proxy(self, request):
        """Proxy API requests to backend nodes"""
        client_ip = request.remote
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            return web.json_response({'error': 'IP blocked'}, status=403)
        
        # Rate limiting check
        if not await self._check_rate_limit(client_ip, request.path):
            return web.json_response({'error': 'Rate limit exceeded'}, status=429)
        
        # Proxy to appropriate backend
        try:
            backend_response = await self._proxy_to_backend(request)
            return backend_response
        except Exception as e:
            logger.error(f"Proxy error: {e}")
            return web.json_response({'error': 'Backend unavailable'}, status=502)
    
    async def _proxy_to_backend(self, request):
        """Proxy request to backend nodes"""
        path = request.match_info.get('path', '')
        
        # Determine backend based on request type
        if 'balance' in path or 'transaction' in path.lower():
            # Route to observer for data queries
            response = await self.protocol.send_message(
                'observer',
                'api_request',
                {
                    'method': request.method,
                    'path': path,
                    'query': dict(request.query),
                    'data': await request.text() if request.can_read_body else None
                }
            )
        elif 'submit' in path.lower():
            # Route to validator for transaction submission
            response = await self.protocol.send_message(
                'validator',
                'api_request',
                {
                    'method': request.method,
                    'path': path,
                    'query': dict(request.query),
                    'data': await request.text() if request.can_read_body else None
                }
            )
        else:
            response = {'error': 'Unknown API endpoint'}
        
        return web.json_response(response)
    
    async def _check_rate_limit(self, client_ip: str, path: str) -> bool:
        """Check rate limits for client IP and path"""
        # Simplified rate limiting
        import time
        
        current_time = time.time()
        key = f"{client_ip}:{path}"
        
        if key not in self.rate_limiters:
            self.rate_limiters[key] = {'count': 0, 'window_start': current_time}
        
        limiter = self.rate_limiters[key]
        
        # Reset window if needed (1 minute)
        if current_time - limiter['window_start'] > 60:
            limiter['count'] = 0
            limiter['window_start'] = current_time
        
        # Check limit (100 requests per minute per IP/path)
        if limiter['count'] >= 100:
            return False
        
        limiter['count'] += 1
        return True
    
    async def _handle_blocked_ips(self, request):
        """Return list of blocked IPs"""
        return web.json_response({'blocked_ips': list(self.blocked_ips)})
    
    async def _handle_block_ip(self, request):
        """Block an IP address"""
        data = await request.json()
        ip = data.get('ip')
        if ip:
            self.blocked_ips.add(ip)
            logger.info(f"Blocked IP: {ip}")
            return web.json_response({'status': 'blocked', 'ip': ip})
        return web.json_response({'error': 'No IP provided'}, status=400)
    
    async def _handle_unblock_ip(self, request):
        """Unblock an IP address"""
        data = await request.json()
        ip = data.get('ip')
        if ip and ip in self.blocked_ips:
            self.blocked_ips.remove(ip)
            logger.info(f"Unblocked IP: {ip}")
            return web.json_response({'status': 'unblocked', 'ip': ip})
        return web.json_response({'error': 'IP not found'}, status=400)
    
    async def _get_health_status(self) -> Dict[str, Any]:
        """Get sentry health status"""
        return {
            'status': 'healthy' if self.running else 'unhealthy',
            'node_type': self.config.node_type,
            'node_id': self.config.node_id,
            'blocked_ips_count': len(self.blocked_ips),
            'active_rate_limiters': len(self.rate_limiters)
        }
    
    async def _get_node_status(self) -> Dict[str, Any]:
        """Get detailed sentry status"""
        return {
            'node_type': self.config.node_type,
            'node_id': self.config.node_id,
            'region': self.config.region,
            'blocked_ips': len(self.blocked_ips),
            'rate_limiters': len(self.rate_limiters),
            'attack_protection': True,
            'proxy_status': 'active'
        }
    
    async def _start_node_specific_services(self) -> List[asyncio.Task]:
        """Start sentry-specific services"""
        tasks = []
        tasks.append(asyncio.create_task(self._attack_detection_service()))
        tasks.append(asyncio.create_task(self._cleanup_service()))
        return tasks
    
    async def _attack_detection_service(self):
        """Attack detection service"""
        while self.running:
            try:
                # Analyze traffic patterns for attacks
                await self._analyze_traffic_patterns()
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Attack detection error: {e}")
                await asyncio.sleep(30)
    
    async def _cleanup_service(self):
        """Cleanup expired rate limiters and blocks"""
        while self.running:
            try:
                await self._cleanup_expired_limiters()
                await asyncio.sleep(300)  # Every 5 minutes
            except Exception as e:
                logger.error(f"Cleanup service error: {e}")
                await asyncio.sleep(600)
    
    async def _analyze_traffic_patterns(self):
        """Analyze traffic for attack patterns"""
        # Attack pattern analysis logic
        pass
    
    async def _cleanup_expired_limiters(self):
        """Remove expired rate limiters"""
        import time
        current_time = time.time()
        expired_keys = []
        
        for key, limiter in self.rate_limiters.items():
            if current_time - limiter['window_start'] > 300:  # 5 minutes
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.rate_limiters[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired rate limiters")
    
    async def _node_specific_service_loop(self):
        """Sentry-specific service loop"""
        # Monitor backend health, update routing, etc.
        pass
    
    async def _node_specific_cleanup(self):
        """Sentry-specific cleanup"""
        logger.info("Cleaning up sentry resources...")

# Service factory
def create_node_service(node_type: str, config: ServiceConfig) -> UniversalNodeService:
    """Create appropriate node service based on type"""
    
    node_type = node_type.lower()
    
    if node_type == 'validator':
        return ValidatorNodeService(config)
    elif node_type == 'sentry':
        return SentryNodeService(config)
    elif node_type == 'observer':
        # ObserverNodeService would be implemented similarly
        return UniversalNodeService(config)  # Placeholder
    elif node_type == 'bootnode':
        # BootnodeService would be implemented similarly
        return UniversalNodeService(config)  # Placeholder
    else:
        raise ValueError(f"Unknown node type: {node_type}")

# Main entry point
async def main():
    """Main entry point for universal node service"""
    
    # Get configuration from environment
    node_type = os.environ.get('NODE_TYPE', 'validator').lower()
    node_id = os.environ.get('NODE_ID', f"{node_type}-{os.urandom(4).hex()}")
    
    config = ServiceConfig(
        node_type=node_type,
        node_id=node_id,
        http_port=int(os.environ.get('HTTP_PORT', '8080')),
        websocket_port=int(os.environ.get('WEBSOCKET_PORT', '8081')),
        p2p_port=int(os.environ.get('P2P_PORT', '26656')),
        rpc_port=int(os.environ.get('RPC_PORT', '26657')),
        metrics_port=int(os.environ.get('METRICS_PORT', '9090')),
        region=os.environ.get('NODE_REGION', 'unknown')
    )
    
    # Create and run service
    service = create_node_service(node_type, config)
    
    try:
        await service.initialize()
        await service.run()
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    except Exception as e:
        logger.error(f"Service error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())