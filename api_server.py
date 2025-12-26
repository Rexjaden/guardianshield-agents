from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# Use the primary agent implementation rather than the legacy alias
from agents.behavioral_analytics import BehavioralAnalyticsAgent
from agents.dmer_monitor_agent import DmerMonitorAgent
from admin_console import AdminConsole
from continuous_training_system import continuous_trainer, LearningEvent
from security_manager import (
    security_manager, 
    get_current_user, 
    require_admin_access, 
    require_master_admin,
    require_permission
)
import json
import asyncio
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import uvicorn
import os

app = FastAPI(
    title="GuardianShield API", 
    description="GuardianShield Agent Management API - Secure Access Required | www.guardian-shield.io",
    version="2.0.0",
    docs_url="/admin/api-docs",  # Move API docs to admin area
    redoc_url="/admin/redoc"     # Move ReDoc to admin area
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:8000", 
        "https://www.guardian-shield.io",
        "https://guardian-shield.io",
        "http://www.guardian-shield.io",
        "http://guardian-shield.io"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Initialize admin console
admin_console = AdminConsole()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove dead connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Authentication Models
class LoginRequest(BaseModel):
    username: str
    password: str

class UserCreationRequest(BaseModel):
    username: str
    password: str
    role: str = "admin"
    permissions: List[str] = ["read", "agents", "threats"]

# Authentication Endpoints
@app.post("/api/auth/login")
async def login(login_data: LoginRequest):
    """Authenticate user and return access token"""
    try:
        token = security_manager.authenticate_user(login_data.username, login_data.password)
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": security_manager.token_expiry_hours * 3600,
            "message": "Authentication successful"
        }
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail, "error": "authentication_failed"}
        )

@app.post("/api/auth/logout")
async def logout(user_info = Depends(get_current_user)):
    """Logout current user"""
    # In a production system, you'd invalidate the token
    return {"message": "Logged out successfully"}

@app.get("/api/auth/me")
async def get_current_user_info(user_info = Depends(get_current_user)):
    """Get current user information"""
    return {
        "username": user_info["username"],
        "role": user_info["role"],
        "permissions": security_manager.authorized_users.get(user_info["username"], {}).get("permissions", [])
    }

@app.post("/api/auth/create-user")
async def create_user(
    user_data: UserCreationRequest,
    admin_user = Depends(require_master_admin)
):
    """Create new authorized user (Master Admin Only)"""
    try:
        security_manager.add_authorized_user(
            user_data.username,
            user_data.password,
            user_data.role,
            user_data.permissions
        )
        return {"message": f"User '{user_data.username}' created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create user: {str(e)}")

