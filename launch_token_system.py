#!/usr/bin/env python3
"""
GuardianShield Token System Launcher
Starts the SHIELD token serial number system alongside main services
"""

import subprocess
import sys
import time
import os
import signal
import threading
from pathlib import Path

class TokenSystemLauncher:
    def __init__(self):
        self.processes = []
        self.running = True
        
    def start_service(self, name, command, port=None):
        """Start a service with error handling"""
        try:
            print(f"🚀 Starting {name}...")
            
            if port:
                # Check if port is already in use
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', port))
                if result == 0:
                    print(f"⚠️  Port {port} is already in use for {name}")
                    sock.close()
                    return None
                sock.close()
            
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            self.processes.append((name, process))
            print(f"✅ {name} started successfully (PID: {process.pid})")
            return process
            
        except Exception as e:
            print(f"❌ Failed to start {name}: {e}")
            return None
    
    def monitor_service(self, name, process):
        """Monitor a service and restart if needed"""
        while self.running:
            if process.poll() is not None:
                print(f"⚠️  {name} stopped unexpectedly")
                break
            time.sleep(5)
    
    def stop_all_services(self):
        """Stop all running services"""
        print("\n🛑 Stopping all services...")
        self.running = False
        
        for name, process in self.processes:
            try:
                process.terminate()
                print(f"🔄 Stopping {name}...")
                
                # Give process time to terminate gracefully
                try:
                    process.wait(timeout=5)
                    print(f"✅ {name} stopped")
                except subprocess.TimeoutExpired:
                    process.kill()
                    print(f"🔨 Force killed {name}")
                    
            except Exception as e:
                print(f"❌ Error stopping {name}: {e}")
        
        self.processes.clear()
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            print(f"\n📡 Received signal {signum}")
            self.stop_all_services()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def check_dependencies(self):
        """Check if required files and dependencies exist"""
        required_files = [
            'shield_token_serial_system.py',
            'shield_serial_api.py',
            'token_management.html'
        ]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            print(f"❌ Missing required files: {', '.join(missing_files)}")
            return False
        
        # Check Python packages
        required_packages = ['fastapi', 'uvicorn', 'sqlite3']
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                if package == 'sqlite3':
                    continue  # sqlite3 is built-in
                print(f"❌ Missing required package: {package}")
                print(f"   Install with: pip install {package}")
                return False
        
        return True
    
    def run(self):
        """Main launcher function"""
        print("🛡️  GuardianShield Token System Launcher")
        print("=" * 50)
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
        # Check dependencies
        if not self.check_dependencies():
            print("\n❌ Dependency check failed. Please install missing requirements.")
            sys.exit(1)
        
        # Initialize token database
        print("\n🔧 Initializing token database...")
        try:
            from shield_token_serial_system import ShieldTokenSerial
            serial_system = ShieldTokenSerial()
            print("✅ Token database initialized")
        except Exception as e:
            print(f"❌ Failed to initialize database: {e}")
            sys.exit(1)
        
        # Start services
        services = [
            {
                'name': 'Token Serial API',
                'command': 'python shield_serial_api.py',
                'port': 8080
            },
            {
                'name': 'Main HTTP Server',
                'command': 'python -m http.server 8081',
                'port': 8081
            }
        ]
        
        # Start each service
        for service in services:
            process = self.start_service(
                service['name'], 
                service['command'], 
                service.get('port')
            )
            
            if process:
                # Start monitoring thread
                monitor_thread = threading.Thread(
                    target=self.monitor_service,
                    args=(service['name'], process),
                    daemon=True
                )
                monitor_thread.start()
                
            time.sleep(2)  # Brief delay between starts
        
        # Display status
        print(f"\n🌐 Services Status:")
        print(f"   Token Management: http://localhost:8081/token_management.html")
        print(f"   Serial Verification: http://localhost:8080/serial-checker")
        print(f"   API Documentation: http://localhost:8080/docs")
        print(f"   Main Website: http://localhost:8081/professional-landing.html")
        
        # Keep main thread alive
        try:
            print(f"\n✅ All services running. Press Ctrl+C to stop.")
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n📡 Shutdown signal received")
        finally:
            self.stop_all_services()

def main():
    launcher = TokenSystemLauncher()
    launcher.run()

if __name__ == "__main__":
    main()