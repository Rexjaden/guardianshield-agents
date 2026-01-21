#!/usr/bin/env python3
"""
GuardianShield Token Serial Number System
Generates unique, secure serial numbers for each SHIELD token
"""

import hashlib
import time
import random
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import secrets

class ShieldTokenSerial:
    def __init__(self, db_path: str = "shield_serial_numbers.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the serial number database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shield_serials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                serial_number TEXT UNIQUE NOT NULL,
                token_id TEXT UNIQUE,
                wallet_address TEXT,
                creation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                mint_transaction TEXT,
                status TEXT DEFAULT 'active',
                metadata TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS serial_batches (
                batch_id TEXT PRIMARY KEY,
                batch_name TEXT,
                total_tokens INTEGER,
                creation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                batch_metadata TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_serial_number(self, batch_id: str = None) -> str:
        """
        Generate a unique SHIELD token serial number
        Format: GST-YYYY-BATCH-XXXXXX-CHECKSUM
        """
        current_year = datetime.now().year
        
        # Use current batch or generate new batch
        if not batch_id:
            batch_id = f"B{random.randint(1000, 9999)}"
        
        # Generate unique 6-digit sequence
        timestamp = str(int(time.time()))[-6:]
        random_part = f"{random.randint(100000, 999999):06d}"
        sequence = f"{timestamp}{random_part}"[-6:]
        
        # Create base serial
        base_serial = f"GST-{current_year}-{batch_id}-{sequence}"
        
        # Generate checksum
        checksum = self.calculate_checksum(base_serial)
        
        # Final serial number
        serial_number = f"{base_serial}-{checksum}"
        
        return serial_number
    
    def calculate_checksum(self, base_serial: str) -> str:
        """Calculate a 3-character checksum for the serial number"""
        hash_obj = hashlib.sha256(base_serial.encode())
        hex_hash = hash_obj.hexdigest()
        
        # Convert to alphanumeric (excluding confusing characters)
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        checksum = ""
        
        for i in range(0, 6, 2):
            byte_val = int(hex_hash[i:i+2], 16)
            checksum += chars[byte_val % len(chars)]
        
        return checksum[:3]
    
    def mint_token_serial(self, wallet_address: str, batch_id: str = None, 
                         token_metadata: Dict = None) -> Dict:
        """Mint a new SHIELD token with serial number"""
        serial_number = self.generate_serial_number(batch_id)
        
        # Ensure uniqueness
        while self.serial_exists(serial_number):
            serial_number = self.generate_serial_number(batch_id)
        
        token_id = f"SHIELD_{secrets.token_hex(16)}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO shield_serials 
                (serial_number, token_id, wallet_address, metadata)
                VALUES (?, ?, ?, ?)
            ''', (
                serial_number, 
                token_id, 
                wallet_address,
                json.dumps(token_metadata or {})
            ))
            
            conn.commit()
            
            return {
                'success': True,
                'serial_number': serial_number,
                'token_id': token_id,
                'wallet_address': wallet_address,
                'creation_date': datetime.now().isoformat(),
                'metadata': token_metadata or {}
            }
            
        except sqlite3.IntegrityError as e:
            return {
                'success': False,
                'error': f'Serial number collision: {e}'
            }
        finally:
            conn.close()
    
    def verify_serial_number(self, serial_number: str) -> Dict:
        """Verify a SHIELD token serial number"""
        if not self.validate_serial_format(serial_number):
            return {
                'valid': False,
                'error': 'Invalid serial number format'
            }
        
        # Verify checksum
        parts = serial_number.split('-')
        if len(parts) != 5:
            return {
                'valid': False,
                'error': 'Invalid serial number structure'
            }
        
        base_serial = '-'.join(parts[:-1])
        provided_checksum = parts[-1]
        calculated_checksum = self.calculate_checksum(base_serial)
        
        if provided_checksum != calculated_checksum:
            return {
                'valid': False,
                'error': 'Invalid checksum'
            }
        
        # Check database
        token_info = self.get_token_info(serial_number)
        if not token_info:
            return {
                'valid': False,
                'error': 'Serial number not found in registry'
            }
        
        return {
            'valid': True,
            'token_info': token_info
        }
    
    def validate_serial_format(self, serial_number: str) -> bool:
        """Validate serial number format"""
        import re
        pattern = r'^GST-\d{4}-B\d{4}-\d{6}-[A-Z0-9]{3}$'
        return bool(re.match(pattern, serial_number))
    
    def serial_exists(self, serial_number: str) -> bool:
        """Check if serial number already exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT COUNT(*) FROM shield_serials WHERE serial_number = ?',
            (serial_number,)
        )
        
        exists = cursor.fetchone()[0] > 0
        conn.close()
        return exists
    
    def get_token_info(self, serial_number: str) -> Optional[Dict]:
        """Get token information by serial number"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT serial_number, token_id, wallet_address, 
                   creation_date, mint_transaction, status, metadata
            FROM shield_serials 
            WHERE serial_number = ?
        ''', (serial_number,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'serial_number': result[0],
                'token_id': result[1],
                'wallet_address': result[2],
                'creation_date': result[3],
                'mint_transaction': result[4],
                'status': result[5],
                'metadata': json.loads(result[6] or '{}')
            }
        return None
    
    def get_wallet_tokens(self, wallet_address: str) -> List[Dict]:
        """Get all tokens owned by a wallet address"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT serial_number, token_id, creation_date, status, metadata
            FROM shield_serials 
            WHERE wallet_address = ? AND status = 'active'
            ORDER BY creation_date DESC
        ''', (wallet_address,))
        
        results = cursor.fetchall()
        conn.close()
        
        tokens = []
        for result in results:
            tokens.append({
                'serial_number': result[0],
                'token_id': result[1],
                'creation_date': result[2],
                'status': result[3],
                'metadata': json.loads(result[4] or '{}')
            })
        
        return tokens
    
    def transfer_token(self, serial_number: str, new_wallet_address: str, 
                      transaction_hash: str = None) -> Dict:
        """Transfer token to new wallet address"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE shield_serials 
                SET wallet_address = ?, mint_transaction = ?
                WHERE serial_number = ? AND status = 'active'
            ''', (new_wallet_address, transaction_hash, serial_number))
            
            if cursor.rowcount == 0:
                return {
                    'success': False,
                    'error': 'Token not found or already transferred'
                }
            
            conn.commit()
            return {
                'success': True,
                'message': 'Token transferred successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Transfer failed: {e}'
            }
        finally:
            conn.close()
    
    def create_batch(self, batch_name: str, total_tokens: int, 
                    batch_metadata: Dict = None) -> str:
        """Create a new batch for minting tokens"""
        batch_id = f"B{random.randint(1000, 9999)}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO serial_batches 
            (batch_id, batch_name, total_tokens, batch_metadata)
            VALUES (?, ?, ?, ?)
        ''', (
            batch_id, 
            batch_name, 
            total_tokens,
            json.dumps(batch_metadata or {})
        ))
        
        conn.commit()
        conn.close()
        
        return batch_id
    
    def get_serial_statistics(self) -> Dict:
        """Get statistics about minted tokens"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM shield_serials')
        total_minted = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM shield_serials WHERE status = "active"')
        active_tokens = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(DISTINCT wallet_address) 
            FROM shield_serials 
            WHERE status = "active"
        ''')
        unique_holders = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_minted': total_minted,
            'active_tokens': active_tokens,
            'unique_holders': unique_holders,
            'last_updated': datetime.now().isoformat()
        }

def main():
    """Example usage of the SHIELD token serial system"""
    shield_serial = ShieldTokenSerial()
    
    # Create a batch
    batch_id = shield_serial.create_batch(
        "Genesis Series", 
        1000, 
        {"description": "First batch of SHIELD tokens"}
    )
    print(f"Created batch: {batch_id}")
    
    # Mint some tokens
    for i in range(5):
        result = shield_serial.mint_token_serial(
            f"0x{secrets.token_hex(20)}",
            batch_id,
            {"tier": "Genesis", "index": i+1}
        )
        
        if result['success']:
            print(f"Minted token: {result['serial_number']}")
            
            # Verify the token
            verification = shield_serial.verify_serial_number(result['serial_number'])
            print(f"Verification: {'✅ Valid' if verification['valid'] else '❌ Invalid'}")
    
    # Get statistics
    stats = shield_serial.get_serial_statistics()
    print(f"\nStatistics: {json.dumps(stats, indent=2)}")

if __name__ == "__main__":
    main()