#!/usr/bin/env python3
"""
GuardianShield Deployment Mode Switcher
Switch between Coming Soon page and Full System deployment
"""

import subprocess
import sys
import os
import time
from pathlib import Path

class DeploymentManager:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.coming_soon_compose = "docker-compose.coming-soon.yml"
        self.full_system_compose = "docker-compose.core.yml"
        self.env_file = ".env.production"
    
    def get_current_mode(self):
        """Check which containers are currently running"""
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"], 
                capture_output=True, text=True, check=True
            )
            containers = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            if "guardianshield-coming-soon" in containers:
                return "coming-soon"
            elif any("guardianshield-main" in c or "guardianshield-app" in c for c in containers):
                return "full-system"
            else:
                return "none"
        except subprocess.CalledProcessError:
            return "error"
    
    def deploy_coming_soon(self):
        """Deploy the coming soon page"""
        print("🚀 Deploying Coming Soon page...")
        
        # Stop any running containers
        self.stop_all()
        
        try:
            # Start coming soon container
            subprocess.run([
                "docker-compose", "-f", self.coming_soon_compose, "up", "-d"
            ], check=True)
            
            # Wait a moment and check health
            time.sleep(5)
            health_result = subprocess.run([
                "curl", "-s", "-f", "http://localhost/health"
            ], capture_output=True, text=True)
            
            if health_result.returncode == 0:
                print("✅ Coming Soon page deployed successfully!")
                print("🌐 Available at: http://localhost")
                print("💡 Admin access will redirect to coming soon until full system is ready")
            else:
                print("⚠️  Coming Soon page deployed but health check failed")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to deploy Coming Soon page: {e}")
            return False
            
        return True
    
    def deploy_full_system(self):
        """Deploy the full GuardianShield system"""
        print("🚀 Deploying Full GuardianShield System...")
        
        # Check if .env.production exists
        if not os.path.exists(self.env_file):
            print(f"❌ Environment file {self.env_file} not found!")
            print("Create this file before deploying the full system.")
            return False
        
        # Stop coming soon page
        self.stop_all()
        
        try:
            # Start full system
            subprocess.run([
                "docker-compose", "-f", self.full_system_compose, 
                "--env-file", self.env_file, "up", "-d"
            ], check=True)
            
            print("🔄 Full system starting... This may take a minute...")
            time.sleep(15)
            
            # Check system health
            health_result = subprocess.run([
                "curl", "-s", "-f", "http://localhost:8000/health"
            ], capture_output=True, text=True)
            
            if health_result.returncode == 0:
                print("✅ Full GuardianShield System deployed successfully!")
                print("🌐 Main App: http://localhost:8000")
                print("🛡️  Admin Dashboard: http://localhost:8000/start.html")
                print("📊 Analytics: http://localhost:8000/dashboard")
            else:
                print("⚠️  Full system deployed but may still be starting up...")
                print("Check logs with: docker-compose -f docker-compose.core.yml logs")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to deploy Full System: {e}")
            return False
            
        return True
    
    def stop_all(self):
        """Stop all GuardianShield containers"""
        print("🛑 Stopping all containers...")
        
        # Stop coming soon
        try:
            subprocess.run([
                "docker-compose", "-f", self.coming_soon_compose, "down"
            ], check=False)  # Don't fail if not running
        except:
            pass
        
        # Stop full system
        try:
            subprocess.run([
                "docker-compose", "-f", self.full_system_compose, 
                "--env-file", self.env_file, "down"
            ], check=False)  # Don't fail if not running
        except:
            pass
        
        print("✅ All containers stopped")
    
    def status(self):
        """Show current deployment status"""
        mode = self.get_current_mode()
        
        print("🔍 GuardianShield Deployment Status")
        print("=" * 40)
        
        if mode == "coming-soon":
            print("📄 Mode: Coming Soon Page")
            print("🌐 URL: http://localhost")
            print("📊 Status: Active")
        elif mode == "full-system":
            print("🚀 Mode: Full System")
            print("🌐 Main App: http://localhost:8000")
            print("📊 Status: Active")
        elif mode == "none":
            print("❌ Mode: Nothing Running")
            print("Use 'coming-soon' or 'full-system' to deploy")
        else:
            print("❓ Mode: Unknown/Error")
        
        print("=" * 40)
    
    def main(self):
        """Main CLI interface"""
        if len(sys.argv) != 2:
            print("GuardianShield Deployment Manager")
            print("=" * 35)
            print("Usage: python deploy_manager.py [command]")
            print()
            print("Commands:")
            print("  coming-soon   Deploy Coming Soon page only")
            print("  full-system   Deploy full GuardianShield system") 
            print("  stop          Stop all containers")
            print("  status        Show current deployment status")
            print()
            print("Quick Start:")
            print("  python deploy_manager.py coming-soon")
            sys.exit(1)
        
        command = sys.argv[1].lower()
        
        if command == "coming-soon":
            self.deploy_coming_soon()
        elif command == "full-system":
            self.deploy_full_system()
        elif command == "stop":
            self.stop_all()
        elif command == "status":
            self.status()
        else:
            print(f"❌ Unknown command: {command}")
            print("Use: coming-soon, full-system, stop, or status")
            sys.exit(1)

if __name__ == "__main__":
    manager = DeploymentManager()
    manager.main()