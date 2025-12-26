"""
Benign Activity Testing
Test AI agents with normal, non-threatening scenarios to check differentiation
"""
import sys
sys.path.append('agents')
import asyncio
from advanced_ai_agents import AdvancedAIAgentManager

async def test_benign_scenarios():
    print("=" * 70)
    print("BENIGN ACTIVITY TESTING")
    print("Testing AI agents with normal, non-threatening scenarios")
    print("=" * 70)
    
    manager = AdvancedAIAgentManager()
    await manager.initialize()
    
    # Test completely benign scenarios
    benign_scenarios = [
        {
            'name': 'Normal Web Browsing',
            'data': {
                'id': 'benign_web_001',
                'threat_type': 'malware',  # Test if it misclassifies
                'features': [0.05, 0.02, 0.01],
                'metadata': {
                    'network': {
                        'connection_count': 3,
                        'tcp_ratio': 0.8,
                        'common_ports_ratio': 0.98,
                        'geographic_diversity': 0.02,
                        'bandwidth_usage': 150
                    },
                    'behavioral': {
                        'activity_anomaly_score': 0.05,
                        'access_pattern_score': 0.1,
                        'time_anomaly_score': 0.02,
                        'privilege_usage_score': 0.1,
                        'data_access_volume': 50
                    }
                }
            }
        },
        {
            'name': 'Regular Email Check',
            'data': {
                'id': 'benign_email_001',
                'threat_type': 'phishing',
                'features': [0.02, 0.01, 0.03],
                'metadata': {
                    'content': {
                        'content_similarity': 0.1,
                        'language_anomaly_score': 0.05,
                        'metadata_consistency': 0.95,
                        'compression_ratio': 0.6
                    }
                }
            }
        },
        {
            'name': 'Legitimate DeFi Transaction',
            'data': {
                'id': 'benign_defi_001',
                'threat_type': 'defi_exploit',
                'features': [0.1, 0.05, 0.08],
                'metadata': {
                    'blockchain': {
                        'transaction_volume': 1000,
                        'gas_efficiency': 0.8,
                        'contract_call_frequency': 1,
                        'value_transfer_anomaly': 0.05,
                        'mev_detection_score': 0.02
                    }
                }
            }
        },
        {
            'name': 'Normal Employee Access',
            'data': {
                'id': 'benign_employee_001',
                'threat_type': 'insider_threat',
                'features': [0.03, 0.02, 0.01],
                'metadata': {
                    'behavioral': {
                        'activity_anomaly_score': 0.02,
                        'access_pattern_score': 0.05,
                        'time_anomaly_score': 0.01,
                        'privilege_usage_score': 0.03,
                        'data_access_volume': 20
                    }
                }
            }
        },
        {
            'name': 'Standard Smart Contract Call',
            'data': {
                'id': 'benign_contract_001',
                'threat_type': 'smart_contract_vulnerability',
                'features': [0.02, 0.01, 0.03],
                'metadata': {
                    'blockchain': {
                        'transaction_volume': 500,
                        'gas_efficiency': 0.9,
                        'contract_call_frequency': 1,
                        'value_transfer_anomaly': 0.01,
                        'mev_detection_score': 0.0
                    }
                }
            }
        },
        {
            'name': 'Normal Network Traffic',
            'data': {
                'id': 'benign_network_001',
                'threat_type': 'ddos',
                'features': [0.01, 0.02, 0.01],
                'metadata': {
                    'network': {
                        'connection_count': 2,
                        'tcp_ratio': 0.7,
                        'common_ports_ratio': 0.99,
                        'geographic_diversity': 0.01,
                        'bandwidth_usage': 80
                    },
                    'temporal': {
                        'event_frequency': 2,
                        'burst_score': 0.01,
                        'time_of_day_anomaly': 0.05
                    }
                }
            }
        }
    ]
    
    print(f"\nTESTING BENIGN SCENARIOS:")
    print("-" * 70)
    
    correct_classifications = 0
    false_positives = 0
    total_tests = len(benign_scenarios)
    
    for i, scenario in enumerate(benign_scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print("-" * 40)
        
        result = await manager.process_threat_data(scenario['data'])
        
        print(f"Threat Detected: {'YES' if result.threat_detected else 'NO'}")
        
        if result.threat_detected:
            false_positives += 1
            print(f"⚠️  FALSE POSITIVE - Classified As: {result.threat_type.value}")
            print(f"   Confidence: {result.confidence:.1%}")
            print(f"   Severity: {result.severity.name}")
            print(f"   Features Used: {', '.join(result.features_used)}")
        else:
            correct_classifications += 1
            print("✅ CORRECT - Identified as normal activity")
    
    # Test some edge cases - low but not zero threat indicators
    print(f"\n" + "=" * 70)
    print("EDGE CASE TESTING - Low but detectable threat indicators")
    print("=" * 70)
    
    edge_cases = [
        {
            'name': 'Slightly Elevated Network Activity',
            'data': {
                'id': 'edge_network_001',
                'threat_type': 'ddos',
                'features': [0.3, 0.2, 0.25],
                'metadata': {
                    'network': {
                        'connection_count': 50,
                        'tcp_ratio': 0.85,
                        'common_ports_ratio': 0.7,
                        'geographic_diversity': 0.3,
                        'bandwidth_usage': 5000
                    }
                }
            }
        },
        {
            'name': 'Suspicious but Legitimate Email',
            'data': {
                'id': 'edge_email_001',
                'threat_type': 'phishing',
                'features': [0.4, 0.3, 0.35],
                'metadata': {
                    'content': {
                        'content_similarity': 0.4,
                        'language_anomaly_score': 0.3,
                        'metadata_consistency': 0.7
                    }
                }
            }
        }
    ]
    
    edge_detections = 0
    for i, scenario in enumerate(edge_cases, 1):
        print(f"\n{i}. {scenario['name']}")
        print("-" * 40)
        
        result = await manager.process_threat_data(scenario['data'])
        
        print(f"Threat Detected: {'YES' if result.threat_detected else 'NO'}")
        
        if result.threat_detected:
            edge_detections += 1
            print(f"Classified As: {result.threat_type.value}")
            print(f"Confidence: {result.confidence:.1%}")
            print(f"Severity: {result.severity.name}")
        else:
            print("Identified as normal activity")
    
    # Summary
    print(f"\n" + "=" * 70)
    print("BENIGN TESTING SUMMARY")
    print("=" * 70)
    print(f"Total Benign Tests: {total_tests}")
    print(f"Correct Classifications (No Threat): {correct_classifications}")
    print(f"False Positives: {false_positives}")
    print(f"Accuracy on Benign Data: {(correct_classifications/total_tests)*100:.1f}%")
    print(f"False Positive Rate: {(false_positives/total_tests)*100:.1f}%")
    
    print(f"\nEdge Case Results:")
    print(f"Edge Cases Detected as Threats: {edge_detections}/{len(edge_cases)}")
    
    # Interpretation
    if false_positives == 0:
        print(f"\n✅ EXCELLENT: No false positives on clearly benign data!")
    elif false_positives <= 1:
        print(f"\n✅ GOOD: Very low false positive rate on benign data")
    elif false_positives <= 2:
        print(f"\n⚠️  MODERATE: Some false positives, may need threshold tuning")
    else:
        print(f"\n❌ HIGH: High false positive rate, aggressive detection settings")
    
    print(f"\nThis test helps determine if the AI agents can distinguish between")
    print(f"normal operations and actual threats.")

if __name__ == "__main__":
    asyncio.run(test_benign_scenarios())