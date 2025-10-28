# Testnet Monitoring Agent Configuration
import os
import json
import time
import threading
from web3 import Web3
from dataclasses import dataclass
from typing import Dict, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('testnet_agent.log'),
        logging.StreamHandler()
    ]
)

@dataclass
class AgentConfig:
    agent_id: str
    batch_index: int
    network: str
    contract_address: str
    private_key: str
    rpc_url: str

class TestnetMonitoringAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.w3 = Web3(Web3.HTTPProvider(config.rpc_url))
        self.logger = logging.getLogger(f"Agent-{config.agent_id}")
        
        # Load contract ABI and create contract instance
        with open(f"deployment_{config.network}.json", "r") as f:
            deployment_info = json.load(f)
        
        # In production, load actual ABI from compilation
        self.contract = self.w3.eth.contract(
            address=config.contract_address,
            abi=[]  # Load actual ABI here
        )
        
        # Agent state
        self.monitoring = False
        self.event_logs = []
        self.suspicious_patterns = []
        
        # Batch configuration
        self.batch_size = 300_000_000
        self.batch_start = config.batch_index * self.batch_size
        self.batch_end = (config.batch_index + 1) * self.batch_size - 1
        
        self.logger.info(f"Initialized agent for batch {config.batch_index} (tokens {self.batch_start}-{self.batch_end})")
    
    def token_in_batch(self, token_id: int) -> bool:
        """Check if token belongs to this agent's batch"""
        return self.batch_start <= token_id <= self.batch_end
    
    def log_event(self, event_type: str, data: Dict, anchor_onchain: bool = True):
        """Log event with tamper-proof hash"""
        log_entry = {
            "timestamp": int(time.time()),
            "agent_id": self.config.agent_id,
            "batch_index": self.config.batch_index,
            "event_type": event_type,
            "data": data
        }
        
        # Create tamper-proof hash
        log_json = json.dumps(log_entry, sort_keys=True)
        import hashlib
        log_hash = hashlib.sha256(log_json.encode()).hexdigest()
        
        log_entry["hash"] = log_hash
        self.event_logs.append(log_entry)
        
        # Save to file
        with open(f"agent_{self.config.agent_id}_logs.jsonl", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        self.logger.info(f"Logged {event_type}: {log_hash[:8]}...")
        
        # Optionally anchor hash on-chain
        if anchor_onchain:
            self.anchor_log_onchain(log_hash, event_type)
    
    def anchor_log_onchain(self, log_hash: str, event_type: str):
        """Anchor log hash on-chain for tamper-proofing"""
        try:
            # In production, this would call contract.logTamperProof()
            self.logger.info(f"Anchored log on-chain: {log_hash[:8]}... ({event_type})")
        except Exception as e:
            self.logger.error(f"Failed to anchor log: {e}")
    
    def detect_suspicious_activity(self, event_data: Dict) -> bool:
        """Advanced pattern detection for theft/fraud"""
        token_id = event_data.get("tokenId", 0)
        
        if not self.token_in_batch(token_id):
            return False
        
        # Pattern 1: Rapid successive transfers
        recent_transfers = [
            log for log in self.event_logs[-10:] 
            if log["event_type"] == "Transfer" and log["data"].get("tokenId") == token_id
        ]
        
        if len(recent_transfers) >= 3:
            time_span = recent_transfers[-1]["timestamp"] - recent_transfers[0]["timestamp"]
            if time_span < 300:  # 5 minutes
                self.logger.warning(f"Rapid transfers detected for token {token_id}")
                return True
        
        # Pattern 2: Transfer to known suspicious address
        suspicious_addresses = [
            "0x1234567890123456789012345678901234567890",  # Known malicious
            "0x0000000000000000000000000000000000000000",  # Null address
        ]
        
        recipient = event_data.get("to", "").lower()
        if recipient in [addr.lower() for addr in suspicious_addresses]:
            self.logger.warning(f"Transfer to suspicious address: {recipient}")
            return True
        
        # Pattern 3: Unusual transfer amounts or timing
        # Add more sophisticated detection logic here
        
        return False
    
    def handle_transfer_event(self, event_data: Dict):
        """Handle token transfer events"""
        token_id = event_data.get("tokenId", 0)
        
        if not self.token_in_batch(token_id):
            return
        
        # Log the transfer
        self.log_event("Transfer", event_data)
        
        # Check for suspicious activity
        if self.detect_suspicious_activity(event_data):
            self.flag_token(token_id, "suspicious_transfer_pattern")
    
    def flag_token(self, token_id: int, reason: str):
        """Flag a token for suspicious activity"""
        if not self.token_in_batch(token_id):
            return
        
        flag_data = {
            "tokenId": token_id,
            "reason": reason,
            "confidence": 0.85,  # AI confidence score
            "timestamp": int(time.time())
        }
        
        self.log_event("TokenFlagged", flag_data)
        self.logger.warning(f"Token {token_id} flagged: {reason}")
        
        # Auto-burn if high confidence
        if flag_data["confidence"] > 0.8:
            self.burn_token(token_id, reason)
    
    def burn_token(self, token_id: int, reason: str):
        """Burn a compromised token"""
        if not self.token_in_batch(token_id):
            return
        
        burn_data = {
            "tokenId": token_id,
            "reason": reason,
            "serial": f"GS-8055-{token_id:06d}",
            "timestamp": int(time.time()),
            "agent_id": self.config.agent_id
        }
        
        try:
            # In production, call contract.agentBurn(token_id)
            self.log_event("TokenBurned", burn_data)
            self.logger.critical(f"BURNED Token {token_id}: {reason}")
            
            # Trigger remint to treasury
            self.request_remint(token_id, burn_data["serial"])
            
        except Exception as e:
            self.logger.error(f"Failed to burn token {token_id}: {e}")
    
    def request_remint(self, token_id: int, serial: str):
        """Request admin to remint burned token to treasury"""
        remint_request = {
            "tokenId": token_id,
            "serial": serial,
            "treasury": "0x742D35Cc6634C0532925a3b8D371D885dc07C08e",
            "status": "remint_requested",
            "timestamp": int(time.time())
        }
        
        self.log_event("RemintRequested", remint_request)
        self.logger.info(f"Requested remint for token {token_id} with serial {serial}")
    
    def verify_ownership_claim(self, token_id: int, claimant: str) -> bool:
        """Verify ownership claim through agent logs"""
        if not self.token_in_batch(token_id):
            return False
        
        # Find original mint record
        mint_logs = [
            log for log in self.event_logs
            if log["event_type"] == "TokenMinted" and log["data"].get("tokenId") == token_id
        ]
        
        if not mint_logs:
            self.logger.warning(f"No mint record found for token {token_id}")
            return False
        
        original_owner = mint_logs[0]["data"].get("to", "").lower()
        
        verification_result = original_owner == claimant.lower()
        
        verification_data = {
            "tokenId": token_id,
            "claimant": claimant,
            "original_owner": original_owner,
            "verified": verification_result,
            "timestamp": int(time.time())
        }
        
        self.log_event("OwnershipVerification", verification_data)
        
        if verification_result:
            self.logger.info(f"Ownership verified for token {token_id} -> {claimant}")
        else:
            self.logger.warning(f"Ownership verification FAILED for token {token_id}")
        
        return verification_result
    
    def start_monitoring(self):
        """Start monitoring contract events"""
        self.monitoring = True
        self.logger.info(f"Starting monitoring for batch {self.config.batch_index}")
        
        # In production, this would set up event filters and polling
        # For testing, we'll simulate events
        self.simulate_test_events()
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        self.logger.info("Stopped monitoring")
    
    def simulate_test_events(self):
        """Simulate various events for testing"""
        if not self.monitoring:
            return
        
        # Simulate normal minting
        for i in range(5):
            token_id = self.batch_start + i
            mint_data = {
                "tokenId": token_id,
                "to": "0x742D35Cc6634C0532925a3b8D371D885dc07C08e",
                "serial": f"GS-8055-{token_id:06d}",
                "batchId": f"BATCH_{self.config.batch_index:03d}"
            }
            self.log_event("TokenMinted", mint_data)
            time.sleep(0.5)
        
        # Simulate suspicious transfer
        suspicious_token = self.batch_start + 2
        transfer_data = {
            "tokenId": suspicious_token,
            "from": "0x742D35Cc6634C0532925a3b8D371D885dc07C08e",
            "to": "0x1234567890123456789012345678901234567890"  # Suspicious address
        }
        self.handle_transfer_event(transfer_data)
        
        self.logger.info("Test event simulation completed")

# Multi-agent deployment configuration
TESTNET_AGENTS = [
    AgentConfig(
        agent_id="AGENT_001",
        batch_index=0,
        network="sepolia",
        contract_address="0x742D35Cc6634C0532925a3b8D371D885dc07C08e",  # Replace with actual
        private_key="YOUR_AGENT_1_PRIVATE_KEY",
        rpc_url="https://sepolia.infura.io/v3/YOUR_INFURA_KEY"
    ),
    AgentConfig(
        agent_id="AGENT_002", 
        batch_index=1,
        network="sepolia",
        contract_address="0x742D35Cc6634C0532925a3b8D371D885dc07C08e",  # Replace with actual
        private_key="YOUR_AGENT_2_PRIVATE_KEY",
        rpc_url="https://sepolia.infura.io/v3/YOUR_INFURA_KEY"
    )
]

def deploy_testnet_agents():
    """Deploy multiple monitoring agents for testing"""
    agents = []
    
    for config in TESTNET_AGENTS:
        agent = TestnetMonitoringAgent(config)
        agents.append(agent)
        
        # Start monitoring in separate thread
        thread = threading.Thread(target=agent.start_monitoring)
        thread.daemon = True
        thread.start()
        
        time.sleep(1)  # Stagger agent startup
    
    return agents

if __name__ == "__main__":
    print("🤖 Deploying testnet monitoring agents...")
    agents = deploy_testnet_agents()
    
    print(f"✅ Deployed {len(agents)} agents")
    print("📊 Monitoring in progress...")
    
    # Keep running for testing
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n🛑 Stopping agents...")
        for agent in agents:
            agent.stop_monitoring()