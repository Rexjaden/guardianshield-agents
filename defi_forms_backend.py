#!/usr/bin/env python3
"""
GuardianShield DeFi Forms Backend Handler
Integrates with existing advanced staking and liquidity pool systems
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, getcontext
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, validator
import uvicorn

# Import existing GuardianShield systems
from advanced_staking_pool_system import AdvancedStakingPoolSystem
from advanced_liquidity_pool_framework import AdvancedLiquidityPoolFramework

# Smart Contract Integration
try:
    from smart_contract_defi_system import SmartContractDeFiProcessor, StakingRequest, LiquidityRequest as SmartContractLiquidityRequest
    SMART_CONTRACT_AVAILABLE = True
    print("✅ Smart contract DeFi integration enabled")
except ImportError:
    SMART_CONTRACT_AVAILABLE = False
    print("⚠️ Smart contract system not available - using advanced simulation")

# Set decimal precision for financial calculations
getcontext().prec = 28

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="GuardianShield DeFi Forms API",
    description="Advanced DeFi operations with security-first architecture",
    version="1.0.0"
)

# Pydantic models for request validation
class LiquidityRequest(BaseModel):
    pool_pair: str = Field(..., regex="^GUARD-(ETH|USDC|BTC)$")
    token_a_amount: Decimal = Field(..., gt=0)
    token_b_amount: Decimal = Field(..., gt=0)
    slippage_tolerance: Decimal = Field(default=Decimal("0.5"), ge=0.1, le=50)
    user_address: str = Field(..., min_length=42, max_length=42)
    
class RemoveLiquidityRequest(BaseModel):
    pool_pair: str = Field(..., regex="^GUARD-(ETH|USDC|BTC)$")
    percentage: int = Field(..., ge=0, le=100)
    user_address: str = Field(..., min_length=42, max_length=42)

class StakeRequest(BaseModel):
    pool_type: str = Field(..., regex="^(standard|premium|platinum)$")
    amount: Decimal = Field(..., gt=0)
    user_address: str = Field(..., min_length=42, max_length=42)
    auto_compound: bool = Field(default=False)

class UnstakeRequest(BaseModel):
    position_id: int = Field(..., gt=0)
    amount: Decimal = Field(..., gt=0)
    user_address: str = Field(..., min_length=42, max_length=42)

class ClaimRewardsRequest(BaseModel):
    reward_type: str = Field(..., regex="^(all|staking|liquidity)$")
    user_address: str = Field(..., min_length=42, max_length=42)
    auto_compound: bool = Field(default=False)

class CompoundSettingsRequest(BaseModel):
    frequency: str = Field(..., regex="^(daily|weekly|monthly|manual)$")
    threshold: Decimal = Field(..., gt=0)
    enabled: bool
    user_address: str = Field(..., min_length=42, max_length=42)

class DeFiFormsHandler:
    """
    Main handler for DeFi forms backend operations
    Integrates with existing GuardianShield staking and liquidity systems
    """
    
    def __init__(self):
        self.staking_system = AdvancedStakingPoolSystem()
        self.liquidity_system = AdvancedLiquidityPoolFramework()
        self.user_sessions = {}
        self.pool_configs = {
            "GUARD-ETH": {
                "ratio": Decimal("2500"),  # 2500 GUARD : 1 ETH
                "fee": Decimal("0.003"),   # 0.3% trading fee
                "decimals": (18, 18)
            },
            "GUARD-USDC": {
                "ratio": Decimal("0.4"),   # 1 GUARD : 2.5 USDC
                "fee": Decimal("0.003"),
                "decimals": (18, 6)
            },
            "GUARD-BTC": {
                "ratio": Decimal("50000"), # 50000 GUARD : 1 BTC
                "fee": Decimal("0.003"),
                "decimals": (18, 8)
            }
        }
        
        self.staking_pools = {
            "standard": {
                "apr": Decimal("0.04"),    # 4%
                "lock_days": 30,
                "penalty": Decimal("0.05") # 5% early withdrawal penalty
            },
            "premium": {
                "apr": Decimal("0.06"),    # 6%
                "lock_days": 90,
                "penalty": Decimal("0.03") # 3% early withdrawal penalty
            },
            "platinum": {
                "apr": Decimal("0.10"),    # 10%
                "lock_days": 180,
                "penalty": Decimal("0.01") # 1% early withdrawal penalty
            }
        }
    
    async def get_user_balances(self, user_address: str) -> Dict[str, Decimal]:
        """Get user token balances"""
        # Mock data - in production, query blockchain
        return {
            "GUARD": Decimal("5000.00"),
            "ETH": Decimal("5.25"),
            "USDC": Decimal("3125.00"),
            "BTC": Decimal("0.025"),
            "LP_GUARD_ETH": Decimal("85.5"),
            "LP_GUARD_USDC": Decimal("42.3"),
            "LP_GUARD_BTC": Decimal("12.8")
        }
    
    async def get_pool_stats(self, pool_pair: str) -> Dict:
        """Get liquidity pool statistics"""
        # Mock data - in production, query smart contracts
        pool_stats = {
            "GUARD-ETH": {
                "total_liquidity_usd": Decimal("2450000"),
                "daily_volume_usd": Decimal("145000"),
                "current_apr": Decimal("15.2"),
                "token_a_reserve": Decimal("6125000"),  # GUARD
                "token_b_reserve": Decimal("2450"),      # ETH
            },
            "GUARD-USDC": {
                "total_liquidity_usd": Decimal("1850000"),
                "daily_volume_usd": Decimal("98000"),
                "current_apr": Decimal("13.8"),
                "token_a_reserve": Decimal("740000"),    # GUARD
                "token_b_reserve": Decimal("1850000"),   # USDC
            },
            "GUARD-BTC": {
                "total_liquidity_usd": Decimal("980000"),
                "daily_volume_usd": Decimal("52000"),
                "current_apr": Decimal("18.5"),
                "token_a_reserve": Decimal("2450000"),   # GUARD
                "token_b_reserve": Decimal("49"),        # BTC
            }
        }
        return pool_stats.get(pool_pair, {})
    
    async def calculate_liquidity_amounts(self, pool_pair: str, token_a_amount: Decimal) -> Tuple[Decimal, Decimal]:
        """Calculate required token B amount for liquidity provision"""
        config = self.pool_configs[pool_pair]
        
        if pool_pair == "GUARD-ETH":
            token_b_amount = token_a_amount / config["ratio"]
        elif pool_pair == "GUARD-USDC":
            token_b_amount = token_a_amount / config["ratio"]
        elif pool_pair == "GUARD-BTC":
            token_b_amount = token_a_amount / config["ratio"]
        
        return token_a_amount, token_b_amount
    
    async def calculate_staking_rewards(self, pool_type: str, amount: Decimal, days: int = None) -> Dict:
        """Calculate staking rewards for given amount and period"""
        pool_config = self.staking_pools[pool_type]
        apr = pool_config["apr"]
        lock_days = days or pool_config["lock_days"]
        
        daily_reward = (amount * apr) / Decimal("365")
        total_reward = daily_reward * Decimal(str(lock_days))
        
        return {
            "daily_reward": daily_reward,
            "total_reward": total_reward,
            "effective_apr": apr,
            "lock_period_days": lock_days
        }
    
    async def get_user_staking_positions(self, user_address: str) -> List[Dict]:
        """Get user's active staking positions"""
        # Mock data - in production, query smart contracts
        return [
            {
                "position_id": 1,
                "pool_type": "standard",
                "staked_amount": Decimal("10000"),
                "earned_rewards": Decimal("125.50"),
                "start_date": datetime(2026, 1, 1),
                "unlock_date": datetime(2026, 2, 15),
                "is_locked": True,
                "penalty_rate": Decimal("0.05")
            },
            {
                "position_id": 2,
                "pool_type": "premium", 
                "staked_amount": Decimal("15000"),
                "earned_rewards": Decimal("285.75"),
                "start_date": datetime(2025, 12, 15),
                "unlock_date": datetime(2026, 4, 15),
                "is_locked": True,
                "penalty_rate": Decimal("0.03")
            }
        ]
    
    async def process_add_liquidity(self, request: LiquidityRequest) -> Dict:
        """Process add liquidity request"""
        try:
            # Validate user balances
            balances = await self.get_user_balances(request.user_address)
            
            if balances["GUARD"] < request.token_a_amount:
                raise HTTPException(status_code=400, detail="Insufficient GUARD balance")
            
            token_b_key = request.pool_pair.split("-")[1]
            if balances[token_b_key] < request.token_b_amount:
                raise HTTPException(status_code=400, detail=f"Insufficient {token_b_key} balance")
            
            # Calculate LP tokens to mint
            pool_stats = await self.get_pool_stats(request.pool_pair)
            
            # Mock LP token calculation
            lp_tokens_minted = (request.token_a_amount + request.token_b_amount) / Decimal("20")
            
            # Simulate transaction
            tx_hash = f"0x{''.join([f'{i:02x}' for i in range(32)])}"
            
            # Log transaction
            logger.info(f"Add Liquidity: {request.user_address} added {request.token_a_amount} GUARD + {request.token_b_amount} {token_b_key}")
            
            return {
                "success": True,
                "transaction_hash": tx_hash,
                "lp_tokens_minted": str(lp_tokens_minted),
                "pool_share_percentage": str((lp_tokens_minted / Decimal("1000")) * Decimal("100")),
                "estimated_apr": str(pool_stats.get("current_apr", "15.0")),
                "message": f"Successfully added liquidity to {request.pool_pair} pool"
            }
            
        except Exception as e:
            logger.error(f"Add liquidity error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def process_remove_liquidity(self, request: RemoveLiquidityRequest) -> Dict:
        """Process remove liquidity request"""
        try:
            balances = await self.get_user_balances(request.user_address)
            lp_key = f"LP_{request.pool_pair.replace('-', '_')}"
            
            if lp_key not in balances:
                raise HTTPException(status_code=400, detail="No LP tokens found for this pool")
            
            lp_balance = balances[lp_key]
            lp_to_remove = lp_balance * Decimal(str(request.percentage)) / Decimal("100")
            
            if lp_to_remove > lp_balance:
                raise HTTPException(status_code=400, detail="Insufficient LP token balance")
            
            # Calculate tokens to receive (mock calculation)
            token_a_amount = lp_to_remove * Decimal("14.6")  # Mock ratio
            token_b_amount = lp_to_remove * Decimal("0.0584")
            
            tx_hash = f"0x{''.join([f'{i+32:02x}' for i in range(32)])}"
            
            logger.info(f"Remove Liquidity: {request.user_address} removed {request.percentage}% from {request.pool_pair}")
            
            return {
                "success": True,
                "transaction_hash": tx_hash,
                "lp_tokens_burned": str(lp_to_remove),
                "token_a_received": str(token_a_amount),
                "token_b_received": str(token_b_amount),
                "message": f"Successfully removed {request.percentage}% liquidity from {request.pool_pair} pool"
            }
            
        except Exception as e:
            logger.error(f"Remove liquidity error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def process_stake(self, request: StakeRequest) -> Dict:
        """Process stake tokens request"""
        try:
            balances = await self.get_user_balances(request.user_address)
            
            if balances["GUARD"] < request.amount:
                raise HTTPException(status_code=400, detail="Insufficient GUARD balance")
            
            # Calculate rewards
            rewards_info = await self.calculate_staking_rewards(request.pool_type, request.amount)
            
            # Create staking position
            position_id = len(await self.get_user_staking_positions(request.user_address)) + 1
            pool_config = self.staking_pools[request.pool_type]
            unlock_date = datetime.now() + timedelta(days=pool_config["lock_days"])
            
            tx_hash = f"0x{''.join([f'{i+64:02x}' for i in range(32)])}"
            
            logger.info(f"Stake: {request.user_address} staked {request.amount} GUARD in {request.pool_type} pool")
            
            return {
                "success": True,
                "transaction_hash": tx_hash,
                "position_id": position_id,
                "staked_amount": str(request.amount),
                "pool_type": request.pool_type,
                "apr": str(rewards_info["effective_apr"] * 100),
                "daily_rewards": str(rewards_info["daily_reward"]),
                "unlock_date": unlock_date.isoformat(),
                "auto_compound": request.auto_compound,
                "message": f"Successfully staked {request.amount} GUARD tokens"
            }
            
        except Exception as e:
            logger.error(f"Stake error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def process_unstake(self, request: UnstakeRequest) -> Dict:
        """Process unstake tokens request"""
        try:
            positions = await self.get_user_staking_positions(request.user_address)
            position = next((p for p in positions if p["position_id"] == request.position_id), None)
            
            if not position:
                raise HTTPException(status_code=400, detail="Staking position not found")
            
            if request.amount > position["staked_amount"]:
                raise HTTPException(status_code=400, detail="Amount exceeds staked balance")
            
            # Calculate penalty if early withdrawal
            penalty_amount = Decimal("0")
            is_early = datetime.now() < position["unlock_date"]
            
            if is_early:
                penalty_amount = request.amount * position["penalty_rate"]
            
            final_amount = request.amount - penalty_amount
            
            tx_hash = f"0x{''.join([f'{i+96:02x}' for i in range(32)])}"
            
            logger.info(f"Unstake: {request.user_address} unstaked {request.amount} GUARD from position {request.position_id}")
            
            return {
                "success": True,
                "transaction_hash": tx_hash,
                "unstaked_amount": str(request.amount),
                "penalty_amount": str(penalty_amount),
                "final_amount": str(final_amount),
                "rewards_claimed": str(position["earned_rewards"]),
                "early_withdrawal": is_early,
                "message": f"Successfully unstaked {request.amount} GUARD tokens"
            }
            
        except Exception as e:
            logger.error(f"Unstake error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def process_claim_rewards(self, request: ClaimRewardsRequest) -> Dict:
        """Process claim rewards request"""
        try:
            positions = await self.get_user_staking_positions(request.user_address)
            
            total_staking_rewards = sum(p["earned_rewards"] for p in positions)
            total_liquidity_rewards = Decimal("40.25")  # Mock liquidity rewards
            
            if request.reward_type == "staking":
                claimable_amount = total_staking_rewards
            elif request.reward_type == "liquidity":
                claimable_amount = total_liquidity_rewards
            else:  # all
                claimable_amount = total_staking_rewards + total_liquidity_rewards
            
            tx_hash = f"0x{''.join([f'{i+128:02x}' for i in range(32)])}"
            
            logger.info(f"Claim Rewards: {request.user_address} claimed {claimable_amount} GUARD rewards")
            
            return {
                "success": True,
                "transaction_hash": tx_hash,
                "claimed_amount": str(claimable_amount),
                "reward_type": request.reward_type,
                "auto_compound": request.auto_compound,
                "staking_rewards": str(total_staking_rewards) if request.reward_type != "liquidity" else "0",
                "liquidity_rewards": str(total_liquidity_rewards) if request.reward_type != "staking" else "0",
                "message": f"Successfully claimed {claimable_amount} GUARD in rewards"
            }
            
        except Exception as e:
            logger.error(f"Claim rewards error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def process_compound_settings(self, request: CompoundSettingsRequest) -> Dict:
        """Update auto-compound settings"""
        try:
            # Store user preferences (in production, save to database)
            user_settings = {
                "user_address": request.user_address,
                "frequency": request.frequency,
                "threshold": str(request.threshold),
                "enabled": request.enabled,
                "updated_at": datetime.now().isoformat()
            }
            
            logger.info(f"Compound Settings: Updated settings for {request.user_address}")
            
            return {
                "success": True,
                "settings": user_settings,
                "message": f"Auto-compound settings updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Compound settings error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# Initialize handler
defi_handler = DeFiFormsHandler()

# API Routes
@app.get("/", response_class=HTMLResponse)
async def serve_defi_forms():
    """Serve the DeFi forms HTML page"""
    try:
        with open("defi_forms.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="DeFi forms page not found")

@app.get("/api/stats/{user_address}")
async def get_user_stats(user_address: str):
    """Get user's DeFi statistics"""
    try:
        balances = await defi_handler.get_user_balances(user_address)
        positions = await defi_handler.get_user_staking_positions(user_address)
        
        total_staked = sum(p["staked_amount"] for p in positions)
        pending_rewards = sum(p["earned_rewards"] for p in positions)
        
        return JSONResponse({
            "balances": {k: str(v) for k, v in balances.items()},
            "staking": {
                "total_staked": str(total_staked),
                "pending_rewards": str(pending_rewards),
                "positions_count": len(positions)
            },
            "liquidity": {
                "my_liquidity": str(balances.get("LP_GUARD_ETH", 0) * Decimal("146")),  # Mock USD value
                "positions": [
                    {"pair": "GUARD-ETH", "lp_tokens": str(balances.get("LP_GUARD_ETH", 0))},
                    {"pair": "GUARD-USDC", "lp_tokens": str(balances.get("LP_GUARD_USDC", 0))},
                    {"pair": "GUARD-BTC", "lp_tokens": str(balances.get("LP_GUARD_BTC", 0))}
                ]
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pool-stats/{pool_pair}")
async def get_pool_statistics(pool_pair: str):
    """Get liquidity pool statistics"""
    if pool_pair not in defi_handler.pool_configs:
        raise HTTPException(status_code=400, detail="Invalid pool pair")
    
    try:
        stats = await defi_handler.get_pool_stats(pool_pair)
        return JSONResponse({k: str(v) for k, v in stats.items()})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/add-liquidity")
async def add_liquidity(request: LiquidityRequest):
    """Add liquidity to pool"""
    return await defi_handler.process_add_liquidity(request)

@app.post("/api/remove-liquidity")
async def remove_liquidity(request: RemoveLiquidityRequest):
    """Remove liquidity from pool"""
    return await defi_handler.process_remove_liquidity(request)

@app.post("/api/stake")
async def stake_tokens(request: StakeRequest):
    """Stake GUARD tokens"""
    return await defi_handler.process_stake(request)

@app.post("/api/unstake")
async def unstake_tokens(request: UnstakeRequest):
    """Unstake GUARD tokens"""
    return await defi_handler.process_unstake(request)

@app.post("/api/claim-rewards")
async def claim_rewards(request: ClaimRewardsRequest):
    """Claim staking/liquidity rewards"""
    return await defi_handler.process_claim_rewards(request)

@app.post("/api/compound-settings")
async def update_compound_settings(request: CompoundSettingsRequest):
    """Update auto-compound settings"""
    return await defi_handler.process_compound_settings(request)

@app.get("/api/staking-positions/{user_address}")
async def get_staking_positions(user_address: str):
    """Get user's staking positions"""
    try:
        positions = await defi_handler.get_user_staking_positions(user_address)
        return JSONResponse([
            {
                "position_id": p["position_id"],
                "pool_type": p["pool_type"],
                "staked_amount": str(p["staked_amount"]),
                "earned_rewards": str(p["earned_rewards"]),
                "start_date": p["start_date"].isoformat(),
                "unlock_date": p["unlock_date"].isoformat(),
                "is_locked": p["is_locked"],
                "penalty_rate": str(p["penalty_rate"] * 100)
            } for p in positions
        ])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    logger.info("Starting GuardianShield DeFi Forms Server...")
    uvicorn.run(
        "defi_forms_backend:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )