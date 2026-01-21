#!/usr/bin/env python3
"""
DHI Cluster Autoscaler Configuration
"""

import os
import yaml
import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger('dhi-autoscaler.config')

DEFAULT_CONFIG = {
    # Node scaling limits
    'min_nodes': 3,
    'max_nodes': 50,
    'initial_nodes': 5,
    
    # Scaling thresholds
    'scale_up_threshold': 0.8,
    'scale_down_threshold': 0.3,
    'cooldown_period': 60,
    
    # Check interval
    'check_interval': 10,
    
    # Blockchain configuration
    'chain_id': 'guardianshield-mainnet',
    'orchestrator_url': 'http://gs-node-orchestrator:3003',
    'validator_ports': [26657, 26658, 26659],
    
    # Regions for node distribution
    'regions': ['us-east', 'eu-west', 'asia-pacific'],
    
    # Resource limits per node
    'node_memory_limit': '512m',
    'node_cpu_limit': 0.5,
    
    # API configuration
    'api_port': 8080,
    'metrics_enabled': True
}


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from file or environment"""
    config = DEFAULT_CONFIG.copy()
    
    # Try to load from YAML file
    if Path(config_path).exists():
        try:
            with open(config_path, 'r') as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    config.update(file_config)
            logger.info(f"✅ Loaded config from {config_path}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load config file: {e}")
    
    # Override with environment variables
    env_mappings = {
        'AUTOSCALER_MIN_NODES': ('min_nodes', int),
        'AUTOSCALER_MAX_NODES': ('max_nodes', int),
        'AUTOSCALER_INITIAL_NODES': ('initial_nodes', int),
        'AUTOSCALER_SCALE_UP_THRESHOLD': ('scale_up_threshold', float),
        'AUTOSCALER_SCALE_DOWN_THRESHOLD': ('scale_down_threshold', float),
        'AUTOSCALER_COOLDOWN': ('cooldown_period', int),
        'AUTOSCALER_CHECK_INTERVAL': ('check_interval', int),
        'GUARDIAN_CHAIN_ID': ('chain_id', str),
        'GUARDIAN_ORCHESTRATOR_URL': ('orchestrator_url', str),
        'AUTOSCALER_API_PORT': ('api_port', int),
    }
    
    for env_var, (config_key, type_fn) in env_mappings.items():
        if env_var in os.environ:
            try:
                config[config_key] = type_fn(os.environ[env_var])
                logger.info(f"✅ Config override from env: {config_key}={config[config_key]}")
            except ValueError as e:
                logger.warning(f"⚠️ Invalid env value for {env_var}: {e}")
    
    # Parse regions from env if provided
    if 'AUTOSCALER_REGIONS' in os.environ:
        config['regions'] = os.environ['AUTOSCALER_REGIONS'].split(',')
    
    logger.info(f"📋 Configuration loaded: min={config['min_nodes']}, max={config['max_nodes']}, initial={config['initial_nodes']}")
    
    return config
