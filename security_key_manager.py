"""
FIDO2/WebAuthn Security Key Integration for GuardianShield
Supports K51T Titan Security Key and other FIDO2 devices
"""

import os
import json
import time
import hashlib
import base64
import secrets
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

from fido2.hid import CtapHidDevice
from fido2.client import Fido2Client, WindowsClient
from fido2.server import Fido2Server
from fido2 import cbor
from fido2.webauthn import PublicKeyCredentialRpEntity, PublicKeyCredentialUserEntity
from fido2.webauthn import PublicKeyCredentialParameters, PublicKeyCredentialType
from fido2.webauthn import AuthenticatorSelectionCriteria, UserVerificationRequirement
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

class GuardianShieldSecurityKey:
    """
    FIDO2/WebAuthn Security Key Manager for GuardianShield
    Provides hardware-based authentication using security keys
    """
    
    def __init__(self, rp_id: str = "guardian-shield.io", rp_name: str = "GuardianShield"):
        self.rp_id = rp_id
        self.rp_name = rp_name
        
        # Initialize FIDO2 server
        self.rp = PublicKeyCredentialRpEntity(rp_id, rp_name)
        self.server = Fido2Server(self.rp)
        
        # Credential storage
        self.credentials_file = ".guardian_webauthn_credentials.json"
        self.credentials = self._load_credentials()
        
        # Session management
        self.active_challenges = {}
        
        logger.info(f"GuardianShield Security Key Manager initialized for {rp_name}")

    def _load_credentials(self) -> Dict[str, Any]:
        """Load stored WebAuthn credentials"""
        if os.path.exists(self.credentials_file):
            try:
                with open(self.credentials_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load credentials: {e}")
        return {"users": {}, "credentials": {}}

    def _save_credentials(self):
        """Save WebAuthn credentials to secure storage"""
        try:
            with open(self.credentials_file, 'w') as f:
                json.dump(self.credentials, f, indent=2)
            os.chmod(self.credentials_file, 0o600)  # Owner read/write only
            logger.info("Credentials saved successfully")
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")

    def detect_security_keys(self) -> List[Dict[str, Any]]:
        """Detect available FIDO2 security keys"""
        keys = []
        try:
            for device in CtapHidDevice.list_devices():
                info = {
                    'product_name': getattr(device, 'product_name', 'Unknown'),
                    'manufacturer': getattr(device, 'manufacturer_string', 'Unknown'),
                    'path': str(device.path) if hasattr(device, 'path') else 'Unknown'
                }
                keys.append(info)
                logger.info(f"Detected security key: {info}")
        except Exception as e:
            logger.error(f"Error detecting security keys: {e}")
        return keys

    def register_security_key(self, user_id: str, username: str, display_name: str = None) -> Dict[str, Any]:
        """
        Register a new security key for a user
        Returns challenge data for the frontend to complete registration
        """
        if not display_name:
            display_name = username
            
        # Create user entity
        user = PublicKeyCredentialUserEntity(
            id=user_id.encode(),
            name=username,
            display_name=display_name
        )
        
        # Get existing credentials for this user
        existing_credentials = []
        user_creds = self.credentials["users"].get(user_id, {}).get("credentials", [])
        for cred_id in user_creds:
            if cred_id in self.credentials["credentials"]:
                cred_data = self.credentials["credentials"][cred_id]
                existing_credentials.append(
                    {"id": base64.b64decode(cred_id), "type": "public-key"}
                )
        
        # Create registration challenge
        options, state = self.server.register_begin(
            user=user,
            credentials=existing_credentials,
            user_verification=UserVerificationRequirement.PREFERRED
        )
        
        # Store challenge state
        challenge_id = secrets.token_urlsafe(32)
        self.active_challenges[challenge_id] = {
            "state": state,
            "user_id": user_id,
            "username": username,
            "display_name": display_name,
            "created_at": time.time(),
            "type": "registration"
        }
        
        return {
            "challenge_id": challenge_id,
            "options": {
                "publicKey": {
                    "challenge": base64.b64encode(options.challenge).decode(),
                    "rp": {"id": options.rp.id, "name": options.rp.name},
                    "user": {
                        "id": base64.b64encode(options.user.id).decode(),
                        "name": options.user.name,
                        "displayName": options.user.display_name
                    },
                    "pubKeyCredParams": [
                        {"type": param.type, "alg": param.alg} 
                        for param in options.pub_key_cred_params
                    ],
                    "authenticatorSelection": {
                        "userVerification": options.authenticator_selection.user_verification.value
                        if options.authenticator_selection else "preferred"
                    },
                    "excludeCredentials": [
                        {"id": base64.b64encode(cred["id"]).decode(), "type": cred["type"]}
                        for cred in existing_credentials
                    ],
                    "timeout": 60000
                }
            }
        }

    def complete_registration(self, challenge_id: str, credential_response: Dict[str, Any]) -> Dict[str, Any]:
        """Complete security key registration"""
        if challenge_id not in self.active_challenges:
            raise ValueError("Invalid or expired challenge")
            
        challenge_data = self.active_challenges[challenge_id]
        if challenge_data["type"] != "registration":
            raise ValueError("Invalid challenge type")
            
        # Check challenge expiry (5 minutes)
        if time.time() - challenge_data["created_at"] > 300:
            del self.active_challenges[challenge_id]
            raise ValueError("Challenge expired")
        
        try:
            # Complete registration
            auth_data = self.server.register_complete(
                challenge_data["state"],
                credential_response
            )
            
            # Store credential
            cred_id = base64.b64encode(auth_data.credential_id).decode()
            self.credentials["credentials"][cred_id] = {
                "id": cred_id,
                "public_key": base64.b64encode(auth_data.credential_public_key).decode(),
                "sign_count": auth_data.sign_count,
                "created_at": datetime.now().isoformat(),
                "last_used": datetime.now().isoformat(),
                "user_id": challenge_data["user_id"],
                "nickname": f"Security Key - {datetime.now().strftime('%Y-%m-%d')}"
            }
            
            # Update user credentials
            user_id = challenge_data["user_id"]
            if user_id not in self.credentials["users"]:
                self.credentials["users"][user_id] = {
                    "username": challenge_data["username"],
                    "display_name": challenge_data["display_name"],
                    "credentials": []
                }
            
            self.credentials["users"][user_id]["credentials"].append(cred_id)
            self._save_credentials()
            
            # Clean up challenge
            del self.active_challenges[challenge_id]
            
            return {
                "success": True,
                "credential_id": cred_id,
                "message": "Security key registered successfully"
            }
            
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            if challenge_id in self.active_challenges:
                del self.active_challenges[challenge_id]
            raise ValueError(f"Registration failed: {str(e)}")

    def authenticate_with_security_key(self, user_id: str = None) -> Dict[str, Any]:
        """
        Start authentication process with security key
        Returns challenge data for the frontend
        """
        # Get credentials for authentication
        allowed_credentials = []
        
        if user_id:
            # Authenticate specific user
            user_creds = self.credentials["users"].get(user_id, {}).get("credentials", [])
            for cred_id in user_creds:
                if cred_id in self.credentials["credentials"]:
                    allowed_credentials.append(
                        {"id": base64.b64decode(cred_id), "type": "public-key"}
                    )
        else:
            # Allow any registered credential
            for cred_id, cred_data in self.credentials["credentials"].items():
                allowed_credentials.append(
                    {"id": base64.b64decode(cred_id), "type": "public-key"}
                )
        
        if not allowed_credentials:
            raise ValueError("No registered security keys found")
        
        # Create authentication challenge
        options, state = self.server.authenticate_begin(
            credentials=allowed_credentials,
            user_verification=UserVerificationRequirement.PREFERRED
        )
        
        # Store challenge state
        challenge_id = secrets.token_urlsafe(32)
        self.active_challenges[challenge_id] = {
            "state": state,
            "user_id": user_id,
            "created_at": time.time(),
            "type": "authentication"
        }
        
        return {
            "challenge_id": challenge_id,
            "options": {
                "publicKey": {
                    "challenge": base64.b64encode(options.challenge).decode(),
                    "allowCredentials": [
                        {"id": base64.b64encode(cred["id"]).decode(), "type": cred["type"]}
                        for cred in allowed_credentials
                    ],
                    "userVerification": options.user_verification.value,
                    "timeout": 60000
                }
            }
        }

    def complete_authentication(self, challenge_id: str, auth_response: Dict[str, Any]) -> Dict[str, Any]:
        """Complete security key authentication"""
        if challenge_id not in self.active_challenges:
            raise ValueError("Invalid or expired challenge")
            
        challenge_data = self.active_challenges[challenge_id]
        if challenge_data["type"] != "authentication":
            raise ValueError("Invalid challenge type")
            
        # Check challenge expiry (5 minutes)
        if time.time() - challenge_data["created_at"] > 300:
            del self.active_challenges[challenge_id]
            raise ValueError("Challenge expired")
        
        try:
            # Complete authentication
            credential = self.server.authenticate_complete(
                challenge_data["state"],
                auth_response
            )
            
            # Update credential usage
            cred_id = base64.b64encode(credential.credential_id).decode()
            if cred_id in self.credentials["credentials"]:
                self.credentials["credentials"][cred_id]["last_used"] = datetime.now().isoformat()
                self.credentials["credentials"][cred_id]["sign_count"] = credential.sign_count
                
                # Find user for this credential
                user_id = self.credentials["credentials"][cred_id]["user_id"]
                username = self.credentials["users"].get(user_id, {}).get("username", "Unknown")
                
                self._save_credentials()
                
                # Clean up challenge
                del self.active_challenges[challenge_id]
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "username": username,
                    "credential_id": cred_id,
                    "message": "Authentication successful"
                }
            else:
                raise ValueError("Credential not found")
                
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            if challenge_id in self.active_challenges:
                del self.active_challenges[challenge_id]
            raise ValueError(f"Authentication failed: {str(e)}")

    def get_user_credentials(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all security keys registered for a user"""
        if user_id not in self.credentials["users"]:
            return []
            
        user_creds = []
        for cred_id in self.credentials["users"][user_id]["credentials"]:
            if cred_id in self.credentials["credentials"]:
                cred_data = self.credentials["credentials"][cred_id].copy()
                # Remove sensitive data
                cred_data.pop("public_key", None)
                user_creds.append(cred_data)
        
        return user_creds

    def remove_credential(self, user_id: str, credential_id: str) -> bool:
        """Remove a security key credential"""
        if user_id not in self.credentials["users"]:
            return False
            
        if credential_id in self.credentials["users"][user_id]["credentials"]:
            # Remove from user's credentials
            self.credentials["users"][user_id]["credentials"].remove(credential_id)
            
            # Remove the credential itself
            if credential_id in self.credentials["credentials"]:
                del self.credentials["credentials"][credential_id]
            
            self._save_credentials()
            return True
        
        return False

    def cleanup_expired_challenges(self):
        """Clean up expired challenges (older than 5 minutes)"""
        current_time = time.time()
        expired_challenges = [
            cid for cid, data in self.active_challenges.items()
            if current_time - data["created_at"] > 300
        ]
        
        for cid in expired_challenges:
            del self.active_challenges[cid]
            
        if expired_challenges:
            logger.info(f"Cleaned up {len(expired_challenges)} expired challenges")