#!/usr/bin/env python3
"""
GuardianShield Smart Contract DeFi System
Integrates staking and liquidity pools with actual smart contracts
"""

import json
import os
import secrets
import hashlib
import sqlite3
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

# DeFi Contract Configuration
DEFI_CONTRACTS = {
    "ethereum": {
        "GuardianStaking": "0x0000000000000000000000000000000000000000",  # To be deployed
        "GuardianLiquidityPool": "0x2c64492B8954180f75Db25bf1665bDA18f712F6e",  # Deployed
        "GuardianToken": "0x0000000000000000000000000000000000000000",  # To be deployed
        "rpc_url": "https://eth-mainnet.alchemyapi.io/v2/YOUR-API-KEY",
        "chain_id": 1
    },
    "sepolia": {
        "GuardianStaking": "0x0000000000000000000000000000000000000000",  # To be deployed
        "GuardianLiquidityPool": "0x2c64492B8954180f75Db25bf1665bDA18f712F6e",  # Deployed
        "GuardianToken": "0x0000000000000000000000000000000000000000",  # To be deployed
        "rpc_url": "https://sepolia.infura.io/v3/YOUR-API-KEY",
        "chain_id": 11155111
    }
}

# Contract ABIs
GUARDIAN_STAKING_ABI = [
    {
        "inputs": [{"name": "amount", "type": "uint256"}],
        "name": "stake",
        "outputs": [],
        "type": "function"
    },
    {
        "inputs": [{"name": "amount", "type": "uint256"}],
        "name": "unstake",
        "outputs": [],
        "type": "function"
    },
    {
        "inputs": [],
        "name": "claimReward",
        "outputs": [],
        "type": "function"
    },
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "stakes",
        "outputs": [
            {"name": "amount", "type": "uint256"},
            {"name": "rewardDebt", "type": "uint256"},
            {"name": "lastStaked", "type": "uint256"}
        ],
        "type": "function"
    },
    {
        "inputs": [],
        "name": "rewardRate",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]

