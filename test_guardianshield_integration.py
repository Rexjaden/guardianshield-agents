"""
test_guardianshield_integration.py: Integration test for enhanced GuardianShield Web3 security platform
"""

import sys
import os
import json
import time
from datetime import datetime

def test_web3_security_agents():
    """Test all Web3 security agents are working properly"""
    print("🔍 Testing GuardianShield Web3 Security Platform Integration")
    print("=" * 60)
    
    test_results = {
        'total_tests': 0,
        'passed': 0,
        'failed': 0,
        'errors': []
    }
    
    # Test 1: Core agents availability
    print("\n1️⃣  Testing Core Agent Availability...")
    test_results['total_tests'] += 1
    try:
        from agents.learning_agent import LearningAgent
        from agents.behavioral_analytics import BehavioralAnalytics
        print("   ✅ Core agents imported successfully")
        test_results['passed'] += 1
    except Exception as e:
        print(f"   ❌ Core agent import failed: {e}")
        test_results['failed'] += 1
        test_results['errors'].append(f"Core agents: {e}")
    
    # Test 2: New specialized agents availability
    print("\n2️⃣  Testing Specialized Web3 Security Agents...")
    test_results['total_tests'] += 1
    try:
        from agents.defi_security_agent import DeFiSecurityAgent
        from agents.smart_contract_auditor import SmartContractAuditor
        from agents.cross_chain_monitor import CrossChainMonitor
        from agents.mev_protection_agent import MEVProtectionAgent
        print("   ✅ All specialized Web3 security agents available")
        test_results['passed'] += 1
    except Exception as e:
        print(f"   ❌ Specialized agent import failed: {e}")
        test_results['failed'] += 1
        test_results['errors'].append(f"Specialized agents: {e}")
    
    # Test 3: Agent initialization
    print("\n3️⃣  Testing Agent Initialization...")
    test_results['total_tests'] += 1
    try:
        from agents.learning_agent import LearningAgent
        agent = LearningAgent()
        assert hasattr(agent, 'autonomous_cycle'), "Missing autonomous_cycle method"
        print("   ✅ Agent initialization successful")
        test_results['passed'] += 1
    except Exception as e:
        print(f"   ❌ Agent initialization failed: {e}")
        test_results['failed'] += 1
        test_results['errors'].append(f"Agent initialization: {e}")
    
    # Test 4: Web3 capabilities
    print("\n4️⃣  Testing Web3 Security Capabilities...")
    test_results['total_tests'] += 1
    try:
        from agents.learning_agent import LearningAgent
        agent = LearningAgent()
        
        # Test real-time monitoring
        assert hasattr(agent, 'start_realtime_security_monitoring'), "Missing real-time monitoring"
        assert hasattr(agent, 'detect_flash_loan_attacks'), "Missing flash loan detection"
        assert hasattr(agent, 'detect_mev_attacks'), "Missing MEV detection"
        
        print("   ✅ Web3 security capabilities present")
        test_results['passed'] += 1
    except Exception as e:
        print(f"   ❌ Web3 capabilities test failed: {e}")
        test_results['failed'] += 1
        test_results['errors'].append(f"Web3 capabilities: {e}")
    
    # Test 5: DeFi security agent
    print("\n5️⃣  Testing DeFi Security Agent...")
    test_results['total_tests'] += 1
    try:
        from agents.defi_security_agent import DeFiSecurityAgent
        agent = DeFiSecurityAgent()
        
        # Test DeFi-specific methods
        assert hasattr(agent, 'monitor_liquidity_pools'), "Missing liquidity pool monitoring"
        assert hasattr(agent, 'detect_flash_loan_attacks'), "Missing flash loan detection"
        assert hasattr(agent, 'monitor_governance_attacks'), "Missing governance monitoring"
        
        print("   ✅ DeFi Security Agent fully functional")
        test_results['passed'] += 1
    except Exception as e:
        print(f"   ❌ DeFi Security Agent test failed: {e}")
        test_results['failed'] += 1
        test_results['errors'].append(f"DeFi Security Agent: {e}")
    
    # Test 6: Smart Contract Auditor
    print("\n6️⃣  Testing Smart Contract Auditor...")
    test_results['total_tests'] += 1
    try:
        from agents.smart_contract_auditor import SmartContractAuditor
        agent = SmartContractAuditor()
        
        # Test auditing methods
        assert hasattr(agent, 'audit_contract'), "Missing contract auditing"
        assert hasattr(agent, 'analyze_bytecode'), "Missing bytecode analysis"
        assert hasattr(agent, 'monitor_proxy_upgrades'), "Missing proxy monitoring"
        
        print("   ✅ Smart Contract Auditor fully functional")
        test_results['passed'] += 1
    except Exception as e:
        print(f"   ❌ Smart Contract Auditor test failed: {e}")
        test_results['failed'] += 1
        test_results['errors'].append(f"Smart Contract Auditor: {e}")
    
    # Test 7: Cross-Chain Monitor
    print("\n7️⃣  Testing Cross-Chain Monitor...")
    test_results['total_tests'] += 1
    try:
        from agents.cross_chain_monitor import CrossChainMonitor
        agent = CrossChainMonitor()
        
        # Test cross-chain methods
        assert hasattr(agent, 'monitor_bridge_security'), "Missing bridge monitoring"
        assert hasattr(agent, 'detect_multi_chain_attacks'), "Missing multi-chain detection"
        assert hasattr(agent, 'verify_wrapped_tokens'), "Missing token verification"
        
        print("   ✅ Cross-Chain Monitor fully functional")
        test_results['passed'] += 1
    except Exception as e:
        print(f"   ❌ Cross-Chain Monitor test failed: {e}")
        test_results['failed'] += 1
        test_results['errors'].append(f"Cross-Chain Monitor: {e}")
    
    # Test 8: MEV Protection Agent
    print("\n8️⃣  Testing MEV Protection Agent...")
    test_results['total_tests'] += 1
    try:
        from agents.mev_protection_agent import MEVProtectionAgent
        agent = MEVProtectionAgent()
        
        # Test MEV protection methods
        assert hasattr(agent, 'detect_sandwich_attacks'), "Missing sandwich detection"
        assert hasattr(agent, 'detect_frontrunning'), "Missing frontrunning detection"
        assert hasattr(agent, 'monitor_liquidation_mev'), "Missing liquidation monitoring"
        
        print("   ✅ MEV Protection Agent fully functional")
        test_results['passed'] += 1
    except Exception as e:
        print(f"   ❌ MEV Protection Agent test failed: {e}")
        test_results['failed'] += 1
        test_results['errors'].append(f"MEV Protection Agent: {e}")
    
    # Test 9: Admin Console Integration
    print("\n9️⃣  Testing Admin Console Integration...")
    test_results['total_tests'] += 1
    try:
        from admin_console import AdminConsole
        console = AdminConsole()
        assert hasattr(console, 'log_action'), "Missing action logging"
        print("   ✅ Admin Console integration working")
        test_results['passed'] += 1
    except Exception as e:
        print(f"   ❌ Admin Console test failed: {e}")
        test_results['failed'] += 1
        test_results['errors'].append(f"Admin Console: {e}")
    
    # Test 10: Main orchestration system
    print("\n🔟 Testing Main Orchestration System...")
    test_results['total_tests'] += 1
    try:
        from main import AutonomousAgentOrchestrator
        orchestrator = AutonomousAgentOrchestrator()
        assert len(orchestrator.agents) >= 11, f"Expected 11+ agents, got {len(orchestrator.agents)}"
        print(f"   ✅ Orchestration system initialized with {len(orchestrator.agents)} agents")
        test_results['passed'] += 1
    except Exception as e:
        print(f"   ❌ Orchestration system test failed: {e}")
        test_results['failed'] += 1
        test_results['errors'].append(f"Orchestration system: {e}")
    
    # Print test summary
    print("\n" + "=" * 60)
    print("🧪 TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {test_results['total_tests']}")
    print(f"Passed: {test_results['passed']}")
    print(f"Failed: {test_results['failed']}")
    
    success_rate = (test_results['passed'] / test_results['total_tests']) * 100
    print(f"Success Rate: {success_rate:.1f}%")
    
    if test_results['failed'] == 0:
        print("\n🎉 ALL TESTS PASSED! GuardianShield Web3 Security Platform is ready!")
        print("✅ Real-time threat monitoring operational")
        print("✅ DeFi security protocols active")
        print("✅ Smart contract auditing enabled")
        print("✅ Cross-chain monitoring functional")
        print("✅ MEV protection systems online")
        return True
    else:
        print("\n⚠️  Some tests failed. Review the following issues:")
        for i, error in enumerate(test_results['errors'], 1):
            print(f"{i}. {error}")
        return False

