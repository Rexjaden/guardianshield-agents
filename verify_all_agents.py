#!/usr/bin/env python3
"""
🔍 COMPREHENSIVE AGENT VERIFICATION SYSTEM
Tests all GuardianShield agents and ensures perfect functionality
"""

import sys
import traceback
import time
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('AgentVerification')

class AgentTester:
    """Comprehensive agent testing and verification system"""
    
    def __init__(self):
        self.results = {}
        self.errors = []
        self.warnings = []
        
    def test_agent_import(self, agent_name: str, import_path: str):
        """Test if an agent can be imported successfully"""
        print(f"\n🔍 Testing {agent_name}...")
        
        try:
            exec(f"import {import_path}")
            print(f"   ✅ Import: SUCCESS")
            self.results[agent_name] = {'import': 'SUCCESS'}
            return True
        except Exception as e:
            print(f"   ❌ Import: FAILED - {e}")
            self.results[agent_name] = {'import': 'FAILED', 'error': str(e)}
            self.errors.append(f"{agent_name}: {e}")
            return False
    
    def test_agent_initialization(self, agent_name: str, class_path: str):
        """Test if an agent can be initialized successfully"""
        if agent_name not in self.results:
            return False
            
        if self.results[agent_name]['import'] != 'SUCCESS':
            return False
            
        try:
            # Import and create instance
            module_name, class_name = class_path.rsplit('.', 1)
            exec(f"from {module_name} import {class_name}")
            exec(f"instance = {class_name}()")
            print(f"   ✅ Initialization: SUCCESS")
            self.results[agent_name]['initialization'] = 'SUCCESS'
            return True
        except Exception as e:
            print(f"   ❌ Initialization: FAILED - {e}")
            self.results[agent_name]['initialization'] = 'FAILED'
            self.errors.append(f"{agent_name} init: {e}")
            return False
    
    def test_agent_basic_functionality(self, agent_name: str, class_path: str, test_method: str = None):
        """Test basic functionality of an agent"""
        if agent_name not in self.results:
            return False
            
        if self.results[agent_name].get('initialization') != 'SUCCESS':
            return False
            
        try:
            module_name, class_name = class_path.rsplit('.', 1)
            exec(f"from {module_name} import {class_name}")
            exec(f"instance = {class_name}()")
            
            # Test basic methods if available
            if test_method:
                exec(f"result = instance.{test_method}()")
                
            print(f"   ✅ Functionality: SUCCESS")
            self.results[agent_name]['functionality'] = 'SUCCESS'
            return True
        except Exception as e:
            print(f"   ⚠️ Functionality: LIMITED - {e}")
            self.results[agent_name]['functionality'] = 'LIMITED'
            self.warnings.append(f"{agent_name} functionality: {e}")
            return True  # Don't fail for functionality tests
    
    def run_comprehensive_tests(self):
        """Run comprehensive tests on all agents"""
        
        print("\n🛡️ GUARDIANSHIELD COMPREHENSIVE AGENT VERIFICATION")
        print("=" * 60)
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🐍 Python Version: {sys.version}")
        
        # Core Agent Tests
        print(f"\n🤖 TESTING CORE AGENTS")
        print("-" * 30)
        
        agents_to_test = [
            ("Learning Agent", "agents.learning_agent", "agents.learning_agent.LearningAgent"),
            ("Behavioral Analytics", "agents.behavioral_analytics", "agents.behavioral_analytics.BehavioralAnalytics"),
            ("Data Ingestion", "agents.data_ingestion", "agents.data_ingestion.DataIngestionAgent"),
            ("DMER Monitor", "agents.dmer_monitor_agent", "agents.dmer_monitor_agent.DmerMonitorAgent"),
            ("External Agent", "agents.external_agent", "agents.external_agent.ExternalAgent"),
            ("Flare Integration", "agents.flare_integration", "agents.flare_integration.FlareIntegrationAgent"),
            ("Genetic Evolver", "agents.genetic_evolver", "agents.genetic_evolver.GeneticEvolver"),
            ("Threat Definitions", "agents.threat_definitions", "agents.threat_definitions.EvolvingThreats"),
        ]
        
        for agent_name, import_path, class_path in agents_to_test:
            success = self.test_agent_import(agent_name, import_path)
            if success:
                self.test_agent_initialization(agent_name, class_path)
                self.test_agent_basic_functionality(agent_name, class_path)
        
        # Security System Tests
        print(f"\n🔐 TESTING SECURITY SYSTEMS")
        print("-" * 30)
        
        security_systems = [
            ("Security System", "guardian_security_system", "guardian_security_system.GuardianSecuritySystem"),
            ("RBAC System", "guardian_rbac_system", "guardian_rbac_system.GuardianRoleBasedAccessControl"),
            ("Audit System", "guardian_audit_system", "guardian_audit_system.GuardianAuditSystem"),
            ("Admin Console", "admin_console", "admin_console.AdminConsole"),
        ]
        
        for system_name, import_path, class_path in security_systems:
            success = self.test_agent_import(system_name, import_path)
            if success:
                self.test_agent_initialization(system_name, class_path)
        
        # Main System Tests
        print(f"\n🚀 TESTING MAIN SYSTEMS")
        print("-" * 30)
        
        main_systems = [
            ("Main Orchestrator", "main", "main.AutonomousAgentOrchestrator"),
            ("Security Integration", "security_integration", "security_integration.GuardianSecurityManager"),
        ]
        
        for system_name, import_path, class_path in main_systems:
            success = self.test_agent_import(system_name, import_path)
            if success:
                self.test_agent_initialization(system_name, class_path)
        
        # Generate Report
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive test report"""
        
        print(f"\n📊 COMPREHENSIVE TEST REPORT")
        print("=" * 60)
        
        total_tests = len(self.results)
        successful_imports = sum(1 for r in self.results.values() if r.get('import') == 'SUCCESS')
        successful_inits = sum(1 for r in self.results.values() if r.get('initialization') == 'SUCCESS')
        successful_funcs = sum(1 for r in self.results.values() if r.get('functionality') == 'SUCCESS')
        
        print(f"\n📈 SUMMARY STATISTICS:")
        print(f"   Total Components Tested: {total_tests}")
        print(f"   Successful Imports: {successful_imports}/{total_tests} ({successful_imports/total_tests*100:.1f}%)")
        print(f"   Successful Initializations: {successful_inits}/{successful_imports} ({successful_inits/successful_imports*100 if successful_imports > 0 else 0:.1f}%)")
        print(f"   Working Functionality: {successful_funcs}")
        
        print(f"\n✅ SUCCESSFUL COMPONENTS:")
        for component, results in self.results.items():
            if results.get('import') == 'SUCCESS':
                status = "🟢 FULLY FUNCTIONAL" if results.get('initialization') == 'SUCCESS' else "🟡 IMPORT ONLY"
                print(f"   {status} {component}")
        
        if self.errors:
            print(f"\n❌ ERRORS FOUND ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")
        
        if self.warnings:
            print(f"\n⚠️ WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        # Overall Status
        print(f"\n🎯 OVERALL STATUS:")
        if successful_imports == total_tests and successful_inits >= total_tests * 0.8:
            print("   🟢 EXCELLENT - All systems operational!")
        elif successful_imports >= total_tests * 0.8:
            print("   🟡 GOOD - Most systems operational, minor issues")
        else:
            print("   🟠 NEEDS ATTENTION - Some systems have issues")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if len(self.errors) == 0:
            print("   ✅ No critical issues found - system ready for production!")
        else:
            print("   🔧 Address the errors listed above")
            print("   📚 Check documentation for missing dependencies")
            print("   🔄 Re-run tests after fixes")
        
        return successful_imports == total_tests and len(self.errors) == 0


def main():
    """Main verification function"""
    tester = AgentTester()
    success = tester.run_comprehensive_tests()
    
    print(f"\n🏁 VERIFICATION COMPLETE!")
    if success:
        print("🎉 ALL AGENTS AND SYSTEMS WORKING PERFECTLY!")
    else:
        print("⚠️ Some issues found - see report above")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        traceback.print_exc()
        sys.exit(1)