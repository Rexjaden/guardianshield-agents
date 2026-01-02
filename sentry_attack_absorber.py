"""
GuardianShield Sentry Attack Absorber
Advanced DDoS protection and attack mitigation system
"""
import asyncio
import time
import json
import logging
import subprocess
import psutil
import redis
from collections import defaultdict, deque
from datetime import datetime, timedelta
import netaddr

class SentryAttackAbsorber:
    def __init__(self, config_path="/sentry/config/attack-absorber.json"):
        self.config = self.load_config(config_path)
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # Attack tracking
        self.attack_patterns = defaultdict(list)
        self.blocked_ips = set()
        self.suspicious_ips = defaultdict(int)
        self.connection_tracker = defaultdict(list)
        
        # DDoS detection thresholds
        self.ddos_thresholds = {
            'requests_per_second': 100,
            'connections_per_ip': 50,
            'bandwidth_mbps': 1000,
            'cpu_threshold': 80,
            'memory_threshold': 85
        }
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [ATTACK-ABSORBER] %(levelname)s: %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def load_config(self, config_path):
        """Load attack absorber configuration"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "sentry_id": "guardian_sentry_absorber_001",
                "protection_modes": {
                    "ddos_protection": True,
                    "slowloris_protection": True,
                    "flood_protection": True,
                    "malware_protection": True,
                    "bot_protection": True
                },
                "auto_mitigation": {
                    "enabled": True,
                    "block_threshold": 100,
                    "block_duration_minutes": 60,
                    "escalation_enabled": True
                },
                "whitelist_ips": [
                    "127.0.0.1",
                    "10.0.0.0/8",
                    "172.16.0.0/12",
                    "192.168.0.0/16"
                ],
                "blacklist_ips": [],
                "geoblocking": {
                    "enabled": False,
                    "blocked_countries": []
                }
            }
    
    def is_whitelisted(self, ip):
        """Check if IP is whitelisted"""
        try:
            ip_obj = netaddr.IPAddress(ip)
            for whitelist_range in self.config['whitelist_ips']:
                if ip_obj in netaddr.IPNetwork(whitelist_range):
                    return True
            return False
        except:
            return False
    
    def is_blacklisted(self, ip):
        """Check if IP is blacklisted"""
        try:
            ip_obj = netaddr.IPAddress(ip)
            for blacklist_range in self.config['blacklist_ips']:
                if ip_obj in netaddr.IPNetwork(blacklist_range):
                    return True
            return False
        except:
            return False
    
    async def detect_ddos_patterns(self):
        """Detect DDoS attack patterns"""
        while True:
            try:
                current_time = time.time()
                
                # Get system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent
                network_io = psutil.net_io_counters()
                
                # Get active connections
                connections = psutil.net_connections(kind='inet')
                connection_count = len([c for c in connections if c.status == 'ESTABLISHED'])
                
                # Detect high resource usage (potential DDoS)
                if cpu_percent > self.ddos_thresholds['cpu_threshold']:
                    await self.trigger_ddos_mitigation("HIGH_CPU", f"CPU: {cpu_percent}%")
                
                if memory_percent > self.ddos_thresholds['memory_threshold']:
                    await self.trigger_ddos_mitigation("HIGH_MEMORY", f"Memory: {memory_percent}%")
                
                # Analyze connection patterns
                await self.analyze_connection_patterns(connections)
                
                # Log status
                self.logger.info(
                    f"System Status - CPU: {cpu_percent}%, Memory: {memory_percent}%, "
                    f"Connections: {connection_count}, Blocked IPs: {len(self.blocked_ips)}"
                )
                
                await asyncio.sleep(10)
                
            except Exception as e:
                self.logger.error(f"DDoS detection error: {e}")
                await asyncio.sleep(30)
    
    async def analyze_connection_patterns(self, connections):
        """Analyze network connections for attack patterns"""
        current_time = time.time()
        ip_connections = defaultdict(int)
        
        # Count connections per IP
        for conn in connections:
            if conn.raddr and conn.status == 'ESTABLISHED':
                client_ip = conn.raddr.ip
                ip_connections[client_ip] += 1
        
        # Check for connection flooding
        for ip, count in ip_connections.items():
            if count > self.ddos_thresholds['connections_per_ip'] and not self.is_whitelisted(ip):
                await self.handle_suspicious_ip(ip, "CONNECTION_FLOOD", f"{count} connections")
    
    async def handle_suspicious_ip(self, ip, attack_type, details):
        """Handle suspicious IP address"""
        self.suspicious_ips[ip] += 1
        
        attack_info = {
            'ip': ip,
            'attack_type': attack_type,
            'details': details,
            'timestamp': time.time(),
            'count': self.suspicious_ips[ip]
        }
        
        self.attack_patterns[ip].append(attack_info)
        self.logger.warning(f"Suspicious activity from {ip}: {attack_type} - {details}")
        
        # Auto-block if threshold exceeded
        if (self.suspicious_ips[ip] >= self.config['auto_mitigation']['block_threshold'] 
            and self.config['auto_mitigation']['enabled']
            and not self.is_whitelisted(ip)):
            
            await self.block_ip(ip, attack_type)
    
    async def block_ip(self, ip, reason):
        """Block IP address using iptables"""
        if ip in self.blocked_ips:
            return
        
        try:
            # Add iptables rule to block IP
            block_cmd = f"iptables -I INPUT 1 -s {ip} -j DROP"
            result = subprocess.run(block_cmd.split(), capture_output=True, text=True)
            
            if result.returncode == 0:
                self.blocked_ips.add(ip)
                self.logger.info(f"BLOCKED IP {ip} for {reason}")
                
                # Store in Redis for persistence
                block_info = {
                    'ip': ip,
                    'reason': reason,
                    'blocked_at': time.time(),
                    'expires_at': time.time() + (self.config['auto_mitigation']['block_duration_minutes'] * 60)
                }
                
                self.redis_client.hset('blocked_ips', ip, json.dumps(block_info))
                
                # Schedule unblock
                asyncio.create_task(self.schedule_unblock(ip))
                
            else:
                self.logger.error(f"Failed to block IP {ip}: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"Error blocking IP {ip}: {e}")
    
    async def schedule_unblock(self, ip):
        """Schedule IP unblocking"""
        unblock_delay = self.config['auto_mitigation']['block_duration_minutes'] * 60
        await asyncio.sleep(unblock_delay)
        await self.unblock_ip(ip)
    
    async def unblock_ip(self, ip):
        """Unblock IP address"""
        if ip not in self.blocked_ips:
            return
        
        try:
            # Remove iptables rule
            unblock_cmd = f"iptables -D INPUT -s {ip} -j DROP"
            result = subprocess.run(unblock_cmd.split(), capture_output=True, text=True)
            
            if result.returncode == 0:
                self.blocked_ips.discard(ip)
                self.logger.info(f"UNBLOCKED IP {ip}")
                
                # Remove from Redis
                self.redis_client.hdel('blocked_ips', ip)
                
                # Reset suspicious count
                self.suspicious_ips[ip] = 0
                
            else:
                self.logger.error(f"Failed to unblock IP {ip}: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"Error unblocking IP {ip}: {e}")
    
    async def trigger_ddos_mitigation(self, attack_type, details):
        """Trigger emergency DDoS mitigation"""
        self.logger.critical(f"DDoS ATTACK DETECTED: {attack_type} - {details}")
        
        # Implement emergency measures
        if attack_type == "HIGH_CPU":
            await self.implement_cpu_protection()
        elif attack_type == "HIGH_MEMORY":
            await self.implement_memory_protection()
        
        # Log to Redis for alerting
        alert = {
            'type': 'DDOS_ALERT',
            'attack_type': attack_type,
            'details': details,
            'timestamp': time.time(),
            'sentry_id': self.config['sentry_id']
        }
        
        self.redis_client.lpush('ddos_alerts', json.dumps(alert))
        self.redis_client.expire('ddos_alerts', 3600)
    
    async def implement_cpu_protection(self):
        """Implement CPU protection measures"""
        self.logger.info("Implementing CPU protection measures")
        
        # Reduce connection limits
        try:
            subprocess.run([
                "iptables", "-A", "INPUT", "-p", "tcp", "--syn", 
                "-m", "limit", "--limit", "10/s", "--limit-burst", "20", "-j", "ACCEPT"
            ])
            subprocess.run([
                "iptables", "-A", "INPUT", "-p", "tcp", "--syn", "-j", "DROP"
            ])
        except Exception as e:
            self.logger.error(f"Failed to implement CPU protection: {e}")
    
    async def implement_memory_protection(self):
        """Implement memory protection measures"""
        self.logger.info("Implementing memory protection measures")
        
        # Limit concurrent connections more aggressively
        try:
            subprocess.run([
                "iptables", "-A", "INPUT", "-p", "tcp", 
                "-m", "connlimit", "--connlimit-above", "20", "-j", "REJECT"
            ])
        except Exception as e:
            self.logger.error(f"Failed to implement memory protection: {e}")
    
    async def restore_blocked_ips_from_redis(self):
        """Restore blocked IPs from Redis on startup"""
        try:
            blocked_data = self.redis_client.hgetall('blocked_ips')
            current_time = time.time()
            
            for ip, data_str in blocked_data.items():
                try:
                    block_info = json.loads(data_str)
                    
                    # Check if block is still valid
                    if current_time < block_info['expires_at']:
                        self.blocked_ips.add(ip)
                        
                        # Re-apply iptables rule
                        block_cmd = f"iptables -I INPUT 1 -s {ip} -j DROP"
                        subprocess.run(block_cmd.split(), capture_output=True)
                        
                        # Schedule unblock
                        remaining_time = block_info['expires_at'] - current_time
                        asyncio.create_task(self.delayed_unblock(ip, remaining_time))
                        
                        self.logger.info(f"Restored block for IP {ip}")
                    else:
                        # Remove expired block
                        self.redis_client.hdel('blocked_ips', ip)
                        
                except Exception as e:
                    self.logger.error(f"Error restoring block for IP {ip}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error restoring blocked IPs: {e}")
    
    async def delayed_unblock(self, ip, delay):
        """Unblock IP after delay"""
        await asyncio.sleep(delay)
        await self.unblock_ip(ip)
    
    async def cleanup_old_attack_data(self):
        """Clean up old attack pattern data"""
        while True:
            try:
                current_time = time.time()
                cleanup_threshold = current_time - 3600  # 1 hour
                
                # Clean up old attack patterns
                for ip in list(self.attack_patterns.keys()):
                    self.attack_patterns[ip] = [
                        attack for attack in self.attack_patterns[ip]
                        if attack['timestamp'] > cleanup_threshold
                    ]
                    
                    if not self.attack_patterns[ip]:
                        del self.attack_patterns[ip]
                
                # Clean up suspicious IP counts
                for ip in list(self.suspicious_ips.keys()):
                    if ip not in self.attack_patterns:
                        self.suspicious_ips[ip] = max(0, self.suspicious_ips[ip] - 1)
                        if self.suspicious_ips[ip] == 0:
                            del self.suspicious_ips[ip]
                
                await asyncio.sleep(300)  # Clean every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Cleanup error: {e}")
                await asyncio.sleep(600)
    
    def get_attack_statistics(self):
        """Get current attack statistics"""
        current_time = time.time()
        recent_threshold = current_time - 300  # Last 5 minutes
        
        recent_attacks = []
        for ip, attacks in self.attack_patterns.items():
            recent_attacks.extend([
                attack for attack in attacks
                if attack['timestamp'] > recent_threshold
            ])
        
        attack_types = defaultdict(int)
        for attack in recent_attacks:
            attack_types[attack['attack_type']] += 1
        
        return {
            'sentry_id': self.config['sentry_id'],
            'blocked_ips': len(self.blocked_ips),
            'suspicious_ips': len(self.suspicious_ips),
            'recent_attacks': len(recent_attacks),
            'attack_types': dict(attack_types),
            'uptime': time.time() - getattr(self, 'start_time', time.time())
        }
    
    async def start_attack_absorber(self):
        """Start the attack absorption system"""
        self.start_time = time.time()
        self.logger.info("Starting GuardianShield Sentry Attack Absorber")
        self.logger.info("DDoS Protection: ACTIVE")
        self.logger.info("Auto-Mitigation: ENABLED")
        
        # Restore blocked IPs from previous session
        await self.restore_blocked_ips_from_redis()
        
        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self.detect_ddos_patterns()),
            asyncio.create_task(self.cleanup_old_attack_data())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            self.logger.info("Attack absorber shutting down...")

async def main():
    """Main attack absorber function"""
    absorber = SentryAttackAbsorber()
    
    # Display status
    stats = absorber.get_attack_statistics()
    print(f"GuardianShield Sentry Attack Absorber")
    print(f"Sentry ID: {stats['sentry_id']}")
    print(f"Protection: MAXIMUM")
    print(f"Status: ACTIVE")
    print("-" * 50)
    
    await absorber.start_attack_absorber()

if __name__ == "__main__":
    asyncio.run(main())