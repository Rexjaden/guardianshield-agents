#!/usr/bin/env python3
"""
DHI Cluster Autoscaler API Server
"""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import uvicorn

logger = logging.getLogger('dhi-autoscaler.api')

app = FastAPI(
    title="DHI Kubernetes Cluster Autoscaler",
    description="GuardianShield Mining Node Autoscaling API",
    version="1.0.0"
)

# Global reference to autoscaler (set during startup)
_autoscaler = None


def set_autoscaler(autoscaler):
    """Set the autoscaler instance for API access"""
    global _autoscaler
    _autoscaler = autoscaler


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if _autoscaler and _autoscaler.running:
        return {"status": "healthy", "version": "1.0.0"}
    return JSONResponse(
        status_code=503,
        content={"status": "unhealthy", "reason": "Autoscaler not running"}
    )


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    if _autoscaler and _autoscaler.running and _autoscaler.docker_client:
        return {"status": "ready"}
    return JSONResponse(
        status_code=503,
        content={"status": "not ready"}
    )


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/status")
async def get_status():
    """Get autoscaler status"""
    if not _autoscaler:
        raise HTTPException(status_code=503, detail="Autoscaler not initialized")
    return _autoscaler.get_status()


@app.get("/nodes")
async def list_nodes():
    """List all mining nodes"""
    if not _autoscaler:
        raise HTTPException(status_code=503, detail="Autoscaler not initialized")
    
    return {
        "total": len(_autoscaler.mining_nodes),
        "nodes": [
            {
                "node_id": node.node_id,
                "region": node.region,
                "status": node.status,
                "blocks_mined": node.blocks_mined,
                "created_at": node.created_at.isoformat()
            }
            for node in _autoscaler.mining_nodes.values()
        ]
    }


@app.post("/scale/{target}")
async def scale_to(target: int):
    """Manually scale to target number of nodes"""
    if not _autoscaler:
        raise HTTPException(status_code=503, detail="Autoscaler not initialized")
    
    if target < _autoscaler.min_nodes or target > _autoscaler.max_nodes:
        raise HTTPException(
            status_code=400,
            detail=f"Target must be between {_autoscaler.min_nodes} and {_autoscaler.max_nodes}"
        )
    
    await _autoscaler.scale_to_target(target, "Manual scaling request via API")
    
    return {
        "success": True,
        "target": target,
        "current": len(_autoscaler.mining_nodes)
    }


@app.post("/nodes/{region}")
async def create_node(region: str):
    """Create a new mining node in specified region"""
    if not _autoscaler:
        raise HTTPException(status_code=503, detail="Autoscaler not initialized")
    
    if len(_autoscaler.mining_nodes) >= _autoscaler.max_nodes:
        raise HTTPException(status_code=400, detail="Maximum nodes reached")
    
    node = await _autoscaler.create_mining_node(region)
    
    if node:
        return {
            "success": True,
            "node_id": node.node_id,
            "region": node.region,
            "status": node.status
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to create node")


@app.delete("/nodes/{node_id}")
async def delete_node(node_id: str):
    """Delete a mining node"""
    if not _autoscaler:
        raise HTTPException(status_code=503, detail="Autoscaler not initialized")
    
    if node_id not in _autoscaler.mining_nodes:
        raise HTTPException(status_code=404, detail="Node not found")
    
    if len(_autoscaler.mining_nodes) <= _autoscaler.min_nodes:
        raise HTTPException(status_code=400, detail="Cannot go below minimum nodes")
    
    await _autoscaler.remove_mining_node(node_id)
    
    return {"success": True, "node_id": node_id}


@app.get("/config")
async def get_config():
    """Get current autoscaler configuration"""
    if not _autoscaler:
        raise HTTPException(status_code=503, detail="Autoscaler not initialized")
    
    return {
        "min_nodes": _autoscaler.min_nodes,
        "max_nodes": _autoscaler.max_nodes,
        "target_nodes": _autoscaler.target_nodes,
        "scale_up_threshold": _autoscaler.scale_up_threshold,
        "scale_down_threshold": _autoscaler.scale_down_threshold,
        "cooldown_period": _autoscaler.cooldown_period,
        "check_interval": _autoscaler.check_interval,
        "regions": _autoscaler.regions,
        "chain_id": _autoscaler.chain_id
    }


async def start_api_server(autoscaler, port: int = 8080):
    """Start the API server"""
    set_autoscaler(autoscaler)
    
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    logger.info(f"🌐 Starting API server on port {port}")
    await server.serve()
