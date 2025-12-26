"""
flare_integration.py: Enhanced Flare blockchain integration for multi-chain spam site info, metadata storage, and price feeds.
"""
import logging
import asyncio
import json
import time
import hashlib
from types import SimpleNamespace
from typing import Dict, List, Optional, Any
import os

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests not available, HTTP features disabled")

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    print("Warning: httpx not available, async HTTP disabled")

try:
    from web3 import Web3
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    print("Warning: web3 not available, blockchain features disabled")

try:
    from dotenv import load_dotenv
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("Warning: python-dotenv not available")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FlareIntegrationAgent:
    def __init__(self, api_url: str = None, api_key: str = None):
        self.api_url = api_url or os.getenv('FLARE_API_URL', 'https://flare-api.flare.network/ext/bc/C/rpc')
        self.api_key = api_key or os.getenv('FLARE_API_KEY')
        self.web3 = self._initialize_web3()
        self.threat_contract_address = os.getenv('THREAT_CONTRACT_ADDRESS')
        self.private_key = os.getenv('FLARE_PRIVATE_KEY')
        self.price_feeds = {
            'ETH': '0x9326BFA02ADD2366b30bacB125260Af641031331',
            'FLR': '0x462Acf84CE50DB6B6B4c7ABF93e8b9A94f6B8c37'
        }
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
        self.rate_limit_delay = 1.0  # 1 second between requests
        self.last_request_time = 0

    def _initialize_web3(self):
        """Initialize Web3 provider with graceful fallback"""
        if not WEB3_AVAILABLE:
            logger.warning("Web3 unavailable, using mock provider")
            return self._build_mock_web3()

        try:
            from importlib import import_module
            web3_module = import_module('web3')
            web3_cls = getattr(web3_module, 'Web3', None)
            provider_cls = getattr(web3_cls, 'HTTPProvider', None) if web3_cls else None

            if web3_cls and provider_cls:
                instance = web3_cls(provider_cls(self.api_url))
            elif web3_cls:
                instance = web3_cls()
            else:
                return self._build_mock_web3()

            return instance

        except Exception as exc:
            logger.error(f"FlareIntegrationAgent Web3 init failed: {exc}")
            return self._build_mock_web3()

    def _build_mock_web3(self):
        """Construct lightweight mock Web3 interface for testing"""
        def default_get_block(block_identifier):
            now = int(time.time())
            return {
                'number': 0,
                'timestamp': now,
                'transactions': []
            }

        eth_interface = SimpleNamespace(
            get_block=default_get_block,
            gas_price=0,
            contract=lambda *args, **kwargs: SimpleNamespace(functions=SimpleNamespace())
        )

        net_interface = SimpleNamespace(version="0")

        return SimpleNamespace(
            eth=eth_interface,
            net=net_interface,
            is_connected=lambda: True,
            to_checksum_address=lambda address: address,
            from_wei=lambda value, unit='wei': value / 1_000_000_000 if unit == 'gwei' else value
        )

    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()

    def _cache_key(self, method: str, params: str) -> str:
        """Generate cache key"""
        return hashlib.md5(f"{method}:{params}".encode()).hexdigest()

    def _get_cached_data(self, cache_key: str) -> Optional[Any]:
        """Get cached data if still valid"""
        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_timeout:
                return data
            else:
                del self.cache[cache_key]
        return None

    def _set_cache_data(self, cache_key: str, data: Any):
        """Set data in cache"""
        self.cache[cache_key] = (data, time.time())

    async def async_post(self, endpoint, payload, headers=None, retries=3):
        """Enhanced async POST with error handling and retries"""
        url = f"{self.api_url}/{endpoint}"
        headers = headers or {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        
        for attempt in range(retries):
            try:
                self._rate_limit()
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    return response.status_code == 200
            except Exception as e:
                logger.error(f"Async POST error to {endpoint} (attempt {attempt+1}): {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        return False

    async def async_get(self, endpoint, params=None, headers=None, retries=3):
        """Enhanced async GET with error handling and retries"""
        url = f"{self.api_url}/{endpoint}"
        headers = headers or {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        
        for attempt in range(retries):
            try:
                self._rate_limit()
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get(url, params=params, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    if isinstance(data, dict):
                        return data
                    else:
                        logger.warning(f"Unexpected response format from Flare async GET {endpoint}.")
                        return None
            except Exception as e:
                logger.error(f"Async GET error from {endpoint} (attempt {attempt+1}): {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        return None

    def get_price_data(self, symbol: str = 'ETH') -> Optional[Dict]:
        """Enhanced price data retrieval with blockchain integration"""
        try:
            cache_key = self._cache_key('price_data', symbol)
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return cached_data

            self._rate_limit()

            if symbol not in self.price_feeds:
                logger.error(f"Price feed not available for {symbol}")
                return None

            # Get price data from Flare price feed
            contract_address = self.price_feeds[symbol]
            
            # Price feed ABI (simplified)
            price_feed_abi = [
                {
                    "inputs": [],
                    "name": "latestAnswer",
                    "outputs": [{"internalType": "int256", "name": "", "type": "int256"}],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [],
                    "name": "latestTimestamp",
                    "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]

            checksum_fn = getattr(self.web3, 'to_checksum_address', None)
            checksum_address = checksum_fn(contract_address) if callable(checksum_fn) else contract_address

            contract = self.web3.eth.contract(
                address=checksum_address,
                abi=price_feed_abi
            )

            # Get latest price and timestamp
            latest_price = contract.functions.latestAnswer().call()
            latest_timestamp = contract.functions.latestTimestamp().call()

            price_data = {
                'symbol': symbol,
                'price': latest_price / 10**8,  # Adjust for decimals
                'timestamp': latest_timestamp,
                'source': 'Flare Price Feed',
                'contract_address': contract_address
            }

            self._set_cache_data(cache_key, price_data)
            return price_data

        except Exception as e:
            logger.error(f"Error fetching price data for {symbol}: {e}")
            return None

    def standardize_metadata(self, metadata: Dict) -> Dict:
        """Enhanced metadata standardization with validation"""
        required_fields = ['id', 'type', 'timestamp', 'source']
        
        # Ensure required fields exist
        for field in required_fields:
            if field not in metadata:
                metadata[field] = None
        
        standardized = {
            "id": str(metadata.get("id", "")),
            "type": metadata.get("type", "unknown"),
            "timestamp": metadata.get("timestamp", time.time()),
            "source": metadata.get("source", "guardian_shield"),
            "details": metadata.get("details", {}),
            "incidents": metadata.get("incidents", []),
            "security_level": metadata.get("security_level", "low"),
            "validation_hash": hashlib.sha256(
                json.dumps(metadata, sort_keys=True).encode()
            ).hexdigest()
        }
        
        return standardized

    def get_spam_site_info(self, query_params=None) -> Optional[Dict]:
        """Enhanced spam site info retrieval with caching"""
        try:
            cache_key = self._cache_key('spam_sites', str(query_params or {}))
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return cached_data

            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            self._rate_limit()
            
            response = requests.get(
                f"{self.api_url}/spam-sites", 
                params=query_params, 
                headers=headers, 
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            if isinstance(data, dict):
                self._set_cache_data(cache_key, data)
                return data
            else:
                logger.warning("Unexpected response format from Flare spam-sites API.")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching spam site info: {e}")
            return None

    def update_dmer(self, dmer_data: Dict) -> bool:
        """Enhanced DMER update with validation"""
        try:
            # Validate DMER data
            required_fields = ['id', 'threat_type', 'severity', 'description']
            if not all(field in dmer_data for field in required_fields):
                logger.error("Invalid DMER data structure")
                return False

            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            self._rate_limit()
            
            # Add validation hash
            dmer_data['validation_hash'] = hashlib.sha256(
                json.dumps(dmer_data, sort_keys=True).encode()
            ).hexdigest()
            
            response = requests.post(
                f"{self.api_url}/dmer/update", 
                json=dmer_data, 
                headers=headers, 
                timeout=10
            )
            response.raise_for_status()
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error updating DMER in Flare: {e}")
            return False

    def store_metadata(self, metadata: Dict) -> bool:
        """Enhanced metadata storage with validation"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            standardized = self.standardize_metadata(metadata)
            self._rate_limit()
            
            response = requests.post(
                f"{self.api_url}/metadata", 
                json=standardized, 
                headers=headers, 
                timeout=10
            )
            response.raise_for_status()
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error storing metadata in Flare: {e}")
            return False

    def get_state_connector_data(self, query_params=None) -> Optional[Dict]:
        """Enhanced state connector data retrieval"""
        try:
            cache_key = self._cache_key('state_connector', str(query_params or {}))
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return cached_data

            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            self._rate_limit()
            
            response = requests.get(
                f"{self.api_url}/state-connector", 
                params=query_params, 
                headers=headers, 
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            if isinstance(data, dict):
                self._set_cache_data(cache_key, data)
                return data
            else:
                logger.warning("Unexpected response format from Flare state-connector API.")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching state connector data: {e}")
            return None

    def verify_external_proof(self, proof_data: Dict) -> bool:
        """Enhanced external proof verification"""
        try:
            # Validate proof data structure
            required_fields = ['proof_hash', 'source', 'timestamp']
            if not all(field in proof_data for field in required_fields):
                logger.error("Invalid proof data structure")
                return False

            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            self._rate_limit()
            
            response = requests.post(
                f"{self.api_url}/state-connector/verify", 
                json=proof_data, 
                headers=headers, 
                timeout=10
            )
            response.raise_for_status()
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error verifying external proof in Flare: {e}")
            return False

    def get_network_metrics(self) -> Optional[Dict]:
        """Get comprehensive Flare network metrics"""
        try:
            cache_key = self._cache_key('network_metrics', '')
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return cached_data

            self._rate_limit()

            # Get basic network info
            latest_block = self.web3.eth.get_block('latest')
            block_number = latest_block['number']
            gas_price = self.web3.eth.gas_price
            
            # Calculate network health metrics
            previous_block = self.web3.eth.get_block(block_number - 1)
            block_time = latest_block['timestamp'] - previous_block['timestamp']
            
            metrics = {
                'block_number': block_number,
                'gas_price': self.web3.from_wei(gas_price, 'gwei'),
                'block_time': block_time,
                'transaction_count': len(latest_block['transactions']),
                'network_id': self.web3.net.version,
                'is_connected': self.web3.is_connected(),
                'timestamp': time.time()
            }

            self._set_cache_data(cache_key, metrics)
            return metrics

        except Exception as e:
            logger.error(f"Error getting network metrics: {e}")
            return None

    def submit_threat_intelligence(self, threat_data: Dict) -> Optional[str]:
        """Submit threat intelligence to Flare blockchain"""
        try:
            if not self.threat_contract_address or not self.private_key:
                logger.error("Contract address or private key not configured")
                return None

            # Validate threat data structure
            required_fields = ['threat_type', 'severity', 'description', 'timestamp']
            if not all(field in threat_data for field in required_fields):
                logger.error("Invalid threat data structure")
                return None

            self._rate_limit()

            # Get account from private key
            account = self.web3.eth.account.from_key(self.private_key)
            
            # Prepare transaction data
            threat_hash = hashlib.sha256(json.dumps(threat_data, sort_keys=True).encode()).hexdigest()
            
            # Simplified contract ABI for threat submission
            threat_contract_abi = [
                {
                    "inputs": [
                        {"internalType": "string", "name": "_threatHash", "type": "string"},
                        {"internalType": "uint8", "name": "_severity", "type": "uint8"},
                        {"internalType": "string", "name": "_description", "type": "string"}
                    ],
                    "name": "submitThreat",
                    "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                    "stateMutability": "nonpayable",
                    "type": "function"
                }
            ]

            contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(self.threat_contract_address),
                abi=threat_contract_abi
            )

            # Build transaction
            transaction = contract.functions.submitThreat(
                threat_hash,
                min(max(threat_data['severity'], 1), 10),  # Ensure severity is 1-10
                threat_data['description'][:255]  # Limit description length
            ).build_transaction({
                'from': account.address,
                'nonce': self.web3.eth.get_transaction_count(account.address),
                'gas': 200000,
                'gasPrice': self.web3.to_wei('20', 'gwei')
            })

            # Sign and send transaction
            signed_txn = self.web3.eth.account.sign_transaction(transaction, self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            logger.info(f"Threat intelligence submitted with transaction hash: {tx_hash.hex()}")
            return tx_hash.hex()

        except Exception as e:
            logger.error(f"Error submitting threat intelligence: {e}")
            return None

    def run_integration_test(self) -> Dict:
        """Comprehensive integration test"""
        test_results = {
            'timestamp': time.time(),
            'tests': {}
        }

        # Test network connection
        try:
            test_results['tests']['network_connection'] = {
                'passed': self.web3.is_connected(),
                'details': f"Connected to {self.api_url}"
            }
        except Exception as e:
            test_results['tests']['network_connection'] = {
                'passed': False,
                'error': str(e)
            }

        # Test price data retrieval
        try:
            price_data = self.get_price_data('ETH')
            test_results['tests']['price_data'] = {
                'passed': price_data is not None,
                'details': price_data
            }
        except Exception as e:
            test_results['tests']['price_data'] = {
                'passed': False,
                'error': str(e)
            }

        # Test network metrics
        try:
            metrics = self.get_network_metrics()
            test_results['tests']['network_metrics'] = {
                'passed': metrics is not None,
                'details': metrics
            }
        except Exception as e:
            test_results['tests']['network_metrics'] = {
                'passed': False,
                'error': str(e)
            }

        return test_results

# Legacy compatibility
class FlareIntegration(FlareIntegrationAgent):
    """Legacy class for backward compatibility"""
    pass
