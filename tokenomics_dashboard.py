"""
GuardianShield Tokenomics Dashboard
Visual representation of token distribution, supply mechanics, and economic metrics
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta
import math
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GuardianShield Tokenomics Dashboard",
    description="Transparent visualization of token economics and distribution",
    version="1.0.0"
)

class TokenomicsData:
    """GuardianShield tokenomics structure and calculations"""
    
    def __init__(self):
        self.total_supply = 5_000_000_000  # 5 billion tokens
        self.circulating_supply = 300_000_000  # 6% initially circulating
        self.token_symbol = "GUARD"
        self.token_name = "GuardianShield Token"
        
        # Distribution breakdown for 5 billion tokens
        self.distribution = {
            "initial_rollout": {
                "percentage": 6,
                "tokens": 300_000_000,
                "description": "Initial community rollout and early adopters",
                "release_schedule": "Immediate circulation for launch",
                "current_locked": 0,
                "release_date": "2024-12-20"
            },
            "team_allocation": {
                "percentage": 12,
                "tokens": 600_000_000,
                "description": "Core team, founders, and key contributors",
                "release_schedule": "4-year vesting with 12-month cliff",
                "current_locked": 600_000_000,
                "release_start": "2025-12-20"
            },
            "development_fund": {
                "percentage": 15,
                "tokens": 750_000_000,
                "description": "Ongoing development, audits, and technical advancement",
                "release_schedule": "Milestone-based over 3 years",
                "current_locked": 750_000_000,
                "release_start": "2025-01-01"
            },
            "staking_pools": {
                "percentage": 25,
                "tokens": 1_250_000_000,
                "description": "GUARD tokens for crypto+GUARD=SHIELD staking pairs",
                "release_schedule": "Released as needed for staking pairs over 5 years",
                "current_locked": 1_250_000_000,
                "release_start": "2024-12-20"
            },
            "community_treasury": {
                "percentage": 20,
                "tokens": 1_000_000_000,
                "description": "Community-governed treasury for ecosystem growth",
                "release_schedule": "Democratic governance decisions",
                "current_locked": 1_000_000_000,
                "release_start": "2025-06-01"
            },
            "security_rewards": {
                "percentage": 10,
                "tokens": 500_000_000,
                "description": "AI threat detection, bug bounties, security contributions",
                "release_schedule": "Performance-based distribution over 7 years",
                "current_locked": 500_000_000,
                "release_start": "2024-12-20"
            },
            "tier_1_release": {
                "percentage": 6,
                "tokens": 300_000_000,
                "description": "First timed release tier",
                "release_schedule": "Released 6 months after launch",
                "current_locked": 300_000_000,
                "release_date": "2025-06-20"
            },
            "tier_2_release": {
                "percentage": 4,
                "tokens": 200_000_000,
                "description": "Second timed release tier",
                "release_schedule": "Released 12 months after launch",
                "current_locked": 200_000_000,
                "release_date": "2025-12-20"
            },
            "tier_3_release": {
                "percentage": 2,
                "tokens": 100_000_000,
                "description": "Final timed release tier",
                "release_schedule": "Released 24 months after launch",
                "current_locked": 100_000_000,
                "release_date": "2026-12-20"
            }
        }
        
        # Utility mechanisms
        self.utility_mechanisms = {
            "governance_voting": {
                "title": "Governance Voting",
                "description": "Vote on protocol upgrades, treasury allocation, and security policies",
                "requirement": "Minimum 1,000 GUARD tokens to participate",
                "rewards": "Voting rewards based on participation"
            },
            "security_staking": {
                "title": "Security Pool Staking", 
                "description": "Stake tokens to support AI agent operations and earn rewards",
                "requirement": "Minimum 100 GUARD tokens",
                "rewards": "8-15% APY based on pool performance"
            },
            "threat_reporting": {
                "title": "Threat Detection Rewards",
                "description": "Earn tokens for reporting valid security threats",
                "requirement": "Verified community member",
                "rewards": "10-1000 GUARD per validated threat"
            },
            "liquidity_provision": {
                "title": "Liquidity Mining",
                "description": "Provide liquidity to DEX pools and earn additional rewards",
                "requirement": "LP tokens in approved pools",
                "rewards": "Additional 5-12% APY on top of trading fees"
            },
            "ecosystem_participation": {
                "title": "Ecosystem Rewards",
                "description": "Earn tokens for using GuardianShield services and referrals",
                "requirement": "Active platform usage",
                "rewards": "Variable based on activity level"
            }
        }
        
        # Economic metrics
        self.metrics = self._calculate_metrics()
    
    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate current economic metrics"""
        locked_percentage = ((self.total_supply - self.circulating_supply) / self.total_supply) * 100
        
        return {
            "market_metrics": {
                "total_supply": self.total_supply,
                "circulating_supply": self.circulating_supply,
                "locked_tokens": self.total_supply - self.circulating_supply,
                "locked_percentage": round(locked_percentage, 1),
                "current_price": 0.0523,  # Simulated price in USD
                "market_cap": round(self.circulating_supply * 0.0523, 2),
                "fully_diluted_valuation": round(self.total_supply * 0.0523, 2)
            },
            
            "staking_metrics": {
                "total_staked": 45_000_000,
                "staking_ratio": 30.0,  # 30% of circulating supply staked
                "average_apy": 12.5,
                "total_stakers": 2_847,
                "security_pool_tvl": round(45_000_000 * 0.0523, 2)
            },
            
            "governance_metrics": {
                "total_proposals": 23,
                "active_voters": 1_456,
                "voting_participation_rate": 67.8,
                "treasury_balance": 380_000_000,
                "treasury_value_usd": round(380_000_000 * 0.0523, 2)
            },
            
            "security_metrics": {
                "threats_detected_24h": 847,
                "rewards_distributed_24h": 12_450,
                "ai_agents_active": 127,
                "network_security_score": 94.2
            }
        }
    
    def get_historical_data(self, days: int = 30) -> Dict[str, List[Dict[str, Any]]]:
        """Generate simulated historical data for charts"""
        base_date = datetime.now() - timedelta(days=days)
        
        price_history = []
        supply_history = []
        staking_history = []
        
        for i in range(days):
            date = base_date + timedelta(days=i)
            
            # Simulate price with some volatility
            base_price = 0.0523
            volatility = math.sin(i * 0.1) * 0.005 + (i * 0.0001)
            price = max(0.01, base_price + volatility)
            
            price_history.append({
                "date": date.strftime("%Y-%m-%d"),
                "price": round(price, 4),
                "volume": round(850_000 + (math.sin(i * 0.2) * 200_000), 0),
                "market_cap": round(self.circulating_supply * price, 2)
            })
            
            # Simulate growing circulating supply
            circulating = min(self.circulating_supply + (i * 100_000), 200_000_000)
            supply_history.append({
                "date": date.strftime("%Y-%m-%d"),
                "circulating_supply": circulating,
                "locked_supply": self.total_supply - circulating,
                "locked_percentage": round(((self.total_supply - circulating) / self.total_supply) * 100, 1)
            })
            
            # Simulate staking growth
            staked = min(25_000_000 + (i * 200_000), 60_000_000)
            staking_history.append({
                "date": date.strftime("%Y-%m-%d"),
                "total_staked": staked,
                "staking_ratio": round((staked / circulating) * 100, 1),
                "apy": round(12.5 + math.sin(i * 0.15) * 2, 1),
                "rewards_distributed": round(staked * 0.125 / 365, 0)
            })
        
        return {
            "price_history": price_history,
            "supply_history": supply_history,
            "staking_history": staking_history
        }

