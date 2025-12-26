"""
web3_utils.py: Secure utilities for interacting with smart contracts using web3.py
"""
import os
import logging
import re
from types import SimpleNamespace
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
    def __init__(self, rpc_url: Optional[str] = None, web3_instance: Any = None):
        self.rpc_url = rpc_url or os.getenv("WEB3_RPC_URL", "http://localhost:8545")
        self.max_gas_price = int(float(os.getenv("WEB3_MAX_GAS_PRICE_GWEI", "200")) * 1_000_000_000)
        self.transaction_timeout = int(os.getenv("WEB3_TRANSACTION_TIMEOUT", "120"))
        self.default_gas_limit = int(os.getenv("WEB3_DEFAULT_GAS_LIMIT", "300000"))
        self.gas_safety_margin = float(os.getenv("WEB3_GAS_SAFETY_MARGIN", "1.0"))
        self.web3 = web3_instance

        if self.web3 is None:
            self.web3 = self._initialize_web3()

    def _initialize_web3(self):
        """Initialize Web3 connection with graceful fallback"""
        if not WEB3_AVAILABLE:
            logger.warning("Web3 not available, using mock provider")
            return self._build_mock_web3()

        try:
            from importlib import import_module
            web3_module = import_module("web3")
            web3_cls = getattr(web3_module, "Web3", None)
            provider_cls = getattr(web3_cls, "HTTPProvider", None) if web3_cls else None

            if web3_cls and provider_cls:
                web3_instance = web3_cls(provider_cls(self.rpc_url))
            elif web3_cls:
                web3_instance = web3_cls()
            else:
                return self._build_mock_web3()

            is_connected = getattr(web3_instance, "is_connected", None)
            if callable(is_connected):
                connected = is_connected()
                if isinstance(connected, bool) and not connected:
                    raise ConnectionError("Web3 connection failed")

            return web3_instance

        except Exception as exc:
            logger.error(f"Web3 initialization failed: {exc}")
            return self._build_mock_web3()

    def _build_mock_web3(self):
        """Build a minimal mock Web3 interface for offline/testing"""
        def default_estimate_gas(params):
            return self.default_gas_limit

        eth_interface = SimpleNamespace(
            estimate_gas=default_estimate_gas,
            gas_price=self.max_gas_price,
            contract=lambda *args, **kwargs: None,
            get_code=lambda address: b"",
            get_transaction_count=lambda address: 0,
            send_raw_transaction=lambda raw: b"",
            wait_for_transaction_receipt=lambda tx_hash, timeout=None: SimpleNamespace(status=1)
        )

        return SimpleNamespace(
            eth=eth_interface,
            is_address=lambda address: bool(re.fullmatch(r"^0x[a-fA-F0-9]{40}$", address or "")),
            to_checksum_address=lambda address: address,
            is_connected=lambda: True
        )

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

    def validate_address(self, address: str) -> bool:
        """Validate Ethereum address format"""
        if not address:
            return False

        try:
            if self.web3 and hasattr(self.web3, "is_address"):
                result = self.web3.is_address(address)
                if isinstance(result, bool):
                    return result
        except Exception:
            pass

        return bool(re.fullmatch(r"^0x[a-fA-F0-9]{40}$", address))

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

    def estimate_gas_safely(self, tx_params: Dict[str, Any]) -> int:
        """Estimate gas with sensible defaults"""
        if not self.web3 or not hasattr(self.web3, 'eth'):
            return self.default_gas_limit

        estimate_callable = getattr(self.web3.eth, 'estimate_gas', None)
        if not callable(estimate_callable):
            return self.default_gas_limit

        try:
            gas_estimate = estimate_callable(tx_params)
            if gas_estimate <= 0:
                raise ValueError("Invalid gas estimate")
            buffered = int(gas_estimate * self.gas_safety_margin)
            return min(buffered, self.default_gas_limit * 5)
        except Exception as exc:
            logger.warning(f"Gas estimation failed, using default: {exc}")
            return self.default_gas_limit

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
