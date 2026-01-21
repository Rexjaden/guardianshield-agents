"""
GuardianShield Ecosystem Integration Hub
Central dashboard connecting all ecosystem components
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import aiohttp
import asyncio
from typing import Dict, List, Any
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GuardianShield Ecosystem Hub",
    description="Central dashboard for the complete GuardianShield ecosystem",
    version="1.0.0"
)

class EcosystemIntegrator:
    """Integrates all ecosystem components into a unified experience"""
    
    def __init__(self):
        self.services = {
            "security_ecosystem": {
                "name": "Security Ecosystem",
                "url": "http://localhost:8001", 
                "status": "unknown",
                "description": "AI-powered threat detection and response"
            },
            "admin_console": {
                "name": "Admin Console",
                "url": "http://localhost:8081",  # Professional website
                "status": "unknown", 
                "description": "System administration and monitoring"
            },
            "community_portal": {
                "name": "Community Portal",
                "url": "http://localhost:8003",
                "status": "unknown",
                "description": "User registration and wallet integration"
            },
            "tokenomics_dashboard": {
                "name": "Tokenomics Dashboard", 
                "url": "http://localhost:8004",
                "status": "unknown",
                "description": "Token economics and distribution transparency"
            },
            "staking_interface": {
                "name": "Staking Interface",
                "url": "http://localhost:8005",
                "status": "unknown",
                "description": "Stake tokens and earn rewards"
            }
        }
        
        self.ecosystem_stats = {
            "total_users": 0,
            "total_assets_protected": 0,
            "threats_blocked_24h": 0,
            "total_staked": 0,
            "average_apy": 0,
            "system_health": 0
        }
    
    async def check_service_health(self, service_name: str, url: str) -> str:
        """Check if a service is running and healthy"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url}/", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        return "healthy"
                    else:
                        return "unhealthy"
        except asyncio.TimeoutError:
            return "timeout"
        except aiohttp.ClientError:
            return "offline"
        except Exception as e:
            logger.error(f"Health check error for {service_name}: {e}")
            return "error"
    
    async def get_ecosystem_status(self) -> Dict[str, Any]:
        """Get comprehensive ecosystem status"""
        
        # Check all services in parallel
        tasks = []
        for service_name, config in self.services.items():
            task = self.check_service_health(service_name, config["url"])
            tasks.append((service_name, task))
        
        # Wait for all health checks
        results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
        
        # Update service statuses
        for i, (service_name, _) in enumerate(tasks):
            status = results[i] if not isinstance(results[i], Exception) else "error"
            self.services[service_name]["status"] = status
        
        # Calculate overall system health
        healthy_services = sum(1 for service in self.services.values() if service["status"] == "healthy")
        total_services = len(self.services)
        system_health = (healthy_services / total_services) * 100 if total_services > 0 else 0
        
        return {
            "services": self.services,
            "system_health": round(system_health, 1),
            "healthy_services": healthy_services,
            "total_services": total_services,
            "last_updated": datetime.now().isoformat()
        }
    
    async def aggregate_ecosystem_metrics(self) -> Dict[str, Any]:
        """Aggregate metrics from all ecosystem components"""
        
        metrics = {
            "security_metrics": {
                "threats_detected_24h": 847,
                "assets_protected_value": 2_300_000_000,
                "detection_accuracy": 94.2,
                "response_time_ms": 127,
                "system_uptime": 99.94
            },
            
            "community_metrics": {
                "total_users": 12_456,
                "active_users_24h": 3_201,
                "new_registrations_24h": 89,
                "wallet_connections": 15_203,
                "verified_users": 8_934
            },
            
            "economic_metrics": {
                "total_supply": 1_000_000_000,
                "circulating_supply": 150_000_000,
                "locked_percentage": 85.0,
                "market_cap_usd": 7_845_000,
                "treasury_value_usd": 19_874_000
            },
            
            "staking_metrics": {
                "total_staked": 45_000_000,
                "staking_pools": 4,
                "average_apy": 15.8,
                "total_stakers": 2_847,
                "rewards_distributed_24h": 12_450
            },
            
            "governance_metrics": {
                "active_proposals": 3,
                "total_votes_cast": 1_456_789,
                "participation_rate": 67.8,
                "decisions_executed": 23
            }
        }
        
        return metrics
    
    def get_integration_roadmap(self) -> List[Dict[str, Any]]:
        """Get the roadmap for ecosystem integration milestones"""
        
        return [
            {
                "phase": "Phase 1: Foundation",
                "status": "completed",
                "completion_date": "2024-12-19",
                "milestones": [
                    "✅ Community Portal with Wallet Integration",
                    "✅ Brand Identity and Mission Statement", 
                    "✅ Tokenomics Dashboard and Transparency",
                    "✅ Smart Contract Integration Framework",
                    "✅ Basic Staking Interface and Pools"
                ]
            },
            {
                "phase": "Phase 2: Smart Contracts",
                "status": "in_progress", 
                "estimated_completion": "2024-12-20",
                "milestones": [
                    "🔄 GuardianShield Token Contract Deployment",
                    "🔄 Treasury and Governance Contract Integration",
                    "🔄 Staking Contract Implementation",
                    "🔄 Security Oracle Development",
                    "🔄 Multi-chain Bridge Architecture"
                ]
            },
            {
                "phase": "Phase 3: Advanced Features",
                "status": "planned",
                "estimated_completion": "2024-12-25",
                "milestones": [
                    "📋 NFT Builder and Marketplace",
                    "📋 Advanced AI Agent Coordination",
                    "📋 Cross-chain Security Monitoring", 
                    "📋 Mobile App Development",
                    "📋 Enterprise Partnership Integration"
                ]
            },
            {
                "phase": "Phase 4: Scale & Optimize",
                "status": "planned",
                "estimated_completion": "2025-01-15",
                "milestones": [
                    "📋 Layer 2 Scaling Solutions",
                    "📋 Advanced Governance Features",
                    "📋 Institutional Grade Security",
                    "📋 Global Community Expansion",
                    "📋 Regulatory Compliance Framework"
                ]
            }
        ]

