"""
admin_auth.py: Authentication and authorization module for GuardianShield Admin Console
Provides secure access control for agent monitoring and management features.
"""

import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import json
import logging

logger = logging.getLogger(__name__)

class AdminAuth:
    """Secure authentication system for admin console access"""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict] = {}
        self.failed_attempts: Dict[str, List[float]] = {}
        self.admin_keys = {
            "GUARDIAN_ADMIN_2025": {
                "level": "full",
                "permissions": ["agent_control", "3d_visualization", "monitoring", "evolution", "console"],
                "expires": None
            },
            "gs_admin_secure": {
                "level": "monitoring",
                "permissions": ["monitoring", "3d_visualization"],
                "expires": None
            }
        }
        
        # Security settings
        self.max_failed_attempts = 3
        self.lockout_duration = 300  # 5 minutes
        self.session_timeout = 3600  # 1 hour
        
    def authenticate(self, admin_key: str, client_ip: str = "127.0.0.1") -> Optional[Dict]:
        """Authenticate admin access with rate limiting"""
        
        # Check for rate limiting
        if self._is_rate_limited(client_ip):
            logger.warning(f"Rate limited authentication attempt from {client_ip}")
            return None
            
        # Validate admin key
        if admin_key not in self.admin_keys:
            self._record_failed_attempt(client_ip)
            logger.warning(f"Invalid admin key attempt from {client_ip}")
            return None
            
        # Create session
        session_token = secrets.token_urlsafe(32)
        session_data = {
            "token": session_token,
            "admin_key": admin_key,
            "permissions": self.admin_keys[admin_key]["permissions"],
            "level": self.admin_keys[admin_key]["level"],
            "client_ip": client_ip,
            "created_at": time.time(),
            "expires_at": time.time() + self.session_timeout,
            "last_activity": time.time()
        }
        
        self.active_sessions[session_token] = session_data
        self._clear_failed_attempts(client_ip)
        
        logger.info(f"Admin session created for {admin_key} from {client_ip}")
        return session_data
        
    def validate_session(self, session_token: str) -> Optional[Dict]:
        """Validate an active admin session"""
        if session_token not in self.active_sessions:
            return None
            
        session = self.active_sessions[session_token]
        
        # Check if session expired
        if time.time() > session["expires_at"]:
            del self.active_sessions[session_token]
            return None
            
        # Update last activity
        session["last_activity"] = time.time()
        return session
        
    def has_permission(self, session_token: str, permission: str) -> bool:
        """Check if session has specific permission"""
        session = self.validate_session(session_token)
        if not session:
            return False
            
        return permission in session["permissions"]
        
    def revoke_session(self, session_token: str) -> bool:
        """Revoke an admin session"""
        if session_token in self.active_sessions:
            del self.active_sessions[session_token]
            logger.info(f"Admin session {session_token[:8]}... revoked")
            return True
        return False
        
    def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client IP is rate limited"""
        if client_ip not in self.failed_attempts:
            return False
            
        attempts = self.failed_attempts[client_ip]
        recent_attempts = [
            attempt for attempt in attempts 
            if time.time() - attempt < self.lockout_duration
        ]
        
        self.failed_attempts[client_ip] = recent_attempts
        return len(recent_attempts) >= self.max_failed_attempts
        
    def _record_failed_attempt(self, client_ip: str) -> None:
        """Record a failed authentication attempt"""
        if client_ip not in self.failed_attempts:
            self.failed_attempts[client_ip] = []
        self.failed_attempts[client_ip].append(time.time())
        
    def _clear_failed_attempts(self, client_ip: str) -> None:
        """Clear failed attempts for successful authentication"""
        if client_ip in self.failed_attempts:
            del self.failed_attempts[client_ip]
            
    def get_active_sessions(self) -> List[Dict]:
        """Get all active admin sessions (for monitoring)"""
        return [
            {
                "token": token[:8] + "...",
                "level": session["level"],
                "client_ip": session["client_ip"],
                "created_at": datetime.fromtimestamp(session["created_at"]).isoformat(),
                "last_activity": datetime.fromtimestamp(session["last_activity"]).isoformat()
            }
            for token, session in self.active_sessions.items()
        ]
        
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        current_time = time.time()
        expired_tokens = [
            token for token, session in self.active_sessions.items()
            if current_time > session["expires_at"]
        ]
        
        for token in expired_tokens:
            del self.active_sessions[token]
            
        if expired_tokens:
            logger.info(f"Cleaned up {len(expired_tokens)} expired admin sessions")
            
        return len(expired_tokens)

# Global auth instance
admin_auth = AdminAuth()

def require_admin_permission(permission: str):
    """Decorator to require admin permission for function access"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            session_token = kwargs.get('session_token')
            if not session_token or not admin_auth.has_permission(session_token, permission):
                raise PermissionError(f"Admin permission '{permission}' required")
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Secure admin functions
@require_admin_permission('agent_control')
def admin_control_agents(session_token: str, action: str, agent_id: str = None):
    """Secure agent control function"""
    session = admin_auth.validate_session(session_token)
    logger.info(f"Admin {session['level']} performed agent control: {action} on {agent_id}")
    # Agent control logic here
    return {"status": "success", "action": action, "agent_id": agent_id}

@require_admin_permission('3d_visualization')
def admin_access_3d_visualization(session_token: str):
    """Secure 3D visualization access"""
    session = admin_auth.validate_session(session_token)
    logger.info(f"Admin {session['level']} accessed 3D visualization")
    return {"status": "authorized", "redirect": "agent3d-demo.html"}

@require_admin_permission('monitoring')
def admin_access_monitoring(session_token: str):
    """Secure monitoring access"""
    session = admin_auth.validate_session(session_token)
    logger.info(f"Admin {session['level']} accessed monitoring systems")
    return {"status": "authorized", "redirect": "index.html#agents"}

@require_admin_permission('evolution')
def admin_control_evolution(session_token: str, parameters: Dict):
    """Secure evolution control"""
    session = admin_auth.validate_session(session_token)
    logger.info(f"Admin {session['level']} modified evolution parameters")
    return {"status": "success", "parameters": parameters}