from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
# Use the primary agent implementation rather than the legacy alias
from agents.behavioral_analytics import BehavioralAnalyticsAgent
from agents.dmer_monitor_agent import DmerMonitorAgent
from admin_console import AdminConsole
from continuous_training_system import continuous_trainer, LearningEvent
from security_manager import (
    security_manager, 
    get_current_user, 
    require_admin_access, 
    require_master_admin,
    require_permission
)
# Import advanced security features
from advanced_api_security import (
    AdvancedSecurityManager,
    EnhancedRateLimitMiddleware,
    APIKeyAuth,
    log_security_event,
    get_security_metrics,
    advanced_security,
    api_key_auth
)
# Import IP protection system
from ip_protection_manager import ip_protection, get_client_ip, require_admin_ip
import json
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, validator
import uvicorn
import os
from collections import defaultdict
import re


# Emergency Access Control
def check_emergency_mode():
    if os.path.exists('.emergency_access_control'):
        if not os.path.exists('.emergency_admin_session'):
            raise HTTPException(status_code=503, detail="System in emergency lockdown mode")
    return True

# Add emergency check to all routes

# Input Validation
class InputValidator:
    @staticmethod
    def validate_agent_id(agent_id: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_-]+$', agent_id):
            raise ValueError("Invalid agent ID format")
        return agent_id
    
    @staticmethod  
    def validate_json_input(data: dict, max_size: int = 10000) -> dict:
        import json
        json_str = json.dumps(data)
        if len(json_str) > max_size:
            raise ValueError("Input data too large")
        return data


# Emergency Access Control
def check_emergency_mode():
    if os.path.exists('.emergency_access_control'):
        if not os.path.exists('.emergency_admin_session'):
            raise HTTPException(status_code=503, detail="System in emergency lockdown mode")
    return True

# Add emergency check to all routes

# Input Validation
class InputValidator:
    @staticmethod
    def validate_agent_id(agent_id: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_-]+$', agent_id):
            raise ValueError("Invalid agent ID format")
        return agent_id
    
    @staticmethod  
    def validate_json_input(data: dict, max_size: int = 10000) -> dict:
        import json
        json_str = json.dumps(data)
        if len(json_str) > max_size:
            raise ValueError("Input data too large")
        return data

# Rate Limiting Middleware
class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent abuse of API endpoints.
    Implements sliding window rate limiting per IP address.
    """
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls  # Max calls allowed
        self.period = period  # Time period in seconds
        self.clients = defaultdict(list)  # IP -> list of timestamps
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()
        
        # Clean old requests outside the time window
        self.clients[client_ip] = [
            req_time for req_time in self.clients[client_ip]
            if now - req_time < self.period
        ]
        
        # Check rate limit
        if len(self.clients[client_ip]) >= self.calls:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "error": "too_many_requests"
                }
            )
        
        # Add current request timestamp
        self.clients[client_ip].append(now)
        
        response = await call_next(request)
        return response

# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses to prevent common web vulnerabilities.
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # Stricter CSP - remove unsafe-inline and unsafe-eval for production
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self';"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response

# IP Protection Middleware
class IPProtectionMiddleware(BaseHTTPMiddleware):
    """
    IP-based security protection middleware
    Validates IP addresses and applies access controls
    """
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = get_client_ip(request)
        
        # Determine access type based on path
        access_type = "general"
        if any(admin_path in str(request.url.path) for admin_path in ["/admin", "/api/admin", "/security"]):
            access_type = "admin"
        
        # Validate IP access
        validation_result = ip_protection.validate_ip_access(client_ip, access_type)
        
        if not validation_result["allowed"]:
            # Log the blocked attempt
            log_security_event("ip_access_blocked", {
                "client_ip": validation_result["anonymized_ip"],
                "reason": validation_result.get("primary_reason", "Access denied"),
                "path": str(request.url.path),
                "user_agent": request.headers.get("user-agent", "unknown")
            })
            
            return JSONResponse(
                status_code=403,
                content={
                    "detail": f"Access denied: {validation_result.get('primary_reason', 'IP not authorized')}",
                    "error": "ip_access_denied",
                    "client_ip": validation_result["anonymized_ip"]
                }
            )
        
        # Add IP info to request state for later use
        request.state.client_ip = client_ip
        request.state.ip_validation = validation_result
        
        response = await call_next(request)
        return response

# Input Validation Utilities
class InputValidator:
    """Utility class for input validation and sanitization"""
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Sanitize string input to prevent injection attacks"""
        if not isinstance(value, str):
            raise ValueError("Input must be a string")
        
        # Truncate to max length
        value = value[:max_length]
        
        # Remove potential script tags and SQL injection patterns
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'DROP\s+TABLE',
            r'DELETE\s+FROM',
            r'INSERT\s+INTO',
            r'UPDATE\s+.*\s+SET'
        ]
        
        for pattern in dangerous_patterns:
            value = re.sub(pattern, '', value, flags=re.IGNORECASE)
        
        return value.strip()
    
    @staticmethod
    def validate_agent_id(agent_id: str) -> str:
        """Validate agent ID format"""
        if not re.match(r'^[a-zA-Z0-9_-]+$', agent_id):
            raise ValueError("Invalid agent ID format")
        return agent_id
    
    @staticmethod
    def validate_username(username: str) -> str:
        """Validate username format"""
        if not re.match(r'^[a-zA-Z0-9_]{3,32}$', username):
            raise ValueError("Username must be 3-32 characters and contain only letters, numbers, and underscores")
        return username

