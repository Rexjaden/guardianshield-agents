"""
GuardianShield External Security Monitoring Agent
Advanced external security monitoring with automated 24-hour audit cycles for smart contracts and blockchain activities
"""

import os
import sys
import json
import time
import hashlib
import logging
import threading
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Union
from pathlib import Path
import sqlite3
from dataclasses import dataclass, asdict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from web3 import Web3
    from eth_account import Account
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    logger.warning("Web3 not available - blockchain features disabled")

try:
    from agents.threat_filing_system import ThreatFilingSystem
    THREAT_FILING_AVAILABLE = True
except ImportError:
    THREAT_FILING_AVAILABLE = False
    logger.warning("Threat filing system not available")

@dataclass
class BlockchainAuditResult:
    """Structure for blockchain security audit results"""
    audit_id: str
    agent_name: str
    audit_type: str
    timestamp: str
    status: str  # success, warning, critical, error
    findings: List[Dict[str, Any]]
    risk_level: int  # 1-10 scale
    recommendations: List[str]
    affected_addresses: List[str]
    remediation_required: bool
    gas_analysis: Optional[Dict[str, Any]] = None
    contract_analysis: Optional[Dict[str, Any]] = None

class ExternalSecurityAgent:
    """
    External Security Monitoring Agent
    - Smart contract security audits
    - Wallet address monitoring
    - Blockchain transaction analysis
    - DeFi protocol monitoring
    - Automated 24-hour security cycles
    """
    
    def __init__(self):
        self.name = "ExternalSecurityAgent"
        self.audit_db_path = "external_security_audits.db"
        
        # Blockchain configuration
        self.monitored_contracts = set()
        self.monitored_wallets = set()
        self.contract_checksums = {}
        self.last_audit_time = None
        self.audit_interval = timedelta(hours=24)  # 24-hour cycle
        self.is_monitoring = False
        
        # Web3 configuration
        if WEB3_AVAILABLE:
            self.setup_web3_connections()
        else:
            self.web3_connections = {}
        
        # Initialize components
        self.init_audit_database()
        self.load_monitoring_targets()
        
        # Initialize threat filing if available
        if THREAT_FILING_AVAILABLE:
            self.threat_filing = ThreatFilingSystem()
            logger.info("Threat filing system connected")
        else:
            self.threat_filing = None
        
        # Start monitoring thread
        self.monitoring_thread = None
        self.start_monitoring()
        
        logger.info("External Security Agent initialized - monitoring blockchain activities")
    
    def setup_web3_connections(self):
        """Setup Web3 connections to various networks"""
        self.web3_connections = {}
        
        # Network configurations
        networks = {
            "ethereum": {
                "rpc_url": "https://eth.llamarpc.com",
                "chain_id": 1,
                "name": "Ethereum Mainnet"
            },
            "polygon": {
                "rpc_url": "https://polygon.llamarpc.com",
                "chain_id": 137,
                "name": "Polygon Mainnet"
            },
            "bsc": {
                "rpc_url": "https://bsc.llamarpc.com",
                "chain_id": 56,
                "name": "BSC Mainnet"
            }
        }
        
        for network_name, config in networks.items():
            try:
                w3 = Web3(Web3.HTTPProvider(config["rpc_url"]))
                if w3.is_connected():
                    self.web3_connections[network_name] = {
                        "web3": w3,
                        "config": config
                    }
                    logger.info(f"Connected to {config['name']}")
                else:
                    logger.warning(f"Failed to connect to {config['name']}")
            except Exception as e:
                logger.error(f"Error connecting to {network_name}: {e}")
    
    def init_audit_database(self):
        """Initialize SQLite database for external audit results"""
        with sqlite3.connect(self.audit_db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blockchain_audits (
                    audit_id TEXT PRIMARY KEY,
                    agent_name TEXT NOT NULL,
                    audit_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    status TEXT NOT NULL,
                    risk_level INTEGER NOT NULL,
                    findings_count INTEGER DEFAULT 0,
                    remediation_required BOOLEAN DEFAULT FALSE,
                    findings_json TEXT,
                    recommendations_json TEXT,
                    affected_addresses_json TEXT,
                    gas_analysis_json TEXT,
                    contract_analysis_json TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contract_monitoring (
                    contract_address TEXT PRIMARY KEY,
                    network TEXT NOT NULL,
                    contract_name TEXT,
                    bytecode_hash TEXT,
                    creation_block INTEGER,
                    last_activity_block INTEGER,
                    risk_score INTEGER DEFAULT 5,
                    is_verified BOOLEAN DEFAULT FALSE,
                    first_seen TEXT NOT NULL,
                    last_checked TEXT NOT NULL,
                    metadata_json TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS wallet_monitoring (
                    wallet_address TEXT PRIMARY KEY,
                    network TEXT NOT NULL,
                    wallet_type TEXT,
                    balance_eth REAL DEFAULT 0,
                    transaction_count INTEGER DEFAULT 0,
                    last_activity TEXT,
                    risk_score INTEGER DEFAULT 5,
                    is_flagged BOOLEAN DEFAULT FALSE,
                    first_seen TEXT NOT NULL,
                    last_checked TEXT NOT NULL,
                    metadata_json TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS suspicious_transactions (
                    tx_hash TEXT PRIMARY KEY,
                    network TEXT NOT NULL,
                    from_address TEXT,
                    to_address TEXT,
                    value_eth REAL,
                    gas_used INTEGER,
                    block_number INTEGER,
                    timestamp TEXT,
                    risk_indicators TEXT,
                    severity TEXT DEFAULT 'medium',
                    investigated BOOLEAN DEFAULT FALSE
                )
            ''')
            
            conn.commit()
            logger.info("External security audit database initialized")
    
    def load_monitoring_targets(self):
        """Load monitoring targets from configuration"""
        targets_file = Path("external_monitoring_targets.json")
        
        default_targets = {
            "contracts": [
                {
                    "address": "0xA0b86a33E6441E2822334c8C79C8ca1819d06000", 
                    "network": "ethereum",
                    "name": "Example DeFi Protocol",
                    "type": "defi"
                }
            ],
            "wallets": [
                {
                    "address": "0x742d35Cc6634C0532925a3b8D98d4E078b2044Cc",
                    "network": "ethereum", 
                    "name": "Test Wallet",
                    "type": "monitored"
                }
            ],
            "monitoring_rules": {
                "high_value_threshold": 10,  # ETH
                "suspicious_gas_multiplier": 3,
                "max_daily_transactions": 1000,
                "min_contract_verification": True
            }
        }
        
        if targets_file.exists():
            try:
                with open(targets_file, 'r') as f:
                    self.monitoring_targets = json.load(f)
                logger.info("Monitoring targets loaded from file")
            except Exception as e:
                logger.error(f"Error loading monitoring targets: {e}")
                self.monitoring_targets = default_targets
        else:
            self.monitoring_targets = default_targets
            try:
                with open(targets_file, 'w') as f:
                    json.dump(self.monitoring_targets, f, indent=2)
                logger.info("Default monitoring targets created")
            except Exception as e:
                logger.error(f"Error saving monitoring targets: {e}")
    
    def analyze_smart_contract(self, contract_address: str, network: str = "ethereum") -> List[Dict[str, Any]]:
        """Analyze smart contract for security issues"""
        findings = []
        
        try:
            if network not in self.web3_connections:
                findings.append({
                    "type": "network_unavailable",
                    "severity": "error",
                    "description": f"Network {network} not available",
                    "contract": contract_address
                })
                return findings
            
            w3 = self.web3_connections[network]["web3"]
            
            # Check if address is a contract
            code = w3.eth.get_code(Web3.to_checksum_address(contract_address))
            if len(code) <= 2:  # '0x' only
                findings.append({
                    "type": "not_a_contract",
                    "severity": "warning",
                    "description": "Address does not contain contract code",
                    "contract": contract_address
                })
                return findings
            
            # Analyze bytecode
            bytecode_hash = hashlib.sha256(code).hexdigest()
            
            # Check for known malicious patterns in bytecode
            malicious_patterns = [
                b'\x31\x60\x00\x52',  # Potential selfdestruct pattern
                b'\xff',  # SELFDESTRUCT opcode
                b'\x54\x60\x00\x55'   # Potential storage manipulation
            ]
            
            for pattern in malicious_patterns:
                if pattern in code:
                    findings.append({
                        "type": "suspicious_bytecode",
                        "severity": "critical",
                        "description": "Suspicious bytecode pattern detected",
                        "contract": contract_address,
                        "details": {
                            "pattern": pattern.hex(),
                            "bytecode_hash": bytecode_hash
                        }
                    })
            
            # Check contract size (unusually large contracts might be suspicious)
            if len(code) > 24576:  # Ethereum contract size limit
                findings.append({
                    "type": "oversized_contract",
                    "severity": "warning", 
                    "description": "Contract exceeds normal size limits",
                    "contract": contract_address,
                    "details": {"size": len(code)}
                })
            
            # Try to get contract creation transaction
            try:
                # This is a simplified check - in production you'd use more sophisticated methods
                latest_block = w3.eth.get_block('latest')
                block_number = latest_block['number']
                
                # Check recent transactions for suspicious activity
                recent_txs = []
                for i in range(max(0, block_number - 100), block_number):
                    try:
                        block = w3.eth.get_block(i, full_transactions=True)
                        for tx in block['transactions']:
                            if tx['to'] and tx['to'].lower() == contract_address.lower():
                                recent_txs.append(tx)
                    except:
                        continue
                
                if len(recent_txs) > 100:  # High transaction volume
                    findings.append({
                        "type": "high_transaction_volume",
                        "severity": "warning",
                        "description": "Unusually high transaction volume",
                        "contract": contract_address,
                        "details": {"recent_transactions": len(recent_txs)}
                    })
                        
            except Exception as e:
                logger.debug(f"Error analyzing contract transactions: {e}")
            
            # Store contract analysis in database
            self.store_contract_analysis(contract_address, network, bytecode_hash, findings)
            
            logger.info(f"Smart contract analysis completed for {contract_address} - {len(findings)} findings")
        
        except Exception as e:
            logger.error(f"Error analyzing smart contract {contract_address}: {e}")
            findings.append({
                "type": "analysis_error",
                "severity": "error",
                "description": f"Contract analysis failed: {str(e)}",
                "contract": contract_address
            })
        
        return findings
    
    def analyze_wallet_security(self, wallet_address: str, network: str = "ethereum") -> List[Dict[str, Any]]:
        """Analyze wallet for security issues"""
        findings = []
        
        try:
            if network not in self.web3_connections:
                findings.append({
                    "type": "network_unavailable",
                    "severity": "error",
                    "description": f"Network {network} not available",
                    "wallet": wallet_address
                })
                return findings
            
            w3 = self.web3_connections[network]["web3"]
            checksum_address = Web3.to_checksum_address(wallet_address)
            
            # Get wallet balance
            balance_wei = w3.eth.get_balance(checksum_address)
            balance_eth = w3.from_wei(balance_wei, 'ether')
            
            # Get transaction count
            tx_count = w3.eth.get_transaction_count(checksum_address)
            
            # Check for high-value wallet
            if balance_eth > self.monitoring_targets["monitoring_rules"]["high_value_threshold"]:
                findings.append({
                    "type": "high_value_wallet",
                    "severity": "info",
                    "description": f"High-value wallet detected: {balance_eth:.4f} ETH",
                    "wallet": wallet_address,
                    "details": {
                        "balance_eth": float(balance_eth),
                        "transaction_count": tx_count
                    }
                })
            
            # Check for suspicious transaction patterns
            if tx_count > self.monitoring_targets["monitoring_rules"]["max_daily_transactions"]:
                findings.append({
                    "type": "high_transaction_frequency",
                    "severity": "warning",
                    "description": "Unusually high transaction frequency",
                    "wallet": wallet_address,
                    "details": {"transaction_count": tx_count}
                })
            
            # Check if wallet is a known exchange or service
            known_exchanges = [
                "0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be",  # Binance
                "0xd551234ae421e3bcba99a0da6d736074f22192ff",  # Binance 2
                "0x28c6c06298d514db089934071355e5743bf21d60",  # Binance 14
            ]
            
            if checksum_address.lower() in [addr.lower() for addr in known_exchanges]:
                findings.append({
                    "type": "exchange_wallet",
                    "severity": "info",
                    "description": "Known exchange wallet detected",
                    "wallet": wallet_address
                })
            
            # Store wallet analysis
            self.store_wallet_analysis(wallet_address, network, balance_eth, tx_count, findings)
            
            logger.info(f"Wallet analysis completed for {wallet_address} - Balance: {balance_eth:.4f} ETH, TXs: {tx_count}")
        
        except Exception as e:
            logger.error(f"Error analyzing wallet {wallet_address}: {e}")
            findings.append({
                "type": "analysis_error",
                "severity": "error",
                "description": f"Wallet analysis failed: {str(e)}",
                "wallet": wallet_address
            })
        
        return findings
    
    def scan_defi_protocols(self) -> List[Dict[str, Any]]:
        """Scan DeFi protocols for security issues"""
        findings = []
        
        try:
            # Known DeFi protocol patterns to check
            defi_risks = {
                "flash_loan_attacks": "Potential flash loan vulnerability",
                "reentrancy_risks": "Reentrancy attack vectors",
                "oracle_manipulation": "Price oracle manipulation risks",
                "liquidity_risks": "Low liquidity concerns"
            }
            
            # Check monitored contracts for DeFi-specific risks
            for contract_info in self.monitoring_targets.get("contracts", []):
                if contract_info.get("type") == "defi":
                    contract_address = contract_info["address"]
                    network = contract_info.get("network", "ethereum")
                    
                    # Perform DeFi-specific analysis
                    defi_findings = self.analyze_smart_contract(contract_address, network)
                    
                    # Add DeFi context to findings
                    for finding in defi_findings:
                        finding["defi_protocol"] = contract_info.get("name", "Unknown")
                        finding["protocol_type"] = "defi"
                    
                    findings.extend(defi_findings)
            
            logger.info(f"DeFi protocol scan completed - {len(findings)} findings")
        
        except Exception as e:
            logger.error(f"Error scanning DeFi protocols: {e}")
            findings.append({
                "type": "scan_error",
                "severity": "error",
                "description": f"DeFi protocol scan failed: {str(e)}"
            })
        
        return findings
    
    def monitor_suspicious_transactions(self, network: str = "ethereum") -> List[Dict[str, Any]]:
        """Monitor for suspicious transaction patterns"""
        findings = []
        
        try:
            if network not in self.web3_connections:
                return findings
            
            w3 = self.web3_connections[network]["web3"]
            
            # Get recent blocks
            latest_block = w3.eth.get_block('latest')
            current_block = latest_block['number']
            
            # Check last few blocks for suspicious patterns
            for block_num in range(max(0, current_block - 10), current_block + 1):
                try:
                    block = w3.eth.get_block(block_num, full_transactions=True)
                    
                    for tx in block['transactions']:
                        # Skip failed transactions
                        if tx.get('status') == 0:
                            continue
                        
                        # Check for high gas usage (potential attack)
                        gas_used = tx.get('gas', 0)
                        gas_limit = 21000  # Standard transfer
                        
                        if gas_used > gas_limit * self.monitoring_targets["monitoring_rules"]["suspicious_gas_multiplier"]:
                            findings.append({
                                "type": "high_gas_usage",
                                "severity": "warning",
                                "description": "Transaction with unusually high gas usage",
                                "details": {
                                    "tx_hash": tx['hash'].hex(),
                                    "gas_used": gas_used,
                                    "from": tx['from'],
                                    "to": tx.get('to'),
                                    "value_eth": float(w3.from_wei(tx['value'], 'ether'))
                                }
                            })
                        
                        # Check for high-value transactions
                        value_eth = w3.from_wei(tx['value'], 'ether')
                        if value_eth > self.monitoring_targets["monitoring_rules"]["high_value_threshold"]:
                            findings.append({
                                "type": "high_value_transaction",
                                "severity": "info",
                                "description": f"High-value transaction: {value_eth:.4f} ETH",
                                "details": {
                                    "tx_hash": tx['hash'].hex(),
                                    "value_eth": float(value_eth),
                                    "from": tx['from'],
                                    "to": tx.get('to')
                                }
                            })
                
                except Exception as e:
                    logger.debug(f"Error processing block {block_num}: {e}")
            
            logger.info(f"Transaction monitoring completed - {len(findings)} suspicious patterns found")
        
        except Exception as e:
            logger.error(f"Error monitoring transactions: {e}")
            findings.append({
                "type": "monitoring_error",
                "severity": "error",
                "description": f"Transaction monitoring failed: {str(e)}"
            })
        
        return findings
    
    def perform_security_audit(self) -> BlockchainAuditResult:
        """Perform comprehensive external security audit"""
        audit_id = f"external_{int(time.time())}"
        timestamp = datetime.now().isoformat()
        
        logger.info(f"Starting external security audit {audit_id}")
        
        try:
            # Run all security scans
            all_findings = []
            affected_addresses = set()
            
            # Analyze monitored smart contracts
            for contract_info in self.monitoring_targets.get("contracts", []):
                contract_findings = self.analyze_smart_contract(
                    contract_info["address"], 
                    contract_info.get("network", "ethereum")
                )
                all_findings.extend(contract_findings)
                affected_addresses.add(contract_info["address"])
            
            # Analyze monitored wallets
            for wallet_info in self.monitoring_targets.get("wallets", []):
                wallet_findings = self.analyze_wallet_security(
                    wallet_info["address"],
                    wallet_info.get("network", "ethereum")
                )
                all_findings.extend(wallet_findings)
                affected_addresses.add(wallet_info["address"])
            
            # Scan DeFi protocols
            defi_findings = self.scan_defi_protocols()
            all_findings.extend(defi_findings)
            
            # Monitor suspicious transactions
            for network in self.web3_connections.keys():
                tx_findings = self.monitor_suspicious_transactions(network)
                all_findings.extend(tx_findings)
            
            # Calculate risk level
            risk_level = self.calculate_risk_level(all_findings)
            
            # Generate recommendations
            recommendations = self.generate_recommendations(all_findings)
            
            # Determine status
            critical_count = len([f for f in all_findings if f.get('severity') == 'critical'])
            error_count = len([f for f in all_findings if f.get('severity') == 'error'])
            
            if critical_count > 0:
                status = "critical"
            elif error_count > 0:
                status = "error"
            elif len(all_findings) > 0:
                status = "warning"
            else:
                status = "success"
            
            # Create audit result
            audit_result = BlockchainAuditResult(
                audit_id=audit_id,
                agent_name=self.name,
                audit_type="external_security",
                timestamp=timestamp,
                status=status,
                findings=all_findings,
                risk_level=risk_level,
                recommendations=recommendations,
                affected_addresses=list(affected_addresses),
                remediation_required=critical_count > 0 or error_count > 0
            )
            
            # Save audit result
            self.save_audit_result(audit_result)
            
            # File critical threats to threat database
            if self.threat_filing and critical_count > 0:
                self.file_security_threats(all_findings)
            
            logger.info(f"External security audit {audit_id} completed - Status: {status}, Risk: {risk_level}/10")
            
            return audit_result
            
        except Exception as e:
            logger.error(f"Error performing external security audit: {e}")
            return BlockchainAuditResult(
                audit_id=audit_id,
                agent_name=self.name,
                audit_type="external_security",
                timestamp=timestamp,
                status="error",
                findings=[{
                    "type": "audit_error",
                    "severity": "error",
                    "description": f"External security audit failed: {str(e)}"
                }],
                risk_level=10,
                recommendations=["Investigate audit system failure"],
                affected_addresses=[],
                remediation_required=True
            )
    
    def calculate_risk_level(self, findings: List[Dict[str, Any]]) -> int:
        """Calculate overall risk level based on findings"""
        if not findings:
            return 1
        
        severity_weights = {
            "critical": 10,
            "error": 7,
            "warning": 4,
            "info": 1
        }
        
        total_weight = sum(severity_weights.get(f.get('severity', 'info'), 1) for f in findings)
        max_possible_weight = len(findings) * 10
        
        if max_possible_weight == 0:
            return 1
        
        risk_level = min(10, max(1, int((total_weight / max_possible_weight) * 10)))
        return risk_level
    
    def generate_recommendations(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Generate security recommendations based on findings"""
        recommendations = []
        
        # Group findings by type
        findings_by_type = {}
        for finding in findings:
            finding_type = finding.get('type', 'unknown')
            if finding_type not in findings_by_type:
                findings_by_type[finding_type] = []
            findings_by_type[finding_type].append(finding)
        
        # Generate type-specific recommendations
        if 'suspicious_bytecode' in findings_by_type:
            recommendations.append("Immediately investigate contracts with suspicious bytecode")
            recommendations.append("Consider contract auditing by security professionals")
        
        if 'high_gas_usage' in findings_by_type:
            recommendations.append("Monitor transactions with high gas usage for potential attacks")
            recommendations.append("Implement gas usage alerts and limits")
        
        if 'high_value_transaction' in findings_by_type:
            recommendations.append("Monitor high-value transactions for money laundering")
            recommendations.append("Implement transaction value thresholds and alerts")
        
        if 'high_transaction_frequency' in findings_by_type:
            recommendations.append("Investigate wallets with unusual transaction patterns")
            recommendations.append("Implement rate limiting and monitoring")
        
        if 'oversized_contract' in findings_by_type:
            recommendations.append("Review large contracts for complexity and security risks")
        
        # General recommendations
        if len(findings) > 0:
            recommendations.append("Implement continuous blockchain monitoring")
            recommendations.append("Regular smart contract security audits")
            recommendations.append("Monitor DeFi protocol risks and vulnerabilities")
        
        return recommendations
    
    def store_contract_analysis(self, address: str, network: str, bytecode_hash: str, findings: List[Dict]):
        """Store contract analysis results"""
        try:
            with sqlite3.connect(self.audit_db_path) as conn:
                cursor = conn.cursor()
                
                risk_score = min(10, max(1, len([f for f in findings if f.get('severity') in ['critical', 'error']]) + 1))
                
                cursor.execute('''
                    INSERT OR REPLACE INTO contract_monitoring 
                    (contract_address, network, bytecode_hash, risk_score, last_checked, first_seen, metadata_json)
                    VALUES (?, ?, ?, ?, ?, COALESCE((SELECT first_seen FROM contract_monitoring WHERE contract_address = ?), ?), ?)
                ''', (address, network, bytecode_hash, risk_score, datetime.now().isoformat(), 
                     address, datetime.now().isoformat(), json.dumps({"findings_count": len(findings)})))
                
                conn.commit()
        except Exception as e:
            logger.error(f"Error storing contract analysis: {e}")
    
    def store_wallet_analysis(self, address: str, network: str, balance_eth: float, tx_count: int, findings: List[Dict]):
        """Store wallet analysis results"""
        try:
            with sqlite3.connect(self.audit_db_path) as conn:
                cursor = conn.cursor()
                
                risk_score = min(10, max(1, len([f for f in findings if f.get('severity') in ['critical', 'error']]) + 1))
                is_flagged = any(f.get('severity') == 'critical' for f in findings)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO wallet_monitoring 
                    (wallet_address, network, balance_eth, transaction_count, risk_score, is_flagged, 
                     last_checked, first_seen, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT first_seen FROM wallet_monitoring WHERE wallet_address = ?), ?), ?)
                ''', (address, network, balance_eth, tx_count, risk_score, is_flagged, 
                     datetime.now().isoformat(), address, datetime.now().isoformat(), 
                     json.dumps({"findings_count": len(findings)})))
                
                conn.commit()
        except Exception as e:
            logger.error(f"Error storing wallet analysis: {e}")
    
    def save_audit_result(self, audit_result: BlockchainAuditResult):
        """Save audit result to database"""
        try:
            with sqlite3.connect(self.audit_db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO blockchain_audits 
                    (audit_id, agent_name, audit_type, timestamp, status, risk_level,
                     findings_count, remediation_required, findings_json, recommendations_json, 
                     affected_addresses_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    audit_result.audit_id,
                    audit_result.agent_name,
                    audit_result.audit_type,
                    audit_result.timestamp,
                    audit_result.status,
                    audit_result.risk_level,
                    len(audit_result.findings),
                    audit_result.remediation_required,
                    json.dumps(audit_result.findings),
                    json.dumps(audit_result.recommendations),
                    json.dumps(audit_result.affected_addresses)
                ))
                
                conn.commit()
                logger.info(f"Audit result {audit_result.audit_id} saved to database")
        
        except Exception as e:
            logger.error(f"Error saving audit result: {e}")
    
    def file_security_threats(self, findings: List[Dict[str, Any]]):
        """File critical security findings as threats"""
        try:
            critical_findings = [f for f in findings if f.get('severity') == 'critical']
            
            for finding in critical_findings:
                if finding.get('type') == 'suspicious_bytecode':
                    # File suspicious contract
                    contract_addr = finding.get('contract', 'Unknown')
                    self.threat_filing.add_malicious_individual(
                        name=f"Suspicious Contract - {contract_addr}",
                        threat_type="hacker",
                        severity=9,
                        description=f"Contract with suspicious bytecode: {finding.get('description', '')}",
                        wallet_addresses=[contract_addr],
                        source="external_security_audit"
                    )
                
                logger.info(f"Filed critical blockchain finding as threat: {finding.get('type')}")
        
        except Exception as e:
            logger.error(f"Error filing blockchain threats: {e}")
    
    def start_monitoring(self):
        """Start continuous external security monitoring"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            logger.info("External security monitoring started")
    
    def stop_monitoring(self):
        """Stop continuous external security monitoring"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("External security monitoring stopped")
    
    def _monitoring_loop(self):
        """Continuous monitoring loop with 24-hour audit cycles"""
        while self.is_monitoring:
            try:
                current_time = datetime.now()
                
                # Check if it's time for a scheduled audit
                if (not self.last_audit_time or 
                    current_time - self.last_audit_time >= self.audit_interval):
                    
                    logger.info("Starting scheduled 24-hour external security audit")
                    audit_result = self.perform_security_audit()
                    self.last_audit_time = current_time
                    
                    # Log audit summary
                    logger.info(f"External audit completed - Status: {audit_result.status}, "
                              f"Risk: {audit_result.risk_level}/10, "
                              f"Findings: {len(audit_result.findings)}")
                
                # Sleep for 1 hour before next check
                time.sleep(3600)  # Check every hour
                
            except Exception as e:
                logger.error(f"Error in external monitoring loop: {e}")
                time.sleep(300)  # Wait 5 minutes before retry
    
    def get_latest_audit_result(self) -> Optional[Dict[str, Any]]:
        """Get the latest audit result"""
        try:
            with sqlite3.connect(self.audit_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM blockchain_audits 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ''')
                
                result = cursor.fetchone()
                if result:
                    audit_data = dict(result)
                    audit_data['findings'] = json.loads(audit_data['findings_json'])
                    audit_data['recommendations'] = json.loads(audit_data['recommendations_json'])
                    audit_data['affected_addresses'] = json.loads(audit_data['affected_addresses_json'])
                    return audit_data
                
        except Exception as e:
            logger.error(f"Error getting latest audit result: {e}")
        
        return None
    
    def force_audit(self) -> BlockchainAuditResult:
        """Force an immediate external security audit"""
        logger.info("Forcing immediate external security audit")
        return self.perform_security_audit()
    
    def add_monitoring_target(self, target_type: str, address: str, network: str = "ethereum", name: str = ""):
        """Add new monitoring target"""
        if target_type not in ["contract", "wallet"]:
            raise ValueError("Target type must be 'contract' or 'wallet'")
        
        target_key = "contracts" if target_type == "contract" else "wallets"
        
        new_target = {
            "address": address,
            "network": network,
            "name": name or f"Monitored {target_type}",
            "type": target_type
        }
        
        if target_key not in self.monitoring_targets:
            self.monitoring_targets[target_key] = []
        
        self.monitoring_targets[target_key].append(new_target)
        
        # Save updated targets
        try:
            with open("external_monitoring_targets.json", 'w') as f:
                json.dump(self.monitoring_targets, f, indent=2)
            logger.info(f"Added {target_type} {address} to monitoring targets")
        except Exception as e:
            logger.error(f"Error saving monitoring targets: {e}")


if __name__ == "__main__":
    # Test the external security agent
    agent = ExternalSecurityAgent()
    
    print("🔗 External Security Agent initialized")
    print(f"Web3 connections: {list(agent.web3_connections.keys())}")
    print(f"Monitoring {len(agent.monitoring_targets.get('contracts', []))} contracts")
    print(f"Monitoring {len(agent.monitoring_targets.get('wallets', []))} wallets")
    
    # Perform immediate audit for testing
    audit_result = agent.force_audit()
    print(f"\n📊 Audit Results:")
    print(f"Status: {audit_result.status}")
    print(f"Risk Level: {audit_result.risk_level}/10")
    print(f"Findings: {len(audit_result.findings)}")
    print(f"Affected Addresses: {len(audit_result.affected_addresses)}")
    
    if audit_result.findings:
        print("\n🔍 Key Findings:")
        for finding in audit_result.findings[:3]:  # Show first 3
            print(f"  • {finding.get('severity', 'info').upper()}: {finding.get('description', 'No description')}")
    
    if audit_result.recommendations:
        print("\n💡 Recommendations:")
        for rec in audit_result.recommendations[:3]:  # Show first 3
            print(f"  • {rec}")