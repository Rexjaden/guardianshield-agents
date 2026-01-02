"""
GuardianShield Sentry Rate Limiter
Advanced multi-tier rate limiting and traffic shaping
"""
import asyncio
import time
import json
import redis
import hashlib
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta
import ipaddress

class SentryRateLimiter:
    def __init__(self, config_path="/sentry/config/rate-limiter.json"):
        self.config = self.load_config(config_path)
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # Multi-tier rate limiting buckets
        self.global_bucket = TokenBucket(self.config['global_limits']['requests_per_second'])
        self.ip_buckets = {}
        self.endpoint_buckets = {}
        
        # Traffic patterns
        self.traffic_patterns = defaultdict(deque)
        self.burst_detection = defaultdict(list)
        
        # VIP and premium users
        self.vip_ips = set(self.config.get('vip_ips', []))
        self.premium_ips = set(self.config.get('premium_ips', []))
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def load_config(self, config_path):
        """Load rate limiter configuration"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "global_limits": {
                    "requests_per_second": 10000,
                    "burst_allowance": 2000
                },
                "ip_limits": {
                    "default_requests_per_second": 100,
                    "burst_allowance": 50,
                    "premium_multiplier": 5,
                    "vip_multiplier": 10
                },
                "endpoint_limits": {
                    "/api/v1/blocks": {"rps": 50, "burst": 20},
                    "/api/v1/transactions": {"rps": 200, "burst": 100},
                    "/api/v1/balance": {"rps": 500, "burst": 200},
                    "/ws/subscribe": {"rps": 10, "burst": 5}
                },
                "adaptive_limits": {
                    "enabled": True,
                    "load_threshold": 0.8,
                    "reduction_factor": 0.5,
                    "recovery_time_seconds": 300
                },
                "burst_detection": {
                    "enabled": True,
                    "threshold_multiplier": 5,
                    "window_seconds": 60,
                    "penalty_duration_seconds": 300
                },
                "geolocation_limits": {
                    "enabled": True,
                    "country_limits": {
                        "US": 1000,
                        "EU": 800,
                        "default": 100
                    }
                },
                "vip_ips": [],
                "premium_ips": []
            }
    
    def get_ip_tier(self, ip):
        """Get IP tier (VIP, Premium, or Regular)"""
        if ip in self.vip_ips:
            return "VIP"
        elif ip in self.premium_ips:
            return "Premium"
        else:
            return "Regular"
    
    def get_rate_limit_for_ip(self, ip):
        """Get rate limit configuration for IP"""
        tier = self.get_ip_tier(ip)
        base_rps = self.config['ip_limits']['default_requests_per_second']
        base_burst = self.config['ip_limits']['burst_allowance']
        
        if tier == "VIP":
            multiplier = self.config['ip_limits']['vip_multiplier']
        elif tier == "Premium":
            multiplier = self.config['ip_limits']['premium_multiplier']
        else:
            multiplier = 1
        
        return {
            'requests_per_second': base_rps * multiplier,
            'burst_allowance': base_burst * multiplier,
            'tier': tier
        }
    
    async def check_rate_limit(self, ip, endpoint, method="GET"):
        """Comprehensive rate limit check"""
        current_time = time.time()
        
        # 1. Global rate limit check
        if not self.global_bucket.consume():
            await self.log_rate_limit_hit(ip, "GLOBAL", endpoint)
            return False, "Global rate limit exceeded"
        
        # 2. IP-based rate limit
        if not await self.check_ip_rate_limit(ip):
            await self.log_rate_limit_hit(ip, "IP", endpoint)
            return False, "IP rate limit exceeded"
        
        # 3. Endpoint-specific rate limit
        if not await self.check_endpoint_rate_limit(ip, endpoint):
            await self.log_rate_limit_hit(ip, "ENDPOINT", endpoint)
            return False, "Endpoint rate limit exceeded"
        
        # 4. Burst detection
        if await self.detect_burst_traffic(ip, endpoint):
            await self.log_rate_limit_hit(ip, "BURST", endpoint)
            return False, "Burst traffic detected"
        
        # 5. Adaptive limiting based on system load
        if await self.check_adaptive_limits(ip):
            await self.log_rate_limit_hit(ip, "ADAPTIVE", endpoint)
            return False, "System under high load"
        
        # Record successful request
        await self.record_request(ip, endpoint, method)
        return True, "OK"
    
    async def check_ip_rate_limit(self, ip):
        """Check IP-specific rate limits"""
        if ip not in self.ip_buckets:
            ip_config = self.get_rate_limit_for_ip(ip)
            self.ip_buckets[ip] = TokenBucket(
                ip_config['requests_per_second'],
                ip_config['burst_allowance']
            )
        
        return self.ip_buckets[ip].consume()
    
    async def check_endpoint_rate_limit(self, ip, endpoint):
        """Check endpoint-specific rate limits"""
        # Find matching endpoint pattern
        endpoint_config = None
        for pattern, config in self.config['endpoint_limits'].items():
            if endpoint.startswith(pattern):
                endpoint_config = config
                break
        
        if not endpoint_config:
            return True  # No specific limit for this endpoint
        
        # Create bucket key
        bucket_key = f"{ip}:{endpoint}"
        
        if bucket_key not in self.endpoint_buckets:
            self.endpoint_buckets[bucket_key] = TokenBucket(
                endpoint_config['rps'],
                endpoint_config.get('burst', endpoint_config['rps'])
            )
        
        return self.endpoint_buckets[bucket_key].consume()
    
    async def detect_burst_traffic(self, ip, endpoint):
        """Detect burst traffic patterns"""
        if not self.config['burst_detection']['enabled']:
            return False
        
        current_time = time.time()
        window = self.config['burst_detection']['window_seconds']
        threshold_multiplier = self.config['burst_detection']['threshold_multiplier']
        
        # Clean old entries
        cutoff_time = current_time - window
        self.burst_detection[ip] = [
            timestamp for timestamp in self.burst_detection[ip]
            if timestamp > cutoff_time
        ]
        
        # Add current request
        self.burst_detection[ip].append(current_time)
        
        # Check if burst threshold exceeded
        ip_config = self.get_rate_limit_for_ip(ip)
        normal_limit = ip_config['requests_per_second'] * window
        burst_threshold = normal_limit * threshold_multiplier
        
        if len(self.burst_detection[ip]) > burst_threshold:
            # Apply penalty
            await self.apply_burst_penalty(ip)
            return True
        
        return False
    
    async def apply_burst_penalty(self, ip):
        """Apply penalty for burst traffic"""
        penalty_duration = self.config['burst_detection']['penalty_duration_seconds']
        penalty_key = f"burst_penalty:{ip}"
        
        self.redis_client.setex(penalty_key, penalty_duration, "penalized")
        self.logger.warning(f"Applied burst penalty to {ip} for {penalty_duration} seconds")
    
    async def check_adaptive_limits(self, ip):
        """Check adaptive limits based on system load"""
        if not self.config['adaptive_limits']['enabled']:
            return False
        
        # Get current system metrics
        try:
            import psutil
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            
            # Calculate load factor
            load_factor = max(cpu_percent / 100, memory_percent / 100)
            load_threshold = self.config['adaptive_limits']['load_threshold']
            
            if load_factor > load_threshold:
                # Reduce limits for non-VIP users
                if self.get_ip_tier(ip) == "Regular":
                    reduction_factor = self.config['adaptive_limits']['reduction_factor']
                    
                    # Reduce IP bucket capacity
                    if ip in self.ip_buckets:
                        self.ip_buckets[ip].capacity *= reduction_factor
                    
                    return True  # Limit this request
            
            return False
            
        except ImportError:
            return False
    
    async def record_request(self, ip, endpoint, method):
        """Record successful request for analytics"""
        current_time = time.time()
        
        # Update traffic patterns
        request_info = {
            'timestamp': current_time,
            'endpoint': endpoint,
            'method': method,
            'ip_tier': self.get_ip_tier(ip)
        }
        
        self.traffic_patterns[ip].append(request_info)
        
        # Keep only recent traffic (last hour)
        cutoff_time = current_time - 3600
        while (self.traffic_patterns[ip] and 
               self.traffic_patterns[ip][0]['timestamp'] < cutoff_time):
            self.traffic_patterns[ip].popleft()
        
        # Update Redis statistics
        stats_key = f"traffic_stats:{ip}:{int(current_time // 60)}"
        self.redis_client.incr(stats_key)
        self.redis_client.expire(stats_key, 3600)
    
    async def log_rate_limit_hit(self, ip, limit_type, endpoint):
        """Log rate limit violations"""
        log_entry = {
            'timestamp': time.time(),
            'ip': ip,
            'limit_type': limit_type,
            'endpoint': endpoint,
            'ip_tier': self.get_ip_tier(ip)
        }
        
        self.logger.warning(f"Rate limit hit: {limit_type} for {ip} on {endpoint}")
        
        # Store in Redis for monitoring
        self.redis_client.lpush('rate_limit_violations', json.dumps(log_entry))
        self.redis_client.expire('rate_limit_violations', 86400)  # 24 hours
    
    def get_ip_statistics(self, ip):
        """Get detailed statistics for an IP"""
        current_time = time.time()
        
        # Get recent traffic
        recent_requests = list(self.traffic_patterns.get(ip, []))
        
        # Calculate request rates
        last_minute = [r for r in recent_requests if r['timestamp'] > current_time - 60]
        last_hour = [r for r in recent_requests if r['timestamp'] > current_time - 3600]
        
        # Get endpoint breakdown
        endpoint_counts = defaultdict(int)
        for request in last_hour:
            endpoint_counts[request['endpoint']] += 1
        
        return {
            'ip': ip,
            'tier': self.get_ip_tier(ip),
            'requests_last_minute': len(last_minute),
            'requests_last_hour': len(last_hour),
            'endpoint_breakdown': dict(endpoint_counts),
            'burst_detections': len(self.burst_detection.get(ip, [])),
            'bucket_tokens': getattr(self.ip_buckets.get(ip), 'tokens', 0)
        }
    
    async def cleanup_old_data(self):
        """Clean up old rate limiting data"""
        while True:
            try:
                current_time = time.time()
                cutoff_time = current_time - 3600  # 1 hour
                
                # Clean up IP buckets for inactive IPs
                inactive_ips = []
                for ip in self.ip_buckets:
                    if ip not in self.traffic_patterns or not self.traffic_patterns[ip]:
                        inactive_ips.append(ip)
                
                for ip in inactive_ips:
                    del self.ip_buckets[ip]
                
                # Clean up endpoint buckets
                inactive_endpoints = []
                for endpoint_key in self.endpoint_buckets:
                    # Check if bucket has been unused
                    bucket = self.endpoint_buckets[endpoint_key]
                    if bucket.last_refill < cutoff_time:
                        inactive_endpoints.append(endpoint_key)
                
                for endpoint_key in inactive_endpoints:
                    del self.endpoint_buckets[endpoint_key]
                
                if inactive_ips or inactive_endpoints:
                    self.logger.info(
                        f"Cleaned up {len(inactive_ips)} IP buckets and "
                        f"{len(inactive_endpoints)} endpoint buckets"
                    )
                
                await asyncio.sleep(300)  # Clean every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Cleanup error: {e}")
                await asyncio.sleep(600)
    
    async def start_rate_limiter(self):
        """Start the rate limiting system"""
        self.logger.info("Starting GuardianShield Sentry Rate Limiter")
        self.logger.info(f"Global limit: {self.config['global_limits']['requests_per_second']} RPS")
        self.logger.info(f"Default IP limit: {self.config['ip_limits']['default_requests_per_second']} RPS")
        
        # Start cleanup task
        cleanup_task = asyncio.create_task(self.cleanup_old_data())
        
        try:
            await cleanup_task
        except KeyboardInterrupt:
            self.logger.info("Rate limiter shutting down...")

class TokenBucket:
    """Token bucket implementation for rate limiting"""
    
    def __init__(self, capacity, refill_rate=None):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate or capacity  # Tokens per second
        self.last_refill = time.time()
    
    def consume(self, tokens=1):
        """Consume tokens from bucket"""
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    
    def _refill(self):
        """Refill bucket with tokens based on time elapsed"""
        current_time = time.time()
        elapsed = current_time - self.last_refill
        
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = current_time

async def main():
    """Main rate limiter function"""
    limiter = SentryRateLimiter()
    
    print("GuardianShield Sentry Rate Limiter")
    print(f"Global Limit: {limiter.config['global_limits']['requests_per_second']} RPS")
    print(f"Burst Detection: {'ENABLED' if limiter.config['burst_detection']['enabled'] else 'DISABLED'}")
    print(f"Adaptive Limits: {'ENABLED' if limiter.config['adaptive_limits']['enabled'] else 'DISABLED'}")
    print("-" * 50)
    
    await limiter.start_rate_limiter()

if __name__ == "__main__":
    asyncio.run(main())