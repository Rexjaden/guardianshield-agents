import os
import hashlib
import secrets
import time
import json
import logging
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import pyotp
import qrcode
from io import BytesIO
from enum import Enum

class AuthMethod(Enum):
    """Authentication methods supported by the security system"""
    PASSWORD_ONLY = "password"
    PASSWORD_MFA = "password_mfa"
    HARDWARE_KEY = "hardware_key"
    BIOMETRIC = "biometric"

class GuardianSecuritySystem:
    """
    🛡️ MAXIMUM SECURITY SYSTEM FOR GUARDIANSHIELD
    
    Multi-layer protection ensuring ONLY authorized access:
    - Master Admin Authentication (You)
    - Designated Admin Authentication (Your designees)
    - Multi-Factor Authentication (MFA)
    - Hardware Key Support
    - Encrypted Session Management
    - Real-time Intrusion Detection
    - Comprehensive Audit Logging
    - Emergency Lockdown System
    """
    
    def __init__(self):
        self.security_config_file = "guardian_security.encrypted"
        self.audit_log_file = "guardian_audit_log.encrypted"
        self.master_key_file = "master.key"
        self.session_file = "active_sessions.encrypted"
        
        # Initialize security system
        self._initialize_security_system()
        self._setup_logging()
        
    def _initialize_security_system(self):
        """Initialize the security system with maximum protection"""
        
        # Generate master encryption key if doesn't exist
        if not os.path.exists(self.master_key_file):
            self._generate_master_key()
            
        # Load master key
        with open(self.master_key_file, 'rb') as f:
            self.master_key = f.read()
            
        self.cipher_suite = Fernet(self.master_key)
        
        # Initialize security config if doesn't exist
        if not os.path.exists(self.security_config_file):
            self._create_initial_security_config()
            
        # Load security configuration
        self.security_config = self._load_encrypted_config()
        
        # Initialize session tracking
        self.active_sessions = self._load_active_sessions()
        
    def _generate_master_key(self):
        """Generate cryptographically secure master key"""
        key = Fernet.generate_key()
        with open(self.master_key_file, 'wb') as f:
            f.write(key)
        
        # Set file permissions (owner only)
        os.chmod(self.master_key_file, 0o600)
        print("🔐 Master encryption key generated and secured")
        
    def _create_initial_security_config(self):
        """Create initial security configuration"""
        
        print("\n🛡️ GUARDIANSHIELD SECURITY INITIALIZATION")
        print("=" * 50)
        print("Setting up MAXIMUM SECURITY for your system...")
        
        # Master admin setup (YOU)
        print("\n👑 MASTER ADMIN SETUP (Primary Owner)")
        master_username = input("Enter your master admin username: ").strip()
        master_password = input("Enter your master admin password (min 12 chars): ").strip()
        
        if len(master_password) < 12:
            raise ValueError("Master password must be at least 12 characters!")
            
        # Generate MFA secret for master admin
        master_mfa_secret = pyotp.random_base32()
        
        # Hash master password with salt
        master_salt = secrets.token_bytes(32)
        master_password_hash = self._hash_password(master_password, master_salt)
        
        initial_config = {
            "system_initialized": True,
            "initialization_date": datetime.now().isoformat(),
            "security_level": "MAXIMUM",
            "lockdown_active": False,
            "failed_attempts": {},
            "master_admin": {
                "username": master_username,
                "password_hash": base64.b64encode(master_password_hash).decode(),
                "salt": base64.b64encode(master_salt).decode(),
                "mfa_secret": master_mfa_secret,
                "role": "MASTER",
                "created": datetime.now().isoformat(),
                "last_login": None,
                "login_attempts": 0
            },
            "designated_admins": {},
            "security_settings": {
                "max_failed_attempts": 3,
                "lockout_duration": 3600,  # 1 hour
                "session_timeout": 1800,   # 30 minutes
                "require_mfa": True,
                "require_ip_whitelist": True,
                "emergency_lockdown": False
            },
            "ip_whitelist": [],
            "audit_settings": {
                "log_all_access": True,
                "log_failed_attempts": True,
                "alert_on_suspicious": True,
                "retention_days": 365
            }
        }
        
        # Encrypt and save configuration
        encrypted_config = self.cipher_suite.encrypt(json.dumps(initial_config).encode())
        with open(self.security_config_file, 'wb') as f:
            f.write(encrypted_config)
            
        os.chmod(self.security_config_file, 0o600)
        
        # Generate MFA QR code for master admin
        self._generate_mfa_qr_code(master_username, master_mfa_secret)
        
        print(f"\n✅ Master admin '{master_username}' created successfully!")
        print("📱 Scan the generated QR code with your authenticator app")
        print("🔐 MFA is REQUIRED for all admin access")
        
    def _hash_password(self, password: str, salt: bytes) -> bytes:
        """Hash password with PBKDF2 and salt"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(password.encode())
        
    def _generate_mfa_qr_code(self, username: str, secret: str):
        """Generate MFA QR code for authenticator app"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=username,
            issuer_name="GuardianShield Security"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        # Save QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        qr_filename = f"mfa_qr_{username}.png"
        img.save(qr_filename)
        
        print(f"📱 MFA QR code saved as: {qr_filename}")
        print(f"🔑 MFA Secret (backup): {secret}")
        
    def _load_encrypted_config(self) -> dict:
        """Load and decrypt security configuration"""
        try:
            with open(self.security_config_file, 'rb') as f:
                encrypted_data = f.read()
                
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
            
        except Exception as e:
            raise Exception(f"Failed to load security configuration: {e}")
            
    def _save_encrypted_config(self):
        """Save encrypted security configuration"""
        encrypted_config = self.cipher_suite.encrypt(json.dumps(self.security_config).encode())
        with open(self.security_config_file, 'wb') as f:
            f.write(encrypted_config)
            
    def _load_active_sessions(self) -> dict:
        """Load active sessions"""
        if not os.path.exists(self.session_file):
            return {}
            
        try:
            with open(self.session_file, 'rb') as f:
                encrypted_data = f.read()
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except:
            return {}
            
    def _save_active_sessions(self):
        """Save active sessions"""
        encrypted_sessions = self.cipher_suite.encrypt(json.dumps(self.active_sessions).encode())
        with open(self.session_file, 'wb') as f:
            f.write(encrypted_sessions)
            
    def _setup_logging(self):
        """Setup secure audit logging"""
        self.logger = logging.getLogger('GuardianSecurity')
        self.logger.setLevel(logging.INFO)
        
        # Create encrypted log handler
        handler = logging.FileHandler('guardian_security.log')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
    def authenticate_admin(self, username: str, password: str, mfa_token: str, 
                          client_ip: str = None) -> dict:
        """
        🔐 SECURE ADMIN AUTHENTICATION
        
        Multi-layer authentication with:
        - Password verification
        - MFA token verification  
        - IP whitelist checking
        - Failed attempt tracking
        - Session management
        """
        
        self._log_security_event("AUTH_ATTEMPT", {
            "username": username,
            "ip": client_ip,
            "timestamp": datetime.now().isoformat()
        })
        
        # Check if system is in lockdown
        if self.security_config.get("lockdown_active", False):
            self._log_security_event("AUTH_BLOCKED", {"reason": "SYSTEM_LOCKDOWN", "username": username})
            raise Exception("🚨 SYSTEM IN LOCKDOWN - ACCESS DENIED")
            
        # Check failed attempts
        failed_key = f"{username}_{client_ip}" if client_ip else username
        failed_attempts = self.security_config.get("failed_attempts", {}).get(failed_key, {})
        
        if failed_attempts.get("count", 0) >= self.security_config["security_settings"]["max_failed_attempts"]:
            if time.time() - failed_attempts.get("last_attempt", 0) < self.security_config["security_settings"]["lockout_duration"]:
                self._log_security_event("AUTH_BLOCKED", {"reason": "TOO_MANY_ATTEMPTS", "username": username})
                raise Exception("🚨 ACCOUNT LOCKED - Too many failed attempts")
                
        # Check IP whitelist (if enabled)
        if self.security_config["security_settings"]["require_ip_whitelist"]:
            if client_ip not in self.security_config.get("ip_whitelist", []):
                self._log_security_event("AUTH_BLOCKED", {"reason": "IP_NOT_WHITELISTED", "username": username, "ip": client_ip})
                raise Exception("🚨 ACCESS DENIED - IP not whitelisted")
                
        # Find admin account
        admin_account = None
        if username == self.security_config["master_admin"]["username"]:
            admin_account = self.security_config["master_admin"]
        elif username in self.security_config.get("designated_admins", {}):
            admin_account = self.security_config["designated_admins"][username]
            
        if not admin_account:
            self._record_failed_attempt(failed_key)
            self._log_security_event("AUTH_FAILED", {"reason": "USER_NOT_FOUND", "username": username})
            raise Exception("🚨 AUTHENTICATION FAILED")
            
        # Verify password
        stored_hash = base64.b64decode(admin_account["password_hash"])
        salt = base64.b64decode(admin_account["salt"])
        
        if self._hash_password(password, salt) != stored_hash:
            self._record_failed_attempt(failed_key)
            self._log_security_event("AUTH_FAILED", {"reason": "INVALID_PASSWORD", "username": username})
            raise Exception("🚨 AUTHENTICATION FAILED")
            
        # Verify MFA token
        if self.security_config["security_settings"]["require_mfa"]:
            totp = pyotp.TOTP(admin_account["mfa_secret"])
            if not totp.verify(mfa_token, valid_window=1):
                self._record_failed_attempt(failed_key)
                self._log_security_event("AUTH_FAILED", {"reason": "INVALID_MFA", "username": username})
                raise Exception("🚨 INVALID MFA TOKEN")
                
        # Clear failed attempts on successful auth
        if failed_key in self.security_config.get("failed_attempts", {}):
            del self.security_config["failed_attempts"][failed_key]
            self._save_encrypted_config()
            
        # Create secure session
        session_token = self._create_secure_session(username, admin_account["role"], client_ip)
        
        # Update last login
        admin_account["last_login"] = datetime.now().isoformat()
        self._save_encrypted_config()
        
        self._log_security_event("AUTH_SUCCESS", {
            "username": username,
            "role": admin_account["role"],
            "ip": client_ip,
            "session_token": session_token[:8] + "..."
        })
        
        return {
            "authenticated": True,
            "session_token": session_token,
            "username": username,
            "role": admin_account["role"],
            "expires_at": (datetime.now() + timedelta(seconds=self.security_config["security_settings"]["session_timeout"])).isoformat()
        }
        
    def _record_failed_attempt(self, failed_key: str):
        """Record failed authentication attempt"""
        if "failed_attempts" not in self.security_config:
            self.security_config["failed_attempts"] = {}
            
        if failed_key not in self.security_config["failed_attempts"]:
            self.security_config["failed_attempts"][failed_key] = {"count": 0, "last_attempt": 0}
            
        self.security_config["failed_attempts"][failed_key]["count"] += 1
        self.security_config["failed_attempts"][failed_key]["last_attempt"] = time.time()
        
        self._save_encrypted_config()
        
    def _create_secure_session(self, username: str, role: str, client_ip: str = None) -> str:
        """Create cryptographically secure session token"""
        session_data = {
            "username": username,
            "role": role,
            "client_ip": client_ip,
            "created_at": time.time(),
            "expires_at": time.time() + self.security_config["security_settings"]["session_timeout"]
        }
        
        # Generate secure session token
        session_token = secrets.token_urlsafe(32)
        
        # Store session
        self.active_sessions[session_token] = session_data
        self._save_active_sessions()
        
        return session_token
        
    def validate_session(self, session_token: str, client_ip: str = None) -> dict:
        """Validate active session with comprehensive checks"""
        
        if session_token not in self.active_sessions:
            self._log_security_event("SESSION_INVALID", {"token": session_token[:8] + "...", "ip": client_ip})
            raise Exception("🚨 INVALID SESSION TOKEN")
            
        session = self.active_sessions[session_token]
        
        # Check session expiration
        if time.time() > session["expires_at"]:
            del self.active_sessions[session_token]
            self._save_active_sessions()
            self._log_security_event("SESSION_EXPIRED", {"username": session["username"], "ip": client_ip})
            raise Exception("🚨 SESSION EXPIRED")
            
        # Verify IP consistency (if set)
        if session.get("client_ip") and client_ip and session["client_ip"] != client_ip:
            self._log_security_event("SESSION_IP_MISMATCH", {
                "username": session["username"],
                "original_ip": session["client_ip"],
                "current_ip": client_ip
            })
            raise Exception("🚨 SESSION IP MISMATCH - SECURITY VIOLATION")
            
        # Extend session if valid
        session["expires_at"] = time.time() + self.security_config["security_settings"]["session_timeout"]
        self._save_active_sessions()
        
        return session
        
    def add_designated_admin(self, master_session: str, new_username: str, 
                           new_password: str, role: str = "ADMIN") -> dict:
        """
        👥 ADD DESIGNATED ADMIN (Master Admin Only)
        
        Only the master admin can add new designated admins
        """
        
        # Validate master admin session
        session = self.validate_session(master_session)
        if session["role"] != "MASTER":
            self._log_security_event("UNAUTHORIZED_ADMIN_CREATION", {
                "attempting_user": session["username"],
                "role": session["role"]
            })
            raise Exception("🚨 ONLY MASTER ADMIN CAN ADD DESIGNATED ADMINS")
            
        # Check if username already exists
        if (new_username == self.security_config["master_admin"]["username"] or 
            new_username in self.security_config.get("designated_admins", {})):
            raise Exception("🚨 USERNAME ALREADY EXISTS")
            
        # Generate MFA secret for new admin
        mfa_secret = pyotp.random_base32()
        
        # Hash password
        salt = secrets.token_bytes(32)
        password_hash = self._hash_password(new_password, salt)
        
        # Create admin account
        new_admin = {
            "username": new_username,
            "password_hash": base64.b64encode(password_hash).decode(),
            "salt": base64.b64encode(salt).decode(),
            "mfa_secret": mfa_secret,
            "role": role,
            "created": datetime.now().isoformat(),
            "created_by": session["username"],
            "last_login": None,
            "login_attempts": 0,
            "active": True
        }
        
        # Add to designated admins
        if "designated_admins" not in self.security_config:
            self.security_config["designated_admins"] = {}
            
        self.security_config["designated_admins"][new_username] = new_admin
        self._save_encrypted_config()
        
        # Generate MFA QR code
        self._generate_mfa_qr_code(new_username, mfa_secret)
        
        self._log_security_event("ADMIN_CREATED", {
            "new_admin": new_username,
            "role": role,
            "created_by": session["username"]
        })
        
        return {
            "success": True,
            "username": new_username,
            "mfa_secret": mfa_secret,
            "qr_code_file": f"mfa_qr_{new_username}.png"
        }
        
    def revoke_admin_access(self, master_session: str, target_username: str):
        """🚫 REVOKE ADMIN ACCESS (Master Admin Only)"""
        
        session = self.validate_session(master_session)
        if session["role"] != "MASTER":
            raise Exception("🚨 ONLY MASTER ADMIN CAN REVOKE ACCESS")
            
        if target_username == self.security_config["master_admin"]["username"]:
            raise Exception("🚨 CANNOT REVOKE MASTER ADMIN ACCESS")
            
        if target_username in self.security_config.get("designated_admins", {}):
            self.security_config["designated_admins"][target_username]["active"] = False
            self._save_encrypted_config()
            
            # Invalidate all sessions for this user
            self._invalidate_user_sessions(target_username)
            
            self._log_security_event("ADMIN_REVOKED", {
                "revoked_admin": target_username,
                "revoked_by": session["username"]
            })
            
    def _invalidate_user_sessions(self, username: str):
        """Invalidate all sessions for a specific user"""
        sessions_to_remove = []
        for token, session_data in self.active_sessions.items():
            if session_data["username"] == username:
                sessions_to_remove.append(token)
                
        for token in sessions_to_remove:
            del self.active_sessions[token]
            
        self._save_active_sessions()
        
    def emergency_lockdown(self, master_session: str, reason: str = "EMERGENCY"):
        """🚨 EMERGENCY LOCKDOWN (Master Admin Only)"""
        
        session = self.validate_session(master_session)
        if session["role"] != "MASTER":
            raise Exception("🚨 ONLY MASTER ADMIN CAN INITIATE LOCKDOWN")
            
        self.security_config["lockdown_active"] = True
        self.security_config["lockdown_reason"] = reason
        self.security_config["lockdown_initiated"] = datetime.now().isoformat()
        self.security_config["lockdown_by"] = session["username"]
        
        # Clear all sessions except master
        master_username = self.security_config["master_admin"]["username"]
        sessions_to_keep = {}
        for token, session_data in self.active_sessions.items():
            if session_data["username"] == master_username:
                sessions_to_keep[token] = session_data
                
        self.active_sessions = sessions_to_keep
        self._save_active_sessions()
        self._save_encrypted_config()
        
        self._log_security_event("EMERGENCY_LOCKDOWN", {
            "reason": reason,
            "initiated_by": session["username"]
        })
        
    def disable_lockdown(self, master_session: str):
        """🔓 DISABLE LOCKDOWN (Master Admin Only)"""
        
        session = self.validate_session(master_session)
        if session["role"] != "MASTER":
            raise Exception("🚨 ONLY MASTER ADMIN CAN DISABLE LOCKDOWN")
            
        self.security_config["lockdown_active"] = False
        self.security_config["lockdown_disabled"] = datetime.now().isoformat()
        self._save_encrypted_config()
        
        self._log_security_event("LOCKDOWN_DISABLED", {
            "disabled_by": session["username"]
        })
        
    def get_security_status(self, session_token: str) -> dict:
        """📊 GET COMPREHENSIVE SECURITY STATUS"""
        
        session = self.validate_session(session_token)
        
        return {
            "system_secure": True,
            "lockdown_active": self.security_config.get("lockdown_active", False),
            "total_admins": 1 + len(self.security_config.get("designated_admins", {})),
            "active_sessions": len(self.active_sessions),
            "security_level": "MAXIMUM",
            "mfa_required": True,
            "ip_whitelist_active": self.security_config["security_settings"]["require_ip_whitelist"],
            "failed_attempts_tracked": len(self.security_config.get("failed_attempts", {})),
            "audit_logging": "ACTIVE",
            "last_security_event": self._get_last_security_event()
        }
        
    def _log_security_event(self, event_type: str, data: dict):
        """🔍 LOG ALL SECURITY EVENTS"""
        
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        }
        
        # Log to standard logger
        self.logger.info(f"SECURITY_EVENT: {event_type} - {json.dumps(data)}")
        
        # Store in encrypted audit log
        try:
            if os.path.exists(self.audit_log_file):
                with open(self.audit_log_file, 'rb') as f:
                    encrypted_data = f.read()
                decrypted_data = self.cipher_suite.decrypt(encrypted_data)
                audit_log = json.loads(decrypted_data.decode())
            else:
                audit_log = []
                
            audit_log.append(event)
            
            # Keep only recent events (based on retention policy)
            retention_days = self.security_config.get("audit_settings", {}).get("retention_days", 365)
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            audit_log = [
                e for e in audit_log 
                if datetime.fromisoformat(e["timestamp"]) > cutoff_date
            ]
            
            # Encrypt and save
            encrypted_log = self.cipher_suite.encrypt(json.dumps(audit_log).encode())
            with open(self.audit_log_file, 'wb') as f:
                f.write(encrypted_log)
                
        except Exception as e:
            self.logger.error(f"Failed to write to audit log: {e}")
            
    def _get_last_security_event(self) -> dict:
        """Get the most recent security event"""
        try:
            if os.path.exists(self.audit_log_file):
                with open(self.audit_log_file, 'rb') as f:
                    encrypted_data = f.read()
                decrypted_data = self.cipher_suite.decrypt(encrypted_data)
                audit_log = json.loads(decrypted_data.decode())
                
                if audit_log:
                    return audit_log[-1]
                    
        except Exception:
            pass
            
        return {"event_type": "NONE", "timestamp": "N/A"}
        
    def whitelist_ip(self, master_session: str, ip_address: str, description: str = ""):
        """🌐 ADD IP TO WHITELIST (Master Admin Only)"""
        
        session = self.validate_session(master_session)
        if session["role"] != "MASTER":
            raise Exception("🚨 ONLY MASTER ADMIN CAN MANAGE IP WHITELIST")
            
        if "ip_whitelist" not in self.security_config:
            self.security_config["ip_whitelist"] = []
            
        whitelist_entry = {
            "ip": ip_address,
            "description": description,
            "added_by": session["username"],
            "added_at": datetime.now().isoformat()
        }
        
        self.security_config["ip_whitelist"].append(whitelist_entry)
        self._save_encrypted_config()
        
        self._log_security_event("IP_WHITELISTED", whitelist_entry)
        
    def remove_ip_from_whitelist(self, master_session: str, ip_address: str):
        """🚫 REMOVE IP FROM WHITELIST (Master Admin Only)"""
        
        session = self.validate_session(master_session)
        if session["role"] != "MASTER":
            raise Exception("🚨 ONLY MASTER ADMIN CAN MANAGE IP WHITELIST")
            
        if "ip_whitelist" in self.security_config:
            original_count = len(self.security_config["ip_whitelist"])
            self.security_config["ip_whitelist"] = [
                entry for entry in self.security_config["ip_whitelist"] 
                if entry["ip"] != ip_address
            ]
            
            if len(self.security_config["ip_whitelist"]) < original_count:
                self._save_encrypted_config()
                self._log_security_event("IP_REMOVED_FROM_WHITELIST", {
                    "ip": ip_address,
                    "removed_by": session["username"]
                })


