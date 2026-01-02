#!/usr/bin/env python3
"""
GuardianShield Node Interaction Protocol System
Multi-layer secure communication between node types
"""

import asyncio
import json
import logging
import os
import socket
import ssl
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse
import aiohttp
import websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class NodeEndpoint:
    """Represents a node endpoint for communication"""
    node_id: str
    node_type: str
    host: str
    port: int
    secure: bool = True
    weight: float = 1.0  # Load balancing weight
    health_score: float = 1.0  # Health status
    region: str = "unknown"
    
@dataclass
class NetworkMessage:
    """Standard message format for inter-node communication"""
    message_id: str
    source_node: str
    source_type: str
    destination_node: str
    destination_type: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: float
    priority: int = 0  # Higher priority = processed first
    requires_response: bool = False
    
class NodeInteractionProtocol:
    """
    Implements secure multi-layer node communication protocols
    
    Architecture:
    - External traffic -> Sentry nodes (rate limiting, attack protection)
    - Sentry nodes -> Observer nodes (analytics, indexing data)
    - Observer nodes -> Validator nodes (consensus data only)
    - Bootnode discovery -> All node types
    """
    
    def __init__(self, node_type: str, node_id: str):
        self.node_type = node_type.lower()
        self.node_id = node_id
        self.endpoints: Dict[str, List[NodeEndpoint]] = {
            'validator': [],
            'sentry': [],
            'observer': [],
            'bootnode': []
        }
        self.message_handlers: Dict[str, callable] = {}
        self.ssl_context = self._create_ssl_context()
        self.rate_limiters: Dict[str, Dict] = {}
        
    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context for secure communications"""
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_REQUIRED
        
        # Load certificates
        cert_dir = os.environ.get('GUARDIAN_CERT_DIR', '/etc/ssl/guardian')
        if os.path.exists(f"{cert_dir}/ca.crt"):
            context.load_verify_locations(f"{cert_dir}/ca.crt")
        if os.path.exists(f"{cert_dir}/node.crt"):
            context.load_cert_chain(f"{cert_dir}/node.crt", f"{cert_dir}/node.key")
            
        return context
    
    def register_endpoint(self, endpoint: NodeEndpoint) -> None:
        """Register a node endpoint for communication"""
        if endpoint.node_type not in self.endpoints:
            self.endpoints[endpoint.node_type] = []
        
        # Remove existing endpoint with same node_id
        self.endpoints[endpoint.node_type] = [
            ep for ep in self.endpoints[endpoint.node_type] 
            if ep.node_id != endpoint.node_id
        ]
        
        # Add new endpoint
        self.endpoints[endpoint.node_type].append(endpoint)
        logger.info(f"Registered {endpoint.node_type} endpoint: {endpoint.node_id}")
        
    def register_message_handler(self, message_type: str, handler: callable) -> None:
        """Register a handler for specific message types"""
        self.message_handlers[message_type] = handler
        logger.info(f"Registered handler for message type: {message_type}")
    
    def can_communicate_with(self, target_type: str) -> bool:
        """Check if this node type can communicate with target node type"""
        # Define allowed communication patterns (multi-layer architecture)
        allowed_patterns = {
            'validator': ['sentry', 'observer'],  # Validators can respond to sentry/observer
            'sentry': ['validator', 'observer', 'bootnode'],  # Sentries connect to all
            'observer': ['sentry', 'validator', 'bootnode'],  # Observers can request from sentry/validator
            'bootnode': ['sentry', 'observer', 'validator']  # Bootnodes help all with discovery
        }
        
        return target_type in allowed_patterns.get(self.node_type, [])
    
    def select_best_endpoint(self, node_type: str) -> Optional[NodeEndpoint]:
        """Select the best available endpoint based on health and load"""
        if node_type not in self.endpoints or not self.endpoints[node_type]:
            return None
        
        # Filter healthy endpoints
        healthy_endpoints = [
            ep for ep in self.endpoints[node_type] 
            if ep.health_score > 0.5
        ]
        
        if not healthy_endpoints:
            return None
        
        # Select endpoint with highest health * weight score
        return max(
            healthy_endpoints, 
            key=lambda ep: ep.health_score * ep.weight
        )
    
    async def send_message(self, 
                          target_type: str, 
                          message_type: str, 
                          payload: Dict[str, Any],
                          target_node: Optional[str] = None,
                          priority: int = 0) -> Optional[Dict[str, Any]]:
        """Send message to target node type with multi-layer routing"""
        
        # Check if communication is allowed
        if not self.can_communicate_with(target_type):
            logger.error(f"{self.node_type} cannot communicate directly with {target_type}")
            return await self._route_through_sentry(target_type, message_type, payload, target_node, priority)
        
        # Select target endpoint
        endpoint = self.select_best_endpoint(target_type)
        if not endpoint:
            logger.error(f"No healthy {target_type} endpoints available")
            return None
        
        # Create message
        message = NetworkMessage(
            message_id=f"{self.node_id}_{int(time.time() * 1000000)}",
            source_node=self.node_id,
            source_type=self.node_type,
            destination_node=target_node or endpoint.node_id,
            destination_type=target_type,
            message_type=message_type,
            payload=payload,
            timestamp=time.time(),
            priority=priority,
            requires_response=True
        )
        
        # Send message based on endpoint type
        if message_type in ['websocket', 'stream']:
            return await self._send_websocket_message(endpoint, message)
        else:
            return await self._send_http_message(endpoint, message)
    
    async def _route_through_sentry(self, 
                                   target_type: str, 
                                   message_type: str, 
                                   payload: Dict[str, Any],
                                   target_node: Optional[str] = None,
                                   priority: int = 0) -> Optional[Dict[str, Any]]:
        """Route message through sentry nodes for indirect communication"""
        logger.info(f"Routing {target_type} request through sentry layer")
        
        # Add routing information to payload
        routing_payload = {
            'original_target_type': target_type,
            'original_target_node': target_node,
            'original_message_type': message_type,
            'original_payload': payload,
            'route_through': 'sentry'
        }
        
        return await self.send_message('sentry', 'route_message', routing_payload, priority=priority)
    
    async def _send_http_message(self, endpoint: NodeEndpoint, message: NetworkMessage) -> Optional[Dict[str, Any]]:
        """Send HTTP/HTTPS message to endpoint"""
        protocol = 'https' if endpoint.secure else 'http'
        url = f"{protocol}://{endpoint.host}:{endpoint.port}/guardian/message"
        
        headers = {
            'Content-Type': 'application/json',
            'Guardian-Node-Type': self.node_type,
            'Guardian-Node-ID': self.node_id,
            'Guardian-Message-Type': message.message_type
        }
        
        try:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context if endpoint.secure else None)
            async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.post(url, json=asdict(message), headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"HTTP message failed: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"HTTP message error: {e}")
            # Mark endpoint as unhealthy
            endpoint.health_score = max(0, endpoint.health_score - 0.1)
            return None
    
    async def _send_websocket_message(self, endpoint: NodeEndpoint, message: NetworkMessage) -> Optional[Dict[str, Any]]:
        """Send WebSocket message to endpoint"""
        protocol = 'wss' if endpoint.secure else 'ws'
        url = f"{protocol}://{endpoint.host}:{endpoint.port}/guardian/ws"
        
        try:
            ssl_context = self.ssl_context if endpoint.secure else None
            async with websockets.connect(url, ssl=ssl_context) as websocket:
                await websocket.send(json.dumps(asdict(message)))
                
                # Wait for response if required
                if message.requires_response:
                    response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    return json.loads(response)
                
                return {'status': 'sent'}
        except Exception as e:
            logger.error(f"WebSocket message error: {e}")
            endpoint.health_score = max(0, endpoint.health_score - 0.1)
            return None
    
    async def handle_incoming_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming message from another node"""
        try:
            message = NetworkMessage(**message_data)
            
            # Validate message source
            if not self._validate_message_source(message):
                return {'error': 'Invalid message source'}
            
            # Check rate limiting
            if not self._check_rate_limit(message.source_node, message.message_type):
                return {'error': 'Rate limit exceeded'}
            
            # Route message if needed
            if message.message_type == 'route_message':
                return await self._handle_route_message(message)
            
            # Handle message with registered handler
            if message.message_type in self.message_handlers:
                handler = self.message_handlers[message.message_type]
                return await handler(message)
            else:
                logger.warning(f"No handler for message type: {message.message_type}")
                return {'error': f'No handler for message type: {message.message_type}'}
                
        except Exception as e:
            logger.error(f"Message handling error: {e}")
            return {'error': f'Message handling error: {str(e)}'}
    
    async def _handle_route_message(self, message: NetworkMessage) -> Dict[str, Any]:
        """Handle message routing through this node (typically sentry nodes)"""
        if self.node_type != 'sentry':
            return {'error': 'Only sentry nodes can route messages'}
        
        payload = message.payload
        target_type = payload.get('original_target_type')
        target_node = payload.get('original_target_node')
        original_message_type = payload.get('original_message_type')
        original_payload = payload.get('original_payload')
        
        # Forward the original message
        return await self.send_message(
            target_type=target_type,
            message_type=original_message_type,
            payload=original_payload,
            target_node=target_node
        )
    
    def _validate_message_source(self, message: NetworkMessage) -> bool:
        """Validate that the message source is authorized"""
        # Basic validation - can be enhanced with cryptographic signatures
        return (
            message.source_type in ['validator', 'sentry', 'observer', 'bootnode'] and
            message.source_node and
            len(message.source_node) > 0
        )
    
    def _check_rate_limit(self, source_node: str, message_type: str) -> bool:
        """Check if message is within rate limits"""
        current_time = time.time()
        key = f"{source_node}:{message_type}"
        
        if key not in self.rate_limiters:
            self.rate_limiters[key] = {'count': 0, 'window_start': current_time}
        
        limiter = self.rate_limiters[key]
        
        # Reset window if needed (1 minute window)
        if current_time - limiter['window_start'] > 60:
            limiter['count'] = 0
            limiter['window_start'] = current_time
        
        # Check limits (configurable per message type)
        limits = {
            'blockchain_data': 1000,  # High frequency data
            'consensus_vote': 100,
            'peer_discovery': 50,
            'health_check': 20,
            'route_message': 500
        }
        
        limit = limits.get(message_type, 10)  # Default limit
        
        if limiter['count'] >= limit:
            return False
        
        limiter['count'] += 1
        return True

