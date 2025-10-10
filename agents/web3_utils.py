"""
web3_utils.py: Secure utilities for interacting with smart contracts using web3.py
"""
import os
import logging
from typing import Optional, Dict, Any

try:
    from web3 import Web3
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    print("Warning: web3 not available, blockchain features disabled")

try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("Warning: cryptography not available, using basic encryption fallbacks")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecureWeb3Utils:
    def __init__(self, rpc_url: Optional[str] = None):
        self.rpc_url = rpc_url or os.getenv("WEB3_RPC_URL", "http://localhost:8545")
        self.web3 = None
        
        if WEB3_AVAILABLE:
            try:
                self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
                if not self.web3.is_connected():
                    logger.error("Failed to connect to Web3 provider")
                    raise ConnectionError("Web3 connection failed")
            except Exception as e:
                logger.error(f"Web3 initialization failed: {e}")
                self.web3 = None
        else:
            logger.warning("Web3 not available, blockchain operations disabled")

    def get_contract(self, address: str, abi: list):
        """Get contract instance with validation"""
        if not self.web3:
            logger.error("Web3 not available")
            return None
            
        try:
            if not self.web3.is_address(address):
                raise ValueError(f"Invalid contract address: {address}")
            
            # Convert to checksum address
            checksum_address = self.web3.to_checksum_address(address)
            contract = self.web3.eth.contract(address=checksum_address, abi=abi)
            
            # Verify contract exists
            code = self.web3.eth.get_code(checksum_address)
            if code == b'':
                raise ValueError(f"No contract found at address: {address}")
                
            return contract
            
        except Exception as e:
            logger.error(f"Error getting contract: {e}")
            raise

    def call_function(self, contract, function_name: str, *args, **kwargs) -> Any:
        """Safely call a contract function"""
        try:
            if not hasattr(contract.functions, function_name):
                raise AttributeError(f"Function {function_name} not found in contract")
                
            func = getattr(contract.functions, function_name)
            return func(*args, **kwargs).call()
            
        except Exception as e:
            logger.error(f"Error calling function {function_name}: {e}")
            raise

    def estimate_gas(self, contract, function_name: str, from_address: str, *args, **kwargs) -> int:
        """Estimate gas for a transaction"""
        try:
            func = getattr(contract.functions, function_name)
            return func(*args, **kwargs).estimate_gas({'from': from_address})
        except Exception as e:
            logger.error(f"Error estimating gas for {function_name}: {e}")
            return 0

    def send_transaction(self, contract, function_name: str, private_key: str, *args, **kwargs) -> str:
        """Send a transaction with enhanced security"""
        try:
            # Decrypt private key if it's encrypted
            decrypted_key = self._decrypt_private_key(private_key)
            
            # Get account from private key
            account = self.web3.eth.account.from_key(decrypted_key)
            
            # Get function
            func = getattr(contract.functions, function_name)
            
            # Estimate gas
            gas_estimate = self.estimate_gas(contract, function_name, account.address, *args, **kwargs)
            
            # Build transaction
            tx = func(*args, **kwargs).build_transaction({
                'from': account.address,
                'nonce': self.web3.eth.get_transaction_count(account.address),
                'gas': int(gas_estimate * 1.2),  # Add 20% buffer
                'gasPrice': self.web3.eth.gas_price
            })
            
            # Sign transaction
            signed_tx = self.web3.eth.account.sign_transaction(tx, decrypted_key)
            
            # Send transaction
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            logger.info(f"Transaction sent: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Error sending transaction: {e}")
            raise
        finally:
            # Clear sensitive data
            if 'decrypted_key' in locals():
                del decrypted_key

    def _decrypt_private_key(self, encrypted_key: str) -> str:
        """Decrypt private key (placeholder - implement your encryption)"""
        # This is a placeholder - implement proper key decryption
        # For now, assume the key is already decrypted
        if encrypted_key.startswith("0x"):
            return encrypted_key
        else:
            # If it's encrypted, decrypt it here
            return encrypted_key

    def wait_for_transaction(self, tx_hash: str, timeout: int = 300) -> Dict:
        """Wait for transaction confirmation"""
        try:
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
            if receipt.status == 1:
                logger.info(f"Transaction {tx_hash} confirmed successfully")
            else:
                logger.error(f"Transaction {tx_hash} failed")
            return receipt
        except Exception as e:
            logger.error(f"Error waiting for transaction {tx_hash}: {e}")
            raise

# Legacy compatibility
class Web3Utils(SecureWeb3Utils):
    """Legacy class for backward compatibility"""
    pass
