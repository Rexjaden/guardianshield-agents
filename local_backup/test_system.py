#!/usr/bin/env python3
"""
test_system.py: Simple test to verify the GuardianShield autonomous system works correctly.
"""

import sys
import os
import time
from admin_console import AdminConsole

def test_admin_console():
    """Test admin console functionality"""
    print("🧪 Testing Admin Console...")
    
    try:
        console = AdminConsole()
        
        # Test logging
        action_id = console.log_action(
            "test_agent",
            "system_test",
            {"test": True, "status": "running"},
            severity=3
        )
        print(f"✅ Action logged with ID: {action_id}")
        
        # Test evolution logging
        console.log_evolution_decision(
            "test_agent",
            "test_evolution",
            {"type": "capability_enhancement", "confidence": 0.9}
        )
        print("✅ Evolution decision logged")
        
        # Test decision logging
        console.log_autonomous_decision(
            "test_agent",
            "test_decision",
            {"confidence": 0.8, "factors": ["test_factor"]},
            {"action": "test_action", "reversible": True}
        )
        print("✅ Autonomous decision logged")
        
        return True
        
    except Exception as e:
        print(f"❌ Admin console test failed: {e}")
        return False

def test_basic_imports():
    """Test that all basic agent imports work"""
    print("🧪 Testing Basic Imports...")
    
    try:
        from agents.learning_agent import LearningAgent
        print("✅ LearningAgent imported")
        
        from agents.behavioral_analytics import BehavioralAnalytics
        print("✅ BehavioralAnalytics imported")
        
        from agents.genetic_evolver import GeneticEvolver
        print("✅ GeneticEvolver imported")
        
        from agents.data_ingestion import DataIngestionAgent
        print("✅ DataIngestionAgent imported")
        
        from agents.dmer_monitor_agent import DmerMonitorAgent
        print("✅ DmerMonitorAgent imported")
        
        from agents.external_agent import ExternalAgent
        print("✅ ExternalAgent imported")
        
        from agents.flare_integration import FlareIntegrationAgent
        print("✅ FlareIntegrationAgent imported")
        
        from agents.threat_definitions import evolving_threats
        print("✅ Threat definitions imported")
        
        from agents.utils import SecureStorage, DataValidator
        print("✅ Utils imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_agent_initialization():
    """Test that agents can be initialized"""
    print("🧪 Testing Agent Initialization...")
    
    try:
        from agents.learning_agent import LearningAgent
        agent = LearningAgent()
        print("✅ LearningAgent initialized")
        
        from agents.behavioral_analytics import BehavioralAnalytics
        ba = BehavioralAnalytics()
        print("✅ BehavioralAnalytics initialized")
        
        from agents.utils import SecureStorage
        storage = SecureStorage()
        print("✅ SecureStorage initialized")
        
        # Test encryption/decryption
        test_data = {"test": "data", "number": 42}
        encrypted = storage.encrypt_data(test_data)
        decrypted = storage.decrypt_data(encrypted)
        
        if decrypted == test_data:
            print("✅ Encryption/decryption working")
        else:
            print("❌ Encryption/decryption failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Agent initialization test failed: {e}")
        return False

def test_system_startup():
    """Test that the main system can start"""
    print("🧪 Testing System Startup (dry run)...")
    
    try:
        # Import the orchestrator class without running it
        from main import AutonomousAgentOrchestrator
        
        orchestrator = AutonomousAgentOrchestrator()
        print("✅ AutonomousAgentOrchestrator initialized")
        
        # Test that agents are initialized
        agent_count = len(orchestrator.agents)
        print(f"✅ {agent_count} agents initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ System startup test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🛡️  GuardianShield System Test Suite")
    print("=" * 50)
    
    tests = [
        ("Admin Console", test_admin_console),
        ("Basic Imports", test_basic_imports),
        ("Agent Initialization", test_agent_initialization),
        ("System Startup", test_system_startup)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! GuardianShield system is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())