class ValidatorInteractionProtocol(NodeInteractionProtocol):
    """Validator-specific interaction protocols"""
    
    def __init__(self, node_id: str):
        super().__init__('validator', node_id)
        
        # Register validator-specific handlers
        self.register_message_handler('consensus_vote', self._handle_consensus_vote)
        self.register_message_handler('block_proposal', self._handle_block_proposal)
        self.register_message_handler('blockchain_sync', self._handle_blockchain_sync)
    
    async def _handle_consensus_vote(self, message: NetworkMessage) -> Dict[str, Any]:
        """Handle consensus voting messages"""
        payload = message.payload
        
        # Validate vote
        if not self._validate_consensus_vote(payload):
            return {'error': 'Invalid consensus vote'}
        
        # Process vote (implementation depends on consensus algorithm)
        logger.info(f"Processing consensus vote from {message.source_node}")
        
        return {
            'status': 'vote_received',
            'validator_id': self.node_id,
            'vote_hash': payload.get('vote_hash')
        }
    
    def _validate_consensus_vote(self, payload: Dict[str, Any]) -> bool:
        """Validate consensus vote payload"""
        required_fields = ['vote_hash', 'block_height', 'timestamp']
        return all(field in payload for field in required_fields)
    
    async def _handle_block_proposal(self, message: NetworkMessage) -> Dict[str, Any]:
        """Handle block proposal messages"""
        payload = message.payload
        
        logger.info(f"Received block proposal: height {payload.get('block_height')}")
        
        # Validate and process block proposal
        if self._validate_block_proposal(payload):
            return {
                'status': 'proposal_accepted',
                'validator_id': self.node_id,
                'block_height': payload.get('block_height')
            }
        else:
            return {
                'status': 'proposal_rejected',
                'validator_id': self.node_id,
                'reason': 'Invalid block proposal'
            }
    
    def _validate_block_proposal(self, payload: Dict[str, Any]) -> bool:
        """Validate block proposal"""
        required_fields = ['block_height', 'block_hash', 'transactions', 'timestamp']
        return all(field in payload for field in required_fields)
    
    async def _handle_blockchain_sync(self, message: NetworkMessage) -> Dict[str, Any]:
        """Handle blockchain synchronization requests"""
        payload = message.payload
        requested_height = payload.get('requested_height', 0)
        
        logger.info(f"Blockchain sync request for height {requested_height}")
        
        # Return blockchain data (simplified)
        return {
            'status': 'sync_data',
            'current_height': requested_height + 100,  # Mock data
            'blocks': [f"block_{i}" for i in range(requested_height, requested_height + 10)]
        }

