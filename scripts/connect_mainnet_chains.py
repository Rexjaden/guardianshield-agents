#!/usr/bin/env python3
"""
Connect to Mainnet Blockchains
Links GuardianShield to live blockchain networks for monitoring and block production
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Owner wallet - works across all EVM chains
OWNER_WALLET = os.getenv('OWNER_WALLET_ADDRESS', '0xF262b772c2EBf526a5cF8634CA92597583Ef38ee')
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY', 'J8QD4YPCWIRT3G1WFGHIC7YWGDBJ4VMGZ4')

# Multi-chain RPC endpoints (all public, no auth needed)
CHAIN_CONFIG = {
    'ethereum': {
        'name': 'Ethereum Mainnet',
        'chain_id': 1,
        'rpc': os.getenv('ETH_MAINNET_RPC', 'https://ethereum-rpc.publicnode.com'),
        'explorer_api': f'https://api.etherscan.io/api?apikey={ETHERSCAN_API_KEY}',
        'native_symbol': 'ETH',
        'block_time': 12
    },
    'polygon': {
        'name': 'Polygon Mainnet',
        'chain_id': 137,
        'rpc': os.getenv('POLYGON_MAINNET_RPC', 'https://polygon-bor-rpc.publicnode.com'),
        'explorer_api': f'https://api.polygonscan.com/api?apikey={ETHERSCAN_API_KEY}',
        'native_symbol': 'MATIC',
        'block_time': 2
    },
    'arbitrum': {
        'name': 'Arbitrum One',
        'chain_id': 42161,
        'rpc': os.getenv('ARBITRUM_MAINNET_RPC', 'https://arbitrum-one-rpc.publicnode.com'),
        'explorer_api': f'https://api.arbiscan.io/api?apikey={ETHERSCAN_API_KEY}',
        'native_symbol': 'ETH',
        'block_time': 0.25
    },
    'bsc': {
        'name': 'BNB Smart Chain',
        'chain_id': 56,
        'rpc': os.getenv('BSC_MAINNET_RPC', 'https://bsc-rpc.publicnode.com'),
        'explorer_api': f'https://api.bscscan.com/api?apikey={ETHERSCAN_API_KEY}',
        'native_symbol': 'BNB',
        'block_time': 3
    },
    'avalanche': {
        'name': 'Avalanche C-Chain',
        'chain_id': 43114,
        'rpc': os.getenv('AVALANCHE_MAINNET_RPC', 'https://avalanche-c-chain-rpc.publicnode.com'),
        'explorer_api': f'https://api.snowtrace.io/api?apikey={ETHERSCAN_API_KEY}',
        'native_symbol': 'AVAX',
        'block_time': 2
    },
    'optimism': {
        'name': 'Optimism Mainnet',
        'chain_id': 10,
        'rpc': os.getenv('OPTIMISM_MAINNET_RPC', 'https://optimism-rpc.publicnode.com'),
        'explorer_api': f'https://api-optimistic.etherscan.io/api?apikey={ETHERSCAN_API_KEY}',
        'native_symbol': 'ETH',
        'block_time': 2
    },
    'base': {
        'name': 'Base Mainnet',
        'chain_id': 8453,
        'rpc': os.getenv('BASE_MAINNET_RPC', 'https://base-rpc.publicnode.com'),
        'explorer_api': f'https://api.basescan.org/api?apikey={ETHERSCAN_API_KEY}',
        'native_symbol': 'ETH',
        'block_time': 2
    },
    'flare': {
        'name': 'Flare Mainnet',
        'chain_id': 14,
        'rpc': os.getenv('FLARE_MAINNET_RPC', 'https://flare-api.flare.network/ext/C/rpc'),
        'explorer_api': 'https://flare-explorer.flare.network/api',
        'native_symbol': 'FLR',
        'block_time': 3
    }
}

try:
    from web3 import Web3
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    logger.warning("web3 not installed - run: pip install web3")


class MultiChainConnector:
    """Connects to multiple blockchain networks for monitoring and block operations"""
    
    def __init__(self):
        self.connections = {}
        self.owner_wallet = OWNER_WALLET
        self.connected_chains = []
        
    async def connect_all_chains(self):
        """Connect to all configured blockchain networks"""
        logger.info("=" * 60)
        logger.info("🔗 GUARDIANSHIELD MULTI-CHAIN CONNECTOR")
        logger.info(f"📍 Owner Wallet: {self.owner_wallet}")
        logger.info("=" * 60)
        
        if not WEB3_AVAILABLE:
            logger.error("❌ web3 library not available")
            return False
            
        results = {}
        for chain_key, config in CHAIN_CONFIG.items():
            try:
                result = await self._connect_chain(chain_key, config)
                results[chain_key] = result
                if result['connected']:
                    self.connected_chains.append(chain_key)
            except Exception as e:
                logger.error(f"❌ {config['name']}: Connection failed - {e}")
                results[chain_key] = {'connected': False, 'error': str(e)}
                
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 CONNECTION SUMMARY")
        logger.info("=" * 60)
        
        connected = sum(1 for r in results.values() if r.get('connected'))
        logger.info(f"✅ Connected: {connected}/{len(CHAIN_CONFIG)} chains")
        
        for chain, result in results.items():
            status = "✅" if result.get('connected') else "❌"
            block = result.get('latest_block', 'N/A')
            balance = result.get('wallet_balance', 'N/A')
            logger.info(f"  {status} {chain}: Block #{block} | Balance: {balance}")
            
        return results
        
    async def _connect_chain(self, chain_key: str, config: dict) -> dict:
        """Connect to a single blockchain"""
        logger.info(f"\n🔌 Connecting to {config['name']}...")
        
        w3 = Web3(Web3.HTTPProvider(config['rpc']))
        
        # Test connection
        if not w3.is_connected():
            return {'connected': False, 'error': 'RPC connection failed'}
            
        # Get chain ID to verify
        chain_id = w3.eth.chain_id
        if chain_id != config['chain_id']:
            logger.warning(f"⚠️  Chain ID mismatch: expected {config['chain_id']}, got {chain_id}")
            
        # Get latest block
        latest_block = w3.eth.block_number
        
        # Get wallet balance
        try:
            balance_wei = w3.eth.get_balance(self.owner_wallet)
            balance = w3.from_wei(balance_wei, 'ether')
            balance_str = f"{float(balance):.6f} {config['native_symbol']}"
        except Exception as e:
            balance_str = f"Error: {e}"
            
        # Store connection
        self.connections[chain_key] = {
            'web3': w3,
            'config': config,
            'connected_at': datetime.now().isoformat()
        }
        
        logger.info(f"  ✅ Connected to {config['name']}")
        logger.info(f"     Chain ID: {chain_id}")
        logger.info(f"     Latest Block: {latest_block}")
        logger.info(f"     Wallet Balance: {balance_str}")
        
        return {
            'connected': True,
            'chain_id': chain_id,
            'latest_block': latest_block,
            'wallet_balance': balance_str,
            'rpc': config['rpc']
        }
        
    async def get_wallet_across_chains(self):
        """Get wallet balances across all connected chains"""
        balances = {}
        
        for chain_key, conn in self.connections.items():
            w3 = conn['web3']
            config = conn['config']
            
            try:
                balance_wei = w3.eth.get_balance(self.owner_wallet)
                balance = float(w3.from_wei(balance_wei, 'ether'))
                balances[chain_key] = {
                    'balance': balance,
                    'symbol': config['native_symbol'],
                    'chain': config['name']
                }
            except Exception as e:
                balances[chain_key] = {'error': str(e)}
                
        return balances
        
    async def monitor_new_blocks(self, callback=None):
        """Monitor new blocks across all chains"""
        logger.info("\n🔍 Starting multi-chain block monitoring...")
        
        last_blocks = {}
        for chain_key, conn in self.connections.items():
            last_blocks[chain_key] = conn['web3'].eth.block_number
            
        while True:
            for chain_key, conn in self.connections.items():
                try:
                    w3 = conn['web3']
                    current_block = w3.eth.block_number
                    
                    if current_block > last_blocks[chain_key]:
                        new_blocks = current_block - last_blocks[chain_key]
                        logger.info(f"⛓️  {conn['config']['name']}: New block(s) {last_blocks[chain_key]+1} → {current_block}")
                        
                        if callback:
                            await callback(chain_key, current_block)
                            
                        last_blocks[chain_key] = current_block
                        
                except Exception as e:
                    logger.error(f"❌ {chain_key} monitoring error: {e}")
                    
            await asyncio.sleep(2)  # Check every 2 seconds


async def main():
    """Main entry point"""
    connector = MultiChainConnector()
    
    # Connect to all chains
    results = await connector.connect_all_chains()
    
    # Get wallet balances across chains
    logger.info("\n" + "=" * 60)
    logger.info("💰 WALLET BALANCES ACROSS CHAINS")
    logger.info("=" * 60)
    
    balances = await connector.get_wallet_across_chains()
    for chain, data in balances.items():
        if 'error' not in data:
            logger.info(f"  {chain}: {data['balance']:.6f} {data['symbol']}")
        else:
            logger.info(f"  {chain}: Error - {data['error']}")
            
    # Optionally start block monitoring
    # await connector.monitor_new_blocks()
    
    return connector


if __name__ == "__main__":
    asyncio.run(main())
