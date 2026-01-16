"""
GuardianShield IP Protection System
Protects against malicious IPs while keeping website accessible
"""

import json
import requests
import ipaddress
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional
import logging
from dataclasses import dataclass
import asyncio
import aiohttp

@dataclass
class IPThreatData:
    ip: str
    threat_level: str  # "low", "medium", "high", "critical"
    sources: List[str]
    last_seen: datetime
    attack_types: List[str]
    reputation_score: int  # 0-100, lower is worse

class IPProtectionManager:
    def __init__(self):
        self.config_file = "ip_protection_config.json"
        self.threat_cache_file = "ip_threat_cache.json"
        self.access_log_file = "ip_access_log.jsonl"
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize threat intelligence
        self.threat_cache = self._load_threat_cache()
        self.blocked_ips = set()
        self.rate_limited_ips = {}
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _load_config(self) -> Dict:
        """Load IP protection configuration"""
        default_config = {
            "protection_enabled": True,
            "server_ip": "172.58.254.32",  # Your server IP
            "website_accessible": True,
            
            # Geographic restrictions
            "geo_blocking": {
                "enabled": False,
                "blocked_countries": [],  # ISO country codes to block
                "allowed_countries": []   # If set, only these are allowed
            },
            
            # Rate limiting by IP
            "rate_limiting": {
                "enabled": True,
                "requests_per_minute": 60,
                "requests_per_hour": 1000,
                "burst_threshold": 10,  # Requests in 10 seconds
                "temporary_ban_minutes": 15
            },
            
            # Admin access restrictions
            "admin_access": {
                "ip_whitelist_enabled": True,
                "allowed_admin_ips": [
                    "172.58.254.32",  # Your server IP
                    "127.0.0.1",      # Localhost
                    # Add your home/office IPs here
                ],
                "allowed_ip_ranges": [
                    "192.168.0.0/16",    # Private networks
                    "10.0.0.0/8",
                    "172.16.0.0/12"
                ]
            },
            
            # Threat intelligence
            "threat_intelligence": {
                "enabled": True,
                "auto_block_high_threat": True,
                "reputation_threshold": 30,  # Block IPs with score below this
                "check_sources": [
                    "abuseipdb",
                    "virustotal", 
                    "malwaredomainlist",
                    "reputation_apis"
                ]
            },
            
            # Privacy protection
            "privacy_protection": {
                "anonymize_logs": True,
                "hash_client_ips": True,
                "retention_days": 30,
                "exclude_private_ips": True
            },
            
            # DDoS protection
            "ddos_protection": {
                "enabled": True,
                "connection_threshold": 100,  # Max connections per IP
                "request_pattern_detection": True,
                "auto_mitigation": True
            }
        }
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                # Merge with defaults
                return {**default_config, **config}
        except FileNotFoundError:
            # Save default config
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
    
    def _load_threat_cache(self) -> Dict[str, IPThreatData]:
        """Load cached threat intelligence"""
        try:
            with open(self.threat_cache_file, 'r') as f:
                data = json.load(f)
                
            cache = {}
            for ip, threat_data in data.items():
                cache[ip] = IPThreatData(
                    ip=threat_data['ip'],
                    threat_level=threat_data['threat_level'],
                    sources=threat_data['sources'],
                    last_seen=datetime.fromisoformat(threat_data['last_seen']),
                    attack_types=threat_data['attack_types'],
                    reputation_score=threat_data['reputation_score']
                )
            
            return cache
        except FileNotFoundError:
            return {}
    
    def _save_threat_cache(self):
        """Save threat intelligence cache"""
        data = {}
        for ip, threat_data in self.threat_cache.items():
            data[ip] = {
                'ip': threat_data.ip,
                'threat_level': threat_data.threat_level,
                'sources': threat_data.sources,
                'last_seen': threat_data.last_seen.isoformat(),
                'attack_types': threat_data.attack_types,
                'reputation_score': threat_data.reputation_score
            }
        
        with open(self.threat_cache_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def anonymize_ip(self, ip_address: str) -> str:
        """Anonymize IP address for logging"""
        if not self.config['privacy_protection']['anonymize_logs']:
            return ip_address
        
        if self.config['privacy_protection']['hash_client_ips']:
            # Hash IP with salt
            salt = "guardian_ip_protection_salt_2026"
            return hashlib.sha256(f"{ip_address}{salt}".encode()).hexdigest()[:16]
        else:
            # Mask last octet for IPv4
            try:
                ip = ipaddress.ip_address(ip_address)
                if ip.version == 4:
                    parts = str(ip).split('.')
                    return f"{parts[0]}.{parts[1]}.{parts[2]}.xxx"
                else:  # IPv6
                    return str(ip)[:20] + "::xxxx"
            except:
                return "unknown"
    
    def is_private_ip(self, ip_address: str) -> bool:
        """Check if IP is private/internal"""
        try:
            ip = ipaddress.ip_address(ip_address)
            return ip.is_private
        except:
            return False
    
    def check_admin_access(self, client_ip: str) -> Dict:
        """Check if IP is allowed for admin access"""
        if not self.config['admin_access']['ip_whitelist_enabled']:
            return {"allowed": True, "reason": "IP whitelist disabled"}
        
        # Check exact matches
        if client_ip in self.config['admin_access']['allowed_admin_ips']:
            return {"allowed": True, "reason": "IP in whitelist"}
        
        # Check IP ranges
        try:
            client_ip_obj = ipaddress.ip_address(client_ip)
            for ip_range in self.config['admin_access']['allowed_ip_ranges']:
                if client_ip_obj in ipaddress.ip_network(ip_range, strict=False):
                    return {"allowed": True, "reason": f"IP in range {ip_range}"}
        except:
            pass
        
        # Log denied access attempt
        self._log_access_attempt(client_ip, "admin_access_denied", {
            "reason": "IP not in whitelist",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {"allowed": False, "reason": "IP not in admin whitelist"}
    
    def check_rate_limit(self, client_ip: str) -> Dict:
        """Check if IP is rate limited"""
        if not self.config['rate_limiting']['enabled']:
            return {"allowed": True, "reason": "Rate limiting disabled"}
        
        now = datetime.utcnow()
        ip_key = self.anonymize_ip(client_ip)
        
        if ip_key not in self.rate_limited_ips:
            self.rate_limited_ips[ip_key] = {
                'requests': [],
                'blocked_until': None
            }
        
        ip_data = self.rate_limited_ips[ip_key]
        
        # Check if temporarily banned
        if ip_data['blocked_until'] and now < ip_data['blocked_until']:
            return {
                "allowed": False, 
                "reason": "Temporarily rate limited",
                "blocked_until": ip_data['blocked_until'].isoformat()
            }
        
        # Clean old requests
        cutoff_time = now - timedelta(minutes=1)
        ip_data['requests'] = [req_time for req_time in ip_data['requests'] 
                             if req_time > cutoff_time]
        
        # Add current request
        ip_data['requests'].append(now)
        
        # Check rate limits
        requests_per_minute = len(ip_data['requests'])
        
        if requests_per_minute > self.config['rate_limiting']['requests_per_minute']:
            # Rate limit exceeded - temporary ban
            ban_duration = timedelta(minutes=self.config['rate_limiting']['temporary_ban_minutes'])
            ip_data['blocked_until'] = now + ban_duration
            
            self._log_access_attempt(client_ip, "rate_limit_exceeded", {
                "requests_per_minute": requests_per_minute,
                "blocked_until": ip_data['blocked_until'].isoformat()
            })
            
            return {
                "allowed": False,
                "reason": "Rate limit exceeded",
                "requests_per_minute": requests_per_minute,
                "blocked_until": ip_data['blocked_until'].isoformat()
            }
        
        return {"allowed": True, "requests_per_minute": requests_per_minute}
    
    async def check_ip_reputation(self, client_ip: str) -> Dict:
        """Check IP reputation against threat intelligence"""
        if not self.config['threat_intelligence']['enabled']:
            return {"threat_level": "unknown", "score": 50}
        
        # Check cache first
        if client_ip in self.threat_cache:
            threat_data = self.threat_cache[client_ip]
            # Check if cache is still valid (24 hours)
            if datetime.utcnow() - threat_data.last_seen < timedelta(hours=24):
                return {
                    "threat_level": threat_data.threat_level,
                    "score": threat_data.reputation_score,
                    "sources": threat_data.sources,
                    "attack_types": threat_data.attack_types
                }
        
        # Skip private IPs
        if self.is_private_ip(client_ip):
            return {"threat_level": "low", "score": 100}
        
        # Query threat intelligence APIs (implement actual API calls)
        reputation_data = await self._query_threat_apis(client_ip)
        
        # Cache result
        self.threat_cache[client_ip] = IPThreatData(
            ip=client_ip,
            threat_level=reputation_data['threat_level'],
            sources=reputation_data['sources'],
            last_seen=datetime.utcnow(),
            attack_types=reputation_data.get('attack_types', []),
            reputation_score=reputation_data['score']
        )
        
        self._save_threat_cache()
        return reputation_data
    
    async def _query_threat_apis(self, ip_address: str) -> Dict:
        """Query threat intelligence APIs"""
        # Placeholder for actual API implementations
        # You would implement real API calls here
        
        # Simulate threat check
        reputation_score = 75  # Default good reputation
        threat_level = "low"
        sources = ["local_analysis"]
        attack_types = []
        
        # Simple heuristics for demonstration
        if any(bad_subnet in ip_address for bad_subnet in ['1.2.3', '127.0.0.1']):
            threat_level = "low"
        
        return {
            "threat_level": threat_level,
            "score": reputation_score,
            "sources": sources,
            "attack_types": attack_types
        }
    
    def validate_ip_access(self, client_ip: str, access_type: str = "general") -> Dict:
        """Main IP validation function"""
        result = {
            "ip": client_ip,
            "anonymized_ip": self.anonymize_ip(client_ip),
            "access_type": access_type,
            "allowed": True,
            "checks": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Skip checks for server IP
        if client_ip == self.config.get('server_ip'):
            result["checks"]["server_ip"] = {"allowed": True, "reason": "Server IP"}
            return result
        
        # Rate limiting check
        rate_check = self.check_rate_limit(client_ip)
        result["checks"]["rate_limit"] = rate_check
        if not rate_check["allowed"]:
            result["allowed"] = False
            result["primary_reason"] = rate_check["reason"]
        
        # Admin access check (if admin endpoint)
        if access_type == "admin":
            admin_check = self.check_admin_access(client_ip)
            result["checks"]["admin_access"] = admin_check
            if not admin_check["allowed"]:
                result["allowed"] = False
                result["primary_reason"] = admin_check["reason"]
        
        # Log access attempt
        self._log_access_attempt(client_ip, "access_validation", result)
        
        return result
    
    def _log_access_attempt(self, client_ip: str, event_type: str, details: Dict):
        """Log IP access attempt"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "client_ip": self.anonymize_ip(client_ip) if self.config['privacy_protection']['anonymize_logs'] else client_ip,
            "event_type": event_type,
            "details": details
        }
        
        with open(self.access_log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def add_admin_ip(self, ip_address: str) -> Dict:
        """Add IP to admin whitelist"""
        if ip_address not in self.config['admin_access']['allowed_admin_ips']:
            self.config['admin_access']['allowed_admin_ips'].append(ip_address)
            
            # Save config
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            self._log_access_attempt(ip_address, "admin_ip_added", {
                "added_by": "system_admin"
            })
            
            return {"success": True, "message": f"Added {ip_address} to admin whitelist"}
        else:
            return {"success": False, "message": "IP already in whitelist"}
    
    def remove_admin_ip(self, ip_address: str) -> Dict:
        """Remove IP from admin whitelist"""
        if ip_address in self.config['admin_access']['allowed_admin_ips']:
            self.config['admin_access']['allowed_admin_ips'].remove(ip_address)
            
            # Save config
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            self._log_access_attempt(ip_address, "admin_ip_removed", {
                "removed_by": "system_admin"
            })
            
            return {"success": True, "message": f"Removed {ip_address} from admin whitelist"}
        else:
            return {"success": False, "message": "IP not in whitelist"}
    
    def get_protection_status(self) -> Dict:
        """Get current IP protection status"""
        total_threats = len(self.threat_cache)
        high_threats = len([t for t in self.threat_cache.values() 
                          if t.threat_level in ['high', 'critical']])
        
        active_rate_limits = len([ip_data for ip_data in self.rate_limited_ips.values() 
                                if ip_data.get('blocked_until') and 
                                datetime.utcnow() < ip_data['blocked_until']])
        
        return {
            "protection_enabled": self.config['protection_enabled'],
            "server_ip": self.config['server_ip'],
            "website_accessible": self.config['website_accessible'],
            "admin_ips_configured": len(self.config['admin_access']['allowed_admin_ips']),
            "threat_cache_entries": total_threats,
            "high_threat_ips": high_threats,
            "active_rate_limits": active_rate_limits,
            "geo_blocking_enabled": self.config['geo_blocking']['enabled'],
            "privacy_protection": self.config['privacy_protection']['anonymize_logs'],
            "last_updated": datetime.utcnow().isoformat()
        }

# Create global instance
ip_protection = IPProtectionManager()

def get_client_ip(request) -> str:
    """Extract client IP from request (FastAPI/Flask compatible)"""
    # Check for forwarded IPs (behind proxy/CDN)
    forwarded_for = getattr(request, 'headers', {}).get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    
    real_ip = getattr(request, 'headers', {}).get('X-Real-IP')
    if real_ip:
        return real_ip
    
    # Fallback to direct connection
    try:
        client = getattr(request, 'client', None)
        if client and hasattr(client, 'host'):
            return client.host
        elif client and isinstance(client, tuple) and len(client) > 0:
            return client[0]
        return 'unknown'
    except Exception:
        return 'unknown'

def require_admin_ip(func):
    """Decorator to require admin IP for access"""
    def wrapper(*args, **kwargs):
        # Extract request from args (Flask/FastAPI compatible)
        request = args[0] if args else None
        
        if request:
            client_ip = get_client_ip(request)
            access_check = ip_protection.validate_ip_access(client_ip, "admin")
            
            if not access_check["allowed"]:
                return {
                    "error": "Access denied",
                    "reason": access_check.get("primary_reason", "IP not authorized"),
                    "client_ip": access_check["anonymized_ip"]
                }, 403
        
        return func(*args, **kwargs)
    return wrapper

if __name__ == "__main__":
    # Example usage
    manager = IPProtectionManager()
    
    # Test IP validation
    test_ip = "203.0.113.10"  # Example IP
    result = manager.validate_ip_access(test_ip, "general")
    print(f"IP Validation Result: {json.dumps(result, indent=2)}")
    
    # Show protection status
    status = manager.get_protection_status()
    print(f"Protection Status: {json.dumps(status, indent=2)}")