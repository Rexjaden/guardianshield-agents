#!/usr/bin/env python3

"""
GuardianShield Universal Node Manager
Configures and manages different node types from a single base image
"""

import json
import os
import logging
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import subprocess
import yaml

@dataclass
class NodeConfig:
    node_type: str  # validator, sentry, observer, bootnode
    node_id: str
    region: str
    tier: str  # primary, secondary, backup
    network_mode: str  # multi-layer, direct
    security_mode: str  # high, standard, minimal
    
    # Network configuration
    bind_address: str = "0.0.0.0"
    p2p_port: int = 26656
    rpc_port: int = 26657
    api_port: int = 8080
    metrics_port: int = 9090
    
    # Node-specific settings
    node_specific_config: Dict[str, Any] = None
    
    # Interaction configuration
    upstream_nodes: List[Dict[str, str]] = None
    downstream_nodes: List[Dict[str, str]] = None

class GuardianNodeManager:
    def __init__(self, config_file: str = "/etc/guardian/node-config.json"):
        self.config_file = config_file
        self.config = None
        self.logger = self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/var/log/guardian/node-manager.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger("GuardianNodeManager")
    
    def load_config(self) -> NodeConfig:
        """Load node configuration from file and environment"""
        self.logger.info(f"Loading configuration from {self.config_file}")
        
        # Load base configuration from file
        try:
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"Config file not found: {self.config_file}, using environment variables")
            config_data = {}
        
        # Override with environment variables
        config_data.update({
            "node_type": os.getenv("NODE_TYPE", config_data.get("node_type", "")),
            "node_id": os.getenv("NODE_ID", config_data.get("node_id", f"guardian-{os.getenv('NODE_TYPE', 'unknown')}-{os.getenv('NODE_REGION', 'unknown')}")),
            "region": os.getenv("NODE_REGION", config_data.get("region", "us-east")),
            "tier": os.getenv("NODE_TIER", config_data.get("tier", "primary")),
            "network_mode": os.getenv("NETWORK_MODE", config_data.get("network_mode", "multi-layer")),
            "security_mode": os.getenv("SECURITY_MODE", config_data.get("security_mode", "standard"))
        })
        
        if not config_data.get("node_type"):
            raise ValueError("NODE_TYPE must be specified (validator, sentry, observer, bootnode)")
        
        # Load node-specific configuration
        node_specific_file = f"/etc/guardian/{config_data['node_type']}/config.json"
        if os.path.exists(node_specific_file):
            with open(node_specific_file, 'r') as f:
                config_data["node_specific_config"] = json.load(f)
        
        self.config = NodeConfig(**{k: v for k, v in config_data.items() if k in NodeConfig.__dataclass_fields__})
        self.logger.info(f"Loaded configuration for {self.config.node_type} node: {self.config.node_id}")
        return self.config
    
    def configure_validator(self):
        """Configure node as a validator"""
        self.logger.info("Configuring as validator node...")
        
        # Validator-specific security hardening
        self.setup_validator_security()
        
        # Configure key management
        self.setup_validator_keys()
        
        # Configure private networking (only connect to sentries)
        self.setup_validator_networking()
        
        # Create validator supervisor config
        self.create_supervisor_config("validator", {
            "command": "/home/guardian/guardian-venv/bin/python /home/guardian/services/validator_service.py",
            "priority": 100,
            "autorestart": True
        })
        
        self.logger.info("Validator configuration complete")
    
    def configure_sentry(self):
        """Configure node as a sentry shield"""
        self.logger.info("Configuring as sentry node...")
        
        # Configure attack protection
        self.setup_sentry_security()
        
        # Configure load balancing and rate limiting
        self.setup_sentry_networking()
        
        # Configure API gateway
        self.setup_sentry_api()
        
        # Create sentry supervisor config
        self.create_supervisor_config("sentry", {
            "sentry-api": {
                "command": "/home/guardian/guardian-venv/bin/python /home/guardian/services/sentry_api_service.py",
                "priority": 90
            },
            "sentry-shield": {
                "command": "/home/guardian/guardian-venv/bin/python /home/guardian/services/sentry_shield_service.py",
                "priority": 95
            },
            "nginx": {
                "command": "/usr/sbin/nginx -g 'daemon off;'",
                "priority": 80
            }
        })
        
        self.logger.info("Sentry configuration complete")
    
    def configure_observer(self):
        """Configure node as an observer/archive node"""
        self.logger.info("Configuring as observer node...")
        
        # Configure analytics database connections
        self.setup_observer_storage()
        
        # Configure indexing services
        self.setup_observer_indexing()
        
        # Configure analytics API
        self.setup_observer_api()
        
        # Create observer supervisor config
        self.create_supervisor_config("observer", {
            "observer": {
                "command": "/home/guardian/guardian-venv/bin/python /home/guardian/services/blockchain_observer_service.py",
                "priority": 100
            },
            "indexer": {
                "command": "/home/guardian/guardian-venv/bin/python /home/guardian/services/blockchain_indexer_service.py",
                "priority": 95
            },
            "analytics-api": {
                "command": "/home/guardian/guardian-venv/bin/python /home/guardian/services/analytics_api_service.py",
                "priority": 90
            }
        })
        
        self.logger.info("Observer configuration complete")
    
    def configure_bootnode(self):
        """Configure node as a bootnode"""
        self.logger.info("Configuring as bootnode...")
        
        # Minimal security for P2P only
        self.setup_bootnode_security()
        
        # Configure P2P networking only
        self.setup_bootnode_networking()
        
        # Create bootnode supervisor config
        self.create_supervisor_config("bootnode", {
            "bootnode": {
                "command": "/home/guardian/guardian-venv/bin/python /home/guardian/services/bootnode_service.py",
                "priority": 100
            }
        })
        
        self.logger.info("Bootnode configuration complete")
    
    def setup_validator_security(self):
        """Setup high-security configuration for validators"""
        security_script = f"""
        # Validator security hardening
        
        # Disable unnecessary services
        systemctl stop apache2 2>/dev/null || true
        systemctl disable apache2 2>/dev/null || true
        
        # Configure iptables for validator (only sentry access)
        iptables -F
        iptables -P INPUT DROP
        iptables -P FORWARD DROP
        iptables -P OUTPUT ACCEPT
        
        # Allow loopback
        iptables -A INPUT -i lo -j ACCEPT
        
        # Allow established connections
        iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
        
        # Allow SSH (if needed for management)
        iptables -A INPUT -p tcp --dport 22 -j ACCEPT
        
        # Allow P2P from sentry nodes only
        {self._generate_sentry_firewall_rules()}
        
        # Allow RPC from sentry nodes only
        iptables -A INPUT -p tcp --dport 26657 -s 172.20.0.0/16 -j ACCEPT
        
        # Allow metrics from monitoring
        iptables -A INPUT -p tcp --dport 9090 -s 172.20.0.0/16 -j ACCEPT
        
        # Save rules
        iptables-save > /etc/iptables/rules.v4
        """
        
        self._execute_security_script(security_script)
    
    def setup_sentry_security(self):
        """Setup sentry security with attack protection"""
        security_script = f"""
        # Sentry security configuration
        
        # Configure fail2ban for attack protection
        cp /etc/fail2ban/jail.d/guardian-sentry.conf /etc/fail2ban/jail.d/guardian-sentry.local
        systemctl enable fail2ban
        systemctl start fail2ban
        
        # Configure iptables for sentry (public facing)
        iptables -F
        iptables -P INPUT DROP
        iptables -P FORWARD DROP
        iptables -P OUTPUT ACCEPT
        
        # Allow loopback
        iptables -A INPUT -i lo -j ACCEPT
        
        # Allow established connections
        iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
        
        # Allow HTTP/HTTPS with rate limiting
        iptables -A INPUT -p tcp --dport 80 -m limit --limit 100/min --limit-burst 200 -j ACCEPT
        iptables -A INPUT -p tcp --dport 443 -m limit --limit 100/min --limit-burst 200 -j ACCEPT
        
        # Allow RPC with stricter limits
        iptables -A INPUT -p tcp --dport 26657 -m limit --limit 50/min --limit-burst 100 -j ACCEPT
        
        # Allow WebSocket connections
        iptables -A INPUT -p tcp --dport 8080 -m limit --limit 25/min --limit-burst 50 -j ACCEPT
        
        # Allow P2P networking
        iptables -A INPUT -p tcp --dport 26656 -j ACCEPT
        
        # Allow metrics
        iptables -A INPUT -p tcp --dport 9090 -s 172.0.0.0/8 -j ACCEPT
        
        # Save rules
        iptables-save > /etc/iptables/rules.v4
        """
        
        self._execute_security_script(security_script)
    
    def setup_observer_storage(self):
        """Configure storage systems for observer node"""
        # Create database configuration
        db_config = {
            "postgresql": {
                "host": self.config.node_specific_config.get("database", {}).get("host", "observer-postgres"),
                "port": self.config.node_specific_config.get("database", {}).get("port", 5432),
                "database": "guardian_analytics",
                "max_connections": 25
            },
            "redis": {
                "host": self.config.node_specific_config.get("redis", {}).get("host", "observer-redis"),
                "port": 6379,
                "db": 0
            },
            "elasticsearch": {
                "hosts": ["http://observer-elasticsearch:9200"]
            }
        }
        
        # Write storage configuration
        with open("/etc/guardian/observer/storage.json", "w") as f:
            json.dump(db_config, f, indent=2)
    
    def setup_networking(self):
        """Setup network configuration based on network mode"""
        if self.config.network_mode == "multi-layer":
            self.setup_multi_layer_networking()
        else:
            self.setup_direct_networking()
    
    def setup_multi_layer_networking(self):
        """Configure multi-layer networking (through sentry/observer)"""
        network_config = {
            "mode": "multi-layer",
            "upstream_nodes": self._get_upstream_nodes(),
            "downstream_nodes": self._get_downstream_nodes(),
            "discovery_nodes": self._get_discovery_nodes()
        }
        
        # Write network configuration
        with open("/etc/guardian/shared/network.json", "w") as f:
            json.dump(network_config, f, indent=2)
    
    def _get_upstream_nodes(self) -> List[Dict[str, str]]:
        """Get upstream nodes based on node type and network topology"""
        if self.config.node_type == "validator":
            # Validators connect to sentries only
            return [
                {"type": "sentry", "address": "sentry-us-east-01", "port": "26656"},
                {"type": "sentry", "address": "sentry-us-east-02", "port": "26656"},
                {"type": "sentry", "address": "sentry-eu-west-01", "port": "26656"},
                {"type": "sentry", "address": "sentry-eu-west-02", "port": "26656"}
            ]
        elif self.config.node_type == "sentry":
            # Sentries connect to validators and observers
            return [
                {"type": "validator", "address": "validator-us-east", "port": "26657"},
                {"type": "validator", "address": "validator-eu-west", "port": "26657"},
                {"type": "validator", "address": "validator-asia-pacific", "port": "26657"}
            ]
        elif self.config.node_type == "observer":
            # Observers connect to sentries for blockchain data
            return [
                {"type": "sentry", "address": "sentry-us-east-01", "port": "26657"},
                {"type": "sentry", "address": "sentry-eu-west-01", "port": "26657"},
                {"type": "sentry", "address": "sentry-asia-pacific-01", "port": "26657"}
            ]
        else:  # bootnode
            # Bootnodes connect to all types for discovery
            return [
                {"type": "sentry", "address": "sentry-us-east-01", "port": "26656"},
                {"type": "observer", "address": "observer-us-east", "port": "26656"}
            ]
    
    def _get_downstream_nodes(self) -> List[Dict[str, str]]:
        """Get downstream nodes that connect to this node"""
        if self.config.node_type == "sentry":
            # Sentries serve external clients and observers
            return [
                {"type": "observer", "address": "observer-*", "port": "26657"},
                {"type": "external", "address": "*", "port": "8080"}
            ]
        elif self.config.node_type == "validator":
            # Validators only serve sentries
            return [
                {"type": "sentry", "address": "sentry-*", "port": "26657"}
            ]
        else:
            return []
    
    def _get_discovery_nodes(self) -> List[Dict[str, str]]:
        """Get bootnode addresses for peer discovery"""
        return [
            {"address": "bootnode-us-east", "port": "26656"},
            {"address": "bootnode-eu-west", "port": "26656"},
            {"address": "bootnode-asia-pacific", "port": "26656"}
        ]
    
    def create_supervisor_config(self, node_type: str, services: Dict[str, Dict[str, Any]]):
        """Create supervisor configuration for the node type"""
        config_content = """
[supervisord]
nodaemon=true
user=root
logfile=/var/log/guardian/supervisord.log
pidfile=/var/run/supervisord.pid
childlogdir=/var/log/guardian

[unix_http_server]
file=/var/run/supervisor.sock
chmod=0700

[supervisorctl]
serverurl=unix:///var/run/supervisor.sock

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

"""
        
        # Add service configurations
        for service_name, service_config in services.items():
            if isinstance(service_config, dict):
                config_content += f"""
[program:{service_name}]
command={service_config.get('command')}
directory=/home/guardian
user=guardian
autorestart={service_config.get('autorestart', True)}
redirect_stderr=true
stdout_logfile=/var/log/guardian/{service_name}.log
stdout_logfile_maxbytes=100MB
stdout_logfile_backups=5
priority={service_config.get('priority', 999)}
environment=PYTHONUNBUFFERED=1,NODE_TYPE={self.config.node_type},NODE_ID={self.config.node_id}

"""
            else:
                # Simple command string
                config_content += f"""
[program:{node_type}]
command={service_config}
directory=/home/guardian
user=guardian
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/guardian/{node_type}.log
stdout_logfile_maxbytes=100MB
stdout_logfile_backups=5
environment=PYTHONUNBUFFERED=1,NODE_TYPE={self.config.node_type},NODE_ID={self.config.node_id}

"""
        
        # Write supervisor configuration
        with open("/etc/supervisor/supervisord.conf", "w") as f:
            f.write(config_content)
    
    def _generate_sentry_firewall_rules(self) -> str:
        """Generate firewall rules to allow sentry node access"""
        # In a real deployment, these would be the actual sentry IP ranges
        sentry_networks = [
            "172.20.1.0/24",  # Sentry US-East
            "172.20.2.0/24",  # Sentry EU-West  
            "172.20.3.0/24"   # Sentry Asia-Pacific
        ]
        
        rules = []
        for network in sentry_networks:
            rules.append(f"iptables -A INPUT -p tcp --dport 26656 -s {network} -j ACCEPT")
            rules.append(f"iptables -A INPUT -p tcp --dport 26657 -s {network} -j ACCEPT")
        
        return "\n        ".join(rules)
    
    def _execute_security_script(self, script: str):
        """Execute security configuration script"""
        try:
            # Write script to temporary file
            script_file = "/tmp/guardian-security-setup.sh"
            with open(script_file, "w") as f:
                f.write("#!/bin/bash\n")
                f.write("set -euo pipefail\n\n")
                f.write(script)
            
            # Make executable and run
            os.chmod(script_file, 0o755)
            result = subprocess.run(["/bin/bash", script_file], 
                                  capture_output=True, text=True, check=True)
            
            self.logger.info("Security script executed successfully")
            if result.stdout:
                self.logger.debug(f"Security script output: {result.stdout}")
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Security script failed: {e.stderr}")
            raise
        finally:
            # Clean up script file
            if os.path.exists(script_file):
                os.unlink(script_file)
    
    def configure_node(self):
        """Main configuration method - configures node based on type"""
        if not self.config:
            self.load_config()
        
        self.logger.info(f"Configuring {self.config.node_type} node in {self.config.region}")
        
        # Common setup for all nodes
        self.setup_networking()
        
        # Node-specific configuration
        if self.config.node_type == "validator":
            self.configure_validator()
        elif self.config.node_type == "sentry":
            self.configure_sentry()
        elif self.config.node_type == "observer":
            self.configure_observer()
        elif self.config.node_type == "bootnode":
            self.configure_bootnode()
        else:
            raise ValueError(f"Unknown node type: {self.config.node_type}")
        
        self.logger.info(f"Node configuration complete: {self.config.node_id}")
        
        # Save final configuration for runtime use
        with open("/etc/guardian/runtime-config.json", "w") as f:
            json.dump(asdict(self.config), f, indent=2)

if __name__ == "__main__":
    manager = GuardianNodeManager()
    manager.configure_node()