# Initialize tokenomics data
tokenomics = TokenomicsData()

@app.get("/")
async def tokenomics_dashboard():
    """Serve the tokenomics dashboard"""
    return HTMLResponse(content=get_tokenomics_html(), status_code=200)

@app.get("/api/tokenomics/overview")
async def get_tokenomics_overview():
    """Get complete tokenomics overview"""
    return {
        "token_info": {
            "name": tokenomics.token_name,
            "symbol": tokenomics.token_symbol,
            "total_supply": tokenomics.total_supply,
            "circulating_supply": tokenomics.circulating_supply
        },
        "distribution": tokenomics.distribution,
        "utility_mechanisms": tokenomics.utility_mechanisms,
        "metrics": tokenomics.metrics,
        "last_updated": datetime.now().isoformat()
    }

@app.get("/api/tokenomics/distribution")
async def get_token_distribution():
    """Get token distribution breakdown"""
    return {
        "distribution": tokenomics.distribution,
        "total_supply": tokenomics.total_supply,
        "chart_data": [
            {
                "name": key.replace("_", " ").title(),
                "value": data["tokens"],
                "percentage": data["percentage"],
                "locked": data["current_locked"],
                "description": data["description"]
            }
            for key, data in tokenomics.distribution.items()
        ]
    }

