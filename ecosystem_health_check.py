#!/usr/bin/env python3
"""
GuardianShield Ecosystem Health Check
Comprehensive system validation and testing
"""

import asyncio
import aiohttp
import json
import sqlite3
import os
from typing import Dict, List, Tuple
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EcosystemHealthChecker:
    """Comprehensive health check for all GuardianShield services"""
    
    def __init__(self):
        self.services = {
            "ecosystem_hub": {
                "port": 8000,
                "name": "Ecosystem Hub",
                "health_endpoint": "/",
                "critical": True
            },
            "community_portal": {
                "port": 8003,
                "name": "Community Portal", 
                "health_endpoint": "/",
                "critical": True
            },
            "tokenomics_dashboard": {
                "port": 8004,
                "name": "Tokenomics Dashboard",
                "health_endpoint": "/",
                "critical": True
            },
            "staking_interface": {
                "port": 8006,
                "name": "Staking Interface",
                "health_endpoint": "/",
                "critical": True
            },
            "nft_builder": {
                "port": 8007,
                "name": "NFT Builder",
                "health_endpoint": "/",
                "critical": False
            },
            "crypto_payment": {
                "port": 8008,
                "name": "Crypto Payment Gateway",
                "health_endpoint": "/",
                "critical": True
            },
            "analytics_dashboard": {
                "port": 8009,
                "name": "Analytics Dashboard",
                "health_endpoint": "/",
                "critical": False
            },
            "guard_purchase": {
                "port": 8010,
                "name": "GUARD Token Purchase",
                "health_endpoint": "/",
                "critical": True
            }
        }
        
        self.databases = [
            "community_portal.db",
            "guard_purchases.db", 
            "staking.db",
            "nft_builder.db",
            "payment_gateway.db",
            "analytics.db"
        ]
        
        self.health_report = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "databases": {},
            "system_health": "unknown",
            "critical_issues": [],
            "warnings": [],
            "recommendations": []
        }
    
    async def check_service_health(self, service_name: str, config: Dict) -> Dict:
        """Check health of individual service"""
        url = f"http://localhost:{config['port']}{config['health_endpoint']}"
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    status = "healthy" if response.status == 200 else "unhealthy"
                    response_time = response.headers.get('X-Response-Time', 'unknown')
                    
                    return {
                        "status": status,
                        "http_status": response.status,
                        "response_time_ms": response_time,
                        "url": url,
                        "error": None
                    }
        
        except aiohttp.ClientError as e:
            return {
                "status": "down",
                "http_status": None,
                "response_time_ms": None,
                "url": url,
                "error": str(e)
            }
        except Exception as e:
            return {
                "status": "error",
                "http_status": None,
                "response_time_ms": None,
                "url": url,
                "error": str(e)
            }
    
    def check_database_health(self, db_name: str) -> Dict:
        """Check database integrity and accessibility"""
        db_path = f"./{db_name}"
        
        try:
            if not os.path.exists(db_path):
                return {
                    "status": "missing",
                    "size_mb": 0,
                    "tables": [],
                    "error": "Database file not found"
                }
            
            # Get file size
            size_bytes = os.path.getsize(db_path)
            size_mb = round(size_bytes / (1024 * 1024), 2)
            
            # Connect and check tables
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Test a simple query
            cursor.execute("SELECT COUNT(*) FROM sqlite_master")
            cursor.fetchone()
            
            conn.close()
            
            return {
                "status": "healthy",
                "size_mb": size_mb,
                "tables": tables,
                "error": None
            }
            
        except Exception as e:
            return {
                "status": "error", 
                "size_mb": 0,
                "tables": [],
                "error": str(e)
            }
    
    async def run_comprehensive_check(self):
        """Run complete ecosystem health check"""
        print("🏥 Starting GuardianShield Ecosystem Health Check")
        print("=" * 60)
        
        # Check all services
        print("\n🌐 Checking Services...")
        service_tasks = []
        for service_name, config in self.services.items():
            task = self.check_service_health(service_name, config)
            service_tasks.append((service_name, task))
        
        for service_name, task in service_tasks:
            result = await task
            self.health_report["services"][service_name] = result
            
            status_emoji = "✅" if result["status"] == "healthy" else "❌" if result["status"] == "down" else "⚠️"
            print(f"{status_emoji} {self.services[service_name]['name']} (:{self.services[service_name]['port']}) - {result['status']}")
            
            if result["error"]:
                print(f"   Error: {result['error']}")
        
        # Check databases
        print("\n💾 Checking Databases...")
        for db_name in self.databases:
            result = self.check_database_health(db_name)
            self.health_report["databases"][db_name] = result
            
            status_emoji = "✅" if result["status"] == "healthy" else "❌" if result["status"] == "missing" else "⚠️"
            print(f"{status_emoji} {db_name} - {result['status']} ({result['size_mb']} MB)")
            
            if result["error"]:
                print(f"   Error: {result['error']}")
        
        # Analyze overall health
        self.analyze_system_health()
        
        # Generate report
        self.print_health_summary()
        self.save_health_report()
    
    def analyze_system_health(self):
        """Analyze overall system health and identify issues"""
        critical_down = 0
        services_down = 0
        db_issues = 0
        
        # Check services
        for service_name, result in self.health_report["services"].items():
            if result["status"] != "healthy":
                services_down += 1
                if self.services[service_name]["critical"]:
                    critical_down += 1
                    self.health_report["critical_issues"].append(
                        f"Critical service {self.services[service_name]['name']} is {result['status']}"
                    )
        
        # Check databases
        for db_name, result in self.health_report["databases"].items():
            if result["status"] != "healthy":
                db_issues += 1
                if result["status"] == "missing":
                    self.health_report["warnings"].append(f"Database {db_name} is missing")
                else:
                    self.health_report["warnings"].append(f"Database {db_name} has issues: {result['error']}")
        
        # Determine overall health
        if critical_down > 0:
            self.health_report["system_health"] = "critical"
        elif services_down > 0 or db_issues > 2:
            self.health_report["system_health"] = "degraded"
        elif db_issues > 0:
            self.health_report["system_health"] = "warning"
        else:
            self.health_report["system_health"] = "healthy"
        
        # Generate recommendations
        if critical_down > 0:
            self.health_report["recommendations"].append("Restart critical services immediately")
        if db_issues > 0:
            self.health_report["recommendations"].append("Check database permissions and disk space")
        if services_down > 3:
            self.health_report["recommendations"].append("Consider full system restart")
    
    def print_health_summary(self):
        """Print comprehensive health summary"""
        print("\n📊 HEALTH SUMMARY")
        print("=" * 30)
        
        # Overall status
        health_emoji = {
            "healthy": "🟢",
            "warning": "🟡", 
            "degraded": "🟠",
            "critical": "🔴"
        }
        
        status = self.health_report["system_health"]
        print(f"Overall System Health: {health_emoji[status]} {status.upper()}")
        
        # Services summary
        total_services = len(self.services)
        healthy_services = sum(1 for r in self.health_report["services"].values() if r["status"] == "healthy")
        print(f"Services: {healthy_services}/{total_services} healthy")
        
        # Database summary  
        total_dbs = len(self.databases)
        healthy_dbs = sum(1 for r in self.health_report["databases"].values() if r["status"] == "healthy")
        print(f"Databases: {healthy_dbs}/{total_dbs} healthy")
        
        # Critical issues
        if self.health_report["critical_issues"]:
            print(f"\n🚨 Critical Issues ({len(self.health_report['critical_issues'])}):")
            for issue in self.health_report["critical_issues"]:
                print(f"  • {issue}")
        
        # Warnings
        if self.health_report["warnings"]:
            print(f"\n⚠️ Warnings ({len(self.health_report['warnings'])}):")
            for warning in self.health_report["warnings"]:
                print(f"  • {warning}")
        
        # Recommendations
        if self.health_report["recommendations"]:
            print(f"\n💡 Recommendations:")
            for rec in self.health_report["recommendations"]:
                print(f"  • {rec}")
        
        print(f"\n✅ Health check completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def save_health_report(self):
        """Save health report to file"""
        filename = f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.health_report, f, indent=2)
        
        print(f"📄 Detailed report saved to {filename}")
    
    async def test_service_functionality(self, service_name: str) -> Dict:
        """Test specific functionality of a service"""
        if service_name == "guard_purchase":
            return await self.test_guard_purchase_service()
        elif service_name == "staking_interface":
            return await self.test_staking_service()
        elif service_name == "tokenomics_dashboard":
            return await self.test_tokenomics_service()
        else:
            return {"status": "not_implemented", "message": "Functional test not implemented"}
    
    async def test_guard_purchase_service(self) -> Dict:
        """Test GUARD token purchase functionality"""
        try:
            url = "http://localhost:8010/api/price"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": "working",
                            "current_price": data.get("guard_price_usd"),
                            "message": "Price API working correctly"
                        }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def test_staking_service(self) -> Dict:
        """Test staking functionality"""
        try:
            url = "http://localhost:8006/api/stats"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return {"status": "working", "message": "Staking API working correctly"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

async def main():
    """Run comprehensive health check"""
    checker = EcosystemHealthChecker()
    await checker.run_comprehensive_check()
    
    # Optional: Test critical service functionality
    print("\n🧪 Testing Critical Service Functionality...")
    
    for service in ["guard_purchase", "staking_interface"]:
        if service in checker.health_report["services"]:
            if checker.health_report["services"][service]["status"] == "healthy":
                result = await checker.test_service_functionality(service)
                print(f"  {service}: {result['status']} - {result['message']}")

if __name__ == "__main__":
    asyncio.run(main())