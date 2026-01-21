#!/usr/bin/env python3
"""
GuardianShield Smart Contract Payment System
Integrates token purchases with actual smart contract calls
"""

import json
import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from decimal import Decimal
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Web3 Integration
try:
    from web3 import Web3
    from eth_account import Account
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    print("⚠️ Web3 not available - running in simulation mode")

# Contract Configuration
DEPLOYED_CONTRACTS = {
    "ethereum": {
        "GuardianTokenSale": "0xC6A4a2591bb0a9d1f45397da616dBc27e4b7BC8d",
        "GuardianToken": "0x0000000000000000000000000000000000000000",  # To be deployed
        "GuardianShieldToken": "0x0000000000000000000000000000000000000000",  # To be deployed
        "rpc_url": "https://eth-mainnet.alchemyapi.io/v2/YOUR-API-KEY",
        "chain_id": 1
    },
    "sepolia": {
        "GuardianTokenSale": "0xC6A4a2591bb0a9d1f45397da616dBc27e4b7BC8d",
        "GuardianToken": "0x0000000000000000000000000000000000000000",
        "GuardianShieldToken": "0x0000000000000000000000000000000000000000",
        "rpc_url": "https://sepolia.infura.io/v3/YOUR-API-KEY",
        "chain_id": 11155111
    }
}

# Contract ABIs (essential functions only)
GUARDIAN_TOKEN_SALE_ABI = [
    {
        "inputs": [{"name": "recipient", "type": "address"}, {"name": "amount", "type": "uint256"}],
        "name": "purchaseTokens",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "inputs": [],
        "name": "tokenPrice",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "inputs": [],
        "name": "tokensRemaining",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]

GUARDIAN_TOKEN_ABI = [
    {
        "inputs": [{"name": "to", "type": "address"}, {"name": "amount", "type": "uint256"}],
        "name": "mintStage",
        "outputs": [],
        "type": "function"
    },
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]

GUARDIAN_SHIELD_TOKEN_ABI = [
    {
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "serial", "type": "uint256"},
            {"name": "tokenURI", "type": "string"}
        ],
        "name": "mint",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]

@dataclass
class TokenPurchaseRequest:
    token_type: str  # "GUARD" or "SHIELD"
    quantity: int
    wallet_address: str
    payment_method: str  # "crypto", "credit_card", "bank_transfer"
    payment_token: Optional[str] = "ETH"  # ETH, USDT, USDC, etc.
    chain: str = "sepolia"  # Default to testnet

@dataclass
class PurchaseResult:
    success: bool
    transaction_hash: Optional[str] = None
    token_ids: Optional[List[int]] = None
    serial_numbers: Optional[List[str]] = None
    error_message: Optional[str] = None
    contract_address: Optional[str] = None