@app.get("/api/tokenomics/metrics")
async def get_current_metrics():
    """Get current economic metrics"""
    return tokenomics.metrics

@app.get("/api/tokenomics/historical")
async def get_historical_data(days: int = 30):
    """Get historical tokenomics data"""
    if days > 365:
        raise HTTPException(status_code=400, detail="Maximum 365 days of historical data")
    
    return tokenomics.get_historical_data(days)

@app.get("/api/tokenomics/utility")
async def get_utility_mechanisms():
    """Get token utility mechanisms"""
    return {
        "mechanisms": tokenomics.utility_mechanisms,
        "total_mechanisms": len(tokenomics.utility_mechanisms)
    }

@app.get("/api/tokenomics/projections")
async def get_supply_projections():
    """Get supply release projections"""
    projections = []
    current_date = datetime.now()
    
    # Project next 24 months
    for month in range(24):
        future_date = current_date + timedelta(days=30 * month)
        
        # Simulate gradual supply increase
        additional_supply = month * 2_000_000  # 2M tokens per month
        projected_circulating = min(
            tokenomics.circulating_supply + additional_supply,
            tokenomics.total_supply * 0.6  # Max 60% circulating
        )
        
        projections.append({
            "date": future_date.strftime("%Y-%m"),
            "circulating_supply": projected_circulating,
            "locked_supply": tokenomics.total_supply - projected_circulating,
            "locked_percentage": round(((tokenomics.total_supply - projected_circulating) / tokenomics.total_supply) * 100, 1),
            "estimated_releases": {
                "security_rewards": min(month * 500_000, 30_000_000),
                "team_vesting": min(max(0, (month - 12) * 1_000_000), 15_000_000),
                "ecosystem_partnerships": min(month * 300_000, 15_000_000)
            }
        })
    
    return {
        "projections": projections,
        "assumptions": [
            "Security rewards distributed based on network performance",
            "Team vesting starts after 12-month cliff period",
            "Ecosystem partnerships unlock based on milestones",
            "Community treasury releases require governance approval"
        ]
    }

