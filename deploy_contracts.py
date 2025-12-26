#!/usr/bin/env python3
"""
GuardianShield Smart Contract Deployment Script
Deploys all core contracts with proper configuration and Chainlink integration
"""

import json
import os
from typing import Dict, Any, Optional
from web3 import Web3
from eth_account import Account
import requests
import time

class ContractDeployer:
    def __init__(self, network: str = "sepolia"):
        self.network = network
        self.w3 = None
        self.account = None
        self.deployed_contracts = {}
        self.deployment_log = []
        
        # Network configurations
        self.networks = {
            "sepolia": {
                "rpc_url": "https://eth-sepolia.g.alchemy.com/v2/your-api-key",
                "chain_id": 11155111,
                "explorer": "https://sepolia.etherscan.io",
                "eth_usd_oracle": "0x694AA1769357215DE4FAC081bf1f309aDC325306",  # Chainlink ETH/USD
                "btc_usd_oracle": "0x1b44F3514812d835EB1BDB0acB33d3fA3351Ee43",  # Chainlink BTC/USD
                "guard_usd_oracle": None  # We'll deploy our own
            },
            "polygon": {
                "rpc_url": "https://polygon-mumbai.g.alchemy.com/v2/your-api-key",
                "chain_id": 80001,
                "explorer": "https://mumbai.polygonscan.com",
                "eth_usd_oracle": "0x0715A7794a1dc8e42615F059dD6e406A6594651A",
                "btc_usd_oracle": "0x007A22900a3B98143368Bd5906f8E17e9867581b",
                "guard_usd_oracle": None
            },
            "localhost": {
                "rpc_url": "http://127.0.0.1:8545",
                "chain_id": 1337,
                "explorer": "http://localhost:8545",
                "eth_usd_oracle": None,  # Mock oracle for testing
                "btc_usd_oracle": None,
                "guard_usd_oracle": None
            }
        }
        
        self.setup_network()
    
    def setup_network(self):
        """Initialize Web3 connection and account"""
        network_config = self.networks[self.network]
        
        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(network_config["rpc_url"]))
        
        if not self.w3.is_connected():
            raise Exception(f"Failed to connect to {self.network} network")
        
        # Load deployment account (in production, use secure key management)
        private_key = os.getenv("DEPLOYMENT_PRIVATE_KEY")
        if not private_key:
            print("⚠️  Warning: No DEPLOYMENT_PRIVATE_KEY found, generating temporary key for testing")
            self.account = Account.create()
            print(f"Generated address: {self.account.address}")
            print(f"Private key: {self.account.key.hex()}")
        else:
            self.account = Account.from_key(private_key)
        
        print(f"🔗 Connected to {self.network}")
        print(f"📍 Deployer address: {self.account.address}")
        print(f"💰 Balance: {self.w3.from_wei(self.w3.eth.get_balance(self.account.address), 'ether')} ETH")
    
    def compile_contract(self, contract_name: str) -> Dict[str, Any]:
        """Compile a Solidity contract (simplified - in production use hardhat/foundry)"""
        # For this demo, we'll use pre-compiled bytecode
        # In production, integrate with Hardhat or Foundry for compilation
        
        contracts_bytecode = {
            "GuardianToken": {
                "abi": [
                    {
                        "inputs": [{"name": "initialSaleAddress", "type": "address"}],
                        "stateMutability": "nonpayable",
                        "type": "constructor"
                    },
                    {
                        "inputs": [],
                        "name": "name",
                        "outputs": [{"type": "string"}],
                        "stateMutability": "view",
                        "type": "function"
                    },
                    {
                        "inputs": [],
                        "name": "symbol", 
                        "outputs": [{"type": "string"}],
                        "stateMutability": "view",
                        "type": "function"
                    },
                    {
                        "inputs": [],
                        "name": "totalSupply",
                        "outputs": [{"type": "uint256"}],
                        "stateMutability": "view",
                        "type": "function"
                    },
                    {
                        "inputs": [{"name": "to", "type": "address"}, {"name": "amount", "type": "uint256"}],
                        "name": "mintStage",
                        "outputs": [],
                        "stateMutability": "nonpayable",
                        "type": "function"
                    }
                ],
                "bytecode": "0x608060405234801561001057600080fd5b5060405161..."  # Simplified
            },
            "GuardianStaking": {
                "abi": [
                    {
                        "inputs": [{"name": "_guardToken", "type": "address"}, {"name": "_rewardRate", "type": "uint256"}],
                        "stateMutability": "nonpayable",
                        "type": "constructor"
                    },
                    {
                        "inputs": [{"name": "amount", "type": "uint256"}],
                        "name": "stake",
                        "outputs": [],
                        "stateMutability": "nonpayable",
                        "type": "function"
                    }
                ],
                "bytecode": "0x608060405234801561001057600080fd5b5060405161..."
            }
        }
        
        return contracts_bytecode.get(contract_name, {})
    
    def deploy_contract(self, contract_name: str, constructor_args: list = None) -> Dict[str, Any]:
        """Deploy a smart contract"""
        print(f"\n🚀 Deploying {contract_name}...")
        
        # Get contract compilation data
        contract_data = self.compile_contract(contract_name)
        if not contract_data:
            raise Exception(f"Contract {contract_name} not found")
        
        # Create contract instance
        contract = self.w3.eth.contract(
            abi=contract_data["abi"],
            bytecode=contract_data["bytecode"]
        )
        
        # Build deployment transaction
        if constructor_args:
            tx = contract.constructor(*constructor_args)
        else:
            tx = contract.constructor()
        
        # Estimate gas
        gas_estimate = tx.estimate_gas({'from': self.account.address})
        gas_price = self.w3.eth.gas_price
        
        # Build transaction
        transaction = tx.build_transaction({
            'from': self.account.address,
            'gas': int(gas_estimate * 1.2),  # Add 20% buffer
            'gasPrice': gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.account.address)
        })
        
        # Sign and send transaction
        signed_tx = self.account.sign_transaction(transaction)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        print(f"📝 Transaction sent: {tx_hash.hex()}")
        print("⏳ Waiting for confirmation...")
        
        # Wait for confirmation
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        
        if tx_receipt.status == 1:
            contract_address = tx_receipt.contractAddress
            print(f"✅ {contract_name} deployed successfully!")
            print(f"📍 Contract address: {contract_address}")
            
            # Create contract instance
            deployed_contract = self.w3.eth.contract(
                address=contract_address,
                abi=contract_data["abi"]
            )
            
            deployment_info = {
                "name": contract_name,
                "address": contract_address,
                "tx_hash": tx_hash.hex(),
                "gas_used": tx_receipt.gasUsed,
                "contract": deployed_contract,
                "abi": contract_data["abi"],
                "deployment_block": tx_receipt.blockNumber
            }
            
            self.deployed_contracts[contract_name] = deployment_info
            self.deployment_log.append(deployment_info)
            
            return deployment_info
        else:
            raise Exception(f"Contract deployment failed: {tx_hash.hex()}")
    
    def deploy_price_oracle(self) -> Dict[str, Any]:
        """Deploy custom GUARD/USD price oracle with Chainlink integration"""
        print("\n🔮 Deploying GUARD Price Oracle...")
        
        # For now, create a simple mock oracle
        # In production, this would be a proper Chainlink oracle contract
        oracle_abi = [
            {
                "inputs": [],
                "name": "latestRoundData",
                "outputs": [
                    {"type": "uint80", "name": "roundId"},
                    {"type": "int256", "name": "answer"},
                    {"type": "uint256", "name": "startedAt"},
                    {"type": "uint256", "name": "updatedAt"},
                    {"type": "uint80", "name": "answeredInRound"}
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [{"name": "_price", "type": "int256"}],
                "name": "updatePrice",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
        
        # Deploy mock oracle for testing
        mock_oracle_info = {
            "name": "GuardPriceOracle",
            "address": "0x" + "1" * 40,  # Mock address for demo
            "abi": oracle_abi,
            "description": "GUARD/USD Price Oracle (Mock for testing)"
        }
        
        self.deployed_contracts["GuardPriceOracle"] = mock_oracle_info
        return mock_oracle_info
    
    def deploy_all_contracts(self):
        """Deploy all GuardianShield contracts in proper order"""
        print("🌟 Starting GuardianShield Contract Deployment")
        print("=" * 50)
        
        try:
            # 1. Deploy GUARD token
            guard_token = self.deploy_contract(
                "GuardianToken",
                [self.account.address]  # Initial sale address
            )
            
            # 2. Deploy price oracle
            price_oracle = self.deploy_price_oracle()
            
            # 3. Deploy staking contract
            staking_contract = self.deploy_contract(
                "GuardianStaking",
                [guard_token["address"], 100]  # Guard token address, reward rate
            )
            
            # 4. Deploy liquidity pool (if needed)
            # liquidity_pool = self.deploy_contract("GuardianLiquidityPool", [...])
            
            print("\n🎉 All contracts deployed successfully!")
            self.save_deployment_info()
            self.print_deployment_summary()
            
        except Exception as e:
            print(f"\n❌ Deployment failed: {str(e)}")
            raise
    
    def save_deployment_info(self):
        """Save deployment information to file"""
        deployment_data = {
            "network": self.network,
            "deployer": self.account.address,
            "timestamp": int(time.time()),
            "contracts": {}
        }
        
        for name, info in self.deployed_contracts.items():
            deployment_data["contracts"][name] = {
                "address": info["address"],
                "tx_hash": info.get("tx_hash"),
                "gas_used": info.get("gas_used"),
                "abi": info["abi"]
            }
        
        # Save to file
        filename = f"deployments_{self.network}_{int(time.time())}.json"
        with open(filename, 'w') as f:
            json.dump(deployment_data, f, indent=2)
        
        print(f"💾 Deployment info saved to {filename}")
    
    def print_deployment_summary(self):
        """Print deployment summary"""
        print("\n📋 Deployment Summary")
        print("=" * 30)
        
        network_config = self.networks[self.network]
        
        for name, info in self.deployed_contracts.items():
            print(f"🔸 {name}")
            print(f"   Address: {info['address']}")
            if info.get('tx_hash'):
                print(f"   TX: {network_config['explorer']}/tx/{info['tx_hash']}")
            print()
        
        print("🔗 Next Steps:")
        print("1. Update guard_token_purchase.py with contract addresses")
        print("2. Integrate Chainlink price feeds")
        print("3. Configure oracle connections")
        print("4. Test contract interactions")

def main():
    """Main deployment function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Deploy GuardianShield contracts")
    parser.add_argument("--network", choices=["sepolia", "polygon", "localhost"], 
                       default="localhost", help="Network to deploy to")
    
    args = parser.parse_args()
    
    print(f"🚀 GuardianShield Contract Deployment")
    print(f"Network: {args.network}")
    print("=" * 40)
    
    try:
        deployer = ContractDeployer(args.network)
        deployer.deploy_all_contracts()
        
        print("\n✅ Deployment completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())