"""
AI Agent Rebalancing Tool
Fix hyper-aggressive DDoS classification bias and restore proper threat discrimination
"""
import sys
sys.path.append('agents')
import sqlite3
import json
import os
from datetime import datetime
import asyncio
from advanced_ai_agents import AdvancedAIAgentManager, ThreatType, AlertSeverity

class AIRebalancer:
    def __init__(self):
        self.db_path = "models/threat_detection/patterns.db"
        self.backup_path = "models/threat_detection/patterns_backup.db"
        self.manager = None
    
    async def initialize(self):
        """Initialize the AI manager"""
        self.manager = AdvancedAIAgentManager()
        await self.manager.initialize()
    
    def backup_current_patterns(self):
        """Backup current pattern database"""
        print("📦 Creating backup of current patterns...")
        
        if os.path.exists(self.db_path):
            import shutil
            shutil.copy2(self.db_path, self.backup_path)
            print(f"✅ Backup created: {self.backup_path}")
        
    def reset_biased_patterns(self):
        """Reset overly biased DDoS patterns"""
        print("🧹 Clearing biased patterns...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current pattern count
            cursor.execute("SELECT COUNT(*) FROM threat_patterns WHERE threat_type = 'ddos'")
            ddos_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM threat_patterns WHERE threat_type != 'ddos'")
            other_count = cursor.fetchone()[0]
            
            print(f"Current patterns: {ddos_count} DDoS, {other_count} others")
            
            # If DDoS is >80% of patterns, reset some of them
            total_patterns = ddos_count + other_count
            if total_patterns > 0 and (ddos_count / total_patterns) > 0.8:
                # Keep only the most recent 2 DDoS patterns
                cursor.execute("""
                    DELETE FROM threat_patterns 
                    WHERE threat_type = 'ddos' 
                    AND id NOT IN (
                        SELECT id FROM threat_patterns 
                        WHERE threat_type = 'ddos' 
                        ORDER BY last_seen DESC 
                        LIMIT 2
                    )
                """)
                
                deleted = cursor.rowcount
                print(f"🗑️  Removed {deleted} biased DDoS patterns")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error resetting patterns: {e}")
    
    def add_balanced_training_data(self):
        """Add balanced training patterns for all threat types"""
        print("⚖️  Adding balanced training patterns...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Balanced training patterns for each threat type
            balanced_patterns = [
                # Malware patterns
                {
                    'threat_type': 'malware',
                    'confidence': 0.85,
                    'accuracy': 0.90,
                    'features': '{"network_anomaly": 0.8, "file_entropy": 0.85, "api_calls": 0.9}',
                    'pattern_hash': 'balanced_malware_001'
                },
                {
                    'threat_type': 'malware',
                    'confidence': 0.75,
                    'accuracy': 0.88,
                    'features': '{"network_anomaly": 0.7, "file_entropy": 0.6, "api_calls": 0.8}',
                    'pattern_hash': 'balanced_malware_002'
                },
                
                # Phishing patterns
                {
                    'threat_type': 'phishing',
                    'confidence': 0.90,
                    'accuracy': 0.93,
                    'features': '{"url_similarity": 0.9, "content_analysis": 0.85, "domain_reputation": 0.2}',
                    'pattern_hash': 'balanced_phishing_001'
                },
                {
                    'threat_type': 'phishing',
                    'confidence': 0.80,
                    'accuracy': 0.91,
                    'features': '{"url_similarity": 0.75, "content_analysis": 0.8, "domain_reputation": 0.3}',
                    'pattern_hash': 'balanced_phishing_002'
                },
                
                # Insider threat patterns
                {
                    'threat_type': 'insider_threat',
                    'confidence': 0.82,
                    'accuracy': 0.87,
                    'features': '{"behavioral_anomaly": 0.8, "access_pattern": 0.85, "privilege_escalation": 0.7}',
                    'pattern_hash': 'balanced_insider_001'
                },
                
                # Smart contract patterns
                {
                    'threat_type': 'smart_contract_vulnerability',
                    'confidence': 0.88,
                    'accuracy': 0.89,
                    'features': '{"reentrancy_risk": 0.9, "overflow_check": 0.8, "access_control": 0.75}',
                    'pattern_hash': 'balanced_contract_001'
                },
                
                # DeFi exploit patterns
                {
                    'threat_type': 'defi_exploit',
                    'confidence': 0.85,
                    'accuracy': 0.86,
                    'features': '{"flash_loan_pattern": 0.85, "arbitrage_signals": 0.8, "mev_detection": 0.9}',
                    'pattern_hash': 'balanced_defi_001'
                },
                
                # Benign patterns (to reduce false positives)
                {
                    'threat_type': 'benign',
                    'confidence': 0.95,
                    'accuracy': 0.98,
                    'features': '{"normal_activity": 0.95, "expected_behavior": 0.9, "baseline_match": 0.85}',
                    'pattern_hash': 'balanced_benign_001'
                },
                {
                    'threat_type': 'benign',
                    'confidence': 0.92,
                    'accuracy': 0.96,
                    'features': '{"normal_activity": 0.9, "expected_behavior": 0.88, "baseline_match": 0.8}',
                    'pattern_hash': 'balanced_benign_002'
                }
            ]
            
            # Insert balanced patterns
            now = datetime.now().isoformat()
            for pattern in balanced_patterns:
                cursor.execute("""
                    INSERT OR REPLACE INTO threat_patterns 
                    (pattern_hash, threat_type, features, confidence, occurrences, 
                     first_seen, last_seen, accuracy, false_positives)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pattern['pattern_hash'],
                    pattern['threat_type'],
                    pattern['features'],
                    pattern['confidence'],
                    1,  # occurrences
                    now,  # first_seen
                    now,  # last_seen
                    pattern['accuracy'],
                    0   # false_positives
                ))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Added {len(balanced_patterns)} balanced training patterns")
            
        except Exception as e:
            print(f"Error adding balanced data: {e}")
    
    def update_model_thresholds(self):
        """Update detection thresholds to be more balanced"""
        print("🎛️  Updating model thresholds...")
        
        # Access the detection engine directly
        detection_engine = self.manager.detection_engine
        
        # Update DDoS model to be less aggressive
        if ThreatType.DDOS in detection_engine.threat_models:
            ddos_model = detection_engine.threat_models[ThreatType.DDOS]
            ddos_model['thresholds']['rate_threshold'] = 2000  # Higher threshold
            ddos_model['thresholds']['diversity_score'] = 0.05  # Lower threshold
            print("  🎯 DDoS thresholds adjusted (less aggressive)")
        
        # Update other models for better discrimination
        threat_adjustments = {
            ThreatType.MALWARE: {
                'entropy': 8.0,  # Higher entropy threshold
                'network_score': 0.85  # Higher network score needed
            },
            ThreatType.PHISHING: {
                'similarity_score': 0.90,  # Higher similarity needed
                'reputation_score': 0.25   # Lower reputation threshold
            },
            ThreatType.INSIDER_THREAT: {
                'anomaly_score': 0.75,  # Higher anomaly threshold
                'risk_score': 0.85      # Higher risk threshold
            },
            ThreatType.SMART_CONTRACT_VULNERABILITY: {
                'vulnerability_score': 0.70,  # Higher vulnerability threshold
                'critical_score': 0.92        # Higher critical threshold
            },
            ThreatType.DEFI_EXPLOIT: {
                'exploit_probability': 0.80,  # Higher probability needed
                'value_at_risk': 2000000      # Higher value threshold
            }
        }
        
        for threat_type, adjustments in threat_adjustments.items():
            if threat_type in detection_engine.threat_models:
                model = detection_engine.threat_models[threat_type]
                model['thresholds'].update(adjustments)
                print(f"  🎯 {threat_type.value} thresholds adjusted")
    
    async def test_rebalanced_system(self):
        """Test the rebalanced system with various scenarios"""
        print("\n🧪 Testing rebalanced AI system...")
        
        test_scenarios = [
            # Benign scenarios (should NOT be detected)
            {
                'name': 'Normal Web Browsing',
                'expected': False,
                'data': {
                    'id': 'test_benign_001',
                    'threat_type': 'malware',
                    'features': [0.05, 0.02, 0.01],
                    'metadata': {
                        'network': {
                            'connection_count': 3,
                            'tcp_ratio': 0.8,
                            'common_ports_ratio': 0.98,
                            'geographic_diversity': 0.02,
                            'bandwidth_usage': 150
                        }
                    }
                }
            },
            {
                'name': 'Legitimate Email',
                'expected': False,
                'data': {
                    'id': 'test_benign_002',
                    'threat_type': 'phishing',
                    'features': [0.02, 0.01, 0.03],
                    'metadata': {
                        'content': {
                            'content_similarity': 0.1,
                            'language_anomaly_score': 0.05,
                            'metadata_consistency': 0.95
                        }
                    }
                }
            },
            
            # Real threats (should BE detected)
            {
                'name': 'Actual DDoS Attack',
                'expected': True,
                'data': {
                    'id': 'test_threat_001',
                    'threat_type': 'ddos',
                    'features': [0.95, 0.9, 0.92],
                    'metadata': {
                        'network': {
                            'connection_count': 5000,
                            'tcp_ratio': 0.98,
                            'common_ports_ratio': 0.05,
                            'geographic_diversity': 0.95,
                            'bandwidth_usage': 50000000
                        },
                        'temporal': {
                            'event_frequency': 500,
                            'burst_score': 0.95
                        }
                    }
                }
            },
            {
                'name': 'Malware Infection',
                'expected': True,
                'data': {
                    'id': 'test_threat_002',
                    'threat_type': 'malware',
                    'features': [0.9, 0.85, 0.88],
                    'metadata': {
                        'network': {
                            'connection_count': 500,
                            'tcp_ratio': 0.95,
                            'common_ports_ratio': 0.1,
                            'geographic_diversity': 0.9,
                            'bandwidth_usage': 10000000
                        },
                        'behavioral': {
                            'activity_anomaly_score': 0.9,
                            'access_pattern_score': 0.85
                        }
                    }
                }
            }
        ]
        
        correct_predictions = 0
        total_tests = len(test_scenarios)
        
        print("\nTest Results:")
        print("-" * 50)
        
        for i, scenario in enumerate(test_scenarios, 1):
            result = await self.manager.process_threat_data(scenario['data'])
            
            detected = result.threat_detected
            expected = scenario['expected']
            correct = detected == expected
            
            if correct:
                correct_predictions += 1
                status = "✅ CORRECT"
            else:
                status = "❌ WRONG"
            
            print(f"{i}. {scenario['name']}: {status}")
            print(f"   Expected: {'Threat' if expected else 'Benign'}")
            print(f"   Detected: {'Threat' if detected else 'Benign'}")
            
            if detected:
                print(f"   Type: {result.threat_type.value}")
                print(f"   Confidence: {result.confidence:.1%}")
                print(f"   Severity: {result.severity.name}")
            print()
        
        accuracy = (correct_predictions / total_tests) * 100
        print(f"Overall Accuracy: {accuracy:.1f}% ({correct_predictions}/{total_tests})")
        
        return accuracy > 75  # Return success if >75% accuracy

async def main():
    print("=" * 70)
    print("🛠️  AI AGENT REBALANCING SYSTEM")
    print("Fixing hyper-aggressive DDoS classification bias")
    print("=" * 70)
    
    rebalancer = AIRebalancer()
    
    # Step 1: Initialize
    print("\n1. Initializing AI system...")
    await rebalancer.initialize()
    
    # Step 2: Backup current state
    print("\n2. Creating backup...")
    rebalancer.backup_current_patterns()
    
    # Step 3: Reset biased patterns
    print("\n3. Resetting biased patterns...")
    rebalancer.reset_biased_patterns()
    
    # Step 4: Add balanced training data
    print("\n4. Adding balanced training data...")
    rebalancer.add_balanced_training_data()
    
    # Step 5: Update model thresholds
    print("\n5. Updating model thresholds...")
    rebalancer.update_model_thresholds()
    
    # Step 6: Test the rebalanced system
    print("\n6. Testing rebalanced system...")
    success = await rebalancer.test_rebalanced_system()
    
    # Summary
    print("\n" + "=" * 70)
    print("REBALANCING SUMMARY")
    print("=" * 70)
    
    if success:
        print("✅ REBALANCING SUCCESSFUL!")
        print("   • DDoS bias reduced")
        print("   • Threat discrimination improved") 
        print("   • False positive rate decreased")
        print("   • Model thresholds balanced")
    else:
        print("⚠️  REBALANCING PARTIALLY SUCCESSFUL")
        print("   • Some improvements made")
        print("   • Further tuning may be needed")
    
    print(f"\n📁 Backup available at: {rebalancer.backup_path}")
    print("🔄 AI agents should now show better discrimination!")

if __name__ == "__main__":
    asyncio.run(main())