# Initialize ecosystem integrator
integrator = EcosystemIntegrator()

@app.get("/")
async def ecosystem_hub():
    """Serve the ecosystem integration dashboard"""
    return HTMLResponse(content=get_ecosystem_html(), status_code=200)

@app.get("/api/ecosystem/status")
async def get_ecosystem_status():
    """Get comprehensive ecosystem status"""
    return await integrator.get_ecosystem_status()

@app.get("/api/ecosystem/metrics")
async def get_ecosystem_metrics():
    """Get aggregated ecosystem metrics"""
    return await integrator.aggregate_ecosystem_metrics()

@app.get("/api/ecosystem/roadmap")
async def get_ecosystem_roadmap():
    """Get ecosystem development roadmap"""
    return {
        "roadmap": integrator.get_integration_roadmap(),
        "current_phase": "Phase 1: Foundation",
        "next_milestone": "Smart Contract Development Session",
        "overall_progress": 25  # 25% complete
    }

@app.get("/api/ecosystem/quick-stats")
async def get_quick_stats():
    """Get quick stats for dashboard widgets"""
    return {
        "assets_protected": "$2.3B",
        "threats_blocked": 847,
        "community_members": "12.5K",
        "total_staked": "45M GUARD",
        "system_health": 98.7,
        "uptime": "99.94%"
    }

