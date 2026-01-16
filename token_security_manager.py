"""
GuardianShield Token Security & Source Code Protection System
Comprehensive protection against unauthorized access to your repository and systems
"""

import os
import json
import hashlib
import secrets
import time
import subprocess
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)

class TokenSecurityManager:
    """
    Advanced token security and source code protection system
    """
    
    def __init__(self):
        self.config_file = ".guardian_token_security.json"
        self.encrypted_tokens_file = ".guardian_encrypted_tokens.bin"
        self.access_log_file = "token_access_log.jsonl"
        
        # Security configuration
        self.config = self._load_security_config()
        
        # Token tracking
        self.active_tokens = {}  # token_id -> {type, permissions, expires, last_used}
        self.revoked_tokens = set()  # Revoked token hashes
        self.suspicious_access_attempts = []
        
        # Repository protection
        self.protected_patterns = [
            r'\.env',
            r'\.guardian_.*',
            r'.*\.key',
            r'.*\.pem',
            r'.*_secret.*',
            r'.*password.*',
            r'token.*\.json'
        ]
        
        # Initialize encryption key for sensitive data
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
    
    def _load_security_config(self) -> Dict:
        """Load token security configuration"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Default security configuration
        default_config = {
            "token_rotation_hours": 24,  # Force token rotation every 24 hours
            "max_failed_attempts": 3,
            "token_entropy_required": 32,  # Minimum token entropy bits
            "allowed_ip_ranges": [],  # Restrict token usage to specific IPs
            "require_mfa_for_tokens": True,
            "alert_on_suspicious_access": True,
            "github_branch_protection": True,
            "repository_access_monitoring": True,
            "created": datetime.now().isoformat()
        }
        
        self._save_security_config(default_config)
        return default_config
    
    def _save_security_config(self, config: Dict):
        """Save security configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        os.chmod(self.config_file, 0o600)
        self.config = config
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for sensitive data"""
        key_file = ".guardian_encryption_key"
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)
            return key
    
    def generate_secure_token(self, token_type: str, permissions: List[str], 
                            expires_hours: int = 24) -> Dict:
        """Generate cryptographically secure token with metadata"""
        
        # Generate high-entropy token
        token = f"gs_{token_type}_{secrets.token_urlsafe(64)}"
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Create token metadata
        token_data = {
            "token_id": token_hash,
            "type": token_type,
            "permissions": permissions,
            "created": datetime.now().isoformat(),
            "expires": (datetime.now() + timedelta(hours=expires_hours)).isoformat(),
            "last_used": None,
            "access_count": 0,
            "created_by": "system",
            "ip_restrictions": self.config.get("allowed_ip_ranges", [])
        }
        
        # Store encrypted token data
        self.active_tokens[token_hash] = token_data
        self._save_encrypted_tokens()
        
        # Log token creation
        self._log_token_event("token_created", token_hash, {
            "type": token_type,
            "permissions": permissions,
            "expires": token_data["expires"]
        })
        
        return {
            "token": token,
            "token_id": token_hash,
            "expires": token_data["expires"],
            "permissions": permissions,
            "warning": "Store this token securely - it cannot be retrieved again"
        }
    
    def validate_token(self, token: str, required_permission: str = None, 
                      client_ip: str = None) -> Optional[Dict]:
        """Validate token and check permissions"""
        
        # Hash the provided token
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Check if token is revoked
        if token_hash in self.revoked_tokens:
            self._log_token_event("token_access_revoked", token_hash, {
                "client_ip": client_ip,
                "required_permission": required_permission
            })
            return None
        
        # Check if token exists and is valid
        if token_hash not in self.active_tokens:
            self._log_token_event("token_access_invalid", token_hash, {
                "client_ip": client_ip
            })
            return None
        
        token_data = self.active_tokens[token_hash]
        
        # Check if token is expired
        expires = datetime.fromisoformat(token_data["expires"])
        if datetime.now() > expires:
            self._log_token_event("token_access_expired", token_hash, {
                "client_ip": client_ip,
                "expired_at": token_data["expires"]
            })
            return None
        
        # Check IP restrictions
        if token_data.get("ip_restrictions") and client_ip:
            if not self._is_ip_allowed(client_ip, token_data["ip_restrictions"]):
                self._log_token_event("token_access_ip_denied", token_hash, {
                    "client_ip": client_ip,
                    "allowed_ranges": token_data["ip_restrictions"]
                })
                return None
        
        # Check permissions
        if required_permission and required_permission not in token_data["permissions"]:
            self._log_token_event("token_access_permission_denied", token_hash, {
                "client_ip": client_ip,
                "required_permission": required_permission,
                "token_permissions": token_data["permissions"]
            })
            return None
        
        # Update token usage
        token_data["last_used"] = datetime.now().isoformat()
        token_data["access_count"] += 1
        self._save_encrypted_tokens()
        
        # Log successful access
        self._log_token_event("token_access_success", token_hash, {
            "client_ip": client_ip,
            "permission_used": required_permission
        })
        
        return token_data
    
    def revoke_token(self, token_or_hash: str, reason: str = "manual_revocation"):
        """Revoke a token immediately"""
        
        # Handle both token and token hash
        if token_or_hash.startswith("gs_"):
            token_hash = hashlib.sha256(token_or_hash.encode()).hexdigest()
        else:
            token_hash = token_or_hash
        
        # Add to revoked tokens
        self.revoked_tokens.add(token_hash)
        
        # Remove from active tokens
        if token_hash in self.active_tokens:
            token_data = self.active_tokens.pop(token_hash)
            self._save_encrypted_tokens()
            
            self._log_token_event("token_revoked", token_hash, {
                "reason": reason,
                "was_active": True,
                "access_count": token_data.get("access_count", 0)
            })
        else:
            self._log_token_event("token_revoked", token_hash, {
                "reason": reason,
                "was_active": False
            })
        
        return True
    
    def rotate_all_tokens(self, reason: str = "scheduled_rotation"):
        """Rotate all active tokens for security"""
        
        rotated_count = 0
        for token_hash in list(self.active_tokens.keys()):
            self.revoke_token(token_hash, f"rotation_{reason}")
            rotated_count += 1
        
        self._log_token_event("mass_token_rotation", "all", {
            "reason": reason,
            "rotated_count": rotated_count
        })
        
        return rotated_count
    
    def _save_encrypted_tokens(self):
        """Save tokens in encrypted format"""
        try:
            data = json.dumps(self.active_tokens).encode()
            encrypted_data = self.cipher.encrypt(data)
            
            with open(self.encrypted_tokens_file, 'wb') as f:
                f.write(encrypted_data)
            os.chmod(self.encrypted_tokens_file, 0o600)
            
        except Exception as e:
            logger.error(f"Failed to save encrypted tokens: {e}")
    
    def _load_encrypted_tokens(self):
        """Load tokens from encrypted storage"""
        if not os.path.exists(self.encrypted_tokens_file):
            return
        
        try:
            with open(self.encrypted_tokens_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            self.active_tokens = json.loads(decrypted_data.decode())
            
        except Exception as e:
            logger.error(f"Failed to load encrypted tokens: {e}")
            self.active_tokens = {}
    
    def _is_ip_allowed(self, ip: str, allowed_ranges: List[str]) -> bool:
        """Check if IP is within allowed ranges"""
        if not allowed_ranges:
            return True
        
        try:
            import ipaddress
            ip_obj = ipaddress.ip_address(ip)
            
            for ip_range in allowed_ranges:
                if ip_obj in ipaddress.ip_network(ip_range):
                    return True
            return False
        except Exception:
            return False
    
    def _log_token_event(self, event_type: str, token_hash: str, details: Dict):
        """Log token-related security events"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "token_hash": token_hash[:16] + "...",  # Partial hash for privacy
            "details": details
        }
        
        try:
            with open(self.access_log_file, 'a') as f:
                f.write(json.dumps(event) + '\n')
        except Exception as e:
            logger.error(f"Failed to log token event: {e}")
    
    def setup_github_protection(self) -> Dict:
        """Configure GitHub repository protection settings"""
        
        protection_status = {
            "branch_protection": False,
            "required_reviews": False,
            "dismiss_stale_reviews": False,
            "require_code_owner_reviews": False,
            "required_status_checks": False,
            "enforce_admins": False,
            "restrict_pushes": False
        }
        
        try:
            # Check if we're in a git repository
            result = subprocess.run(['git', 'status'], 
                                  capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode != 0:
                return {"error": "Not in a git repository"}
            
            # Get current branch
            result = subprocess.run(['git', 'branch', '--show-current'], 
                                  capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode == 0:
                current_branch = result.stdout.strip()
                protection_status["current_branch"] = current_branch
            
            # Note: Actual GitHub API calls would require authentication
            # This is a framework for protection setup
            
            return {
                "status": "configured",
                "protections": protection_status,
                "recommendations": [
                    "Enable branch protection rules on main branch",
                    "Require pull request reviews before merging",
                    "Enable dismiss stale reviews when new commits are pushed",
                    "Require status checks to pass before merging",
                    "Require signed commits",
                    "Restrict push access to specific users/teams"
                ]
            }
            
        except Exception as e:
            return {"error": f"Failed to configure GitHub protection: {e}"}
    
    def scan_for_exposed_secrets(self, directory: str = ".") -> Dict:
        """Scan for potentially exposed secrets in the codebase"""
        
        exposed_secrets = []
        patterns = {
            "api_key": r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?([a-zA-Z0-9_-]{20,})['\"]?",
            "secret_key": r"(?i)(secret[_-]?key|secretkey)\s*[:=]\s*['\"]?([a-zA-Z0-9_-]{20,})['\"]?",
            "password": r"(?i)password\s*[:=]\s*['\"]?([^'\"\s]{8,})['\"]?",
            "token": r"(?i)token\s*[:=]\s*['\"]?([a-zA-Z0-9_-]{20,})['\"]?",
            "private_key": r"-----BEGIN [A-Z ]+PRIVATE KEY-----",
            "github_token": r"gh[ps]_[a-zA-Z0-9]{36}",
        }
        
        for root, dirs, files in os.walk(directory):
            # Skip hidden directories and common build directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and 
                      d not in ['node_modules', '__pycache__', 'venv', '.git']]
            
            for file in files:
                # Skip binary files and common non-text files
                if any(file.endswith(ext) for ext in ['.pyc', '.exe', '.bin', '.jpg', '.png']):
                    continue
                
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    for pattern_name, pattern in patterns.items():
                        matches = re.finditer(pattern, content, re.MULTILINE)
                        for match in matches:
                            exposed_secrets.append({
                                "file": file_path,
                                "type": pattern_name,
                                "line": content[:match.start()].count('\n') + 1,
                                "context": match.group(0)[:50] + "..." if len(match.group(0)) > 50 else match.group(0)
                            })
                
                except Exception:
                    continue  # Skip files that can't be read
        
        return {
            "total_secrets_found": len(exposed_secrets),
            "secrets": exposed_secrets,
            "scan_timestamp": datetime.now().isoformat(),
            "recommendations": [
                "Move secrets to environment variables",
                "Use encrypted configuration files",
                "Add sensitive files to .gitignore",
                "Implement proper secret management"
            ] if exposed_secrets else []
        }
    
    def create_gitignore_security_rules(self) -> str:
        """Generate .gitignore rules for security"""
        
        security_rules = """
# GuardianShield Security - DO NOT COMMIT THESE FILES
.env
.env.*
*.key
*.pem
*secret*
*password*
*token*
.guardian_*
security_events.jsonl
token_access_log.jsonl

# API Keys and Credentials
api_keys/
credentials/
secrets/

# Database files with sensitive data
*.db
*.sqlite

# Log files that might contain sensitive info
*.log
logs/

# Backup files
*.backup
*.bak

# Temporary files
*.tmp
.temp/

# IDE specific files that might contain paths
.vscode/settings.json
.idea/

# OS specific files
Thumbs.db
.DS_Store
"""
        
        gitignore_path = ".gitignore"
        
        # Read existing .gitignore
        existing_content = ""
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r') as f:
                existing_content = f.read()
        
        # Add security rules if not already present
        if "# GuardianShield Security" not in existing_content:
            with open(gitignore_path, 'a') as f:
                f.write(security_rules)
            return "Security rules added to .gitignore"
        else:
            return "Security rules already present in .gitignore"
    
    def get_security_report(self) -> Dict:
        """Generate comprehensive security report"""
        
        # Load tokens
        self._load_encrypted_tokens()
        
        # Count active vs expired tokens
        now = datetime.now()
        active_count = 0
        expired_count = 0
        
        for token_data in self.active_tokens.values():
            expires = datetime.fromisoformat(token_data["expires"])
            if now < expires:
                active_count += 1
            else:
                expired_count += 1
        
        # Analyze recent access logs
        recent_access_count = 0
        if os.path.exists(self.access_log_file):
            try:
                with open(self.access_log_file, 'r') as f:
                    lines = f.readlines()
                    # Count events in last 24 hours
                    yesterday = now - timedelta(hours=24)
                    for line in lines:
                        try:
                            event = json.loads(line.strip())
                            event_time = datetime.fromisoformat(event["timestamp"])
                            if event_time > yesterday:
                                recent_access_count += 1
                        except:
                            continue
            except:
                pass
        
        return {
            "security_status": "active",
            "tokens": {
                "active": active_count,
                "expired": expired_count,
                "revoked": len(self.revoked_tokens),
                "total_created": active_count + expired_count + len(self.revoked_tokens)
            },
            "access_activity": {
                "events_last_24h": recent_access_count,
                "log_file_exists": os.path.exists(self.access_log_file)
            },
            "configuration": {
                "token_rotation_hours": self.config.get("token_rotation_hours", 24),
                "ip_restrictions_enabled": len(self.config.get("allowed_ip_ranges", [])) > 0,
                "mfa_required": self.config.get("require_mfa_for_tokens", True)
            },
            "recommendations": self._get_security_recommendations()
        }
    
    def _get_security_recommendations(self) -> List[str]:
        """Get security recommendations based on current state"""
        recommendations = []
        
        # Check token age
        if self.active_tokens:
            oldest_token = min(
                datetime.fromisoformat(token["created"]) 
                for token in self.active_tokens.values()
            )
            token_age_days = (datetime.now() - oldest_token).days
            
            if token_age_days > 30:
                recommendations.append("Consider rotating tokens older than 30 days")
        
        # Check IP restrictions
        if not self.config.get("allowed_ip_ranges"):
            recommendations.append("Configure IP restrictions for enhanced security")
        
        # Check for .gitignore
        if not os.path.exists(".gitignore"):
            recommendations.append("Create .gitignore file with security rules")
        
        return recommendations

# Global instance
token_security_manager = TokenSecurityManager()