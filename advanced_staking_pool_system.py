"""
Advanced Staking Pool System for GuardianShield
Comprehensive staking mechanism with rewards, slashing, and governance
"""

import asyncio
import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal, getcontext
from dataclasses import dataclass, field
from enum import Enum
import math
import time
import hashlib
import random

# Set high precision for financial calculations
getcontext().prec = 28

class StakingType(Enum):
    """Types of staking mechanisms"""
    FLEXIBLE = "flexible"           # Unstake anytime
    FIXED_TERM = "fixed_term"      # Lock for specific period
    LIQUIDITY_MINING = "liquidity_mining"  # LP token staking
    GOVERNANCE = "governance"       # Governance token staking
    VALIDATOR = "validator"         # Validator node staking
    YIELD_FARMING = "yield_farming" # Multi-reward farming

class StakeStatus(Enum):
    """Status of individual stakes"""
    ACTIVE = "active"
    UNBONDING = "unbonding"
    SLASHED = "slashed"
    WITHDRAWN = "withdrawn"
    LOCKED = "locked"

class RewardType(Enum):
    """Types of staking rewards"""
    NATIVE_TOKEN = "native_token"
    SECONDARY_TOKEN = "secondary_token"
    LP_FEES = "lp_fees"
    GOVERNANCE_REWARDS = "governance_rewards"
    VALIDATOR_REWARDS = "validator_rewards"

@dataclass
class StakePosition:
    """Individual stake position"""
    stake_id: str
    user_address: str
    pool_id: str
    amount: Decimal
    staking_type: StakingType
    status: StakeStatus
    stake_timestamp: datetime
    unlock_timestamp: Optional[datetime]
    last_reward_claim: datetime
    accumulated_rewards: Dict[str, Decimal] = field(default_factory=dict)
    multiplier: Decimal = Decimal('1.0')
    penalty_applied: Decimal = Decimal('0')
    governance_power: Decimal = Decimal('0')

@dataclass
class RewardProgram:
    """Reward distribution program"""
    program_id: str
    pool_id: str
    reward_token: str
    total_rewards: Decimal
    reward_rate: Decimal  # tokens per second
    start_time: datetime
    end_time: datetime
    active: bool
    distributed_amount: Decimal = Decimal('0')
    participants: List[str] = field(default_factory=list)

@dataclass
class ValidatorNode:
    """Validator node configuration"""
    node_id: str
    operator_address: str
    stake_amount: Decimal
    commission_rate: Decimal
    performance_score: Decimal
    slashing_events: int
    uptime_percentage: Decimal
    delegated_stake: Decimal
    status: str

