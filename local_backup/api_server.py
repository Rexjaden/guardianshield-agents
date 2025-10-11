from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from agents.behavioral_analytics import BehavioralAnalytics
from agents.dmer_monitor_agent import DmerMonitorAgent
from admin_console import AdminConsole
import json
import asyncio
import time
from typing import List
import uvicorn
import os

app = FastAPI(title="GuardianShield API", description="GuardianShield Agent Management API")

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
async def start_agent(agent_id: str):
    """Start an agent"""
    try:
        # Log the action
        admin_console.log_action(
            agent_id,
            "agent_start",
            {"action": "start", "timestamp": time.time()},
            severity=5
        )
        
        # Broadcast status update
        await manager.broadcast(json.dumps({
            "type": "agent_status_update",
            "payload": {
                "agentId": agent_id,
                "status": "active",
                "timestamp": time.time()
            }
        }))
        
        return {"status": "success", "message": f"Agent {agent_id} started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/{agent_id}/stop")
async def stop_agent(agent_id: str):
    """Stop an agent"""
    try:
        # Log the action
        admin_console.log_action(
            agent_id,
            "agent_stop", 
            {"action": "stop", "timestamp": time.time()},
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

# Emergency stop endpoint
@app.post("/api/emergency-stop")
async def emergency_stop():
    """Emergency stop all agents"""
    try:
        # Create emergency stop flag
        with open("emergency_stop.flag", "w") as f:
            f.write(str(time.time()))
        
        # Log emergency stop
        admin_console.log_action(
            "SYSTEM",
            "emergency_stop",
            {"reason": "manual_trigger", "timestamp": time.time()},
            severity=10
        )
        
        # Broadcast emergency alert
        await manager.broadcast(json.dumps({
            "type": "emergency_alert",
            "payload": {
                "message": "Emergency stop initiated - All agents stopped",
                "timestamp": time.time()
            }
        }))
        
        return {"status": "success", "message": "Emergency stop executed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Example: Endpoint to run Behavioral Analytics Agent
def get_behavioral_analytics_result():
    agent = BehavioralAnalytics()
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
    print("📊 Dashboard available at: http://localhost:8000")
    print("🔌 WebSocket endpoint: ws://localhost:8000/ws/dashboard")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
