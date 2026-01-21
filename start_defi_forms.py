#!/usr/bin/env python3
"""
GuardianShield DeFi Forms Startup Script
Quick launcher for the DeFi forms with integrated security
"""

import os
import sys
import subprocess
import webbrowser
import time
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_requirements():
    """Check if required files exist"""
    required_files = [
        "defi_forms.html",
        "defi_forms_backend.py",
        "advanced_staking_pool_system.py",
        "advanced_liquidity_pool_framework.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        logger.error(f"Missing required files: {missing_files}")
        return False
    
    logger.info("✅ All required files found")
    return True

def install_dependencies():
    """Install required Python packages"""
    logger.info("Installing Python dependencies...")
    
    packages = [
        "fastapi",
        "uvicorn[standard]",
        "pydantic",
        "python-multipart",
        "aiofiles"
    ]
    
    try:
        for package in packages:
            logger.info(f"Installing {package}...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], check=True, capture_output=True)
        
        logger.info("✅ All dependencies installed successfully")
        return True
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False

def start_defi_server():
    """Start the DeFi forms backend server"""
    logger.info("🚀 Starting GuardianShield DeFi Forms Server...")
    
    try:
        # Start server in background
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "defi_forms_backend:app", 
            "--host", "0.0.0.0",
            "--port", "8080",
            "--reload"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(3)
        
        # Check if server is running
        if process.poll() is None:
            logger.info("✅ DeFi Forms Server started successfully!")
            logger.info("📊 Server running at: http://localhost:8080")
            logger.info("🌐 Forms available at: http://localhost:8080/")
            
            # Open browser
            try:
                webbrowser.open("http://localhost:8080")
                logger.info("🌐 Opened DeFi forms in default browser")
            except Exception as e:
                logger.warning(f"Could not open browser: {e}")
            
            return process
        else:
            logger.error("❌ Failed to start server")
            return None
            
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        return None

def show_defi_info():
    """Show information about the DeFi forms"""
    info = f"""
🛡️  GuardianShield DeFi Forms - Now Running!
{'='*60}

📋 Available Features:
   • Liquidity Pool Management (Add/Remove Liquidity)
   • Advanced Staking Pools (Standard/Premium/Platinum)
   • Rewards Claiming & Auto-Compound
   • Real-time Pool Statistics
   • Security-First Architecture

🔗 Access Points:
   • Forms Interface: http://localhost:8080/
   • API Documentation: http://localhost:8080/docs
   • Health Check: http://localhost:8080/health

💰 Supported Pools:
   • GUARD/ETH    (15.2% APR)
   • GUARD/USDC   (13.8% APR) 
   • GUARD/BTC    (18.5% APR)

🔒 Staking Options:
   • Standard Pool: 12.5% APR (30 days lock)
   • Premium Pool:  18.5% APR (90 days lock)
   • Platinum Pool: 25.0% APR (180 days lock)

⚡ Security Features:
   • Input validation & sanitization
   • Transaction simulation
   • Slippage protection
   • Auto-compound optimization
   • Real-time risk monitoring

🎯 Next Steps:
   1. Connect your wallet
   2. Check available balances
   3. Start with small amounts for testing
   4. Monitor your positions in the dashboard

📞 Support:
   • Documentation: Check README files
   • API Docs: http://localhost:8080/docs
   • Logs: Check terminal output for details

Press Ctrl+C to stop the server
    """
    
    print(info)

def main():
    """Main startup function"""
    print("🛡️  GuardianShield DeFi Forms Launcher")
    print("="*50)
    
    # Check requirements
    if not check_requirements():
        logger.error("❌ Requirements check failed")
        return False
    
    # Install dependencies
    if not install_dependencies():
        logger.error("❌ Dependency installation failed")
        return False
    
    # Start server
    server_process = start_defi_server()
    if not server_process:
        logger.error("❌ Server startup failed")
        return False
    
    # Show info
    show_defi_info()
    
    try:
        # Keep server running
        server_process.wait()
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down DeFi Forms Server...")
        server_process.terminate()
        server_process.wait()
        logger.info("✅ Server stopped successfully")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)