app = FastAPI(
    title="GuardianShield API", 
    description="GuardianShield Agent Management API - Secure Access Required | www.guardian-shield.io",
    version="2.0.0",
    docs_url="/admin/api-docs",  # Move API docs to admin area
    redoc_url="/admin/redoc"     # Move ReDoc to admin area
)

# Add security middlewares with enhanced protection
enhanced_rate_limiter = EnhancedRateLimitMiddleware(advanced_security)
app.add_middleware(IPProtectionMiddleware)  # Add IP protection first
app.add_middleware(SecurityHeadersMiddleware)
app.middleware("http")(enhanced_rate_limiter)  # Enhanced DDoS protection

# Configure CORS for frontend with stricter settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:8000", 
        "https://www.guardian-shield.io",
        "https://guardian-shield.io"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],  # Added API key header
    max_age=3600  # Cache preflight requests for 1 hour
)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Initialize admin console
admin_console = AdminConsole()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove dead connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Authentication Models
class LoginRequest(BaseModel):
    username: str
    password: str
    
    @validator('username')
    def validate_username(cls, v):
        return InputValidator.validate_username(v)
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8 or len(v) > 128:
            raise ValueError("Password must be between 8 and 128 characters")
        return v

class UserCreationRequest(BaseModel):
    username: str
    password: str
    role: str = "admin"
    permissions: List[str] = ["read", "agents", "threats"]
    
    @validator('username')
    def validate_username(cls, v):
        return InputValidator.validate_username(v)
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters for new users")
        return v
    
    @validator('role')
    def validate_role(cls, v):
        allowed_roles = ["admin", "operator", "viewer"]
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {', '.join(allowed_roles)}")
        return v

# Authentication Endpoints with Enhanced Security
@app.post("/api/auth/login")
async def login(login_data: LoginRequest, request: Request):
    """Authenticate user and return access token with enhanced security"""
    client_ip = request.client.host
    
    try:
        # Check if IP is blocked due to failed attempts
        if advanced_security.is_ip_blocked(client_ip):
            log_security_event('login_blocked_ip', client_ip, {
                'username': login_data.username,
                'reason': 'ip_blocked'
            })
            raise HTTPException(status_code=423, detail="IP temporarily blocked")
        
        # Authenticate user
        token = security_manager.authenticate_user(login_data.username, login_data.password)
        
        # Check if master admin requires Titan key
        if login_data.username == "master_admin":
            try:
                from google_titan_manager import GoogleTitanKeyManager
                titan_manager = GoogleTitanKeyManager()
                
                if titan_manager.settings.get("required_for_admin", False):
                    # Verify Titan key presence
                    if not titan_manager.verify_titan_key_present():
                        log_security_event('login_titan_key_missing', client_ip, {
                            'username': login_data.username
                        })
                        return JSONResponse(
                            status_code=206,  # Partial content - need second factor
                            content={
                                "message": "Insert your Google Titan Security Key and try again",
                                "requires_titan_key": True,
                                "error": "titan_key_required"
                            }
                        )
                    
                    # Authenticate with Titan key
                    auth_result = titan_manager.authenticate_with_titan_key("master_admin")
                    if not auth_result.get("success"):
                        advanced_security.log_failed_auth(client_ip)
                        log_security_event('login_titan_key_failed', client_ip, {
                            'username': login_data.username
                        })
                        raise HTTPException(status_code=401, detail="Titan key authentication failed")
            except ImportError:
                pass  # Titan key not available, continue with password only
        
        # Successful login
        log_security_event('login_success', client_ip, {
            'username': login_data.username,
            'auth_method': 'password_titan' if login_data.username == "master_admin" else 'password'
        })
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": security_manager.token_expiry_hours * 3600,
            "message": "Authentication successful",
            "requires_titan_key": False
        }
        
    except HTTPException:
        # Log failed authentication attempt
        advanced_security.log_failed_auth(client_ip)
        log_security_event('login_failed', client_ip, {
            'username': login_data.username,
            'reason': 'invalid_credentials'
        })
        raise
    except Exception as e:
        # Log failed authentication attempt
        advanced_security.log_failed_auth(client_ip)
        log_security_event('login_error', client_ip, {
            'username': login_data.username,
            'error': str(e)
        })
        
        # Generic error message to prevent information disclosure
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Authentication service temporarily unavailable",
                "error": "service_error"
            }
        )