class SentryInteractionProtocol(NodeInteractionProtocol):
    """Sentry-specific interaction protocols with attack protection"""
    
    def __init__(self, node_id: str):
        super().__init__('sentry', node_id)
        
        # Register sentry-specific handlers
        self.register_message_handler('api_request', self._handle_api_request)
        self.register_message_handler('route_message', self._handle_route_message)
        self.register_message_handler('attack_detection', self._handle_attack_detection)
    
    async def _handle_api_request(self, message: NetworkMessage) -> Dict[str, Any]:
        """Handle API requests from external clients"""
        payload = message.payload
        api_method = payload.get('method')
        
        logger.info(f"API request: {api_method} from {message.source_node}")
        
        # Route to appropriate backend service
        if api_method in ['get_balance', 'get_transaction']:
            return await self.send_message('observer', 'query_data', payload)
        elif api_method in ['submit_transaction']:
            return await self.send_message('validator', 'process_transaction', payload)
        else:
            return {'error': f'Unknown API method: {api_method}'}
    
    async def _handle_attack_detection(self, message: NetworkMessage) -> Dict[str, Any]:
        """Handle attack detection and mitigation"""
        payload = message.payload
        attack_type = payload.get('attack_type')
        source_ip = payload.get('source_ip')
        
        logger.warning(f"Attack detected: {attack_type} from {source_ip}")
        
        # Implement mitigation (rate limiting, IP blocking, etc.)
        mitigation_result = await self._mitigate_attack(attack_type, source_ip)
        
        return {
            'status': 'attack_mitigated',
            'attack_type': attack_type,
            'mitigation': mitigation_result
        }
    
    async def _mitigate_attack(self, attack_type: str, source_ip: str) -> Dict[str, Any]:
        """Implement attack mitigation strategies"""
        # This would integrate with firewall, rate limiting, etc.
        logger.info(f"Implementing mitigation for {attack_type} from {source_ip}")
        
        return {
            'blocked_ip': source_ip,
            'mitigation_type': 'rate_limit_increase',
            'duration': 3600  # 1 hour
        }

