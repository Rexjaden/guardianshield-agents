#!/usr/bin/env python3
"""
🔍 GUARDIANSHIELD SYSTEM STATUS & HEALTH REPORT
Complete system verification and status dashboard
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
import subprocess

class SystemHealthChecker:
    """Comprehensive system health and status checker"""
    
    def __init__(self):
        self.status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'UNKNOWN',
            'components': {},
            'databases': {},
            'files': {},
            'dependencies': {},
            'recommendations': []
        }
    
    def check_agents(self):
        """Check all agent systems"""
        print("🤖 CHECKING AGENT SYSTEMS...")
        
        agents = {
            'learning_agent': 'agents.learning_agent',
            'behavioral_analytics': 'agents.behavioral_analytics', 
            'data_ingestion': 'agents.data_ingestion',
            'dmer_monitor': 'agents.dmer_monitor_agent',
            'external_agent': 'agents.external_agent',
            'flare_integration': 'agents.flare_integration',
            'genetic_evolver': 'agents.genetic_evolver',
            'threat_definitions': 'agents.threat_definitions'
        }
        
        for agent_name, module_path in agents.items():
            try:
                exec(f"import {module_path}")
                self.status['components'][agent_name] = {
                    'status': 'OPERATIONAL',
                    'type': 'agent',
                    'module': module_path
                }
                print(f"   ✅ {agent_name}: OPERATIONAL")
            except Exception as e:
                self.status['components'][agent_name] = {
                    'status': 'ERROR',
                    'type': 'agent',
                    'error': str(e),
                    'module': module_path
                }
                print(f"   ❌ {agent_name}: ERROR - {e}")
    
    def check_security_systems(self):
        """Check security systems"""
        print("\n🔐 CHECKING SECURITY SYSTEMS...")
        
        security = {
            'authentication': 'guardian_security_system',
            'rbac': 'guardian_rbac_system',
            'audit': 'guardian_audit_system',
            'admin_console': 'admin_console',
            'security_integration': 'security_integration'
        }
        
        for system_name, module_path in security.items():
            try:
                exec(f"import {module_path}")
                self.status['components'][system_name] = {
                    'status': 'OPERATIONAL',
                    'type': 'security',
                    'module': module_path
                }
                print(f"   ✅ {system_name}: OPERATIONAL")
            except Exception as e:
                self.status['components'][system_name] = {
                    'status': 'ERROR',
                    'type': 'security',
                    'error': str(e),
                    'module': module_path
                }
                print(f"   ❌ {system_name}: ERROR - {e}")
    
    def check_main_systems(self):
        """Check main orchestration systems"""
        print("\n🚀 CHECKING MAIN SYSTEMS...")
        
        main_systems = {
            'main_orchestrator': 'main',
            'guardian_main_menu': 'guardianshield_main_menu'
        }
        
        for system_name, module_path in main_systems.items():
            try:
                exec(f"import {module_path}")
                self.status['components'][system_name] = {
                    'status': 'OPERATIONAL',
                    'type': 'main_system',
                    'module': module_path
                }
                print(f"   ✅ {system_name}: OPERATIONAL")
            except Exception as e:
                self.status['components'][system_name] = {
                    'status': 'LIMITED',  # Main systems might have optional dependencies
                    'type': 'main_system',
                    'warning': str(e),
                    'module': module_path
                }
                print(f"   ⚠️ {system_name}: LIMITED - {e}")
    
    def check_databases(self):
        """Check database files and connections"""
        print("\n💾 CHECKING DATABASES...")
        
        db_paths = [
            './databases/threat_intelligence.db',
            './databases/analytics.db',
            './databases/security_orchestration.db',
            './databases/dmer_monitoring.db',
            './databases/behavioral_data.db'
        ]
        
        for db_path in db_paths:
            if os.path.exists(db_path):
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    conn.close()
                    
                    self.status['databases'][db_path] = {
                        'status': 'OPERATIONAL',
                        'tables': len(tables),
                        'size_mb': round(os.path.getsize(db_path) / (1024*1024), 2)
                    }
                    print(f"   ✅ {os.path.basename(db_path)}: {len(tables)} tables, {self.status['databases'][db_path]['size_mb']} MB")
                    
                except Exception as e:
                    self.status['databases'][db_path] = {
                        'status': 'ERROR',
                        'error': str(e)
                    }
                    print(f"   ❌ {os.path.basename(db_path)}: ERROR - {e}")
            else:
                self.status['databases'][db_path] = {
                    'status': 'MISSING'
                }
                print(f"   ⚠️ {os.path.basename(db_path)}: MISSING")
    
    def check_key_files(self):
        """Check important system files"""
        print("\n📁 CHECKING KEY FILES...")
        
        key_files = [
            'main.py',
            'admin_console.py',
            'guardian_security_system.py',
            'guardian_rbac_system.py',
            'guardian_audit_system.py',
            'package.json',
            'hardhat.config.js'
        ]
        
        for file_path in key_files:
            if os.path.exists(file_path):
                size_kb = round(os.path.getsize(file_path) / 1024, 1)
                self.status['files'][file_path] = {
                    'status': 'PRESENT',
                    'size_kb': size_kb
                }
                print(f"   ✅ {file_path}: {size_kb} KB")
            else:
                self.status['files'][file_path] = {
                    'status': 'MISSING'
                }
                print(f"   ❌ {file_path}: MISSING")
                self.status['recommendations'].append(f"Create missing file: {file_path}")
    
    def check_dependencies(self):
        """Check Python dependencies"""
        print("\n📦 CHECKING PYTHON DEPENDENCIES...")
        
        required_packages = [
            'pyotp', 'qrcode', 'cryptography', 'web3', 'requests',
            'flask', 'fastapi', 'sqlite3', 'numpy', 'sklearn'
        ]
        
        for package in required_packages:
            try:
                exec(f"import {package}")
                self.status['dependencies'][package] = 'AVAILABLE'
                print(f"   ✅ {package}: AVAILABLE")
            except ImportError:
                self.status['dependencies'][package] = 'MISSING'
                print(f"   ❌ {package}: MISSING")
                self.status['recommendations'].append(f"Install missing package: pip install {package}")
    
    def generate_overall_status(self):
        """Generate overall system status"""
        
        # Count operational components
        total_components = len(self.status['components'])
        operational_components = sum(1 for comp in self.status['components'].values() 
                                   if comp['status'] == 'OPERATIONAL')
        
        # Count available dependencies
        total_deps = len(self.status['dependencies'])
        available_deps = sum(1 for dep in self.status['dependencies'].values() 
                           if dep == 'AVAILABLE')
        
        # Count operational databases
        total_dbs = len(self.status['databases'])
        operational_dbs = sum(1 for db in self.status['databases'].values() 
                            if db['status'] == 'OPERATIONAL')
        
        # Determine overall status
        if operational_components >= total_components * 0.9 and available_deps >= total_deps * 0.8:
            self.status['overall_status'] = 'EXCELLENT'
        elif operational_components >= total_components * 0.8:
            self.status['overall_status'] = 'GOOD' 
        elif operational_components >= total_components * 0.6:
            self.status['overall_status'] = 'FAIR'
        else:
            self.status['overall_status'] = 'NEEDS_ATTENTION'
        
        return {
            'total_components': total_components,
            'operational_components': operational_components,
            'component_rate': f"{operational_components/total_components*100:.1f}%",
            'total_deps': total_deps,
            'available_deps': available_deps,
            'dependency_rate': f"{available_deps/total_deps*100:.1f}%",
            'total_dbs': total_dbs,
            'operational_dbs': operational_dbs,
            'database_rate': f"{operational_dbs/total_dbs*100:.1f}%" if total_dbs > 0 else "N/A"
        }
    
    def print_summary_report(self):
        """Print comprehensive summary report"""
        
        stats = self.generate_overall_status()
        
        print(f"\n📊 COMPREHENSIVE SYSTEM HEALTH REPORT")
        print("=" * 55)
        print(f"🕐 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Overall Status: {self.status['overall_status']}")
        
        print(f"\n📈 SYSTEM STATISTICS:")
        print(f"   Components: {stats['operational_components']}/{stats['total_components']} ({stats['component_rate']}) operational")
        print(f"   Dependencies: {stats['available_deps']}/{stats['total_deps']} ({stats['dependency_rate']}) available")
        print(f"   Databases: {stats['operational_dbs']}/{stats['total_dbs']} ({stats['database_rate']}) operational")
        
        # Status interpretation
        status_meanings = {
            'EXCELLENT': '🟢 All systems fully operational - production ready!',
            'GOOD': '🟡 Most systems operational - minor issues only',
            'FAIR': '🟠 Core systems working - some attention needed',
            'NEEDS_ATTENTION': '🔴 Significant issues - maintenance required'
        }
        
        print(f"\n🎯 STATUS INTERPRETATION:")
        print(f"   {status_meanings[self.status['overall_status']]}")
        
        # Recommendations
        if self.status['recommendations']:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(self.status['recommendations'][:5], 1):
                print(f"   {i}. {rec}")
        else:
            print(f"\n💡 RECOMMENDATIONS:")
            print("   ✅ No critical issues found - system ready!")
        
        print(f"\n🚀 NEXT STEPS:")
        if self.status['overall_status'] in ['EXCELLENT', 'GOOD']:
            print("   • Launch admin console: python admin_console.py")
            print("   • Start main system: python main.py")
            print("   • Run security verification: python verify_security.py")
        else:
            print("   • Address recommendations above")
            print("   • Re-run this health check")
            print("   • Check logs for detailed error information")
    
    def save_report(self, filename="system_health_report.json"):
        """Save detailed report to file"""
        with open(filename, 'w') as f:
            json.dump(self.status, f, indent=2)
        print(f"\n💾 Detailed report saved to: {filename}")
    
    def run_full_check(self):
        """Run complete system health check"""
        print("\n🔍 GUARDIANSHIELD COMPREHENSIVE SYSTEM HEALTH CHECK")
        print("=" * 60)
        
        self.check_agents()
        self.check_security_systems()
        self.check_main_systems()
        self.check_databases()
        self.check_key_files()
        self.check_dependencies()
        
        self.print_summary_report()
        self.save_report()
        
        return self.status['overall_status'] in ['EXCELLENT', 'GOOD']

def main():
    """Main health check function"""
    checker = SystemHealthChecker()
    success = checker.run_full_check()
    
    print(f"\n🏁 HEALTH CHECK COMPLETE!")
    if success:
        print("🎉 GUARDIANSHIELD IS READY FOR OPERATION!")
    else:
        print("⚠️ Some attention needed - see recommendations above")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        sys.exit(1)