class AdvancedStakingPoolSystem:
    """Comprehensive staking pool management system"""
    
    def __init__(self):
        self.staking_pools = {}
        self.stake_positions = {}
        self.reward_programs = {}
        self.validator_nodes = {}
        
        # System configuration
        self.config = {
            'min_stake_amount': Decimal('10'),
            'max_stake_amount': Decimal('10000000'),
            'default_reward_rate': Decimal('0.10'),  # 10% APY
            'unbonding_period': timedelta(days=21),
            'slashing_penalty': Decimal('0.05'),  # 5% slashing
            'governance_threshold': Decimal('1000'),
            'validator_min_stake': Decimal('32'),
            'commission_max_rate': Decimal('0.20'),  # 20% max commission
            'performance_threshold': Decimal('0.95'),
            'early_withdrawal_penalty': Decimal('0.02'),  # 2% penalty
        }
        
        # Database setup
        self.database_path = "staking_pools.db"
        self.setup_database()
        
        # Reward calculation
        self.reward_multipliers = {
            StakingType.FLEXIBLE: Decimal('1.0'),
            StakingType.FIXED_TERM: Decimal('1.5'),
            StakingType.LIQUIDITY_MINING: Decimal('2.0'),
            StakingType.GOVERNANCE: Decimal('1.2'),
            StakingType.VALIDATOR: Decimal('3.0'),
            StakingType.YIELD_FARMING: Decimal('2.5')
        }
        
        # Lock period multipliers
        self.lock_multipliers = {
            30: Decimal('1.1'),   # 30 days: 10% bonus
            90: Decimal('1.3'),   # 90 days: 30% bonus
            180: Decimal('1.6'),  # 180 days: 60% bonus
            365: Decimal('2.0'),  # 1 year: 100% bonus
        }
    
    def setup_database(self):
        """Setup comprehensive staking database schema"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Staking pools table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS staking_pools (
                pool_id TEXT PRIMARY KEY,
                name TEXT,
                staking_token TEXT,
                reward_tokens TEXT,  -- JSON array
                staking_type TEXT,
                total_staked REAL,
                total_rewards_distributed REAL,
                apy REAL,
                min_stake REAL,
                max_stake REAL,
                lock_period INTEGER,  -- days
                active BOOLEAN,
                created_timestamp TIMESTAMP,
                last_updated TIMESTAMP
            )
        ''')
        
        # Stake positions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stake_positions (
                stake_id TEXT PRIMARY KEY,
                user_address TEXT,
                pool_id TEXT,
                amount REAL,
                staking_type TEXT,
                status TEXT,
                multiplier REAL,
                stake_timestamp TIMESTAMP,
                unlock_timestamp TIMESTAMP,
                last_reward_claim TIMESTAMP,
                accumulated_rewards TEXT,  -- JSON object
                penalty_applied REAL,
                governance_power REAL
            )
        ''')
        
        # Reward programs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reward_programs (
                program_id TEXT PRIMARY KEY,
                pool_id TEXT,
                reward_token TEXT,
                total_rewards REAL,
                reward_rate REAL,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                active BOOLEAN,
                distributed_amount REAL,
                participants_count INTEGER
            )
        ''')
        
        # Validator nodes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS validator_nodes (
                node_id TEXT PRIMARY KEY,
                operator_address TEXT,
                stake_amount REAL,
                commission_rate REAL,
                performance_score REAL,
                slashing_events INTEGER,
                uptime_percentage REAL,
                delegated_stake REAL,
                status TEXT,
                created_timestamp TIMESTAMP,
                last_updated TIMESTAMP
            )
        ''')
        
        # Rewards distribution history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reward_distributions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_address TEXT,
                pool_id TEXT,
                reward_token TEXT,
                amount REAL,
                distribution_timestamp TIMESTAMP,
                program_id TEXT,
                claim_transaction TEXT
            )
        ''')
        
        # Slashing events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS slashing_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stake_id TEXT,
                validator_id TEXT,
                slashing_type TEXT,
                penalty_amount REAL,
                reason TEXT,
                evidence_hash TEXT,
                timestamp TIMESTAMP,
                resolved BOOLEAN
            )
        ''')
        
        # Governance proposals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS governance_proposals (
                proposal_id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                proposer_address TEXT,
                voting_start TIMESTAMP,
                voting_end TIMESTAMP,
                votes_for REAL,
                votes_against REAL,
                votes_abstain REAL,
                status TEXT,
                execution_timestamp TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_staking_pool(self, pool_id: str, name: str, staking_token: str,
                           reward_tokens: List[str], staking_type: StakingType,
                           apy: Decimal, lock_period_days: int = 0,
                           min_stake: Optional[Decimal] = None,
                           max_stake: Optional[Decimal] = None) -> str:
        """Create new staking pool"""
        
        if min_stake is None:
            min_stake = self.config['min_stake_amount']
        if max_stake is None:
            max_stake = self.config['max_stake_amount']
        
        pool_data = {
            'pool_id': pool_id,
            'name': name,
            'staking_token': staking_token,
            'reward_tokens': reward_tokens,
            'staking_type': staking_type,
            'total_staked': Decimal('0'),
            'total_rewards_distributed': Decimal('0'),
            'apy': apy,
            'min_stake': min_stake,
            'max_stake': max_stake,
            'lock_period': lock_period_days,
            'active': True,
            'created_timestamp': datetime.now(),
            'last_updated': datetime.now(),
            'stake_positions': [],
            'reward_programs': []
        }
        
        self.staking_pools[pool_id] = pool_data
        
        # Store in database
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO staking_pools
            (pool_id, name, staking_token, reward_tokens, staking_type,
             total_staked, total_rewards_distributed, apy, min_stake, max_stake,
             lock_period, active, created_timestamp, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            pool_id, name, staking_token, json.dumps(reward_tokens), staking_type.value,
            0.0, 0.0, float(apy), float(min_stake), float(max_stake),
            lock_period_days, True, datetime.now(), datetime.now()
        ))
        
        conn.commit()
        conn.close()
        
        print(f"Created staking pool: {name} ({pool_id})")
        print(f"  Type: {staking_type.value}")
        print(f"  APY: {apy * 100:.2f}%")
        print(f"  Lock Period: {lock_period_days} days")
        print(f"  Min/Max Stake: {min_stake} - {max_stake}")
        
        return pool_id
    
    def stake_tokens(self, pool_id: str, user_address: str, amount: Decimal,
                    lock_days: Optional[int] = None) -> StakePosition:
        """Stake tokens in the specified pool"""
        
        if pool_id not in self.staking_pools:
            raise ValueError(f"Staking pool {pool_id} not found")
        
        pool = self.staking_pools[pool_id]
        
        if not pool['active']:
            raise ValueError(f"Staking pool {pool_id} is not active")
        
        if amount < pool['min_stake'] or amount > pool['max_stake']:
            raise ValueError(f"Stake amount must be between {pool['min_stake']} and {pool['max_stake']}")
        
        # Calculate unlock timestamp
        unlock_timestamp = None
        multiplier = self.reward_multipliers[pool['staking_type']]
        
        if pool['staking_type'] == StakingType.FIXED_TERM or lock_days:
            lock_period = lock_days or pool['lock_period']
            unlock_timestamp = datetime.now() + timedelta(days=lock_period)
            
            # Apply lock period bonus
            if lock_period in self.lock_multipliers:
                multiplier *= self.lock_multipliers[lock_period]
        
        # Calculate governance power
        governance_power = Decimal('0')
        if pool['staking_type'] == StakingType.GOVERNANCE:
            governance_power = amount * multiplier
        
        # Create stake position
        stake_id = f"{pool_id}_{user_address}_{int(time.time())}"
        
        position = StakePosition(
            stake_id=stake_id,
            user_address=user_address,
            pool_id=pool_id,
            amount=amount,
            staking_type=pool['staking_type'],
            status=StakeStatus.ACTIVE,
            stake_timestamp=datetime.now(),
            unlock_timestamp=unlock_timestamp,
            last_reward_claim=datetime.now(),
            multiplier=multiplier,
            governance_power=governance_power
        )
        
        self.stake_positions[stake_id] = position
        
        # Update pool totals
        pool['total_staked'] += amount
        pool['stake_positions'].append(stake_id)
        pool['last_updated'] = datetime.now()
        
        # Store in database
        self._store_stake_position(position)
        self._update_pool_database(pool_id)
        
        print(f"Staked {amount} tokens in {pool['name']}:")
        print(f"  User: {user_address}")
        print(f"  Stake ID: {stake_id}")
        print(f"  Multiplier: {multiplier:.2f}x")
        if unlock_timestamp:
            print(f"  Unlock Date: {unlock_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Governance Power: {governance_power}")
        
        return position
    
    def unstake_tokens(self, stake_id: str, amount: Optional[Decimal] = None) -> Dict[str, Any]:
        """Unstake tokens (full or partial)"""
        
        if stake_id not in self.stake_positions:
            raise ValueError(f"Stake position {stake_id} not found")
        
        position = self.stake_positions[stake_id]
        pool = self.staking_pools[position.pool_id]
        
        if position.status != StakeStatus.ACTIVE:
            raise ValueError(f"Stake {stake_id} is not active")
        
        # Check if unlock period has passed for fixed-term stakes
        current_time = datetime.now()
        early_withdrawal = False
        penalty = Decimal('0')
        
        if (position.unlock_timestamp and current_time < position.unlock_timestamp and
            position.staking_type == StakingType.FIXED_TERM):
            early_withdrawal = True
            penalty = amount * self.config['early_withdrawal_penalty']
        
        # Default to full unstake
        if amount is None:
            amount = position.amount
        
        if amount > position.amount:
            raise ValueError("Cannot unstake more than staked amount")
        
        # Calculate pending rewards before unstaking
        pending_rewards = self._calculate_pending_rewards(stake_id)
        
        # Update position
        position.amount -= amount
        pool['total_staked'] -= amount
        
        withdrawal_result = {
            'stake_id': stake_id,
            'withdrawn_amount': amount,
            'penalty_applied': penalty,
            'pending_rewards': pending_rewards,
            'early_withdrawal': early_withdrawal,
            'final_amount': amount - penalty,
            'timestamp': current_time
        }
        
        # Handle different unstaking scenarios
        if position.amount == 0:
            # Full unstake
            position.status = StakeStatus.WITHDRAWN
            pool['stake_positions'].remove(stake_id)
        elif position.staking_type == StakingType.FLEXIBLE:
            # Partial flexible unstake - immediate
            pass
        else:
            # Partial fixed-term unstake - start unbonding
            position.status = StakeStatus.UNBONDING
        
        # Apply penalty if early withdrawal
        if penalty > 0:
            position.penalty_applied += penalty
        
        # Update databases
        self._store_stake_position(position)
        self._update_pool_database(position.pool_id)
        
        print(f"Unstaking from {pool['name']}:")
        print(f"  Amount: {amount}")
        print(f"  Penalty: {penalty}")
        print(f"  Final Amount: {amount - penalty}")
        if early_withdrawal:
            print(f"  Early Withdrawal Penalty Applied")
        
        return withdrawal_result
    
    def claim_rewards(self, stake_id: str) -> Dict[str, Decimal]:
        """Claim accumulated staking rewards"""
        
        if stake_id not in self.stake_positions:
            raise ValueError(f"Stake position {stake_id} not found")
        
        position = self.stake_positions[stake_id]
        pool = self.staking_pools[position.pool_id]
        
        if position.status != StakeStatus.ACTIVE:
            raise ValueError(f"Stake {stake_id} is not active")
        
        # Calculate pending rewards
        pending_rewards = self._calculate_pending_rewards(stake_id)
        
        # Add to accumulated rewards
        for token, amount in pending_rewards.items():
            if token not in position.accumulated_rewards:
                position.accumulated_rewards[token] = Decimal('0')
            position.accumulated_rewards[token] += amount
        
        # Update last reward claim timestamp
        position.last_reward_claim = datetime.now()
        
        # Update pool statistics
        for token, amount in pending_rewards.items():
            pool['total_rewards_distributed'] += amount
        
        # Store reward distribution in database
        for token, amount in pending_rewards.items():
            self._store_reward_distribution(
                position.user_address, 
                position.pool_id, 
                token, 
                amount, 
                datetime.now()
            )
        
        # Update databases
        self._store_stake_position(position)
        self._update_pool_database(position.pool_id)
        
        print(f"Claimed rewards for stake {stake_id}:")
        for token, amount in pending_rewards.items():
            print(f"  {amount:.6f} {token}")
        
        return pending_rewards
    
    def create_validator_node(self, node_id: str, operator_address: str, 
                             stake_amount: Decimal, commission_rate: Decimal) -> ValidatorNode:
        """Create validator node for staking"""
        
        if stake_amount < self.config['validator_min_stake']:
            raise ValueError(f"Minimum validator stake is {self.config['validator_min_stake']}")
        
        if commission_rate > self.config['commission_max_rate']:
            raise ValueError(f"Maximum commission rate is {self.config['commission_max_rate'] * 100}%")
        
        validator = ValidatorNode(
            node_id=node_id,
            operator_address=operator_address,
            stake_amount=stake_amount,
            commission_rate=commission_rate,
            performance_score=Decimal('1.0'),
            slashing_events=0,
            uptime_percentage=Decimal('1.0'),
            delegated_stake=Decimal('0'),
            status='active'
        )
        
        self.validator_nodes[node_id] = validator
        
        # Store in database
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO validator_nodes
            (node_id, operator_address, stake_amount, commission_rate,
             performance_score, slashing_events, uptime_percentage, 
             delegated_stake, status, created_timestamp, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            node_id, operator_address, float(stake_amount), float(commission_rate),
            1.0, 0, 1.0, 0.0, 'active', datetime.now(), datetime.now()
        ))
        
        conn.commit()
        conn.close()
        
        print(f"Created validator node: {node_id}")
        print(f"  Operator: {operator_address}")
        print(f"  Stake: {stake_amount}")
        print(f"  Commission: {commission_rate * 100:.2f}%")
        
        return validator
    
    def delegate_to_validator(self, user_address: str, validator_id: str, amount: Decimal) -> str:
        """Delegate stake to a validator node"""
        
        if validator_id not in self.validator_nodes:
            raise ValueError(f"Validator {validator_id} not found")
        
        validator = self.validator_nodes[validator_id]
        
        if validator.status != 'active':
            raise ValueError(f"Validator {validator_id} is not active")
        
        # Create delegation stake position
        delegation_id = f"delegation_{validator_id}_{user_address}_{int(time.time())}"
        
        position = StakePosition(
            stake_id=delegation_id,
            user_address=user_address,
            pool_id=validator_id,  # Using validator_id as pool_id for delegation
            amount=amount,
            staking_type=StakingType.VALIDATOR,
            status=StakeStatus.ACTIVE,
            stake_timestamp=datetime.now(),
            unlock_timestamp=datetime.now() + self.config['unbonding_period'],
            last_reward_claim=datetime.now(),
            multiplier=self.reward_multipliers[StakingType.VALIDATOR]
        )
        
        self.stake_positions[delegation_id] = position
        
        # Update validator delegated stake
        validator.delegated_stake += amount
        
        # Store in databases
        self._store_stake_position(position)
        self._update_validator_database(validator_id)
        
        print(f"Delegated {amount} tokens to validator {validator_id}")
        print(f"  Delegation ID: {delegation_id}")
        print(f"  Unbonding Period: {self.config['unbonding_period'].days} days")
        
        return delegation_id
    
    def apply_slashing(self, validator_id: str, slashing_type: str, 
                      penalty_percentage: Decimal, reason: str) -> Dict[str, Any]:
        """Apply slashing penalty to validator and delegators"""
        
        if validator_id not in self.validator_nodes:
            raise ValueError(f"Validator {validator_id} not found")
        
        validator = self.validator_nodes[validator_id]
        
        # Calculate slashing amounts
        validator_penalty = validator.stake_amount * penalty_percentage
        delegator_penalty = validator.delegated_stake * penalty_percentage
        
        # Apply penalty to validator
        validator.stake_amount -= validator_penalty
        validator.slashing_events += 1
        validator.performance_score *= Decimal('0.9')  # Reduce performance score
        
        # Apply penalty to all delegated positions
        affected_delegations = []
        for stake_id, position in self.stake_positions.items():
            if (position.pool_id == validator_id and 
                position.staking_type == StakingType.VALIDATOR and
                position.status == StakeStatus.ACTIVE):
                
                delegation_penalty = position.amount * penalty_percentage
                position.amount -= delegation_penalty
                position.penalty_applied += delegation_penalty
                position.status = StakeStatus.SLASHED
                
                affected_delegations.append({
                    'stake_id': stake_id,
                    'user_address': position.user_address,
                    'penalty_amount': delegation_penalty
                })
        
        # Update validator delegated stake
        validator.delegated_stake -= delegator_penalty
        
        # Create slashing event record
        slashing_event = {
            'validator_id': validator_id,
            'slashing_type': slashing_type,
            'penalty_percentage': penalty_percentage,
            'validator_penalty': validator_penalty,
            'delegator_penalty': delegator_penalty,
            'reason': reason,
            'timestamp': datetime.now(),
            'affected_delegations': len(affected_delegations)
        }
        
        # Store slashing event
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO slashing_events
            (stake_id, validator_id, slashing_type, penalty_amount, 
             reason, evidence_hash, timestamp, resolved)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            None, validator_id, slashing_type, float(validator_penalty + delegator_penalty),
            reason, hashlib.sha256(reason.encode()).hexdigest(), datetime.now(), False
        ))
        
        conn.commit()
        conn.close()
        
        # Update databases
        self._update_validator_database(validator_id)
        for delegation in affected_delegations:
            self._store_stake_position(self.stake_positions[delegation['stake_id']])
        
        print(f"Applied slashing to validator {validator_id}:")
        print(f"  Slashing Type: {slashing_type}")
        print(f"  Penalty Percentage: {penalty_percentage * 100:.2f}%")
        print(f"  Validator Penalty: {validator_penalty}")
        print(f"  Delegator Penalty: {delegator_penalty}")
        print(f"  Affected Delegations: {len(affected_delegations)}")
        print(f"  Reason: {reason}")
        
        return slashing_event
    
    def create_governance_proposal(self, proposal_id: str, title: str, description: str,
                                  proposer_address: str, voting_duration_days: int = 7) -> str:
        """Create governance proposal for voting"""
        
        # Check if proposer has minimum governance power
        proposer_governance_power = self._get_user_governance_power(proposer_address)
        if proposer_governance_power < self.config['governance_threshold']:
            raise ValueError(f"Insufficient governance power. Required: {self.config['governance_threshold']}")
        
        voting_start = datetime.now()
        voting_end = voting_start + timedelta(days=voting_duration_days)
        
        proposal_data = {
            'proposal_id': proposal_id,
            'title': title,
            'description': description,
            'proposer_address': proposer_address,
            'voting_start': voting_start,
            'voting_end': voting_end,
            'votes_for': Decimal('0'),
            'votes_against': Decimal('0'),
            'votes_abstain': Decimal('0'),
            'status': 'active',
            'execution_timestamp': None
        }
        
        # Store in database
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO governance_proposals
            (proposal_id, title, description, proposer_address,
             voting_start, voting_end, votes_for, votes_against,
             votes_abstain, status, execution_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            proposal_id, title, description, proposer_address,
            voting_start, voting_end, 0.0, 0.0, 0.0, 'active', None
        ))
        
        conn.commit()
        conn.close()
        
        print(f"Created governance proposal: {proposal_id}")
        print(f"  Title: {title}")
        print(f"  Proposer: {proposer_address}")
        print(f"  Voting Period: {voting_start} to {voting_end}")
        
        return proposal_id
    
    def vote_on_proposal(self, proposal_id: str, user_address: str, 
                        vote: str, voting_power: Optional[Decimal] = None) -> bool:
        """Vote on governance proposal"""
        
        if voting_power is None:
            voting_power = self._get_user_governance_power(user_address)
        
        if voting_power == 0:
            raise ValueError("No governance power to vote")
        
        # In a real implementation, this would update the proposal votes
        print(f"Vote cast on proposal {proposal_id}:")
        print(f"  User: {user_address}")
        print(f"  Vote: {vote}")
        print(f"  Voting Power: {voting_power}")
        
        return True
    
    def _calculate_pending_rewards(self, stake_id: str) -> Dict[str, Decimal]:
        """Calculate pending rewards for a stake position"""
        
        position = self.stake_positions[stake_id]
        pool = self.staking_pools[position.pool_id]
        
        # Calculate time elapsed since last reward claim
        time_elapsed = datetime.now() - position.last_reward_claim
        seconds_elapsed = Decimal(time_elapsed.total_seconds())
        
        # Calculate base rewards
        annual_rate = pool['apy'] * position.multiplier
        reward_per_second = (position.amount * annual_rate) / (Decimal('365') * Decimal('24') * Decimal('3600'))
        
        pending_amount = reward_per_second * seconds_elapsed
        
        # Return rewards by token
        rewards = {}
        for reward_token in pool['reward_tokens']:
            rewards[reward_token] = pending_amount / len(pool['reward_tokens'])
        
        return rewards
    
    def _get_user_governance_power(self, user_address: str) -> Decimal:
        """Get total governance power for a user"""
        
        total_power = Decimal('0')
        
        for position in self.stake_positions.values():
            if (position.user_address == user_address and 
                position.status == StakeStatus.ACTIVE):
                total_power += position.governance_power
        
        return total_power
    
    def _store_stake_position(self, position: StakePosition):
        """Store stake position in database"""
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO stake_positions
            (stake_id, user_address, pool_id, amount, staking_type, status,
             multiplier, stake_timestamp, unlock_timestamp, last_reward_claim,
             accumulated_rewards, penalty_applied, governance_power)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            position.stake_id, position.user_address, position.pool_id,
            float(position.amount), position.staking_type.value, position.status.value,
            float(position.multiplier), position.stake_timestamp, position.unlock_timestamp,
            position.last_reward_claim, json.dumps({k: str(v) for k, v in position.accumulated_rewards.items()}),
            float(position.penalty_applied), float(position.governance_power)
        ))
        
        conn.commit()
        conn.close()
    
    def _store_reward_distribution(self, user_address: str, pool_id: str, 
                                  reward_token: str, amount: Decimal, timestamp: datetime):
        """Store reward distribution record"""
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO reward_distributions
            (user_address, pool_id, reward_token, amount, distribution_timestamp, program_id, claim_transaction)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_address, pool_id, reward_token, float(amount), timestamp, 
            None, f"claim_{int(time.time())}"
        ))
        
        conn.commit()
        conn.close()
    
    def _update_pool_database(self, pool_id: str):
        """Update pool data in database"""
        
        pool = self.staking_pools[pool_id]
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE staking_pools SET
                total_staked = ?, total_rewards_distributed = ?, last_updated = ?
            WHERE pool_id = ?
        ''', (
            float(pool['total_staked']), float(pool['total_rewards_distributed']),
            pool['last_updated'], pool_id
        ))
        
        conn.commit()
        conn.close()
    
    def _update_validator_database(self, validator_id: str):
        """Update validator data in database"""
        
        validator = self.validator_nodes[validator_id]
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE validator_nodes SET
                stake_amount = ?, performance_score = ?, slashing_events = ?,
                uptime_percentage = ?, delegated_stake = ?, status = ?, last_updated = ?
            WHERE node_id = ?
        ''', (
            float(validator.stake_amount), float(validator.performance_score),
            validator.slashing_events, float(validator.uptime_percentage),
            float(validator.delegated_stake), validator.status, datetime.now(),
            validator_id
        ))
        
        conn.commit()
        conn.close()
    
    def get_pool_analytics(self, pool_id: str) -> Dict[str, Any]:
        """Get comprehensive pool analytics"""
        
        if pool_id not in self.staking_pools:
            raise ValueError(f"Staking pool {pool_id} not found")
        
        pool = self.staking_pools[pool_id]
        
        # Calculate metrics
        total_stakers = len([p for p in self.stake_positions.values() 
                           if p.pool_id == pool_id and p.status == StakeStatus.ACTIVE])
        
        avg_stake = pool['total_staked'] / total_stakers if total_stakers > 0 else Decimal('0')
        
        analytics = {
            'pool_id': pool_id,
            'name': pool['name'],
            'type': pool['staking_type'].value,
            'total_staked': float(pool['total_staked']),
            'total_rewards_distributed': float(pool['total_rewards_distributed']),
            'apy': float(pool['apy'] * 100),  # As percentage
            'total_stakers': total_stakers,
            'average_stake': float(avg_stake),
            'min_stake': float(pool['min_stake']),
            'max_stake': float(pool['max_stake']),
            'lock_period': pool['lock_period'],
            'active': pool['active'],
            'staking_token': pool['staking_token'],
            'reward_tokens': pool['reward_tokens'],
            'created_timestamp': pool['created_timestamp'].isoformat(),
            'last_updated': pool['last_updated'].isoformat()
        }
        
        return analytics
    
    def get_user_positions(self, user_address: str) -> List[Dict[str, Any]]:
        """Get all staking positions for a user"""
        
        user_positions = []
        
        for stake_id, position in self.stake_positions.items():
            if position.user_address == user_address:
                pool = self.staking_pools.get(position.pool_id, {})
                pending_rewards = self._calculate_pending_rewards(stake_id)
                
                position_data = {
                    'stake_id': stake_id,
                    'pool_name': pool.get('name', 'Unknown'),
                    'pool_id': position.pool_id,
                    'amount': float(position.amount),
                    'staking_type': position.staking_type.value,
                    'status': position.status.value,
                    'multiplier': float(position.multiplier),
                    'pending_rewards': {k: float(v) for k, v in pending_rewards.items()},
                    'accumulated_rewards': {k: float(v) for k, v in position.accumulated_rewards.items()},
                    'governance_power': float(position.governance_power),
                    'stake_timestamp': position.stake_timestamp.isoformat(),
                    'unlock_timestamp': position.unlock_timestamp.isoformat() if position.unlock_timestamp else None,
                    'penalty_applied': float(position.penalty_applied)
                }
                
                user_positions.append(position_data)
        
        return user_positions
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive staking system status"""
        
        total_staked = sum(float(pool['total_staked']) for pool in self.staking_pools.values())
        total_rewards = sum(float(pool['total_rewards_distributed']) for pool in self.staking_pools.values())
        total_positions = len(self.stake_positions)
        active_validators = len([v for v in self.validator_nodes.values() if v.status == 'active'])
        
        return {
            'total_pools': len(self.staking_pools),
            'total_staked_value': total_staked,
            'total_rewards_distributed': total_rewards,
            'total_stake_positions': total_positions,
            'active_validators': active_validators,
            'total_delegated_stake': sum(float(v.delegated_stake) for v in self.validator_nodes.values()),
            'governance_proposals': 0,  # Placeholder
            'slashing_events': sum(v.slashing_events for v in self.validator_nodes.values()),
            'system_config': {k: float(v) if isinstance(v, Decimal) else v 
                            for k, v in self.config.items()},
            'timestamp': datetime.now().isoformat()
        }

