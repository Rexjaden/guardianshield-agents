"""
dmer_monitor_agent.py: Enhanced DMER (Decentralized Malicious Entity Registry) monitoring with recursive improvement and Web3 threat intelligence.
"""
import time
import json
import hashlib
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import os

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

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    print("Warning: beautifulsoup4 not available, web scraping disabled")

import re

# Load environment variables
if DOTENV_AVAILABLE:
    load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DmerMonitorAgent:
    """Enhanced DMER monitoring agent with autonomous threat hunting"""
    
    def __init__(self):
        self.name = "DmerMonitorAgent"
        
    def autonomous_cycle(self):
        """Run autonomous monitoring cycle"""
        pass

# Legacy class for backward compatibility
class DMERMonitorAgent:
    def __init__(self, name: str = "DMER_Monitor", flare_api_url: str = None, flare_api_key: str = None):
        self.name = name
        self.registry_url = os.getenv('DMER_REGISTRY_URL', 'https://api.guardianshield.network/dmer')
        self.api_key = os.getenv('DMER_API_KEY')
        
        # Initialize Flare integration
        if flare_api_url or flare_api_key:
            from agents.flare_integration import FlareIntegrationAgent
            self.flare = FlareIntegrationAgent(flare_api_url, flare_api_key)
        else:
            self.flare = None
        
        self.local_cache = {}
        self.cache_timeout = int(os.getenv('DMER_CACHE_TIMEOUT', '3600'))  # 1 hour default
        self.known_entities = set()
        self.threat_levels = {}
        self.monitoring_stats = {
            'total_checks': 0,
            'threats_detected': 0,
            'false_positives': 0,
            'cache_hits': 0,
            'api_errors': 0,
            'web_searches': 0,
            'threats_ingested': 0
        }
        self.rate_limit_delay = float(os.getenv('DMER_RATE_LIMIT', '1.0'))
        self.last_request_time = 0
        self.improvement_threshold = 0.8
        self.action_log = []

        # Initialize NLP if available
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
        except (ImportError, OSError):
            self.nlp = None
            logger.warning("spaCy not available. NLP features will be limited.")

    def _rate_limit(self):
        """Implement rate limiting to avoid overwhelming APIs"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()

    def _generate_cache_key(self, entity_id: str) -> str:
        """Generate a cache key for an entity"""
        return hashlib.md5(f"dmer_entity_{entity_id}".encode()).hexdigest()

    def _is_cache_valid(self, timestamp: float) -> bool:
        """Check if cached data is still valid"""
        return time.time() - timestamp < self.cache_timeout

    def _get_cached_entity(self, entity_id: str) -> Optional[Dict]:
        """Retrieve entity from cache if valid"""
        cache_key = self._generate_cache_key(entity_id)
        if cache_key in self.local_cache:
            data, timestamp = self.local_cache[cache_key]
            if self._is_cache_valid(timestamp):
                self.monitoring_stats['cache_hits'] += 1
                return data
            else:
                del self.local_cache[cache_key]
        return None

    def _cache_entity(self, entity_id: str, data: Dict):
        """Cache entity data with timestamp"""
        cache_key = self._generate_cache_key(entity_id)
        self.local_cache[cache_key] = (data, time.time())

    def log_action(self, action_type: str, description: str):
        """Log actions for monitoring and improvement"""
        log_entry = {
            'timestamp': time.time(),
            'action_type': action_type,
            'description': description,
            'agent': self.name
        }
        self.action_log.append(log_entry)
        
        # Keep only last 1000 entries
        if len(self.action_log) > 1000:
            self.action_log = self.action_log[-1000:]
        
        logger.info(f"[{self.name}] {action_type}: {description}")

    def query_entity(self, entity_id: str) -> Optional[Dict]:
        """Enhanced entity query with caching and error handling"""
        try:
            # Check cache first
            cached_data = self._get_cached_entity(entity_id)
            if cached_data:
                return cached_data

            self._rate_limit()
            self.monitoring_stats['total_checks'] += 1

            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            headers['Content-Type'] = 'application/json'

            response = requests.get(
                f"{self.registry_url}/entity/{entity_id}",
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                entity_data = response.json()
                
                # Validate response structure
                if not isinstance(entity_data, dict):
                    logger.error(f"Invalid response format for entity {entity_id}")
                    return None
                
                # Enhance entity data with metadata
                entity_data['query_timestamp'] = time.time()
                entity_data['source'] = 'dmer_registry'
                
                # Cache the result
                self._cache_entity(entity_id, entity_data)
                
                # Update known entities
                self.known_entities.add(entity_id)
                
                # Update threat level if present
                if 'threat_level' in entity_data:
                    self.threat_levels[entity_id] = entity_data['threat_level']
                
                return entity_data
                
            elif response.status_code == 404:
                logger.info(f"Entity {entity_id} not found in DMER registry")
                return None
            else:
                logger.error(f"DMER API error {response.status_code}: {response.text}")
                self.monitoring_stats['api_errors'] += 1
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error querying DMER for entity {entity_id}: {e}")
            self.monitoring_stats['api_errors'] += 1
            return None
        except Exception as e:
            logger.error(f"Unexpected error querying DMER for entity {entity_id}: {e}")
            return None

    def web_search_and_ingest_web3_threats(self):
        """Search the web for Web3 threats, scams, and techniques; store in DMER"""
        search_terms = [
            "web3 scam database",
            "address poisoning techniques",
            "web3 threat intelligence", 
            "crypto scam list",
            "blockchain scam addresses",
            "responsible individuals web3 scam",
            "web3 scam IP addresses",
            "defi exploit addresses",
            "nft scam techniques",
            "rug pull indicators"
        ]
        
        all_threats = []
        
        for term in search_terms:
            try:
                self._rate_limit()
                self.monitoring_stats['web_searches'] += 1
                
                # Use DuckDuckGo for search (no API key required)
                search_url = f"https://html.duckduckgo.com/html/?q={term.replace(' ', '+')}"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = requests.get(search_url, headers=headers, timeout=10)
                if response.status_code != 200:
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract search results
                for result in soup.find_all('div', class_='result')[:5]:  # Limit to top 5 results
                    try:
                        title_elem = result.find('a', class_='result__a')
                        title = title_elem.text.strip() if title_elem else ''
                        link = title_elem.get('href', '') if title_elem else ''
                        
                        snippet_elem = result.find('a', class_='result__snippet')
                        snippet = snippet_elem.text.strip() if snippet_elem else ''
                        
                        # Extract threat intelligence
                        threat_info = self._extract_threat_intelligence(title, snippet, link, term)
                        if threat_info:
                            all_threats.append(threat_info)
                            
                            # Store metadata in Flare if available
                            if self.flare:
                                self.flare.store_metadata(threat_info)
                        
                    except Exception as e:
                        logger.error(f"Error processing search result: {e}")
                        continue
                
            except Exception as e:
                logger.error(f"Error searching for term '{term}': {e}")
                continue
        
        # Update DMER registry with all threats
        if all_threats:
            self.update_dmer_registry(all_threats)
            self.monitoring_stats['threats_ingested'] += len(all_threats)
        
        self.log_action("web_search_and_ingest_web3_threats", 
                       f"Web-searched and ingested {len(all_threats)} web3 threats")

    def _extract_threat_intelligence(self, title: str, snippet: str, link: str, search_term: str) -> Optional[Dict]:
        """Extract threat intelligence from web content using NLP and regex"""
        try:
            full_text = f"{title} {snippet}".lower()
            
            # Extract IP addresses
            ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', full_text)
            
            # Extract cryptocurrency addresses (basic patterns)
            eth_addresses = re.findall(r'\b0x[a-fA-F0-9]{40}\b', full_text)
            btc_addresses = re.findall(r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b', full_text)
            
            # Extract techniques using keywords
            technique_keywords = [
                "address poisoning", "phishing", "rug pull", "dusting", "scam", 
                "exploit", "honeypot", "flash loan", "sandwich attack", "frontrunning"
            ]
            techniques = [kw for kw in technique_keywords if kw in full_text]
            
            # Extract entities using NLP if available
            individuals = []
            organizations = []
            
            if self.nlp:
                try:
                    doc = self.nlp(snippet)
                    for ent in doc.ents:
                        if ent.label_ == "PERSON":
                            individuals.append(ent.text)
                        elif ent.label_ == "ORG":
                            organizations.append(ent.text)
                except Exception as e:
                    logger.debug(f"NLP processing error: {e}")
            
            # Only create threat info if we found something useful
            if ips or eth_addresses or btc_addresses or techniques or individuals:
                threat_info = {
                    "id": hashlib.md5(f"{link}_{search_term}".encode()).hexdigest(),
                    "search_term": search_term,
                    "title": title,
                    "link": link,
                    "snippet": snippet,
                    "techniques": list(set(techniques)),
                    "individuals": list(set(individuals)),
                    "organizations": list(set(organizations)),
                    "ip_addresses": list(set(ips)),
                    "eth_addresses": list(set(eth_addresses)),
                    "btc_addresses": list(set(btc_addresses)),
                    "timestamp": time.time(),
                    "source": "web_search",
                    "type": "threat_intelligence"
                }
                return threat_info
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting threat intelligence: {e}")
            return None

    def update_dmer_registry(self, new_threats: List[Dict]):
        """Update DMER registry with new threats"""
        try:
            if not new_threats:
                return
            
            # Prepare threats for DMER format
            dmer_threats = []
            for threat in new_threats:
                dmer_threat = {
                    "entity_id": threat.get("id", hashlib.md5(str(threat).encode()).hexdigest()),
                    "threat_type": "web3_scam" if "scam" in threat.get("search_term", "") else "threat_intelligence",
                    "description": threat.get("title", "Web3 threat detected"),
                    "evidence": {
                        "source_url": threat.get("link"),
                        "techniques": threat.get("techniques", []),
                        "addresses": {
                            "ethereum": threat.get("eth_addresses", []),
                            "bitcoin": threat.get("btc_addresses", [])
                        },
                        "ip_addresses": threat.get("ip_addresses", []),
                        "entities": {
                            "individuals": threat.get("individuals", []),
                            "organizations": threat.get("organizations", [])
                        }
                    },
                    "severity": self._calculate_threat_severity(threat),
                    "timestamp": threat.get("timestamp", time.time())
                }
                dmer_threats.append(dmer_threat)
            
            # Submit to DMER registry
            for threat in dmer_threats:
                success = self.submit_entity(threat)
                if success:
                    self.monitoring_stats['threats_detected'] += 1
            
            # Update Flare if available
            if self.flare:
                self.flare.update_dmer({"threats": dmer_threats})
            
            self.log_action("update_dmer_registry", f"Added {len(dmer_threats)} threats to DMER")
            
        except Exception as e:
            logger.error(f"Error updating DMER registry: {e}")

    def _calculate_threat_severity(self, threat: Dict) -> int:
        """Calculate threat severity based on extracted intelligence"""
        severity = 1  # Base severity
        
        # Increase severity based on number of techniques
        severity += min(len(threat.get("techniques", [])), 3)
        
        # Increase severity if addresses are found
        if threat.get("eth_addresses") or threat.get("btc_addresses"):
            severity += 2
        
        # Increase severity if IP addresses are found
        if threat.get("ip_addresses"):
            severity += 1
        
        # Increase severity if individuals/organizations are identified
        if threat.get("individuals") or threat.get("organizations"):
            severity += 1
        
        # Check for high-risk keywords
        high_risk_keywords = ["rug pull", "exploit", "honeypot", "scam"]
        text = threat.get("title", "") + " " + threat.get("snippet", "")
        for keyword in high_risk_keywords:
            if keyword in text.lower():
                severity += 2
                break
        
        return min(severity, 10)  # Cap at 10

    def submit_entity(self, entity_data: Dict) -> bool:
        """Enhanced entity submission with validation"""
        try:
            # Validate required fields
            required_fields = ['entity_id', 'threat_type', 'description', 'evidence']
            if not all(field in entity_data for field in required_fields):
                logger.error("Missing required fields in entity data")
                return False
            
            # Add metadata
            entity_data['submission_timestamp'] = time.time()
            entity_data['submitter'] = os.getenv('GUARDIAN_AGENT_ID', 'guardian_shield_agent')
            entity_data['validation_hash'] = hashlib.sha256(
                json.dumps(entity_data, sort_keys=True).encode()
            ).hexdigest()
            
            self._rate_limit()
            
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            headers['Content-Type'] = 'application/json'
            
            response = requests.post(
                f"{self.registry_url}/entity",
                json=entity_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Successfully submitted entity: {entity_data['entity_id']}")
                
                # Update local tracking
                self.known_entities.add(entity_data['entity_id'])
                if 'severity' in entity_data:
                    self.threat_levels[entity_data['entity_id']] = entity_data['severity']
                
                return True
            else:
                logger.error(f"Failed to submit entity. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error submitting entity: {e}")
            return False

    def ingest_and_update_registry(self):
        """Comprehensive threat ingestion from multiple sources"""
        try:
            # Import data ingestion module
            from agents.data_ingestion import DataIngestionAgent
            data_ingestor = DataIngestionAgent()
            
            all_threats = []
            
            # Get available sources
            sources = data_ingestor.get_available_sources()
            
            for source in sources:
                try:
                    # Fetch threats from each source
                    threats = data_ingestor.fetch_from_source(source)
                    
                    for threat in threats:
                        # Fetch additional incident data
                        incidents = data_ingestor.get_related_incidents(threat.get('id', ''))
                        
                        threat_info = {
                            "id": threat.get("id") or hashlib.md5(str(threat).encode()).hexdigest(),
                            "source": source,
                            "identifier": threat.get("identifier"),
                            "entity_type": threat.get("entity_type", "unknown"),
                            "threat_type": threat.get("threat_type", "general"),
                            "description": threat.get("description", ""),
                            "details": threat,
                            "incidents": incidents,
                            "timestamp": time.time()
                        }
                        all_threats.append(threat_info)
                        
                        # Store metadata in Flare if available
                        if self.flare:
                            self.flare.store_metadata(threat_info)
                
                except Exception as e:
                    logger.error(f"Error ingesting from source {source}: {e}")
                    continue
            
            # Update DMER registry with all threats
            if all_threats:
                self.update_dmer_registry(all_threats)
            
            self.log_action("ingest_and_update_registry", 
                           f"Ingested and stored {len(all_threats)} threats from {len(sources)} sources")
            
        except Exception as e:
            logger.error(f"Error in comprehensive ingestion: {e}")

    def monitor(self, dmer_data: Dict = None) -> Dict:
        """Enhanced monitoring with Flare integration"""
        try:
            # Fetch latest data from Flare if available
            latest_data = {}
            if self.flare:
                latest_data = self.flare.get_state_connector_data()
            
            # Combine with provided DMER data
            if dmer_data:
                latest_data.update(dmer_data)
            
            # Perform monitoring analysis
            monitoring_result = {
                'timestamp': time.time(),
                'agent': self.name,
                'data_sources': ['flare', 'dmer'] if self.flare else ['dmer'],
                'entities_monitored': len(self.known_entities),
                'threat_levels': self.threat_levels,
                'latest_data': latest_data,
                'stats': self.monitoring_stats
            }
            
            return monitoring_result
            
        except Exception as e:
            logger.error(f"Error in monitoring: {e}")
            return {'error': str(e)}

    def report(self) -> Dict:
        """Generate comprehensive monitoring report"""
        try:
            report_metadata = {
                "id": f"report_{self.name}_{int(time.time())}",
                "type": "dmer_report",
                "timestamp": time.time(),
                "source": self.name,
                "details": {
                    "monitoring_stats": self.monitoring_stats,
                    "known_entities": len(self.known_entities),
                    "threat_levels": self.threat_levels,
                    "recent_actions": self.action_log[-10:] if self.action_log else []
                },
                "incidents": []
            }
            
            # Store report in Flare if available
            if self.flare:
                self.flare.store_metadata(report_metadata)
            
            self.log_action("report", "Generated monitoring report")
            return report_metadata
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {'error': str(e)}

    def recursive_improve_monitoring(self):
        """Recursively improve monitoring based on performance metrics"""
        try:
            total_checks = self.monitoring_stats['total_checks']
            api_errors = self.monitoring_stats['api_errors']
            
            if total_checks == 0:
                return
            
            error_rate = api_errors / total_checks
            cache_hit_rate = self.monitoring_stats['cache_hits'] / total_checks
            
            logger.info(f"DMER Monitor Performance - Error Rate: {error_rate:.2%}, Cache Hit Rate: {cache_hit_rate:.2%}")
            
            # Adjust cache timeout based on error rate
            if error_rate > 0.1:  # More than 10% error rate
                self.cache_timeout = min(self.cache_timeout * 1.5, 7200)  # Increase cache timeout, max 2 hours
                logger.info(f"High error rate detected. Increased cache timeout to {self.cache_timeout} seconds")
            
            # Adjust rate limiting based on errors
            if error_rate > 0.05:  # More than 5% error rate
                self.rate_limit_delay = min(self.rate_limit_delay * 1.2, 5.0)  # Increase delay, max 5 seconds
                logger.info(f"Increased rate limit delay to {self.rate_limit_delay} seconds")
            elif error_rate < 0.01 and self.rate_limit_delay > 0.5:  # Less than 1% error rate
                self.rate_limit_delay = max(self.rate_limit_delay * 0.9, 0.5)  # Decrease delay, min 0.5 seconds
                logger.info(f"Decreased rate limit delay to {self.rate_limit_delay} seconds")
            
        except Exception as e:
            logger.error(f"Error in recursive improvement: {e}")

# Legacy compatibility
class DMERMonitor(DMERMonitorAgent):
    """Legacy class for backward compatibility"""
    pass
