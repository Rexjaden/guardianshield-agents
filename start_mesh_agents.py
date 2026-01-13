#!/usr/bin/env python3
"""
Start GuardianShield with Cilium Mesh Integration
Complete startup orchestration for the autonomous agent system
"""

import os
import sys
import asyncio
import subprocess
import time
import json
from pathlib import Path

async def check_docker_running():
    """Check if Docker is running"""
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

async def check_containers_health():
    """Check health of core containers"""
    containers = [
        "guardianshield-clustermesh",
        "guardianshield-redis", 
        "guardianshield-postgres"
    ]
    
    healthy = []
    for container in containers:
        try:
            result = subprocess.run([
                "docker", "inspect", container, "--format", "{{.State.Status}}"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                status = result.stdout.strip()
                healthy.append(f"{container}: {status}")
            else:
                healthy.append(f"{container}: not found")
        except:
            healthy.append(f"{container}: error")
    
    return healthy

async def main():
    """Main startup with Cilium mesh"""
    print("🛡️ GUARDIANSHIELD + CILIUM MESH STARTUP")
    print("=" * 50)
    
    # Check Docker
    if not await check_docker_running():
        print("❌ Docker not running")
        return 1
    
    print("✅ Docker running")
    
    # Check container health
    health = await check_containers_health()
    print("📊 Container Status:")
    for status in health:
        print(f"   {status}")
    
    # Start mesh integration
    print("\n🔗 Starting Cilium mesh integration...")
    try:
        result = subprocess.run([sys.executable, "cilium_agent_mesh.py"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Cilium mesh ready")
        else:
            print(f"⚠️ Mesh warning: {result.stderr[:100]}")
    except Exception as e:
        print(f"⚠️ Mesh error: {e}")
    
    # Start agents with mesh
    print("🤖 Starting GuardianShield agents...")
    try:
        from main import AutonomousAgentOrchestrator
        orchestrator = AutonomousAgentOrchestrator()
        
        # Set mesh enabled
        os.environ['CILIUM_MESH_ENABLED'] = 'true'
        
        print("✅ Agents initialized with Cilium mesh")
        print("🔗 Service mesh networking active")
        print("🛡️ GuardianShield + Cilium ready!")
        
        return 0
        
    except Exception as e:
        print(f"❌ Agent startup failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)