#!/usr/bin/env python3
"""
Node Startup Script for GuardianShield Chain
Runs on each distributed blockchain node
"""

import asyncio
import json
import os
import sys
import signal
from guardianshield_chain_core import GuardianShieldNode
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductionNodeRunner:
    """Runs a GuardianShield node in production environment"""
    
    def __init__(self):
        # Get configuration from environment
        self.node_id = os.getenv('GUARDIAN_NODE_ID', 'guardian_node_1')
        self.node_type = os.getenv('GUARDIAN_NODE_TYPE', 'validator')
        self.network_port = int(os.getenv('GUARDIAN_PORT', '8333'))
        self.region = os.getenv('GUARDIAN_REGION', 'us-east-1')
        
        # Load peer configuration
        self.peers = self._load_peer_config()
        
        # Initialize node
        self.node = GuardianShieldNode(self.node_id, self.node_type)
        self.node.port = self.network_port
        
        self.running = False
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _load_peer_config(self) -> list:
        """Load peer configuration from file or environment"""
        try:
            if os.path.exists('/app/network_config.json'):
                with open('/app/network_config.json', 'r') as f:
                    config = json.load(f)
                    return config.get(self.node_id, {}).get('peers', [])
        except Exception as e:
            logger.warning(f"Could not load peer config: {e}")
        
        return []
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    async def start_production_node(self):
        """Start the production blockchain node"""
        logger.info(f"🚀 Starting GuardianShield {self.node_type.title()} Node")
        logger.info(f"   Node ID: {self.node_id}")
        logger.info(f"   Region: {self.region}")
        logger.info(f"   Port: {self.network_port}")
        logger.info(f"   Peers: {len(self.peers)}")
        
        self.running = True
        
        try:
            # Start the node
            node_task = asyncio.create_task(self.node.start_node())
            
            # Start peer connections
            peer_task = asyncio.create_task(self._maintain_peer_connections())
            
            # Start health check server
            health_task = asyncio.create_task(self._start_health_server())
            
            # Wait for shutdown
            while self.running:
                await asyncio.sleep(1)
            
            logger.info("Shutting down node...")
            node_task.cancel()
            peer_task.cancel()
            health_task.cancel()
            
        except Exception as e:
            logger.error(f"Node error: {e}")
        
        logger.info("Node shutdown complete")
    
    async def _maintain_peer_connections(self):
        """Maintain connections to peer nodes"""
        logger.info(f"🌐 Starting peer connections to {len(self.peers)} peers")
        
        while self.running:
            # In a real implementation, this would establish WebSocket
            # connections to other nodes for block and transaction sync
            
            for peer in self.peers[:5]:  # Connect to first 5 peers
                logger.debug(f"Maintaining connection to {peer['id']}")
            
            await asyncio.sleep(30)  # Check connections every 30 seconds
    
    async def _start_health_server(self):
        """Start HTTP health check server"""
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import threading
        
        class HealthHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/health':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    
                    status = {
                        "status": "healthy",
                        "node_id": self.server.node_runner.node_id,
                        "node_type": self.server.node_runner.node_type,
                        "blocks": len(self.server.node_runner.node.blockchain),
                        "mempool": len(self.server.node_runner.node.mempool),
                        "mining": self.server.node_runner.node.mining_active
                    }
                    
                    self.wfile.write(json.dumps(status).encode())
                else:
                    self.send_error(404)
            
            def log_message(self, format, *args):
                pass  # Suppress access logs
        
        try:
            server = HTTPServer(('0.0.0.0', 8334), HealthHandler)
            server.node_runner = self
            
            # Run server in background thread
            server_thread = threading.Thread(target=server.serve_forever, daemon=True)
            server_thread.start()
            
            logger.info("✅ Health check server started on port 8334")
            
            while self.running:
                await asyncio.sleep(1)
                
            server.shutdown()
            
        except Exception as e:
            logger.error(f"Health server error: {e}")

async def main():
    """Main entry point for production node"""
    logger.info("🌟 GuardianShield Production Node Starting...")
    
    runner = ProductionNodeRunner()
    await runner.start_production_node()

if __name__ == "__main__":
    asyncio.run(main())