#!/usr/bin/env python3
"""
DHI Kubernetes Cluster Autoscaler - Main Entry Point
Autoscales GuardianShield mining nodes based on blockchain demand
"""

import asyncio
import argparse
import logging
import signal
import sys
from pathlib import Path

from .core import ClusterAutoscaler
from .config import load_config
from .api import start_api_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('dhi-autoscaler')


async def main():
    parser = argparse.ArgumentParser(description='DHI Kubernetes Cluster Autoscaler')
    parser.add_argument('--config', type=str, default='/app/config/autoscaler.yaml',
                        help='Path to configuration file')
    parser.add_argument('--port', type=int, default=8080,
                        help='API server port')
    args = parser.parse_args()

    logger.info("🚀 Starting DHI Kubernetes Cluster Autoscaler v1.0.0")
    logger.info("🛡️ GuardianShield Mining Node Autoscaling System")

    # Load configuration
    config = load_config(args.config)
    
    # Initialize autoscaler
    autoscaler = ClusterAutoscaler(config)
    
    # Handle shutdown gracefully
    loop = asyncio.get_event_loop()
    
    def shutdown_handler():
        logger.info("⚠️ Shutdown signal received, stopping autoscaler...")
        asyncio.create_task(autoscaler.shutdown())
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, shutdown_handler)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            pass
    
    # Start API server in background
    api_task = asyncio.create_task(start_api_server(autoscaler, args.port))
    
    # Start autoscaler main loop
    try:
        await autoscaler.start()
    except KeyboardInterrupt:
        logger.info("⚠️ Keyboard interrupt received")
    finally:
        await autoscaler.shutdown()
        api_task.cancel()

    logger.info("✅ DHI Autoscaler shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
