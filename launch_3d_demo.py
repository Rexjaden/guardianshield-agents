#!/usr/bin/env python3
"""
GuardianShield 3D Agent Visualization Demo Launcher
"""

import webbrowser
import http.server
import socketserver
import threading
import time
import os
from pathlib import Path

def start_server():
    """Start HTTP server for the demo"""
    os.chdir(Path(__file__).parent / "frontend")
    
    PORT = 8080
    Handler = http.server.SimpleHTTPRequestHandler
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🌐 Server running at http://localhost:{PORT}")
        print(f"🛡️ GuardianShield 3D Demo: http://localhost:{PORT}/agent3d-demo.html")
        print(f"📊 Main Dashboard: http://localhost:{PORT}/index.html")
        print("\nPress Ctrl+C to stop the server")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")

def open_demo():
    """Open the 3D demo in browser"""
    time.sleep(2)  # Wait for server to start
    webbrowser.open("http://localhost:8080/agent3d-demo.html")

if __name__ == "__main__":
    print("🛡️ GuardianShield 3D Agent Visualization Demo")
    print("=" * 50)
    
    # Start server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Open demo in browser
    browser_thread = threading.Thread(target=open_demo, daemon=True)
    browser_thread.start()
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Demo ended")