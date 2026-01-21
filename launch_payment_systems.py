#!/usr/bin/env python3
"""
GuardianShield Complete Payment System Launcher
Starts all payment systems with smart contract integration
"""

import subprocess
import sys
import time
import os
import signal
import threading
from pathlib import Path

class PaymentSystemLauncher:
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
    
    def stop_all_services(self):
        """Stop all running services"""
        print("\n🛑 Stopping all services...")
        self.running = False
        
        for name, process in self.processes:
            try:
                process.terminate()
                print(f"🔄 Stopping {name}...")
                
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
            'smart_contract_payment_system.py',
            'shield_token_serial_system.py',
            'guard_token_purchase.py',
            'crypto_payment_gateway.py'
        ]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            print(f"❌ Missing required files: {', '.join(missing_files)}")
            return False
        
        return True
    
    def run(self):
        """Main launcher function"""
        print("🛡️  GuardianShield Complete Payment System Launcher")
        print("=" * 60)
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
        # Check dependencies
        if not self.check_dependencies():
            print("\n❌ Dependency check failed. Please ensure all files are present.")
            sys.exit(1)
        
        # Initialize systems
        print("\n🔧 Initializing payment systems...")
        
        # Start services
        services = [
            {
                'name': 'Smart Contract Payment System',
                'command': 'python smart_contract_payment_system.py',
                'port': 8082,
                'description': 'Integrated token purchases with smart contracts'
            },
            {
                'name': 'Main HTTP Server',
                'command': 'python -m http.server 8081',
                'port': 8081,
                'description': 'Static file server for frontend'
            },
            {
                'name': 'Token Serial API',
                'command': 'python shield_serial_api.py',
                'port': 8080,
                'description': 'Token serial number management API'
            },
            {
                'name': 'GUARD Token Purchase Platform',
                'command': 'python guard_token_purchase.py',
                'port': 8083,
                'description': 'Legacy GUARD token purchase interface'
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
                print(f"   📋 {service['description']}")
                
            time.sleep(2)  # Brief delay between starts
        
        # Display status
        print(f"\n🌐 Payment System Status:")
        print(f"   💰 Smart Contract Purchases: http://localhost:8082/purchase-interface")
        print(f"   🛡️ Token Management: http://localhost:8081/token_management.html")
        print(f"   🔍 Serial Verification: http://localhost:8080/serial-checker")
        print(f"   📊 Contract Info: http://localhost:8082/contract-info")
        print(f"   🏠 Main Website: http://localhost:8081/professional-landing.html")
        print(f"   💳 GUARD Token Sales: http://localhost:8083/")
        
        # Contract integration status
        print(f"\n🔗 Smart Contract Integration:")
        print(f"   ✅ GuardianTokenSale: 0xC6A4a2591bb0a9d1f45397da616dBc27e4b7BC8d")
        print(f"   ⏳ GuardianToken: To be deployed")
        print(f"   ⏳ GuardianShieldToken: To be deployed")
        print(f"   🌐 Network: Sepolia Testnet (Safe for testing)")
        
        # Keep main thread alive
        try:
            print(f"\n✅ All payment systems running. Press Ctrl+C to stop.")
            print(f"💡 Customers can now purchase GUARD and SHIELD tokens through smart contracts!")
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n📡 Shutdown signal received")
        finally:
            self.stop_all_services()

def main():
    launcher = PaymentSystemLauncher()
    launcher.run()

if __name__ == "__main__":
    main()