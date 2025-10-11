#!/usr/bin/env python3
"""
launch_dashboard.py: Convenient launcher for GuardianShield web dashboard
"""

import subprocess
import sys
import time
import webbrowser
import os
from threading import Thread

def check_dependencies():
    """Check if required dependencies are available"""
    required = ['fastapi', 'uvicorn']
    missing = []
    
    for dep in required:
        try:
            __import__(dep)
        except ImportError:
            missing.append(dep)
    
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("📦 Installing dependencies...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
            print("✅ Dependencies installed successfully!")
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            return False
    
    return True

def start_api_server():
    """Start the FastAPI server"""
    print("🚀 Starting GuardianShield API server...")
    try:
        # Change to the correct directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # Start the server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "api_server:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 Shutting down GuardianShield dashboard...")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")

def open_dashboard():
    """Open dashboard in browser after server starts"""
    time.sleep(3)  # Wait for server to start
    dashboard_url = "http://localhost:8000"
    print(f"🌐 Opening dashboard at: {dashboard_url}")
    webbrowser.open(dashboard_url)

def main():
    """Main launcher function"""
    print("🛡️ GuardianShield Dashboard Launcher")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        input("Press Enter to exit...")
        return
    
    # Start browser opener in background
    browser_thread = Thread(target=open_dashboard, daemon=True)
    browser_thread.start()
    
    print("🎯 Starting dashboard components...")
    print("📊 Dashboard will open automatically in your browser")
    print("🔌 WebSocket real-time features enabled")
    print("⚡ Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Start API server (this will block)
    start_api_server()

if __name__ == "__main__":
    main()