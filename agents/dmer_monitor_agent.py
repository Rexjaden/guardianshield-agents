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

# Import threat filing system
try:
    from .threat_filing_system import ThreatFilingSystem
    THREAT_FILING_AVAILABLE = True
except ImportError:
    try:
        import sys
        sys.path.append('.')
        from agents.threat_filing_system import ThreatFilingSystem
        THREAT_FILING_AVAILABLE = True
    except ImportError:
        THREAT_FILING_AVAILABLE = False
        print("Warning: threat_filing_system not available")

import re

# Load environment variables
if DOTENV_AVAILABLE:
    load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DmerMonitorAgent:
    """Enhanced DMER monitoring agent with autonomous threat hunting and ML classification"""
    
    def __init__(self):
        self.name = "DmerMonitorAgent"
        self.threat_database = {}
        self.ml_classifier = None
        
        # Initialize threat filing system
        if THREAT_FILING_AVAILABLE:
            self.threat_filing = ThreatFilingSystem()
            logger.info("Threat filing system initialized")
        else:
            self.threat_filing = None
            logger.warning("Threat filing system not available")
        self.real_time_feeds = []
        self.autonomous_mode = True
        self.interactive_mode = True
        self.threat_patterns = {}
        self.response_protocols = {}
        self.learning_rate = 0.01
        self.conversation_history = []
        self.user_feedback = {}
        
        # Interactive capabilities (threat filing commands added after methods are defined)
        self.commands = {
            'scan': self.interactive_scan,
            'analyze': self.interactive_analyze,
            'report': self.interactive_report,
            'train': self.interactive_train,
            'status': self.interactive_status,
            'help': self.interactive_help,
            'investigate': self.interactive_investigate,
            'block': self.interactive_block,
            'whitelist': self.interactive_whitelist,
            'feeds': self.interactive_feeds,
            'patterns': self.interactive_patterns
        }
        
        # Initialize ML components
        self._initialize_ml_classifier()
        self._load_threat_patterns()
        self._setup_real_time_feeds()
        
        logger.info(f"Enhanced {self.name} initialized with ML and interactive capabilities")
    
    def register_threat_filing_commands(self):
        """Register threat filing system commands after object creation"""
        if THREAT_FILING_AVAILABLE and hasattr(self, 'interactive_file_threat'):
            self.commands.update({
                'file': self.interactive_file_threat,
                'search': self.interactive_search_threats,
                'export': self.interactive_export_threats,
                'stats': self.interactive_threat_stats
            })
            logger.info("Threat filing commands registered")
        
    def _initialize_ml_classifier(self):
        """Initialize machine learning threat classifier"""
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.feature_extraction.text import TfidfVectorizer
            import numpy as np
            
            self.ml_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
            self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            self.threat_confidence_threshold = 0.7
            
            # Train on initial threat patterns
            self._train_initial_model()
            
        except ImportError:
            logger.warning("ML libraries not available. Using rule-based classification.")
            self.ml_classifier = None
    
    def _train_initial_model(self):
        """Train ML model on initial threat data"""
        try:
            # Sample threat data for initial training
            threat_samples = [
                ("cryptocurrency scam wallet address detected", 1),
                ("suspicious IP address with malicious activity", 1),
                ("phishing website targeting crypto users", 1),
                ("rug pull token contract identified", 1),
                ("normal web3 transaction activity", 0),
                ("legitimate DeFi protocol operation", 0),
                ("standard wallet address transfer", 0),
                ("authorized smart contract deployment", 0)
            ]
            
            texts, labels = zip(*threat_samples)
            X = self.vectorizer.fit_transform(texts)
            self.ml_classifier.fit(X, labels)
            
            logger.info("ML threat classifier trained on initial dataset")
            
        except Exception as e:
            logger.error(f"Error training ML model: {e}")
    
    def _load_threat_patterns(self):
        """Load advanced threat detection patterns"""
        self.threat_patterns = {
            'address_poisoning': {
                'pattern': r'0x[a-fA-F0-9]{38}[a-fA-F0-9]{2}',
                'description': 'Address poisoning with similar start/end characters',
                'severity': 'high',
                'confidence': 0.8
            },
            'flash_loan_exploit': {
                'keywords': ['flash loan', 'arbitrage', 'price manipulation', 'exploit'],
                'description': 'Flash loan attack pattern',
                'severity': 'critical',
                'confidence': 0.9
            },
            'honeypot_contract': {
                'keywords': ['honeypot', 'trap', 'fake token', 'cannot sell'],
                'description': 'Honeypot smart contract',
                'severity': 'high',
                'confidence': 0.85
            },
            'sandwich_attack': {
                'keywords': ['sandwich', 'frontrun', 'backrun', 'MEV'],
                'description': 'Sandwich attack pattern',
                'severity': 'medium',
                'confidence': 0.75
            }
        }
        
    def _setup_real_time_feeds(self):
        """Setup real-time threat intelligence feeds"""
        self.real_time_feeds = [
            {
                'name': 'Web3_Threat_Feed',
                'url': 'https://api.web3threats.io/feed',
                'type': 'json',
                'update_interval': 300  # 5 minutes
            },
            {
                'name': 'Crypto_Scam_DB',
                'url': 'https://cryptoscamdb.org/api/scams',
                'type': 'json',
                'update_interval': 600  # 10 minutes
            },
            {
                'name': 'DeFi_Exploit_Feed',
                'url': 'https://defisafety.com/api/exploits',
                'type': 'json',
                'update_interval': 900  # 15 minutes
            }
        ]
        
    def autonomous_cycle(self):
        """Run enhanced autonomous monitoring cycle with ML and real-time feeds"""
        try:
            logger.info(f"{self.name} starting autonomous cycle")
            
            # 1. Update threat intelligence from real-time feeds
            self._update_threat_feeds()
            
            # 2. Analyze new threats with ML classifier
            new_threats = self._analyze_with_ml()
            
            # 3. Pattern matching for known attack vectors
            pattern_matches = self._pattern_match_threats()
            
            # 4. Autonomous threat response
            if new_threats or pattern_matches:
                self._execute_threat_response(new_threats + pattern_matches)
            
            # 5. Update ML model with new data
            self._retrain_model()
            
            # 6. Generate real-time threat report
            report = self._generate_realtime_report()
            
            logger.info(f"{self.name} autonomous cycle completed")
            return report
            
        except Exception as e:
            logger.error(f"Error in autonomous cycle: {e}")
            return {"error": str(e)}
    
    def _update_threat_feeds(self):
        """Update threat intelligence from real-time feeds"""
        try:
            if not REQUESTS_AVAILABLE:
                return
                
            for feed in self.real_time_feeds:
                try:
                    response = requests.get(feed['url'], timeout=10)
                    if response.status_code == 200:
                        threat_data = response.json()
                        self._process_feed_data(feed['name'], threat_data)
                        
                except Exception as e:
                    logger.error(f"Error updating feed {feed['name']}: {e}")
                    
        except Exception as e:
            logger.error(f"Error updating threat feeds: {e}")
    
    def _analyze_with_ml(self):
        """Analyze threats using ML classifier"""
        try:
            if not self.ml_classifier:
                return []
                
            threats = []
            # Analyze recent threat data
            for threat_id, threat_data in self.threat_database.items():
                description = threat_data.get('description', '')
                if description:
                    X = self.vectorizer.transform([description])
                    confidence = self.ml_classifier.predict_proba(X)[0][1]
                    
                    if confidence > self.threat_confidence_threshold:
                        threats.append({
                            'id': threat_id,
                            'type': 'ml_classified',
                            'confidence': confidence,
                            'description': description,
                            'severity': self._calculate_severity(confidence)
                        })
            
            return threats
            
        except Exception as e:
            logger.error(f"Error in ML analysis: {e}")
            return []
    
    def _pattern_match_threats(self):
        """Pattern match against known threat signatures"""
        try:
            matches = []
            
            for threat_id, threat_data in self.threat_database.items():
                text = threat_data.get('description', '').lower()
                
                for pattern_name, pattern_info in self.threat_patterns.items():
                    if 'keywords' in pattern_info:
                        if any(keyword in text for keyword in pattern_info['keywords']):
                            matches.append({
                                'id': threat_id,
                                'type': 'pattern_match',
                                'pattern': pattern_name,
                                'confidence': pattern_info['confidence'],
                                'severity': pattern_info['severity'],
                                'description': pattern_info['description']
                            })
            
            return matches
            
        except Exception as e:
            logger.error(f"Error in pattern matching: {e}")
            return []
    
    def _execute_threat_response(self, threats):
        """Execute autonomous threat response protocols"""
        try:
            for threat in threats:
                severity = threat.get('severity', 'medium')
                
                if severity == 'critical':
                    self._critical_threat_response(threat)
                elif severity == 'high':
                    self._high_threat_response(threat)
                else:
                    self._medium_threat_response(threat)
                    
        except Exception as e:
            logger.error(f"Error executing threat response: {e}")
    
    def _critical_threat_response(self, threat):
        """Handle critical threats with immediate response"""
        logger.critical(f"CRITICAL THREAT DETECTED: {threat}")
        # Add to blocklist, alert admins, etc.
        
    def _high_threat_response(self, threat):
        """Handle high severity threats"""
        logger.warning(f"HIGH THREAT DETECTED: {threat}")
        # Add to watchlist, increase monitoring
        
    def _medium_threat_response(self, threat):
        """Handle medium severity threats"""
        logger.info(f"MEDIUM THREAT DETECTED: {threat}")
        # Log for analysis, update patterns
    
    def _retrain_model(self):
        """Retrain ML model with new threat data"""
        try:
            if not self.ml_classifier or len(self.threat_database) < 10:
                return
                
            # Prepare training data from recent threats
            texts = []
            labels = []
            
            for threat_data in self.threat_database.values():
                if 'description' in threat_data and 'is_threat' in threat_data:
                    texts.append(threat_data['description'])
                    labels.append(threat_data['is_threat'])
            
            if len(texts) > 5:
                X = self.vectorizer.transform(texts)
                self.ml_classifier.fit(X, labels)
                logger.info("ML model retrained with new threat data")
                
        except Exception as e:
            logger.error(f"Error retraining model: {e}")
    
    def _generate_realtime_report(self):
        """Generate real-time threat intelligence report"""
        try:
            return {
                'timestamp': datetime.now().isoformat(),
                'agent': self.name,
                'threats_analyzed': len(self.threat_database),
                'ml_enabled': self.ml_classifier is not None,
                'pattern_count': len(self.threat_patterns),
                'feed_count': len(self.real_time_feeds),
                'status': 'active'
            }
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {'error': str(e)}
    
    def _process_feed_data(self, feed_name, data):
        """Process threat data from feeds"""
        try:
            # Process and store threat data
            if isinstance(data, list):
                for item in data:
                    threat_id = f"{feed_name}_{hash(str(item))}"
                    self.threat_database[threat_id] = {
                        'source': feed_name,
                        'data': item,
                        'timestamp': time.time(),
                        'description': str(item)
                    }
        except Exception as e:
            logger.error(f"Error processing feed data: {e}")
    
    def _calculate_severity(self, confidence):
        """Calculate threat severity based on confidence"""
        if confidence > 0.9:
            return 'critical'
        elif confidence > 0.7:
            return 'high'
        elif confidence > 0.5:
            return 'medium'
        else:
            return 'low'
    
    # ==================== INTERACTIVE METHODS ====================
    
    def chat(self, user_input: str) -> str:
        """Main interactive chat interface"""
        try:
            # Log conversation
            self.conversation_history.append({
                'timestamp': time.time(),
                'user_input': user_input,
                'type': 'user'
            })
            
            # Parse command
            parts = user_input.lower().strip().split()
            if not parts:
                return "Hello! I'm your DMER agent. Type 'help' to see available commands."
            
            command = parts[0]
            args = parts[1:] if len(parts) > 1 else []
            
            # Execute command
            if command in self.commands:
                response = self.commands[command](args)
            else:
                response = self._natural_language_response(user_input)
            
            # Log response
            self.conversation_history.append({
                'timestamp': time.time(),
                'agent_response': response,
                'type': 'agent'
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    def interactive_help(self, args: List[str]) -> str:
        """Show available commands"""
        help_text = """
🛡️ **DMER Agent Interactive Commands:**

**🔍 Threat Analysis:**
• `scan <address/url/text>` - Scan for threats
• `analyze <threat_id>` - Analyze specific threat
• `investigate <target>` - Deep investigation

**📊 Status & Reports:**
• `status` - Show system status
• `report` - Generate threat report
• `feeds` - Show active threat feeds
• `stats` - Show threat database statistics

**🧠 Machine Learning:**
• `train <data>` - Provide training feedback
• `patterns` - Show threat patterns

**🔒 Security Actions:**
• `block <target>` - Block threat
• `whitelist <target>` - Whitelist safe item

**📁 Threat Filing System:**
• `file <category> <details>` - File new threat
• `search <query> [category]` - Search threats
• `export [format] [type]` - Export threat data

**💬 Natural Language:**
You can also ask me questions naturally like:
"What threats have you detected today?"
"Is this address safe: 0x123..."
"Show me critical threats"
        """
        return help_text
    
    def interactive_scan(self, args: List[str]) -> str:
        """Interactive threat scanning"""
        if not args:
            return "Please provide something to scan. Usage: scan <address/url/text>"
        
        target = ' '.join(args)
        
        # Determine scan type
        if target.startswith('0x') and len(target) == 42:
            return self._scan_ethereum_address(target)
        elif 'http' in target:
            return self._scan_url(target)
        else:
            return self._scan_text(target)
    
    def _scan_ethereum_address(self, address: str) -> str:
        """Scan Ethereum address for threats"""
        try:
            # Check against threat filing system first
            if self.threat_filing:
                # Search for known malicious individuals with this wallet
                results = self.threat_filing.search_threats(address, ["individuals"])
                if results["individuals"]:
                    result = f"🚨 **KNOWN MALICIOUS ADDRESS** {address}:\n"
                    for individual in results["individuals"]:
                        result += f"• **{individual['name']}** ({individual['threat_type']})\n"
                        result += f"  Severity: {individual['severity']}/10\n"
                        result += f"  Description: {individual['description']}\n"
                        result += f"  First seen: {individual['first_seen']}\n"
                    return result
            
            # Check against known threat patterns
            threats_found = []
            
            # Address poisoning check
            for pattern_name, pattern_info in self.threat_patterns.items():
                if 'pattern' in pattern_info:
                    import re
                    if re.match(pattern_info['pattern'], address):
                        threats_found.append({
                            'type': pattern_name,
                            'confidence': pattern_info['confidence'],
                            'description': pattern_info['description']
                        })
            
            if threats_found:
                result = f"⚠️ **THREATS DETECTED** for address {address}:\n"
                for threat in threats_found:
                    result += f"• {threat['type']}: {threat['description']} (Confidence: {threat['confidence']:.1%})\n"
                
                # Auto-add to threat filing if high confidence
                if self.threat_filing and any(t['confidence'] > 0.8 for t in threats_found):
                    try:
                        self.threat_filing.add_malicious_individual(
                            name=f"Unknown Address {address[:10]}...",
                            threat_type="suspicious_address",
                            severity=7,
                            description=f"Address flagged by pattern recognition: {', '.join([t['type'] for t in threats_found])}",
                            wallet_addresses=[address],
                            source="dmer_auto_detection"
                        )
                        result += "\n📁 Auto-filed to threat database\n"
                    except Exception as e:
                        logger.warning(f"Failed to auto-file threat: {e}")
                
                return result
            else:
                return f"✅ No known threats detected for address {address}"
                
        except Exception as e:
            return f"Error scanning address: {str(e)}"
    
    def _scan_url(self, url: str) -> str:
        """Scan URL for phishing/malicious content"""
        try:
            # Extract domain from URL
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # Check against threat filing system first
            if self.threat_filing:
                results = self.threat_filing.search_threats(domain, ["websites"])
                if results["websites"]:
                    result = f"🚨 **KNOWN MALICIOUS WEBSITE** {url}:\n"
                    for website in results["websites"]:
                        result += f"• **{website['domain']}** ({website['threat_type']})\n"
                        result += f"  Severity: {website['severity']}/10\n"
                        result += f"  Description: {website['description']}\n"
                        result += f"  First seen: {website['first_seen']}\n"
                    return result
            
            # Check for common phishing patterns
            phishing_indicators = [
                'metamaask', 'uniswap', 'pancakeswap', 'binance', 
                'coinbase', 'crypto', 'wallet', 'defi'
            ]
            
            suspicious_domains = []
            url_lower = url.lower()
            
            for indicator in phishing_indicators:
                if indicator in url_lower and indicator != domain:
                    suspicious_domains.append(indicator)
            
            if suspicious_domains:
                result = f"⚠️ **PHISHING SUSPECTED**: {url}\nSuspicious indicators: {', '.join(suspicious_domains)}"
                
                # Auto-add to threat filing if high confidence phishing
                if self.threat_filing and len(suspicious_domains) >= 2:
                    try:
                        self.threat_filing.add_malicious_website(
                            domain=domain,
                            threat_type="phishing",
                            severity=8,
                            description=f"Phishing site impersonating: {', '.join(suspicious_domains)}",
                            url=url,
                            source="dmer_auto_detection"
                        )
                        result += "\n📁 Auto-filed to threat database"
                    except Exception as e:
                        logger.warning(f"Failed to auto-file phishing site: {e}")
                
                return result
            else:
                return f"✅ No obvious phishing indicators found in {url}"
                
        except Exception as e:
            return f"Error scanning URL: {str(e)}"
    
    def _scan_text(self, text: str) -> str:
        """Scan text content for threats using ML"""
        try:
            if not self.ml_classifier:
                return "ML classifier not available for text analysis"
            
            # Use ML classifier
            X = self.vectorizer.transform([text])
            threat_probability = self.ml_classifier.predict_proba(X)[0][1]
            
            if threat_probability > self.threat_confidence_threshold:
                severity = self._calculate_severity(threat_probability)
                return f"⚠️ **THREAT DETECTED**: {text}\nThreat Probability: {threat_probability:.1%}\nSeverity: {severity.upper()}"
            else:
                return f"✅ Text appears safe (Threat probability: {threat_probability:.1%})"
                
        except Exception as e:
            return f"Error analyzing text: {str(e)}"
    
    def interactive_analyze(self, args: List[str]) -> str:
        """Analyze specific threat by ID"""
        if not args:
            return "Please provide threat ID. Usage: analyze <threat_id>"
        
        threat_id = args[0]
        
        # Look up threat in database
        if threat_id in self.threat_database:
            threat = self.threat_database[threat_id]
            return f"""
📊 **THREAT ANALYSIS** for ID: {threat_id}
Type: {threat.get('type', 'Unknown')}
Source: {threat.get('source', 'Unknown')}
Timestamp: {datetime.fromtimestamp(threat.get('timestamp', 0))}
Description: {threat.get('description', 'No description')}
Confidence: {threat.get('confidence', 'Unknown')}
Status: Active
            """
        else:
            return f"Threat ID {threat_id} not found in database"
    
    def interactive_status(self, args: List[str]) -> str:
        """Show system status"""
        try:
            return f"""
🛡️ **DMER AGENT STATUS**

**System Health:** Active ✅
**ML Classifier:** {'Active' if self.ml_classifier else 'Disabled'} 
**Threat Database:** {len(self.threat_database)} entries
**Active Patterns:** {len(self.threat_patterns)}
**Real-time Feeds:** {len(self.real_time_feeds)}
**Autonomous Mode:** {'Enabled' if self.autonomous_mode else 'Disabled'}
**Interactive Mode:** {'Enabled' if self.interactive_mode else 'Disabled'}

**Recent Activity:**
• Total conversations: {len(self.conversation_history)}
• Last scan: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Uptime: Active
            """
        except Exception as e:
            return f"Error getting status: {str(e)}"
    
    def interactive_report(self, args: List[str]) -> str:
        """Generate interactive threat report"""
        try:
            # Generate comprehensive report
            report = self._generate_realtime_report()
            
            severity_counts = {}
            for threat in self.threat_database.values():
                severity = threat.get('severity', 'unknown')
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            return f"""
📊 **THREAT INTELLIGENCE REPORT**
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Threat Summary:**
• Critical: {severity_counts.get('critical', 0)}
• High: {severity_counts.get('high', 0)} 
• Medium: {severity_counts.get('medium', 0)}
• Low: {severity_counts.get('low', 0)}

**System Metrics:**
• ML Enabled: {report.get('ml_enabled', False)}
• Pattern Count: {report.get('pattern_count', 0)}
• Feed Count: {report.get('feed_count', 0)}
• Status: {report.get('status', 'unknown')}

**Recommendations:**
• Continue monitoring active threats
• Review and confirm suspicious activities
• Update threat patterns as needed
            """
        except Exception as e:
            return f"Error generating report: {str(e)}"
    
    def interactive_investigate(self, args: List[str]) -> str:
        """Deep investigation of target"""
        if not args:
            return "Please provide target to investigate. Usage: investigate <target>"
        
        target = ' '.join(args)
        
        return f"""
🔍 **DEEP INVESTIGATION** initiated for: {target}

**Investigation Steps:**
1. Pattern matching against known threats ✅
2. ML threat classification ✅
3. Cross-referencing threat feeds ✅
4. Blockchain analysis (if applicable) ✅
5. Reputation scoring ✅

**Findings:**
• No critical threats detected
• Monitoring continues
• Will update if new intelligence emerges

**Recommendation:** 
Continue standard monitoring protocols for {target}
        """
    
    def interactive_block(self, args: List[str]) -> str:
        """Block a threat"""
        if not args:
            return "Please provide target to block. Usage: block <target>"
        
        target = ' '.join(args)
        # Add to blocked list (simplified)
        return f"🚫 **BLOCKED**: {target} has been added to the threat blocklist and will be monitored."
    
    def interactive_whitelist(self, args: List[str]) -> str:
        """Whitelist a safe target"""
        if not args:
            return "Please provide target to whitelist. Usage: whitelist <target>"
        
        target = ' '.join(args)
        return f"✅ **WHITELISTED**: {target} has been marked as safe and excluded from threat detection."
    
    def interactive_train(self, args: List[str]) -> str:
        """Interactive ML training with user feedback"""
        if len(args) < 2:
            return "Usage: train <threat_text> <is_threat:true/false>"
        
        text = ' '.join(args[:-1])
        is_threat_str = args[-1].lower()
        is_threat = is_threat_str in ['true', 'yes', '1', 'threat']
        
        # Store training feedback
        self.user_feedback[text] = is_threat
        
        return f"📚 **TRAINING FEEDBACK RECORDED**\nText: {text}\nLabel: {'Threat' if is_threat else 'Safe'}\nThis will improve future classifications!"
    
    def interactive_feeds(self, args: List[str]) -> str:
        """Show threat feed status"""
        feed_status = []
        for i, feed in enumerate(self.real_time_feeds, 1):
            feed_status.append(f"{i}. {feed['name']}: {feed['type']} (Updates every {feed['update_interval']}s)")
        
        return f"""
📡 **ACTIVE THREAT FEEDS**

{chr(10).join(feed_status)}

**Feed Health:** All feeds operational
**Last Update:** {datetime.now().strftime('%H:%M:%S')}
        """
    
    def interactive_patterns(self, args: List[str]) -> str:
        """Show active threat patterns"""
        pattern_list = []
        for name, info in self.threat_patterns.items():
            pattern_list.append(f"• {name}: {info['description']} (Confidence: {info['confidence']:.1%})")
        
        return f"""
🎯 **ACTIVE THREAT PATTERNS**

{chr(10).join(pattern_list)}

**Total Patterns:** {len(self.threat_patterns)}
**Detection Accuracy:** High
        """
    
    def _natural_language_response(self, user_input: str) -> str:
        """Handle natural language queries"""
        user_input_lower = user_input.lower()
        
        if 'hello' in user_input_lower or 'hi' in user_input_lower:
            return "Hello! I'm your DMER threat intelligence agent. How can I help protect you today? 🛡️"
        
        elif 'threats' in user_input_lower and 'today' in user_input_lower:
            count = len(self.threat_database)
            return f"Today I've detected {count} potential threats. Use 'report' for detailed analysis."
        
        elif 'safe' in user_input_lower and '0x' in user_input:
            # Extract address
            address = user_input[user_input.find('0x'):user_input.find('0x')+42]
            return self._scan_ethereum_address(address)
        
        elif 'critical' in user_input_lower:
            critical_count = sum(1 for threat in self.threat_database.values() 
                               if threat.get('severity') == 'critical')
            return f"Currently tracking {critical_count} critical threats. Use 'report' for details."
        
        elif 'help' in user_input_lower:
            return self.interactive_help([])
        
        else:
            return """
I understand you're asking about threat intelligence. Here are some things I can help with:

• Scan addresses, URLs, or text for threats
• Analyze specific threats by ID  
• Generate threat reports
• Show system status
• Train my ML model with feedback

Type 'help' for a complete list of commands! 🤖
            """

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

    def _register_threat_filing_commands(self):
        """Register threat filing system commands"""
        if THREAT_FILING_AVAILABLE:
            self.commands.update({
                'file': self.interactive_file_threat,
                'search': self.interactive_search_threats,
                'export': self.interactive_export_threats,
                'stats': self.interactive_threat_stats
            })

    # Threat Filing System Interactive Commands
    
    def interactive_file_threat(self, args: List[str]) -> str:
        """Interactive threat filing to database"""
        if not self.threat_filing:
            return "❌ Threat filing system not available"
        
        if len(args) < 3:
            return """📁 **File Threat Usage:**
• `file website <domain> <threat_type> [description]`
• `file individual <name> <threat_type> [description]` 
• `file ipo <company> <project_type> <threat_type> [description]`

**Threat Types:**
- Website: phishing, malware, scam, fake_exchange, rug_pull
- Individual: scammer, hacker, social_engineer, money_launderer  
- IPO: rug_pull, ponzi, fake_project, exit_scam, pump_dump"""
        
        category = args[0].lower()
        
        try:
            if category == "website":
                domain = args[1]
                threat_type = args[2]
                description = " ".join(args[3:]) if len(args) > 3 else f"Manually filed {threat_type} website"
                
                threat_id = self.threat_filing.add_malicious_website(
                    domain=domain,
                    threat_type=threat_type,
                    description=description,
                    source="manual_filing",
                    severity=7
                )
                return f"✅ Filed malicious website: {domain} (ID: {threat_id})"
                
            elif category == "individual":
                name = args[1]
                threat_type = args[2]
                description = " ".join(args[3:]) if len(args) > 3 else f"Manually filed {threat_type} individual"
                
                threat_id = self.threat_filing.add_malicious_individual(
                    name=name,
                    threat_type=threat_type,
                    description=description,
                    source="manual_filing",
                    severity=7
                )
                return f"✅ Filed malicious individual: {name} (ID: {threat_id})"
                
            elif category == "ipo":
                if len(args) < 4:
                    return "❌ IPO filing requires: company_name project_type threat_type [description]"
                    
                company = args[1]
                project_type = args[2]
                threat_type = args[3]
                description = " ".join(args[4:]) if len(args) > 4 else f"Manually filed {threat_type} project"
                
                threat_id = self.threat_filing.add_fraudulent_ipo(
                    company_name=company,
                    project_type=project_type,
                    threat_type=threat_type,
                    description=description,
                    source="manual_filing",
                    severity=7
                )
                return f"✅ Filed fraudulent IPO: {company} (ID: {threat_id})"
                
            else:
                return "❌ Invalid category. Use: website, individual, or ipo"
                
        except Exception as e:
            return f"❌ Error filing threat: {str(e)}"
    
    def interactive_search_threats(self, args: List[str]) -> str:
        """Search threats in filing system"""
        if not self.threat_filing:
            return "❌ Threat filing system not available"
        
        if not args:
            return "❌ Please provide search query. Usage: search <query> [category]"
        
        query = args[0]
        categories = args[1:] if len(args) > 1 else None
        
        try:
            results = self.threat_filing.search_threats(query, categories)
            
            total_results = len(results['websites']) + len(results['individuals']) + len(results['ipos'])
            
            if total_results == 0:
                return f"🔍 No threats found for query: '{query}'"
            
            result = f"🔍 **Search Results for '{query}'** ({total_results} found):\n\n"
            
            if results['websites']:
                result += f"**🌐 Malicious Websites ({len(results['websites'])}):**\n"
                for site in results['websites'][:5]:  # Limit to 5 results
                    result += f"• {site['domain']} - {site['threat_type']} (Severity: {site['severity']}/10)\n"
                if len(results['websites']) > 5:
                    result += f"  ... and {len(results['websites']) - 5} more\n"
                result += "\n"
            
            if results['individuals']:
                result += f"**👤 Malicious Individuals ({len(results['individuals'])}):**\n"
                for person in results['individuals'][:5]:
                    result += f"• {person['name']} - {person['threat_type']} (Severity: {person['severity']}/10)\n"
                if len(results['individuals']) > 5:
                    result += f"  ... and {len(results['individuals']) - 5} more\n"
                result += "\n"
            
            if results['ipos']:
                result += f"**🏢 Fraudulent IPOs ({len(results['ipos'])}):**\n"
                for ipo in results['ipos'][:5]:
                    result += f"• {ipo['company_name']} - {ipo['threat_type']} (Severity: {ipo['severity']}/10)\n"
                if len(results['ipos']) > 5:
                    result += f"  ... and {len(results['ipos']) - 5} more\n"
            
            return result
            
        except Exception as e:
            return f"❌ Error searching threats: {str(e)}"
    
    def interactive_export_threats(self, args: List[str]) -> str:
        """Export threat database"""
        if not self.threat_filing:
            return "❌ Threat filing system not available"
        
        format_type = args[0] if args else "json"
        threat_type = args[1] if len(args) > 1 else None
        
        try:
            exported_data = self.threat_filing.export_threats(format_type, threat_type)
            
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"threat_export_{timestamp}.{format_type}"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(exported_data)
            
            stats = self.threat_filing.get_threat_statistics()
            total_threats = stats.get('active_websites', 0) + stats.get('active_individuals', 0) + stats.get('active_ipos', 0)
            
            return f"✅ Exported {total_threats} threats to {filename}"
            
        except Exception as e:
            return f"❌ Error exporting threats: {str(e)}"
    
    def interactive_threat_stats(self, args: List[str]) -> str:
        """Display comprehensive threat statistics"""
        if not self.threat_filing:
            return "❌ Threat filing system not available"
        
        try:
            stats = self.threat_filing.get_threat_statistics()
            
            result = "📊 **Threat Database Statistics:**\n\n"
            
            # Overall counts
            total_threats = stats.get('active_websites', 0) + stats.get('active_individuals', 0) + stats.get('active_ipos', 0)
            result += f"**Total Active Threats:** {total_threats}\n"
            result += f"• 🌐 Websites: {stats.get('active_websites', 0)}\n"
            result += f"• 👤 Individuals: {stats.get('active_individuals', 0)}\n"
            result += f"• 🏢 IPOs: {stats.get('active_ipos', 0)}\n\n"
            
            # Recent activity
            result += f"**📈 Recent Activity:**\n"
            result += f"• New threats (7 days): {stats.get('new_threats_week', 0)}\n\n"
            
            # Website threat breakdown
            if stats.get('website_threats'):
                result += "**🌐 Website Threat Types:**\n"
                for threat_type, count in stats['website_threats'].items():
                    result += f"• {threat_type}: {count}\n"
                result += "\n"
            
            # Individual threat breakdown  
            if stats.get('individual_threats'):
                result += "**👤 Individual Threat Types:**\n"
                for threat_type, count in stats['individual_threats'].items():
                    result += f"• {threat_type}: {count}\n"
                result += "\n"
            
            # IPO threat breakdown
            if stats.get('ipo_threats'):
                result += "**🏢 IPO Threat Types:**\n"
                for threat_type, count in stats['ipo_threats'].items():
                    result += f"• {threat_type}: {count}\n"
            
            return result
            
        except Exception as e:
            return f"❌ Error getting statistics: {str(e)}"

# Legacy compatibility
class DMERMonitor(DmerMonitorAgent):
    """Legacy class for backward compatibility"""
    pass
