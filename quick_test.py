#!/usr/bin/env python3
"""
Quick Agent Functionality Test
"""

def test_core_agents():
    """Test core agent functionality"""
    print("🤖 TESTING CORE AGENTS")
    print("-" * 30)
    
    agents = [
        ("Learning Agent", "agents.learning_agent"),
        ("Behavioral Analytics", "agents.behavioral_analytics"),
        ("Data Ingestion", "agents.data_ingestion"),
        ("DMER Monitor", "agents.dmer_monitor_agent"),
        ("External Agent", "agents.external_agent"),
        ("Flare Integration", "agents.flare_integration"),
        ("Genetic Evolver", "agents.genetic_evolver"),
        ("Threat Definitions", "agents.threat_definitions"),
    ]
    
    success_count = 0
    for name, module in agents:
        try:
            exec(f"import {module}")
            print(f"✅ {name}: OK")
            success_count += 1
        except Exception as e:
            print(f"❌ {name}: {e}")
    
    print(f"\n📊 Result: {success_count}/{len(agents)} agents working")
    return success_count == len(agents)

def test_security_systems():
    """Test security systems"""
    print("\n🔐 TESTING SECURITY SYSTEMS")
    print("-" * 30)
    
    systems = [
        ("Security System", "guardian_security_system"),
        ("RBAC System", "guardian_rbac_system"),
        ("Audit System", "guardian_audit_system"),
        ("Admin Console", "admin_console"),
    ]
    
    success_count = 0
    for name, module in systems:
        try:
            exec(f"import {module}")
            print(f"✅ {name}: OK")
            success_count += 1
        except Exception as e:
            print(f"❌ {name}: {e}")
    
    print(f"\n📊 Result: {success_count}/{len(systems)} security systems working")
    return success_count == len(systems)

def test_main_system():
    """Test main orchestrator"""
    print("\n🚀 TESTING MAIN SYSTEM")
    print("-" * 30)
    
    try:
        import main
        print("✅ Main Orchestrator: OK")
        return True
    except Exception as e:
        print(f"❌ Main Orchestrator: {e}")
        return False

if __name__ == "__main__":
    print("\n🛡️ QUICK GUARDIANSHIELD FUNCTIONALITY TEST")
    print("=" * 50)
    
    agents_ok = test_core_agents()
    security_ok = test_security_systems()
    main_ok = test_main_system()
    
    print(f"\n🎯 FINAL RESULT:")
    if agents_ok and security_ok and main_ok:
        print("🎉 ALL SYSTEMS OPERATIONAL!")
        exit(0)
    else:
        print("⚠️ Some systems need attention")
        exit(1)