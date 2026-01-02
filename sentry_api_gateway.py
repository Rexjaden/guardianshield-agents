"""
GuardianShield Sentry API Gateway
Handles all public API/RPC/WebSocket traffic and protects validators
"""
import asyncio
import json
import time
import logging
import aiohttp
import websockets
import redis
from aiohttp import web, ClientTimeout
from collections import defaultdict, deque
from datetime import datetime, timedelta
import psutil

class SentryAPIGateway:
    def __init__(self, config_path="/sentry/config/sentry-gateway.json"):
        self.config = self.load_config(config_path)
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.validator_connections = {}
        self.request_stats = defaultdict(int)
        self.attack_logs = deque(maxlen=10000)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Load balancer for validator connections
        self.validator_pool = self.config.get('validator_endpoints', [
            'validator-us-east:26657',
            'validator-eu-west:26657', 
            'validator-asia-pacific:26657'
        ])
        self.current_validator_index = 0
        
    def load_config(self, config_path):
        """Load sentry gateway configuration"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "sentry_id": "guardian_sentry_001",
                "bind_address": "0.0.0.0",
                "api_port": 80,
                "rpc_port": 26657,
                "websocket_port": 8080,
                "https_port": 443,
                "validator_endpoints": [
                    "validator-us-east:26657",
                    "validator-eu-west:26657",
                    "validator-asia-pacific:26657"
                ],
                "rate_limits": {
                    "requests_per_minute": 1000,
                    "requests_per_ip_per_minute": 60,
                    "concurrent_connections_per_ip": 10,
                    "websocket_connections_per_ip": 5
                },
                "ddos_protection": {
                    "max_request_size": 1048576,  # 1MB
                    "timeout_seconds": 30,
                    "ban_threshold": 100,
                    "ban_duration_minutes": 60
                },
                "attack_mitigation": {
                    "enabled": True,
                    "slow_loris_protection": True,
                    "request_flood_protection": True,
                    "malformed_request_protection": True
                }
            }
    
    async def rate_limit_check(self, client_ip, endpoint):
        """Check if request is within rate limits"""
        current_minute = int(time.time() // 60)
        
        # Per-IP rate limiting
        ip_key = f"rate_limit:ip:{client_ip}:{current_minute}"
        ip_requests = await self.redis_get_int(ip_key)
        
        if ip_requests >= self.config['rate_limits']['requests_per_ip_per_minute']:
            self.log_attack("RATE_LIMIT", client_ip, f"IP rate limit exceeded: {ip_requests}/min")
            return False
        
        # Global rate limiting
        global_key = f"rate_limit:global:{current_minute}"
        global_requests = await self.redis_get_int(global_key)
        
        if global_requests >= self.config['rate_limits']['requests_per_minute']:
            self.log_attack("RATE_LIMIT", client_ip, f"Global rate limit exceeded: {global_requests}/min")
            return False
        
        # Increment counters
        await self.redis_increment(ip_key, 60)  # Expire in 60 seconds
        await self.redis_increment(global_key, 60)
        
        return True
    
    async def redis_get_int(self, key):
        """Get integer value from Redis"""
        try:
            value = self.redis_client.get(key)
            return int(value) if value else 0
        except:
            return 0
    
    async def redis_increment(self, key, expiry=None):
        """Increment Redis counter"""
        try:
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            if expiry:
                pipe.expire(key, expiry)
            pipe.execute()
        except Exception as e:
            self.logger.error(f"Redis error: {e}")
    
    def get_next_validator(self):
        """Get next validator using round-robin"""
        validator = self.validator_pool[self.current_validator_index]
        self.current_validator_index = (self.current_validator_index + 1) % len(self.validator_pool)
        return validator
    
    async def proxy_to_validator(self, method, path, data=None, client_ip="unknown"):
        """Proxy request to validator with protection"""
        validator_endpoint = self.get_next_validator()
        
        try:
            timeout = ClientTimeout(total=self.config['ddos_protection']['timeout_seconds'])
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = f"http://{validator_endpoint}{path}"
                
                async with session.request(
                    method=method,
                    url=url,
                    json=data if data else None,
                    headers={'X-Forwarded-For': client_ip}
                ) as response:
                    result = await response.text()
                    return web.Response(
                        text=result,
                        status=response.status,
                        headers={'Content-Type': 'application/json'}
                    )
                    
        except asyncio.TimeoutError:
            self.log_attack("TIMEOUT", client_ip, f"Request timeout to {validator_endpoint}")
            return web.Response(status=408, text='{"error": "Request timeout"}')
        
        except Exception as e:
            self.logger.error(f"Validator proxy error: {e}")
            return web.Response(status=503, text='{"error": "Service unavailable"}')
    
    def log_attack(self, attack_type, client_ip, details):
        """Log attack attempts"""
        attack_log = {
            'timestamp': datetime.now().isoformat(),
            'type': attack_type,
            'client_ip': client_ip,
            'details': details
        }
        
        self.attack_logs.append(attack_log)
        self.logger.warning(f"ATTACK DETECTED [{attack_type}] from {client_ip}: {details}")
        
        # Store in Redis for fail2ban integration
        self.redis_client.lpush('attack_log', json.dumps(attack_log))
        self.redis_client.expire('attack_log', 3600)  # Keep for 1 hour
    
    async def handle_http_request(self, request):
        """Handle HTTP API requests with protection"""
        client_ip = self.get_client_ip(request)
        
        # Rate limiting
        if not await self.rate_limit_check(client_ip, request.path):
            return web.Response(status=429, text='{"error": "Rate limit exceeded"}')
        
        # Request size protection
        if request.content_length and request.content_length > self.config['ddos_protection']['max_request_size']:
            self.log_attack("LARGE_REQUEST", client_ip, f"Request size: {request.content_length}")
            return web.Response(status=413, text='{"error": "Request too large"}')
        
        # Malformed request protection
        try:
            if request.method == 'POST':
                data = await request.json()
            else:
                data = None
        except Exception as e:
            self.log_attack("MALFORMED_REQUEST", client_ip, f"JSON parsing error: {e}")
            return web.Response(status=400, text='{"error": "Invalid JSON"}')
        
        # Proxy to validator
        return await self.proxy_to_validator(request.method, request.path, data, client_ip)
    
    def get_client_ip(self, request):
        """Extract client IP with proxy support"""
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.remote or 'unknown'
    
    async def handle_websocket_connection(self, websocket, path):
        """Handle WebSocket connections with protection"""
        client_ip = websocket.remote_address[0] if websocket.remote_address else 'unknown'
        
        # Check WebSocket connection limits
        ws_key = f"websocket_connections:{client_ip}"
        current_connections = await self.redis_get_int(ws_key)
        
        if current_connections >= self.config['rate_limits']['websocket_connections_per_ip']:
            self.log_attack("WS_LIMIT", client_ip, f"WebSocket limit exceeded: {current_connections}")
            await websocket.close(code=1008, reason="Connection limit exceeded")
            return
        
        # Track connection
        await self.redis_increment(ws_key, 300)  # 5 minute expiry
        
        try:
            self.logger.info(f"WebSocket connection from {client_ip}")
            
            async for message in websocket:
                # Rate limit WebSocket messages
                if not await self.rate_limit_check(client_ip, "websocket"):
                    await websocket.send(json.dumps({"error": "Rate limit exceeded"}))
                    continue
                
                # Forward to validator
                try:
                    data = json.loads(message)
                    # Process WebSocket message through validator
                    # (Implementation depends on your specific WebSocket protocol)
                    response = await self.proxy_websocket_to_validator(data, client_ip)
                    await websocket.send(json.dumps(response))
                    
                except Exception as e:
                    self.log_attack("WS_MALFORMED", client_ip, f"WebSocket error: {e}")
                    await websocket.send(json.dumps({"error": "Invalid message format"}))
        
        finally:
            # Decrement connection count
            self.redis_client.decr(ws_key)
            self.logger.info(f"WebSocket disconnected: {client_ip}")
    
    async def proxy_websocket_to_validator(self, data, client_ip):
        """Proxy WebSocket data to validator"""
        # This would implement your specific WebSocket protocol
        # For now, return a basic response
        return {
            "type": "response",
            "data": "Message processed",
            "timestamp": time.time()
        }
    
    async def start_http_server(self):
        """Start HTTP/HTTPS API server"""
        app = web.Application()
        
        # Add all routes to the same handler for comprehensive protection
        app.router.add_route('*', '/{path:.*}', self.handle_http_request)
        
        # Start HTTP server
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(
            runner, 
            self.config['bind_address'], 
            self.config['api_port']
        )
        await site.start()
        
        self.logger.info(f"HTTP API server started on port {self.config['api_port']}")
    
    async def start_websocket_server(self):
        """Start WebSocket server"""
        server = await websockets.serve(
            self.handle_websocket_connection,
            self.config['bind_address'],
            self.config['websocket_port']
        )
        
        self.logger.info(f"WebSocket server started on port {self.config['websocket_port']}")
        return server
    
    async def monitor_attacks(self):
        """Monitor and log attack patterns"""
        while True:
            try:
                # System metrics
                cpu_percent = psutil.cpu_percent()
                memory_percent = psutil.virtual_memory().percent
                
                # Network connections
                connections = len(psutil.net_connections(kind='inet'))
                
                # Attack summary
                recent_attacks = len([
                    attack for attack in self.attack_logs 
                    if datetime.fromisoformat(attack['timestamp']) > datetime.now() - timedelta(minutes=5)
                ])
                
                self.logger.info(
                    f"Sentry Status - CPU: {cpu_percent}%, "
                    f"Memory: {memory_percent}%, "
                    f"Connections: {connections}, "
                    f"Recent attacks: {recent_attacks}"
                )
                
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Monitor error: {e}")
                await asyncio.sleep(60)
    
    async def start_gateway(self):
        """Start the complete sentry gateway"""
        self.logger.info("Starting GuardianShield Sentry API Gateway")
        self.logger.info(f"Protecting validators: {', '.join(self.validator_pool)}")
        
        # Start all services
        tasks = [
            asyncio.create_task(self.start_http_server()),
            asyncio.create_task(self.start_websocket_server()),
            asyncio.create_task(self.monitor_attacks())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            self.logger.info("Sentry gateway shutting down...")

async def main():
    """Main sentry gateway function"""
    gateway = SentryAPIGateway()
    await gateway.start_gateway()

if __name__ == "__main__":
    asyncio.run(main())