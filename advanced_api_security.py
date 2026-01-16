"""
Advanced API Endpoint Security for GuardianShield
Enhanced protection against common attacks and vulnerabilities
"""

import time
import hashlib
import secrets
import json
import re
from typing import Dict, Set, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer
import asyncio
import ipaddress

class AdvancedSecurityManager:
    """
    Advanced security manager with multiple protection layers
    """
    
    def __init__(self):
        # DDoS Protection
        self.ip_request_counts = defaultdict(deque)  # IP -> deque of request times
        self.blocked_ips = {}  # IP -> block_until_time
        self.suspicious_ips = set()  # IPs showing suspicious behavior
        
        # API Key Management
        self.api_keys = {}  # key -> {user, permissions, rate_limit, created_at}
        self.api_key_usage = defaultdict(deque)  # key -> deque of request times
        
        # Request Pattern Analysis
        self.request_patterns = defaultdict(list)  # IP -> list of (endpoint, time)
        self.failed_attempts = defaultdict(deque)  # IP -> deque of failed auth times
        
        # Security Rules
        self.rate_limits = {
            'default': {'requests': 100, 'window': 60},  # 100 req/min
            'auth': {'requests': 5, 'window': 60},       # 5 auth attempts/min
            'admin': {'requests': 20, 'window': 60},     # 20 admin actions/min
            'api_key': {'requests': 1000, 'window': 60}  # 1000 req/min for API keys
        }
        
        # Geoblocking (optional)
        self.blocked_countries = set()  # Country codes to block
        self.allowed_ip_ranges = []     # Allowed IP ranges for admin access
        
        # Attack Detection
        self.sql_injection_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC)\b)",
            r"(\b(UNION|ORDER BY|GROUP BY)\b)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(--|\/\*|\*\/|;)",
            r"(\b(SCRIPT|JAVASCRIPT|VBSCRIPT)\b)"
        ]
        
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>"
        ]
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is currently blocked"""
        if ip in self.blocked_ips:
            if time.time() < self.blocked_ips[ip]:
                return True
            else:
                # Unblock expired IPs
                del self.blocked_ips[ip]
        return False
    
    def block_ip(self, ip: str, duration_minutes: int = 15):
        """Block IP for specified duration"""
        self.blocked_ips[ip] = time.time() + (duration_minutes * 60)
        print(f"🚨 SECURITY: Blocked IP {ip} for {duration_minutes} minutes")
    
    def check_rate_limit(self, ip: str, endpoint_type: str = 'default') -> bool:
        """Check if request exceeds rate limit"""
        now = time.time()
        limits = self.rate_limits[endpoint_type]
        window = limits['window']
        max_requests = limits['requests']
        
        # Clean old requests outside time window
        ip_requests = self.ip_request_counts[ip]
        while ip_requests and now - ip_requests[0] > window:
            ip_requests.popleft()
        
        # Check if under limit
        if len(ip_requests) >= max_requests:
            # Add to suspicious IPs after multiple violations
            self.suspicious_ips.add(ip)
            if len(ip_requests) >= max_requests * 2:  # Double violation = block
                self.block_ip(ip, 30)  # Block for 30 minutes
            return False
        
        # Add current request
        ip_requests.append(now)
        return True
    
    def detect_attack_patterns(self, request_data: str) -> Dict[str, bool]:
        """Detect common attack patterns in request data"""
        results = {
            'sql_injection': False,
            'xss': False,
            'suspicious': False
        }
        
        # SQL Injection Detection
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, request_data, re.IGNORECASE):
                results['sql_injection'] = True
                break
        
        # XSS Detection
        for pattern in self.xss_patterns:
            if re.search(pattern, request_data, re.IGNORECASE):
                results['xss'] = True
                break
        
        # General suspicious patterns
        suspicious_indicators = [
            len(request_data) > 50000,  # Unusually large payload
            request_data.count('../') > 5,  # Directory traversal
            request_data.count('%') > 20,   # Excessive URL encoding
        ]
        
        if any(suspicious_indicators):
            results['suspicious'] = True
        
        return results
    
    def log_failed_auth(self, ip: str):
        """Log failed authentication attempt"""
        now = time.time()
        self.failed_attempts[ip].append(now)
        
        # Clean old attempts (last 15 minutes)
        while (self.failed_attempts[ip] and 
               now - self.failed_attempts[ip][0] > 900):
            self.failed_attempts[ip].popleft()
        
        # Block IP after 5 failed attempts in 15 minutes
        if len(self.failed_attempts[ip]) >= 5:
            self.block_ip(ip, 60)  # Block for 1 hour
    
    def is_admin_ip_allowed(self, ip: str) -> bool:
        """Check if IP is allowed for admin access"""
        if not self.allowed_ip_ranges:
            return True  # No restrictions if not configured
        
        try:
            ip_obj = ipaddress.ip_address(ip)
            for ip_range in self.allowed_ip_ranges:
                if ip_obj in ipaddress.ip_network(ip_range):
                    return True
            return False
        except:
            return False  # Block invalid IPs
    
    def create_api_key(self, user: str, permissions: List[str], 
                       rate_limit: int = 1000) -> str:
        """Create new API key for user"""
        api_key = f"gs_{secrets.token_urlsafe(32)}"
        self.api_keys[api_key] = {
            'user': user,
            'permissions': permissions,
            'rate_limit': rate_limit,
            'created_at': datetime.now().isoformat(),
            'active': True
        }
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[Dict]:
        """Validate API key and return user info"""
        if api_key in self.api_keys and self.api_keys[api_key]['active']:
            # Check API key rate limit
            now = time.time()
            key_requests = self.api_key_usage[api_key]
            
            # Clean old requests (last minute)
            while key_requests and now - key_requests[0] > 60:
                key_requests.popleft()
            
            rate_limit = self.api_keys[api_key]['rate_limit']
            if len(key_requests) >= rate_limit:
                return None  # Rate limit exceeded
            
            key_requests.append(now)
            return self.api_keys[api_key]
        
        return None

class EnhancedRateLimitMiddleware:
    """
    Enhanced rate limiting with DDoS protection and attack detection
    """
    
    def __init__(self, security_manager: AdvancedSecurityManager):
        self.security_manager = security_manager
    
    async def __call__(self, request: Request, call_next):
        client_ip = request.client.host
        
        # Check if IP is blocked
        if self.security_manager.is_ip_blocked(client_ip):
            return self._create_error_response(
                423, "IP temporarily blocked due to suspicious activity"
            )
        
        # Determine endpoint type for rate limiting
        path = request.url.path
        if path.startswith('/api/auth/'):
            endpoint_type = 'auth'
        elif path.startswith('/admin/'):
            endpoint_type = 'admin'
        elif request.headers.get('X-API-Key'):
            endpoint_type = 'api_key'
        else:
            endpoint_type = 'default'
        
        # Check rate limit
        if not self.security_manager.check_rate_limit(client_ip, endpoint_type):
            return self._create_error_response(
                429, "Rate limit exceeded", 
                {"retry_after": 60, "endpoint_type": endpoint_type}
            )
        
        # For admin endpoints, check IP allowlist
        if endpoint_type == 'admin':
            if not self.security_manager.is_admin_ip_allowed(client_ip):
                return self._create_error_response(
                    403, "Admin access not allowed from this IP"
                )
        
        # Analyze request data for attacks
        try:
            body = await request.body()
            if body:
                body_str = body.decode('utf-8')
                attack_detection = self.security_manager.detect_attack_patterns(body_str)
                
                if attack_detection['sql_injection'] or attack_detection['xss']:
                    # Block IP immediately for attack attempts
                    self.security_manager.block_ip(client_ip, 120)  # 2 hours
                    return self._create_error_response(
                        403, "Request blocked by security filter"
                    )
                
                if attack_detection['suspicious']:
                    # Log suspicious activity but allow request
                    print(f"⚠️ SECURITY: Suspicious request from {client_ip}")
                    self.security_manager.suspicious_ips.add(client_ip)
        except:
            pass  # Continue if body parsing fails
        
        response = await call_next(request)
        return response
    
    def _create_error_response(self, status_code: int, message: str, 
                             extra_data: Dict = None):
        """Create standardized error response"""
        from fastapi.responses import JSONResponse
        
        content = {
            "detail": message,
            "timestamp": datetime.now().isoformat(),
            "error_code": f"SECURITY_{status_code}"
        }
        
        if extra_data:
            content.update(extra_data)
        
        return JSONResponse(status_code=status_code, content=content)

class APIKeyAuth:
    """
    API Key authentication for programmatic access
    """
    
    def __init__(self, security_manager: AdvancedSecurityManager):
        self.security_manager = security_manager
        self.bearer = HTTPBearer(auto_error=False)
    
    async def __call__(self, request: Request):
        # Check for API key in header
        api_key = request.headers.get('X-API-Key')
        if api_key:
            user_info = self.security_manager.validate_api_key(api_key)
            if user_info:
                return {
                    'username': user_info['user'],
                    'auth_method': 'api_key',
                    'permissions': user_info['permissions']
                }
        
        # Fallback to JWT token
        credentials = await self.bearer(request)
        if credentials:
            from security_manager import security_manager
            return security_manager.verify_token(credentials.credentials)
        
        raise HTTPException(status_code=401, detail="Valid authentication required")

# Security monitoring functions
def log_security_event(event_type: str, ip: str, details: Dict = None):
    """Log security events for monitoring"""
    event = {
        'timestamp': datetime.now().isoformat(),
        'type': event_type,
        'ip': ip,
        'details': details or {}
    }
    
    # Log to security log file
    with open('security_events.jsonl', 'a') as f:
        f.write(json.dumps(event) + '\n')

def get_security_metrics() -> Dict:
    """Get current security metrics"""
    # This would integrate with your monitoring system
    return {
        'active_blocks': len(advanced_security.blocked_ips),
        'suspicious_ips': len(advanced_security.suspicious_ips),
        'api_keys_active': sum(1 for k in advanced_security.api_keys.values() if k['active']),
        'recent_attacks': 0  # Would count recent attack attempts
    }

# Initialize advanced security manager
advanced_security = AdvancedSecurityManager()
api_key_auth = APIKeyAuth(advanced_security)