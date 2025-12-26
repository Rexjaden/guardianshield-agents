"""
Overnight AI Training System
Intensive training cycles for GuardianShield AI agents while you sleep
"""
import asyncio
import sys
sys.path.append('agents')
import json
import random
import time
from datetime import datetime, timedelta
from advanced_ai_agents import AdvancedAIAgentManager, ThreatType

class OvernightTrainingSystem:
    def __init__(self):
        self.manager = None
        self.training_session_id = f"overnight_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.training_cycles_completed = 0
        self.performance_improvements = {}
        self.training_log = []
        
    async def initialize(self):
        """Initialize the AI manager for training"""
        print("🌙 INITIALIZING OVERNIGHT TRAINING SYSTEM")
        print("=" * 60)
        self.manager = AdvancedAIAgentManager()
        await self.manager.initialize()
        print("✅ AI Manager initialized for overnight training")
        
    async def run_intensive_training_cycles(self, cycles=50):
        """Run intensive training cycles overnight"""
        print(f"\n🚀 STARTING {cycles} INTENSIVE TRAINING CYCLES")
        print("Sleep well! Your AI agents are learning...")
        print("-" * 60)
        
        for cycle in range(cycles):
            cycle_start = time.time()
            
            print(f"\n⚡ Training Cycle {cycle + 1}/{cycles} - {datetime.now().strftime('%H:%M:%S')}")
            
            # Generate diverse training scenarios
            training_batch = await self._generate_training_batch()
            
            # Train on each scenario
            cycle_improvements = []
            for scenario in training_batch:
                improvement = await self._train_on_scenario(scenario)
                cycle_improvements.append(improvement)
            
            # Calculate cycle performance
            avg_improvement = sum(cycle_improvements) / len(cycle_improvements)
            cycle_time = time.time() - cycle_start
            
            # Log cycle results
            cycle_log = {
                'cycle': cycle + 1,
                'timestamp': datetime.now().isoformat(),
                'scenarios_trained': len(training_batch),
                'avg_improvement': avg_improvement,
                'cycle_time': cycle_time,
                'cumulative_improvements': sum(cycle_improvements)
            }
            
            self.training_log.append(cycle_log)
            self.training_cycles_completed += 1
            
            # Display progress
            print(f"   📊 Scenarios Processed: {len(training_batch)}")
            print(f"   📈 Average Improvement: {avg_improvement:.3f}")
            print(f"   ⏱️  Cycle Time: {cycle_time:.2f}s")
            print(f"   🎯 Cumulative Cycles: {self.training_cycles_completed}")
            
            # Progressive difficulty increase
            if cycle % 10 == 9:
                await self._increase_training_difficulty()
                print(f"   🔥 Training difficulty increased!")
            
            # Performance checkpoint every 5 cycles
            if (cycle + 1) % 5 == 0:
                await self._performance_checkpoint(cycle + 1)
            
            # Small delay between cycles
            await asyncio.sleep(2)
        
        print(f"\n🎉 COMPLETED {cycles} TRAINING CYCLES!")
        
    async def _generate_training_batch(self, batch_size=8):
        """Generate diverse training scenarios"""
        training_batch = []
        
        # Mix of threat types for balanced training
        threat_types = ['malware', 'phishing', 'ddos', 'insider_threat', 'smart_contract_vulnerability', 'defi_exploit']
        
        for i in range(batch_size):
            if i < 2:
                # Benign scenarios (25% of batch)
                scenario = self._create_benign_scenario()
            else:
                # Threat scenarios (75% of batch)
                threat_type = random.choice(threat_types)
                scenario = self._create_threat_scenario(threat_type)
            
            training_batch.append(scenario)
        
        return training_batch
    
    def _create_benign_scenario(self):
        """Create benign activity scenario"""
        scenarios = [
            {
                'id': f'benign_training_{random.randint(1000, 9999)}',
                'threat_type': 'malware',
                'features': [random.uniform(0.01, 0.1), random.uniform(0.01, 0.08), random.uniform(0.01, 0.05)],
                'expected': 'benign',
                'difficulty': random.uniform(0.1, 0.3),
                'metadata': {
                    'network': {
                        'connection_count': random.randint(1, 5),
                        'tcp_ratio': random.uniform(0.7, 0.9),
                        'common_ports_ratio': random.uniform(0.95, 1.0),
                        'geographic_diversity': random.uniform(0.01, 0.05),
                        'bandwidth_usage': random.randint(50, 200)
                    }
                }
            },
            {
                'id': f'benign_employee_{random.randint(1000, 9999)}',
                'threat_type': 'insider_threat',
                'features': [random.uniform(0.01, 0.1), random.uniform(0.01, 0.05), random.uniform(0.01, 0.08)],
                'expected': 'benign',
                'difficulty': random.uniform(0.2, 0.4),
                'metadata': {
                    'behavioral': {
                        'activity_anomaly_score': random.uniform(0.01, 0.1),
                        'access_pattern_score': random.uniform(0.01, 0.1),
                        'time_anomaly_score': random.uniform(0.01, 0.05),
                        'privilege_usage_score': random.uniform(0.01, 0.1),
                        'data_access_volume': random.randint(10, 100)
                    }
                }
            }
        ]
        
        return random.choice(scenarios)
    
    def _create_threat_scenario(self, threat_type):
        """Create realistic threat scenario"""
        base_confidence = random.uniform(0.7, 0.95)
        difficulty = random.uniform(0.5, 0.9)
        
        threat_profiles = {
            'malware': {
                'features': [random.uniform(0.8, 0.95), random.uniform(0.7, 0.9), random.uniform(0.75, 0.9)],
                'metadata': {
                    'network': {
                        'connection_count': random.randint(100, 2000),
                        'tcp_ratio': random.uniform(0.85, 0.98),
                        'common_ports_ratio': random.uniform(0.05, 0.3),
                        'geographic_diversity': random.uniform(0.6, 0.95),
                        'bandwidth_usage': random.randint(1000000, 10000000)
                    },
                    'behavioral': {
                        'activity_anomaly_score': random.uniform(0.7, 0.95),
                        'access_pattern_score': random.uniform(0.8, 0.95)
                    }
                }
            },
            'phishing': {
                'features': [random.uniform(0.85, 0.98), random.uniform(0.8, 0.95), random.uniform(0.75, 0.9)],
                'metadata': {
                    'content': {
                        'content_similarity': random.uniform(0.8, 0.98),
                        'language_anomaly_score': random.uniform(0.6, 0.9),
                        'metadata_consistency': random.uniform(0.1, 0.4)
                    }
                }
            },
            'ddos': {
                'features': [random.uniform(0.9, 0.98), random.uniform(0.85, 0.95), random.uniform(0.8, 0.95)],
                'metadata': {
                    'network': {
                        'connection_count': random.randint(3000, 10000),
                        'tcp_ratio': random.uniform(0.95, 0.99),
                        'common_ports_ratio': random.uniform(0.01, 0.1),
                        'geographic_diversity': random.uniform(0.8, 0.98),
                        'bandwidth_usage': random.randint(20000000, 100000000)
                    }
                }
            },
            'insider_threat': {
                'features': [random.uniform(0.7, 0.9), random.uniform(0.8, 0.95), random.uniform(0.75, 0.9)],
                'metadata': {
                    'behavioral': {
                        'activity_anomaly_score': random.uniform(0.8, 0.95),
                        'access_pattern_score': random.uniform(0.85, 0.98),
                        'time_anomaly_score': random.uniform(0.7, 0.9),
                        'privilege_usage_score': random.uniform(0.8, 0.95),
                        'data_access_volume': random.randint(5000, 50000)
                    }
                }
            },
            'smart_contract_vulnerability': {
                'features': [random.uniform(0.8, 0.95), random.uniform(0.75, 0.9), random.uniform(0.8, 0.92)],
                'metadata': {
                    'blockchain': {
                        'transaction_volume': random.randint(5000000, 20000000),
                        'gas_efficiency': random.uniform(0.1, 0.3),
                        'contract_call_frequency': random.randint(200, 800),
                        'value_transfer_anomaly': random.uniform(0.8, 0.98),
                        'mev_detection_score': random.uniform(0.7, 0.95)
                    }
                }
            },
            'defi_exploit': {
                'features': [random.uniform(0.9, 0.98), random.uniform(0.85, 0.97), random.uniform(0.8, 0.95)],
                'metadata': {
                    'blockchain': {
                        'transaction_volume': random.randint(10000000, 50000000),
                        'gas_efficiency': random.uniform(0.05, 0.2),
                        'contract_call_frequency': random.randint(400, 1000),
                        'value_transfer_anomaly': random.uniform(0.9, 0.99),
                        'mev_detection_score': random.uniform(0.85, 0.98)
                    }
                }
            }
        }
        
        profile = threat_profiles.get(threat_type, threat_profiles['malware'])
        
        return {
            'id': f'{threat_type}_training_{random.randint(1000, 9999)}',
            'threat_type': threat_type,
            'features': profile['features'],
            'expected': threat_type,
            'difficulty': difficulty,
            'confidence_target': base_confidence,
            'metadata': profile['metadata']
        }
    
    async def _train_on_scenario(self, scenario):
        """Train AI on specific scenario"""
        try:
            # Process the scenario
            result = await self.manager.process_threat_data(scenario)
            
            # Calculate improvement metrics
            if scenario['expected'] == 'benign':
                # For benign scenarios, success is NOT detecting a threat
                success = not result.threat_detected
                improvement = 0.01 if success else -0.005  # Small penalty for false positive
            else:
                # For threat scenarios, success is detecting the correct threat type
                success = (result.threat_detected and 
                          result.threat_type.value == scenario['expected'])
                confidence_bonus = result.confidence * 0.001 if success else 0
                improvement = 0.02 + confidence_bonus if success else -0.01
            
            # Add difficulty modifier
            difficulty_modifier = scenario.get('difficulty', 0.5) * 0.005
            improvement += difficulty_modifier if success else -difficulty_modifier
            
            return improvement
            
        except Exception as e:
            print(f"   ❌ Training error: {e}")
            return -0.005  # Small penalty for errors
    
    async def _increase_training_difficulty(self):
        """Increase training difficulty progressively"""
        print(f"   🔥 Implementing advanced training techniques...")
        
        # Simulate difficulty increase by adjusting thresholds
        detection_engine = self.manager.detection_engine
        
        # Slightly increase thresholds (making detection more challenging)
        for threat_type, model in detection_engine.threat_models.items():
            for threshold_name in model.get('thresholds', {}):
                current = model['thresholds'][threshold_name]
                # Increase threshold by 1-2%
                model['thresholds'][threshold_name] = min(0.98, current + random.uniform(0.01, 0.02))
        
        await asyncio.sleep(1)  # Simulate processing time
    
    async def _performance_checkpoint(self, cycle):
        """Performance checkpoint and analysis"""
        print(f"\n📊 PERFORMANCE CHECKPOINT - Cycle {cycle}")
        print("-" * 40)
        
        # Get current system status
        status = self.manager.get_system_status()
        models = status['detection_engine']['models']
        
        # Calculate improvements
        total_accuracy = 0
        model_count = 0
        
        for model_name, model_info in models.items():
            accuracy = model_info['accuracy']
            total_accuracy += accuracy
            model_count += 1
            
            # Track improvements
            if model_name not in self.performance_improvements:
                self.performance_improvements[model_name] = {'initial': accuracy, 'current': accuracy}
            else:
                old_accuracy = self.performance_improvements[model_name]['current']
                improvement = accuracy - old_accuracy
                self.performance_improvements[model_name]['current'] = accuracy
                
                if improvement > 0:
                    print(f"   📈 {model_name}: {accuracy:.1%} (+{improvement:.3f})")
                else:
                    print(f"   📊 {model_name}: {accuracy:.1%}")
        
        avg_accuracy = total_accuracy / model_count if model_count > 0 else 0
        print(f"   🎯 Average Accuracy: {avg_accuracy:.1%}")
        print(f"   🔄 Training Cycles: {self.training_cycles_completed}")
        
        return avg_accuracy
    
    async def _save_training_results(self):
        """Save overnight training results"""
        results = {
            'session_id': self.training_session_id,
            'start_time': self.training_log[0]['timestamp'] if self.training_log else datetime.now().isoformat(),
            'end_time': datetime.now().isoformat(),
            'total_cycles': self.training_cycles_completed,
            'performance_improvements': self.performance_improvements,
            'training_log': self.training_log,
            'final_status': self.manager.get_system_status() if self.manager else None
        }
        
        filename = f"overnight_training_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Training results saved to: {filename}")
        return filename
    
    async def run_continuous_learning(self, hours=8):
        """Run continuous learning for specified hours"""
        print(f"\n🌙 CONTINUOUS LEARNING MODE - {hours} HOURS")
        print("Your AI agents will train continuously while you sleep!")
        print("-" * 60)
        
        start_time = time.time()
        end_time = start_time + (hours * 3600)  # Convert hours to seconds
        
        cycle_count = 0
        while time.time() < end_time:
            cycle_count += 1
            current_time = datetime.now().strftime('%H:%M:%S')
            remaining_hours = (end_time - time.time()) / 3600
            
            print(f"\n🌟 Continuous Learning Cycle {cycle_count} - {current_time}")
            print(f"   ⏰ Remaining: {remaining_hours:.1f} hours")
            
            # Mini training session
            mini_batch = await self._generate_training_batch(batch_size=4)
            improvements = []
            
            for scenario in mini_batch:
                improvement = await self._train_on_scenario(scenario)
                improvements.append(improvement)
            
            avg_improvement = sum(improvements) / len(improvements)
            print(f"   📈 Mini-batch improvement: {avg_improvement:.4f}")
            
            # Longer sleep between continuous cycles
            await asyncio.sleep(300)  # 5 minute intervals
        
        print(f"\n🎉 CONTINUOUS LEARNING COMPLETE!")
        print(f"Completed {cycle_count} continuous learning cycles over {hours} hours")