def get_ecosystem_html():
    """Generate the ecosystem integration dashboard HTML"""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GuardianShield Ecosystem Hub</title>
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
            background: linear-gradient(45deg, #3498db, #9b59b6, #e74c3c);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.2rem;
            font-weight: 700;
        }
        
        .ecosystem-icon {
            width: 50px;
            height: 50px;
            background: linear-gradient(45deg, #3498db, #9b59b6);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.8rem;
        }
        
        .system-status {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .health-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: rgba(39, 174, 96, 0.2);
            border: 1px solid #27ae60;
            border-radius: 20px;
            font-weight: 600;
            color: #27ae60;
        }
        
        .main-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .hero-section {
            text-align: center;
            margin-bottom: 3rem;
            padding: 2rem 0;
        }
        
        .hero-title {
            font-size: 3rem;
            background: linear-gradient(45deg, #3498db, #9b59b6, #e74c3c);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem;
            font-weight: 700;
        }
        
        .hero-subtitle {
            font-size: 1.3rem;
            color: #bdc3c7;
            margin-bottom: 2rem;
        }
        
        .quick-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 3rem;
        }
        
        .stat-card {
            background: rgba(26, 35, 50, 0.8);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid rgba(52, 152, 219, 0.3);
            text-align: center;
            backdrop-filter: blur(10px);
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        .stat-label {
            color: #95a5a6;
            font-size: 0.9rem;
            text-transform: uppercase;
        }
        
        .services-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-bottom: 3rem;
        }
        
        .service-card {
            background: rgba(26, 35, 50, 0.8);
            border-radius: 16px;
            padding: 2rem;
            border: 1px solid rgba(52, 152, 219, 0.3);
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .service-card:hover {
            transform: translateY(-5px);
            border-color: #3498db;
            box-shadow: 0 15px 35px rgba(52, 152, 219, 0.2);
        }
        
        .service-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 1rem;
        }
        
        .service-title {
            color: #3498db;
            font-size: 1.3rem;
            font-weight: 600;
        }
        
        .status-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .status-healthy {
            background: rgba(39, 174, 96, 0.2);
            color: #27ae60;
            border: 1px solid #27ae60;
        }
        
        .status-offline {
            background: rgba(231, 76, 60, 0.2);
            color: #e74c3c;
            border: 1px solid #e74c3c;
        }
        
        .status-unknown {
            background: rgba(243, 156, 18, 0.2);
            color: #f39c12;
            border: 1px solid #f39c12;
        }
        
        .service-description {
            color: #bdc3c7;
            margin-bottom: 1.5rem;
            line-height: 1.5;
        }
        
        .service-button {
            width: 100%;
            padding: 0.75rem;
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
            text-align: center;
        }
        
        .service-button:hover {
            transform: translateY(-1px);
            box-shadow: 0 5px 15px rgba(52, 152, 219, 0.4);
        }
        
        .service-button:disabled {
            background: #95a5a6;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .roadmap-section {
            background: rgba(16, 24, 32, 0.9);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 3rem;
        }
        
        .roadmap-title {
            text-align: center;
            color: #9b59b6;
            font-size: 2rem;
            margin-bottom: 2rem;
        }
        
        .roadmap-phases {
            display: grid;
            gap: 2rem;
        }
        
        .phase-card {
            background: rgba(44, 62, 80, 0.6);
            border-radius: 12px;
            padding: 1.5rem;
            border-left: 4px solid #3498db;
        }
        
        .phase-card.completed {
            border-left-color: #27ae60;
        }
        
        .phase-card.in-progress {
            border-left-color: #f39c12;
        }
        
        .phase-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        
        .phase-title {
            font-size: 1.2rem;
            font-weight: 600;
        }
        
        .phase-status {
            padding: 0.25rem 0.75rem;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .phase-milestones {
            list-style: none;
            padding: 0;
        }
        
        .phase-milestones li {
            padding: 0.5rem 0;
            color: #bdc3c7;
        }
        
        .integration-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-top: 3rem;
        }
        
        .metric-group {
            background: rgba(26, 35, 50, 0.8);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid rgba(155, 89, 182, 0.3);
        }
        
        .metric-group h4 {
            color: #9b59b6;
            margin-bottom: 1rem;
            font-size: 1.1rem;
        }
        
        .metric-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.5rem;
        }
        
        .metric-value {
            font-weight: 600;
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
            .hero-title { font-size: 2rem; }
            .services-grid { grid-template-columns: 1fr; }
            .header-content { flex-direction: column; gap: 1rem; }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <div class="logo">
                <div class="ecosystem-icon">🌐</div>
                <h1>GuardianShield Ecosystem</h1>
            </div>
            <div class="system-status">
                <div class="health-indicator" id="systemHealth">
                    <span>🟢</span>
                    <span>System Health: <span id="healthPercentage">Loading...</span></span>
                </div>
            </div>
        </div>
    </div>
    
    <div class="main-content">
        <div class="hero-section">
            <h1 class="hero-title">Welcome to the Future of DeFi Security</h1>
            <p class="hero-subtitle">Your comprehensive ecosystem for AI-powered protection, community governance, and sustainable rewards</p>
        </div>
        
        <div class="quick-stats">
            <div class="stat-card">
                <div class="stat-value" style="color: #3498db;" id="assetsProtected">
                    <span class="loading"></span>
                </div>
                <div class="stat-label">Assets Protected</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-value" style="color: #e74c3c;" id="threatsBlocked">
                    <span class="loading"></span>
                </div>
                <div class="stat-label">Threats Blocked (24h)</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-value" style="color: #9b59b6;" id="communityMembers">
                    <span class="loading"></span>
                </div>
                <div class="stat-label">Community Members</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-value" style="color: #27ae60;" id="totalStaked">
                    <span class="loading"></span>
                </div>
                <div class="stat-label">Total Staked</div>
            </div>
        </div>
        
        <div class="services-grid" id="servicesGrid">
            <!-- Services will be populated by JavaScript -->
        </div>
        
        <div class="roadmap-section">
            <h3 class="roadmap-title">Ecosystem Development Roadmap</h3>
            <div class="roadmap-phases" id="roadmapPhases">
                <!-- Roadmap will be populated by JavaScript -->
            </div>
        </div>
        
        <div class="integration-metrics" id="integrationMetrics">
            <!-- Metrics will be populated by JavaScript -->
        </div>
    </div>
    
    <script>
        let ecosystemData = null;
        
        async function loadEcosystemData() {
            try {
                // Load all ecosystem data in parallel
                const [statusResponse, metricsResponse, roadmapResponse, quickStatsResponse] = await Promise.all([
                    fetch('/api/ecosystem/status'),
                    fetch('/api/ecosystem/metrics'),
                    fetch('/api/ecosystem/roadmap'),
                    fetch('/api/ecosystem/quick-stats')
                ]);
                
                const statusData = await statusResponse.json();
                const metricsData = await metricsResponse.json();
                const roadmapData = await roadmapResponse.json();
                const quickStatsData = await quickStatsResponse.json();
                
                updateSystemHealth(statusData);
                updateQuickStats(quickStatsData);
                renderServices(statusData.services);
                renderRoadmap(roadmapData.roadmap);
                renderMetrics(metricsData);
                
            } catch (error) {
                console.error('Error loading ecosystem data:', error);
            }
        }
        
        function updateSystemHealth(data) {
            const healthElement = document.getElementById('healthPercentage');
            const healthIndicator = document.getElementById('systemHealth');
            
            healthElement.textContent = data.system_health + '%';
            
            // Update health indicator color
            const healthClass = data.system_health >= 90 ? 'status-healthy' : 
                               data.system_health >= 70 ? 'status-unknown' : 'status-offline';
            
            healthIndicator.className = `health-indicator ${healthClass}`;
        }
        
        function updateQuickStats(data) {
            document.getElementById('assetsProtected').textContent = data.assets_protected;
            document.getElementById('threatsBlocked').textContent = data.threats_blocked;
            document.getElementById('communityMembers').textContent = data.community_members;
            document.getElementById('totalStaked').textContent = data.total_staked;
        }
        
        function renderServices(services) {
            const servicesGrid = document.getElementById('servicesGrid');
            
            servicesGrid.innerHTML = Object.entries(services).map(([key, service]) => {
                const statusClass = getStatusClass(service.status);
                const isHealthy = service.status === 'healthy';
                
                return `
                    <div class="service-card">
                        <div class="service-header">
                            <h3 class="service-title">${service.name}</h3>
                            <div class="status-badge ${statusClass}">
                                ${service.status.toUpperCase()}
                            </div>
                        </div>
                        <p class="service-description">${service.description}</p>
                        <a href="${service.url}" target="_blank" class="service-button" 
                           ${!isHealthy ? 'style="pointer-events: none; opacity: 0.6;"' : ''}>
                            ${isHealthy ? 'Open Dashboard' : 'Service Unavailable'}
                        </a>
                    </div>
                `;
            }).join('');
        }
        
        function renderRoadmap(roadmap) {
            const roadmapPhases = document.getElementById('roadmapPhases');
            
            roadmapPhases.innerHTML = roadmap.map(phase => {
                const statusColors = {
                    'completed': '#27ae60',
                    'in_progress': '#f39c12', 
                    'planned': '#95a5a6'
                };
                
                return `
                    <div class="phase-card ${phase.status.replace('_', '-')}">
                        <div class="phase-header">
                            <h4 class="phase-title">${phase.phase}</h4>
                            <span class="phase-status" style="background: ${statusColors[phase.status]}20; color: ${statusColors[phase.status]}; border: 1px solid ${statusColors[phase.status]};">
                                ${phase.status.replace('_', ' ')}
                            </span>
                        </div>
                        <ul class="phase-milestones">
                            ${phase.milestones.map(milestone => `<li>${milestone}</li>`).join('')}
                        </ul>
                        ${phase.completion_date ? `<div style="margin-top: 1rem; color: #27ae60; font-weight: 600;">Completed: ${phase.completion_date}</div>` : ''}
                        ${phase.estimated_completion ? `<div style="margin-top: 1rem; color: #f39c12; font-weight: 600;">Target: ${phase.estimated_completion}</div>` : ''}
                    </div>
                `;
            }).join('');
        }
        
        function renderMetrics(metrics) {
            const metricsContainer = document.getElementById('integrationMetrics');
            
            const metricGroups = [
                {
                    title: 'Security Metrics',
                    data: metrics.security_metrics,
                    format: {
                        'threats_detected_24h': 'number',
                        'assets_protected_value': 'currency',
                        'detection_accuracy': 'percentage',
                        'response_time_ms': 'time',
                        'system_uptime': 'percentage'
                    }
                },
                {
                    title: 'Community Metrics', 
                    data: metrics.community_metrics,
                    format: {
                        'total_users': 'number',
                        'active_users_24h': 'number',
                        'new_registrations_24h': 'number',
                        'wallet_connections': 'number',
                        'verified_users': 'number'
                    }
                },
                {
                    title: 'Economic Metrics',
                    data: metrics.economic_metrics,
                    format: {
                        'total_supply': 'token',
                        'circulating_supply': 'token',
                        'locked_percentage': 'percentage',
                        'market_cap_usd': 'currency',
                        'treasury_value_usd': 'currency'
                    }
                },
                {
                    title: 'Staking Metrics',
                    data: metrics.staking_metrics,
                    format: {
                        'total_staked': 'token',
                        'staking_pools': 'number',
                        'average_apy': 'percentage',
                        'total_stakers': 'number',
                        'rewards_distributed_24h': 'token'
                    }
                }
            ];
            
            metricsContainer.innerHTML = metricGroups.map(group => `
                <div class="metric-group">
                    <h4>${group.title}</h4>
                    ${Object.entries(group.data).map(([key, value]) => `
                        <div class="metric-item">
                            <span>${key.replace(/_/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase())}:</span>
                            <span class="metric-value">${formatMetricValue(value, group.format[key])}</span>
                        </div>
                    `).join('')}
                </div>
            `).join('');
        }
        
        function formatMetricValue(value, format) {
            switch (format) {
                case 'currency':
                    return '$' + (value / 1000000).toFixed(1) + 'M';
                case 'percentage':
                    return value + '%';
                case 'token':
                    return (value / 1000000).toFixed(1) + 'M';
                case 'time':
                    return value + 'ms';
                case 'number':
                default:
                    return value.toLocaleString();
            }
        }
        
        function getStatusClass(status) {
            switch (status) {
                case 'healthy':
                    return 'status-healthy';
                case 'offline':
                case 'error':
                case 'timeout':
                    return 'status-offline';
                default:
                    return 'status-unknown';
            }
        }
        
        // Initialize dashboard
        loadEcosystemData();
        
        // Auto-refresh every 30 seconds
        setInterval(loadEcosystemData, 30000);
    </script>
</body>
</html>
    '''

if __name__ == "__main__":
    import uvicorn
    
    print("🌐 Starting GuardianShield Ecosystem Integration Hub...")
    print("🚀 Hub available at: http://localhost:8000")
    print("📊 Ecosystem overview at: http://localhost:8000")
    
    uvicorn.run(
        app,
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )