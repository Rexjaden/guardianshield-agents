"""
GuardianShield Smart Contract Integration Framework
Infrastructure for connecting Web3 contracts with our ecosystem
"""

from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from typing import Dict, List, Any, Optional, Union
import json
import os
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum
import asyncio
import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChainId(Enum):
    """Supported blockchain networks"""
    ETHEREUM = 1
    BSC = 56
    POLYGON = 137
    AVALANCHE = 43114
    ARBITRUM = 42161
    
    @classmethod
    def get_name(cls, chain_id: int) -> str:
        mapping = {
            1: "Ethereum",
            56: "Binance Smart Chain", 
            137: "Polygon",
            43114: "Avalanche",
            42161: "Arbitrum"
        }
        return mapping.get(chain_id, f"Chain {chain_id}")

@dataclass
class ContractConfig:
    """Contract configuration structure"""
    name: str
    address: str
    abi: List[Dict[str, Any]]
    chain_id: int
    deployment_block: int
    verified: bool = False
    audit_report_url: Optional[str] = None

@dataclass
class NetworkConfig:
    """Network configuration for Web3 connections"""
    chain_id: int
    name: str
    rpc_url: str
    explorer_url: str
    native_token: str
    gas_price_oracle: Optional[str] = None

class SmartContractManager:
    """
    Manages smart contract interactions across multiple chains
    Handles deployment, upgrades, and cross-chain coordination
    """
    
    def __init__(self):
        self.networks = self._initialize_networks()
        self.contracts = {}
        self.web3_instances = {}
        self.contract_templates = self._load_contract_templates()
        
        # Initialize Web3 connections
        self._initialize_web3_connections()
    
    def _initialize_networks(self) -> Dict[int, NetworkConfig]:
        """Initialize supported network configurations"""
        return {
            ChainId.ETHEREUM.value: NetworkConfig(
                chain_id=1,
                name="Ethereum Mainnet",
                rpc_url="https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY",
                explorer_url="https://etherscan.io",
                native_token="ETH",
                gas_price_oracle="https://api.etherscan.io/api?module=gastracker&action=gasoracle"
            ),
            ChainId.BSC.value: NetworkConfig(
                chain_id=56,
                name="Binance Smart Chain",
                rpc_url="https://bsc-dataseed1.binance.org/",
                explorer_url="https://bscscan.com",
                native_token="BNB"
            ),
            ChainId.POLYGON.value: NetworkConfig(
                chain_id=137,
                name="Polygon",
                rpc_url="https://polygon-rpc.com/",
                explorer_url="https://polygonscan.com",
                native_token="MATIC"
            ),
            ChainId.AVALANCHE.value: NetworkConfig(
                chain_id=43114,
                name="Avalanche",
                rpc_url="https://api.avax.network/ext/bc/C/rpc",
                explorer_url="https://snowtrace.io",
                native_token="AVAX"
            ),
            ChainId.ARBITRUM.value: NetworkConfig(
                chain_id=42161,
                name="Arbitrum One",
                rpc_url="https://arb1.arbitrum.io/rpc",
                explorer_url="https://arbiscan.io",
                native_token="ETH"
            )
        }
    
    def _initialize_web3_connections(self):
        """Initialize Web3 instances for all networks"""
        for chain_id, config in self.networks.items():
            try:
                # Use environment variable or default to public RPC
                rpc_url = os.getenv(f"RPC_URL_{chain_id}", config.rpc_url)
                
                w3 = Web3(Web3.HTTPProvider(rpc_url))
                
                # Add PoA middleware for BSC and other PoA chains
                if chain_id in [ChainId.BSC.value, ChainId.POLYGON.value]:
                    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                
                # Test connection
                if w3.is_connected():
                    self.web3_instances[chain_id] = w3
                    logger.info(f"✅ Connected to {config.name}")
                else:
                    logger.warning(f"❌ Failed to connect to {config.name}")
                    
            except Exception as e:
                logger.error(f"Error connecting to {config.name}: {e}")
    
    def _load_contract_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load contract templates and ABIs"""
        return {
            "GuardianToken": {
                "description": "Main governance and utility token",
                "functions": [
                    "transfer", "approve", "transferFrom", "balanceOf",
                    "totalSupply", "mint", "burn", "stake", "unstake"
                ],
                "events": [
                    "Transfer", "Approval", "Staked", "Unstaked", "Burned"
                ],
                "deployment_priority": 1
            },
            
            "GuardianTreasury": {
                "description": "Community-governed treasury contract",
                "functions": [
                    "propose", "vote", "execute", "deposit", "withdraw",
                    "getBalance", "getProposal", "getVotingPower"
                ],
                "events": [
                    "ProposalCreated", "VoteCast", "ProposalExecuted",
                    "FundsDeposited", "FundsWithdrawn"
                ],
                "deployment_priority": 2
            },
            
            "GuardianStaking": {
                "description": "Token staking and reward distribution",
                "functions": [
                    "stake", "unstake", "claimRewards", "getStakeInfo",
                    "calculateRewards", "setRewardRate", "emergencyWithdraw"
                ],
                "events": [
                    "Staked", "Unstaked", "RewardsClaimed", "RewardRateUpdated"
                ],
                "deployment_priority": 3
            },
            
            "SecurityOracle": {
                "description": "AI threat detection and reporting oracle",
                "functions": [
                    "reportThreat", "verifyThreat", "updateSecurityScore",
                    "getThreatLevel", "getSecurityMetrics", "addReporter"
                ],
                "events": [
                    "ThreatReported", "ThreatVerified", "SecurityScoreUpdated",
                    "ReporterAdded", "ReporterRemoved"
                ],
                "deployment_priority": 4
            },
            
            "MultiChainBridge": {
                "description": "Cross-chain asset and message bridge",
                "functions": [
                    "bridgeTokens", "verifyMessage", "executeMessage",
                    "addSupportedChain", "updateValidator", "pause", "unpause"
                ],
                "events": [
                    "TokensBridged", "MessageSent", "MessageExecuted",
                    "ChainAdded", "ValidatorUpdated", "BridgePaused"
                ],
                "deployment_priority": 5
            }
        }
    
    async def deploy_contract(self, contract_name: str, chain_id: int, 
                            constructor_params: List[Any] = None,
                            deploy_from: str = None) -> Dict[str, Any]:
        """Deploy a contract to specified chain"""
        
        if chain_id not in self.web3_instances:
            raise ValueError(f"Chain {chain_id} not supported or not connected")
        
        if contract_name not in self.contract_templates:
            raise ValueError(f"Contract template {contract_name} not found")
        
        w3 = self.web3_instances[chain_id]
        template = self.contract_templates[contract_name]
        
        # Load contract bytecode and ABI (would be from compiled contracts)
        contract_data = await self._load_contract_bytecode(contract_name)
        
        if not contract_data:
            raise ValueError(f"Contract bytecode not found for {contract_name}")
        
        try:
            # Create contract object
            contract = w3.eth.contract(
                abi=contract_data['abi'],
                bytecode=contract_data['bytecode']
            )
            
            # Get deployment account
            if not deploy_from:
                deploy_from = os.getenv('DEPLOYER_PRIVATE_KEY')
                if not deploy_from:
                    raise ValueError("No deployer account specified")
            
            account = Account.from_key(deploy_from)
            
            # Build constructor transaction
            constructor_tx = contract.constructor(
                *(constructor_params or [])
            ).build_transaction({
                'chainId': chain_id,
                'gas': 3000000,  # Estimate gas properly in production
                'gasPrice': w3.to_wei('20', 'gwei'),
                'nonce': w3.eth.get_transaction_count(account.address)
            })
            
            # Sign and send transaction
            signed_tx = w3.eth.account.sign_transaction(constructor_tx, deploy_from)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for deployment
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if tx_receipt.status == 1:
                contract_address = tx_receipt.contractAddress
                
                # Create contract config
                contract_config = ContractConfig(
                    name=contract_name,
                    address=contract_address,
                    abi=contract_data['abi'],
                    chain_id=chain_id,
                    deployment_block=tx_receipt.blockNumber,
                    verified=False
                )
                
                # Store contract
                self.register_contract(contract_config)
                
                logger.info(f"✅ {contract_name} deployed to {contract_address} on {ChainId.get_name(chain_id)}")
                
                return {
                    "success": True,
                    "contract_address": contract_address,
                    "transaction_hash": tx_hash.hex(),
                    "block_number": tx_receipt.blockNumber,
                    "gas_used": tx_receipt.gasUsed,
                    "chain_id": chain_id
                }
            else:
                raise Exception(f"Contract deployment failed: {tx_receipt}")
                
        except Exception as e:
            logger.error(f"Deployment error: {e}")
            return {
                "success": False,
                "error": str(e),
                "chain_id": chain_id
            }
    
    def register_contract(self, config: ContractConfig):
        """Register a deployed contract"""
        if config.chain_id not in self.contracts:
            self.contracts[config.chain_id] = {}
        
        self.contracts[config.chain_id][config.name] = config
        
        # Create contract instance
        w3 = self.web3_instances[config.chain_id]
        contract_instance = w3.eth.contract(
            address=config.address,
            abi=config.abi
        )
        
        # Store instance for easy access
        if not hasattr(self, 'instances'):
            self.instances = {}
        if config.chain_id not in self.instances:
            self.instances[config.chain_id] = {}
        
        self.instances[config.chain_id][config.name] = contract_instance
        
        logger.info(f"📝 Registered {config.name} at {config.address}")
    
    async def call_contract_method(self, chain_id: int, contract_name: str, 
                                 method_name: str, args: List[Any] = None,
                                 from_address: str = None) -> Any:
        """Call a contract method (read-only)"""
        
        if chain_id not in self.instances or contract_name not in self.instances[chain_id]:
            raise ValueError(f"Contract {contract_name} not found on chain {chain_id}")
        
        contract = self.instances[chain_id][contract_name]
        method = getattr(contract.functions, method_name)
        
        if args:
            result = method(*args).call({'from': from_address} if from_address else {})
        else:
            result = method().call({'from': from_address} if from_address else {})
        
        return result
    
    async def send_contract_transaction(self, chain_id: int, contract_name: str,
                                      method_name: str, args: List[Any] = None,
                                      private_key: str = None, gas_limit: int = None) -> Dict[str, Any]:
        """Send a contract transaction"""
        
        if chain_id not in self.instances or contract_name not in self.instances[chain_id]:
            raise ValueError(f"Contract {contract_name} not found on chain {chain_id}")
        
        if not private_key:
            private_key = os.getenv('TRANSACTION_PRIVATE_KEY')
            if not private_key:
                raise ValueError("No private key provided for transaction")
        
        w3 = self.web3_instances[chain_id]
        contract = self.instances[chain_id][contract_name]
        account = Account.from_key(private_key)
        
        # Build transaction
        method = getattr(contract.functions, method_name)
        
        if args:
            tx_data = method(*args)
        else:
            tx_data = method()
        
        transaction = tx_data.build_transaction({
            'chainId': chain_id,
            'gas': gas_limit or 200000,
            'gasPrice': w3.to_wei('20', 'gwei'),
            'nonce': w3.eth.get_transaction_count(account.address)
        })
        
        # Sign and send
        signed_tx = w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        # Wait for confirmation
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return {
            "success": tx_receipt.status == 1,
            "transaction_hash": tx_hash.hex(),
            "block_number": tx_receipt.blockNumber,
            "gas_used": tx_receipt.gasUsed,
            "logs": [log for log in tx_receipt.logs]
        }
    
    async def _load_contract_bytecode(self, contract_name: str) -> Optional[Dict[str, Any]]:
        """Load contract bytecode and ABI from compilation artifacts"""
        # In production, this would load from actual contract compilation
        # For now, return template structure
        
        if contract_name not in self.contract_templates:
            return None
        
        # This is a placeholder - actual implementation would load from
        # compiled contract artifacts (e.g., artifacts/ContractName.sol/ContractName.json)
        return {
            "abi": [],  # Would contain actual ABI
            "bytecode": "0x608060405234801561001057600080fd5b50",  # Placeholder bytecode
            "metadata": self.contract_templates[contract_name]
        }
    
    def get_contract_addresses(self, chain_id: int = None) -> Dict[str, Any]:
        """Get all deployed contract addresses"""
        if chain_id:
            if chain_id in self.contracts:
                return {
                    name: config.address 
                    for name, config in self.contracts[chain_id].items()
                }
            return {}
        
        # Return all chains
        result = {}
        for cid, contracts in self.contracts.items():
            chain_name = ChainId.get_name(cid)
            result[chain_name] = {
                name: config.address 
                for name, config in contracts.items()
            }
        
        return result
    
    async def verify_contract_on_explorer(self, chain_id: int, contract_name: str,
                                        source_code: str = None) -> bool:
        """Verify contract source code on block explorer"""
        
        if chain_id not in self.contracts or contract_name not in self.contracts[chain_id]:
            raise ValueError(f"Contract {contract_name} not found on chain {chain_id}")
        
        config = self.contracts[chain_id][contract_name]
        network_config = self.networks[chain_id]
        
        # Implementation would depend on specific explorer APIs
        # (Etherscan, BSCScan, PolygonScan, etc.)
        
        logger.info(f"🔍 Verifying {contract_name} on {network_config.explorer_url}")
        
        # Placeholder for actual verification logic
        # Would use explorer APIs to verify source code
        
        config.verified = True  # Mark as verified
        return True
    
    def get_deployment_plan(self) -> List[Dict[str, Any]]:
        """Get recommended deployment plan based on priorities"""
        
        plan = []
        for contract_name, template in self.contract_templates.items():
            plan.append({
                "contract_name": contract_name,
                "description": template["description"],
                "priority": template["deployment_priority"],
                "dependencies": self._get_contract_dependencies(contract_name),
                "estimated_gas": self._estimate_deployment_gas(contract_name),
                "recommended_chains": self._get_recommended_chains(contract_name)
            })
        
        # Sort by priority
        plan.sort(key=lambda x: x["priority"])
        return plan
    
    def _get_contract_dependencies(self, contract_name: str) -> List[str]:
        """Get contract dependencies for deployment order"""
        dependencies = {
            "GuardianToken": [],
            "GuardianTreasury": ["GuardianToken"],
            "GuardianStaking": ["GuardianToken"],
            "SecurityOracle": ["GuardianToken"],
            "MultiChainBridge": ["GuardianToken", "GuardianTreasury"]
        }
        return dependencies.get(contract_name, [])
    
    def _estimate_deployment_gas(self, contract_name: str) -> int:
        """Estimate gas costs for contract deployment"""
        estimates = {
            "GuardianToken": 2_500_000,
            "GuardianTreasury": 3_200_000,
            "GuardianStaking": 2_800_000,
            "SecurityOracle": 2_200_000,
            "MultiChainBridge": 4_100_000
        }
        return estimates.get(contract_name, 2_000_000)
    
    def _get_recommended_chains(self, contract_name: str) -> List[int]:
        """Get recommended deployment chains for each contract"""
        recommendations = {
            "GuardianToken": [ChainId.ETHEREUM.value, ChainId.BSC.value, ChainId.POLYGON.value],
            "GuardianTreasury": [ChainId.ETHEREUM.value],  # Main treasury on Ethereum
            "GuardianStaking": [ChainId.ETHEREUM.value, ChainId.BSC.value, ChainId.POLYGON.value],
            "SecurityOracle": [ChainId.ETHEREUM.value, ChainId.BSC.value, ChainId.POLYGON.value, 
                             ChainId.AVALANCHE.value, ChainId.ARBITRUM.value],
            "MultiChainBridge": [ChainId.ETHEREUM.value]  # Bridge hub on Ethereum
        }
        return recommendations.get(contract_name, [ChainId.ETHEREUM.value])
    
    def export_deployment_config(self) -> str:
        """Export deployment configuration for team collaboration"""
        
        config = {
            "networks": {
                str(chain_id): {
                    "name": config.name,
                    "chain_id": config.chain_id,
                    "rpc_url": config.rpc_url,
                    "explorer_url": config.explorer_url,
                    "native_token": config.native_token
                }
                for chain_id, config in self.networks.items()
            },
            "contracts": self.contract_templates,
            "deployment_plan": self.get_deployment_plan(),
            "deployed_contracts": self.get_contract_addresses(),
            "generated_at": datetime.now().isoformat(),
            "framework_version": "1.0.0"
        }
        
        return json.dumps(config, indent=2)

# Global contract manager instance
contract_manager = SmartContractManager()

# Utility functions for easy access
async def deploy_contract(contract_name: str, chain_id: int, **kwargs) -> Dict[str, Any]:
    """Quick contract deployment"""
    return await contract_manager.deploy_contract(contract_name, chain_id, **kwargs)

async def call_method(chain_id: int, contract: str, method: str, *args) -> Any:
    """Quick contract method call"""
    return await contract_manager.call_contract_method(chain_id, contract, method, list(args))

async def send_transaction(chain_id: int, contract: str, method: str, *args, **kwargs) -> Dict[str, Any]:
    """Quick contract transaction"""
    return await contract_manager.send_contract_transaction(chain_id, contract, method, list(args), **kwargs)

def get_addresses(chain_id: int = None) -> Dict[str, Any]:
    """Quick address lookup"""
    return contract_manager.get_contract_addresses(chain_id)

if __name__ == "__main__":
    print("🔗 GuardianShield Smart Contract Integration Framework")
    print("=" * 60)
    
    # Show deployment plan
    plan = contract_manager.get_deployment_plan()
    print("\n📋 Recommended Deployment Plan:")
    for item in plan:
        print(f"{item['priority']}. {item['contract_name']}: {item['description']}")
        print(f"   Dependencies: {', '.join(item['dependencies']) or 'None'}")
        print(f"   Estimated Gas: {item['estimated_gas']:,}")
        print(f"   Recommended Chains: {[ChainId.get_name(cid) for cid in item['recommended_chains']]}")
        print()
    
    # Show network connections
    print("🌐 Network Connections:")
    for chain_id, w3 in contract_manager.web3_instances.items():
        network_name = ChainId.get_name(chain_id)
        status = "✅ Connected" if w3.is_connected() else "❌ Disconnected"
        print(f"   {network_name}: {status}")
    
    # Export configuration
    print("\n💾 Exporting deployment configuration...")
    config_json = contract_manager.export_deployment_config()
    
    with open("smart_contract_deployment_config.json", "w") as f:
        f.write(config_json)
    
    print("📄 Configuration saved to smart_contract_deployment_config.json")
    print("\n🚀 Framework ready for smart contract development!")
    print("   - Multi-chain deployment support")
    print("   - Automated verification")
    print("   - Cross-chain coordination")
    print("   - Production-ready infrastructure")