# Demo function
async def demonstrate_staking_system():
    """Demonstrate the staking system capabilities"""
    
    print("Advanced Staking Pool System Demo")
    print("=" * 50)
    
    staking_system = AdvancedStakingPoolSystem()
    
    # Create staking pools
    flexible_pool = staking_system.create_staking_pool(
        "GUARD_FLEXIBLE_001",
        "Guardian Flexible Staking",
        "GUARD",
        ["GUARD", "USDC"],
        StakingType.FLEXIBLE,
        Decimal('0.08'),  # 8% APY
        0  # No lock period
    )
    
    fixed_pool = staking_system.create_staking_pool(
        "GUARD_FIXED_001",
        "Guardian Fixed Term Staking",
        "GUARD", 
        ["GUARD"],
        StakingType.FIXED_TERM,
        Decimal('0.15'),  # 15% APY
        365  # 1 year lock
    )
    
    governance_pool = staking_system.create_staking_pool(
        "GUARD_GOV_001",
        "Guardian Governance Staking",
        "GUARD",
        ["GUARD"],
        StakingType.GOVERNANCE,
        Decimal('0.12'),  # 12% APY
        0
    )
    
    # Create validator
    validator = staking_system.create_validator_node(
        "validator_001",
        "0xValidator1",
        Decimal('100'),  # 100 GUARD stake
        Decimal('0.1')   # 10% commission
    )
    
    # Stake tokens
    position1 = staking_system.stake_tokens(flexible_pool, "0xUser1", Decimal('1000'))
    position2 = staking_system.stake_tokens(fixed_pool, "0xUser2", Decimal('5000'))
    position3 = staking_system.stake_tokens(governance_pool, "0xUser3", Decimal('2000'))
    
    # Delegate to validator
    delegation = staking_system.delegate_to_validator("0xUser4", "validator_001", Decimal('500'))
    
    # Simulate time passage for rewards
    print("\nSimulating reward accumulation...")
    
    # Claim rewards (after simulated time)
    await asyncio.sleep(0.1)  # Simulate time passage
    rewards1 = staking_system.claim_rewards(position1.stake_id)
    
    # Create governance proposal
    proposal = staking_system.create_governance_proposal(
        "PROPOSAL_001",
        "Increase Staking Rewards",
        "Proposal to increase base staking rewards by 2%",
        "0xUser3",
        7
    )
    
    # Vote on proposal
    staking_system.vote_on_proposal(proposal, "0xUser3", "for")
    
    # Get analytics
    flexible_analytics = staking_system.get_pool_analytics(flexible_pool)
    fixed_analytics = staking_system.get_pool_analytics(fixed_pool)
    
    print(f"\nFlexible Pool Analytics:")
    print(f"  Total Staked: {flexible_analytics['total_staked']:,.2f} GUARD")
    print(f"  APY: {flexible_analytics['apy']:.2f}%")
    print(f"  Total Stakers: {flexible_analytics['total_stakers']}")
    print(f"  Rewards Distributed: {flexible_analytics['total_rewards_distributed']:,.6f}")
    
    print(f"\nFixed Term Pool Analytics:")
    print(f"  Total Staked: {fixed_analytics['total_staked']:,.2f} GUARD")
    print(f"  APY: {fixed_analytics['apy']:.2f}%")
    print(f"  Lock Period: {fixed_analytics['lock_period']} days")
    print(f"  Total Stakers: {fixed_analytics['total_stakers']}")
    
    # Get user positions
    user1_positions = staking_system.get_user_positions("0xUser1")
    print(f"\nUser1 Positions:")
    for pos in user1_positions:
        print(f"  Pool: {pos['pool_name']}")
        print(f"  Amount: {pos['amount']:,.2f}")
        print(f"  Status: {pos['status']}")
        print(f"  Governance Power: {pos['governance_power']:,.2f}")
    
    # System status
    system_status = staking_system.get_system_status()
    print(f"\nSystem Status:")
    print(f"  Total Pools: {system_status['total_pools']}")
    print(f"  Total Staked: {system_status['total_staked_value']:,.2f}")
    print(f"  Total Positions: {system_status['total_stake_positions']}")
    print(f"  Active Validators: {system_status['active_validators']}")
    print(f"  Total Delegated: {system_status['total_delegated_stake']:,.2f}")
    
    print("\n" + "=" * 50)
    print("Advanced Staking System Ready!")

# Main execution
if __name__ == "__main__":
    asyncio.run(demonstrate_staking_system())