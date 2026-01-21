#!/usr/bin/env python3
"""
DHI Cluster Autoscaler Core - Mining Node Scaling Engine
"""

import asyncio
import logging
import docker
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger('dhi-autoscaler.core')

# Prometheus metrics
NODES_TOTAL = Gauge('guardian_mining_nodes_total', 'Total mining nodes')
NODES_ACTIVE = Gauge('guardian_mining_nodes_active', 'Active mining nodes')
SCALE_UP_TOTAL = Counter('guardian_scale_up_total', 'Total scale up events')
SCALE_DOWN_TOTAL = Counter('guardian_scale_down_total', 'Total scale down events')
BLOCKS_MINED = Counter('guardian_blocks_mined_total', 'Total blocks mined')
SCALING_LATENCY = Histogram('guardian_scaling_latency_seconds', 'Scaling operation latency')


@dataclass
class MiningNode:
    """Represents a mining node in the cluster"""
    node_id: str
    container_id: str
    region: str
    status: str = "initializing"
    blocks_mined: int = 0
    hash_rate: float = 0.0
    last_block_time: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    health_checks_failed: int = 0


@dataclass
class ScalingDecision:
    """Represents a scaling decision"""
    action: str  # "scale_up" or "scale_down"
    target_nodes: int
    reason: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ClusterAutoscaler:
    """
    DHI Kubernetes Cluster Autoscaler for GuardianShield Mining Network
    
    Features:
    - Automatic node scaling based on blockchain demand
    - Multi-region node distribution
    - Health monitoring and self-healing
    - Integration with existing validators
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.docker_client = None
        self.running = False
        
        # Node management
        self.mining_nodes: Dict[str, MiningNode] = {}
        self.scaling_history: List[ScalingDecision] = []
        
        # Scaling parameters
        self.min_nodes = config.get('min_nodes', 3)
        self.max_nodes = config.get('max_nodes', 50)
        self.target_nodes = config.get('initial_nodes', 5)
        self.scale_up_threshold = config.get('scale_up_threshold', 0.8)
        self.scale_down_threshold = config.get('scale_down_threshold', 0.3)
        self.cooldown_period = config.get('cooldown_period', 60)
        
        # Network configuration
        self.chain_id = config.get('chain_id', 'guardianshield-mainnet')
        self.regions = config.get('regions', ['us-east', 'eu-west', 'asia-pacific'])
        
        # Blockchain integration
        self.orchestrator_url = config.get('orchestrator_url', 'http://gs-node-orchestrator:3003')
        self.validator_ports = config.get('validator_ports', [26657, 26658, 26659])
        
        # Timing
        self.last_scale_time = 0
        self.check_interval = config.get('check_interval', 10)
        
        logger.info(f"✅ Autoscaler initialized: min={self.min_nodes}, max={self.max_nodes}, target={self.target_nodes}")
    
    async def start(self):
        """Start the autoscaler main loop"""
        logger.info("🚀 Starting ClusterAutoscaler main loop")
        self.running = True
        
        # Initialize Docker client
        try:
            self.docker_client = docker.from_env()
            logger.info("✅ Docker client connected")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Docker: {e}")
            raise
        
        # Discover existing nodes
        await self.discover_existing_nodes()
        
        # Scale to initial target
        await self.scale_to_target(self.target_nodes, "Initial scaling on startup")
        
        # Main autoscaling loop
        while self.running:
            try:
                await self.autoscale_cycle()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"❌ Error in autoscale cycle: {e}")
                await asyncio.sleep(5)
        
        logger.info("⚠️ Autoscaler main loop stopped")
    
    async def shutdown(self):
        """Gracefully shutdown the autoscaler"""
        logger.info("⚠️ Shutting down autoscaler...")
        self.running = False
        
        if self.docker_client:
            self.docker_client.close()
    
    async def discover_existing_nodes(self):
        """Discover existing mining nodes in the cluster"""
        logger.info("🔍 Discovering existing mining nodes...")
        
        try:
            containers = self.docker_client.containers.list(
                filters={'label': 'guardian.type=mining-node'}
            )
            
            for container in containers:
                node = MiningNode(
                    node_id=container.labels.get('guardian.node-id', container.short_id),
                    container_id=container.id,
                    region=container.labels.get('guardian.region', 'unknown'),
                    status='running' if container.status == 'running' else 'stopped'
                )
                self.mining_nodes[node.node_id] = node
            
            logger.info(f"✅ Discovered {len(self.mining_nodes)} existing mining nodes")
            NODES_TOTAL.set(len(self.mining_nodes))
            
        except Exception as e:
            logger.error(f"❌ Error discovering nodes: {e}")
    
    async def autoscale_cycle(self):
        """Single autoscaling evaluation cycle"""
        # Update node health
        await self.check_node_health()
        
        # Get current metrics
        active_nodes = sum(1 for n in self.mining_nodes.values() if n.status == 'running')
        total_nodes = len(self.mining_nodes)
        
        NODES_ACTIVE.set(active_nodes)
        NODES_TOTAL.set(total_nodes)
        
        # Check if in cooldown
        if time.time() - self.last_scale_time < self.cooldown_period:
            return
        
        # Calculate utilization
        utilization = active_nodes / max(total_nodes, 1)
        
        # Scaling decisions
        if utilization > self.scale_up_threshold and total_nodes < self.max_nodes:
            # Scale up
            new_target = min(total_nodes + self.calculate_scale_increment(), self.max_nodes)
            await self.scale_to_target(new_target, f"High utilization: {utilization:.2%}")
            
        elif utilization < self.scale_down_threshold and total_nodes > self.min_nodes:
            # Scale down
            new_target = max(total_nodes - 1, self.min_nodes)
            await self.scale_to_target(new_target, f"Low utilization: {utilization:.2%}")
    
    def calculate_scale_increment(self) -> int:
        """Calculate how many nodes to add based on current load"""
        current = len(self.mining_nodes)
        
        if current < 10:
            return 2
        elif current < 25:
            return 3
        else:
            return 5
    
    async def scale_to_target(self, target: int, reason: str):
        """Scale cluster to target number of nodes"""
        current = len(self.mining_nodes)
        
        if target == current:
            return
        
        logger.info(f"📊 Scaling from {current} to {target} nodes. Reason: {reason}")
        
        with SCALING_LATENCY.time():
            if target > current:
                # Scale up
                nodes_to_add = target - current
                await self.scale_up(nodes_to_add)
                SCALE_UP_TOTAL.inc(nodes_to_add)
                
            else:
                # Scale down
                nodes_to_remove = current - target
                await self.scale_down(nodes_to_remove)
                SCALE_DOWN_TOTAL.inc(nodes_to_remove)
        
        # Record decision
        decision = ScalingDecision(
            action="scale_up" if target > current else "scale_down",
            target_nodes=target,
            reason=reason
        )
        self.scaling_history.append(decision)
        self.last_scale_time = time.time()
        
        logger.info(f"✅ Scaling complete. Current nodes: {len(self.mining_nodes)}")
    
    async def scale_up(self, count: int):
        """Add new mining nodes to the cluster"""
        logger.info(f"⬆️ Scaling up: adding {count} mining nodes")
        
        for i in range(count):
            region = self.regions[len(self.mining_nodes) % len(self.regions)]
            await self.create_mining_node(region)
            await asyncio.sleep(1)  # Stagger node creation
    
    async def scale_down(self, count: int):
        """Remove mining nodes from the cluster"""
        logger.info(f"⬇️ Scaling down: removing {count} mining nodes")
        
        # Select nodes to remove (prefer unhealthy or least productive)
        nodes_to_remove = sorted(
            self.mining_nodes.values(),
            key=lambda n: (n.health_checks_failed, -n.blocks_mined)
        )[:count]
        
        for node in nodes_to_remove:
            await self.remove_mining_node(node.node_id)
            await asyncio.sleep(1)
    
    async def create_mining_node(self, region: str) -> Optional[MiningNode]:
        """Create a new mining node container"""
        node_id = f"mining-node-{region}-{int(time.time())}"
        
        try:
            logger.info(f"🔨 Creating mining node: {node_id} in {region}")
            
            container = self.docker_client.containers.run(
                image="guardianshield-agents-guardian-validator:latest",
                name=f"guardian-{node_id}",
                detach=True,
                labels={
                    'guardian.type': 'mining-node',
                    'guardian.node-id': node_id,
                    'guardian.region': region,
                    'guardian.chain-id': self.chain_id,
                    'guardian.managed-by': 'dhi-cluster-autoscaler'
                },
                environment={
                    'NODE_ID': node_id,
                    'REGION': region,
                    'CHAIN_ID': self.chain_id,
                    'ORCHESTRATOR_URL': self.orchestrator_url,
                    'GUARDIAN_SHIELD_WALLET': '0xF262b772c2EBf526a5cF8634CA92597583Ef38ee',
                    'GUARDIAN_SHIELD_API_KEY': 'J8QD4YPCWIRT3G1WFGHIC7YWGDBJ4VMGZ4'
                },
                network='guardianshield-network',
                restart_policy={'Name': 'unless-stopped'},
                mem_limit='512m',
                cpu_period=100000,
                cpu_quota=50000  # 50% CPU limit
            )
            
            node = MiningNode(
                node_id=node_id,
                container_id=container.id,
                region=region,
                status='running'
            )
            
            self.mining_nodes[node_id] = node
            logger.info(f"✅ Created mining node: {node_id}")
            
            return node
            
        except Exception as e:
            logger.error(f"❌ Failed to create mining node {node_id}: {e}")
            return None
    
    async def remove_mining_node(self, node_id: str):
        """Remove a mining node container"""
        if node_id not in self.mining_nodes:
            return
        
        node = self.mining_nodes[node_id]
        
        try:
            logger.info(f"🗑️ Removing mining node: {node_id}")
            
            container = self.docker_client.containers.get(node.container_id)
            container.stop(timeout=30)
            container.remove()
            
            del self.mining_nodes[node_id]
            logger.info(f"✅ Removed mining node: {node_id}")
            
        except docker.errors.NotFound:
            logger.warning(f"⚠️ Container not found for node: {node_id}")
            del self.mining_nodes[node_id]
        except Exception as e:
            logger.error(f"❌ Failed to remove mining node {node_id}: {e}")
    
    async def check_node_health(self):
        """Check health of all mining nodes"""
        for node_id, node in list(self.mining_nodes.items()):
            try:
                container = self.docker_client.containers.get(node.container_id)
                
                if container.status == 'running':
                    node.status = 'running'
                    node.health_checks_failed = 0
                else:
                    node.status = container.status
                    node.health_checks_failed += 1
                    
                    # Restart unhealthy nodes
                    if node.health_checks_failed >= 3:
                        logger.warning(f"⚠️ Restarting unhealthy node: {node_id}")
                        container.restart()
                        node.health_checks_failed = 0
                        
            except docker.errors.NotFound:
                logger.warning(f"⚠️ Node container not found: {node_id}")
                del self.mining_nodes[node_id]
            except Exception as e:
                logger.error(f"❌ Health check failed for {node_id}: {e}")
                node.health_checks_failed += 1
    
    def get_status(self) -> Dict[str, Any]:
        """Get current autoscaler status"""
        return {
            'running': self.running,
            'total_nodes': len(self.mining_nodes),
            'active_nodes': sum(1 for n in self.mining_nodes.values() if n.status == 'running'),
            'min_nodes': self.min_nodes,
            'max_nodes': self.max_nodes,
            'target_nodes': self.target_nodes,
            'regions': self.regions,
            'chain_id': self.chain_id,
            'nodes': {
                node_id: {
                    'region': node.region,
                    'status': node.status,
                    'blocks_mined': node.blocks_mined,
                    'created_at': node.created_at.isoformat()
                }
                for node_id, node in self.mining_nodes.items()
            },
            'recent_scaling': [
                {
                    'action': d.action,
                    'target': d.target_nodes,
                    'reason': d.reason,
                    'timestamp': d.timestamp.isoformat()
                }
                for d in self.scaling_history[-10:]
            ]
        }