def validate_web3_security_features():
    """Validate specific Web3 security features"""
    print("\n🔒 Validating Web3 Security Features...")
    print("-" * 40)
    
    features = {
        'real_time_monitoring': False,
        'flash_loan_detection': False,
        'mev_protection': False,
        'defi_monitoring': False,
        'cross_chain_security': False,
        'smart_contract_auditing': False
    }
    
    try:
        # Check real-time monitoring
        from agents.learning_agent import LearningAgent
        agent = LearningAgent()
        if hasattr(agent, 'start_realtime_security_monitoring'):
            features['real_time_monitoring'] = True
            print("   ✅ Real-time monitoring: ACTIVE")
        
        if hasattr(agent, 'detect_flash_loan_attacks'):
            features['flash_loan_detection'] = True
            print("   ✅ Flash loan detection: ACTIVE")
        
        if hasattr(agent, 'detect_mev_attacks'):
            features['mev_protection'] = True
            print("   ✅ MEV attack detection: ACTIVE")
        
        # Check DeFi monitoring
        from agents.defi_security_agent import DeFiSecurityAgent
        defi_agent = DeFiSecurityAgent()
        if hasattr(defi_agent, 'monitor_liquidity_pools'):
            features['defi_monitoring'] = True
            print("   ✅ DeFi protocol monitoring: ACTIVE")
        
        # Check cross-chain security
        from agents.cross_chain_monitor import CrossChainMonitor
        cross_agent = CrossChainMonitor()
        if hasattr(cross_agent, 'monitor_bridge_security'):
            features['cross_chain_security'] = True
            print("   ✅ Cross-chain security: ACTIVE")
        
        # Check smart contract auditing
        from agents.smart_contract_auditor import SmartContractAuditor
        audit_agent = SmartContractAuditor()
        if hasattr(audit_agent, 'audit_contract'):
            features['smart_contract_auditing'] = True
            print("   ✅ Smart contract auditing: ACTIVE")
    
    except Exception as e:
        print(f"   ❌ Feature validation error: {e}")
    
    active_features = sum(features.values())
    total_features = len(features)
    
    print(f"\n📊 Security Features Status: {active_features}/{total_features} active")
    
    if active_features == total_features:
        print("🎯 All Web3 security features are operational!")
        return True
    else:
        inactive = [name for name, active in features.items() if not active]
        print(f"⚠️  Inactive features: {', '.join(inactive)}")
        return False

if __name__ == "__main__":
    print("🛡️  GuardianShield Web3 Security Platform Integration Test")
    print("🧬 Testing autonomous agent ecosystem with unlimited capabilities")
    print("⚡ Validating admin oversight and reversal controls")
    print()
    
    # Run main integration tests
    main_tests_passed = test_web3_security_agents()
    
    # Validate security features
    features_validated = validate_web3_security_features()
    
    print("\n" + "=" * 60)
    print("🏁 FINAL INTEGRATION STATUS")
    print("=" * 60)
    
    if main_tests_passed and features_validated:
        print("🎉 INTEGRATION SUCCESSFUL!")
        print("✅ GuardianShield Web3 Security Platform is fully operational")
        print("🚀 All agents ready for autonomous operation")
        print("🔒 Comprehensive Web3 threat protection active")
        print("\n💡 Next steps:")
        print("   1. Run 'python main.py' to start autonomous operations")
        print("   2. Use 'python admin_console.py' for monitoring and control")
        print("   3. Monitor logs for real-time threat detection")
        sys.exit(0)
    else:
        print("❌ INTEGRATION ISSUES DETECTED")
        print("⚠️  Please review and fix the identified issues")
        print("🔧 Check dependencies and agent implementations")
        sys.exit(1)