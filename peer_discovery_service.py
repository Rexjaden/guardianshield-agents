"""
GuardianShield Bootnode Peer Discovery Service
Ultra-minimal peer discovery for new nodes joining the network
NO RPC/API - P2P ONLY
"""
import asyncio
import json
import time
import socket
import hashlib
import logging
from collections import defaultdict
from datetime import datetime, timedelta

class BootnodePeerDiscovery:
    def __init__(self, config_path="/bootnode/config/bootnode.json"):
        self.config = self.load_config(config_path)
        self.known_peers = {}  # peer_id -> peer_info
        self.peer_connections = defaultdict(list)  # active connections
        self.discovery_cache = {}  # cached peer lists
        self.start_time = time.time()
        
        # Setup minimal logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [BOOTNODE] %(levelname)s: %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def load_config(self, config_path):
        """Load bootnode configuration"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default minimal config
            return {
                "bootnode_id": "guardian_bootnode_001",
                "p2p_port": 26656,
                "max_peers": 100,  # Conservative limit for bootnodes
                "discovery_interval": 30,
                "peer_timeout": 300,
                "bootstrap_peers": [],
                "chain_id": "guardianshield-mainnet",
                "security": {
                    "rate_limit_per_ip": 10,  # Max 10 connections per IP
                    "ban_threshold": 50,      # Ban after 50 violations
                    "ban_duration": 3600      # 1 hour ban
                }
            }
    
    def generate_peer_id(self, ip, port):
        """Generate unique peer ID"""
        data = f"{ip}:{port}:{self.config['chain_id']}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    async def handle_peer_discovery_request(self, peer_ip, peer_port, peer_data):
        """Handle peer discovery request (P2P only)"""
        peer_id = self.generate_peer_id(peer_ip, peer_port)
        
        self.logger.info(f"Discovery request from {peer_ip}:{peer_port} (ID: {peer_id})")
        
        # Rate limiting check
        if not self.check_rate_limit(peer_ip):
            self.logger.warning(f"Rate limit exceeded for {peer_ip}")
            return None
        
        # Register peer
        self.known_peers[peer_id] = {
            'id': peer_id,
            'ip': peer_ip,
            'port': peer_port,
            'last_seen': time.time(),
            'chain_id': peer_data.get('chain_id'),
            'node_type': peer_data.get('node_type', 'unknown'),
            'version': peer_data.get('version', 'unknown')
        }
        
        # Return peer list for discovery
        peer_list = self.get_peer_list_for_discovery(requesting_peer_id=peer_id)
        
        return {
            'bootnode_id': self.config['bootnode_id'],
            'peers': peer_list,
            'timestamp': time.time(),
            'chain_id': self.config['chain_id']
        }
    
    def get_peer_list_for_discovery(self, requesting_peer_id=None, max_peers=20):
        """Get list of peers for discovery (excluding requester)"""
        current_time = time.time()
        active_peers = []
        
        for peer_id, peer_info in self.known_peers.items():
            # Skip the requesting peer
            if peer_id == requesting_peer_id:
                continue
            
            # Only include recent active peers
            if current_time - peer_info['last_seen'] < self.config['peer_timeout']:
                active_peers.append({
                    'id': peer_info['id'],
                    'ip': peer_info['ip'],
                    'port': peer_info['port'],
                    'node_type': peer_info['node_type']
                })
        
        # Return limited number of peers to prevent overwhelming new nodes
        return active_peers[:max_peers]
    
    def check_rate_limit(self, ip):
        """Check if IP is within rate limits"""
        current_time = time.time()
        
        # Clean old entries
        if hasattr(self, '_rate_limits'):
            self._rate_limits = {
                k: [t for t in times if current_time - t < 60]  # Last minute
                for k, times in self._rate_limits.items()
            }
        else:
            self._rate_limits = {}
        
        # Check current rate
        if ip not in self._rate_limits:
            self._rate_limits[ip] = []
        
        if len(self._rate_limits[ip]) >= self.config['security']['rate_limit_per_ip']:
            return False
        
        # Record this request
        self._rate_limits[ip].append(current_time)
        return True
    
    async def connect_to_bootstrap_peers(self):
        """Connect to other bootstrap peers"""
        for bootstrap_peer in self.config.get('bootstrap_peers', []):
            try:
                host, port = bootstrap_peer.split(':')
                port = int(port)
                
                # Attempt connection to bootstrap peer
                await self.connect_to_peer(host, port)
                
            except Exception as e:
                self.logger.error(f"Failed to connect to bootstrap peer {bootstrap_peer}: {e}")
    
    async def connect_to_peer(self, host, port):
        """Connect to a specific peer for discovery"""
        try:
            # Simple TCP connection for P2P handshake
            reader, writer = await asyncio.open_connection(host, port)
            
            # Send discovery handshake
            handshake = {
                'type': 'discovery_handshake',
                'bootnode_id': self.config['bootnode_id'],
                'chain_id': self.config['chain_id'],
                'timestamp': time.time()
            }
            
            writer.write(json.dumps(handshake).encode() + b'\n')
            await writer.drain()
            
            # Read response
            data = await reader.readline()
            if data:
                response = json.loads(data.decode().strip())
                self.logger.info(f"Connected to peer {host}:{port} - {response.get('node_type', 'unknown')}")
            
            writer.close()
            await writer.wait_closed()
            
        except Exception as e:
            self.logger.debug(f"Connection to {host}:{port} failed: {e}")
    
    async def peer_discovery_server(self):
        """Start P2P peer discovery server"""
        async def handle_client(reader, writer):
            try:
                peer_addr = writer.get_extra_info('peername')
                peer_ip = peer_addr[0] if peer_addr else 'unknown'
                
                # Read peer discovery request
                data = await reader.readline()
                if not data:
                    return
                
                request = json.loads(data.decode().strip())
                
                # Handle discovery request
                response = await self.handle_peer_discovery_request(
                    peer_ip, 
                    request.get('port', 0),
                    request
                )
                
                if response:
                    writer.write(json.dumps(response).encode() + b'\n')
                    await writer.drain()
                
            except Exception as e:
                self.logger.error(f"Error handling client: {e}")
            finally:
                try:
                    writer.close()
                    await writer.wait_closed()
                except:
                    pass
        
        # Start discovery server
        server = await asyncio.start_server(
            handle_client,
            '0.0.0.0',
            self.config['p2p_port']
        )
        
        self.logger.info(f"Bootnode discovery server started on port {self.config['p2p_port']}")
        
        async with server:
            await server.serve_forever()
    
    async def cleanup_stale_peers(self):
        """Periodically clean up stale peer entries"""
        while True:
            try:
                current_time = time.time()
                timeout = self.config['peer_timeout']
                
                stale_peers = [
                    peer_id for peer_id, peer_info in self.known_peers.items()
                    if current_time - peer_info['last_seen'] > timeout
                ]
                
                for peer_id in stale_peers:
                    del self.known_peers[peer_id]
                
                if stale_peers:
                    self.logger.info(f"Cleaned up {len(stale_peers)} stale peers")
                
                # Log current status
                active_peers = len(self.known_peers)
                uptime = int(time.time() - self.start_time)
                self.logger.info(f"Bootnode status: {active_peers} active peers, uptime: {uptime}s")
                
                await asyncio.sleep(self.config['discovery_interval'])
                
            except Exception as e:
                self.logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)
    
    def get_bootnode_stats(self):
        """Get bootnode statistics"""
        current_time = time.time()
        active_peers = len([
            p for p in self.known_peers.values()
            if current_time - p['last_seen'] < self.config['peer_timeout']
        ])
        
        return {
            'bootnode_id': self.config['bootnode_id'],
            'uptime_seconds': int(current_time - self.start_time),
            'total_peers_seen': len(self.known_peers),
            'active_peers': active_peers,
            'chain_id': self.config['chain_id'],
            'discovery_only': True,
            'rpc_enabled': False,
            'api_enabled': False
        }
    
    async def start_bootnode(self):
        """Start bootnode discovery service"""
        self.logger.info(f"Starting GuardianShield Bootnode {self.config['bootnode_id']}")
        self.logger.info("Mode: DISCOVERY ONLY - No RPC/API")
        
        # Start tasks
        tasks = [
            asyncio.create_task(self.peer_discovery_server()),
            asyncio.create_task(self.cleanup_stale_peers()),
            asyncio.create_task(self.connect_to_bootstrap_peers())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            self.logger.info("Bootnode shutting down...")
            for task in tasks:
                task.cancel()

async def main():
    """Main bootnode function"""
    bootnode = BootnodePeerDiscovery()
    
    # Display bootnode info
    stats = bootnode.get_bootnode_stats()
    print(f"GuardianShield Bootnode {stats['bootnode_id']}")
    print(f"Chain ID: {stats['chain_id']}")
    print(f"Mode: Discovery Only (P2P Port: {bootnode.config['p2p_port']})")
    print("Security: No RPC/API - P2P ONLY")
    print("-" * 50)
    
    # Start bootnode
    await bootnode.start_bootnode()

if __name__ == "__main__":
    asyncio.run(main())