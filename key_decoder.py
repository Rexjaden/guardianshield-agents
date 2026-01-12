#!/usr/bin/env python3
"""
GuardianShield Key Decoder Utility
Safely decodes the encoded private key for contract deployment
"""

import os
import base64
from typing import Optional

def decode_private_key() -> Optional[str]:
    """Decode the Base64 encoded private key from environment"""
    try:
        # Load encoded key from environment
        encoded_key = os.getenv('PRIVATE_KEY_ENCODED')
        
        if not encoded_key:
            raise ValueError("PRIVATE_KEY_ENCODED not found in environment")
        
        # Decode Base64
        decoded_bytes = base64.b64decode(encoded_key)
        private_key = decoded_bytes.decode('utf-8')
        
        # Validate format (should be 64 hex characters)
        if len(private_key) != 64:
            raise ValueError("Invalid private key length")
        
        # Validate hex format
        int(private_key, 16)
        
        return private_key
        
    except Exception as e:
        print(f"❌ Error decoding private key: {e}")
        return None

def get_private_key_for_deployment() -> str:
    """Get private key for contract deployment (with 0x prefix)"""
    private_key = decode_private_key()
    if not private_key:
        raise ValueError("Failed to decode private key")
    
    # Add 0x prefix if not present
    if not private_key.startswith('0x'):
        private_key = '0x' + private_key
    
    return private_key

if __name__ == "__main__":
    # Test the decoder
    from dotenv import load_dotenv
    load_dotenv()
    
    key = decode_private_key()
    if key:
        print("✅ Private key decoded successfully")
        print(f"🔑 Key format: {'0x' + key[:8]}...{key[-8:]} (showing first/last 8 chars)")
    else:
        print("❌ Failed to decode private key")