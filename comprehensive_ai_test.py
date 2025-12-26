"""
Comprehensive AI Agents Testing
Testing the learning improvements after several days of operation
"""
import sys
sys.path.append('agents')
import asyncio
from advanced_ai_agents import AdvancedAIAgentManager

async def comprehensive_ai_test():
    print("=" * 60)
    print("COMPREHENSIVE AI AGENTS TESTING")
    print("Testing learning improvements after several days")
    print("=" * 60)
    
    manager = AdvancedAIAgentManager()
    await manager.initialize()
    
    # Get system status first
    status = manager.get_system_status()
    print(f"\nSYSTEM STATUS:")
    print(f"Learning Active: {status['learning_active']}")
    print(f"Models Loaded: {len(status['detection_engine']['models'])}")
    
    # Test scenarios with different threat types and severities
    test_scenarios = [
        {
            'name': 'Low Risk Network Activity',
            'data': {
                'id': 'test_low_001',
                'threat_type': 'malware',
                'features': [0.2, 0.1, 0.3],
                'metadata': {
                    'network': {
                        'connection_count': 5,
                        'tcp_ratio': 0.7,
                        'common_ports_ratio': 0.95,
                        'geographic_diversity': 0.1,
                        'bandwidth_usage': 500
                    }
                }
            }
        },
        {
            'name': 'Suspicious Phishing Email',
            'data': {
                'id': 'test_phishing_001',
                'threat_type': 'phishing',
                'features': [0.85, 0.9, 0.8],
                'metadata': {
                    'content': {
                        'content_similarity': 0.92,
                        'language_anomaly_score': 0.85,
                        'metadata_consistency': 0.3,
                        'compression_ratio': 0.7
                    }
                }
            }
        },
        {
            'name': 'DDoS Attack Pattern',
            'data': {
                'id': 'test_ddos_001',
                'threat_type': 'ddos',
                'features': [0.95, 0.88, 0.92],
                'metadata': {
                    'network': {
                        'connection_count': 5000,
                        'tcp_ratio': 0.98,
                        'common_ports_ratio': 0.05,
                        'geographic_diversity': 0.95,
                        'bandwidth_usage': 50000000
                    },
                    'temporal': {
                        'event_frequency': 200,
                        'burst_score': 0.95,
                        'time_of_day_anomaly': 0.8
                    }
                }
            }
        },
        {
            'name': 'Insider Threat Behavior',
            'data': {
                'id': 'test_insider_001',
                'threat_type': 'insider_threat',
                'features': [0.8, 0.9, 0.75],
                'metadata': {
                    'behavioral': {
                        'activity_anomaly_score': 0.88,
                        'access_pattern_score': 0.92,
                        'time_anomaly_score': 0.85,
                        'privilege_usage_score': 0.9,
                        'data_access_volume': 30000
                    }
                }
            }
        },
        {
            'name': 'Smart Contract Exploit',
            'data': {
                'id': 'test_contract_001',
                'threat_type': 'smart_contract_vulnerability',
                'features': [0.9, 0.85, 0.88],
                'metadata': {
                    'blockchain': {
                        'transaction_volume': 8000000,
                        'gas_efficiency': 0.2,
                        'contract_call_frequency': 400,
                        'value_transfer_anomaly': 0.9,
                        'mev_detection_score': 0.88
                    }
                }
            }
        },
        {
            'name': 'Advanced DeFi Flash Loan Attack',
            'data': {
                'id': 'test_defi_advanced_001',
                'threat_type': 'defi_exploit',
                'features': [0.98, 0.95, 0.92],
                'metadata': {
                    'blockchain': {
                        'transaction_volume': 15000000,
                        'gas_efficiency': 0.1,
                        'contract_call_frequency': 600,
                        'value_transfer_anomaly': 0.97,
                        'mev_detection_score': 0.95
                    },
                    'temporal': {
                        'event_frequency': 300,
                        'burst_score': 0.98,
                        'duration_anomaly_score': 0.9
                    }
                }
            }
        }
    ]
    
    print(f"\nTEST RESULTS:")
    print("-" * 60)
    
    detection_count = 0
    total_confidence = 0
    severity_counts = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'CRITICAL': 0, 'EMERGENCY': 0}
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print("-" * 40)
        
        result = await manager.process_threat_data(scenario['data'])
        
        print(f"Threat Detected: {'YES' if result.threat_detected else 'NO'}")
        
        if result.threat_detected:
            detection_count += 1
            total_confidence += result.confidence
            severity_counts[result.severity.name] += 1
            
            print(f"Classified As: {result.threat_type.value}")
            print(f"Confidence: {result.confidence:.1%}")
            print(f"Severity: {result.severity.name}")
            print(f"Features Used: {', '.join(result.features_used)}")
            print(f"Primary Action: {result.recommended_actions[0] if result.recommended_actions else 'None'}")
        else:
            print("No threat detected - Normal activity")
    
    # Summary statistics
    print(f"\n" + "=" * 60)
    print("TESTING SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {len(test_scenarios)}")
    print(f"Threats Detected: {detection_count}")
    print(f"Detection Rate: {(detection_count/len(test_scenarios))*100:.1f}%")
    
    if detection_count > 0:
        avg_confidence = total_confidence / detection_count
        print(f"Average Confidence: {avg_confidence:.1%}")
        
        print(f"\nSeverity Distribution:")
        for severity, count in severity_counts.items():
            if count > 0:
                print(f"  {severity}: {count} ({(count/detection_count)*100:.1f}%)")
    
    print(f"\nAI Learning Status:")
    metrics = status['detection_engine']['learning_metrics']
    print(f"  Patterns Learned: {metrics['patterns_learned']}")
    print(f"  Accuracy Improvements: {len(metrics['accuracy_improvements'])}")
    print(f"  False Positive Reductions: {len(metrics['false_positive_reduction'])}")
    
    print(f"\nModel Performance:")
    for model_name, model_info in status['detection_engine']['models'].items():
        print(f"  {model_name}: {model_info['accuracy']:.1%} accuracy ({model_info['type']})")
    
    print(f"\nTesting Complete! AI agents are operational and learning.")

if __name__ == "__main__":
    asyncio.run(comprehensive_ai_test())