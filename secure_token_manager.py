#!/usr/bin/env python3
"""
GuardianShield Token Security Management
Generate, rotate, and manage secure tokens to protect source code access
"""

import secrets
import os
import json
import hashlib
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from typing import Dict, List, Optional

class SecureTokenManager:
    def __init__(self):
        self.config_file = "token_security_config.json"
        self.token_file = "encrypted_tokens.json"
        self.audit_log = "token_access_log.jsonl"
        self.master_key_file = ".guardian_token_master_key"
        
        self._ensure_master_key()
        self.cipher = Fernet(self._load_master_key())
        
    def _ensure_master_key(self):
        """Ensure master encryption key exists"""
        if not os.path.exists(self.master_key_file):
            master_key = Fernet.generate_key()
            with open(self.master_key_file, 'wb') as f:
                f.write(master_key)
            os.chmod(self.master_key_file, 0o600)  # Read-only for owner
            print(f"🔑 Generated master encryption key: {self.master_key_file}")
    
    def _load_master_key(self) -> bytes:
        """Load master encryption key"""
        with open(self.master_key_file, 'rb') as f:
            return f.read()
    
    def generate_secure_api_token(self, permissions: List[str] = None, expires_days: int = 30) -> Dict:
        """Generate a secure API token for source code access"""
        if permissions is None:
            permissions = ["read", "api"]
        
        # Generate high-entropy token
        token_bytes = secrets.token_bytes(32)
        token_string = secrets.token_urlsafe(64)  # URL-safe base64
        token_hash = hashlib.sha256(token_string.encode()).hexdigest()
        
        # Create token metadata
        token_data = {
            "token_id": secrets.token_hex(16),
            "token_hash": token_hash,
            "permissions": permissions,
            "created": datetime.utcnow().isoformat(),
            "expires": (datetime.utcnow() + timedelta(days=expires_days)).isoformat(),
            "access_count": 0,
            "last_access": None,
            "source_ip": None,
            "status": "active"
        }
        
        # Encrypt token data
        encrypted_data = self.cipher.encrypt(json.dumps(token_data).encode())
        
        # Store encrypted token
        self._store_encrypted_token(token_data["token_id"], encrypted_data)
        
        # Log token creation
        self._audit_log("token_created", {
            "token_id": token_data["token_id"],
            "permissions": permissions,
            "expires": token_data["expires"]
        })
        
        return {
            "token": token_string,
            "token_id": token_data["token_id"],
            "permissions": permissions,
            "expires": token_data["expires"],
            "warning": "SAVE THIS TOKEN - It cannot be retrieved again!"
        }
    
    def _store_encrypted_token(self, token_id: str, encrypted_data: bytes):
        """Store encrypted token data"""
        tokens = {}
        if os.path.exists(self.token_file):
            with open(self.token_file, 'r') as f:
                tokens = json.load(f)
        
        tokens[token_id] = encrypted_data.decode('utf-8')  # Store as base64 string
        
        with open(self.token_file, 'w') as f:
            json.dump(tokens, f, indent=2)
        
        os.chmod(self.token_file, 0o600)  # Secure file permissions
    
    def validate_token(self, token: str, required_permissions: List[str] = None, client_ip: str = None) -> Dict:
        """Validate a token and check permissions"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Load and check all tokens
        if not os.path.exists(self.token_file):
            return {"valid": False, "error": "No tokens configured"}
        
        with open(self.token_file, 'r') as f:
            encrypted_tokens = json.load(f)
        
        for token_id, encrypted_data in encrypted_tokens.items():
            try:
                # Decrypt token data
                decrypted_data = self.cipher.decrypt(encrypted_data.encode())
                token_data = json.loads(decrypted_data.decode())
                
                if token_data["token_hash"] == token_hash:
                    # Check if token is expired
                    expires = datetime.fromisoformat(token_data["expires"])
                    if datetime.utcnow() > expires:
                        self._audit_log("token_access_expired", {
                            "token_id": token_id,
                            "client_ip": client_ip,
                            "expired_on": token_data["expires"]
                        })
                        return {"valid": False, "error": "Token expired"}
                    
                    # Check if token is active
                    if token_data["status"] != "active":
                        self._audit_log("token_access_inactive", {
                            "token_id": token_id,
                            "client_ip": client_ip,
                            "status": token_data["status"]
                        })
                        return {"valid": False, "error": "Token inactive"}
                    
                    # Check permissions
                    if required_permissions:
                        if not all(perm in token_data["permissions"] for perm in required_permissions):
                            self._audit_log("token_access_insufficient_permissions", {
                                "token_id": token_id,
                                "client_ip": client_ip,
                                "required": required_permissions,
                                "granted": token_data["permissions"]
                            })
                            return {"valid": False, "error": "Insufficient permissions"}
                    
                    # Update access tracking
                    token_data["access_count"] += 1
                    token_data["last_access"] = datetime.utcnow().isoformat()
                    token_data["source_ip"] = client_ip
                    
                    # Re-encrypt and store updated data
                    updated_encrypted = self.cipher.encrypt(json.dumps(token_data).encode())
                    encrypted_tokens[token_id] = updated_encrypted.decode('utf-8')
                    
                    with open(self.token_file, 'w') as f:
                        json.dump(encrypted_tokens, f, indent=2)
                    
                    # Log successful access
                    self._audit_log("token_access_success", {
                        "token_id": token_id,
                        "client_ip": client_ip,
                        "permissions": token_data["permissions"]
                    })
                    
                    return {
                        "valid": True,
                        "token_id": token_id,
                        "permissions": token_data["permissions"],
                        "access_count": token_data["access_count"]
                    }
            
            except Exception as e:
                continue
        
        # Token not found
        self._audit_log("token_access_invalid", {
            "token_hash": token_hash[:16] + "...",
            "client_ip": client_ip,
            "error": "Token not found"
        })
        
        return {"valid": False, "error": "Invalid token"}
    
    def revoke_token(self, token_id: str) -> Dict:
        """Revoke a specific token"""
        if not os.path.exists(self.token_file):
            return {"success": False, "error": "No tokens found"}
        
        with open(self.token_file, 'r') as f:
            encrypted_tokens = json.load(f)
        
        if token_id not in encrypted_tokens:
            return {"success": False, "error": "Token not found"}
        
        try:
            # Decrypt and mark as revoked
            decrypted_data = self.cipher.decrypt(encrypted_tokens[token_id].encode())
            token_data = json.loads(decrypted_data.decode())
            
            token_data["status"] = "revoked"
            token_data["revoked_at"] = datetime.utcnow().isoformat()
            
            # Re-encrypt and store
            updated_encrypted = self.cipher.encrypt(json.dumps(token_data).encode())
            encrypted_tokens[token_id] = updated_encrypted.decode('utf-8')
            
            with open(self.token_file, 'w') as f:
                json.dump(encrypted_tokens, f, indent=2)
            
            self._audit_log("token_revoked", {"token_id": token_id})
            
            return {"success": True, "message": f"Token {token_id} revoked"}
        
        except Exception as e:
            return {"success": False, "error": f"Failed to revoke token: {e}"}
    
    def rotate_all_tokens(self) -> Dict:
        """Emergency: Revoke all active tokens"""
        if not os.path.exists(self.token_file):
            return {"revoked_count": 0}
        
        with open(self.token_file, 'r') as f:
            encrypted_tokens = json.load(f)
        
        revoked_count = 0
        
        for token_id, encrypted_data in encrypted_tokens.items():
            try:
                decrypted_data = self.cipher.decrypt(encrypted_data.encode())
                token_data = json.loads(decrypted_data.decode())
                
                if token_data["status"] == "active":
                    token_data["status"] = "revoked"
                    token_data["revoked_at"] = datetime.utcnow().isoformat()
                    token_data["revocation_reason"] = "emergency_rotation"
                    
                    updated_encrypted = self.cipher.encrypt(json.dumps(token_data).encode())
                    encrypted_tokens[token_id] = updated_encrypted.decode('utf-8')
                    
                    revoked_count += 1
            
            except Exception:
                continue
        
        with open(self.token_file, 'w') as f:
            json.dump(encrypted_tokens, f, indent=2)
        
        self._audit_log("emergency_token_rotation", {"revoked_count": revoked_count})
        
        return {"revoked_count": revoked_count}
    
    def list_active_tokens(self) -> List[Dict]:
        """List all active tokens (without sensitive data)"""
        if not os.path.exists(self.token_file):
            return []
        
        active_tokens = []
        
        with open(self.token_file, 'r') as f:
            encrypted_tokens = json.load(f)
        
        for token_id, encrypted_data in encrypted_tokens.items():
            try:
                decrypted_data = self.cipher.decrypt(encrypted_data.encode())
                token_data = json.loads(decrypted_data.decode())
                
                if token_data["status"] == "active":
                    active_tokens.append({
                        "token_id": token_id,
                        "permissions": token_data["permissions"],
                        "created": token_data["created"],
                        "expires": token_data["expires"],
                        "access_count": token_data["access_count"],
                        "last_access": token_data.get("last_access", "Never")
                    })
            
            except Exception:
                continue
        
        return active_tokens
    
    def _audit_log(self, event_type: str, details: Dict):
        """Log security events"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "details": details
        }
        
        with open(self.audit_log, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_security_report(self) -> Dict:
        """Generate security report"""
        active_tokens = self.list_active_tokens()
        
        # Analyze audit log
        audit_stats = {"total_events": 0, "access_attempts": 0, "failed_attempts": 0}
        
        if os.path.exists(self.audit_log):
            with open(self.audit_log, 'r') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        audit_stats["total_events"] += 1
                        
                        if event["event_type"].startswith("token_access"):
                            audit_stats["access_attempts"] += 1
                            
                            if "invalid" in event["event_type"] or "expired" in event["event_type"]:
                                audit_stats["failed_attempts"] += 1
                    
                    except:
                        continue
        
        return {
            "active_tokens": len(active_tokens),
            "total_events": audit_stats["total_events"],
            "access_attempts": audit_stats["access_attempts"],
            "failed_attempts": audit_stats["failed_attempts"],
            "security_level": "HIGH" if len(active_tokens) < 5 else "MEDIUM",
            "last_rotation": "Manual rotation recommended",
            "recommendations": [
                "Regularly rotate tokens (monthly)",
                "Monitor failed access attempts",
                "Use IP restrictions for production tokens",
                "Enable MFA for token generation",
                "Review token permissions periodically"
            ]
        }

def main():
    """Main function for command-line usage"""
    import sys
    
    manager = SecureTokenManager()
    
    if len(sys.argv) < 2:
        print("🔐 GuardianShield Token Security Manager")
        print("Usage: python secure_token_manager.py <command>")
        print("\nCommands:")
        print("  generate [permissions] - Generate new API token")
        print("  list                  - List active tokens")
        print("  revoke <token_id>    - Revoke specific token")
        print("  rotate               - Emergency: revoke all tokens")
        print("  report               - Security report")
        print("  test <token>         - Test token validation")
        return
    
    command = sys.argv[1]
    
    if command == "generate":
        permissions = sys.argv[2].split(',') if len(sys.argv) > 2 else ['read', 'api']
        result = manager.generate_secure_api_token(permissions)
        
        print("🎫 Generated Secure API Token")
        print(f"Token: {result['token']}")
        print(f"Token ID: {result['token_id']}")
        print(f"Permissions: {', '.join(result['permissions'])}")
        print(f"Expires: {result['expires']}")
        print(f"\n⚠️ {result['warning']}")
    
    elif command == "list":
        tokens = manager.list_active_tokens()
        print(f"🎫 Active Tokens ({len(tokens)}):")
        
        if not tokens:
            print("  No active tokens found")
        else:
            for token in tokens:
                print(f"\n  Token ID: {token['token_id']}")
                print(f"  Permissions: {', '.join(token['permissions'])}")
                print(f"  Created: {token['created'][:19]}")
                print(f"  Expires: {token['expires'][:19]}")
                print(f"  Access Count: {token['access_count']}")
                print(f"  Last Access: {token['last_access'][:19] if token['last_access'] != 'Never' else 'Never'}")
    
    elif command == "revoke":
        if len(sys.argv) < 3:
            print("❌ Token ID required")
            return
        
        token_id = sys.argv[2]
        result = manager.revoke_token(token_id)
        
        if result["success"]:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['error']}")
    
    elif command == "rotate":
        print("⚠️ This will revoke ALL active tokens!")
        confirm = input("Type 'CONFIRM' to proceed: ")
        
        if confirm == "CONFIRM":
            result = manager.rotate_all_tokens()
            print(f"🔄 Revoked {result['revoked_count']} tokens")
            print("💡 Generate new tokens for continued access")
        else:
            print("Cancelled.")
    
    elif command == "report":
        report = manager.get_security_report()
        print("📊 Token Security Report")
        print(f"Active Tokens: {report['active_tokens']}")
        print(f"Total Events: {report['total_events']}")
        print(f"Access Attempts: {report['access_attempts']}")
        print(f"Failed Attempts: {report['failed_attempts']}")
        print(f"Security Level: {report['security_level']}")
        
        print("\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
    
    elif command == "test":
        if len(sys.argv) < 3:
            print("❌ Token required")
            return
        
        token = sys.argv[2]
        result = manager.validate_token(token, client_ip="127.0.0.1")
        
        if result["valid"]:
            print(f"✅ Token Valid")
            print(f"Token ID: {result['token_id']}")
            print(f"Permissions: {', '.join(result['permissions'])}")
            print(f"Access Count: {result['access_count']}")
        else:
            print(f"❌ Token Invalid: {result['error']}")
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()