# Example usage and initialization
async def initialize_node_protocol(node_type: str, node_id: str) -> NodeInteractionProtocol:
    """Initialize node interaction protocol based on node type"""
    
    if node_type.lower() == 'validator':
        protocol = ValidatorInteractionProtocol(node_id)
    elif node_type.lower() == 'sentry':
        protocol = SentryInteractionProtocol(node_id)
    else:
        protocol = NodeInteractionProtocol(node_type, node_id)
    
    # Register endpoints from environment variables
    await _register_endpoints_from_environment(protocol)
    
    return protocol

async def _register_endpoints_from_environment(protocol: NodeInteractionProtocol):
    """Register node endpoints from environment variables"""
    
    # Example environment variable parsing
    for node_type in ['validator', 'sentry', 'observer', 'bootnode']:
        env_key = f"GUARDIAN_{node_type.upper()}_ENDPOINTS"
        endpoints_str = os.environ.get(env_key, '')
        
        if endpoints_str:
            for endpoint_str in endpoints_str.split(','):
                parts = endpoint_str.strip().split(':')
                if len(parts) >= 3:
                    endpoint = NodeEndpoint(
                        node_id=parts[0],
                        node_type=node_type,
                        host=parts[1],
                        port=int(parts[2]),
                        secure=len(parts) > 3 and parts[3].lower() == 'true',
                        region=parts[4] if len(parts) > 4 else 'unknown'
                    )
                    protocol.register_endpoint(endpoint)

if __name__ == '__main__':
    # Example usage
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python node_interaction_protocol.py <node_type> <node_id>")
        sys.exit(1)
    
    node_type = sys.argv[1]
    node_id = sys.argv[2]
    
    async def main():
        protocol = await initialize_node_protocol(node_type, node_id)
        logger.info(f"Initialized {node_type} protocol for node {node_id}")
        
        # Keep the protocol running
        while True:
            await asyncio.sleep(60)
    
    asyncio.run(main())