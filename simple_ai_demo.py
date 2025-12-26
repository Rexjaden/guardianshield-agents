"""
Advanced AI Agents Demo - Simple Version
"""

import asyncio
import sys
import json
from datetime import datetime

sys.path.append('agents')

async def simple_ai_demo():
    """Simple demonstration of advanced AI capabilities"""
    
    print("ADVANCED AI AGENTS DEMONSTRATION")
    print("=" * 50)
    
    # Import the advanced AI system
    try:
        from advanced_ai_agents import AdvancedAIAgentManager
        
        # Initialize system
        print("\nInitializing Advanced AI System...")
        manager = AdvancedAIAgentManager()
        await manager.initialize()
        print("System initialized successfully!")
        
        # Test case 1: Malware detection
        print("\nTest Case 1: MALWARE DETECTION")
        print("-" * 30)
        
        malware_data = {
            'id': 'test_malware_001',
            'threat_type': 'malware',
            'features': [0.9, 0.8, 0.7, 0.6],
            'metadata': {
                'network': {
                    'connection_count': 1500,
                    'tcp_ratio': 0.9,
                    'common_ports_ratio': 0.2,
                    'geographic_diversity': 0.8,
                    'bandwidth_usage': 5000000
                },
                'behavioral': {
                    'activity_anomaly_score': 0.85,
                    'access_pattern_score': 0.9,
                    'time_anomaly_score': 0.7,
                    'privilege_usage_score': 0.8,
                    'data_access_volume': 15000
                }
            }
        }
        
        result1 = await manager.process_threat_data(malware_data)
        
        print(f"Threat Detected: {result1.threat_detected}")
        if result1.threat_detected:
            print(f"Threat Type: {result1.threat_type.value}")
            print(f"Confidence: {result1.confidence:.2%}")
            print(f"Severity: {result1.severity.name}")
            print(f"Features Used: {', '.join(result1.features_used)}")
            print(f"Top Recommendation: {result1.recommended_actions[0]}")
        
        # Test case 2: DeFi exploit detection
        print("\nTest Case 2: DEFI EXPLOIT DETECTION")
        print("-" * 30)
        
        defi_data = {
            'id': 'test_defi_001',
            'threat_type': 'defi_exploit',
            'features': [0.8, 0.9, 0.85],
            'metadata': {
                'blockchain': {
                    'transaction_volume': 2000000,
                    'gas_efficiency': 0.3,
                    'contract_call_frequency': 150,
                    'value_transfer_anomaly': 0.9,
                    'mev_detection_score': 0.85
                }
            }
        }
        
        result2 = await manager.process_threat_data(defi_data)
        
        print(f"Threat Detected: {result2.threat_detected}")
        if result2.threat_detected:
            print(f"Threat Type: {result2.threat_type.value}")
            print(f"Confidence: {result2.confidence:.2%}")
            print(f"Severity: {result2.severity.name}")
            print(f"Features Used: {', '.join(result2.features_used)}")
            print(f"Top Recommendation: {result2.recommended_actions[0]}")
        
        # Show system status
        print("\nSYSTEM STATUS")
        print("-" * 30)
        status = manager.get_system_status()
        print(f"Learning Active: {status['learning_active']}")
        print(f"Models Loaded: {len(status['detection_engine']['models'])}")
        print(f"Patterns Learned: {status['detection_engine']['learning_metrics']['patterns_learned']}")
        
        # Show model details
        print("\nMODEL CAPABILITIES")
        print("-" * 30)
        for model_name, model_info in status['detection_engine']['models'].items():
            print(f"{model_name}: {model_info['accuracy']:.1%} accuracy ({model_info['type']})")
        
        print("\nAdvanced AI Agents demonstration complete!")
        return True
        
    except Exception as e:
        print(f"Error in demonstration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(simple_ai_demo())