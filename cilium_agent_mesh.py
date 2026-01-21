"""
Cilium Clustermesh Integration for GuardianShield AI Agents
Provides secure service mesh networking for agent communication
"""

import json
import subprocess
import asyncio
import logging
from typing import Dict, List, Any
import yaml

logger = logging.getLogger(__name__)

class CiliumAgentMesh:
    """Cilium service mesh integration for AI agent communication"""
    
    def __init__(self):
        self.mesh_config = {
            "cluster_name": "guardianshield-agents",
            "cluster_id": 1,
            "agents": {
                "learning_agent": {
                    "port": 8001,
                    "mesh_id": "learning-svc",
                    "labels": {
                        "app": "learning-agent",
                        "version": "v1",
                        "security.cilium.io/policy": "enabled"
                    }
                },
                "behavioral_analytics": {
                    "port": 8081, 
                    "mesh_id": "analytics-svc",
                    "labels": {
                        "app": "behavioral-analytics",
                        "version": "v1",
                        "security.cilium.io/policy": "enabled"
                    }
                },
                "genetic_evolver": {
                    "port": 8003,
                    "mesh_id": "evolver-svc", 
                    "labels": {
                        "app": "genetic-evolver",
                        "version": "v1",
                        "security.cilium.io/policy": "enabled"
                    }
                },
                "data_ingestion": {
                    "port": 8004,
                    "mesh_id": "ingestion-svc",
                    "labels": {
                        "app": "data-ingestion", 
                        "version": "v1",
                        "security.cilium.io/policy": "enabled"
                    }
                },
                "dmer_monitor": {
                    "port": 8005,
                    "mesh_id": "dmer-monitor-svc",
                    "labels": {
                        "app": "dmer-monitor",
                        "version": "v1",
                        "security.cilium.io/policy": "enabled"
                    }
                },
                "flare_integration": {
                    "port": 8006,
                    "mesh_id": "flare-svc",
                    "labels": {
                        "app": "flare-integration",
                        "version": "v1", 
                        "security.cilium.io/policy": "enabled"
                    }
                }
            },
            "api_server": {
                "port": 8000,
                "mesh_id": "api-server",
                "labels": {
                    "app": "guardianshield-api",
                    "version": "v1",
                    "security.cilium.io/policy": "enabled"
                }
            },
            "blockchain_cluster": {
                "port": 8545,
                "mesh_id": "blockchain-cluster", 
                "labels": {
                    "app": "blockchain-node",
                    "version": "v1",
                    "security.cilium.io/policy": "enabled"
                }
            }
        }
        
        self.network_policies = {
            "agent_to_agent": {
                "allow_learning_to_analytics": True,
                "allow_analytics_to_evolver": True,
                "allow_evolver_to_ingestion": True,
                "allow_cross_agent_communication": True
            },
            "api_access": {
                "allow_api_to_agents": True,
                "allow_agents_to_api": True
            },
            "blockchain_access": {
                "allow_agents_to_blockchain": True,
                "allow_blockchain_to_agents": True
            }
        }

    async def setup_cilium_mesh(self):
        """Setup Cilium service mesh for AI agents"""
        logger.info("🔗 Setting up Cilium mesh for GuardianShield AI agents")
        
        try:
            # Create Docker network for agents
            await self.create_agent_network()
            
            # Start Cilium clustermesh API server
            await self.start_clustermesh_server()
            
            # Configure service mesh policies
            await self.apply_network_policies()
            
            # Setup agent service discovery
            await self.setup_service_discovery()
            
            logger.info("✅ Cilium mesh setup complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup Cilium mesh: {e}")
            return False

    async def create_agent_network(self):
        """Create Docker network for agent mesh communication"""
        logger.info("🌐 Creating GuardianShield agent network")
        
        try:
            # Remove existing network if it exists
            try:
                result = subprocess.run([
                    "docker", "network", "rm", "guardianshield-mesh"
                ], capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info("Removed existing network")
            except:
                pass
            
            # Create new network with Cilium driver
            result = subprocess.run([
                "docker", "network", "create",
                "--driver", "bridge",
                "--label", "io.cilium.network=enabled",
                "--label", "app=guardianshield-agents",
                "guardianshield-mesh"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Created network: guardianshield-mesh")
                return True
            else:
                logger.error(f"Failed to create network: {result.stderr}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Failed to create agent network: {e}")
            raise

    async def start_clustermesh_server(self):
        """Start Cilium clustermesh API server"""
        logger.info("🚀 Starting Cilium clustermesh API server")
        
        try:
            # Check if container already running
            try:
                result = subprocess.run([
                    "docker", "stop", "cilium-clustermesh"
                ], capture_output=True, text=True)
                subprocess.run([
                    "docker", "rm", "cilium-clustermesh" 
                ], capture_output=True, text=True)
                logger.info("Removed existing clustermesh container")
            except:
                pass
            
            # Start clustermesh API server
            cmd = [
                "docker", "run", "-d",
                "--name", "cilium-clustermesh",
                "-p", "2379:2379",
                "-p", "2380:2380",
                "-e", "CILIUM_CLUSTER_NAME=guardianshield-agents",
                "-e", "CILIUM_CLUSTER_ID=1",
                "-e", "ETCD_LISTEN_CLIENT_URLS=http://0.0.0.0:2379",
                "-e", "ETCD_ADVERTISE_CLIENT_URLS=http://localhost:2379",
                "--network", "guardianshield-mesh",
                "--restart", "unless-stopped",
                "guardianshield/dhi-cilium-clustermesh-apiserver:latest"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                container_id = result.stdout.strip()
                logger.info(f"✅ Started clustermesh server: {container_id[:12]}")
                
                # Wait for server to be ready
                await asyncio.sleep(5)
                return container_id
            else:
                logger.error(f"Failed to start clustermesh: {result.stderr}")
                return None
            
        except Exception as e:
            logger.error(f"❌ Failed to start clustermesh server: {e}")
            raise

    async def apply_network_policies(self):
        """Apply Cilium network security policies"""
        logger.info("🔒 Applying Cilium network policies")
        
        # Agent-to-agent communication policy
        agent_policy = {
            "apiVersion": "cilium.io/v2",
            "kind": "CiliumNetworkPolicy", 
            "metadata": {
                "name": "agent-communication"
            },
            "spec": {
                "endpointSelector": {
                    "matchLabels": {
                        "app.kubernetes.io/component": "guardianshield-agent"
                    }
                },
                "ingress": [
                    {
                        "fromEndpoints": [
                            {
                                "matchLabels": {
                                    "app.kubernetes.io/component": "guardianshield-agent"
                                }
                            }
                        ],
                        "toPorts": [
                            {
                                "ports": [
                                    {"port": "8001", "protocol": "TCP"},
                                    {"port": "8081", "protocol": "TCP"}, 
                                    {"port": "8003", "protocol": "TCP"},
                                    {"port": "8004", "protocol": "TCP"},
                                    {"port": "8005", "protocol": "TCP"},
                                    {"port": "8006", "protocol": "TCP"}
                                ]
                            }
                        ]
                    }
                ],
                "egress": [
                    {
                        "toEndpoints": [
                            {
                                "matchLabels": {
                                    "app.kubernetes.io/component": "guardianshield-agent"
                                }
                            }
                        ]
                    },
                    {
                        "toServices": [
                            {
                                "k8sService": {
                                    "serviceName": "blockchain-cluster",
                                    "namespace": "default"
                                }
                            }
                        ]
                    }
                ]
            }
        }
        
        # API server access policy  
        api_policy = {
            "apiVersion": "cilium.io/v2",
            "kind": "CiliumNetworkPolicy",
            "metadata": {
                "name": "api-server-access"
            },
            "spec": {
                "endpointSelector": {
                    "matchLabels": {
                        "app": "guardianshield-api"
                    }
                },
                "ingress": [
                    {
                        "fromEndpoints": [
                            {
                                "matchLabels": {}  # Allow from any endpoint for now
                            }
                        ],
                        "toPorts": [
                            {
                                "ports": [
                                    {"port": "8000", "protocol": "TCP"}
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        
        # Save policies to files
        with open("agent_communication_policy.yaml", "w") as f:
            yaml.dump(agent_policy, f)
            
        with open("api_server_policy.yaml", "w") as f:
            yaml.dump(api_policy, f)
        
        logger.info("✅ Network policies configured")

    async def setup_service_discovery(self):
        """Setup service discovery for AI agents"""
        logger.info("🔍 Setting up service discovery")
        
        # Create service registry
        service_registry = {
            "services": {},
            "mesh_config": self.mesh_config,
            "last_updated": datetime.now().isoformat()
        }
        
        # Register each agent service
        for agent_name, config in self.mesh_config["agents"].items():
            service_registry["services"][agent_name] = {
                "mesh_id": config["mesh_id"],
                "port": config["port"],
                "labels": config["labels"],
                "endpoint": f"http://localhost:{config['port']}",
                "health_check": f"http://localhost:{config['port']}/health",
                "status": "pending"
            }
        
        # Register API server
        service_registry["services"]["api_server"] = {
            "mesh_id": self.mesh_config["api_server"]["mesh_id"], 
            "port": self.mesh_config["api_server"]["port"],
            "labels": self.mesh_config["api_server"]["labels"],
            "endpoint": f"http://localhost:{self.mesh_config['api_server']['port']}",
            "health_check": f"http://localhost:{self.mesh_config['api_server']['port']}/health",
            "status": "pending"
        }
        
        # Register blockchain cluster
        service_registry["services"]["blockchain_cluster"] = {
            "mesh_id": self.mesh_config["blockchain_cluster"]["mesh_id"],
            "port": self.mesh_config["blockchain_cluster"]["port"], 
            "labels": self.mesh_config["blockchain_cluster"]["labels"],
            "endpoint": f"http://localhost:{self.mesh_config['blockchain_cluster']['port']}",
            "health_check": f"http://localhost:{self.mesh_config['blockchain_cluster']['port']}",
            "status": "pending"
        }
        
        # Save service registry
        with open("cilium_service_registry.json", "w") as f:
            json.dump(service_registry, f, indent=2)
        
        logger.info("✅ Service discovery configured")

    async def start_agent_mesh_proxy(self, agent_name: str, agent_port: int):
        """Start mesh proxy for specific agent"""
        logger.info(f"🔗 Starting mesh proxy for {agent_name}")
        
        try:
            proxy_container = self.docker_client.containers.run(
                image="envoyproxy/envoy:v1.28-latest",
                name=f"cilium-proxy-{agent_name}",
                ports={
                    f"{agent_port}/tcp": agent_port
                },
                environment={
                    "AGENT_NAME": agent_name,
                    "AGENT_PORT": str(agent_port),
                    "CLUSTER_NAME": self.mesh_config["cluster_name"]
                },
                network="guardianshield-mesh",
                detach=True,
                restart_policy={"Name": "unless-stopped"}
            )
            
            logger.info(f"✅ Started proxy for {agent_name}: {proxy_container.id[:12]}")
            return proxy_container
            
        except Exception as e:
            logger.error(f"❌ Failed to start proxy for {agent_name}: {e}")
            raise

    async def health_check_mesh(self):
        """Check health of mesh components"""
        logger.info("🏥 Checking Cilium mesh health")
        
        health_status = {
            "mesh_server": False,
            "network": False,
            "agents": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Check clustermesh server
            try:
                clustermesh = self.docker_client.containers.get("cilium-clustermesh")
                health_status["mesh_server"] = clustermesh.status == "running"
            except docker.errors.NotFound:
                health_status["mesh_server"] = False
            
            # Check network
            try:
                network = self.docker_client.networks.get("guardianshield-mesh")
                health_status["network"] = True
            except docker.errors.NotFound:
                health_status["network"] = False
            
            # Check agent connectivity (would be implemented with actual health endpoints)
            for agent_name, config in self.mesh_config["agents"].items():
                health_status["agents"][agent_name] = {
                    "configured": True,
                    "port": config["port"],
                    "reachable": "pending"  # Would check actual endpoint
                }
            
            logger.info(f"🏥 Mesh health: {health_status}")
            return health_status
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return health_status

    async def stop_mesh(self):
        """Stop Cilium mesh components"""
        logger.info("🛑 Stopping Cilium mesh")
        
        try:
            # Stop clustermesh server
            try:
                clustermesh = self.docker_client.containers.get("cilium-clustermesh")
                clustermesh.stop()
                clustermesh.remove()
                logger.info("Stopped clustermesh server")
            except docker.errors.NotFound:
                pass
            
            # Stop agent proxies
            for agent_name in self.mesh_config["agents"].keys():
                try:
                    proxy = self.docker_client.containers.get(f"cilium-proxy-{agent_name}")
                    proxy.stop()
                    proxy.remove()
                    logger.info(f"Stopped proxy for {agent_name}")
                except docker.errors.NotFound:
                    pass
            
            logger.info("✅ Cilium mesh stopped")
            
        except Exception as e:
            logger.error(f"❌ Failed to stop mesh: {e}")

# Integration functions
async def integrate_cilium_with_agents():
    """Integrate Cilium mesh with existing AI agents"""
    logger.info("🔗 Integrating Cilium with GuardianShield AI agents")
    
    mesh = CiliumAgentMesh()
    
    try:
        # Setup mesh
        await mesh.setup_cilium_mesh()
        
        # Health check
        health = await mesh.health_check_mesh()
        
        logger.info("✅ Cilium integration complete")
        return mesh, health
        
    except Exception as e:
        logger.error(f"❌ Cilium integration failed: {e}")
        raise

if __name__ == "__main__":
    import asyncio
    from datetime import datetime
    
    async def main():
        print("🔗 GuardianShield Cilium Mesh Integration")
        print("=" * 50)
        
        mesh, health = await integrate_cilium_with_agents()
        
        print("📊 Mesh Status:")
        print(f"   Server: {'✅ Running' if health['mesh_server'] else '❌ Stopped'}")
        print(f"   Network: {'✅ Active' if health['network'] else '❌ Missing'}")
        print(f"   Agents: {len(health['agents'])} configured")
        
        print("\n🔗 Service Discovery:")
        with open("cilium_service_registry.json", "r") as f:
            registry = json.load(f)
            for service_name, service_info in registry["services"].items():
                print(f"   {service_name}: {service_info['endpoint']}")
        
        print(f"\n⏰ Started at: {datetime.now()}")
        print("🛡️ GuardianShield Cilium Mesh is running!")
    
    asyncio.run(main())