#!/usr/bin/env python3
"""
GuardianShield Advanced Analytics Dashboard
Comprehensive analytics platform for ecosystem monitoring
"""

import uvicorn
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import random

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Analytics Models
class AnalyticsTimeframe(str):
    HOUR = "1h"
    DAY = "24h" 
    WEEK = "7d"
    MONTH = "30d"
    YEAR = "365d"

@dataclass
class EcosystemMetrics:
    total_users: int
    active_users_24h: int
    total_transactions: int
    total_volume_usd: float
    guard_token_supply: float
    guard_token_price: float
    shield_tokens_minted: int
    nfts_created: int
    staking_pools_active: int
    total_staked_guard: float

@dataclass
class UserBehaviorMetrics:
    new_users_today: int
    returning_users: int
    avg_session_duration: float
    most_popular_feature: str
    user_retention_rate: float
    conversion_rate: float

class AnalyticsDashboard:
    """Advanced analytics and metrics tracking"""
    
    def __init__(self, db_path: str = "analytics.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize analytics database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Daily metrics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_metrics (
                date TEXT PRIMARY KEY,
                total_users INTEGER DEFAULT 0,
                active_users INTEGER DEFAULT 0,
                new_users INTEGER DEFAULT 0,
                total_transactions INTEGER DEFAULT 0,
                total_volume_usd REAL DEFAULT 0,
                guard_price REAL DEFAULT 0,
                shield_tokens_minted INTEGER DEFAULT 0,
                nfts_created INTEGER DEFAULT 0,
                staking_volume REAL DEFAULT 0,
                payment_volume REAL DEFAULT 0
            )
        """)
        
        # Hourly metrics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hourly_metrics (
                datetime TEXT PRIMARY KEY,
                active_users INTEGER DEFAULT 0,
                transactions INTEGER DEFAULT 0,
                volume_usd REAL DEFAULT 0,
                new_signups INTEGER DEFAULT 0,
                shield_mints INTEGER DEFAULT 0,
                nft_creations INTEGER DEFAULT 0
            )
        """)
        
        # User activity tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_activity (
                activity_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                feature TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                session_id TEXT,
                metadata TEXT
            )
        """)
        
        # Feature usage stats
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feature_usage (
                feature TEXT PRIMARY KEY,
                total_uses INTEGER DEFAULT 0,
                unique_users INTEGER DEFAULT 0,
                avg_session_time REAL DEFAULT 0,
                last_used TEXT
            )
        """)
        
        # Performance metrics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                timestamp TEXT PRIMARY KEY,
                response_time_ms REAL DEFAULT 0,
                cpu_usage REAL DEFAULT 0,
                memory_usage REAL DEFAULT 0,
                active_connections INTEGER DEFAULT 0,
                error_rate REAL DEFAULT 0
            )
        """)
        
        # Initialize with sample data
        self.generate_sample_data()
        
        conn.commit()
        conn.close()
    
    def generate_sample_data(self):
        """Generate sample analytics data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Generate last 30 days of data
        for i in range(30):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            
            # Simulate growth over time
            base_users = 1000 + (30-i) * 50
            active_users = int(base_users * (0.6 + random.random() * 0.3))
            new_users = random.randint(20, 100)
            transactions = random.randint(50, 300)
            volume = random.uniform(10000, 50000)
            guard_price = 0.85 + random.uniform(-0.05, 0.05)
            shield_mints = random.randint(5, 25)
            nfts = random.randint(3, 15)
            staking_vol = random.uniform(5000, 25000)
            payment_vol = random.uniform(3000, 15000)
            
            cursor.execute("""
                INSERT OR REPLACE INTO daily_metrics VALUES 
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (date, base_users, active_users, new_users, transactions, 
                  volume, guard_price, shield_mints, nfts, staking_vol, payment_vol))
        
        # Generate hourly data for last 24 hours
        for i in range(24):
            hour = (datetime.now() - timedelta(hours=i)).strftime('%Y-%m-%d %H:00:00')
            
            active_users = random.randint(50, 200)
            transactions = random.randint(5, 30)
            volume = random.uniform(1000, 5000)
            signups = random.randint(1, 10)
            shields = random.randint(1, 5)
            nfts = random.randint(0, 3)
            
            cursor.execute("""
                INSERT OR REPLACE INTO hourly_metrics VALUES 
                (?, ?, ?, ?, ?, ?, ?)
            """, (hour, active_users, transactions, volume, signups, shields, nfts))
        
        # Feature usage data
        features = [
            ('staking', 450, 280, 25.5),
            ('nft_builder', 320, 180, 18.2),
            ('payment_gateway', 280, 150, 12.8),
            ('tokenomics', 380, 220, 8.5),
            ('community', 520, 340, 15.3),
            ('shield_minting', 180, 90, 22.1)
        ]
        
        for feature, uses, users, time in features:
            cursor.execute("""
                INSERT OR REPLACE INTO feature_usage VALUES 
                (?, ?, ?, ?, ?)
            """, (feature, uses, users, time, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_ecosystem_overview(self) -> Dict:
        """Get high-level ecosystem metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get latest daily metrics
        cursor.execute("""
            SELECT * FROM daily_metrics 
            ORDER BY date DESC LIMIT 1
        """)
        latest = cursor.fetchone()
        
        # Get 24h active users
        cursor.execute("""
            SELECT SUM(active_users) FROM hourly_metrics 
            WHERE datetime >= datetime('now', '-24 hours')
        """)
        active_24h = cursor.fetchone()[0] or 0
        
        # Calculate growth rates
        cursor.execute("""
            SELECT total_users, active_users FROM daily_metrics 
            ORDER BY date DESC LIMIT 2
        """)
        growth_data = cursor.fetchall()
        
        user_growth = 0
        if len(growth_data) >= 2:
            user_growth = ((growth_data[0][0] - growth_data[1][0]) / growth_data[1][0]) * 100
        
        # Total volumes
        cursor.execute("""
            SELECT SUM(total_volume_usd), SUM(staking_volume), SUM(payment_volume)
            FROM daily_metrics
        """)
        volumes = cursor.fetchone()
        
        conn.close()
        
        if latest:
            return {
                'total_users': latest[1],
                'active_users_24h': active_24h,
                'user_growth_rate': user_growth,
                'total_transactions': latest[4],
                'total_volume_usd': volumes[0] or 0,
                'guard_token_price': latest[6],
                'shield_tokens_minted': latest[7],
                'nfts_created': latest[8],
                'staking_volume': volumes[1] or 0,
                'payment_volume': volumes[2] or 0,
                'last_updated': datetime.now().isoformat()
            }
        
        return {}
    
    def get_time_series_data(self, metric: str, timeframe: str) -> List[Dict]:
        """Get time series data for charts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if timeframe == "24h":
            cursor.execute(f"""
                SELECT datetime, {metric} FROM hourly_metrics 
                WHERE datetime >= datetime('now', '-24 hours')
                ORDER BY datetime ASC
            """)
        else:
            days = {'7d': 7, '30d': 30, '365d': 365}.get(timeframe, 7)
            
            # Map metric names to table columns
            metric_map = {
                'users': 'active_users',
                'transactions': 'total_transactions', 
                'volume': 'total_volume_usd',
                'guard_price': 'guard_price',
                'shield_mints': 'shield_tokens_minted',
                'nft_creations': 'nfts_created'
            }
            
            db_metric = metric_map.get(metric, metric)
            
            cursor.execute(f"""
                SELECT date, {db_metric} FROM daily_metrics 
                WHERE date >= date('now', '-{days} days')
                ORDER BY date ASC
            """)
        
        data = []
        for row in cursor.fetchall():
            data.append({
                'timestamp': row[0],
                'value': row[1] or 0
            })
        
        conn.close()
        return data
    
    def get_feature_analytics(self) -> List[Dict]:
        """Get feature usage analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT feature, total_uses, unique_users, avg_session_time
            FROM feature_usage
            ORDER BY total_uses DESC
        """)
        
        features = []
        for row in cursor.fetchall():
            features.append({
                'feature': row[0],
                'total_uses': row[1],
                'unique_users': row[2],
                'avg_session_time': row[3],
                'engagement_rate': (row[1] / row[2]) if row[2] > 0 else 0
            })
        
        conn.close()
        return features
    
    def get_user_behavior_insights(self) -> Dict:
        """Get user behavior insights"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # New users today
        cursor.execute("""
            SELECT new_users FROM daily_metrics 
            WHERE date = date('now')
        """)
        new_users = cursor.fetchone()
        new_users = new_users[0] if new_users else 0
        
        # Most popular feature
        cursor.execute("""
            SELECT feature FROM feature_usage 
            ORDER BY total_uses DESC LIMIT 1
        """)
        popular_feature = cursor.fetchone()
        popular_feature = popular_feature[0] if popular_feature else 'staking'
        
        # Average session time across all features
        cursor.execute("""
            SELECT AVG(avg_session_time) FROM feature_usage
        """)
        avg_session = cursor.fetchone()[0] or 0
        
        # Calculate retention rate (simplified)
        cursor.execute("""
            SELECT AVG(active_users * 1.0 / total_users) * 100 
            FROM daily_metrics 
            WHERE date >= date('now', '-7 days')
        """)
        retention_rate = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'new_users_today': new_users,
            'returning_users': random.randint(150, 300),  # Simulated
            'avg_session_duration': avg_session,
            'most_popular_feature': popular_feature,
            'user_retention_rate': retention_rate,
            'conversion_rate': random.uniform(2.5, 4.8)  # Simulated
        }
    
    def get_real_time_metrics(self) -> Dict:
        """Get real-time dashboard metrics"""
        # Simulate real-time data
        return {
            'active_users_now': random.randint(80, 150),
            'transactions_last_hour': random.randint(15, 45),
            'volume_last_hour': random.uniform(2000, 8000),
            'new_shield_tokens': random.randint(2, 8),
            'new_nfts': random.randint(1, 5),
            'server_response_time': random.uniform(120, 280),
            'system_health': random.uniform(85, 98)
        }

