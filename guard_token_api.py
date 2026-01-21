"""
GuardianShield Guard Token API Integration
Provides REST API endpoints for Guard Token contract interactions
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any, List
from decimal import Decimal
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from web3 import Web3
from eth_account import Account
import aiohttp
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
GUARDIAN_WALLET = '0xF262b772c2EBf526a5cF8634CA92597583Ef38ee'
GUARDIAN_API_KEY = 'J8QD4YPCWIRT3G1WFGHIC7YWGDBJ4VMGZ4'

# Web3 Configuration
WEB3_PROVIDERS = {
    'mainnet': 'https://eth.llamarpc.com',
    'sepolia': 'https://sepolia.infura.io/v3/YOUR_INFURA_KEY',
    'polygon': 'https://polygon-rpc.com',
    'arbitrum': 'https://arb1.arbitrum.io/rpc'
}

# Guard Token ABI (essential functions)
GUARD_TOKEN_ABI = [
    # ERC20 Standard
    {"inputs":[],"name":"name","outputs":[{"type":"string"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"symbol","outputs":[{"type":"string"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"decimals","outputs":[{"type":"uint8"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"totalSupply","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    
    # Guard Token Specific
    {"inputs":[],"name":"MAX_SUPPLY","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"INITIAL_SUPPLY","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"TOKEN_PRICE_USD_8","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"saleActive","outputs":[{"type":"bool"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"treasurer","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"getLatestEthUsdPrice","outputs":[{"type":"int256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"","type":"address"}],"name":"purchasedFromSale","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    
    # Sale Functions
    {"inputs":[],"name":"buyTokens","outputs":[],"stateMutability":"payable","type":"function"},
    {"inputs":[{"name":"_active","type":"bool"}],"name":"setSaleActive","outputs":[],"stateMutability":"nonpayable","type":"function"},
    
    # Owner Functions
    {"inputs":[{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"name":"ownerMint","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"_treasurer","type":"address"}],"name":"setTreasurer","outputs":[],"stateMutability":"nonpayable","type":"function"},
    
    # Withdrawal Functions
    {"inputs":[{"name":"amount","type":"uint256"}],"name":"createWithdrawalRequest","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"id","type":"uint256"}],"name":"approveWithdrawalAsOwner","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"id","type":"uint256"}],"name":"approveWithdrawalAsTreasurer","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"id","type":"uint256"}],"name":"executeWithdrawal","outputs":[],"stateMutability":"nonpayable","type":"function"},
    
    # Burn Functions
    {"inputs":[{"name":"account","type":"address"},{"name":"amount","type":"uint256"}],"name":"createBurnRequest","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"id","type":"uint256"}],"name":"approveBurnAsOwner","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"id","type":"uint256"}],"name":"approveBurnAsTreasurer","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"id","type":"uint256"}],"name":"executeBurn","outputs":[],"stateMutability":"nonpayable","type":"function"},
    
    # Events
    {"anonymous":false,"inputs":[{"indexed":true,"name":"id","type":"uint256"},{"indexed":false,"name":"amount","type":"uint256"}],"name":"WithdrawalRequested","type":"event"},
    {"anonymous":false,"inputs":[{"indexed":true,"name":"id","type":"uint256"},{"indexed":true,"name":"approver","type":"address"}],"name":"WithdrawalApproved","type":"event"},
    {"anonymous":false,"inputs":[{"indexed":true,"name":"id","type":"uint256"},{"indexed":false,"name":"amount","type":"uint256"},{"indexed":true,"name":"to","type":"address"}],"name":"WithdrawalExecuted","type":"event"},
]

# Request/Response Models
class TokenPurchaseRequest(BaseModel):
    eth_amount: str
    buyer_address: str
    
class TokenPurchaseResponse(BaseModel):
    transaction_hash: str
    tokens_purchased: str
    eth_spent: str
    gas_used: int
    status: str

class TokenInfoResponse(BaseModel):
    name: str
    symbol: str
    decimals: int
    total_supply: str
    max_supply: str
    sale_active: bool
    token_price_usd: str
    eth_usd_price: str
    contract_address: str

class WithdrawalRequest(BaseModel):
    amount: str
    
class BurnRequest(BaseModel):
    account: str
    amount: str

class ApprovalRequest(BaseModel):
    request_id: int

# FastAPI App
app = FastAPI(
    title="GuardianShield Guard Token API",
    description="REST API for Guard Token contract interactions",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GuardTokenAPI:
    def __init__(self):
        self.web3 = None
        self.contract = None
        self.account = None
        self.contract_address = None
        self.network = "mainnet"
        
    async def initialize(self, network: str = "mainnet", contract_address: str = None):
        """Initialize Web3 connection and contract instance"""
        try:
            self.network = network
            provider_url = WEB3_PROVIDERS.get(network, WEB3_PROVIDERS['mainnet'])
            self.web3 = Web3(Web3.HTTPProvider(provider_url))
            
            # Load contract address from deployment file if not provided
            if not contract_address:
                chain_id = await self._get_chain_id()
                deployment_file = f"deployment-guard-token-{chain_id}.json"
                if os.path.exists(deployment_file):
                    with open(deployment_file, 'r') as f:
                        deployment_data = json.load(f)
                        contract_address = deployment_data['guardToken']
            
            if not contract_address:
                raise ValueError("Contract address not provided and no deployment file found")
            
            self.contract_address = Web3.toChecksumAddress(contract_address)
            self.contract = self.web3.eth.contract(
                address=self.contract_address,
                abi=GUARD_TOKEN_ABI
            )
            
            # Set up account (in production, use secure key management)
            private_key = os.environ.get('GUARDIAN_PRIVATE_KEY')
            if private_key:
                self.account = Account.from_key(private_key)
            
            logger.info(f"GuardToken API initialized on {network}")
            logger.info(f"Contract address: {self.contract_address}")
            
        except Exception as e:
            logger.error(f"Failed to initialize GuardToken API: {e}")
            raise
    
    async def _get_chain_id(self) -> int:
        """Get current chain ID"""
        return await asyncio.to_thread(lambda: self.web3.eth.chain_id)
    
    async def get_token_info(self) -> TokenInfoResponse:
        """Get basic token information"""
        try:
            # Get token details
            name = await asyncio.to_thread(self.contract.functions.name().call)
            symbol = await asyncio.to_thread(self.contract.functions.symbol().call)
            decimals = await asyncio.to_thread(self.contract.functions.decimals().call)
            total_supply = await asyncio.to_thread(self.contract.functions.totalSupply().call)
            max_supply = await asyncio.to_thread(self.contract.functions.MAX_SUPPLY().call)
            sale_active = await asyncio.to_thread(self.contract.functions.saleActive().call)
            token_price_usd_8 = await asyncio.to_thread(self.contract.functions.TOKEN_PRICE_USD_8().call)
            
            # Get ETH/USD price
            eth_usd_price = "0"
            try:
                eth_price_raw = await asyncio.to_thread(self.contract.functions.getLatestEthUsdPrice().call)
                eth_usd_price = str(eth_price_raw / 1e8)
            except:
                pass
            
            return TokenInfoResponse(
                name=name,
                symbol=symbol,
                decimals=decimals,
                total_supply=str(total_supply),
                max_supply=str(max_supply),
                sale_active=sale_active,
                token_price_usd=str(token_price_usd_8 / 1e8),
                eth_usd_price=eth_usd_price,
                contract_address=self.contract_address
            )
            
        except Exception as e:
            logger.error(f"Error getting token info: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_balance(self, address: str) -> str:
        """Get token balance for an address"""
        try:
            address = Web3.toChecksumAddress(address)
            balance = await asyncio.to_thread(
                self.contract.functions.balanceOf(address).call
            )
            return str(balance)
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def purchase_tokens(self, request: TokenPurchaseRequest) -> TokenPurchaseResponse:
        """Purchase tokens via the smart contract"""
        if not self.account:
            raise HTTPException(status_code=400, detail="Private key not configured")
        
        try:
            eth_amount = Web3.toWei(request.eth_amount, 'ether')
            buyer_address = Web3.toChecksumAddress(request.buyer_address)
            
            # Build transaction
            transaction = self.contract.functions.buyTokens().buildTransaction({
                'from': self.account.address,
                'value': eth_amount,
                'gas': 200000,
                'gasPrice': await asyncio.to_thread(self.web3.eth.gas_price),
                'nonce': await asyncio.to_thread(
                    lambda: self.web3.eth.get_transaction_count(self.account.address)
                )
            })
            
            # Sign and send transaction
            signed_tx = self.account.sign_transaction(transaction)
            tx_hash = await asyncio.to_thread(
                lambda: self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            )
            
            # Wait for confirmation
            receipt = await asyncio.to_thread(
                lambda: self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            )
            
            return TokenPurchaseResponse(
                transaction_hash=tx_hash.hex(),
                tokens_purchased="0",  # Would need to parse logs to get exact amount
                eth_spent=request.eth_amount,
                gas_used=receipt['gasUsed'],
                status="confirmed" if receipt['status'] == 1 else "failed"
            )
            
        except Exception as e:
            logger.error(f"Error purchasing tokens: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# Global API instance
guard_token_api = GuardTokenAPI()

@app.on_event("startup")
async def startup_event():
    """Initialize the API on startup"""
    try:
        # Load contract address from environment or deployment file
        contract_address = os.environ.get('GUARD_TOKEN_CONTRACT')
        network = os.environ.get('NETWORK', 'mainnet')
        
        await guard_token_api.initialize(network, contract_address)
        logger.info("Guard Token API started successfully")
    except Exception as e:
        logger.error(f"Failed to start API: {e}")

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "GuardianShield Guard Token API",
        "version": "1.0.0",
        "contract": guard_token_api.contract_address,
        "network": guard_token_api.network
    }

@app.get("/token/info", response_model=TokenInfoResponse)
async def get_token_info():
    """Get token information"""
    return await guard_token_api.get_token_info()

@app.get("/token/balance/{address}")
async def get_balance(address: str):
    """Get token balance for an address"""
    balance = await guard_token_api.get_balance(address)
    return {"address": address, "balance": balance}

@app.post("/token/purchase", response_model=TokenPurchaseResponse)
async def purchase_tokens(request: TokenPurchaseRequest):
    """Purchase tokens"""
    return await guard_token_api.purchase_tokens(request)

@app.get("/token/price")
async def get_token_price():
    """Get current token price in USD and ETH"""
    try:
        info = await guard_token_api.get_token_info()
        return {
            "token_price_usd": info.token_price_usd,
            "eth_usd_price": info.eth_usd_price,
            "sale_active": info.sale_active
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        if guard_token_api.web3 and guard_token_api.web3.isConnected():
            latest_block = guard_token_api.web3.eth.block_number
            return {
                "status": "healthy",
                "network": guard_token_api.network,
                "latest_block": latest_block,
                "contract": guard_token_api.contract_address
            }
        else:
            return {"status": "unhealthy", "reason": "Web3 not connected"}
    except Exception as e:
        return {"status": "unhealthy", "reason": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)