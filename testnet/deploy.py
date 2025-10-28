# Testnet Deployment Configuration for ERC-8055
import json
from web3 import Web3
from solcx import compile_source, install_solc

# Testnet Configuration
TESTNET_CONFIG = {
    "sepolia": {
        "rpc_url": "https://sepolia.infura.io/v3/YOUR_INFURA_KEY",
        "chain_id": 11155111,
        "explorer": "https://sepolia.etherscan.io"
    },
    "goerli": {
        "rpc_url": "https://goerli.infura.io/v3/YOUR_INFURA_KEY", 
        "chain_id": 5,
        "explorer": "https://goerli.etherscan.io"
    }
}

# Deployment Parameters
DEPLOYMENT_PARAMS = {
    "treasury_address": "0x742D35Cc6634C0532925a3b8D371D885dc07C08e",  # Replace with actual treasury
    "initial_batch_size": 300_000_000,
    "gas_limit": 5_000_000,
    "gas_price": Web3.toWei('20', 'gwei')
}

# Test Wallet Addresses (for testing purposes)
TEST_WALLETS = {
    "deployer": {
        "address": "0x...", 
        "private_key": "YOUR_DEPLOYER_PRIVATE_KEY"
    },
    "treasury": {
        "address": "0x742D35Cc6634C0532925a3b8D371D885dc07C08e",
        "private_key": "YOUR_TREASURY_PRIVATE_KEY"
    },
    "test_user1": {
        "address": "0x...",
        "private_key": "YOUR_TEST_USER1_PRIVATE_KEY"
    },
    "test_user2": {
        "address": "0x...",
        "private_key": "YOUR_TEST_USER2_PRIVATE_KEY"
    },
    "malicious_actor": {
        "address": "0x...",
        "private_key": "YOUR_MALICIOUS_ACTOR_PRIVATE_KEY"
    }
}

def deploy_contract(network="sepolia"):
    """Deploy GuardianShield8055 contract to testnet"""
    # Connect to testnet
    w3 = Web3(Web3.HTTPProvider(TESTNET_CONFIG[network]["rpc_url"]))
    
    # Load contract source
    with open("../contracts/erc-8055/GuardianShield8055.sol", "r") as f:
        contract_source = f.read()
    
    # Compile contract
    install_solc('0.8.20')
    compiled_sol = compile_source(contract_source)
    contract_interface = compiled_sol['<stdin>:GuardianShield8055']
    
    # Deploy contract
    contract = w3.eth.contract(
        abi=contract_interface['abi'],
        bytecode=contract_interface['bin']
    )
    
    # Set up deployer account
    deployer_account = w3.eth.account.from_key(TEST_WALLETS["deployer"]["private_key"])
    w3.eth.default_account = deployer_account.address
    
    # Deploy transaction
    transaction = contract.constructor(
        DEPLOYMENT_PARAMS["treasury_address"]
    ).buildTransaction({
        'chainId': TESTNET_CONFIG[network]["chain_id"],
        'gas': DEPLOYMENT_PARAMS["gas_limit"],
        'gasPrice': DEPLOYMENT_PARAMS["gas_price"],
        'nonce': w3.eth.get_transaction_count(deployer_account.address),
    })
    
    # Sign and send transaction
    signed_txn = w3.eth.account.sign_transaction(transaction, TEST_WALLETS["deployer"]["private_key"])
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    
    # Wait for deployment
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    deployed_contract = w3.eth.contract(
        address=tx_receipt.contractAddress,
        abi=contract_interface['abi']
    )
    
    deployment_info = {
        "network": network,
        "contract_address": tx_receipt.contractAddress,
        "transaction_hash": tx_hash.hex(),
        "gas_used": tx_receipt.gasUsed,
        "block_number": tx_receipt.blockNumber,
        "explorer_url": f"{TESTNET_CONFIG[network]['explorer']}/address/{tx_receipt.contractAddress}"
    }
    
    # Save deployment info
    with open(f"deployment_{network}.json", "w") as f:
        json.dump(deployment_info, f, indent=2)
    
    print(f"✅ Contract deployed to {network}")
    print(f"📍 Address: {tx_receipt.contractAddress}")
    print(f"🔗 Explorer: {deployment_info['explorer_url']}")
    
    return deployed_contract, deployment_info

if __name__ == "__main__":
    # Deploy to Sepolia testnet
    contract, info = deploy_contract("sepolia")