# Initialize FastAPI app and analytics
app = FastAPI(title="GuardianShield Analytics Dashboard", version="2.0.0")
analytics = AnalyticsDashboard()

@app.get("/", response_class=HTMLResponse)
async def analytics_dashboard():
    """Serve the Advanced Analytics Dashboard"""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GuardianShield Analytics Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            
            body {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #0a0e1a 0%, #1a2332 50%, #2d3e50 100%);
                color: #e0e6ed;
                min-height: 100vh;
                line-height: 1.6;
            }}
            
            .header {{
                background: linear-gradient(135deg, #2c3e50, #34495e);
                padding: 1.5rem 0;
                border-bottom: 3px solid #9b59b6;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            }}
            
            .header-content {{
                max-width: 1400px;
                margin: 0 auto;
                padding: 0 2rem;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }}
            
            .logo {{
                display: flex;
                align-items: center;
                gap: 1rem;
            }}
            
            .analytics-icon {{
                width: 50px;
                height: 50px;
                background: linear-gradient(45deg, #9b59b6, #8e44ad);
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.5rem;
                font-weight: bold;
                color: white;
                box-shadow: 0 4px 15px rgba(155, 89, 182, 0.3);
            }}
            
            .logo h1 {{
                color: #ecf0f1;
                font-size: 1.8rem;
                font-weight: 600;
            }}
            
            .real-time-indicator {{
                display: flex;
                align-items: center;
                gap: 0.5rem;
                background: rgba(39, 174, 96, 0.2);
                padding: 0.5rem 1rem;
                border-radius: 20px;
                border: 1px solid #27ae60;
            }}
            
            .pulse {{
                width: 10px;
                height: 10px;
                background: #27ae60;
                border-radius: 50%;
                animation: pulse 2s infinite;
            }}
            
            @keyframes pulse {{
                0% {{ opacity: 1; transform: scale(1); }}
                50% {{ opacity: 0.7; transform: scale(1.1); }}
                100% {{ opacity: 1; transform: scale(1); }}
            }}
            
            .main-content {{
                max-width: 1400px;
                margin: 0 auto;
                padding: 2rem;
            }}
            
            .dashboard-grid {{
                display: grid;
                gap: 2rem;
                margin-bottom: 3rem;
            }}
            
            .overview-section {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1.5rem;
                margin-bottom: 2rem;
            }}
            
            .metric-card {{
                background: linear-gradient(135deg, rgba(26, 35, 50, 0.8), rgba(44, 62, 80, 0.6));
                border-radius: 15px;
                padding: 1.5rem;
                border: 1px solid rgba(155, 89, 182, 0.3);
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }}
            
            .metric-card:hover {{
                transform: translateY(-3px);
                box-shadow: 0 8px 25px rgba(155, 89, 182, 0.3);
                border-color: #9b59b6;
            }}
            
            .metric-icon {{
                font-size: 2rem;
                margin-bottom: 1rem;
                opacity: 0.8;
            }}
            
            .metric-value {{
                font-size: 2.2rem;
                font-weight: bold;
                color: #9b59b6;
                margin-bottom: 0.5rem;
            }}
            
            .metric-label {{
                color: #bdc3c7;
                font-size: 0.9rem;
                font-weight: 500;
            }}
            
            .metric-change {{
                position: absolute;
                top: 1rem;
                right: 1rem;
                padding: 0.3rem 0.8rem;
                border-radius: 15px;
                font-size: 0.8rem;
                font-weight: 600;
            }}
            
            .change-positive {{
                background: rgba(39, 174, 96, 0.2);
                color: #27ae60;
                border: 1px solid #27ae60;
            }}
            
            .change-negative {{
                background: rgba(231, 76, 60, 0.2);
                color: #e74c3c;
                border: 1px solid #e74c3c;
            }}
            
            .charts-section {{
                display: grid;
                grid-template-columns: 2fr 1fr;
                gap: 2rem;
                margin-bottom: 3rem;
            }}
            
            .chart-container {{
                background: linear-gradient(135deg, rgba(26, 35, 50, 0.8), rgba(44, 62, 80, 0.6));
                border-radius: 15px;
                padding: 2rem;
                border: 1px solid rgba(155, 89, 182, 0.3);
            }}
            
            .chart-title {{
                color: #9b59b6;
                font-size: 1.3rem;
                font-weight: 600;
                margin-bottom: 1rem;
                text-align: center;
            }}
            
            .chart-controls {{
                display: flex;
                justify-content: center;
                gap: 0.5rem;
                margin-bottom: 1.5rem;
            }}
            
            .control-button {{
                padding: 0.5rem 1rem;
                background: rgba(155, 89, 182, 0.2);
                border: 1px solid #9b59b6;
                border-radius: 20px;
                color: #9b59b6;
                cursor: pointer;
                transition: all 0.3s ease;
                font-size: 0.85rem;
            }}
            
            .control-button.active {{
                background: #9b59b6;
                color: white;
            }}
            
            .control-button:hover {{
                background: rgba(155, 89, 182, 0.4);
            }}
            
            .features-section {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 2rem;
            }}
            
            .feature-item {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 1rem;
                background: rgba(52, 73, 94, 0.4);
                border-radius: 8px;
                margin-bottom: 0.5rem;
                transition: all 0.3s ease;
            }}
            
            .feature-item:hover {{
                background: rgba(155, 89, 182, 0.2);
                transform: translateX(5px);
            }}
            
            .feature-name {{
                font-weight: 600;
                color: #ecf0f1;
            }}
            
            .feature-stats {{
                display: flex;
                gap: 1rem;
                font-size: 0.9rem;
                color: #bdc3c7;
            }}
            
            .real-time-section {{
                background: linear-gradient(135deg, #1e3c72, #2a5298);
                border-radius: 15px;
                padding: 2rem;
                border: 2px solid #3498db;
                margin-bottom: 2rem;
            }}
            
            .real-time-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1.5rem;
            }}
            
            .real-time-metric {{
                text-align: center;
                padding: 1rem;
                background: rgba(52, 152, 219, 0.1);
                border-radius: 10px;
                border: 1px solid rgba(52, 152, 219, 0.3);
            }}
            
            .real-time-value {{
                font-size: 1.8rem;
                font-weight: bold;
                color: #3498db;
                margin-bottom: 0.5rem;
            }}
            
            .real-time-label {{
                color: #bdc3c7;
                font-size: 0.9rem;
            }}
            
            @media (max-width: 1024px) {{
                .charts-section {{
                    grid-template-columns: 1fr;
                }}
                
                .features-section {{
                    grid-template-columns: 1fr;
                }}
                
                .overview-section {{
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                }}
            }}
            
            @media (max-width: 768px) {{
                .main-content {{
                    padding: 1rem;
                }}
                
                .header-content {{
                    padding: 0 1rem;
                    flex-direction: column;
                    gap: 1rem;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <div class="logo">
                    <div class="analytics-icon">📊</div>
                    <h1>Advanced Analytics Dashboard</h1>
                </div>
                <div class="real-time-indicator">
                    <div class="pulse"></div>
                    <span>Live Data</span>
                </div>
            </div>
        </div>
        
        <div class="main-content">
            <div class="real-time-section">
                <h2 class="chart-title">🔴 Real-Time Metrics</h2>
                <div class="real-time-grid" id="realTimeGrid">
                    <!-- Real-time metrics will be populated here -->
                </div>
            </div>
            
            <div class="overview-section" id="overviewSection">
                <!-- Overview metrics will be populated here -->
            </div>
            
            <div class="charts-section">
                <div class="chart-container">
                    <h3 class="chart-title">📈 Ecosystem Growth Trends</h3>
                    <div class="chart-controls">
                        <button class="control-button active" onclick="changeTimeframe('24h')">24H</button>
                        <button class="control-button" onclick="changeTimeframe('7d')">7D</button>
                        <button class="control-button" onclick="changeTimeframe('30d')">30D</button>
                    </div>
                    <canvas id="mainChart" width="400" height="200"></canvas>
                </div>
                
                <div class="chart-container">
                    <h3 class="chart-title">🎯 Feature Usage</h3>
                    <canvas id="featureChart" width="400" height="200"></canvas>
                </div>
            </div>
            
            <div class="features-section">
                <div class="chart-container">
                    <h3 class="chart-title">🔧 Feature Analytics</h3>
                    <div id="featuresList">
                        <!-- Feature analytics will be populated here -->
                    </div>
                </div>
                
                <div class="chart-container">
                    <h3 class="chart-title">👥 User Behavior Insights</h3>
                    <div id="userInsights">
                        <!-- User insights will be populated here -->
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let mainChart, featureChart;
            let currentTimeframe = '24h';
            
            // Initialize charts
            function initCharts() {{
                const ctx1 = document.getElementById('mainChart').getContext('2d');
                mainChart = new Chart(ctx1, {{
                    type: 'line',
                    data: {{
                        labels: [],
                        datasets: [{{
                            label: 'Active Users',
                            data: [],
                            borderColor: '#9b59b6',
                            backgroundColor: 'rgba(155, 89, 182, 0.1)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                labels: {{
                                    color: '#ecf0f1'
                                }}
                            }}
                        }},
                        scales: {{
                            x: {{
                                ticks: {{
                                    color: '#bdc3c7'
                                }},
                                grid: {{
                                    color: 'rgba(189, 195, 199, 0.1)'
                                }}
                            }},
                            y: {{
                                ticks: {{
                                    color: '#bdc3c7'
                                }},
                                grid: {{
                                    color: 'rgba(189, 195, 199, 0.1)'
                                }}
                            }}
                        }}
                    }}
                }});
                
                const ctx2 = document.getElementById('featureChart').getContext('2d');
                featureChart = new Chart(ctx2, {{
                    type: 'doughnut',
                    data: {{
                        labels: [],
                        datasets: [{{
                            data: [],
                            backgroundColor: [
                                '#9b59b6', '#3498db', '#27ae60', 
                                '#f39c12', '#e74c3c', '#1abc9c'
                            ],
                            borderWidth: 0
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                position: 'bottom',
                                labels: {{
                                    color: '#ecf0f1',
                                    padding: 20
                                }}
                            }}
                        }}
                    }}
                }});
            }}
            
            // Load real-time metrics
            async function loadRealTimeMetrics() {{
                try {{
                    const response = await fetch('/api/analytics/realtime');
                    const data = await response.json();
                    
                    const grid = document.getElementById('realTimeGrid');
                    grid.innerHTML = `
                        <div class="real-time-metric">
                            <div class="real-time-value">${{data.active_users_now}}</div>
                            <div class="real-time-label">Active Users</div>
                        </div>
                        <div class="real-time-metric">
                            <div class="real-time-value">${{data.transactions_last_hour}}</div>
                            <div class="real-time-label">Transactions/Hour</div>
                        </div>
                        <div class="real-time-metric">
                            <div class="real-time-value">$${{data.volume_last_hour.toLocaleString()}}</div>
                            <div class="real-time-label">Volume/Hour</div>
                        </div>
                        <div class="real-time-metric">
                            <div class="real-time-value">${{data.new_shield_tokens}}</div>
                            <div class="real-time-label">New SHIELD Tokens</div>
                        </div>
                        <div class="real-time-metric">
                            <div class="real-time-value">${{data.new_nfts}}</div>
                            <div class="real-time-label">New NFTs</div>
                        </div>
                        <div class="real-time-metric">
                            <div class="real-time-value">${{data.server_response_time.toFixed(0)}}ms</div>
                            <div class="real-time-label">Response Time</div>
                        </div>
                    `;
                }} catch (error) {{
                    console.error('Error loading real-time metrics:', error);
                }}
            }}
            
            // Load overview metrics
            async function loadOverviewMetrics() {{
                try {{
                    const response = await fetch('/api/analytics/overview');
                    const data = await response.json();
                    
                    const section = document.getElementById('overviewSection');
                    section.innerHTML = `
                        <div class="metric-card">
                            <div class="metric-icon">👥</div>
                            <div class="metric-value">${{data.total_users?.toLocaleString() || 0}}</div>
                            <div class="metric-label">Total Users</div>
                            <div class="metric-change change-positive">+${{data.user_growth_rate?.toFixed(1) || 0}}%</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-icon">⚡</div>
                            <div class="metric-value">${{data.active_users_24h?.toLocaleString() || 0}}</div>
                            <div class="metric-label">Active 24H</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-icon">💰</div>
                            <div class="metric-value">$${{data.total_volume_usd?.toLocaleString() || 0}}</div>
                            <div class="metric-label">Total Volume</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-icon">🛡️</div>
                            <div class="metric-value">${{data.shield_tokens_minted?.toLocaleString() || 0}}</div>
                            <div class="metric-label">SHIELD Tokens</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-icon">🎨</div>
                            <div class="metric-value">${{data.nfts_created?.toLocaleString() || 0}}</div>
                            <div class="metric-label">NFTs Created</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-icon">📊</div>
                            <div class="metric-value">${{data.total_transactions?.toLocaleString() || 0}}</div>
                            <div class="metric-label">Transactions</div>
                        </div>
                    `;
                }} catch (error) {{
                    console.error('Error loading overview metrics:', error);
                }}
            }}
            
            // Load time series data
            async function loadTimeSeriesData(timeframe = '24h') {{
                try {{
                    const response = await fetch(`/api/analytics/timeseries/users?timeframe=${{timeframe}}`);
                    const data = await response.json();
                    
                    const labels = data.map(item => {{
                        const date = new Date(item.timestamp);
                        return timeframe === '24h' ? 
                            date.toLocaleTimeString([], {{hour: '2-digit', minute: '2-digit'}}) :
                            date.toLocaleDateString();
                    }});
                    
                    const values = data.map(item => item.value);
                    
                    mainChart.data.labels = labels;
                    mainChart.data.datasets[0].data = values;
                    mainChart.update();
                }} catch (error) {{
                    console.error('Error loading time series data:', error);
                }}
            }}
            
            // Load feature analytics
            async function loadFeatureAnalytics() {{
                try {{
                    const response = await fetch('/api/analytics/features');
                    const data = await response.json();
                    
                    // Update doughnut chart
                    featureChart.data.labels = data.map(f => f.feature.replace('_', ' ').toUpperCase());
                    featureChart.data.datasets[0].data = data.map(f => f.total_uses);
                    featureChart.update();
                    
                    // Update features list
                    const list = document.getElementById('featuresList');
                    list.innerHTML = data.map(feature => `
                        <div class="feature-item">
                            <div class="feature-name">${{feature.feature.replace('_', ' ').toUpperCase()}}</div>
                            <div class="feature-stats">
                                <span>${{feature.total_uses}} uses</span>
                                <span>${{feature.unique_users}} users</span>
                                <span>${{feature.avg_session_time.toFixed(1)}}min</span>
                            </div>
                        </div>
                    `).join('');
                }} catch (error) {{
                    console.error('Error loading feature analytics:', error);
                }}
            }}
            
            // Load user insights
            async function loadUserInsights() {{
                try {{
                    const response = await fetch('/api/analytics/behavior');
                    const data = await response.json();
                    
                    const insights = document.getElementById('userInsights');
                    insights.innerHTML = `
                        <div class="feature-item">
                            <div class="feature-name">New Users Today</div>
                            <div class="feature-stats">${{data.new_users_today}}</div>
                        </div>
                        <div class="feature-item">
                            <div class="feature-name">Returning Users</div>
                            <div class="feature-stats">${{data.returning_users}}</div>
                        </div>
                        <div class="feature-item">
                            <div class="feature-name">Avg Session Time</div>
                            <div class="feature-stats">${{data.avg_session_duration.toFixed(1)}} min</div>
                        </div>
                        <div class="feature-item">
                            <div class="feature-name">Top Feature</div>
                            <div class="feature-stats">${{data.most_popular_feature.replace('_', ' ').toUpperCase()}}</div>
                        </div>
                        <div class="feature-item">
                            <div class="feature-name">Retention Rate</div>
                            <div class="feature-stats">${{data.user_retention_rate.toFixed(1)}}%</div>
                        </div>
                        <div class="feature-item">
                            <div class="feature-name">Conversion Rate</div>
                            <div class="feature-stats">${{data.conversion_rate.toFixed(1)}}%</div>
                        </div>
                    `;
                }} catch (error) {{
                    console.error('Error loading user insights:', error);
                }}
            }}
            
            // Change timeframe
            function changeTimeframe(timeframe) {{
                currentTimeframe = timeframe;
                
                // Update active button
                document.querySelectorAll('.control-button').forEach(btn => {{
                    btn.classList.remove('active');
                }});
                event.target.classList.add('active');
                
                // Reload chart data
                loadTimeSeriesData(timeframe);
            }}
            
            // Initialize dashboard
            function initDashboard() {{
                initCharts();
                loadRealTimeMetrics();
                loadOverviewMetrics();
                loadTimeSeriesData();
                loadFeatureAnalytics();
                loadUserInsights();
                
                // Auto-refresh real-time metrics every 10 seconds
                setInterval(loadRealTimeMetrics, 10000);
                
                // Refresh other data every 60 seconds
                setInterval(() => {{
                    loadOverviewMetrics();
                    loadTimeSeriesData(currentTimeframe);
                    loadFeatureAnalytics();
                    loadUserInsights();
                }}, 60000);
            }}
            
            // Start dashboard when page loads
            window.addEventListener('load', initDashboard);
        </script>
    </body>
    </html>
    """

@app.get("/api/analytics/overview")
async def get_ecosystem_overview():
    """Get ecosystem overview metrics"""
    try:
        overview = analytics.get_ecosystem_overview()
        return overview
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/timeseries/{metric}")
async def get_time_series_data(metric: str, timeframe: str = "24h"):
    """Get time series data for charts"""
    try:
        data = analytics.get_time_series_data(metric, timeframe)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/features")
async def get_feature_analytics():
    """Get feature usage analytics"""
    try:
        features = analytics.get_feature_analytics()
        return features
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/behavior")
async def get_user_behavior():
    """Get user behavior insights"""
    try:
        behavior = analytics.get_user_behavior_insights()
        return behavior
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/realtime")
async def get_real_time_metrics():
    """Get real-time metrics"""
    try:
        metrics = analytics.get_real_time_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("📊 Starting GuardianShield Advanced Analytics Dashboard...")
    print("🚀 Dashboard available at: http://localhost:8009")
    print("📈 API documentation at: http://localhost:8009/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0", 
        port=8009,
        log_level="info"
    )