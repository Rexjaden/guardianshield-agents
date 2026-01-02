"""
Sentry Node Protection System for GuardianShield Validators
Provides security layer between validators and public internet
"""
import asyncio
import json
import time
import logging
import subprocess
from collections import defaultdict
from datetime import datetime, timedelta

class SentryNodeProtection:
    def __init__(self, config_path="/sentry/config/sentry.json"):
        self.config = self.load_config(config_path)
        self.peer_connections = defaultdict(list)
        self.rate_limits = defaultdict(int)
        self.blocked_peers = set()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def load_config(self, config_path):
        """Load sentry node configuration"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default configuration
            return {
                "max_connections_per_ip": 10,
                "rate_limit_requests_per_minute": 100,
                "validator_private_peers": [
                    "guardian_validator_001@172.20.0.10:26656",
                    "guardian_validator_002@172.20.0.11:26656", 
                    "guardian_validator_003@172.20.0.12:26656"
                ],
                "ddos_protection": {
                    "enabled": True,
                    "max_packet_rate": 1000,
                    "block_duration_minutes": 60
                },
                "firewall_rules": {
                    "allow_rpc_rate_limit": True,
                    "block_suspicious_patterns": True
                }
            }
    
    def setup_firewall_rules(self):
        """Configure iptables rules for DDoS protection"""
        self.logger.info("Setting up firewall rules...")
        
        # Basic DDoS protection rules
        firewall_commands = [
            # Limit new connections per IP
            "iptables -A INPUT -p tcp --dport 26656 -m connlimit --connlimit-above 10 -j REJECT",
            
            # Rate limit RPC requests
            "iptables -A INPUT -p tcp --dport 26657 -m limit --limit 25/min --limit-burst 100 -j ACCEPT",
            "iptables -A INPUT -p tcp --dport 26657 -j DROP",
            
            # SYN flood protection
            "iptables -A INPUT -p tcp --syn -m limit --limit 1/s --limit-burst 3 -j ACCEPT",
            "iptables -A INPUT -p tcp --syn -j DROP",
            
            # Ping flood protection
            "iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 1/s -j ACCEPT",
            "iptables -A INPUT -p icmp --icmp-type echo-request -j DROP"
        ]
        
        for cmd in firewall_commands:
            try:
                subprocess.run(cmd.split(), check=True, capture_output=True)
                self.logger.info(f"Applied rule: {cmd}")
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to apply rule {cmd}: {e}")
    
    def monitor_connections(self):
        """Monitor peer connections for suspicious activity"""
        self.logger.info("Starting connection monitoring...")
        
        while True:
            try:
                # Get current connections
                result = subprocess.run(
                    ["netstat", "-tn"], 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                
                connections = self.parse_netstat_output(result.stdout)
                self.analyze_connections(connections)
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Connection monitoring error: {e}")
                time.sleep(60)
    
    def parse_netstat_output(self, output):
        """Parse netstat output to extract connection info"""
        connections = []
        lines = output.split('\n')
        
        for line in lines:
            if ':26656' in line or ':26657' in line:
                parts = line.split()
                if len(parts) >= 5:
                    local_addr = parts[3]
                    foreign_addr = parts[4]
                    state = parts[5] if len(parts) > 5 else 'UNKNOWN'
                    
                    # Extract IP from address
                    foreign_ip = foreign_addr.split(':')[0]
                    
                    connections.append({
                        'local_addr': local_addr,
                        'foreign_addr': foreign_addr,
                        'foreign_ip': foreign_ip,
                        'state': state,
                        'timestamp': datetime.now()
                    })
        
        return connections
    
    def analyze_connections(self, connections):
        """Analyze connections for suspicious patterns"""
        ip_counts = defaultdict(int)
        
        for conn in connections:
            if conn['state'] == 'ESTABLISHED':
                ip_counts[conn['foreign_ip']] += 1
        
        # Check for IPs with too many connections
        for ip, count in ip_counts.items():
            if count > self.config['max_connections_per_ip']:
                self.logger.warning(f"IP {ip} has {count} connections, blocking...")
                self.block_ip(ip)
    
    def block_ip(self, ip):
        """Block suspicious IP address"""
        if ip not in self.blocked_peers:
            try:
                # Add iptables rule to block IP
                block_cmd = f"iptables -A INPUT -s {ip} -j DROP"
                subprocess.run(block_cmd.split(), check=True)
                
                self.blocked_peers.add(ip)
                self.logger.info(f"Blocked IP: {ip}")
                
                # Schedule unblock after configured duration
                asyncio.create_task(
                    self.schedule_unblock(ip, self.config['ddos_protection']['block_duration_minutes'])
                )
                
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to block IP {ip}: {e}")
    
    async def schedule_unblock(self, ip, duration_minutes):
        """Schedule IP unblocking after specified duration"""
        await asyncio.sleep(duration_minutes * 60)
        
        try:
            # Remove iptables rule
            unblock_cmd = f"iptables -D INPUT -s {ip} -j DROP"
            subprocess.run(unblock_cmd.split(), check=True)
            
            self.blocked_peers.discard(ip)
            self.logger.info(f"Unblocked IP: {ip}")
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to unblock IP {ip}: {e}")
    
    def proxy_to_validators(self, peer_id, message):
        """Proxy validated messages to validator nodes"""
        # Only forward to specific validator nodes
        validator_peers = self.config['validator_private_peers']
        
        for validator in validator_peers:
            try:
                # Forward message to validator (simplified)
                self.logger.debug(f"Forwarding message from {peer_id} to {validator}")
                # In production, implement actual P2P message forwarding
                
            except Exception as e:
                self.logger.error(f"Failed to forward to validator {validator}: {e}")
    
    def health_check(self):
        """Sentry node health check"""
        try:
            # Check if firewall rules are active
            result = subprocess.run(
                ["iptables", "-L", "-n"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            if "26656" not in result.stdout:
                return False, "Firewall rules not active"
            
            # Check blocked IPs count
            blocked_count = len(self.blocked_peers)
            
            return True, f"Sentry healthy, {blocked_count} IPs blocked"
            
        except Exception as e:
            return False, f"Health check failed: {str(e)}"
    
    async def start_protection(self):
        """Start sentry protection services"""
        self.logger.info("Starting GuardianShield Sentry Protection...")
        
        # Setup firewall
        self.setup_firewall_rules()
        
        # Start monitoring in background
        monitor_task = asyncio.create_task(self.run_monitoring())
        
        # Keep running
        try:
            await monitor_task
        except KeyboardInterrupt:
            self.logger.info("Sentry protection stopped")
    
    async def run_monitoring(self):
        """Run connection monitoring loop"""
        while True:
            try:
                # Monitor connections
                await asyncio.sleep(30)
                
                # Health check
                healthy, message = self.health_check()
                if not healthy:
                    self.logger.error(f"Health check failed: {message}")
                
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(60)

async def main():
    """Main sentry protection function"""
    sentry = SentryNodeProtection()
    await sentry.start_protection()

if __name__ == "__main__":
    asyncio.run(main())