class SmartContractPaymentProcessor:
    def __init__(self):
        self.web3_connections = {}
        self.private_key = os.getenv('GUARDIAN_PRIVATE_KEY')  # Load from environment
        
        if WEB3_AVAILABLE:
            self._init_web3_connections()
        
        # Token pricing
        self.token_prices = {
            "GUARD": Decimal("0.025"),  # $0.025 per GUARD
            "SHIELD": Decimal("0.500")  # $0.50 per SHIELD (higher value NFT)
        }
        
        # Simulate payment database
        self.payment_database = {}
    
    def _init_web3_connections(self):
        """Initialize Web3 connections for different networks"""
        for chain, config in DEPLOYED_CONTRACTS.items():
            try:
                w3 = Web3(Web3.HTTPProvider(config["rpc_url"]))
                if w3.is_connected():
                    self.web3_connections[chain] = w3
                    print(f"✅ Connected to {chain} network")
                else:
                    print(f"❌ Failed to connect to {chain} network")
            except Exception as e:
                print(f"❌ Error connecting to {chain}: {e}")
    
    def get_token_price_in_wei(self, token_type: str, chain: str = "sepolia") -> int:
        """Get token price from smart contract or fallback to local pricing"""
        if not WEB3_AVAILABLE or chain not in self.web3_connections:
            # Fallback pricing
            usd_price = self.token_prices[token_type]
            eth_price_usd = 3000  # Approximate ETH price
            token_price_eth = usd_price / eth_price_usd
            return int(token_price_eth * 10**18)  # Convert to wei
        
        try:
            w3 = self.web3_connections[chain]
            contract_addr = DEPLOYED_CONTRACTS[chain]["GuardianTokenSale"]
            contract = w3.eth.contract(
                address=contract_addr,
                abi=GUARDIAN_TOKEN_SALE_ABI
            )
            
            return contract.functions.tokenPrice().call()
            
        except Exception as e:
            print(f"❌ Error getting price from contract: {e}")
            # Fallback to local pricing
            usd_price = self.token_prices[token_type]
            return int(float(usd_price) * 10**18 // 3000)  # Rough ETH conversion
    
    async def purchase_guard_tokens(self, request: TokenPurchaseRequest) -> PurchaseResult:
        """Purchase GUARD tokens via smart contract"""
        try:
            if not WEB3_AVAILABLE:
                return await self._simulate_guard_purchase(request)
            
            chain = request.chain
            if chain not in self.web3_connections:
                return PurchaseResult(
                    success=False,
                    error_message=f"Chain {chain} not supported or not connected"
                )
            
            w3 = self.web3_connections[chain]
            contract_config = DEPLOYED_CONTRACTS[chain]
            
            # Calculate total cost
            token_price = self.get_token_price_in_wei("GUARD", chain)
            total_cost = token_price * request.quantity
            
            # Get contract instance
            sale_contract = w3.eth.contract(
                address=contract_config["GuardianTokenSale"],
                abi=GUARDIAN_TOKEN_SALE_ABI
            )
            
            # Build transaction
            if self.private_key:
                account = Account.from_key(self.private_key)
                
                transaction = sale_contract.functions.purchaseTokens(
                    request.wallet_address,
                    request.quantity * 10**18  # Convert to wei units
                ).build_transaction({
                    'from': account.address,
                    'value': total_cost,
                    'gas': 200000,
                    'gasPrice': w3.eth.gas_price,
                    'nonce': w3.eth.get_transaction_count(account.address),
                })
                
                # Sign and send transaction
                signed_txn = w3.eth.account.sign_transaction(transaction, self.private_key)
                tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                
                # Wait for confirmation
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                
                return PurchaseResult(
                    success=receipt['status'] == 1,
                    transaction_hash=tx_hash.hex(),
                    contract_address=contract_config["GuardianTokenSale"],
                    error_message=None if receipt['status'] == 1 else "Transaction failed"
                )
            else:
                return PurchaseResult(
                    success=False,
                    error_message="Private key not configured for transaction signing"
                )
                
        except Exception as e:
            return PurchaseResult(
                success=False,
                error_message=f"Error purchasing GUARD tokens: {str(e)}"
            )
    
    async def purchase_shield_tokens(self, request: TokenPurchaseRequest) -> PurchaseResult:
        """Purchase SHIELD tokens (NFTs) via smart contract"""
        try:
            if not WEB3_AVAILABLE:
                return await self._simulate_shield_purchase(request)
            
            # Import the serial number system
            from shield_token_serial_system import ShieldTokenSerial
            serial_system = ShieldTokenSerial()
            
            chain = request.chain
            if chain not in self.web3_connections:
                return PurchaseResult(
                    success=False,
                    error_message=f"Chain {chain} not supported or not connected"
                )
            
            w3 = self.web3_connections[chain]
            contract_config = DEPLOYED_CONTRACTS[chain]
            
            # Check if SHIELD contract is deployed
            shield_contract_addr = contract_config.get("GuardianShieldToken")
            if not shield_contract_addr or shield_contract_addr == "0x0000000000000000000000000000000000000000":
                return PurchaseResult(
                    success=False,
                    error_message="GuardianShieldToken contract not deployed yet"
                )
            
            # Get contract instance
            shield_contract = w3.eth.contract(
                address=shield_contract_addr,
                abi=GUARDIAN_SHIELD_TOKEN_ABI
            )
            
            token_ids = []
            serial_numbers = []
            tx_hashes = []
            
            # Mint each SHIELD token individually
            for i in range(request.quantity):
                # Generate serial number
                serial_result = serial_system.mint_token_serial(
                    request.wallet_address,
                    metadata={"purchase_type": "smart_contract"}
                )
                
                if not serial_result['success']:
                    continue
                
                serial_number = serial_result['serial_number']
                serial_as_uint = int(serial_number.replace('GST-', '').replace('-', ''), 16) % (2**256)
                
                if self.private_key:
                    account = Account.from_key(self.private_key)
                    
                    # Create metadata URI (could point to IPFS or centralized server)
                    metadata_uri = f"https://guardian-shield.io/api/token-metadata/{serial_number}"
                    
                    transaction = shield_contract.functions.mint(
                        request.wallet_address,
                        serial_as_uint,
                        metadata_uri
                    ).build_transaction({
                        'from': account.address,
                        'gas': 300000,
                        'gasPrice': w3.eth.gas_price,
                        'nonce': w3.eth.get_transaction_count(account.address),
                    })
                    
                    # Sign and send transaction
                    signed_txn = w3.eth.account.sign_transaction(transaction, self.private_key)
                    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                    
                    # Wait for confirmation
                    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                    
                    if receipt['status'] == 1:
                        # Parse logs to get token ID
                        logs = shield_contract.events.TokenMinted().processReceipt(receipt)
                        if logs:
                            token_id = logs[0]['args']['tokenId']
                            token_ids.append(token_id)
                            serial_numbers.append(serial_number)
                            tx_hashes.append(tx_hash.hex())
            
            return PurchaseResult(
                success=len(token_ids) > 0,
                transaction_hash=tx_hashes[0] if tx_hashes else None,
                token_ids=token_ids,
                serial_numbers=serial_numbers,
                contract_address=shield_contract_addr,
                error_message=None if len(token_ids) > 0 else "Failed to mint any SHIELD tokens"
            )
            
        except Exception as e:
            return PurchaseResult(
                success=False,
                error_message=f"Error purchasing SHIELD tokens: {str(e)}"
            )
    
    async def _simulate_guard_purchase(self, request: TokenPurchaseRequest) -> PurchaseResult:
        """Simulate GUARD token purchase when Web3 is not available"""
        purchase_id = secrets.token_hex(16)
        
        # Simulate transaction hash
        tx_hash = "0x" + hashlib.sha256(f"{purchase_id}{request.wallet_address}".encode()).hexdigest()
        
        # Store in simulated database
        self.payment_database[purchase_id] = {
            "type": "GUARD",
            "quantity": request.quantity,
            "wallet": request.wallet_address,
            "tx_hash": tx_hash,
            "timestamp": datetime.now().isoformat(),
            "status": "completed"
        }
        
        return PurchaseResult(
            success=True,
            transaction_hash=tx_hash,
            contract_address=DEPLOYED_CONTRACTS["sepolia"]["GuardianTokenSale"]
        )
    
    async def _simulate_shield_purchase(self, request: TokenPurchaseRequest) -> PurchaseResult:
        """Simulate SHIELD token purchase when Web3 is not available"""
        try:
            from shield_token_serial_system import ShieldTokenSerial
            serial_system = ShieldTokenSerial()
            
            purchase_id = secrets.token_hex(16)
            tx_hash = "0x" + hashlib.sha256(f"{purchase_id}{request.wallet_address}".encode()).hexdigest()
            
            token_ids = []
            serial_numbers = []
            
            # Generate serial numbers for each token
            for i in range(request.quantity):
                serial_result = serial_system.mint_token_serial(
                    request.wallet_address,
                    metadata={"purchase_type": "simulated"}
                )
                
                if serial_result['success']:
                    serial_numbers.append(serial_result['serial_number'])
                    token_ids.append(len(token_ids) + 1)  # Simulated token ID
            
            # Store in simulated database
            self.payment_database[purchase_id] = {
                "type": "SHIELD",
                "quantity": len(token_ids),
                "wallet": request.wallet_address,
                "tx_hash": tx_hash,
                "token_ids": token_ids,
                "serial_numbers": serial_numbers,
                "timestamp": datetime.now().isoformat(),
                "status": "completed"
            }
            
            return PurchaseResult(
                success=True,
                transaction_hash=tx_hash,
                token_ids=token_ids,
                serial_numbers=serial_numbers,
                contract_address="0x0000000000000000000000000000000000000000"  # Simulated
            )
            
        except Exception as e:
            return PurchaseResult(
                success=False,
                error_message=f"Error in simulated purchase: {str(e)}"
            )
    
    async def process_token_purchase(self, request: TokenPurchaseRequest) -> PurchaseResult:
        """Main entry point for token purchases"""
        if request.token_type.upper() == "GUARD":
            return await self.purchase_guard_tokens(request)
        elif request.token_type.upper() == "SHIELD":
            return await self.purchase_shield_tokens(request)
        else:
            return PurchaseResult(
                success=False,
                error_message=f"Unsupported token type: {request.token_type}"
            )

# FastAPI Integration
app = FastAPI(title="GuardianShield Smart Contract Payment System", version="1.0.0")
payment_processor = SmartContractPaymentProcessor()

class PurchaseRequest(BaseModel):
    token_type: str
    quantity: int
    wallet_address: str
    payment_method: str = "crypto"
    payment_token: str = "ETH"
    chain: str = "sepolia"

@app.post("/purchase-tokens")
async def purchase_tokens(request: PurchaseRequest):
    """Purchase tokens through smart contracts"""
    try:
        purchase_request = TokenPurchaseRequest(
            token_type=request.token_type,
            quantity=request.quantity,
            wallet_address=request.wallet_address,
            payment_method=request.payment_method,
            payment_token=request.payment_token,
            chain=request.chain
        )
        
        result = await payment_processor.process_token_purchase(purchase_request)
        
        return {
            "success": result.success,
            "transaction_hash": result.transaction_hash,
            "token_ids": result.token_ids,
            "serial_numbers": result.serial_numbers,
            "contract_address": result.contract_address,
            "error": result.error_message
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/token-prices")
async def get_token_prices():
    """Get current token prices"""
    return {
        "GUARD": {
            "usd": float(payment_processor.token_prices["GUARD"]),
            "wei": payment_processor.get_token_price_in_wei("GUARD")
        },
        "SHIELD": {
            "usd": float(payment_processor.token_prices["SHIELD"]),
            "wei": payment_processor.get_token_price_in_wei("SHIELD")
        }
    }

@app.get("/contract-info")
async def get_contract_info():
    """Get deployed contract information"""
    return {
        "contracts": DEPLOYED_CONTRACTS,
        "web3_available": WEB3_AVAILABLE,
        "connected_chains": list(payment_processor.web3_connections.keys()) if WEB3_AVAILABLE else []
    }

@app.get("/purchase-interface", response_class=HTMLResponse)
async def purchase_interface():
    """Web interface for token purchases"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GuardianShield - Buy Tokens</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Inter', sans-serif;
                background: linear-gradient(135deg, #1a1a2e, #16213e, #0f172a);
                color: #e2e8f0;
                min-height: 100vh;
                padding: 40px 20px;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: rgba(30, 41, 59, 0.8);
                backdrop-filter: blur(20px);
                border-radius: 20px;
                padding: 40px;
                border: 1px solid rgba(148, 163, 184, 0.2);
            }
            .header {
                text-align: center;
                margin-bottom: 40px;
            }
            .header h1 {
                font-size: 2.5rem;
                margin-bottom: 10px;
                background: linear-gradient(135deg, #00d4aa, #60a5fa);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            .token-selector {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 30px;
            }
            .token-card {
                background: rgba(30, 41, 59, 0.6);
                border: 2px solid rgba(148, 163, 184, 0.3);
                border-radius: 15px;
                padding: 20px;
                cursor: pointer;
                transition: all 0.3s ease;
                text-align: center;
            }
            .token-card:hover, .token-card.selected {
                border-color: #00d4aa;
                background: rgba(0, 212, 170, 0.1);
            }
            .token-card h3 {
                font-size: 1.5rem;
                margin-bottom: 10px;
                color: #00d4aa;
            }
            .token-card .price {
                font-size: 1.2rem;
                color: #cbd5e1;
            }
            .form-group {
                margin-bottom: 20px;
            }
            .form-group label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #00d4aa;
            }
            .form-group input, .form-group select {
                width: 100%;
                padding: 15px;
                border: 2px solid rgba(148, 163, 184, 0.3);
                border-radius: 10px;
                background: rgba(30, 41, 59, 0.6);
                color: white;
                font-size: 1rem;
            }
            .form-group input:focus, .form-group select:focus {
                outline: none;
                border-color: #00d4aa;
            }
            .purchase-btn {
                width: 100%;
                padding: 20px;
                background: linear-gradient(135deg, #00d4aa, #60a5fa);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 1.2rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .purchase-btn:hover {
                background: linear-gradient(135deg, #00b894, #4f96ff);
                transform: translateY(-2px);
            }
            .purchase-btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            .result {
                margin-top: 30px;
                padding: 20px;
                border-radius: 10px;
                display: none;
            }
            .result.success {
                background: rgba(0, 212, 170, 0.2);
                border: 2px solid #00d4aa;
            }
            .result.error {
                background: rgba(220, 38, 127, 0.2);
                border: 2px solid #dc267f;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛡️ Buy GuardianShield Tokens</h1>
                <p>Smart Contract Integration - Secure Token Purchases</p>
            </div>
            
            <form id="purchaseForm">
                <div class="token-selector">
                    <div class="token-card" data-token="GUARD">
                        <h3>💰 GUARD Token</h3>
                        <p class="price">$0.025 USD</p>
                        <p>Utility & Governance</p>
                    </div>
                    <div class="token-card" data-token="SHIELD">
                        <h3>🛡️ SHIELD Token</h3>
                        <p class="price">$0.50 USD</p>
                        <p>NFT with Serial Number</p>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="quantity">Quantity:</label>
                    <input type="number" id="quantity" name="quantity" min="1" max="1000" value="1" required>
                </div>
                
                <div class="form-group">
                    <label for="walletAddress">Wallet Address:</label>
                    <input type="text" id="walletAddress" name="walletAddress" placeholder="0x..." required>
                </div>
                
                <div class="form-group">
                    <label for="chain">Network:</label>
                    <select id="chain" name="chain">
                        <option value="sepolia">Sepolia Testnet</option>
                        <option value="ethereum">Ethereum Mainnet</option>
                    </select>
                </div>
                
                <button type="submit" class="purchase-btn" id="purchaseBtn">
                    Purchase Tokens
                </button>
            </form>
            
            <div id="result" class="result">
                <div id="resultMessage"></div>
            </div>
        </div>
        
        <script>
            let selectedToken = 'GUARD';
            
            // Token selection
            document.querySelectorAll('.token-card').forEach(card => {
                card.addEventListener('click', () => {
                    document.querySelectorAll('.token-card').forEach(c => c.classList.remove('selected'));
                    card.classList.add('selected');
                    selectedToken = card.dataset.token;
                });
            });
            
            // Form submission
            document.getElementById('purchaseForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = new FormData(e.target);
                const purchaseBtn = document.getElementById('purchaseBtn');
                const resultDiv = document.getElementById('result');
                const messageDiv = document.getElementById('resultMessage');
                
                purchaseBtn.disabled = true;
                purchaseBtn.textContent = 'Processing...';
                
                try {
                    const response = await fetch('/purchase-tokens', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            token_type: selectedToken,
                            quantity: parseInt(formData.get('quantity')),
                            wallet_address: formData.get('walletAddress'),
                            chain: formData.get('chain')
                        })
                    });
                    
                    const result = await response.json();
                    
                    resultDiv.style.display = 'block';
                    
                    if (result.success) {
                        resultDiv.className = 'result success';
                        let message = `✅ Purchase Successful!<br>`;
                        message += `Transaction Hash: ${result.transaction_hash}<br>`;
                        message += `Contract: ${result.contract_address}<br>`;
                        
                        if (result.serial_numbers) {
                            message += `Serial Numbers: ${result.serial_numbers.join(', ')}<br>`;
                        }
                        
                        messageDiv.innerHTML = message;
                    } else {
                        resultDiv.className = 'result error';
                        messageDiv.innerHTML = `❌ Purchase Failed: ${result.error}`;
                    }
                    
                } catch (error) {
                    resultDiv.style.display = 'block';
                    resultDiv.className = 'result error';
                    messageDiv.innerHTML = `❌ Error: ${error.message}`;
                }
                
                purchaseBtn.disabled = false;
                purchaseBtn.textContent = 'Purchase Tokens';
            });
            
            // Select GUARD by default
            document.querySelector('[data-token="GUARD"]').click();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    print("🛡️ Starting GuardianShield Smart Contract Payment System...")
    print("📍 Purchase Interface: http://localhost:8082/purchase-interface")
    print("🔗 Contract Integration: Enabled")
    uvicorn.run(app, host="0.0.0.0", port=8082)