def get_tokenomics_html():
    """Generate tokenomics dashboard HTML"""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GuardianShield Tokenomics Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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
            border-bottom: 3px solid #3498db;
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
            background: linear-gradient(45deg, #3498db, #9b59b6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2rem;
            font-weight: 700;
        }
        
        .shield-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(45deg, #3498db, #9b59b6);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.5rem;
        }
        
        .dashboard-nav {
            display: flex;
            gap: 1rem;
        }
        
        .nav-btn {
            padding: 0.5rem 1rem;
            background: rgba(52, 152, 219, 0.2);
            border: 1px solid rgba(52, 152, 219, 0.5);
            border-radius: 6px;
            color: #3498db;
            text-decoration: none;
            transition: all 0.3s ease;
        }
        
        .nav-btn:hover {
            background: rgba(52, 152, 219, 0.3);
            transform: translateY(-1px);
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
            background: linear-gradient(45deg, #3498db, #9b59b6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem;
        }
        
        .subtitle {
            color: #bdc3c7;
            font-size: 1.2rem;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 3rem;
        }
        
        .metric-card {
            background: rgba(26, 35, 50, 0.8);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid rgba(52, 152, 219, 0.3);
            backdrop-filter: blur(10px);
        }
        
        .metric-title {
            color: #3498db;
            font-size: 0.9rem;
            font-weight: 600;
            text-transform: uppercase;
            margin-bottom: 0.5rem;
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #27ae60;
            margin-bottom: 0.25rem;
        }
        
        .metric-description {
            color: #95a5a6;
            font-size: 0.9rem;
        }
        
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 2rem;
            margin-bottom: 3rem;
        }
        
        .chart-container {
            background: rgba(26, 35, 50, 0.8);
            border-radius: 16px;
            padding: 2rem;
            border: 1px solid rgba(52, 152, 219, 0.3);
        }
        
        .chart-title {
            color: #3498db;
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 1rem;
            text-align: center;
        }
        
        .distribution-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 3rem;
        }
        
        .distribution-card {
            background: rgba(26, 35, 50, 0.8);
            border-radius: 12px;
            padding: 2rem;
            border: 1px solid rgba(52, 152, 219, 0.3);
        }
        
        .distribution-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        
        .distribution-title {
            color: #3498db;
            font-weight: 600;
            font-size: 1.1rem;
        }
        
        .distribution-percentage {
            background: linear-gradient(45deg, #27ae60, #2ecc71);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9rem;
        }
        
        .distribution-details {
            color: #bdc3c7;
            margin-bottom: 1rem;
            line-height: 1.5;
        }
        
        .distribution-stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin-top: 1rem;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-value {
            font-size: 1.3rem;
            font-weight: 700;
            color: #3498db;
        }
        
        .stat-label {
            font-size: 0.8rem;
            color: #95a5a6;
            text-transform: uppercase;
        }
        
        .utility-section {
            background: rgba(16, 24, 32, 0.9);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 3rem;
        }
        
        .utility-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin-top: 2rem;
        }
        
        .utility-card {
            background: rgba(44, 62, 80, 0.6);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid rgba(155, 89, 182, 0.3);
        }
        
        .utility-title {
            color: #9b59b6;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        .utility-description {
            color: #bdc3c7;
            margin-bottom: 1rem;
            font-size: 0.95rem;
        }
        
        .utility-requirement {
            background: rgba(52, 152, 219, 0.2);
            padding: 0.5rem;
            border-radius: 6px;
            font-size: 0.85rem;
            color: #3498db;
            margin-bottom: 0.5rem;
        }
        
        .utility-rewards {
            background: rgba(39, 174, 96, 0.2);
            padding: 0.5rem;
            border-radius: 6px;
            font-size: 0.85rem;
            color: #27ae60;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(52, 152, 219, 0.3);
            border-radius: 50%;
            border-top-color: #3498db;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        @media (max-width: 768px) {
            .main-content { padding: 1rem; }
            .dashboard-title h2 { font-size: 2rem; }
            .charts-grid { grid-template-columns: 1fr; }
            .header-content { flex-direction: column; gap: 1rem; }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <div class="logo">
                <div class="shield-icon">$</div>
                <h1>Tokenomics Dashboard</h1>
            </div>
            <div class="dashboard-nav">
                <a href="#overview" class="nav-btn">Overview</a>
                <a href="#distribution" class="nav-btn">Distribution</a>
                <a href="#utility" class="nav-btn">Utility</a>
                <a href="#projections" class="nav-btn">Projections</a>
            </div>
        </div>
    </div>
    
    <div class="main-content">
        <div class="dashboard-title">
            <h2>GuardianShield Token Economics</h2>
            <p class="subtitle">Transparent, community-governed, and utility-driven tokenomics</p>
        </div>
        
        <div id="overview" class="metrics-grid">
            <div class="metric-card">
                <div class="metric-title">Total Supply</div>
                <div class="metric-value" id="totalSupply">
                    <span class="loading"></span>
                </div>
                <div class="metric-description">GUARD tokens</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">Circulating Supply</div>
                <div class="metric-value" id="circulatingSupply">
                    <span class="loading"></span>
                </div>
                <div class="metric-description">Currently available</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">Locked Tokens</div>
                <div class="metric-value" id="lockedPercentage">
                    <span class="loading"></span>
                </div>
                <div class="metric-description">Supply locked</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">Market Cap</div>
                <div class="metric-value" id="marketCap">
                    <span class="loading"></span>
                </div>
                <div class="metric-description">USD value</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">Staking APY</div>
                <div class="metric-value" id="stakingApy">
                    <span class="loading"></span>
                </div>
                <div class="metric-description">Average returns</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">Total Staked</div>
                <div class="metric-value" id="totalStaked">
                    <span class="loading"></span>
                </div>
                <div class="metric-description">In security pools</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-container">
                <h3 class="chart-title">Token Distribution</h3>
                <canvas id="distributionChart" width="400" height="300"></canvas>
            </div>
            
            <div class="chart-container">
                <h3 class="chart-title">Supply Release Schedule</h3>
                <canvas id="supplyChart" width="400" height="300"></canvas>
            </div>
        </div>
        
        <div id="distribution" class="distribution-grid">
            <!-- Distribution cards will be populated by JavaScript -->
        </div>
        
        <div id="utility" class="utility-section">
            <h3 style="color: #9b59b6; font-size: 1.8rem; margin-bottom: 1rem; text-align: center;">
                Token Utility Mechanisms
            </h3>
            <p style="text-align: center; color: #bdc3c7; margin-bottom: 2rem;">
                Multiple ways to earn, participate, and grow the ecosystem
            </p>
            
            <div class="utility-grid">
                <!-- Utility cards will be populated by JavaScript -->
            </div>
        </div>
    </div>
    
    <script>
        // Global variables for chart data
        let tokenomicsData = null;
        
        // Load tokenomics data
        async function loadTokenomicsData() {
            try {
                const response = await fetch('/api/tokenomics/overview');
                tokenomicsData = await response.json();
                
                updateMetrics();
                createDistributionChart();
                createSupplyChart();
                renderDistributionCards();
                renderUtilityCards();
                
            } catch (error) {
                console.error('Error loading tokenomics data:', error);
            }
        }
        
        function updateMetrics() {
            if (!tokenomicsData) return;
            
            const metrics = tokenomicsData.metrics;
            
            document.getElementById('totalSupply').textContent = 
                (tokenomicsData.token_info.total_supply / 1000000).toFixed(0) + 'M';
            
            document.getElementById('circulatingSupply').textContent = 
                (tokenomicsData.token_info.circulating_supply / 1000000).toFixed(0) + 'M';
            
            document.getElementById('lockedPercentage').textContent = 
                metrics.market_metrics.locked_percentage + '%';
            
            document.getElementById('marketCap').textContent = 
                '$' + (metrics.market_metrics.market_cap / 1000000).toFixed(1) + 'M';
            
            document.getElementById('stakingApy').textContent = 
                metrics.staking_metrics.average_apy + '%';
            
            document.getElementById('totalStaked').textContent = 
                (metrics.staking_metrics.total_staked / 1000000).toFixed(0) + 'M';
        }
        
        function createDistributionChart() {
            if (!tokenomicsData) return;
            
            const ctx = document.getElementById('distributionChart').getContext('2d');
            const distribution = tokenomicsData.distribution;
            
            const data = Object.keys(distribution).map(key => ({
                label: key.replace(/_/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase()),
                value: distribution[key].percentage,
                color: getColorForCategory(key)
            }));
            
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data.map(d => d.label),
                    datasets: [{
                        data: data.map(d => d.value),
                        backgroundColor: data.map(d => d.color),
                        borderColor: '#1a2332',
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '#e0e6ed',
                                padding: 20,
                                usePointStyle: true
                            }
                        }
                    }
                }
            });
        }
        
        function createSupplyChart() {
            // Simulated supply release data
            const months = [];
            const circulating = [];
            const locked = [];
            
            for (let i = 0; i < 12; i++) {
                const date = new Date();
                date.setMonth(date.getMonth() + i);
                months.push(date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' }));
                
                const circulatingAmount = 150 + (i * 15); // Gradual increase
                circulating.push(circulatingAmount);
                locked.push(1000 - circulatingAmount);
            }
            
            const ctx = document.getElementById('supplyChart').getContext('2d');
            
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: months,
                    datasets: [
                        {
                            label: 'Circulating Supply (M)',
                            data: circulating,
                            borderColor: '#3498db',
                            backgroundColor: 'rgba(52, 152, 219, 0.1)',
                            fill: true,
                            tension: 0.4
                        },
                        {
                            label: 'Locked Supply (M)',
                            data: locked,
                            borderColor: '#9b59b6',
                            backgroundColor: 'rgba(155, 89, 182, 0.1)',
                            fill: true,
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: '#34495e' },
                            ticks: { color: '#bdc3c7' }
                        },
                        x: {
                            grid: { color: '#34495e' },
                            ticks: { color: '#bdc3c7' }
                        }
                    },
                    plugins: {
                        legend: {
                            labels: { color: '#e0e6ed' }
                        }
                    }
                }
            });
        }
        
        function renderDistributionCards() {
            if (!tokenomicsData) return;
            
            const distributionGrid = document.querySelector('.distribution-grid');
            const distribution = tokenomicsData.distribution;
            
            distributionGrid.innerHTML = Object.keys(distribution).map(key => {
                const data = distribution[key];
                const tokensM = (data.tokens / 1000000).toFixed(0);
                const lockedM = (data.current_locked / 1000000).toFixed(0);
                
                return `
                    <div class="distribution-card">
                        <div class="distribution-header">
                            <div class="distribution-title">
                                ${key.replace(/_/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase())}
                            </div>
                            <div class="distribution-percentage">${data.percentage}%</div>
                        </div>
                        <div class="distribution-details">
                            ${data.description}
                        </div>
                        <div class="distribution-stats">
                            <div class="stat-item">
                                <div class="stat-value">${tokensM}M</div>
                                <div class="stat-label">Total Allocated</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-value">${lockedM}M</div>
                                <div class="stat-label">Currently Locked</div>
                            </div>
                        </div>
                        <div style="margin-top: 1rem; padding: 0.75rem; background: rgba(52, 152, 219, 0.1); border-radius: 6px; border-left: 3px solid #3498db;">
                            <strong style="color: #3498db;">Release Schedule:</strong><br>
                            <span style="color: #bdc3c7; font-size: 0.9rem;">${data.release_schedule}</span>
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        function renderUtilityCards() {
            if (!tokenomicsData) return;
            
            const utilityGrid = document.querySelector('.utility-grid');
            const utilities = tokenomicsData.utility_mechanisms;
            
            utilityGrid.innerHTML = Object.keys(utilities).map(key => {
                const data = utilities[key];
                
                return `
                    <div class="utility-card">
                        <h4 class="utility-title">${data.title}</h4>
                        <p class="utility-description">${data.description}</p>
                        <div class="utility-requirement">
                            <strong>Requirement:</strong> ${data.requirement}
                        </div>
                        <div class="utility-rewards">
                            <strong>Rewards:</strong> ${data.rewards}
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        function getColorForCategory(category) {
            const colors = {
                community_treasury: '#3498db',
                security_rewards: '#27ae60',
                initial_distribution: '#e74c3c',
                team_advisors: '#9b59b6',
                ecosystem_partnerships: '#f39c12'
            };
            return colors[category] || '#95a5a6';
        }
        
        // Smooth scrolling for navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(btn.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });
        
        // Initialize dashboard
        loadTokenomicsData();
        
        // Auto-refresh data every 30 seconds
        setInterval(loadTokenomicsData, 30000);
    </script>
</body>
</html>
    '''

if __name__ == "__main__":
    import uvicorn
    
    print("📊 Starting GuardianShield Tokenomics Dashboard...")
    print("💰 Dashboard available at: http://localhost:8004")
    print("📈 API documentation at: http://localhost:8004/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0", 
        port=8004,
        log_level="info"
    )