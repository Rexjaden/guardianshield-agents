#!/usr/bin/env python3
"""
GuardianShield Secure Key Management
Handles private key security with encryption and secure storage
"""

import os
import getpass
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import json

class SecureKeyManager:
    """Manages private keys with encryption and secure access"""
    
    def __init__(self, key_file='.secure_keys.enc'):
        self.key_file = key_file
        self.salt_file = '.key_salt'
        
    def _derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def _get_or_create_salt(self) -> bytes:
        """Get existing salt or create new one"""
        if os.path.exists(self.salt_file):
            with open(self.salt_file, 'rb') as f:
                return f.read()
        else:
            salt = os.urandom(16)
            with open(self.salt_file, 'wb') as f:
                f.write(salt)
            return salt
    
    def encrypt_and_store_key(self, private_key: str):
        """Encrypt and securely store private key"""
        # Get master password
        print("🔐 Setting up secure key storage...")
        password = getpass.getpass("Enter master password for key encryption (min 12 chars): ")
        
        if len(password) < 12:
            raise ValueError("Password must be at least 12 characters long")
        
        # Confirm password
        confirm_password = getpass.getpass("Confirm master password: ")
        if password != confirm_password:
            raise ValueError("Passwords do not match")
        
        # Get or create salt
        salt = self._get_or_create_salt()
        
        # Derive encryption key
        encryption_key = self._derive_key_from_password(password, salt)
        fernet = Fernet(encryption_key)
        
        # Encrypt the private key
        encrypted_key = fernet.encrypt(private_key.encode())
        
        # Store encrypted key with metadata
        key_data = {
            'encrypted_key': base64.urlsafe_b64encode(encrypted_key).decode(),
            'key_hash': hashlib.sha256(private_key.encode()).hexdigest()[:16],  # Partial hash for verification
            'created': str(int(time.time())) if 'time' in globals() else '0'
        }
        
        with open(self.key_file, 'w') as f:
            json.dump(key_data, f)
        
        print("✅ Private key encrypted and stored securely")
        print(f"🔒 Encrypted file: {self.key_file}")
        print("⚠️  IMPORTANT: Remember your master password - it cannot be recovered!")
    
    def decrypt_and_get_key(self) -> str:
        """Decrypt and retrieve private key"""
        if not os.path.exists(self.key_file) or not os.path.exists(self.salt_file):
            raise FileNotFoundError("Encrypted key file not found. Run encrypt_and_store_key() first.")
        
        # Load encrypted data
        with open(self.key_file, 'r') as f:
            key_data = json.load(f)
        
        # Load salt
        with open(self.salt_file, 'rb') as f:
            salt = f.read()
        
        # Get password
        password = getpass.getpass("🔐 Enter master password to decrypt private key: ")
        
        try:
            # Derive encryption key
            encryption_key = self._derive_key_from_password(password, salt)
            fernet = Fernet(encryption_key)
            
            # Decrypt private key
            encrypted_key = base64.urlsafe_b64decode(key_data['encrypted_key'].encode())
            decrypted_key = fernet.decrypt(encrypted_key).decode()
            
            # Verify integrity with partial hash
            key_hash = hashlib.sha256(decrypted_key.encode()).hexdigest()[:16]
            if key_hash != key_data['key_hash']:
                raise ValueError("Key integrity check failed")
            
            return decrypted_key
            
        except Exception as e:
            raise ValueError(f"Failed to decrypt key: {e}")
    
    def key_exists(self) -> bool:
        """Check if encrypted key exists"""
        return os.path.exists(self.key_file) and os.path.exists(self.salt_file)

def setup_secure_key_storage():
    """Interactive setup for secure key storage"""
    manager = SecureKeyManager()
    
    if manager.key_exists():
        print("🔒 Encrypted key storage already exists")
        choice = input("Replace existing key? (y/N): ").strip().lower()
        if choice != 'y':
            print("Keeping existing encrypted key")
            return
    
    print("\n🛡️ SECURE PRIVATE KEY SETUP")
    print("=" * 50)
    print("This will encrypt and securely store your private key.")
    print("You will need to enter your master password each time you deploy contracts.")
    print("⚠️  NEVER store your private key in plain text files!")
    
    # Get private key securely
    private_key = getpass.getpass("\n🔑 Enter your private key (will be hidden): ").strip()
    
    if not private_key or len(private_key) < 60:
        print("❌ Invalid private key format")
        return
    
    if private_key.startswith('0x'):
        private_key = private_key[2:]
    
    try:
        # Validate hex format
        int(private_key, 16)
        manager.encrypt_and_store_key(private_key)
        print("\n✅ PRIVATE KEY SECURED!")
        print("🔐 Your key is now encrypted and protected")
        print("💡 Update your deployment scripts to use decrypt_and_get_key()")
        
    except ValueError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Failed to secure key: {e}")

if __name__ == "__main__":
    import time
    setup_secure_key_storage()