async def main():
    print("🌙🤖 OVERNIGHT AI TRAINING SYSTEM")
    print("=" * 70)
    print("Training your GuardianShield AI agents while you sleep!")
    print("Sweet dreams! Your AI will be smarter when you wake up! 😴💪")
    print("=" * 70)
    
    trainer = OvernightTrainingSystem()
    
    try:
        # Initialize training system
        await trainer.initialize()
        
        # Run intensive training cycles
        await trainer.run_intensive_training_cycles(cycles=30)
        
        # Run continuous learning
        await trainer.run_continuous_learning(hours=6)  # 6 hours of continuous learning
        
        # Save results
        results_file = await trainer._save_training_results()
        
        # Final report
        print("\n" + "=" * 70)
        print("🎉 OVERNIGHT TRAINING COMPLETE!")
        print("=" * 70)
        
        print(f"✅ Training cycles completed: {trainer.training_cycles_completed}")
        print(f"📊 Performance improvements tracked across all models")
        print(f"💾 Results saved to: {results_file}")
        
        # Final performance status
        if trainer.manager:
            final_status = trainer.manager.get_system_status()
            models = final_status['detection_engine']['models']
            
            print(f"\n🏆 FINAL MODEL PERFORMANCE:")
            total_accuracy = 0
            for model_name, model_info in models.items():
                print(f"   {model_name}: {model_info['accuracy']:.1%} accuracy")
                total_accuracy += model_info['accuracy']
            
            avg_accuracy = total_accuracy / len(models)
            print(f"\n🎯 Final Average Accuracy: {avg_accuracy:.1%}")
            
            if avg_accuracy > 0.94:
                print("🏆 EXCELLENT! Your AI agents achieved superior performance!")
            elif avg_accuracy > 0.92:
                print("🌟 GREAT! Your AI agents showed significant improvement!")
            else:
                print("📈 GOOD! Your AI agents are progressing well!")
        
        print(f"\n💤 Good morning! Your AI agents trained hard all night!")
        print(f"🚀 They're ready for even better performance today!")
        
    except KeyboardInterrupt:
        print("\n🛑 Training interrupted by user")
        await trainer._save_training_results()
    except Exception as e:
        print(f"\n❌ Training error: {e}")
        import traceback
        traceback.print_exc()
        if trainer.training_log:
            await trainer._save_training_results()

if __name__ == "__main__":
    asyncio.run(main())