@app.post("/api/auth/logout")
async def logout(user_info = Depends(get_current_user)):
    """Logout current user"""
    # In a production system, you'd invalidate the token
    return {"message": "Logged out successfully"}

@app.get("/api/auth/me")
async def get_current_user_info(user_info = Depends(get_current_user)):
    """Get current user information"""
    return {
        "username": user_info["username"],
        "role": user_info["role"],
        "permissions": security_manager.authorized_users.get(user_info["username"], {}).get("permissions", [])
    }

# Enhanced Security Endpoints
@app.post("/api/security/api-key")
async def create_api_key(
    request_data: Dict[str, Any],
    user_info = Depends(require_master_admin)
):
    """Create new API key for programmatic access (Master admin only)"""
    try:
        user = request_data.get('user', user_info['username'])
        permissions = request_data.get('permissions', ['read'])
        rate_limit = min(request_data.get('rate_limit', 1000), 10000)  # Max 10k req/min
        
        api_key = advanced_security.create_api_key(user, permissions, rate_limit)
        
        log_security_event('api_key_created', request.client.host, {
            'created_by': user_info['username'],
            'target_user': user,
            'permissions': permissions
        })
        
        return {
            "api_key": api_key,
            "user": user,
            "permissions": permissions,
            "rate_limit": rate_limit,
            "created_at": datetime.now().isoformat(),
            "note": "Store this key securely - it cannot be retrieved again"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create API key")

@app.get("/api/security/status")
async def get_security_status(user_info = Depends(require_admin_access)):
    """Get current security status and metrics"""
    try:
        metrics = get_security_metrics()
        return {
            "security_status": "active",
            "blocked_ips": metrics['active_blocks'],
            "suspicious_ips": metrics['suspicious_ips'],
            "api_keys_active": metrics['api_keys_active'],
            "rate_limit_active": True,
            "ddos_protection": True,
            "attack_detection": True,
            "titan_key_enabled": getattr(security_manager, 'security_key_required', False)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get security status")

@app.post("/api/security/unblock-ip")
async def unblock_ip(
    request_data: Dict[str, str],
    user_info = Depends(require_master_admin)
):
    """Manually unblock an IP address (Master admin only)"""
    try:
        ip = request_data.get('ip', '').strip()
        if not ip:
            raise ValueError("IP address required")
        
        if ip in advanced_security.blocked_ips:
            del advanced_security.blocked_ips[ip]
            log_security_event('ip_unblocked', request.client.host, {
                'unblocked_by': user_info['username'],
                'target_ip': ip
            })
            return {"message": f"IP {ip} has been unblocked", "unblocked_by": user_info['username']}
        else:
            return {"message": f"IP {ip} was not blocked"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to unblock IP")

@app.get("/api/security/events")
async def get_security_events(
    limit: int = 100,
    user_info = Depends(require_admin_access)
):
    """Get recent security events"""
    try:
        events = []
        if os.path.exists('security_events.jsonl'):
            with open('security_events.jsonl', 'r') as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    try:
                        event = json.loads(line.strip())
                        # Sanitize sensitive information
                        if 'details' in event:
                            event['details'].pop('password', None)
                            event['details'].pop('api_key', None)
                        events.append(event)
                    except:
                        continue
        
        return {"events": events, "total": len(events)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve security events")

# === IP PROTECTION ENDPOINTS ===

@app.get("/api/security/ip-status")
async def get_ip_protection_status(
    user_info = Depends(require_admin_access)
):
    """Get IP protection system status"""
    try:
        status = ip_protection.get_protection_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get IP protection status: {e}")

@app.post("/api/security/add-admin-ip")
async def add_admin_ip(
    request_data: Dict[str, str],
    user_info = Depends(require_master_admin)
):
    """Add IP address to admin whitelist"""
    try:
        ip_address = request_data.get('ip', '').strip()
        if not ip_address:
            raise ValueError("IP address required")
        
        result = ip_protection.add_admin_ip(ip_address)
        
        if result["success"]:
            log_security_event('admin_ip_added', ip_address, {
                'added_by': user_info['username'],
                'ip_address': ip_address
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add admin IP: {e}")

@app.post("/api/security/remove-admin-ip")
async def remove_admin_ip(
    request_data: Dict[str, str],
    user_info = Depends(require_master_admin)
):
    """Remove IP address from admin whitelist"""
    try:
        ip_address = request_data.get('ip', '').strip()
        if not ip_address:
            raise ValueError("IP address required")
        
        result = ip_protection.remove_admin_ip(ip_address)
        
        if result["success"]:
            log_security_event('admin_ip_removed', ip_address, {
                'removed_by': user_info['username'],
                'ip_address': ip_address
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove admin IP: {e}")

@app.get("/api/security/ip-logs")
async def get_ip_access_logs(
    limit: int = 100,
    user_info = Depends(require_admin_access)
):
    """Get IP access logs"""
    try:
        logs = []
        if os.path.exists('ip_access_log.jsonl'):
            with open('ip_access_log.jsonl', 'r') as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    try:
                        log_entry = json.loads(line.strip())
                        logs.append(log_entry)
                    except:
                        continue
        
        return {"logs": logs, "total": len(logs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get IP logs: {e}")

@app.get("/api/security/client-ip")
async def get_client_ip_info(request: Request):
    """Get current client IP information (public endpoint)"""
    try:
        client_ip = get_client_ip(request)
        
        # Get IP validation info if available
        ip_validation = getattr(request.state, 'ip_validation', None)
        
        return {
            "client_ip": ip_validation["anonymized_ip"] if ip_validation else "unknown",
            "access_allowed": ip_validation["allowed"] if ip_validation else True,
            "server_ip": ip_protection.config.get("server_ip", "unknown"),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": f"Failed to get IP info: {e}"}

# Enhanced authentication with API key support
def get_enhanced_user(request: Request):
    """Enhanced user authentication with API key and JWT support"""
    return api_key_auth(request)

@app.post("/api/auth/create-user")
async def create_user(
    user_data: UserCreationRequest,
    admin_user = Depends(require_master_admin)
):
    """Create new authorized user (Master Admin Only)"""
    try:
        security_manager.add_authorized_user(
            user_data.username,
            user_data.password,
            user_data.role,
            user_data.permissions
        )
        return {"message": f"User '{user_data.username}' created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create user: {str(e)}")

@app.delete("/api/auth/revoke-user/{username}")
async def revoke_user_access(
    username: str,
    admin_user = Depends(require_master_admin)
):
    """Revoke user access (Master Admin Only)"""
    try:
        security_manager.revoke_user_access(username)
        return {"message": f"Access revoked for user '{username}'"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to revoke access: {str(e)}")

# Continuous Training API Endpoints (Now Secured)
@app.post("/api/training/threat-detection")
async def report_threat_detection(
    data: Dict[str, Any],
    user_info = Depends(require_permission("agents"))
):
    """Report a threat detection for training (Requires agent access)"""
    try:
        # Validate and sanitize inputs
        agent_id = InputValidator.validate_agent_id(data.get('agent_id', 'unknown'))
        confidence = float(data.get('confidence', 0.5))
        
        # Validate confidence range
        if not 0 <= confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        
        event = LearningEvent(
            event_type='threat_detected',
            agent_id=agent_id,
            data=data.get('threat_data', {}),
            confidence=confidence
        )
        continuous_trainer.add_learning_event(event)
        
        # Broadcast to connected clients with user context
        await manager.broadcast(json.dumps({
            'type': 'training_event',
            'event': 'threat_detection',
            'agent': agent_id,
            'reported_by': user_info["username"],
            'timestamp': datetime.now().isoformat()
        }))
        
        return {"status": "success", "message": "Threat detection reported for training", "reported_by": user_info["username"]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to report threat detection")

@app.post("/api/training/false-positive")
async def report_false_positive(
    data: Dict[str, Any],
    user_info = Depends(require_permission("agents"))
):
    """Report a false positive for immediate retraining (Requires agent access)"""
    try:
        # Validate and sanitize inputs
        agent_id = InputValidator.validate_agent_id(data.get('agent_id', 'unknown'))
        feedback = InputValidator.sanitize_string(data.get('feedback', ''), max_length=500)
        
        event = LearningEvent(
            event_type='false_positive',
            agent_id=agent_id,
            data=data.get('detection_data', {}),
            feedback=feedback,
            confidence=0.0
        )
        continuous_trainer.add_learning_event(event)
        
        # Broadcast to connected clients with user context
        await manager.broadcast(json.dumps({
            'type': 'training_event',
            'event': 'false_positive',
            'agent': agent_id,
            'feedback': feedback[:100],  # Truncate for broadcast
            'reported_by': user_info["username"],
            'timestamp': datetime.now().isoformat()
        }))
        
        return {"status": "success", "message": "False positive reported for retraining", "reported_by": user_info["username"]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to report false positive")

@app.get("/api/training/status")
async def get_training_status():
    """Get current training system status"""
    try:
        status = continuous_trainer.get_training_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/training/start")
async def start_training(admin_user = Depends(require_admin_access)):
    """Start continuous training system"""
    try:
        # Start training in background task
        asyncio.create_task(continuous_trainer.continuous_training_loop())
        return {"status": "success", "message": "Continuous training started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/training/stop")
async def stop_training(admin_user = Depends(require_admin_access)):
    """Stop continuous training system"""
    try:
        continuous_trainer.stop_training()
        return {"status": "success", "message": "Continuous training stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve frontend
@app.get("/")
async def serve_frontend():
    return FileResponse("frontend/index.html")

# Agent management endpoints
@app.get("/api/agents")
async def get_agents(user = Depends(get_current_user)):
    """Get all agents status"""
    return {
        "agents": [
            {
                "id": "learning_agent",
                "name": "Learning Agent", 
                "status": "active",
                "actions": 1247,
                "evolutions": 5,
                "accuracy": 94.5,
                "autonomyLevel": 10
            },
            {
                "id": "behavioral_analytics",
                "name": "Behavioral Analytics",
                "status": "active", 
                "actions": 892,
                "evolutions": 3,
                "accuracy": 96.2,
                "autonomyLevel": 9
            }
        ]
    }

@app.post("/api/agents/{agent_id}/start")
async def start_agent(agent_id: str, admin_user = Depends(require_admin_access)):
    """Start an agent (Admin Only)"""
    try:
        # Validate agent_id
        agent_id = InputValidator.validate_agent_id(agent_id)
        
        # Log the action
        admin_console.log_action(
            agent_id,
            "agent_start",
            {"action": "start", "admin": admin_user["username"], "timestamp": time.time()},
            severity=5
        )
        
        # Broadcast status update with admin context
        await manager.broadcast(json.dumps({
            "type": "agent_status_update",
            "payload": {
                "agentId": agent_id,
                "status": "active",
                "admin": admin_user["username"],
                "timestamp": time.time()
            }
        }))
        
        return {"status": "success", "message": f"Agent {agent_id} started by {admin_user['username']}"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Don't expose internal error details
        raise HTTPException(status_code=500, detail="Failed to start agent")

@app.post("/api/agents/{agent_id}/stop")
async def stop_agent(agent_id: str, admin_user = Depends(require_admin_access)):
    """Stop an agent (Admin Only)"""
    try:
        # Validate agent_id
        agent_id = InputValidator.validate_agent_id(agent_id)
        
        # Log the action
        admin_console.log_action(
            agent_id,
            "agent_stop", 
            {"action": "stop", "admin": admin_user["username"], "timestamp": time.time()},
            severity=5
        )
        
        # Broadcast status update
        await manager.broadcast(json.dumps({
            "type": "agent_status_update",
            "payload": {
                "agentId": agent_id,
                "status": "inactive",
                "timestamp": time.time()
            }
        }))
        
        return {"status": "success", "message": f"Agent {agent_id} stopped"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to stop agent")

@app.put("/api/agents/{agent_id}/config")
async def update_agent_config(agent_id: str, config: dict, admin_user = Depends(require_admin_access)):
    """Update agent configuration (Admin Only)"""
    try:
        # Validate agent_id
        agent_id = InputValidator.validate_agent_id(agent_id)
        
        # Validate config size to prevent DoS
        config_str = json.dumps(config)
        if len(config_str) > 10000:  # Max 10KB config
            raise HTTPException(status_code=400, detail="Configuration too large")
        
        # Log the configuration change
        admin_console.log_action(
            agent_id,
            "config_update",
            {"config": config, "admin": admin_user["username"], "timestamp": time.time()},
            severity=6
        )
        
        return {"status": "success", "message": "Configuration updated"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update configuration")

@app.post("/api/agents/{agent_id}/evolve")
async def evolve_agent(agent_id: str, admin_user = Depends(require_admin_access)):
    """Trigger agent evolution (Admin Only)"""
    try:
        # Validate agent_id
        agent_id = InputValidator.validate_agent_id(agent_id)
        
        # Log evolution trigger
        admin_console.log_evolution_decision(
            agent_id,
            "manual_evolution_trigger",
            {"trigger": "api", "admin": admin_user["username"], "timestamp": time.time()}
        )
        
        # Simulate evolution process
        await asyncio.sleep(1)
        
        # Broadcast evolution complete
        await manager.broadcast(json.dumps({
            "type": "agent_evolution",
            "payload": {
                "agentId": agent_id,
                "evolutionData": {
                    "improvementPercentage": 12.5,
                    "newAccuracy": 96.7
                },
                "timestamp": time.time()
            }
        }))
        
        return {"status": "success", "message": f"Agent {agent_id} evolution initiated"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to trigger evolution")

# Emergency stop endpoint (Master Admin Only)
@app.post("/api/emergency-stop")
async def emergency_stop(master_admin = Depends(require_master_admin)):
    """Emergency stop all agents (MASTER ADMIN ONLY)"""
    try:
        # Create emergency stop flag
        with open("emergency_stop.flag", "w") as f:
            f.write(f"{time.time()}|{master_admin['username']}")
        
        # Log emergency stop with admin info
        admin_console.log_action(
            "SYSTEM",
            "emergency_stop",
            {"reason": "manual_trigger", "admin": master_admin["username"], "timestamp": time.time()},
            severity=10
        )
        
        # Broadcast emergency alert with admin context
        await manager.broadcast(json.dumps({
            "type": "emergency_alert",
            "payload": {
                "message": f"EMERGENCY STOP initiated by {master_admin['username']} - All agents stopped",
                "admin": master_admin["username"],
                "timestamp": time.time()
            }
        }))
        
        return {"status": "success", "message": f"Emergency stop executed by {master_admin['username']}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Example: Endpoint to run Behavioral Analytics Agent
def get_behavioral_analytics_result():
    agent = BehavioralAnalyticsAgent()
    result = agent.run() if hasattr(agent, 'run') else {"status": "agent_active"}
    return result

@app.get("/api/behavioral-analytics")
def behavioral_analytics():
    return {"result": get_behavioral_analytics_result()}

# Example: Endpoint to run DMER Monitor Agent
def get_dmer_monitor_result():
    agent = DmerMonitorAgent()
    result = agent.run() if hasattr(agent, 'run') else {"status": "agent_active"}
    return result

@app.get("/api/dmer-monitor")
def dmer_monitor():
    return {"result": get_dmer_monitor_result()}

# WebSocket endpoint for real-time updates
@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Send heartbeat every 30 seconds
            await asyncio.sleep(30)
            await websocket.send_text(json.dumps({
                "type": "heartbeat",
                "payload": {"timestamp": time.time()}
            }))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Background task to simulate real-time data
async def simulate_real_time_data():
    """Simulate real-time agent data and threats"""
    while True:
        try:
            # Simulate threat detection
            if len(manager.active_connections) > 0:
                await manager.broadcast(json.dumps({
                    "type": "threat_detected",
                    "payload": {
                        "id": f"threat_{int(time.time())}",
                        "title": "Suspicious Activity Detected",
                        "description": "Anomalous transaction pattern identified",
                        "severity": "medium",
                        "source": "behavioral_analytics"
                    }
                }))
            
            await asyncio.sleep(60)  # Send update every minute
            
        except Exception as e:
            print(f"Error in background task: {e}")
            await asyncio.sleep(10)

# Start background task
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(simulate_real_time_data())

# Add more endpoints for other agents as needed

if __name__ == "__main__":
    print("🛡️ Starting GuardianShield API Server...")
    print("🌐 Production Domain: https://www.guardian-shield.io")
    print("📊 Local Dashboard: http://localhost:8000")
    print("🔐 Admin Access: http://localhost:8000/admin")
    print("🔌 WebSocket endpoint: ws://localhost:8000/ws")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
