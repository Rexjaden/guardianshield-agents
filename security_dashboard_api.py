"""
GuardianShield Security Dashboard API Server
Provides REST API endpoints for the security orchestration dashboard
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="GuardianShield Security Dashboard API",
    description="REST API for security orchestration dashboard",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator instance
orchestrator = None

def init_orchestrator():
    """Initialize the security orchestrator"""
    global orchestrator
    try:
        from agents.security_orchestrator import SecurityOrchestrator
        orchestrator = SecurityOrchestrator()
        logger.info("Security orchestrator initialized")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
        return False

@app.on_event("startup")
async def startup_event():
    """Initialize orchestrator on startup"""
    success = init_orchestrator()
    if not success:
        logger.warning("Starting API server without orchestrator (demo mode)")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "GuardianShield Security Dashboard API",
        "version": "1.0.0",
        "status": "active",
        "orchestrator_available": orchestrator is not None
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "orchestrator_available": orchestrator is not None
    }
    
    if orchestrator:
        try:
            status = orchestrator.get_security_status()
            health_status["system_risk"] = status.system_risk_level
            health_status["agents_active"] = (
                status.internal_agent_status == "active" and 
                status.external_agent_status == "active"
            )
        except Exception as e:
            health_status["status"] = "degraded"
            health_status["error"] = str(e)
    
    return health_status

@app.get("/dashboard")
async def get_dashboard_data():
    """Get comprehensive dashboard data"""
    if not orchestrator:
        # Return mock data when orchestrator is not available
        return get_mock_dashboard_data()
    
    try:
        return orchestrator.get_dashboard_data()
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_security_status():
    """Get current security status"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")
    
    try:
        status = orchestrator.get_security_status()
        return {
            "timestamp": status.timestamp,
            "internal_agent_status": status.internal_agent_status,
            "external_agent_status": status.external_agent_status,
            "last_internal_audit": status.last_internal_audit,
            "last_external_audit": status.last_external_audit,
            "total_threats_detected": status.total_threats_detected,
            "critical_threats": status.critical_threats,
            "system_risk_level": status.system_risk_level,
            "next_scheduled_audit": status.next_scheduled_audit,
            "uptime_hours": status.uptime_hours
        }
    except Exception as e:
        logger.error(f"Error getting security status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/coordinate-audit")
async def run_coordinated_audit(background_tasks: BackgroundTasks):
    """Trigger a coordinated security audit"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")
    
    try:
        # Run the coordinated audit
        result = orchestrator.coordinate_audits()
        return {
            "message": "Coordinated audit completed",
            "coordination_id": result["coordination_id"],
            "timestamp": result["timestamp"],
            "combined_risk": result["combined_risk"],
            "internal_audit": result.get("internal_audit"),
            "external_audit": result.get("external_audit"),
            "response_actions_count": len(result.get("response_actions", []))
        }
    except Exception as e:
        logger.error(f"Error running coordinated audit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/audit-history")
async def get_audit_history(days: int = 7):
    """Get audit coordination history"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")
    
    try:
        history = orchestrator.get_coordination_history(days=days)
        return {
            "history": history,
            "total_audits": len(history),
            "days": days
        }
    except Exception as e:
        logger.error(f"Error getting audit history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/escalations")
async def get_escalations():
    """Get recent threat escalations"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")
    
    try:
        dashboard_data = orchestrator.get_dashboard_data()
        escalations = dashboard_data.get("recent_escalations", [])
        return {
            "escalations": escalations,
            "total_escalations": len(escalations)
        }
    except Exception as e:
        logger.error(f"Error getting escalations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents/internal/status")
async def get_internal_agent_status():
    """Get internal security agent status"""
    if not orchestrator or not orchestrator.internal_agent:
        raise HTTPException(status_code=503, detail="Internal agent not available")
    
    try:
        agent = orchestrator.internal_agent
        latest_audit = agent.get_latest_audit_result()
        
        return {
            "is_monitoring": agent.is_monitoring,
            "audit_interval_hours": agent.audit_interval_hours,
            "latest_audit": latest_audit,
            "threat_filing_enabled": agent.threat_filing_enabled
        }
    except Exception as e:
        logger.error(f"Error getting internal agent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents/external/status")
async def get_external_agent_status():
    """Get external security agent status"""
    if not orchestrator or not orchestrator.external_agent:
        raise HTTPException(status_code=503, detail="External agent not available")
    
    try:
        agent = orchestrator.external_agent
        latest_audit = agent.get_latest_audit_result()
        
        return {
            "is_monitoring": agent.is_monitoring,
            "audit_interval_hours": agent.audit_interval_hours,
            "connected_networks": list(agent.web3_connections.keys()),
            "monitored_contracts": len(agent.monitored_contracts),
            "monitored_wallets": len(agent.monitored_wallets),
            "latest_audit": latest_audit
        }
    except Exception as e:
        logger.error(f"Error getting external agent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard-ui", response_class=HTMLResponse)
async def serve_dashboard_ui():
    """Serve the security dashboard UI"""
    try:
        dashboard_path = Path("frontend/security-dashboard.html")
        if dashboard_path.exists():
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                return HTMLResponse(content=f.read())
        else:
            return HTMLResponse(
                content="<h1>Dashboard UI not found</h1><p>Please ensure frontend/security-dashboard.html exists</p>",
                status_code=404
            )
    except Exception as e:
        return HTMLResponse(
            content=f"<h1>Error loading dashboard</h1><p>{str(e)}</p>",
            status_code=500
        )

def get_mock_dashboard_data():
    """Generate mock dashboard data for testing"""
    now = datetime.now()
    return {
        "status": {
            "timestamp": now.isoformat(),
            "internal_agent_status": "active",
            "external_agent_status": "active",
            "last_internal_audit": now.isoformat(),
            "last_external_audit": now.isoformat(),
            "total_threats_detected": 42,
            "critical_threats": 3,
            "system_risk_level": 4,
            "next_scheduled_audit": now.isoformat(),
            "uptime_hours": 24.5
        },
        "coordination_history": [
            {
                "coordination_id": "coord_mock_001",
                "timestamp": now.isoformat(),
                "combined_risk_level": 4,
                "response_actions": json.dumps([
                    "MEDIUM: Enhanced monitoring recommended",
                    "Review recent security events",
                    "Schedule additional audits"
                ])
            }
        ],
        "recent_escalations": [
            {
                "escalation_id": "esc_mock_001",
                "timestamp": now.isoformat(),
                "threat_source": "demo_mode",
                "severity": "medium",
                "description": "Mock escalation for demonstration",
                "escalated_to": "security_team",
                "status": "open"
            }
        ],
        "agents_available": False,
        "orchestrator_uptime": 0.0
    }

if __name__ == "__main__":
    print("🚀 Starting GuardianShield Security Dashboard API Server")
    print("📊 Dashboard UI will be available at: http://localhost:8001/dashboard-ui")
    print("🔌 API endpoints available at: http://localhost:8001/docs")
    
    uvicorn.run(
        "security_dashboard_api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )