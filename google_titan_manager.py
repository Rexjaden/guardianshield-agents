"""
GuardianShield Google Titan Security Key Integration (Simple Implementation)
Direct hardware integration for K51T Titan Security Key
"""

import os
import json
import hashlib
import secrets
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Optional

class GoogleTitanKeyManager:
    """
    Simple Google Titan Security Key Manager
    Uses Windows APIs for hardware security key integration
    """
    
    def __init__(self):
        self.settings_file = ".guardian_titan_key_settings.json"
        self.registered_keys_file = ".guardian_registered_keys.json"
        self.settings = self._load_settings()
        self.registered_keys = self._load_registered_keys()
    
    def _load_settings(self) -> Dict:
        """Load security key settings"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        default_settings = {
            "enabled": False,
            "required_for_admin": False,
            "created": datetime.now().isoformat()
        }
        self._save_settings(default_settings)
        return default_settings
    
    def _save_settings(self, settings: Dict):
        """Save settings to file"""
        with open(self.settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        os.chmod(self.settings_file, 0o600)
        self.settings = settings
    
    def _load_registered_keys(self) -> Dict:
        """Load registered keys"""
        if os.path.exists(self.registered_keys_file):
            try:
                with open(self.registered_keys_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"keys": []}
    
    def _save_registered_keys(self, keys_data: Dict):
        """Save registered keys"""
        with open(self.registered_keys_file, 'w') as f:
            json.dump(keys_data, f, indent=2)
        os.chmod(self.registered_keys_file, 0o600)
        self.registered_keys = keys_data
    
    def detect_google_titan_key(self) -> Dict:
        """Detect Google Titan Security Key using PowerShell"""
        try:
            cmd = [
                'powershell', '-Command',
                "Get-PnpDevice | Where-Object {$_.InstanceId -like '*VID_18D1*'} | Select-Object FriendlyName, Status, Present, InstanceId | ConvertTo-Json"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                try:
                    devices = json.loads(result.stdout)
                    if not isinstance(devices, list):
                        devices = [devices]
                    
                    # Filter for FIDO devices
                    titan_keys = [
                        device for device in devices 
                        if 'fido' in device.get('FriendlyName', '').lower() and 
                           device.get('Present') is True and 
                           device.get('Status') == 'OK'
                    ]
                    
                    return {
                        "detected": len(titan_keys) > 0,
                        "count": len(titan_keys),
                        "devices": titan_keys
                    }
                except json.JSONDecodeError:
                    pass
                    
        except Exception:
            pass
        
        return {"detected": False, "count": 0, "devices": []}
    
    def register_titan_key(self, admin_username: str = "master_admin") -> Dict:
        """Register the detected Google Titan key"""
        detection = self.detect_google_titan_key()
        
        if not detection["detected"]:
            raise ValueError("No Google Titan Security Key detected. Please insert your key.")
        
        # Create a registration entry
        key_id = secrets.token_urlsafe(32)
        registration_data = {
            "key_id": key_id,
            "username": admin_username,
            "registered_at": datetime.now().isoformat(),
            "device_info": detection["devices"][0] if detection["devices"] else {},
            "nickname": f"Google Titan Key - {datetime.now().strftime('%Y-%m-%d')}",
            "last_used": None
        }
        
        # Add to registered keys
        if key_id not in [key["key_id"] for key in self.registered_keys["keys"]]:
            self.registered_keys["keys"].append(registration_data)
            self._save_registered_keys(self.registered_keys)
        
        return {
            "success": True,
            "key_id": key_id,
            "message": "Google Titan Security Key registered successfully",
            "device_count": detection["count"]
        }
    
    def verify_titan_key_present(self) -> bool:
        """Verify that a registered Titan key is currently present"""
        if not self.registered_keys["keys"]:
            return False
            
        detection = self.detect_google_titan_key()
        return detection["detected"]
    
    def authenticate_with_titan_key(self, username: str = "master_admin") -> Dict:
        """Simulate authentication with Titan key (hardware presence check)"""
        if not self.verify_titan_key_present():
            raise ValueError("Google Titan Security Key not detected. Please insert your key.")
        
        # Find registered key for user
        user_keys = [
            key for key in self.registered_keys["keys"] 
            if key["username"] == username
        ]
        
        if not user_keys:
            raise ValueError("No registered security key found for user")
        
        # Update last used timestamp
        for key in user_keys:
            key["last_used"] = datetime.now().isoformat()
        self._save_registered_keys(self.registered_keys)
        
        # Generate authentication token/session
        auth_token = secrets.token_urlsafe(32)
        
        return {
            "success": True,
            "auth_token": auth_token,
            "message": "Google Titan Security Key authentication successful",
            "key_info": user_keys[0]
        }
    
    def enable_titan_key_requirement(self):
        """Enable Titan key requirement for admin access"""
        if not self.registered_keys["keys"]:
            raise ValueError("No security keys registered. Register a key first.")
        
        self.settings["enabled"] = True
        self.settings["required_for_admin"] = True
        self.settings["updated"] = datetime.now().isoformat()
        self._save_settings(self.settings)
        
        return True
    
    def disable_titan_key_requirement(self):
        """Disable Titan key requirement (password-only access)"""
        self.settings["enabled"] = False
        self.settings["required_for_admin"] = False
        self.settings["updated"] = datetime.now().isoformat()
        self._save_settings(self.settings)
        
        return True
    
    def get_status(self) -> Dict:
        """Get current status of Titan key integration"""
        detection = self.detect_google_titan_key()
        
        return {
            "titan_key_detected": detection["detected"],
            "device_count": detection["count"],
            "registered_keys": len(self.registered_keys["keys"]),
            "requirement_enabled": self.settings.get("required_for_admin", False),
            "last_detection": detection["devices"],
            "registered_key_info": [
                {
                    "nickname": key["nickname"],
                    "registered_at": key["registered_at"][:10],
                    "last_used": key["last_used"][:10] if key["last_used"] else "Never"
                }
                for key in self.registered_keys["keys"]
            ]
        }

# Simple integration with existing security manager
class EnhancedSecurityManager:
    """Enhanced security manager with Google Titan key support"""
    
    def __init__(self, base_security_manager):
        self.base_sm = base_security_manager
        self.titan_manager = GoogleTitanKeyManager()
    
    def authenticate_admin_with_titan(self, password: str) -> tuple[bool, Optional[str]]:
        """Authenticate admin with password + Titan key"""
        # First verify password
        password_valid = self.base_sm.authenticate_master_admin(password)
        if not password_valid:
            return False, "Invalid password"
        
        # If Titan key is required, verify it
        if self.titan_manager.settings.get("required_for_admin", False):
            try:
                auth_result = self.titan_manager.authenticate_with_titan_key("master_admin")
                if auth_result.get("success"):
                    return True, "Password + Titan key authentication successful"
                else:
                    return False, "Titan key authentication failed"
            except Exception as e:
                return False, f"Titan key error: {str(e)}"
        
        # Password-only authentication
        return True, "Password authentication successful"