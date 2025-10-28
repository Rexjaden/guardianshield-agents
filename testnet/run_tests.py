# ERC-8055 Testnet Execution Script
import json
import time
import subprocess
import sys
from datetime import datetime

def run_testnet_deployment():
    """Deploy contract to testnet"""
    print("🚀 Deploying ERC-8055 to Sepolia Testnet...")
    
    try:
        # Run deployment script
        result = subprocess.run([sys.executable, "deploy.py"], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Contract deployed successfully!")
            print(result.stdout)
            return True
        else:
            print("❌ Deployment failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        return False

def run_agent_deployment():
    """Start monitoring agents"""
    print("🤖 Starting monitoring agents...")
    
    try:
        # Start agents in background
        process = subprocess.Popen([sys.executable, "monitoring_agents.py"],
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # Give agents time to initialize
        time.sleep(5)
        
        if process.poll() is None:  # Process is still running
            print("✅ Monitoring agents started successfully!")
            return process
        else:
            print("❌ Agents failed to start")
            return None
    except Exception as e:
        print(f"❌ Agent deployment error: {e}")
        return None

def run_test_scenarios(iterations=5):
    """Execute test scenarios multiple times"""
    print(f"🧪 Running test scenarios ({iterations} iterations)...")
    
    try:
        # Import and run test suite
        from test_scenarios import ERC8055TestSuite
        
        # Replace with actual deployed contract address
        with open("deployment_sepolia.json", "r") as f:
            deployment_info = json.load(f)
        
        contract_address = deployment_info["contract_address"]
        
        test_suite = ERC8055TestSuite(contract_address, "sepolia")
        results = test_suite.run_full_test_suite(iterations=iterations)
        
        return results
    except Exception as e:
        print(f"❌ Test execution error: {e}")
        return None

def analyze_test_consistency(results):
    """Analyze test results for consistency across iterations"""
    print("\n📈 Consistency Analysis Across Iterations")
    print("=" * 60)
    
    scenarios = ["Normal Minting", "Theft Detection & Burn", "Remint to Treasury", 
                "Ownership Verification", "Ownership Recovery"]
    
    consistency_report = {}
    
    for i, scenario in enumerate(scenarios):
        scenario_results = [iteration[i] for iteration in results]
        
        # Success rate consistency
        success_rates = [r.success for r in scenario_results]
        success_consistency = all(success_rates) or not any(success_rates)  # All pass or all fail
        
        # Execution time variance
        exec_times = [r.execution_time for r in scenario_results]
        avg_time = sum(exec_times) / len(exec_times)
        time_variance = sum((t - avg_time) ** 2 for t in exec_times) / len(exec_times)
        time_std_dev = time_variance ** 0.5
        
        # Agent response time consistency (if applicable)
        agent_times = [getattr(r, 'agent_response_time', 0) for r in scenario_results]
        agent_times = [t for t in agent_times if t > 0]
        
        if agent_times:
            avg_agent_time = sum(agent_times) / len(agent_times)
            agent_variance = sum((t - avg_agent_time) ** 2 for t in agent_times) / len(agent_times)
            agent_std_dev = agent_variance ** 0.5
        else:
            avg_agent_time = 0
            agent_std_dev = 0
        
        # Serial preservation consistency
        serial_preservation = [getattr(r, 'serial_preserved', True) for r in scenario_results]
        serial_consistency = all(serial_preservation)
        
        consistency_report[scenario] = {
            "success_consistency": success_consistency,
            "avg_execution_time": avg_time,
            "execution_time_std_dev": time_std_dev,
            "avg_agent_response": avg_agent_time,
            "agent_response_std_dev": agent_std_dev,
            "serial_preservation_rate": sum(serial_preservation) / len(serial_preservation),
            "overall_stability": success_consistency and time_std_dev < 1.0 and serial_consistency
        }
        
        print(f"\n{scenario}:")
        print(f"  ✓ Success Consistency: {'STABLE' if success_consistency else 'VARIABLE'}")
        print(f"  ⏱️  Avg Execution Time: {avg_time:.3f}s (±{time_std_dev:.3f}s)")
        if avg_agent_time > 0:
            print(f"  🤖 Avg Agent Response: {avg_agent_time:.3f}s (±{agent_std_dev:.3f}s)")
        print(f"  🔢 Serial Preservation: {sum(serial_preservation)}/{len(serial_preservation)} ({sum(serial_preservation)/len(serial_preservation):.1%})")
        print(f"  📊 Overall Stability: {'STABLE' if consistency_report[scenario]['overall_stability'] else 'NEEDS REVIEW'}")
    
    return consistency_report

def generate_test_report(results, consistency_report):
    """Generate comprehensive test report"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"testnet_report_{timestamp}.json"
    
    report = {
        "timestamp": timestamp,
        "test_summary": {
            "total_iterations": len(results),
            "scenarios_tested": len(results[0]) if results else 0,
            "total_tests": len(results) * len(results[0]) if results else 0
        },
        "consistency_analysis": consistency_report,
        "detailed_results": [
            [{
                "scenario": r.scenario,
                "success": r.success,
                "execution_time": r.execution_time,
                "agent_response_time": getattr(r, 'agent_response_time', 0),
                "serial_preserved": getattr(r, 'serial_preserved', True),
                "details": r.details
            } for r in iteration] for iteration in results
        ],
        "recommendations": []
    }
    
    # Add recommendations based on results
    if consistency_report:
        for scenario, analysis in consistency_report.items():
            if not analysis["overall_stability"]:
                report["recommendations"].append({
                    "scenario": scenario,
                    "issue": "Stability concerns detected",
                    "suggestion": "Review agent logic and add additional error handling"
                })
            
            if analysis["execution_time_std_dev"] > 2.0:
                report["recommendations"].append({
                    "scenario": scenario,
                    "issue": "High execution time variance",
                    "suggestion": "Optimize performance and investigate bottlenecks"
                })
    
    # Save report
    with open(report_filename, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Test report saved: {report_filename}")
    return report

def main():
    """Main testnet execution function"""
    print("🛡️ ERC-8055 Testnet Testing Suite")
    print("=" * 50)
    print(f"Started at: {datetime.now()}")
    
    # Step 1: Deploy contract
    if not run_testnet_deployment():
        print("❌ Cannot proceed without successful deployment")
        return
    
    # Step 2: Deploy monitoring agents
    agent_process = run_agent_deployment()
    if not agent_process:
        print("⚠️ Proceeding without agents (limited functionality)")
    
    # Step 3: Execute test scenarios
    test_results = run_test_scenarios(iterations=5)
    if not test_results:
        print("❌ Test execution failed")
        return
    
    # Step 4: Analyze consistency
    consistency_report = analyze_test_consistency(test_results)
    
    # Step 5: Generate report
    final_report = generate_test_report(test_results, consistency_report)
    
    # Step 6: Cleanup
    if agent_process:
        print("\n🛑 Stopping monitoring agents...")
        agent_process.terminate()
    
    # Final summary
    print(f"\n🎉 Testnet testing completed!")
    print(f"📊 Results: {len(test_results)} iterations, {len(test_results[0])} scenarios each")
    
    stable_scenarios = sum(1 for analysis in consistency_report.values() if analysis["overall_stability"])
    total_scenarios = len(consistency_report)
    
    print(f"✅ Stable scenarios: {stable_scenarios}/{total_scenarios}")
    
    if stable_scenarios == total_scenarios:
        print("🎯 All scenarios showing consistent behavior - Ready for mainnet!")
    else:
        print("⚠️ Some scenarios need review before mainnet deployment")

if __name__ == "__main__":
    main()