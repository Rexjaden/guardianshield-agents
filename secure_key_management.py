"""
Secure Key Management System for GuardianShield Validators
Implements HSM-like security for validator private keys
"""
import os
import json
import base64
import hashlib
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

class SecureKeyManager:
    def __init__(self, master_password=None, key_store_path="/kms/keys"):
        self.key_store_path = key_store_path
        self.master_key = self._derive_master_key(master_password or os.environ.get('MASTER_PASSWORD', ''))
        self.fernet = Fernet(self.master_key)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Ensure key store exists
        os.makedirs(key_store_path, mode=0o700, exist_ok=True)
    
    def _derive_master_key(self, password):
        """Derive master encryption key from password"""
        if not password:
            raise ValueError("Master password is required")
        
        # Use a fixed salt for consistency (in production, use HSM-stored salt)
        salt = b'guardianshield_validator_salt_2026'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def generate_validator_keys(self, validator_id, region):
        """Generate new validator key pair"""
        self.logger.info(f"Generating keys for validator {validator_id} in {region}")
        
        # Generate private key (32 bytes for ed25519)
        private_key = secrets.token_bytes(32)
        
        # Generate public key (simplified - in production use proper crypto)
        public_key = hashlib.sha256(private_key).digest()
        
        # Encrypt private key
        encrypted_private_key = self.fernet.encrypt(private_key)
        
        key_data = {
            'validator_id': validator_id,
            'region': region,
            'public_key': base64.b64encode(public_key).decode(),
            'encrypted_private_key': base64.b64encode(encrypted_private_key).decode(),
            'created_at': int(time.time()),
            'key_type': 'ed25519',
            'purpose': 'validator_consensus'
        }
        
        # Save encrypted key
        key_file = f"{self.key_store_path}/{validator_id}_{region}_validator.key"
        with open(key_file, 'w') as f:
            json.dump(key_data, f, indent=2)
        
        os.chmod(key_file, 0o600)  # Read-only by owner
        
        self.logger.info(f"Keys generated and stored for {validator_id}")
        return key_data
    
    def load_validator_key(self, validator_id, region):
        """Load and decrypt validator private key"""
        key_file = f"{self.key_store_path}/{validator_id}_{region}_validator.key"
        
        if not os.path.exists(key_file):
            raise FileNotFoundError(f"Key file not found: {key_file}")
        
        with open(key_file, 'r') as f:
            key_data = json.load(f)
        
        # Decrypt private key
        encrypted_private_key = base64.b64decode(key_data['encrypted_private_key'])
        private_key = self.fernet.decrypt(encrypted_private_key)
        
        return {
            'private_key': private_key,
            'public_key': base64.b64decode(key_data['public_key']),
            'validator_id': key_data['validator_id'],
            'region': key_data['region']
        }
    
    def backup_keys(self, backup_path="/kms/backup"):
        """Create encrypted backup of all keys"""
        self.logger.info("Creating key backup...")
        
        os.makedirs(backup_path, mode=0o700, exist_ok=True)
        
        import time
        backup_file = f"{backup_path}/validator_keys_backup_{int(time.time())}.json.enc"
        
        # Collect all key files
        key_files = []
        for filename in os.listdir(self.key_store_path):
            if filename.endswith('.key'):
                with open(f"{self.key_store_path}/{filename}", 'r') as f:
                    key_files.append({
                        'filename': filename,
                        'data': json.load(f)
                    })
        
        # Encrypt backup
        backup_data = json.dumps(key_files)
        encrypted_backup = self.fernet.encrypt(backup_data.encode())
        
        with open(backup_file, 'wb') as f:
            f.write(encrypted_backup)
        
        os.chmod(backup_file, 0o600)
        self.logger.info(f"Backup created: {backup_file}")
        return backup_file
    
    def rotate_keys(self, validator_id, region):
        """Rotate validator keys (generate new, keep old for transition)"""
        self.logger.info(f"Rotating keys for {validator_id} in {region}")
        
        # Backup old key
        old_key = self.load_validator_key(validator_id, region)
        
        # Generate new key
        new_key_data = self.generate_validator_keys(validator_id, region)
        
        # Store old key with timestamp
        import time
        old_key_file = f"{self.key_store_path}/{validator_id}_{region}_validator_old_{int(time.time())}.key"
        current_key_file = f"{self.key_store_path}/{validator_id}_{region}_validator.key"
        
        # Move current key to old
        if os.path.exists(current_key_file):
            os.rename(current_key_file, old_key_file)
        
        self.logger.info(f"Keys rotated for {validator_id}")
        return new_key_data
    
    def health_check(self):
        """Verify key manager health"""
        try:
            # Test encryption/decryption
            test_data = b"health_check_test"
            encrypted = self.fernet.encrypt(test_data)
            decrypted = self.fernet.decrypt(encrypted)
            
            if decrypted != test_data:
                return False, "Encryption test failed"
            
            # Check key store accessibility
            if not os.path.exists(self.key_store_path):
                return False, "Key store not accessible"
            
            return True, "Key manager healthy"
        
        except Exception as e:
            return False, f"Health check failed: {str(e)}"

def main():
    """Key manager main function"""
    import time
    
    # Initialize key manager
    kms = SecureKeyManager()
    
    # Health check
    healthy, message = kms.health_check()
    print(f"KMS Health: {message}")
    
    if not healthy:
        exit(1)
    
    # Generate initial keys if not exist
    regions = ['us-east', 'eu-west', 'asia-pacific']
    
    for i, region in enumerate(regions, 1):
        validator_id = f"guardian_validator_{i:03d}"
        key_file = f"{kms.key_store_path}/{validator_id}_{region}_validator.key"
        
        if not os.path.exists(key_file):
            print(f"Generating initial keys for {validator_id} in {region}")
            kms.generate_validator_keys(validator_id, region)
    
    # Create initial backup
    kms.backup_keys()
    
    print("Key Manager initialized successfully")
    print("Entering maintenance mode...")
    
    # Keep running for health checks
    while True:
        time.sleep(60)  # Check every minute
        healthy, message = kms.health_check()
        if not healthy:
            print(f"KMS Error: {message}")
        else:
            print("KMS: Healthy")

if __name__ == "__main__":
    main()