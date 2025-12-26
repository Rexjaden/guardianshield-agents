"""
Launch Continuous Training System
Simple interface to start and manage continuous agent training
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from continuous_training_system import (
    continuous_trainer, 
    start_continuous_training,
    simulate_threat_detection,
    report_false_positive,
    LearningEvent
)

async def demo_continuous_training():
    """Demo the continuous training system with sample data"""
    print("🚀 GuardianShield Continuous Training Demo")
    print("=" * 50)
    
    # Start training in background
    training_task = asyncio.create_task(start_continuous_training())
    
    # Wait a moment for initialization
    await asyncio.sleep(2)
    
    print("🎯 Simulating threat detections...")
    
    # Simulate specialized threat scenarios for different agent types
    threat_scenarios = [
        # Behavioral Analysis scenarios
        {
            'agent_id': 'behavioral_agent',
            'threat_data': {
                'type': 'unusual_login_pattern',
                'severity': 6,
                'user_id': 'user_123',
                'login_time': '03:00 AM',
                'location': 'unusual_country',
                'confidence': 0.87
            },
            'verified': True,
            'category': 'behavioral'
        },
        {
            'agent_id': 'behavioral_agent',
            'threat_data': {
                'type': 'bulk_data_access',
                'severity': 7,
                'user_id': 'user_456',
                'files_accessed': 1500,
                'time_span': '5_minutes',
                'confidence': 0.91
            },
            'verified': True,
            'category': 'behavioral'
        },
        # External Threat scenarios
        {
            'agent_id': 'external_agent',
            'threat_data': {
                'type': 'malware',
                'severity': 9,
                'hash': 'abc123def456',
                'file_type': 'executable',
                'source': 'network_scanner',
                'confidence': 0.95
            },
            'verified': True,
            'category': 'external'
        },
        {
            'agent_id': 'external_agent',
            'threat_data': {
                'type': 'phishing',
                'severity': 8,
                'url': 'fake-bank-login.com',
                'similarity_score': 0.94,
                'target_brand': 'major_bank',
                'confidence': 0.89
            },
            'verified': True,
            'category': 'external'
        },
        # Cross-training scenario (should go to learning agent)
        {
            'agent_id': 'learning_agent',
            'threat_data': {
                'type': 'adaptive_attack',
                'severity': 8,
                'evolution_pattern': 'multi_stage',
                'techniques': ['social_engineering', 'technical_exploit'],
                'confidence': 0.83
            },
            'verified': True,
            'category': 'adaptive'
        },
        # False positive for retraining
        {
            'agent_id': 'behavioral_agent',
            'threat_data': {
                'type': 'normal_admin_activity',
                'severity': 5,
                'user_id': 'admin_user',
                'elevated_permissions': True,
                'confidence': 0.70
            },
            'verified': False,  # False positive
            'category': 'behavioral'
        }
    ]
    
    for i, scenario in enumerate(threat_scenarios):
        category = scenario.get('category', 'general')
        agent_type = scenario['agent_id'].replace('_agent', '').title()
        
        print(f"   📡 {agent_type} Threat {i+1}: {scenario['threat_data']['type']} (severity: {scenario['threat_data']['severity']})")
        print(f"       🎯 Category: {category} | Agent: {scenario['agent_id']}")
        
        simulate_threat_detection(
            scenario['agent_id'],
            scenario['threat_data'],
            scenario['verified']
        )
        
        # If false positive, report it for immediate learning
        if not scenario['verified']:
            report_false_positive(
                scenario['agent_id'],
                scenario['threat_data'],
                f"False positive: {scenario['threat_data']['type']} was normal {category} activity"
            )
            print(f"       ⚠️  Reported as false positive for specialized retraining")
        else:
            print(f"       ✅ Verified threat - training {agent_type} agent on {category} patterns")
        
        await asyncio.sleep(1.5)
    
    # Let training run for a bit
    print(f"\n🧠 Training agents for 10 seconds...")
    await asyncio.sleep(10)
    
    # Show training status
    status = continuous_trainer.get_training_status()
    print(f"\n📊 Training Status:")
    print(f"   Active Agents: {status['active_agents']}")
    print(f"   Queue Size: {status['training_queue_size']}")
    print(f"   Total Events: {status['learning_events_total']}")
    print(f"   Average Accuracy: {status['global_performance']['average_accuracy']:.3f}")
    
    print(f"\n🤖 Agent Performance:")
    for agent_id, metrics in status['agent_metrics'].items():
        print(f"   {agent_id}:")
        print(f"     Training Sessions: {metrics['training_sessions']}")
        print(f"     Recent Accuracy: {metrics['recent_accuracy']:.3f}")
        print(f"     Last Training: {metrics['last_training'] or 'Never'}")
    
    # Stop the training system
    continuous_trainer.stop_training()
    training_task.cancel()
    
    print(f"\n✅ Continuous training demo completed!")

def run_interactive_training():
    """Interactive training system management"""
    print("🛡️ GuardianShield Continuous Training Manager")
    print("=" * 50)
    
    while True:
        print("\n📋 Options:")
        print("1. Start continuous training")
        print("2. Simulate threat detection")
        print("3. Report false positive")
        print("4. View training status")
        print("5. Run training demo")
        print("6. Exit")
        
        try:
            choice = input("\n👉 Enter choice (1-6): ").strip()
            
            if choice == '1':
                print("🚀 Starting continuous training system...")
                asyncio.run(start_continuous_training())
                
            elif choice == '2':
                agent_id = input("Agent ID (learning_agent/behavioral_agent/external_agent): ").strip()
                threat_type = input("Threat type (malware/phishing/ddos/etc): ").strip()
                severity = int(input("Severity (1-10): "))
                
                simulate_threat_detection(agent_id, {
                    'type': threat_type,
                    'severity': severity,
                    'timestamp': datetime.now().isoformat(),
                    'confidence': 0.8
                }, True)
                print("✅ Threat detection simulated")
                
            elif choice == '3':
                agent_id = input("Agent ID: ").strip()
                threat_type = input("Original threat type: ").strip()
                feedback = input("Feedback/correction: ").strip()
                
                report_false_positive(agent_id, {
                    'type': threat_type,
                    'timestamp': datetime.now().isoformat()
                }, feedback)
                print("✅ False positive reported")
                
            elif choice == '4':
                status = continuous_trainer.get_training_status()
                print(f"\n📊 Training Status:")
                print(f"Active Agents: {status['active_agents']}")
                print(f"Queue Size: {status['training_queue_size']}")
                print(f"Learning Events: {status['learning_events_total']}")
                print(f"Global Performance: {status['global_performance']}")
                
            elif choice == '5':
                print("🎯 Running training demo...")
                asyncio.run(demo_continuous_training())
                
            elif choice == '6':
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1-6.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🛡️ GuardianShield Continuous Training System")
    print("=" * 50)
    
    # Check if we should run demo or interactive mode
    if len(sys.argv) > 1 and sys.argv[1] == '--demo':
        asyncio.run(demo_continuous_training())
    else:
        run_interactive_training()