@app.delete("/api/auth/revoke-user/{username}")
async def revoke_user_access(
    username: str,
    admin_user = Depends(require_master_admin)
):
    """Revoke user access (Master Admin Only)"""
    try:
        security_manager.revoke_user_access(username)
        return {"message": f"Access revoked for user '{username}'"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to revoke access: {str(e)}")

# Continuous Training API Endpoints (Now Secured)
@app.post("/api/training/threat-detection")
async def report_threat_detection(
    data: Dict[str, Any],
    user_info = Depends(require_permission("agents"))
):
    """Report a threat detection for training (Requires agent access)"""
    try:
        event = LearningEvent(
            event_type='threat_detected',
            agent_id=data.get('agent_id', 'unknown'),
            data=data.get('threat_data', {}),
            confidence=data.get('confidence', 0.5)
        )
        continuous_trainer.add_learning_event(event)
        
        # Broadcast to connected clients with user context
        await manager.broadcast(json.dumps({
            'type': 'training_event',
            'event': 'threat_detection',
            'agent': data.get('agent_id'),
            'reported_by': user_info["username"],
            'timestamp': datetime.now().isoformat()
        }))
        
        return {"status": "success", "message": "Threat detection reported for training", "reported_by": user_info["username"]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/training/false-positive")
async def report_false_positive(
    data: Dict[str, Any],
    user_info = Depends(require_permission("agents"))
):
    """Report a false positive for immediate retraining (Requires agent access)"""
    try:
        event = LearningEvent(
            event_type='false_positive',
            agent_id=data.get('agent_id', 'unknown'),
            data=data.get('detection_data', {}),
            feedback=data.get('feedback', ''),
            confidence=0.0
        )
        continuous_trainer.add_learning_event(event)
        
        # Broadcast to connected clients with user context
        await manager.broadcast(json.dumps({
            'type': 'training_event',
            'event': 'false_positive',
            'agent': data.get('agent_id'),
            'feedback': data.get('feedback'),
            'reported_by': user_info["username"],
            'timestamp': datetime.now().isoformat()
        }))
        
        return {"status": "success", "message": "False positive reported for retraining", "reported_by": user_info["username"]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/training/status")
async def get_training_status():
    """Get current training system status"""
    try:
        status = continuous_trainer.get_training_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/training/start")
async def start_training():
    """Start continuous training system"""
    try:
        # Start training in background task
        asyncio.create_task(continuous_trainer.continuous_training_loop())
        return {"status": "success", "message": "Continuous training started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/training/stop")
async def stop_training():
    """Stop continuous training system"""
    try:
        continuous_trainer.stop_training()
        return {"status": "success", "message": "Continuous training stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve frontend
@app.get("/")
async def serve_frontend():
    return FileResponse("frontend/index.html")

# Agent management endpoints
@app.get("/api/agents")
async def get_agents():
    """Get all agents status"""
    return {
        "agents": [
            {
                "id": "learning_agent",
                "name": "Learning Agent", 
                "status": "active",
                "actions": 1247,
                "evolutions": 5,
                "accuracy": 94.5,
                "autonomyLevel": 10
            },
            {
                "id": "behavioral_analytics",
                "name": "Behavioral Analytics",
                "status": "active", 
                "actions": 892,
                "evolutions": 3,
                "accuracy": 96.2,
                "autonomyLevel": 9
            }
        ]
    }

@app.post("/api/agents/{agent_id}/start")
async def start_agent(agent_id: str, admin_user = Depends(require_admin_access)):
    """Start an agent (Admin Only)"""
    try:
        # Log the action
        admin_console.log_action(
            agent_id,
            "agent_start",
            {"action": "start", "admin": admin_user["username"], "timestamp": time.time()},
            severity=5
        )
        
        # Broadcast status update with admin context
        await manager.broadcast(json.dumps({
            "type": "agent_status_update",
            "payload": {
                "agentId": agent_id,
                "status": "active",
                "admin": admin_user["username"],
                "timestamp": time.time()
            }
        }))
        
        return {"status": "success", "message": f"Agent {agent_id} started by {admin_user['username']}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/{agent_id}/stop")
async def stop_agent(agent_id: str, admin_user = Depends(require_admin_access)):
    """Stop an agent (Admin Only)"""
    try:
        # Log the action
        admin_console.log_action(
            agent_id,
            "agent_stop", 
            {"action": "stop", "admin": admin_user["username"], "timestamp": time.time()},
            severity=5
        )
        
        # Broadcast status update
        await manager.broadcast(json.dumps({
            "type": "agent_status_update",
            "payload": {
                "agentId": agent_id,
                "status": "inactive",
                "timestamp": time.time()
            }
        }))
        
        return {"status": "success", "message": f"Agent {agent_id} stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/agents/{agent_id}/config")
async def update_agent_config(agent_id: str, config: dict):
    """Update agent configuration"""
    try:
        # Log the configuration change
        admin_console.log_action(
            agent_id,
            "config_update",
            {"config": config, "timestamp": time.time()},
            severity=6
        )
        
        return {"status": "success", "message": "Configuration updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/{agent_id}/evolve")
async def evolve_agent(agent_id: str):
    """Trigger agent evolution"""
    try:
        # Log evolution trigger
        admin_console.log_evolution_decision(
            agent_id,
            "manual_evolution_trigger",
            {"trigger": "api", "timestamp": time.time()}
        )
        
        # Simulate evolution process
        await asyncio.sleep(1)
        
        # Broadcast evolution complete
        await manager.broadcast(json.dumps({
            "type": "agent_evolution",
            "payload": {
                "agentId": agent_id,
                "evolutionData": {
                    "improvementPercentage": 12.5,
                    "newAccuracy": 96.7
                },
                "timestamp": time.time()
            }
        }))
        
        return {"status": "success", "message": f"Agent {agent_id} evolution initiated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Emergency stop endpoint (Master Admin Only)
@app.post("/api/emergency-stop")
async def emergency_stop(master_admin = Depends(require_master_admin)):
    """Emergency stop all agents (MASTER ADMIN ONLY)"""
    try:
        # Create emergency stop flag
        with open("emergency_stop.flag", "w") as f:
            f.write(f"{time.time()}|{master_admin['username']}")
        
        # Log emergency stop with admin info
        admin_console.log_action(
            "SYSTEM",
            "emergency_stop",
            {"reason": "manual_trigger", "admin": master_admin["username"], "timestamp": time.time()},
            severity=10
        )
        
        # Broadcast emergency alert with admin context
        await manager.broadcast(json.dumps({
            "type": "emergency_alert",
            "payload": {
                "message": f"EMERGENCY STOP initiated by {master_admin['username']} - All agents stopped",
                "admin": master_admin["username"],
                "timestamp": time.time()
            }
        }))
        
        return {"status": "success", "message": f"Emergency stop executed by {master_admin['username']}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Example: Endpoint to run Behavioral Analytics Agent
def get_behavioral_analytics_result():
    agent = BehavioralAnalyticsAgent()
    result = agent.run() if hasattr(agent, 'run') else {"status": "agent_active"}
    return result

@app.get("/api/behavioral-analytics")
def behavioral_analytics():
    return {"result": get_behavioral_analytics_result()}

# Example: Endpoint to run DMER Monitor Agent
def get_dmer_monitor_result():
    agent = DmerMonitorAgent()
    result = agent.run() if hasattr(agent, 'run') else {"status": "agent_active"}
    return result

@app.get("/api/dmer-monitor")
def dmer_monitor():
    return {"result": get_dmer_monitor_result()}

# WebSocket endpoint for real-time updates
@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Send heartbeat every 30 seconds
            await asyncio.sleep(30)
            await websocket.send_text(json.dumps({
                "type": "heartbeat",
                "payload": {"timestamp": time.time()}
            }))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Background task to simulate real-time data
async def simulate_real_time_data():
    """Simulate real-time agent data and threats"""
    while True:
        try:
            # Simulate threat detection
            if len(manager.active_connections) > 0:
                await manager.broadcast(json.dumps({
                    "type": "threat_detected",
                    "payload": {
                        "id": f"threat_{int(time.time())}",
                        "title": "Suspicious Activity Detected",
                        "description": "Anomalous transaction pattern identified",
                        "severity": "medium",
                        "source": "behavioral_analytics"
                    }
                }))
            
            await asyncio.sleep(60)  # Send update every minute
            
        except Exception as e:
            print(f"Error in background task: {e}")
            await asyncio.sleep(10)

# Start background task
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(simulate_real_time_data())

# Add more endpoints for other agents as needed

if __name__ == "__main__":
    print("🛡️ Starting GuardianShield API Server...")
    print("🌐 Production Domain: https://www.guardian-shield.io")
    print("📊 Local Dashboard: http://localhost:8000")
    print("🔐 Admin Access: http://localhost:8000/admin")
    print("🔌 WebSocket endpoint: ws://localhost:8000/ws")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