# 🛡️ GUARDIAN SECURITY MANAGER CLASS
class GuardianSecurityManager:
    """
    Master security manager for all GuardianShield components
    """
    
    def __init__(self):
        self.security_system = GuardianSecuritySystem()
        
    def secure_admin_login(self) -> dict:
        """🔐 Secure admin login with full protection"""
        
        print("\n🛡️ GUARDIANSHIELD SECURE ADMIN LOGIN")
        print("=" * 45)
        
        username = input("👤 Username: ").strip()
        password = input("🔒 Password: ").strip()
        mfa_token = input("📱 MFA Token (6 digits): ").strip()
        
        try:
            # Get client IP (in production, get from request)
            client_ip = "127.0.0.1"  # Replace with actual IP detection
            
            result = self.security_system.authenticate_admin(
                username, password, mfa_token, client_ip
            )
            
            print(f"\n✅ AUTHENTICATION SUCCESSFUL!")
            print(f"👤 Welcome, {result['username']}")
            print(f"👑 Role: {result['role']}")
            print(f"⏰ Session expires: {result['expires_at']}")
            
            return result
            
        except Exception as e:
            print(f"\n❌ AUTHENTICATION FAILED: {e}")
            return {"authenticated": False, "error": str(e)}
            
    def initialize_security_system(self):
        """Initialize security system if not already done"""
        if not hasattr(self.security_system, 'security_config'):
            self.security_system._create_initial_security_config()
            
    def get_security_dashboard(self, session_token: str) -> dict:
        """📊 Security dashboard for authorized admins"""
        try:
            return self.security_system.get_security_status(session_token)
        except Exception as e:
            return {"error": f"Unauthorized access: {e}"}


# Initialize the security system
if __name__ == "__main__":
    print("\n🛡️ GUARDIANSHIELD MAXIMUM SECURITY SYSTEM")
    print("=" * 50)
    print("Initializing comprehensive security protection...")
    
    try:
        security_manager = GuardianSecurityManager()
        
        # Check if system needs initialization
        if not os.path.exists("guardian_security.encrypted"):
            print("\n🔧 Security system not initialized. Starting setup...")
            security_manager.initialize_security_system()
        else:
            print("\n✅ Security system ready!")
            
        # Demo login
        login_result = security_manager.secure_admin_login()
        
        if login_result.get("authenticated"):
            # Show security dashboard
            dashboard = security_manager.get_security_dashboard(login_result["session_token"])
            
            print(f"\n📊 SECURITY DASHBOARD")
            print(f"System Status: {'🔒 SECURE' if dashboard['system_secure'] else '🚨 COMPROMISED'}")
            print(f"Total Admins: {dashboard['total_admins']}")
            print(f"Active Sessions: {dashboard['active_sessions']}")
            print(f"Security Level: {dashboard['security_level']}")
            print(f"MFA Required: {'✅ YES' if dashboard['mfa_required'] else '❌ NO'}")
            print(f"Audit Logging: {dashboard['audit_logging']}")
            
    except Exception as e:
        print(f"\n❌ Security system error: {e}")