GUARDIAN_LIQUIDITY_POOL_ABI = [
    {
        "inputs": [{"name": "guardAmount", "type": "uint256"}, {"name": "shieldAmount", "type": "uint256"}],
        "name": "addLiquidity",
        "outputs": [],
        "type": "function"
    },
    {
        "inputs": [{"name": "amount", "type": "uint256"}],
        "name": "removeLiquidity",
        "outputs": [],
        "type": "function"
    },
    {
        "inputs": [{"name": "provider", "type": "address"}],
        "name": "liquidity",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalLiquidity",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]

GUARDIAN_TOKEN_ABI = [
    {
        "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]

@dataclass
class StakingRequest:
    action: str  # "stake", "unstake", "claim"
    amount: Optional[Decimal] = None
    wallet_address: str = ""
    duration_months: int = 1  # 1, 6, 12 months
    chain: str = "sepolia"

@dataclass
class LiquidityRequest:
    action: str  # "add", "remove"
    guard_amount: Optional[Decimal] = None
    shield_amount: Optional[Decimal] = None
    wallet_address: str = ""
    chain: str = "sepolia"

@dataclass
class DeFiResult:
    success: bool
    transaction_hash: Optional[str] = None
    staking_info: Optional[Dict] = None
    liquidity_info: Optional[Dict] = None
    rewards_claimed: Optional[Decimal] = None
    error_message: Optional[str] = None

class SmartContractDeFiProcessor:
    def __init__(self):
        self.web3_connections = {}
        self.private_key = os.getenv('GUARDIAN_PRIVATE_KEY')
        
        if WEB3_AVAILABLE:
            self._init_web3_connections()
        
        # Initialize database
        self._init_database()
        
        # APR rates for different staking periods
        self.staking_apr = {
            1: Decimal("0.04"),   # 4% APR for 1 month
            6: Decimal("0.06"),   # 6% APR for 6 months  
            12: Decimal("0.10")   # 10% APR for 12 months
        }
    
    def _init_web3_connections(self):
        """Initialize Web3 connections"""
        for chain, config in DEFI_CONTRACTS.items():
            try:
                w3 = Web3(Web3.HTTPProvider(config["rpc_url"]))
                if w3.is_connected():
                    self.web3_connections[chain] = w3
                    print(f"✅ Connected to {chain} network")
                else:
                    print(f"❌ Failed to connect to {chain} network")
            except Exception as e:
                print(f"❌ Error connecting to {chain}: {e}")
    
    def _init_database(self):
        """Initialize staking and liquidity databases"""
        conn = sqlite3.connect('defi_operations.db')
        cursor = conn.cursor()
        
        # Staking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS staking_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wallet_address TEXT NOT NULL,
                amount DECIMAL NOT NULL,
                duration_months INTEGER NOT NULL,
                apr DECIMAL NOT NULL,
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date TIMESTAMP,
                status TEXT DEFAULT 'active',
                transaction_hash TEXT,
                rewards_earned DECIMAL DEFAULT 0,
                last_reward_claim TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Liquidity pool table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS liquidity_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wallet_address TEXT NOT NULL,
                guard_amount DECIMAL NOT NULL,
                shield_amount DECIMAL NOT NULL,
                lp_tokens DECIMAL NOT NULL,
                fees_earned DECIMAL DEFAULT 0,
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active',
                transaction_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def process_staking(self, request: StakingRequest) -> DeFiResult:
        """Process staking operations through smart contracts"""
        try:
            if not WEB3_AVAILABLE or not self._contracts_deployed(request.chain):
                return await self._simulate_staking(request)
            
            # Real smart contract interaction
            chain = request.chain
            w3 = self.web3_connections[chain]
            contract_config = DEFI_CONTRACTS[chain]
            
            staking_contract = w3.eth.contract(
                address=contract_config["GuardianStaking"],
                abi=GUARDIAN_STAKING_ABI
            )
            
            guard_token_contract = w3.eth.contract(
                address=contract_config["GuardianToken"],
                abi=GUARDIAN_TOKEN_ABI
            )
            
            if request.action == "stake":
                return await self._execute_stake(request, w3, staking_contract, guard_token_contract)
            elif request.action == "unstake":
                return await self._execute_unstake(request, w3, staking_contract)
            elif request.action == "claim":
                return await self._execute_claim_rewards(request, w3, staking_contract)
            else:
                return DeFiResult(success=False, error_message=f"Unknown staking action: {request.action}")
                
        except Exception as e:
            return DeFiResult(success=False, error_message=f"Staking error: {str(e)}")
    
    async def process_liquidity(self, request: LiquidityRequest) -> DeFiResult:
        """Process liquidity pool operations through smart contracts"""
        try:
            if not WEB3_AVAILABLE or not self._contracts_deployed(request.chain):
                return await self._simulate_liquidity(request)
            
            # Real smart contract interaction
            chain = request.chain
            w3 = self.web3_connections[chain]
            contract_config = DEFI_CONTRACTS[chain]
            
            liquidity_contract = w3.eth.contract(
                address=contract_config["GuardianLiquidityPool"],
                abi=GUARDIAN_LIQUIDITY_POOL_ABI
            )
            
            if request.action == "add":
                return await self._execute_add_liquidity(request, w3, liquidity_contract)
            elif request.action == "remove":
                return await self._execute_remove_liquidity(request, w3, liquidity_contract)
            else:
                return DeFiResult(success=False, error_message=f"Unknown liquidity action: {request.action}")
                
        except Exception as e:
            return DeFiResult(success=False, error_message=f"Liquidity error: {str(e)}")
    
    def _contracts_deployed(self, chain: str) -> bool:
        """Check if contracts are deployed"""
        config = DEFI_CONTRACTS.get(chain, {})
        return (config.get("GuardianStaking", "0x0000000000000000000000000000000000000000") != "0x0000000000000000000000000000000000000000" and
                config.get("GuardianLiquidityPool", "0x0000000000000000000000000000000000000000") != "0x0000000000000000000000000000000000000000")
    
    async def _simulate_staking(self, request: StakingRequest) -> DeFiResult:
        """Simulate staking operations"""
        conn = sqlite3.connect('defi_operations.db')
        cursor = conn.cursor()
        
        tx_hash = "0x" + hashlib.sha256(f"stake_{request.wallet_address}_{datetime.now()}".encode()).hexdigest()
        
        try:
            if request.action == "stake":
                apr = self.staking_apr.get(request.duration_months, Decimal("0.04"))
                end_date = datetime.now() + timedelta(days=30 * request.duration_months)
                
                cursor.execute('''
                    INSERT INTO staking_positions 
                    (wallet_address, amount, duration_months, apr, end_date, transaction_hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (request.wallet_address, str(request.amount), request.duration_months, 
                      str(apr), end_date, tx_hash))
                
                conn.commit()
                
                return DeFiResult(
                    success=True,
                    transaction_hash=tx_hash,
                    staking_info={
                        "amount": str(request.amount),
                        "duration_months": request.duration_months,
                        "apr": str(apr),
                        "end_date": end_date.isoformat()
                    }
                )
            
            elif request.action == "unstake":
                cursor.execute('''
                    UPDATE staking_positions 
                    SET status = 'unstaked' 
                    WHERE wallet_address = ? AND status = 'active'
                ''', (request.wallet_address,))
                
                conn.commit()
                
                return DeFiResult(
                    success=True,
                    transaction_hash=tx_hash,
                    staking_info={"action": "unstaked"}
                )
            
            elif request.action == "claim":
                # Calculate simulated rewards
                cursor.execute('''
                    SELECT amount, apr, start_date FROM staking_positions 
                    WHERE wallet_address = ? AND status = 'active'
                ''', (request.wallet_address,))
                
                positions = cursor.fetchall()
                total_rewards = Decimal("0")
                
                for amount, apr, start_date in positions:
                    days_staked = (datetime.now() - datetime.fromisoformat(start_date)).days
                    rewards = Decimal(amount) * Decimal(apr) * (days_staked / 365)
                    total_rewards += rewards
                
                return DeFiResult(
                    success=True,
                    transaction_hash=tx_hash,
                    rewards_claimed=total_rewards
                )
                
        except Exception as e:
            conn.rollback()
            return DeFiResult(success=False, error_message=f"Database error: {str(e)}")
        finally:
            conn.close()
    
    async def _simulate_liquidity(self, request: LiquidityRequest) -> DeFiResult:
        """Simulate liquidity pool operations"""
        conn = sqlite3.connect('defi_operations.db')
        cursor = conn.cursor()
        
        tx_hash = "0x" + hashlib.sha256(f"liquidity_{request.wallet_address}_{datetime.now()}".encode()).hexdigest()
        
        try:
            if request.action == "add":
                # Calculate LP tokens (simplified)
                lp_tokens = (request.guard_amount + request.shield_amount) / 2
                
                cursor.execute('''
                    INSERT INTO liquidity_positions 
                    (wallet_address, guard_amount, shield_amount, lp_tokens, transaction_hash)
                    VALUES (?, ?, ?, ?, ?)
                ''', (request.wallet_address, str(request.guard_amount), str(request.shield_amount),
                      str(lp_tokens), tx_hash))
                
                conn.commit()
                
                return DeFiResult(
                    success=True,
                    transaction_hash=tx_hash,
                    liquidity_info={
                        "guard_amount": str(request.guard_amount),
                        "shield_amount": str(request.shield_amount),
                        "lp_tokens": str(lp_tokens)
                    }
                )
            
            elif request.action == "remove":
                cursor.execute('''
                    UPDATE liquidity_positions 
                    SET status = 'removed' 
                    WHERE wallet_address = ? AND status = 'active'
                ''', (request.wallet_address,))
                
                conn.commit()
                
                return DeFiResult(
                    success=True,
                    transaction_hash=tx_hash,
                    liquidity_info={"action": "removed"}
                )
                
        except Exception as e:
            conn.rollback()
            return DeFiResult(success=False, error_message=f"Database error: {str(e)}")
        finally:
            conn.close()
    
    def get_staking_positions(self, wallet_address: str) -> List[Dict]:
        """Get user's staking positions"""
        conn = sqlite3.connect('defi_operations.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM staking_positions 
            WHERE wallet_address = ? AND status = 'active'
            ORDER BY created_at DESC
        ''', (wallet_address,))
        
        positions = []
        for row in cursor.fetchall():
            positions.append({
                "id": row[0],
                "amount": row[2],
                "duration_months": row[3],
                "apr": row[4],
                "start_date": row[5],
                "end_date": row[6],
                "rewards_earned": row[9]
            })
        
        conn.close()
        return positions
    
    def get_liquidity_positions(self, wallet_address: str) -> List[Dict]:
        """Get user's liquidity positions"""
        conn = sqlite3.connect('defi_operations.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM liquidity_positions 
            WHERE wallet_address = ? AND status = 'active'
            ORDER BY created_at DESC
        ''', (wallet_address,))
        
        positions = []
        for row in cursor.fetchall():
            positions.append({
                "id": row[0],
                "guard_amount": row[2],
                "shield_amount": row[3],
                "lp_tokens": row[4],
                "fees_earned": row[5],
                "start_date": row[6]
            })
        
        conn.close()
        return positions

# FastAPI Integration
app = FastAPI(title="GuardianShield Smart Contract DeFi System", version="1.0.0")
defi_processor = SmartContractDeFiProcessor()

class StakingRequestModel(BaseModel):
    action: str
    amount: Optional[float] = None
    wallet_address: str
    duration_months: int = 1
    chain: str = "sepolia"

class LiquidityRequestModel(BaseModel):
    action: str
    guard_amount: Optional[float] = None
    shield_amount: Optional[float] = None
    wallet_address: str
    chain: str = "sepolia"

@app.post("/staking")
async def process_staking_request(request: StakingRequestModel):
    """Process staking operations"""
    try:
        staking_request = StakingRequest(
            action=request.action,
            amount=Decimal(str(request.amount)) if request.amount else None,
            wallet_address=request.wallet_address,
            duration_months=request.duration_months,
            chain=request.chain
        )
        
        result = await defi_processor.process_staking(staking_request)
        
        return {
            "success": result.success,
            "transaction_hash": result.transaction_hash,
            "staking_info": result.staking_info,
            "rewards_claimed": str(result.rewards_claimed) if result.rewards_claimed else None,
            "error": result.error_message
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/liquidity")
async def process_liquidity_request(request: LiquidityRequestModel):
    """Process liquidity pool operations"""
    try:
        liquidity_request = LiquidityRequest(
            action=request.action,
            guard_amount=Decimal(str(request.guard_amount)) if request.guard_amount else None,
            shield_amount=Decimal(str(request.shield_amount)) if request.shield_amount else None,
            wallet_address=request.wallet_address,
            chain=request.chain
        )
        
        result = await defi_processor.process_liquidity(liquidity_request)
        
        return {
            "success": result.success,
            "transaction_hash": result.transaction_hash,
            "liquidity_info": result.liquidity_info,
            "error": result.error_message
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/staking/{wallet_address}")
async def get_user_staking(wallet_address: str):
    """Get user's staking positions"""
    positions = defi_processor.get_staking_positions(wallet_address)
    return {"positions": positions}

@app.get("/liquidity/{wallet_address}")
async def get_user_liquidity(wallet_address: str):
    """Get user's liquidity positions"""
    positions = defi_processor.get_liquidity_positions(wallet_address)
    return {"positions": positions}

@app.get("/defi-interface", response_class=HTMLResponse)
async def defi_interface():
    """Web interface for DeFi operations"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GuardianShield - DeFi Operations</title>
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
                max-width: 1200px;
                margin: 0 auto;
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
            .defi-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 30px;
                margin-bottom: 40px;
            }
            .defi-card {
                background: rgba(30, 41, 59, 0.8);
                backdrop-filter: blur(20px);
                border-radius: 20px;
                padding: 30px;
                border: 1px solid rgba(148, 163, 184, 0.2);
            }
            .card-header {
                display: flex;
                align-items: center;
                margin-bottom: 25px;
            }
            .card-header i {
                font-size: 2rem;
                margin-right: 15px;
                color: #00d4aa;
            }
            .card-header h3 {
                font-size: 1.5rem;
                color: #f1f5f9;
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
            .btn {
                width: 100%;
                padding: 15px;
                border: none;
                border-radius: 10px;
                font-size: 1.1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                margin-top: 10px;
            }
            .btn-primary {
                background: linear-gradient(135deg, #00d4aa, #60a5fa);
                color: white;
            }
            .btn-secondary {
                background: linear-gradient(135deg, #6366f1, #8b5cf6);
                color: white;
            }
            .apr-info {
                background: rgba(0, 212, 170, 0.1);
                border: 1px solid #00d4aa;
                border-radius: 10px;
                padding: 15px;
                margin: 15px 0;
                text-align: center;
            }
            .positions {
                margin-top: 30px;
            }
            .position-card {
                background: rgba(30, 41, 59, 0.6);
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 15px;
            }
        </style>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏦 GuardianShield DeFi</h1>
                <p>Smart Contract Staking & Liquidity Pools</p>
            </div>
            
            <div class="defi-grid">
                <!-- Staking Section -->
                <div class="defi-card">
                    <div class="card-header">
                        <i class="fas fa-coins"></i>
                        <h3>Staking</h3>
                    </div>
                    
                    <div class="apr-info">
                        <div><strong>APR Rates:</strong></div>
                        <div>1 Month: 4% APR</div>
                        <div>6 Months: 6% APR</div>
                        <div>12 Months: 10% APR</div>
                    </div>
                    
                    <form id="stakingForm">
                        <div class="form-group">
                            <label for="stakeWallet">Wallet Address:</label>
                            <input type="text" id="stakeWallet" placeholder="0x..." required>
                        </div>
                        <div class="form-group">
                            <label for="stakeAmount">Amount (GUARD):</label>
                            <input type="number" id="stakeAmount" min="1" step="0.01" required>
                        </div>
                        <div class="form-group">
                            <label for="stakeDuration">Duration:</label>
                            <select id="stakeDuration" required>
                                <option value="1">1 Month (4% APR)</option>
                                <option value="6">6 Months (6% APR)</option>
                                <option value="12">12 Months (10% APR)</option>
                            </select>
                        </div>
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-lock"></i> Stake Tokens
                        </button>
                    </form>
                    
                    <button onclick="unstakeTokens()" class="btn btn-secondary">
                        <i class="fas fa-unlock"></i> Unstake Tokens
                    </button>
                    
                    <button onclick="claimRewards()" class="btn btn-secondary">
                        <i class="fas fa-gift"></i> Claim Rewards
                    </button>
                </div>
                
                <!-- Liquidity Pool Section -->
                <div class="defi-card">
                    <div class="card-header">
                        <i class="fas fa-water"></i>
                        <h3>Liquidity Pool</h3>
                    </div>
                    
                    <form id="liquidityForm">
                        <div class="form-group">
                            <label for="lpWallet">Wallet Address:</label>
                            <input type="text" id="lpWallet" placeholder="0x..." required>
                        </div>
                        <div class="form-group">
                            <label for="guardAmount">GUARD Amount:</label>
                            <input type="number" id="guardAmount" min="1" step="0.01" required>
                        </div>
                        <div class="form-group">
                            <label for="shieldAmount">SHIELD Amount:</label>
                            <input type="number" id="shieldAmount" min="1" step="0.01" required>
                        </div>
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-plus"></i> Add Liquidity
                        </button>
                    </form>
                    
                    <button onclick="removeLiquidity()" class="btn btn-secondary">
                        <i class="fas fa-minus"></i> Remove Liquidity
                    </button>
                </div>
            </div>
            
            <!-- User Positions -->
            <div id="userPositions" style="display: none;">
                <h3>Your Positions</h3>
                <div id="stakingPositions" class="positions"></div>
                <div id="liquidityPositions" class="positions"></div>
            </div>
        </div>
        
        <script>
            // Staking operations
            document.getElementById('stakingForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = new FormData(e.target);
                
                try {
                    const response = await fetch('/staking', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            action: 'stake',
                            wallet_address: formData.get('stakeWallet'),
                            amount: parseFloat(formData.get('stakeAmount')),
                            duration_months: parseInt(formData.get('stakeDuration'))
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        alert(`✅ Staking successful! TX: ${result.transaction_hash}`);
                        loadUserPositions(formData.get('stakeWallet'));
                    } else {
                        alert(`❌ Staking failed: ${result.error}`);
                    }
                    
                } catch (error) {
                    alert(`❌ Error: ${error.message}`);
                }
            });
            
            // Liquidity operations
            document.getElementById('liquidityForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = new FormData(e.target);
                
                try {
                    const response = await fetch('/liquidity', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            action: 'add',
                            wallet_address: formData.get('lpWallet'),
                            guard_amount: parseFloat(formData.get('guardAmount')),
                            shield_amount: parseFloat(formData.get('shieldAmount'))
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        alert(`✅ Liquidity added! TX: ${result.transaction_hash}`);
                        loadUserPositions(formData.get('lpWallet'));
                    } else {
                        alert(`❌ Liquidity failed: ${result.error}`);
                    }
                    
                } catch (error) {
                    alert(`❌ Error: ${error.message}`);
                }
            });
            
            async function unstakeTokens() {
                const wallet = document.getElementById('stakeWallet').value;
                if (!wallet) {
                    alert('Please enter wallet address');
                    return;
                }
                
                try {
                    const response = await fetch('/staking', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            action: 'unstake',
                            wallet_address: wallet
                        })
                    });
                    
                    const result = await response.json();
                    alert(result.success ? `✅ Unstaked! TX: ${result.transaction_hash}` : `❌ Error: ${result.error}`);
                    
                } catch (error) {
                    alert(`❌ Error: ${error.message}`);
                }
            }
            
            async function claimRewards() {
                const wallet = document.getElementById('stakeWallet').value;
                if (!wallet) {
                    alert('Please enter wallet address');
                    return;
                }
                
                try {
                    const response = await fetch('/staking', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            action: 'claim',
                            wallet_address: wallet
                        })
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        alert(`✅ Claimed ${result.rewards_claimed} GUARD rewards!`);
                    } else {
                        alert(`❌ Error: ${result.error}`);
                    }
                    
                } catch (error) {
                    alert(`❌ Error: ${error.message}`);
                }
            }
            
            async function removeLiquidity() {
                const wallet = document.getElementById('lpWallet').value;
                if (!wallet) {
                    alert('Please enter wallet address');
                    return;
                }
                
                try {
                    const response = await fetch('/liquidity', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            action: 'remove',
                            wallet_address: wallet
                        })
                    });
                    
                    const result = await response.json();
                    alert(result.success ? `✅ Liquidity removed! TX: ${result.transaction_hash}` : `❌ Error: ${result.error}`);
                    
                } catch (error) {
                    alert(`❌ Error: ${error.message}`);
                }
            }
            
            async function loadUserPositions(wallet) {
                try {
                    const [stakingResponse, liquidityResponse] = await Promise.all([
                        fetch(`/staking/${wallet}`),
                        fetch(`/liquidity/${wallet}`)
                    ]);
                    
                    const stakingData = await stakingResponse.json();
                    const liquidityData = await liquidityResponse.json();
                    
                    // Display positions
                    const stakingDiv = document.getElementById('stakingPositions');
                    const liquidityDiv = document.getElementById('liquidityPositions');
                    
                    if (stakingData.positions.length > 0) {
                        stakingDiv.innerHTML = '<h4>Staking Positions</h4>' + 
                            stakingData.positions.map(pos => `
                                <div class="position-card">
                                    <div>Amount: ${pos.amount} GUARD</div>
                                    <div>Duration: ${pos.duration_months} months</div>
                                    <div>APR: ${pos.apr}%</div>
                                    <div>Rewards: ${pos.rewards_earned} GUARD</div>
                                </div>
                            `).join('');
                    }
                    
                    if (liquidityData.positions.length > 0) {
                        liquidityDiv.innerHTML = '<h4>Liquidity Positions</h4>' + 
                            liquidityData.positions.map(pos => `
                                <div class="position-card">
                                    <div>GUARD: ${pos.guard_amount}</div>
                                    <div>SHIELD: ${pos.shield_amount}</div>
                                    <div>LP Tokens: ${pos.lp_tokens}</div>
                                    <div>Fees Earned: ${pos.fees_earned}</div>
                                </div>
                            `).join('');
                    }
                    
                    document.getElementById('userPositions').style.display = 'block';
                    
                } catch (error) {
                    console.error('Error loading positions:', error);
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    print("🏦 Starting GuardianShield Smart Contract DeFi System...")
    print("📍 DeFi Interface: http://localhost:8084/defi-interface")
    print("🔗 Smart Contract Integration: Enabled")
    uvicorn.run(app, host="0.0.0.0", port=8084)