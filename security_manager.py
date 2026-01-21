"""
GuardianShield Authentication & Access Control System
Implements strict security controls for admin access with FIDO2/WebAuthn support
"""

import os
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import json
import logging

# Import security key manager
try:
    from security_key_manager import GuardianShieldSecurityKey
    SECURITY_KEY_AVAILABLE = True
except ImportError:
    SECURITY_KEY_AVAILABLE = False
    logging.warning("Security key support not available - install fido2 package")

class SecurityManager:
    def __init__(self):
        # Load or generate master keys
        self.secret_key = self._load_or_generate_secret()
        self.master_admin_hash = self._load_or_generate_master_admin()
        self.authorized_users = self._load_authorized_users()
        self.active_sessions = {}
        
        # Initialize security key manager
        if SECURITY_KEY_AVAILABLE:
            self.security_key_manager = GuardianShieldSecurityKey()
            self.security_key_required = self._load_security_key_settings()
        else:
            self.security_key_manager = None
            self.security_key_required = False
        
        # Security settings
        self.token_expiry_hours = 8  # Sessions expire after 8 hours
        self.max_failed_attempts = 3
        self.lockout_duration_minutes = 15
        self.failed_attempts = {}
        
    def _load_or_generate_secret(self) -> str:
        """Load existing secret key or generate new one"""
        secret_file = ".guardian_secret"
        if os.path.exists(secret_file):
            with open(secret_file, 'r') as f:
                return f.read().strip()
        else:
            # Generate cryptographically secure secret
            secret = secrets.token_urlsafe(64)
            with open(secret_file, 'w') as f:
                f.write(secret)
            os.chmod(secret_file, 0o600)  # Owner read/write only
            return secret
    
    def _load_or_generate_master_admin(self) -> str:
        """Load or generate master admin credentials"""
        admin_file = ".guardian_admin"
        if os.path.exists(admin_file):
            with open(admin_file, 'r') as f:
                return f.read().strip()
        else:
            # Generate master admin password and hash it
            master_password = secrets.token_urlsafe(32)
            password_hash = hashlib.sha256(f"guardian_master_{master_password}".encode()).hexdigest()
            
            with open(admin_file, 'w') as f:
                f.write(password_hash)
            os.chmod(admin_file, 0o600)
            
            # Save the actual password for initial setup
            with open(".guardian_master_password.txt", 'w') as f:
                f.write(f"MASTER ADMIN PASSWORD: {master_password}\n")
                f.write(f"Generated: {datetime.now()}\n")
                f.write("IMPORTANT: Save this password securely and delete this file!\n")
            os.chmod(".guardian_master_password.txt", 0o600)
            
            return password_hash
    
    def _load_authorized_users(self) -> Dict:
        """Load authorized users list"""
        users_file = ".guardian_authorized_users.json"
        if os.path.exists(users_file):
            with open(users_file, 'r') as f:
                return json.load(f)
        else:
            # Initialize with empty authorized users
            default_users = {
                "master_admin": {
                    "role": "master",
                    "permissions": ["all"],
                    "created": datetime.now().isoformat(),
                    "active": True
                }
            }
            self._save_authorized_users(default_users)
            return default_users
    
    def _save_authorized_users(self, users: Dict):
        """Save authorized users to file"""
        users_file = ".guardian_authorized_users.json"
        with open(users_file, 'w') as f:
            json.dump(users, f, indent=2)
        os.chmod(users_file, 0o600)
        self.authorized_users = users
    
    def authenticate_master_admin(self, password: str) -> bool:
        """Authenticate master admin password"""
        password_hash = hashlib.sha256(f"guardian_master_{password}".encode()).hexdigest()
        return password_hash == self.master_admin_hash
    
    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return JWT token"""
        # Check for lockout
        if self._is_locked_out(username):
            raise HTTPException(status_code=423, detail="Account temporarily locked due to failed attempts")
        
        # Master admin authentication
        if username == "master_admin":
            if self.authenticate_master_admin(password):
                self._clear_failed_attempts(username)
                return self._generate_token(username, "master")
            else:
                self._record_failed_attempt(username)
                raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Regular user authentication
        if username not in self.authorized_users:
            # RELOAD ATTEMPT: User might suspect file update but server hasn't restarted
            # Reload users from disk to check if a new user was added
            self.authorized_users = self._load_authorized_users()
            
            if username not in self.authorized_users:
                self._record_failed_attempt(username)
                print(f"[AUTH-DEBUG] Auth failed: User '{username}' not found in authorized_users. Users loaded: {list(self.authorized_users.keys())}")
                raise HTTPException(status_code=401, detail=f"User '{username}' not recognized")
        
        user_info = self.authorized_users[username]
        if not user_info.get("active", False):
            raise HTTPException(status_code=401, detail="Account disabled")
        
        # Check password (for demo, using simple hash - in production use proper password hashing)
        expected_hash = user_info.get("password_hash", "")
        provided_hash = hashlib.sha256(f"guardian_user_{password}".encode()).hexdigest()
        
        if expected_hash == provided_hash:
            self._clear_failed_attempts(username)
            return self._generate_token(username, user_info.get("role", "user"))
        else:
            # RELOAD ATTEMPT: Hash mismatch, maybe password was updated?
            self.authorized_users = self._load_authorized_users()
            user_info = self.authorized_users[username]
            expected_hash = user_info.get("password_hash", "")
            
            if expected_hash == provided_hash:
                 self._clear_failed_attempts(username)
                 return self._generate_token(username, user_info.get("role", "user"))

            self._record_failed_attempt(username)
            print(f"[AUTH-DEBUG] Auth failed: Password mismatch for '{username}'. Provided hash: {provided_hash[:8]}... Expected: {expected_hash[:8]}...")
            raise HTTPException(status_code=401, detail="Invalid password")
    
    def _generate_token(self, username: str, role: str) -> str:
        """Generate JWT token for authenticated user"""
        payload = {
            "username": username,
            "role": role,
            "exp": datetime.utcnow() + timedelta(hours=self.token_expiry_hours),
            "iat": datetime.utcnow(),
            "session_id": secrets.token_urlsafe(16)
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        
        # Store active session
        self.active_sessions[payload["session_id"]] = {
            "username": username,
            "role": role,
            "created": datetime.utcnow(),
            "last_activity": datetime.utcnow()
        }
        
        return token
    
    def verify_token(self, token: str) -> Dict:
        """Verify JWT token and return user info"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            
            # Check if session is still active
            session_id = payload.get("session_id")
            if session_id not in self.active_sessions:
                raise HTTPException(status_code=401, detail="Session expired")
            
            # Update last activity
            self.active_sessions[session_id]["last_activity"] = datetime.utcnow()
            
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    def _is_locked_out(self, username: str) -> bool:
        """Check if user is locked out due to failed attempts"""
        if username not in self.failed_attempts:
            return False
        
        attempts = self.failed_attempts[username]
        if attempts["count"] >= self.max_failed_attempts:
            lockout_time = attempts["last_attempt"] + timedelta(minutes=self.lockout_duration_minutes)
            if datetime.utcnow() < lockout_time:
                return True
            else:
                # Lockout period expired, clear attempts
                del self.failed_attempts[username]
        
        return False
    
    def _record_failed_attempt(self, username: str):
        """Record failed login attempt"""
        if username not in self.failed_attempts:
            self.failed_attempts[username] = {"count": 0, "last_attempt": None}
        
        self.failed_attempts[username]["count"] += 1
        self.failed_attempts[username]["last_attempt"] = datetime.utcnow()
    
    def _clear_failed_attempts(self, username: str):
        """Clear failed attempts for user"""
        if username in self.failed_attempts:
            del self.failed_attempts[username]
    
    def add_authorized_user(self, username: str, password: str, role: str = "admin", permissions: List[str] = None):
        """Add new authorized user (master admin only)"""
        if permissions is None:
            permissions = ["read", "agents", "threats"]
        
        password_hash = hashlib.sha256(f"guardian_user_{password}".encode()).hexdigest()
        
        self.authorized_users[username] = {
            "role": role,
            "permissions": permissions,
            "password_hash": password_hash,
            "created": datetime.now().isoformat(),
            "active": True
        }
        
        self._save_authorized_users(self.authorized_users)
    
    def revoke_user_access(self, username: str):
        """Revoke user access (master admin only)"""
        if username in self.authorized_users and username != "master_admin":
            self.authorized_users[username]["active"] = False
            self._save_authorized_users(self.authorized_users)
            
            # End all active sessions for this user
            sessions_to_remove = []
            for session_id, session_info in self.active_sessions.items():
                if session_info["username"] == username:
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del self.active_sessions[session_id]
    
    def has_permission(self, user_info: Dict, permission: str) -> bool:
        """Check if user has specific permission"""
        role = user_info.get("role", "")
        username = user_info.get("username", "")
        
        # Master admin has all permissions
        if role == "master" or username == "master_admin":
            return True
        
        # Check user permissions
        if username in self.authorized_users:
            user_perms = self.authorized_users[username].get("permissions", [])
            return permission in user_perms or "all" in user_perms
        
        return False
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions to prevent memory leaks"""
        now = datetime.utcnow()
        expired_sessions = []
        
        for session_id, session_info in self.active_sessions.items():
            # Remove sessions older than token expiry time
            session_age = now - session_info.get("created", now)
            if session_age > timedelta(hours=self.token_expiry_hours):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
        
        return len(expired_sessions)
    
    def _load_security_key_settings(self) -> bool:
        """Load security key requirement settings"""
        settings_file = ".guardian_security_key_settings.json"
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                return settings.get("required", False)
            except Exception:
                return False
        return False
    
    def _save_security_key_settings(self, required: bool):
        """Save security key requirement settings"""
        settings_file = ".guardian_security_key_settings.json"
        settings = {"required": required, "updated": datetime.now().isoformat()}
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        os.chmod(settings_file, 0o600)
        self.security_key_required = required
    
    def enable_security_key_requirement(self):
        """Enable security key requirement for admin access"""
        if not SECURITY_KEY_AVAILABLE:
            raise ValueError("Security key support not available")
        self._save_security_key_settings(True)
        return True
    
    def disable_security_key_requirement(self):
        """Disable security key requirement (password-only access)"""
        self._save_security_key_settings(False)
        return True
    
    def register_admin_security_key(self, admin_username: str = "master_admin") -> Dict:
        """Register a security key for admin user"""
        if not SECURITY_KEY_AVAILABLE:
            raise ValueError("Security key support not available")
        
        # Create unique user ID for master admin
        user_id = hashlib.sha256(f"guardian_admin_{admin_username}".encode()).hexdigest()
        
        return self.security_key_manager.register_security_key(
            user_id=user_id,
            username=admin_username,
            display_name="GuardianShield Master Admin"
        )
    
    def complete_admin_key_registration(self, challenge_id: str, credential_response: Dict) -> Dict:
        """Complete security key registration for admin"""
        if not SECURITY_KEY_AVAILABLE:
            raise ValueError("Security key support not available")
        
        result = self.security_key_manager.complete_registration(challenge_id, credential_response)
        
        # If registration successful, enable security key requirement
        if result.get("success"):
            self.enable_security_key_requirement()
            
        return result
    
    def authenticate_with_master_admin_key(self, password: str) -> Dict:
        """Start security key authentication for master admin (requires password first)"""
        if not SECURITY_KEY_AVAILABLE:
            raise ValueError("Security key support not available")
        
        # First verify password
        if not self.authenticate_master_admin(password):
            raise ValueError("Invalid master admin password")
        
        # Then request security key authentication
        admin_user_id = hashlib.sha256("guardian_admin_master_admin".encode()).hexdigest()
        return self.security_key_manager.authenticate_with_security_key(admin_user_id)
    
    def complete_admin_key_authentication(self, challenge_id: str, auth_response: Dict) -> str:
        """Complete security key authentication and create admin session"""
        if not SECURITY_KEY_AVAILABLE:
            raise ValueError("Security key support not available")
        
        result = self.security_key_manager.complete_authentication(challenge_id, auth_response)
        
        if result.get("success"):
            # Create admin session token
            token_data = {
                "username": "master_admin",
                "role": "master",
                "permissions": ["all"],
                "auth_method": "password+security_key",
                "exp": datetime.utcnow() + timedelta(hours=self.token_expiry_hours)
            }
            
            token = jwt.encode(token_data, self.secret_key, algorithm="HS256")
            
            # Store session info
            self.active_sessions[token] = {
                "username": "master_admin",
                "role": "master",
                "created": datetime.utcnow(),
                "auth_method": "password+security_key"
            }
            
            return token
        else:
            raise ValueError("Security key authentication failed")
    
    def authenticate_master_admin_with_key(self, password: str) -> tuple[bool, Optional[Dict]]:
        """
        Authenticate master admin with password and security key requirement check
        Returns: (password_valid, security_key_challenge_or_none)
        """
        password_valid = self.authenticate_master_admin(password)
        
        if not password_valid:
            return False, None
        
        # If security key is required and available, return challenge
        if self.security_key_required and SECURITY_KEY_AVAILABLE:
            try:
                challenge_data = self.authenticate_with_master_admin_key(password)
                return True, challenge_data
            except Exception as e:
                # If security key fails, still allow password-only if not strictly required
                return True, None
        
        # Password-only authentication
        return True, None
    
    def get_admin_security_keys(self) -> List[Dict]:
        """Get registered security keys for admin user"""
        if not SECURITY_KEY_AVAILABLE:
            return []
        
        admin_user_id = hashlib.sha256("guardian_admin_master_admin".encode()).hexdigest()
        return self.security_key_manager.get_user_credentials(admin_user_id)
    
    def remove_admin_security_key(self, credential_id: str) -> bool:
        """Remove a security key for admin user"""
        if not SECURITY_KEY_AVAILABLE:
            return False
        
        admin_user_id = hashlib.sha256("guardian_admin_master_admin".encode()).hexdigest()
        return self.security_key_manager.remove_credential(admin_user_id, credential_id)

# Global security manager instance
security_manager = SecurityManager()

# FastAPI security scheme
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user"""
    return security_manager.verify_token(credentials.credentials)

async def require_admin_access(user_info = Depends(get_current_user)):
    """Dependency to require admin access"""
    if not security_manager.has_permission(user_info, "admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_info

async def require_master_admin(user_info = Depends(get_current_user)):
    """Dependency to require master admin access"""
    if user_info.get("role") != "master":
        raise HTTPException(status_code=403, detail="Master admin access required")
    return user_info

def require_permission(permission: str):
    """Factory function to create permission-specific dependency"""
    async def permission_check(user_info = Depends(get_current_user)):
        if not security_manager.has_permission(user_info, permission):
            raise HTTPException(status_code=403, detail=f"Permission '{permission}' required")
        return user_info
    return permission_check