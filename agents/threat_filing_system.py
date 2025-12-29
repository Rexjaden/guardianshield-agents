"""
GuardianShield Threat Filing System
Advanced database system for tracking malicious websites, individuals, and IPOs
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from pathlib import Path
import requests
from urllib.parse import urlparse
import ipaddress

logger = logging.getLogger(__name__)

class ThreatFilingSystem:
    """
    Comprehensive threat intelligence filing system for tracking:
    - Malicious websites and domains
    - Known bad actors and individuals  
    - Fraudulent IPOs and investment schemes
    - Associated metadata and evidence
    """
    
    def __init__(self, db_path: str = "./databases/threat_intelligence.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database with threat intelligence schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Malicious websites table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS malicious_websites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT UNIQUE NOT NULL,
                    url TEXT,
                    ip_address TEXT,
                    threat_type TEXT NOT NULL,
                    severity INTEGER NOT NULL DEFAULT 5,
                    description TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    source TEXT,
                    evidence_hash TEXT,
                    tags TEXT,
                    whois_data TEXT,
                    ssl_info TEXT,
                    reputation_score INTEGER DEFAULT 0
                )
            ''')
            
            # Malicious individuals table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS malicious_individuals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    aliases TEXT,
                    wallet_addresses TEXT,
                    social_profiles TEXT,
                    threat_type TEXT NOT NULL,
                    severity INTEGER NOT NULL DEFAULT 5,
                    description TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    source TEXT,
                    evidence_hash TEXT,
                    tags TEXT,
                    known_associates TEXT,
                    location_data TEXT,
                    reputation_score INTEGER DEFAULT 0
                )
            ''')
            
            # Fraudulent IPOs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fraudulent_ipos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT NOT NULL,
                    ticker_symbol TEXT,
                    exchange TEXT,
                    website TEXT,
                    contract_address TEXT,
                    project_type TEXT NOT NULL,
                    threat_type TEXT NOT NULL,
                    severity INTEGER NOT NULL DEFAULT 5,
                    description TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    source TEXT,
                    evidence_hash TEXT,
                    tags TEXT,
                    whitepaper_hash TEXT,
                    team_members TEXT,
                    social_metrics TEXT,
                    reputation_score INTEGER DEFAULT 0
                )
            ''')
            
            # Threat intelligence feeds table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS threat_feeds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feed_name TEXT NOT NULL,
                    feed_url TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    entries_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active'
                )
            ''')
            
            # Threat associations table (relationships between threats)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS threat_associations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    threat_type_1 TEXT NOT NULL,
                    threat_id_1 INTEGER NOT NULL,
                    threat_type_2 TEXT NOT NULL,
                    threat_id_2 INTEGER NOT NULL,
                    association_type TEXT NOT NULL,
                    confidence_score REAL DEFAULT 0.5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    evidence TEXT
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_websites_domain ON malicious_websites(domain)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_websites_threat_type ON malicious_websites(threat_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_websites_severity ON malicious_websites(severity)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_individuals_name ON malicious_individuals(name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_individuals_threat_type ON malicious_individuals(threat_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ipos_company ON fraudulent_ipos(company_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ipos_contract ON fraudulent_ipos(contract_address)')
            
            conn.commit()
            logger.info("Threat filing system database initialized successfully")
    
    def add_malicious_website(self, domain: str, threat_type: str, **kwargs) -> int:
        """Add a malicious website to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Extract IP if possible
            ip_address = kwargs.get('ip_address')
            if not ip_address:
                try:
                    import socket
                    ip_address = socket.gethostbyname(domain)
                except:
                    ip_address = None
            
            # Generate evidence hash
            evidence = f"{domain}:{threat_type}:{kwargs.get('description', '')}"
            evidence_hash = hashlib.sha256(evidence.encode()).hexdigest()[:16]
            
            cursor.execute('''
                INSERT OR REPLACE INTO malicious_websites 
                (domain, url, ip_address, threat_type, severity, description, source, 
                 evidence_hash, tags, whois_data, ssl_info, reputation_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                domain,
                kwargs.get('url', f"http://{domain}"),
                ip_address,
                threat_type,
                kwargs.get('severity', 5),
                kwargs.get('description', ''),
                kwargs.get('source', 'manual'),
                evidence_hash,
                json.dumps(kwargs.get('tags', [])),
                json.dumps(kwargs.get('whois_data', {})),
                json.dumps(kwargs.get('ssl_info', {})),
                kwargs.get('reputation_score', 0)
            ))
            
            website_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Added malicious website: {domain} (ID: {website_id})")
            return website_id
    
    def add_malicious_individual(self, name: str, threat_type: str, **kwargs) -> int:
        """Add a malicious individual to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Generate evidence hash
            evidence = f"{name}:{threat_type}:{kwargs.get('description', '')}"
            evidence_hash = hashlib.sha256(evidence.encode()).hexdigest()[:16]
            
            cursor.execute('''
                INSERT OR REPLACE INTO malicious_individuals 
                (name, aliases, wallet_addresses, social_profiles, threat_type, severity, 
                 description, source, evidence_hash, tags, known_associates, location_data, reputation_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                name,
                json.dumps(kwargs.get('aliases', [])),
                json.dumps(kwargs.get('wallet_addresses', [])),
                json.dumps(kwargs.get('social_profiles', {})),
                threat_type,
                kwargs.get('severity', 5),
                kwargs.get('description', ''),
                kwargs.get('source', 'manual'),
                evidence_hash,
                json.dumps(kwargs.get('tags', [])),
                json.dumps(kwargs.get('known_associates', [])),
                json.dumps(kwargs.get('location_data', {})),
                kwargs.get('reputation_score', 0)
            ))
            
            individual_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Added malicious individual: {name} (ID: {individual_id})")
            return individual_id
    
    def add_fraudulent_ipo(self, company_name: str, project_type: str, threat_type: str, **kwargs) -> int:
        """Add a fraudulent IPO/project to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Generate evidence hash
            evidence = f"{company_name}:{project_type}:{threat_type}:{kwargs.get('description', '')}"
            evidence_hash = hashlib.sha256(evidence.encode()).hexdigest()[:16]
            
            cursor.execute('''
                INSERT OR REPLACE INTO fraudulent_ipos 
                (company_name, ticker_symbol, exchange, website, contract_address, project_type,
                 threat_type, severity, description, source, evidence_hash, tags, 
                 whitepaper_hash, team_members, social_metrics, reputation_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                company_name,
                kwargs.get('ticker_symbol'),
                kwargs.get('exchange'),
                kwargs.get('website'),
                kwargs.get('contract_address'),
                project_type,
                threat_type,
                kwargs.get('severity', 5),
                kwargs.get('description', ''),
                kwargs.get('source', 'manual'),
                evidence_hash,
                json.dumps(kwargs.get('tags', [])),
                kwargs.get('whitepaper_hash'),
                json.dumps(kwargs.get('team_members', [])),
                json.dumps(kwargs.get('social_metrics', {})),
                kwargs.get('reputation_score', 0)
            ))
            
            ipo_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Added fraudulent IPO: {company_name} (ID: {ipo_id})")
            return ipo_id
    
    def search_threats(self, query: str, threat_categories: List[str] = None) -> Dict[str, List[Dict]]:
        """Search across all threat categories"""
        results = {"websites": [], "individuals": [], "ipos": []}
        
        if not threat_categories:
            threat_categories = ["websites", "individuals", "ipos"]
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if "websites" in threat_categories:
                cursor.execute('''
                    SELECT * FROM malicious_websites 
                    WHERE domain LIKE ? OR description LIKE ? OR tags LIKE ?
                    ORDER BY severity DESC, last_updated DESC
                ''', (f"%{query}%", f"%{query}%", f"%{query}%"))
                results["websites"] = [dict(row) for row in cursor.fetchall()]
            
            if "individuals" in threat_categories:
                cursor.execute('''
                    SELECT * FROM malicious_individuals 
                    WHERE name LIKE ? OR description LIKE ? OR aliases LIKE ? OR tags LIKE ?
                    ORDER BY severity DESC, last_updated DESC
                ''', (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"))
                results["individuals"] = [dict(row) for row in cursor.fetchall()]
            
            if "ipos" in threat_categories:
                cursor.execute('''
                    SELECT * FROM fraudulent_ipos 
                    WHERE company_name LIKE ? OR description LIKE ? OR ticker_symbol LIKE ? OR tags LIKE ?
                    ORDER BY severity DESC, last_updated DESC
                ''', (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"))
                results["ipos"] = [dict(row) for row in cursor.fetchall()]
        
        return results
    
    def get_threat_by_id(self, threat_type: str, threat_id: int) -> Optional[Dict]:
        """Get specific threat by ID and type"""
        table_map = {
            "website": "malicious_websites",
            "individual": "malicious_individuals", 
            "ipo": "fraudulent_ipos"
        }
        
        table_name = table_map.get(threat_type)
        if not table_name:
            return None
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (threat_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def update_threat_status(self, threat_type: str, threat_id: int, status: str) -> bool:
        """Update threat status (active, resolved, monitoring, etc.)"""
        table_map = {
            "website": "malicious_websites",
            "individual": "malicious_individuals",
            "ipo": "fraudulent_ipos"
        }
        
        table_name = table_map.get(threat_type)
        if not table_name:
            return False
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE {table_name} 
                SET status = ?, last_updated = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (status, threat_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_threat_statistics(self) -> Dict[str, Any]:
        """Get comprehensive threat database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Website stats
            cursor.execute("SELECT COUNT(*) FROM malicious_websites WHERE status = 'active'")
            stats["active_websites"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT threat_type, COUNT(*) FROM malicious_websites GROUP BY threat_type")
            stats["website_threats"] = dict(cursor.fetchall())
            
            # Individual stats  
            cursor.execute("SELECT COUNT(*) FROM malicious_individuals WHERE status = 'active'")
            stats["active_individuals"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT threat_type, COUNT(*) FROM malicious_individuals GROUP BY threat_type")
            stats["individual_threats"] = dict(cursor.fetchall())
            
            # IPO stats
            cursor.execute("SELECT COUNT(*) FROM fraudulent_ipos WHERE status = 'active'")
            stats["active_ipos"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT threat_type, COUNT(*) FROM fraudulent_ipos GROUP BY threat_type")
            stats["ipo_threats"] = dict(cursor.fetchall())
            
            # Recent activity
            cursor.execute('''
                SELECT COUNT(*) FROM (
                    SELECT first_seen FROM malicious_websites WHERE first_seen >= datetime('now', '-7 days')
                    UNION ALL
                    SELECT first_seen FROM malicious_individuals WHERE first_seen >= datetime('now', '-7 days')
                    UNION ALL  
                    SELECT first_seen FROM fraudulent_ipos WHERE first_seen >= datetime('now', '-7 days')
                )
            ''')
            stats["new_threats_week"] = cursor.fetchone()[0]
            
            return stats
    
    def export_threats(self, format_type: str = "json", threat_type: str = None) -> str:
        """Export threat data in various formats"""
        threats = []
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if not threat_type or threat_type == "websites":
                cursor.execute("SELECT * FROM malicious_websites WHERE status = 'active'")
                websites = [dict(row) for row in cursor.fetchall()]
                threats.extend([{**w, "category": "website"} for w in websites])
            
            if not threat_type or threat_type == "individuals":
                cursor.execute("SELECT * FROM malicious_individuals WHERE status = 'active'")
                individuals = [dict(row) for row in cursor.fetchall()]
                threats.extend([{**i, "category": "individual"} for i in individuals])
            
            if not threat_type or threat_type == "ipos":
                cursor.execute("SELECT * FROM fraudulent_ipos WHERE status = 'active'")
                ipos = [dict(row) for row in cursor.fetchall()]
                threats.extend([{**i, "category": "ipo"} for i in ipos])
        
        if format_type == "json":
            return json.dumps(threats, indent=2, default=str)
        elif format_type == "csv":
            if not threats:
                return ""
            
            import csv
            import io
            output = io.StringIO()
            fieldnames = threats[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(threats)
            return output.getvalue()
        
        return str(threats)
    
    def bulk_import_threats(self, threat_data: List[Dict]) -> Dict[str, int]:
        """Import multiple threats from external sources"""
        results = {"websites": 0, "individuals": 0, "ipos": 0, "errors": 0}
        
        for threat in threat_data:
            try:
                category = threat.get("category", "").lower()
                
                if category == "website":
                    self.add_malicious_website(
                        threat["domain"],
                        threat["threat_type"],
                        **{k: v for k, v in threat.items() if k not in ["domain", "threat_type", "category"]}
                    )
                    results["websites"] += 1
                
                elif category == "individual":
                    self.add_malicious_individual(
                        threat["name"],
                        threat["threat_type"],
                        **{k: v for k, v in threat.items() if k not in ["name", "threat_type", "category"]}
                    )
                    results["individuals"] += 1
                
                elif category == "ipo":
                    self.add_fraudulent_ipo(
                        threat["company_name"],
                        threat["project_type"],
                        threat["threat_type"],
                        **{k: v for k, v in threat.items() if k not in ["company_name", "project_type", "threat_type", "category"]}
                    )
                    results["ipos"] += 1
                    
            except Exception as e:
                logger.error(f"Error importing threat: {e}")
                results["errors"] += 1
        
        return results


# Predefined threat categories and types
THREAT_CATEGORIES = {
    "websites": {
        "phishing": "Phishing and credential theft sites",
        "malware": "Malware distribution sites", 
        "scam": "Investment and crypto scams",
        "fake_exchange": "Fake cryptocurrency exchanges",
        "rug_pull": "Rug pull project websites",
        "impersonation": "Impersonation of legitimate services"
    },
    "individuals": {
        "scammer": "Known scammer or fraudster",
        "hacker": "Malicious hacker or cybercriminal",
        "insider": "Insider threat or malicious employee",
        "social_engineer": "Social engineering specialist",
        "money_launderer": "Money laundering operations",
        "fake_influencer": "Fake crypto influencer or shill"
    },
    "ipos": {
        "rug_pull": "Planned rug pull project",
        "ponzi": "Ponzi or pyramid scheme",
        "fake_project": "Non-existent or fake project",
        "exit_scam": "Exit scam operation",
        "pump_dump": "Pump and dump scheme",
        "impersonation": "Impersonates legitimate projects"
    }
}