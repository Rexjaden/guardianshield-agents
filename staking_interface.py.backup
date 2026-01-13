"""
GuardianShield Staking Interface
User-friendly staking dashboard with APY calculations, lock periods, and rewards
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import sqlite3
import json
from datetime import datetime, timedelta
import math
import logging
from dataclasses import dataclass
from enum import Enum
import secrets

class CryptoType(Enum):
    """Supported cryptocurrencies for pairing"""
    BITCOIN = "BTC"
    ETHEREUM = "ETH"
    SOLANA = "SOL"
    BINANCE_COIN = "BNB"
    CARDANO = "ADA"
    POLYGON = "MATIC"
    AVALANCHE = "AVAX"
    CHAINLINK = "LINK"

@dataclass
class ShieldToken:
    """SHIELD token representation with unique security number"""
    shield_id: str
    security_number: str
    total_value_usd: float
    crypto_type: str
    crypto_amount: float
    guard_amount: float
    mint_timestamp: datetime
    lock_end_timestamp: datetime
    apy_rate: float
    owner_address: str
    
    @property
    def is_mature(self) -> bool:
        """Check if SHIELD token has matured"""
        return datetime.now() >= self.lock_end_timestamp
    
    @property
    def days_remaining(self) -> int:
        """Days remaining until maturity"""
        if self.is_mature:
            return 0
        return (self.lock_end_timestamp - datetime.now()).days
    
    @property
    def current_value(self) -> float:
        """Calculate current value including rewards"""
        days_held = (datetime.now() - self.mint_timestamp).days
        daily_rate = self.apy_rate / 365 / 100
        return self.total_value_usd * (1 + daily_rate * days_held)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GuardianShield Staking Interface",
    description="Stake GUARD tokens and earn rewards while securing the ecosystem",
    version="1.0.0"
)

security = HTTPBearer()

@dataclass
class StakingPool:
    """Staking pool configuration"""
    pool_id: str
    name: str
    description: str
    min_stake: int
    lock_period_days: int
    base_apy: float
    bonus_apy: float
    max_capacity: int
    current_staked: int
    security_level: str
    
    @property
    def effective_apy(self) -> float:
        """Calculate effective APY including bonuses"""
        utilization_rate = self.current_staked / self.max_capacity if self.max_capacity > 0 else 0
        bonus_multiplier = 1 + (utilization_rate * 0.2)  # Up to 20% bonus at full capacity
        return (self.base_apy + self.bonus_apy) * bonus_multiplier
    
    @property
    def available_capacity(self) -> int:
        """Remaining staking capacity"""
        return max(0, self.max_capacity - self.current_staked)
    
    @property
    def utilization_percentage(self) -> float:
        """Pool utilization percentage"""
        return (self.current_staked / self.max_capacity * 100) if self.max_capacity > 0 else 0

class StakingManager:
    """Manages staking pools and user stakes"""
    
    def __init__(self):
        self.pools = self._initialize_pools()
        self.db_path = "staking.db"
        self._initialize_database()
    
    def _initialize_pools(self) -> Dict[str, StakingPool]:
        """Initialize SHIELD staking pool configurations for crypto+GUARD=SHIELD pairs"""
        return {
            "shield_btc_guard": StakingPool(
                pool_id="shield_btc_guard",
                name="SHIELD-BTC Pool",
                description="Pair your Bitcoin with GUARD tokens to mint high-security numbered SHIELD tokens",
                min_stake=1000,  # Minimum GUARD tokens required
                lock_period_days=30,
                base_apy=15.0,
                bonus_apy=5.0,
                max_capacity=250_000_000,  # GUARD tokens available for pairing
                current_staked=45_800_000,
                security_level="Ultra"
            ),
            
            "shield_eth_guard": StakingPool(
                pool_id="shield_eth_guard",
                name="SHIELD-ETH Pool", 
                description="Pair your Ethereum with GUARD tokens to mint premium numbered SHIELD tokens",
                min_stake=500,
                lock_period_days=14,
                base_apy=18.0,
                bonus_apy=7.0,
                max_capacity=300_000_000,
                current_staked=87_200_000,
                security_level="Premium"
            ),
            
            "shield_sol_guard": StakingPool(
                pool_id="shield_sol_guard",
                name="SHIELD-SOL Pool",
                description="Pair your Solana with GUARD tokens for fast, secure SHIELD token generation",
                min_stake=300,
                lock_period_days=7,
                base_apy=22.0,
                bonus_apy=8.0,
                max_capacity=200_000_000,
                current_staked=62_100_000,
                security_level="Advanced"
            ),
            
            "shield_multi_guard": StakingPool(
                pool_id="shield_multi_guard",
                name="SHIELD-MULTI Pool",
                description="Pair multiple cryptocurrencies with GUARD tokens for diversified SHIELD minting",
                min_stake=100,
                lock_period_days=21,
                base_apy=12.0,
                bonus_apy=4.0,
                max_capacity=500_000_000,
                current_staked=156_300_000,
                security_level="Diversified"
            )
        }
    
    def _initialize_database(self):
        """Initialize staking database with SHIELD token support"""
        conn = sqlite3.connect(self.db_path)
        
        # User stakes table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_stakes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                pool_id TEXT NOT NULL,
                amount INTEGER NOT NULL,
                stake_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                lock_end_timestamp TIMESTAMP NOT NULL,
                rewards_claimed INTEGER DEFAULT 0,
                last_reward_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active',
                transaction_hash TEXT,
                chain_id INTEGER DEFAULT 1
            )
        ''')
        
        # SHIELD tokens table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS shield_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shield_id TEXT UNIQUE NOT NULL,
                security_number TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                crypto_type TEXT NOT NULL,
                crypto_amount REAL NOT NULL,
                guard_amount INTEGER NOT NULL,
                total_value_usd REAL NOT NULL,
                apy_rate REAL NOT NULL,
                mint_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                lock_end_timestamp TIMESTAMP NOT NULL,
                owner_address TEXT NOT NULL,
                pool_id TEXT NOT NULL,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        # Crypto pair transactions table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS crypto_pairs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                crypto_type TEXT NOT NULL,
                crypto_amount REAL NOT NULL,
                crypto_tx_hash TEXT NOT NULL,
                guard_amount INTEGER NOT NULL,
                guard_tx_hash TEXT,
                shield_id TEXT,
                pair_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (shield_id) REFERENCES shield_tokens (shield_id)
            )
        ''')
        
        # Rewards history table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS reward_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                stake_id INTEGER NOT NULL,
                shield_id TEXT,
                amount INTEGER NOT NULL,
                reward_type TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                transaction_hash TEXT,
                FOREIGN KEY (stake_id) REFERENCES user_stakes (id),
                FOREIGN KEY (shield_id) REFERENCES shield_tokens (shield_id)
            )
        ''')
        
        # Pool statistics table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS pool_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pool_id TEXT NOT NULL,
                total_staked INTEGER NOT NULL,
                total_rewards_distributed INTEGER NOT NULL,
                active_stakers INTEGER NOT NULL,
                shields_minted INTEGER DEFAULT 0,
                total_shield_value REAL DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_security_number(self) -> str:
        """Generate unique high-security number for SHIELD token"""
        # Format: SHIELD-YYYY-XXXXXXXX (Year + 8 random chars)
        year = datetime.now().year
        random_part = secrets.token_hex(4).upper()
        return f"SHIELD-{year}-{random_part}"
    
    def calculate_crypto_guard_ratio(self, crypto_type: str, crypto_amount: float) -> int:
        """Calculate required GUARD tokens for crypto pairing"""
        # Simulated crypto prices (in production, use real price feeds)
        crypto_prices = {
            "BTC": 45000.0,
            "ETH": 2800.0,
            "SOL": 95.0,
            "BNB": 320.0,
            "ADA": 0.48,
            "MATIC": 0.85,
            "AVAX": 28.0,
            "LINK": 15.0
        }
        
        guard_price = 0.0523  # Current GUARD price
        
        crypto_value_usd = crypto_amount * crypto_prices.get(crypto_type, 1.0)
        required_guard = int(crypto_value_usd / guard_price)
        
        return required_guard
    
    def mint_shield_token(self, user_id: str, pool_id: str, crypto_type: str, 
                         crypto_amount: float, guard_amount: int, 
                         owner_address: str) -> Dict[str, Any]:
        """Mint a new SHIELD token from crypto+GUARD pairing"""
        
        pool = self.get_pool(pool_id)
        if not pool:
            raise ValueError(f"Pool {pool_id} not found")
        
        # Validate pairing ratio
        required_guard = self.calculate_crypto_guard_ratio(crypto_type, crypto_amount)
        if guard_amount < required_guard:
            raise ValueError(f"Insufficient GUARD tokens. Required: {required_guard}, Provided: {guard_amount}")
        
        # Generate unique identifiers
        shield_id = f"shield_{secrets.token_urlsafe(16)}"
        security_number = self.generate_security_number()
        
        # Calculate total value and create SHIELD token
        crypto_prices = {
            "BTC": 45000.0, "ETH": 2800.0, "SOL": 95.0, "BNB": 320.0,
            "ADA": 0.48, "MATIC": 0.85, "AVAX": 28.0, "LINK": 15.0
        }
        
        crypto_value = crypto_amount * crypto_prices.get(crypto_type, 1.0)
        guard_value = guard_amount * 0.0523
        total_value = crypto_value + guard_value
        
        lock_end = datetime.now() + timedelta(days=pool.lock_period_days)
        
        shield_token = ShieldToken(
            shield_id=shield_id,
            security_number=security_number,
            total_value_usd=total_value,
            crypto_type=crypto_type,
            crypto_amount=crypto_amount,
            guard_amount=guard_amount,
            mint_timestamp=datetime.now(),
            lock_end_timestamp=lock_end,
            apy_rate=pool.effective_apy,
            owner_address=owner_address
        )
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO shield_tokens 
            (shield_id, security_number, user_id, crypto_type, crypto_amount, 
             guard_amount, total_value_usd, apy_rate, lock_end_timestamp, 
             owner_address, pool_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            shield_id, security_number, user_id, crypto_type, crypto_amount,
            guard_amount, total_value, pool.effective_apy, lock_end,
            owner_address, pool_id
        ))
        
        conn.commit()
        conn.close()
        
        # Update pool capacity
        pool.current_staked += guard_amount
        
        return {
            "success": True,
            "shield_token": {
                "shield_id": shield_id,
                "security_number": security_number,
                "total_value_usd": total_value,
                "crypto_type": crypto_type,
                "crypto_amount": crypto_amount,
                "guard_amount": guard_amount,
                "apy_rate": pool.effective_apy,
                "lock_end_date": lock_end.isoformat(),
                "estimated_maturity_value": shield_token.current_value
            },
            "message": f"Successfully minted SHIELD token {security_number}"
        }
    
    def get_pool(self, pool_id: str) -> Optional[StakingPool]:
        """Get staking pool by ID"""
        return self.pools.get(pool_id)
    
    def get_all_pools(self) -> List[Dict[str, Any]]:
        """Get all staking pools with current data"""
        pools_data = []
        
        for pool in self.pools.values():
            pools_data.append({
                "pool_id": pool.pool_id,
                "name": pool.name,
                "description": pool.description,
                "min_stake": pool.min_stake,
                "lock_period_days": pool.lock_period_days,
                "base_apy": pool.base_apy,
                "bonus_apy": pool.bonus_apy,
                "effective_apy": round(pool.effective_apy, 2),
                "max_capacity": pool.max_capacity,
                "current_staked": pool.current_staked,
                "available_capacity": pool.available_capacity,
                "utilization_percentage": round(pool.utilization_percentage, 1),
                "security_level": pool.security_level,
                "estimated_daily_rewards": self._calculate_daily_rewards(pool, 1000),
                "risk_level": self._assess_pool_risk(pool)
            })
        
        return sorted(pools_data, key=lambda x: x["min_stake"])
    
    def calculate_potential_rewards(self, pool_id: str, amount: int, days: int = None) -> Dict[str, Any]:
        """Calculate potential rewards for a stake"""
        pool = self.get_pool(pool_id)
        if not pool:
            raise ValueError(f"Pool {pool_id} not found")
        
        if amount < pool.min_stake:
            raise ValueError(f"Minimum stake for {pool.name} is {pool.min_stake} GUARD")
        
        days = days or pool.lock_period_days
        effective_apy = pool.effective_apy
        
        # Calculate rewards
        daily_rate = effective_apy / 365 / 100
        total_rewards = amount * daily_rate * days
        
        # Bonus calculations
        early_bird_bonus = 0
        if pool.utilization_percentage < 50:
            early_bird_bonus = total_rewards * 0.1  # 10% early bird bonus
        
        loyalty_bonus = 0
        if days >= 365:
            loyalty_bonus = total_rewards * 0.15  # 15% loyalty bonus for 1+ year
        elif days >= 90:
            loyalty_bonus = total_rewards * 0.05  # 5% loyalty bonus for 3+ months
        
        final_rewards = total_rewards + early_bird_bonus + loyalty_bonus
        
        return {
            "base_rewards": round(total_rewards, 2),
            "early_bird_bonus": round(early_bird_bonus, 2),
            "loyalty_bonus": round(loyalty_bonus, 2),
            "total_rewards": round(final_rewards, 2),
            "effective_apy": round(effective_apy, 2),
            "daily_rewards": round(final_rewards / days, 4),
            "final_amount": amount + round(final_rewards, 2),
            "break_even_days": 1,  # Always positive rewards
            "risk_assessment": self._assess_stake_risk(pool, amount)
        }
    
    def _calculate_daily_rewards(self, pool: StakingPool, amount: int) -> float:
        """Calculate daily rewards for given amount"""
        daily_rate = pool.effective_apy / 365 / 100
        return round(amount * daily_rate, 4)
    
    def _assess_pool_risk(self, pool: StakingPool) -> str:
        """Assess risk level of a staking pool"""
        if pool.lock_period_days <= 7:
            return "Low"
        elif pool.lock_period_days <= 30:
            return "Medium"
        elif pool.lock_period_days <= 90:
            return "Medium-High"
        else:
            return "High"
    
    def _assess_stake_risk(self, pool: StakingPool, amount: int) -> Dict[str, Any]:
        """Assess risk factors for a specific stake"""
        risks = []
        risk_score = 0
        
        # Lock period risk
        if pool.lock_period_days > 90:
            risks.append("Long lock period reduces liquidity")
            risk_score += 3
        elif pool.lock_period_days > 30:
            risks.append("Medium lock period")
            risk_score += 2
        else:
            risks.append("Short lock period - low liquidity risk")
            risk_score += 1
        
        # Pool utilization risk
        if pool.utilization_percentage > 90:
            risks.append("Pool near capacity - limited flexibility")
            risk_score += 2
        elif pool.utilization_percentage < 20:
            risks.append("Low pool utilization - network effects may be limited")
            risk_score += 1
        
        # Amount risk
        if amount > pool.max_capacity * 0.1:
            risks.append("Large stake relative to pool size")
            risk_score += 2
        
        # Determine overall risk level
        if risk_score <= 3:
            risk_level = "Low"
        elif risk_score <= 6:
            risk_level = "Medium" 
        elif risk_score <= 9:
            risk_level = "High"
        else:
            risk_level = "Very High"
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risks,
            "mitigation_tips": self._get_risk_mitigation_tips(risk_level)
        }
    
    def _get_risk_mitigation_tips(self, risk_level: str) -> List[str]:
        """Get risk mitigation tips based on risk level"""
        tips = {
            "Low": [
                "Consider staking additional amounts as you become more comfortable",
                "Monitor pool performance and adjust strategy accordingly"
            ],
            "Medium": [
                "Diversify across multiple pools to reduce concentration risk",
                "Consider starting with smaller amounts to test the process",
                "Keep some liquidity outside of staking for emergencies"
            ],
            "High": [
                "Only stake amounts you can afford to lock for the full period",
                "Carefully consider your liquidity needs before committing",
                "Start with smaller test stakes before committing large amounts",
                "Ensure you understand all terms and conditions"
            ],
            "Very High": [
                "Seek financial advice before proceeding with large stakes",
                "Consider alternative investment strategies",
                "Ensure complete understanding of smart contract risks",
                "Only proceed if you can afford total loss"
            ]
        }
        return tips.get(risk_level, [])

# Initialize staking manager
staking_manager = StakingManager()

# Pydantic models
class StakeRequest(BaseModel):
    pool_id: str
    amount: int
    user_id: str

class ShieldMintRequest(BaseModel):
    pool_id: str
    crypto_type: str
    crypto_amount: float
    guard_amount: int
    user_id: str
    owner_address: str

class RewardCalculationRequest(BaseModel):
    pool_id: str
    amount: int
    days: Optional[int] = None

class CryptoPairCalculationRequest(BaseModel):
    crypto_type: str
    crypto_amount: float

# API endpoints
@app.get("/")
async def staking_dashboard():
    """Serve the staking dashboard"""
    return HTMLResponse(content=get_staking_html(), status_code=200)

@app.get("/api/staking/pools")
async def get_staking_pools():
    """Get all available staking pools"""
    return {
        "pools": staking_manager.get_all_pools(),
        "total_pools": len(staking_manager.pools),
        "total_tvl": sum(pool.current_staked for pool in staking_manager.pools.values()),
        "average_apy": sum(pool.effective_apy for pool in staking_manager.pools.values()) / len(staking_manager.pools)
    }

@app.get("/api/staking/pool/{pool_id}")
async def get_pool_details(pool_id: str):
    """Get detailed information about a specific pool"""
    pool = staking_manager.get_pool(pool_id)
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")
    
    return {
        "pool_id": pool.pool_id,
        "name": pool.name,
        "description": pool.description,
        "min_stake": pool.min_stake,
        "lock_period_days": pool.lock_period_days,
        "base_apy": pool.base_apy,
        "bonus_apy": pool.bonus_apy,
        "effective_apy": round(pool.effective_apy, 2),
        "max_capacity": pool.max_capacity,
        "current_staked": pool.current_staked,
        "available_capacity": pool.available_capacity,
        "utilization_percentage": round(pool.utilization_percentage, 1),
        "security_level": pool.security_level,
        "risk_assessment": staking_manager._assess_pool_risk(pool)
    }

@app.post("/api/staking/calculate-rewards")
async def calculate_rewards(request: RewardCalculationRequest):
    """Calculate potential rewards for a staking scenario"""
    try:
        rewards = staking_manager.calculate_potential_rewards(
            request.pool_id, 
            request.amount, 
            request.days
        )
        return rewards
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/staking/stake")
async def create_stake(request: StakeRequest):
    """Create a new stake (simulation - would interact with smart contracts)"""
    
    pool = staking_manager.get_pool(request.pool_id)
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")
    
    if request.amount < pool.min_stake:
        raise HTTPException(
            status_code=400, 
            detail=f"Minimum stake for {pool.name} is {pool.min_stake} GUARD"
        )
    
    if request.amount > pool.available_capacity:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient pool capacity. Available: {pool.available_capacity} GUARD"
        )
    
    # In production, this would:
    # 1. Validate user's token balance
    # 2. Create smart contract transaction
    # 3. Wait for confirmation
    # 4. Update database
    
    # For now, simulate successful staking
    lock_end = datetime.now() + timedelta(days=pool.lock_period_days)
    
    # Simulate database insertion
    conn = sqlite3.connect(staking_manager.db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO user_stakes 
        (user_id, pool_id, amount, lock_end_timestamp, transaction_hash)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        request.user_id,
        request.pool_id,
        request.amount,
        lock_end,
        f"0x{'a' * 64}"  # Simulated tx hash
    ))
    
    stake_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Update pool capacity
    pool.current_staked += request.amount
    
    return {
        "success": True,
        "stake_id": stake_id,
        "message": f"Successfully staked {request.amount} GUARD in {pool.name}",
        "lock_end_date": lock_end.isoformat(),
        "estimated_rewards": staking_manager.calculate_potential_rewards(
            request.pool_id, request.amount
        )["total_rewards"]
    }

@app.get("/api/staking/user/{user_id}/stakes")
async def get_user_stakes(user_id: str):
    """Get all stakes for a user"""
    
    conn = sqlite3.connect(staking_manager.db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM user_stakes 
        WHERE user_id = ? AND status = 'active'
        ORDER BY stake_timestamp DESC
    ''', (user_id,))
    
    stakes = []
    for row in cursor.fetchall():
        stake_id, user_id, pool_id, amount, stake_time, lock_end, rewards_claimed, last_reward, status, tx_hash, chain_id = row
        
        pool = staking_manager.get_pool(pool_id)
        if pool:
            # Calculate current rewards
            days_staked = (datetime.now() - datetime.fromisoformat(stake_time)).days
            current_rewards = staking_manager._calculate_daily_rewards(pool, amount) * days_staked
            
            stakes.append({
                "stake_id": stake_id,
                "pool_id": pool_id,
                "pool_name": pool.name,
                "amount": amount,
                "stake_date": stake_time,
                "lock_end_date": lock_end,
                "days_remaining": max(0, (datetime.fromisoformat(lock_end) - datetime.now()).days),
                "current_rewards": round(current_rewards, 2),
                "rewards_claimed": rewards_claimed,
                "apy": pool.effective_apy,
                "status": status,
                "can_unstake": datetime.now() >= datetime.fromisoformat(lock_end)
            })
    
    conn.close()
    
    return {
        "stakes": stakes,
        "total_staked": sum(stake["amount"] for stake in stakes),
        "total_rewards": sum(stake["current_rewards"] for stake in stakes),
        "active_pools": len(set(stake["pool_id"] for stake in stakes))
    }

@app.post("/api/staking/calculate-crypto-pair")
async def calculate_crypto_pair_requirement(request: CryptoPairCalculationRequest):
    """Calculate GUARD tokens required for crypto pairing"""
    try:
        required_guard = staking_manager.calculate_crypto_guard_ratio(
            request.crypto_type, 
            request.crypto_amount
        )
        
        # Calculate potential SHIELD value
        crypto_prices = {
            "BTC": 45000.0, "ETH": 2800.0, "SOL": 95.0, "BNB": 320.0,
            "ADA": 0.48, "MATIC": 0.85, "AVAX": 28.0, "LINK": 15.0
        }
        
        crypto_value = request.crypto_amount * crypto_prices.get(request.crypto_type, 1.0)
        guard_value = required_guard * 0.0523
        total_shield_value = crypto_value + guard_value
        
        return {
            "crypto_type": request.crypto_type,
            "crypto_amount": request.crypto_amount,
            "crypto_value_usd": round(crypto_value, 2),
            "required_guard_tokens": required_guard,
            "guard_value_usd": round(guard_value, 2),
            "total_shield_value_usd": round(total_shield_value, 2),
            "recommended_pools": [
                {"pool_id": "shield_btc_guard", "apy": "20.0%"} if request.crypto_type == "BTC" else
                {"pool_id": "shield_eth_guard", "apy": "25.0%"} if request.crypto_type == "ETH" else
                {"pool_id": "shield_sol_guard", "apy": "30.0%"} if request.crypto_type == "SOL" else
                {"pool_id": "shield_multi_guard", "apy": "16.0%"}
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/staking/mint-shield")
async def mint_shield_token(request: ShieldMintRequest):
    """Mint a new SHIELD token from crypto+GUARD pairing"""
    try:
        result = staking_manager.mint_shield_token(
            user_id=request.user_id,
            pool_id=request.pool_id,
            crypto_type=request.crypto_type,
            crypto_amount=request.crypto_amount,
            guard_amount=request.guard_amount,
            owner_address=request.owner_address
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Minting failed: {str(e)}")

@app.get("/api/staking/user/{user_id}/shields")
async def get_user_shield_tokens(user_id: str):
    """Get all SHIELD tokens owned by a user"""
    
    conn = sqlite3.connect(staking_manager.db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM shield_tokens 
        WHERE user_id = ? AND status = 'active'
        ORDER BY mint_timestamp DESC
    ''', (user_id,))
    
    shields = []
    for row in cursor.fetchall():
        (id, shield_id, security_number, user_id, crypto_type, crypto_amount,
         guard_amount, total_value_usd, apy_rate, mint_timestamp, 
         lock_end_timestamp, owner_address, pool_id, status) = row
        
        # Calculate current value with rewards
        mint_time = datetime.fromisoformat(mint_timestamp)
        lock_end = datetime.fromisoformat(lock_end_timestamp)
        days_held = (datetime.now() - mint_time).days
        daily_rate = apy_rate / 365 / 100
        current_value = total_value_usd * (1 + daily_rate * days_held)
        
        shields.append({
            "shield_id": shield_id,
            "security_number": security_number,
            "crypto_type": crypto_type,
            "crypto_amount": crypto_amount,
            "guard_amount": guard_amount,
            "initial_value_usd": total_value_usd,
            "current_value_usd": round(current_value, 2),
            "apy_rate": apy_rate,
            "mint_date": mint_timestamp,
            "lock_end_date": lock_end_timestamp,
            "days_remaining": max(0, (lock_end - datetime.now()).days),
            "is_mature": datetime.now() >= lock_end,
            "total_rewards_earned": round(current_value - total_value_usd, 2),
            "pool_id": pool_id,
            "status": status
        })
    
    conn.close()
    
    return {
        "shield_tokens": shields,
        "total_shields": len(shields),
        "total_initial_value": sum(shield["initial_value_usd"] for shield in shields),
        "total_current_value": sum(shield["current_value_usd"] for shield in shields),
        "total_rewards_earned": sum(shield["total_rewards_earned"] for shield in shields)
    }

@app.get("/api/staking/supported-cryptos")
async def get_supported_cryptocurrencies():
    """Get list of supported cryptocurrencies for pairing"""
    
    return {
        "supported_cryptos": [
            {
                "symbol": "BTC",
                "name": "Bitcoin",
                "current_price_usd": 45000.0,
                "min_amount": 0.001,
                "recommended_pool": "shield_btc_guard",
                "security_level": "Ultra"
            },
            {
                "symbol": "ETH", 
                "name": "Ethereum",
                "current_price_usd": 2800.0,
                "min_amount": 0.01,
                "recommended_pool": "shield_eth_guard",
                "security_level": "Premium"
            },
            {
                "symbol": "SOL",
                "name": "Solana", 
                "current_price_usd": 95.0,
                "min_amount": 1.0,
                "recommended_pool": "shield_sol_guard",
                "security_level": "Advanced"
            },
            {
                "symbol": "BNB",
                "name": "Binance Coin",
                "current_price_usd": 320.0,
                "min_amount": 0.1,
                "recommended_pool": "shield_multi_guard",
                "security_level": "Standard"
            },
            {
                "symbol": "ADA",
                "name": "Cardano",
                "current_price_usd": 0.48,
                "min_amount": 100.0,
                "recommended_pool": "shield_multi_guard",
                "security_level": "Standard"
            }
        ],
        "pairing_info": {
            "formula": "Crypto + GUARD = SHIELD",
            "security_features": [
                "Unique numbered SHIELD tokens",
                "High-security identification system",
                "Transparent reward calculation",
                "Multi-crypto diversification support"
            ],
            "benefits": [
                "Earn rewards on both crypto and GUARD tokens",
                "Protection through diversified pairing",
                "Transferable SHIELD tokens",
                "Competitive APY rates"
            ]
        }
    }

def get_staking_html():
    """Generate staking dashboard HTML"""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GuardianShield Staking Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0a0e1a 0%, #1a2332 50%, #2d3e50 100%);
            color: #e0e6ed;
            min-height: 100vh;
            line-height: 1.6;
        }
        
        .header {
            background: rgba(16, 24, 32, 0.95);
            padding: 1.5rem 2rem;
            border-bottom: 3px solid #27ae60;
            backdrop-filter: blur(15px);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .header-content {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .logo h1 {
            background: linear-gradient(45deg, #27ae60, #2ecc71);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2rem;
            font-weight: 700;
        }
        
        .stake-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(45deg, #27ae60, #2ecc71);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.5rem;
        }
        
        .main-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .dashboard-title {
            text-align: center;
            margin-bottom: 3rem;
        }
        
        .dashboard-title h2 {
            font-size: 2.5rem;
            background: linear-gradient(45deg, #27ae60, #2ecc71);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem;
        }
        
        .subtitle {
            color: #bdc3c7;
            font-size: 1.2rem;
        }
        
        .stats-overview {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 3rem;
        }
        
        .stat-card {
            background: rgba(26, 35, 50, 0.8);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid rgba(39, 174, 96, 0.3);
            text-align: center;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: #27ae60;
            margin-bottom: 0.5rem;
        }
        
        .stat-label {
            color: #95a5a6;
            font-size: 0.9rem;
            text-transform: uppercase;
        }
        
        .pools-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 2rem;
            margin-bottom: 3rem;
        }
        
        .calculator-section {
            background: linear-gradient(135deg, #1e3c72, #2a5298);
            padding: 2rem;
            border-radius: 15px;
            border: 2px solid #3498db;
            margin-top: 3rem;
        }
        
        .calculator-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            margin-top: 2rem;
        }
        
        .calculator-form {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }
        
        .calculator-results {
            background: linear-gradient(135deg, #2c3e50, #34495e);
            padding: 1.5rem;
            border-radius: 10px;
            border: 1px solid #34495e;
            min-height: 300px;
        }
        
        .form-group {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .form-label {
            color: #ecf0f1;
            font-weight: 600;
            font-size: 0.9rem;
        }
        
        .form-select, .form-input {
            padding: 12px 15px;
            border: 1px solid #34495e;
            border-radius: 8px;
            background: rgba(52, 73, 94, 0.8);
            color: #ecf0f1;
            font-size: 1rem;
        }
        
        .form-select:focus, .form-input:focus {
            outline: none;
            border-color: #3498db;
            box-shadow: 0 0 10px rgba(52, 152, 219, 0.3);
        }
        
        .shield-calculation {
            background: linear-gradient(135deg, #27ae60, #2ecc71);
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
            text-align: center;
        }
        
        .shield-number {
            background: linear-gradient(45deg, #f39c12, #e67e22);
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            text-align: center;
            font-size: 1.2rem;
            font-weight: bold;
        }
        
        .security-level {
            background: linear-gradient(45deg, #9b59b6, #8e44ad);
            padding: 0.8rem;
            border-radius: 6px;
            text-align: center;
            color: white;
            font-weight: 600;
        }
        
        .pool-card {
            background: rgba(26, 35, 50, 0.8);
            border-radius: 16px;
            padding: 2rem;
            border: 1px solid rgba(39, 174, 96, 0.3);
            backdrop-filter: blur(10px);
            position: relative;
            overflow: hidden;
        }
        
        .pool-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(45deg, #27ae60, #2ecc71);
        }
        
        .pool-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 1rem;
        }
        
        .pool-title {
            color: #27ae60;
            font-size: 1.3rem;
            font-weight: 600;
        }
        
        .security-badge {
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .pool-description {
            color: #bdc3c7;
            margin-bottom: 1.5rem;
            line-height: 1.5;
        }
        
        .pool-metrics {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        
        .metric {
            text-align: center;
        }
        
        .metric-value {
            font-size: 1.4rem;
            font-weight: 700;
            color: #27ae60;
        }
        
        .metric-label {
            font-size: 0.8rem;
            color: #95a5a6;
            text-transform: uppercase;
        }
        
        .pool-progress {
            margin-bottom: 1.5rem;
        }
        
        .progress-bar {
            background: rgba(44, 62, 80, 0.8);
            border-radius: 10px;
            height: 8px;
            overflow: hidden;
            margin-bottom: 0.5rem;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(45deg, #27ae60, #2ecc71);
            border-radius: 10px;
            transition: width 0.3s ease;
        }
        
        .progress-label {
            display: flex;
            justify-content: space-between;
            font-size: 0.85rem;
            color: #95a5a6;
        }
        
        .pool-details {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin-bottom: 1.5rem;
            padding: 1rem;
            background: rgba(44, 62, 80, 0.3);
            border-radius: 8px;
        }
        
        .detail-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .detail-label {
            font-size: 0.9rem;
            color: #95a5a6;
        }
        
        .detail-value {
            font-weight: 600;
            color: #e0e6ed;
        }
        
        .stake-button {
            width: 100%;
            padding: 1rem;
            background: linear-gradient(45deg, #27ae60, #2ecc71);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .stake-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(39, 174, 96, 0.4);
        }
        
        .stake-button:disabled {
            background: #95a5a6;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .calculator-section {
            background: rgba(16, 24, 32, 0.9);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 3rem;
        }
        
        .calculator-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            margin-top: 2rem;
        }
        
        .calculator-form {
            background: rgba(44, 62, 80, 0.6);
            border-radius: 12px;
            padding: 1.5rem;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        .form-label {
            display: block;
            color: #e0e6ed;
            margin-bottom: 0.5rem;
            font-weight: 600;
        }
        
        .form-input, .form-select {
            width: 100%;
            padding: 0.75rem;
            background: rgba(26, 35, 50, 0.8);
            border: 1px solid rgba(52, 152, 219, 0.3);
            border-radius: 6px;
            color: #e0e6ed;
            font-size: 1rem;
        }
        
        .form-input:focus, .form-select:focus {
            outline: none;
            border-color: #27ae60;
            box-shadow: 0 0 0 2px rgba(39, 174, 96, 0.2);
        }
        
        .calculator-results {
            background: rgba(44, 62, 80, 0.6);
            border-radius: 12px;
            padding: 1.5rem;
        }
        
        .result-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 1rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid rgba(52, 152, 219, 0.1);
        }
        
        .result-item:last-child {
            border-bottom: none;
            margin-bottom: 0;
        }
        
        .result-label {
            color: #bdc3c7;
        }
        
        .result-value {
            font-weight: 700;
            color: #27ae60;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(39, 174, 96, 0.3);
            border-radius: 50%;
            border-top-color: #27ae60;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        @media (max-width: 768px) {
            .main-content { padding: 1rem; }
            .pools-grid { grid-template-columns: 1fr; }
            .calculator-grid { grid-template-columns: 1fr; }
            .pool-metrics { grid-template-columns: 1fr; }
            .pool-details { grid-template-columns: 1fr; }
            .calculator-section { padding: 1.5rem; }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <div class="logo">
                <div class="stake-icon">%</div>
                <h1>Staking Dashboard</h1>
            </div>
            <div style="color: #27ae60; font-weight: 600;">
                Earn rewards while securing the ecosystem
            </div>
        </div>
    </div>
    
    <div class="main-content">
        <div class="dashboard-title">
            <h2>SHIELD Token Minting Platform</h2>
            <p class="subtitle">Pair your crypto with GUARD tokens to mint high-security numbered SHIELD tokens</p>
            <div style="margin-top: 1rem; padding: 1rem; background: rgba(39, 174, 96, 0.1); border-radius: 8px; border-left: 4px solid #27ae60;">
                <strong style="color: #27ae60;">Revolutionary Formula: Crypto + GUARD = SHIELD</strong><br>
                <span style="color: #bdc3c7;">Secure your assets while earning competitive rewards through our innovative pairing system</span>
            </div>
        </div>
        
        <div class="stats-overview">
            <div class="stat-card">
                <div class="stat-value" id="totalTvl">
                    <span class="loading"></span>
                </div>
                <div class="stat-label">Total Value Locked</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-value" id="avgApy">
                    <span class="loading"></span>
                </div>
                <div class="stat-label">Average APY</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-value" id="totalPools">
                    <span class="loading"></span>
                </div>
                <div class="stat-label">Active Pools</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-value" id="totalStakers">2,847</div>
                <div class="stat-label">Total Stakers</div>
            </div>
        </div>
        
        <div class="pools-grid" id="poolsGrid">
            <!-- Pools will be populated by JavaScript -->
        </div>
        
        <div class="calculator-section">
            <h3 style="color: #27ae60; font-size: 1.8rem; margin-bottom: 1rem; text-align: center;">
                🏭 SHIELD Token Minting Factory
            </h3>
            <p style="text-align: center; color: #bdc3c7; margin-bottom: 2rem;">
                Pair your cryptocurrency with GUARD tokens to mint unique numbered SHIELD tokens
            </p>
            
            <div class="calculator-grid">
                <div class="calculator-form">
                    <div class="form-group">
                        <label class="form-label">Select Cryptocurrency</label>
                        <select class="form-select" id="cryptoType">
                            <option value="">Choose cryptocurrency to pair...</option>
                            <option value="BTC">Bitcoin (BTC) - Ultra Security</option>
                            <option value="ETH">Ethereum (ETH) - Premium Security</option>
                            <option value="SOL">Solana (SOL) - Advanced Security</option>
                            <option value="BNB">Binance Coin (BNB) - Standard</option>
                            <option value="ADA">Cardano (ADA) - Standard</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Crypto Amount</label>
                        <input type="number" class="form-input" id="cryptoAmount" placeholder="Enter crypto amount" step="0.001">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Required GUARD Tokens</label>
                        <input type="number" class="form-input" id="requiredGuard" placeholder="Will be calculated automatically" readonly>
                    </div>
                    
                    <button onclick="calculateShieldMinting()" class="stake-button">
                        Calculate SHIELD Value
                    </button>
                    
                    <button onclick="mintShieldToken()" class="stake-button" style="margin-top: 1rem; background: linear-gradient(45deg, #9b59b6, #8e44ad);">
                        🏭 Mint SHIELD Token
                    </button>
                </div>
                
                <div class="calculator-results" id="shieldResults">
                    <div style="text-align: center; color: #95a5a6; margin-top: 2rem;">
                        Select crypto and amount to see SHIELD minting details
                    </div>
                </div>
            </div>
        </div>
        
        <div class="calculator-section">
            <h3 style="color: #27ae60; font-size: 1.8rem; margin-bottom: 1rem; text-align: center;">
                Staking Rewards Calculator
            </h3>
            <p style="text-align: center; color: #bdc3c7; margin-bottom: 2rem;">
                Calculate your potential earnings before staking
            </p>
            
            <div class="calculator-grid">
                <div class="calculator-form">
                    <div class="form-group">
                        <label class="form-label">Select Pool</label>
                        <select class="form-select" id="calcPool">
                            <option value="">Choose a staking pool...</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Stake Amount (GUARD)</label>
                        <input type="number" class="form-input" id="calcAmount" placeholder="Enter amount to stake" min="1">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Custom Duration (days)</label>
                        <input type="number" class="form-input" id="calcDays" placeholder="Leave empty for pool default">
                    </div>
                    
                    <button onclick="calculateRewards()" class="stake-button">
                        Calculate Rewards
                    </button>
                </div>
                
                <div class="calculator-results" id="calculatorResults">
                    <div style="text-align: center; color: #95a5a6; margin-top: 2rem;">
                        Enter staking details to see potential rewards
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let poolsData = null;
        
        async function loadStakingData() {
            try {
                const response = await fetch('/api/staking/pools');
                const data = await response.json();
                poolsData = data;
                
                updateOverviewStats(data);
                renderPools(data.pools);
                populateCalculatorPools(data.pools);
                
            } catch (error) {
                console.error('Error loading staking data:', error);
            }
        }
        
        function updateOverviewStats(data) {
            document.getElementById('totalTvl').textContent = 
                (data.total_tvl / 1000000).toFixed(1) + 'M GUARD';
            
            document.getElementById('avgApy').textContent = 
                data.average_apy.toFixed(1) + '%';
            
            document.getElementById('totalPools').textContent = data.total_pools;
        }
        
        function renderPools(pools) {
            const poolsGrid = document.getElementById('poolsGrid');
            
            poolsGrid.innerHTML = pools.map(pool => `
                <div class="pool-card">
                    <div class="pool-header">
                        <h3 class="pool-title">${pool.name}</h3>
                        <div class="security-badge">${pool.security_level}</div>
                    </div>
                    
                    <p class="pool-description">${pool.description}</p>
                    
                    <div class="pool-metrics">
                        <div class="metric">
                            <div class="metric-value">${pool.effective_apy}%</div>
                            <div class="metric-label">Effective APY</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">${pool.lock_period_days}d</div>
                            <div class="metric-label">Lock Period</div>
                        </div>
                    </div>
                    
                    <div class="pool-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${pool.utilization_percentage}%"></div>
                        </div>
                        <div class="progress-label">
                            <span>Utilization</span>
                            <span>${pool.utilization_percentage}%</span>
                        </div>
                    </div>
                    
                    <div class="pool-details">
                        <div class="detail-item">
                            <span class="detail-label">Min Stake:</span>
                            <span class="detail-value">${pool.min_stake.toLocaleString()} GUARD</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Available:</span>
                            <span class="detail-value">${(pool.available_capacity / 1000000).toFixed(1)}M GUARD</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Risk Level:</span>
                            <span class="detail-value">${pool.risk_level}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Daily Rewards:</span>
                            <span class="detail-value">${pool.estimated_daily_rewards} per 1K</span>
                        </div>
                    </div>
                    
                    <button class="stake-button" onclick="openStakeModal('${pool.pool_id}')" 
                            ${pool.available_capacity === 0 ? 'disabled' : ''}>
                        ${pool.available_capacity === 0 ? 'Pool Full' : 'Stake Now'}
                    </button>
                </div>
            `).join('');
        }
        
        function populateCalculatorPools(pools) {
            const select = document.getElementById('calcPool');
            select.innerHTML = '<option value="">Choose a staking pool...</option>' +
                pools.map(pool => 
                    `<option value="${pool.pool_id}">${pool.name} (${pool.effective_apy}% APY)</option>`
                ).join('');
        }
        
        async function calculateRewards() {
            const poolId = document.getElementById('calcPool').value;
            const amount = parseInt(document.getElementById('calcAmount').value);
            const days = document.getElementById('calcDays').value;
            
            if (!poolId || !amount) {
                alert('Please select a pool and enter an amount');
                return;
            }
            
            try {
                const response = await fetch('/api/staking/calculate-rewards', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        pool_id: poolId,
                        amount: amount,
                        days: days ? parseInt(days) : null
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    displayCalculatorResults(data);
                } else {
                    alert(data.detail || 'Calculation failed');
                }
                
            } catch (error) {
                console.error('Calculation error:', error);
                alert('Failed to calculate rewards');
            }
        }
        
        function displayCalculatorResults(results) {
            const resultsDiv = document.getElementById('calculatorResults');
            
            resultsDiv.innerHTML = `
                <div class="result-item">
                    <span class="result-label">Base Rewards:</span>
                    <span class="result-value">${results.base_rewards} GUARD</span>
                </div>
                
                <div class="result-item">
                    <span class="result-label">Bonuses:</span>
                    <span class="result-value">+${(results.early_bird_bonus + results.loyalty_bonus).toFixed(2)} GUARD</span>
                </div>
                
                <div class="result-item">
                    <span class="result-label">Total Rewards:</span>
                    <span class="result-value">${results.total_rewards} GUARD</span>
                </div>
                
                <div class="result-item">
                    <span class="result-label">Final Amount:</span>
                    <span class="result-value">${results.final_amount} GUARD</span>
                </div>
                
                <div class="result-item">
                    <span class="result-label">Daily Rewards:</span>
                    <span class="result-value">${results.daily_rewards} GUARD</span>
                </div>
                
                <div class="result-item">
                    <span class="result-label">Effective APY:</span>
                    <span class="result-value">${results.effective_apy}%</span>
                </div>
                
                <div style="margin-top: 1rem; padding: 1rem; background: rgba(39, 174, 96, 0.1); border-radius: 6px; border-left: 3px solid #27ae60;">
                    <strong style="color: #27ae60;">Risk Assessment: ${results.risk_assessment.risk_level}</strong><br>
                    <span style="color: #bdc3c7; font-size: 0.9rem;">
                        ${results.risk_assessment.risk_factors.slice(0, 2).join('. ')}.
                    </span>
                </div>
            `;
        }
        
        function openStakeModal(poolId) {
            // In a real application, this would open a staking modal
            // For now, show a simple alert
            alert(`Staking interface for ${poolId} would open here. This requires wallet connection and smart contract integration.`);
        }
        
        // SHIELD Token Minting Functions
        const cryptoPrices = {
            'BTC': 45000,
            'ETH': 3200,
            'SOL': 85,
            'BNB': 320,
            'ADA': 0.65
        };
        
        const pairingRatios = {
            'BTC': 1.0,    // 1:1 ratio (premium)
            'ETH': 1.2,    // 1:1.2 ratio
            'SOL': 1.5,    // 1:1.5 ratio
            'BNB': 1.8,    // 1:1.8 ratio
            'ADA': 2.0     // 1:2.0 ratio
        };
        
        const securityLevels = {
            'BTC': 'Ultra Security',
            'ETH': 'Premium Security',
            'SOL': 'Advanced Security',
            'BNB': 'Standard Security',
            'ADA': 'Standard Security'
        };
        
        async function calculateShieldMinting() {
            const cryptoType = document.getElementById('cryptoType').value;
            const cryptoAmount = parseFloat(document.getElementById('cryptoAmount').value);
            
            if (!cryptoType || !cryptoAmount) {
                document.getElementById('shieldResults').innerHTML = 
                    '<div style="text-align: center; color: #e74c3c;">Please select crypto and enter amount</div>';
                return;
            }
            
            const cryptoPrice = cryptoPrices[cryptoType];
            const guardPrice = 0.85; // Current GUARD token price
            const ratio = pairingRatios[cryptoType];
            
            const cryptoValue = cryptoAmount * cryptoPrice;
            const requiredGuard = (cryptoValue / guardPrice) * ratio;
            
            document.getElementById('requiredGuard').value = requiredGuard.toFixed(2);
            
            const securityLevel = securityLevels[cryptoType];
            const shieldNumber = Math.floor(Math.random() * 900000) + 100000; // 6-digit security number
            const lockPeriod = cryptoType === 'BTC' ? 180 : cryptoType === 'ETH' ? 120 : 90;
            const apy = cryptoType === 'BTC' ? 15 : cryptoType === 'ETH' ? 12 : 10;
            
            const resultsHTML = `
                <div class="shield-calculation">
                    <h4 style="color: white; margin-bottom: 1rem;">🏭 SHIELD Token Preview</h4>
                    <div class="shield-number">
                        SHIELD #${shieldNumber}
                    </div>
                    <div class="security-level">
                        ${securityLevel}
                    </div>
                </div>
                
                <div style="background: rgba(52, 73, 94, 0.8); padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                    <div style="display: flex; justify-content: space-between; margin: 0.5rem 0;">
                        <span>Crypto Value:</span>
                        <span style="color: #27ae60;">$${cryptoValue.toLocaleString()}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin: 0.5rem 0;">
                        <span>GUARD Required:</span>
                        <span style="color: #f39c12;">${requiredGuard.toFixed(0)} GUARD</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin: 0.5rem 0;">
                        <span>Lock Period:</span>
                        <span>${lockPeriod} days</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin: 0.5rem 0;">
                        <span>APY Rate:</span>
                        <span style="color: #9b59b6;">${apy}%</span>
                    </div>
                </div>
                
                <div style="text-align: center; color: #3498db; font-size: 0.9rem; margin-top: 1rem;">
                    Total Value: $${(cryptoValue + (requiredGuard * guardPrice)).toLocaleString()}
                </div>
            `;
            
            document.getElementById('shieldResults').innerHTML = resultsHTML;
        }
        
        async function mintShieldToken() {
            const cryptoType = document.getElementById('cryptoType').value;
            const cryptoAmount = parseFloat(document.getElementById('cryptoAmount').value);
            const requiredGuard = parseFloat(document.getElementById('requiredGuard').value);
            
            if (!cryptoType || !cryptoAmount || !requiredGuard) {
                alert('Please calculate SHIELD value first');
                return;
            }
            
            try {
                const response = await fetch('/api/staking/mint-shield', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        crypto_type: cryptoType,
                        crypto_amount: cryptoAmount,
                        guard_amount: requiredGuard
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert(`SHIELD Token #${result.shield_number} minted successfully!`);
                    loadStakingData(); // Refresh the dashboard
                } else {
                    alert('Error minting SHIELD token: ' + result.error);
                }
            } catch (error) {
                console.error('Minting error:', error);
                alert('Error connecting to server');
            }
        }
        
        // Initialize dashboard
        loadStakingData();
        
        // Auto-refresh data every 60 seconds
        setInterval(loadStakingData, 60000);
    </script>
</body>
</html>
    '''

if __name__ == "__main__":
    import uvicorn
    
    print("💰 Starting GuardianShield Staking Dashboard...")
    print("🚀 Dashboard available at: http://localhost:8006")
    print("📈 API documentation at: http://localhost:8006/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0", 
        port=8006,
        log_level="info"
    )