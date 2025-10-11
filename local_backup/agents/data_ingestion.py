"""
data_ingestion.py: Secure modules and functions for ingesting external threat intelligence, open datasets, and APIs for GuardianShield agents.
"""
import json
import os
import time
import logging
from typing import Dict, List, Optional, Any

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests not available, HTTP features disabled")

try:
    from dotenv import load_dotenv
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("Warning: python-dotenv not available")

# Setup secure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataIngestionAgent:
    """Enhanced data ingestion agent with autonomous source discovery"""
    
    def __init__(self):
        self.name = "DataIngestionAgent"
        
    def autonomous_cycle(self):
        """Run autonomous data ingestion cycle"""
        pass

# Legacy class for backward compatibility
class DataIngestion:
    def __init__(self):
        self.sources = {
            "abuseipdb": "https://api.abuseipdb.com/api/v2/blacklist",
            "cryptoscamdb": "https://api.cryptoscamdb.org/v1/addresses",
            "phishstats": "https://phishstats.info:2096/api/phishing",
            "virustotal": "https://www.virustotal.com/api/v3/files",
            "otx_alienvault": "https://otx.alienvault.com/api/v1/indicators/export",
            "urlhaus": "https://urlhaus-api.abuse.ch/v1/urls/recent/",
            "chainabuse": "https://api.chainabuse.com/api/v1/reports",
            "bitcoinabuse": "https://www.bitcoinabuse.com/api/reports/check",
        }
        # Secure API key handling
        self.headers = {
            "abuseipdb": {"Key": os.getenv("ABUSEIPDB_API_KEY", "")},
            "virustotal": {"x-apikey": os.getenv("VIRUSTOTAL_API_KEY", "")},
        }
        self.rate_limits = {
            "abuseipdb": {"calls": 0, "reset_time": 0, "limit": 1000},
            "virustotal": {"calls": 0, "reset_time": 0, "limit": 500},
        }
        self.session = requests.Session()
        self.session.timeout = 30

    def secure_api_call(self, source: str, url: str, headers: Dict = None, params: Dict = None, retries: int = 3) -> Optional[Dict]:
        """
        Secure API call with rate limiting, retry logic, and error handling
        """
        if not self.check_rate_limit(source):
            logger.warning(f"Rate limit exceeded for {source}")
            return None
            
        for attempt in range(retries):
            try:
                response = self.session.get(
                    url, 
                    headers=headers or {}, 
                    params=params or {},
                    timeout=30,
                    verify=True  # SSL verification
                )
                response.raise_for_status()
                self.update_rate_limit(source)
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logger.error(f"API call failed for {source} (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
        return None

    def check_rate_limit(self, source: str) -> bool:
        """Check if we're within rate limits"""
        if source not in self.rate_limits:
            return True
            
        limit_info = self.rate_limits[source]
        if time.time() > limit_info["reset_time"]:
            limit_info["calls"] = 0
            limit_info["reset_time"] = time.time() + 3600  # Reset hourly
            
        return limit_info["calls"] < limit_info["limit"]

    def update_rate_limit(self, source: str):
        """Update rate limit counters"""
        if source in self.rate_limits:
            self.rate_limits[source]["calls"] += 1

    def fetch_threats(self, source: str) -> List[Dict]:
        """Fetch threats from a specific source"""
        if source == "abuseipdb":
            return self.fetch_abuseipdb_blacklist()
        elif source == "cryptoscamdb":
            return self.fetch_cryptoscamdb_addresses()
        elif source == "phishstats":
            return self.fetch_phishstats()
        elif source == "urlhaus":
            return self.fetch_urlhaus()
        elif source == "chainabuse":
            return self.fetch_chainabuse()
        else:
            logger.warning(f"Unknown source: {source}")
            return []

    def fetch_incidents(self, threat: Dict) -> List[Dict]:
        """Fetch incidents related to a specific threat"""
        # This would fetch historical incidents for the threat
        # Placeholder implementation
        return []
    def fetch_abuseipdb_blacklist(self) -> Optional[Dict]:
        """Securely fetch AbuseIPDB blacklist"""
        headers = self.headers.get("abuseipdb", {})
        if not headers.get("Key"):
            logger.warning("AbuseIPDB API key not configured")
            return None
            
        return self.secure_api_call("abuseipdb", self.sources["abuseipdb"], headers)

    def fetch_cryptoscamdb_addresses(self) -> Optional[Dict]:
        """Securely fetch CryptoScamDB addresses"""
        return self.secure_api_call("cryptoscamdb", self.sources["cryptoscamdb"])

    def fetch_phishstats(self) -> Optional[Dict]:
        """Securely fetch PhishStats data"""
        return self.secure_api_call("phishstats", self.sources["phishstats"])

    def fetch_virustotal(self, file_hash: str) -> Optional[Dict]:
        """Securely fetch VirusTotal data"""
        if not file_hash or len(file_hash) not in [32, 40, 64]:  # MD5, SHA1, SHA256
            logger.error("Invalid file hash provided")
            return None
            
        headers = self.headers.get("virustotal", {})
        if not headers.get("x-apikey"):
            logger.warning("VirusTotal API key not configured")
            return None
            
        url = f"{self.sources['virustotal']}/{file_hash}"
        return self.secure_api_call("virustotal", url, headers)

    def fetch_urlhaus(self) -> Optional[Dict]:
        """Securely fetch URLhaus data"""
        return self.secure_api_call("urlhaus", self.sources["urlhaus"], method="POST")

    def fetch_chainabuse(self) -> Optional[Dict]:
        """Securely fetch ChainAbuse data"""
        return self.secure_api_call("chainabuse", self.sources["chainabuse"])

    def fetch_bitcoinabuse(self, address: str) -> Optional[Dict]:
        """Securely fetch BitcoinAbuse data"""
        if not address:
            logger.error("No address provided")
            return None
            
        api_key = os.getenv("BITCOINABUSE_API_KEY", "")
        if not api_key:
            logger.warning("BitcoinAbuse API key not configured")
            return None
            
        params = {"address": address, "api_token": api_key}
        return self.secure_api_call("bitcoinabuse", self.sources["bitcoinabuse"], params=params)

    def aggregate_all(self) -> Dict[str, Any]:
        """Securely aggregate data from all sources"""
        logger.info("Starting secure threat intelligence aggregation...")
        
        data = {}
        for source in self.sources.keys():
            try:
                if source == "virustotal":
                    # Skip VirusTotal without a specific hash
                    continue
                elif source == "bitcoinabuse":
                    # Skip BitcoinAbuse without a specific address
                    continue
                else:
                    result = getattr(self, f"fetch_{source}")()
                    if result:
                        data[source] = result
                        logger.info(f"Successfully fetched data from {source}")
                    else:
                        logger.warning(f"No data retrieved from {source}")
                        
            except Exception as e:
                logger.error(f"Error fetching from {source}: {e}")
                
        # Secure storage with backup
        try:
            with open("knowledge_base.json", "w") as f:
                json.dump(data, f, indent=2)
            
            # Create backup
            backup_filename = f"knowledge_base_backup_{int(time.time())}.json"
            with open(backup_filename, "w") as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Data saved to knowledge_base.json and {backup_filename}")
            
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            
        return data

if __name__ == "__main__":
    ingestion = DataIngestion()
    print("Fetching and aggregating threat intelligence...")
    result = ingestion.aggregate_all()
    print("Data saved to knowledge_base.json.")
