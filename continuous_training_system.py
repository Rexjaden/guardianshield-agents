"""
Continuous Agent Training System
Real-time learning and adaptation for GuardianShield AI agents
"""

import asyncio
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass
from collections import deque
import numpy as np

# Import existing agents
from agents.learning_agent import LearningAgent
from agents.behavioral_analytics import BehavioralAnalyticsAgent
from agents.external_agent import ExternalAgent

@dataclass
class TrainingMetrics:
    agent_id: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    training_time: float
    data_points: int
    timestamp: datetime

@dataclass
class LearningEvent:
    event_type: str  # 'threat_detected', 'false_positive', 'new_pattern', 'performance_update'
    agent_id: str
    data: Dict[str, Any]
    feedback: Optional[str] = None
    confidence: float = 0.0
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class ContinuousTrainingSystem:
    """
    Continuous learning system that trains agents in real-time based on:
    - Live threat detection feedback
    - Performance metrics
    - New attack patterns
    - Cross-agent knowledge sharing
    """
    
    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self.training_queue = deque(maxlen=10000)
        self.performance_history = {}
        self.learning_events = deque(maxlen=50000)
        self.training_active = True
        
        # Training parameters
        self.batch_size = 100
        self.training_interval = 30  # seconds
        self.performance_window = 1000  # events to consider for performance
        
        # Learning thresholds
        self.accuracy_threshold = 0.85
        self.confidence_threshold = 0.7
        self.improvement_threshold = 0.02
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.training_metrics = {}
        self.global_performance = {
            'total_threats_detected': 0,
            'total_false_positives': 0,
            'total_true_positives': 0,
            'average_accuracy': 0.0,
            'learning_velocity': 0.0
        }
        
    def register_agent(self, agent_id: str, agent: Any):
        """Register an agent for continuous training"""
        self.agents[agent_id] = agent
        self.performance_history[agent_id] = deque(maxlen=1000)
        self.training_metrics[agent_id] = {
            'training_sessions': 0,
            'last_training': None,
            'accuracy_trend': deque(maxlen=100),
            'learning_rate_adjustments': 0,
            'specialization': getattr(agent, 'training_specialization', 'general'),
            'expertise_areas': self._identify_expertise_areas(agent)
        }
        
        # Initialize specialized training queues
        specialization = getattr(agent, 'training_specialization', 'general')
        self.logger.info(f"🤖 Registered {specialization} agent {agent_id} for continuous training")
        
    def _identify_expertise_areas(self, agent: Any) -> List[str]:
        """Identify agent's areas of expertise based on its attributes and methods"""
        expertise = []
        
        # Check agent class name and attributes
        class_name = agent.__class__.__name__.lower()
        
        if 'behavioral' in class_name or hasattr(agent, 'behavior_log'):
            expertise.extend(['user_behavior', 'access_patterns', 'behavioral_anomalies'])
        
        if 'external' in class_name or hasattr(agent, 'network_signatures'):
            expertise.extend(['network_threats', 'malware', 'phishing', 'external_attacks'])
        
        if 'learning' in class_name or hasattr(agent, 'learn_from_experience'):
            expertise.extend(['pattern_recognition', 'adaptive_learning', 'threat_classification'])
        
        if hasattr(agent, 'blockchain_monitor'):
            expertise.extend(['smart_contract_security', 'defi_attacks', 'blockchain_analysis'])
        
        if hasattr(agent, 'file_analysis'):
            expertise.extend(['malware_analysis', 'file_inspection', 'static_analysis'])
            
        return expertise if expertise else ['general_security']
        
    def add_learning_event(self, event: LearningEvent):
        """Add a learning event to the training queue"""
        self.learning_events.append(event)
        self.training_queue.append(event)
        
        # Update global performance metrics
        if event.event_type == 'threat_detected':
            self.global_performance['total_threats_detected'] += 1
            if event.data.get('verified', False):
                self.global_performance['total_true_positives'] += 1
            else:
                self.global_performance['total_false_positives'] += 1
                
        # Trigger immediate training if critical event
        if event.event_type in ['false_positive', 'missed_threat']:
            asyncio.create_task(self.train_agent_immediate(event.agent_id, event))
            
    async def continuous_training_loop(self):
        """Main continuous training loop"""
        self.logger.info("🚀 Starting continuous training system...")
        
        while self.training_active:
            try:
                # Process training queue
                if len(self.training_queue) >= self.batch_size:
                    await self.process_training_batch()
                
                # Update performance metrics
                await self.update_performance_metrics()
                
                # Adaptive learning rate adjustment
                await self.adjust_learning_rates()
                
                # Cross-agent knowledge sharing
                await self.share_knowledge_between_agents()
                
                # Performance-based agent improvement
                await self.improve_underperforming_agents()
                
                await asyncio.sleep(self.training_interval)
                
            except Exception as e:
                self.logger.error(f"❌ Error in continuous training loop: {e}")
                await asyncio.sleep(5)
                
    async def process_training_batch(self):
        """Process a batch of training events with specialization-based routing"""
        batch = []
        for _ in range(min(self.batch_size, len(self.training_queue))):
            if self.training_queue:
                batch.append(self.training_queue.popleft())
        
        # Route events to appropriate agents based on specialization
        specialized_batches = self._route_events_by_specialization(batch)
        
        # Train each agent with its specialized batch
        training_tasks = []
        for agent_id, events in specialized_batches.items():
            if agent_id in self.agents and events:
                task = self.train_agent_batch(agent_id, events)
                training_tasks.append(task)
        
        if training_tasks:
            await asyncio.gather(*training_tasks)
            
    def _route_events_by_specialization(self, events: List[LearningEvent]) -> Dict[str, List[LearningEvent]]:
        """Route training events to appropriate agents based on their specialization"""
        routed_events = {agent_id: [] for agent_id in self.agents.keys()}
        
        for event in events:
            # Determine which agents should receive this event
            relevant_agents = self._find_relevant_agents(event)
            
            for agent_id in relevant_agents:
                if agent_id in routed_events:
                    routed_events[agent_id].append(event)
        
        return routed_events
    
    def _find_relevant_agents(self, event: LearningEvent) -> List[str]:
        """Find agents that should be trained on this specific event"""
        relevant_agents = []
        
        # Extract event characteristics
        event_type = event.event_type
        data = event.data
        threat_type = data.get('type', '').lower()
        
        # Route based on event characteristics
        for agent_id, agent in self.agents.items():
            agent_metrics = self.training_metrics.get(agent_id, {})
            expertise = agent_metrics.get('expertise_areas', [])
            specialization = agent_metrics.get('specialization', 'general')
            
            should_train = False
            
            # Behavioral events for behavioral agents
            if (specialization == 'behavioral_analysis' and 
                any(keyword in event_type.lower() or keyword in threat_type 
                    for keyword in ['behavior', 'user', 'access', 'pattern', 'anomaly'])):
                should_train = True
            
            # External threats for external agents
            elif (specialization == 'external_threats' and 
                  any(keyword in threat_type or keyword in str(data).lower()
                      for keyword in ['malware', 'phishing', 'ddos', 'network', 'intrusion'])):
                should_train = True
            
            # Learning agents get diverse training data
            elif specialization in ['general', 'adaptive_learning']:
                should_train = True
            
            # Specific expertise matches
            elif any(exp in threat_type or exp in event_type.lower() 
                    for exp in expertise):
                should_train = True
            
            if should_train:
                relevant_agents.append(agent_id)
        
        # Ensure at least one agent gets the event
        if not relevant_agents and self.agents:
            # Default to the first available agent
            relevant_agents = [list(self.agents.keys())[0]]
        
        return relevant_agents
            
    async def train_agent_batch(self, agent_id: str, events: List[LearningEvent]):
        """Train a specific agent with a batch of events"""
        agent = self.agents[agent_id]
        start_time = time.time()
        
        try:
            # Prepare training data
            training_data = self.prepare_training_data(events)
            
            # Perform training based on agent type
            if hasattr(agent, 'continuous_learn'):
                await agent.continuous_learn(training_data)
            elif hasattr(agent, 'learn_from_experience'):
                for data in training_data:
                    agent.learn_from_experience(data)
            
            # Update training metrics
            training_time = time.time() - start_time
            self.training_metrics[agent_id]['training_sessions'] += 1
            self.training_metrics[agent_id]['last_training'] = datetime.now()
            
            # Evaluate performance after training
            performance = await self.evaluate_agent_performance(agent_id, events)
            self.performance_history[agent_id].append(performance)
            
            self.logger.info(f"🎯 Trained {agent_id} with {len(events)} events (accuracy: {performance.accuracy:.3f})")
            
        except Exception as e:
            self.logger.error(f"❌ Error training agent {agent_id}: {e}")
            
    def prepare_training_data(self, events: List[LearningEvent]) -> List[Dict[str, Any]]:
        """Prepare training data from learning events"""
        training_data = []
        
        for event in events:
            data_point = {
                'event_type': event.event_type,
                'timestamp': event.timestamp,
                'data': event.data,
                'feedback': event.feedback,
                'confidence': event.confidence
            }
            
            # Add features based on event type
            if event.event_type == 'threat_detected':
                data_point.update({
                    'threat_level': event.data.get('severity', 5),
                    'threat_type': event.data.get('type', 'unknown'),
                    'success': event.data.get('verified', False)
                })
            elif event.event_type == 'false_positive':
                data_point.update({
                    'error_type': 'false_positive',
                    'correction': event.feedback,
                    'success': False
                })
            
            training_data.append(data_point)
            
        return training_data
    
    async def evaluate_agent_performance(self, agent_id: str, recent_events: List[LearningEvent]) -> TrainingMetrics:
        """Evaluate agent performance based on recent events"""
        
        # Calculate basic metrics
        true_positives = sum(1 for e in recent_events 
                           if e.event_type == 'threat_detected' and e.data.get('verified', False))
        false_positives = sum(1 for e in recent_events 
                            if e.event_type == 'false_positive')
        total_detections = sum(1 for e in recent_events 
                             if e.event_type == 'threat_detected')
        
        accuracy = true_positives / max(total_detections, 1)
        precision = true_positives / max(true_positives + false_positives, 1)
        recall = true_positives / max(true_positives + false_positives, 1)  # Simplified
        f1_score = 2 * (precision * recall) / max(precision + recall, 0.001)
        
        return TrainingMetrics(
            agent_id=agent_id,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            training_time=0.0,
            data_points=len(recent_events),
            timestamp=datetime.now()
        )
    
    async def adjust_learning_rates(self):
        """Dynamically adjust learning rates based on performance"""
        for agent_id, agent in self.agents.items():
            if not hasattr(agent, 'learning_rate'):
                continue
                
            performance_trend = self.get_performance_trend(agent_id)
            
            if performance_trend > self.improvement_threshold:
                # Performance improving - slightly increase learning rate
                if hasattr(agent, 'max_learning_rate'):
                    agent.learning_rate = min(agent.learning_rate * 1.05, agent.max_learning_rate)
            elif performance_trend < -self.improvement_threshold:
                # Performance declining - decrease learning rate
                if hasattr(agent, 'min_learning_rate'):
                    agent.learning_rate = max(agent.learning_rate * 0.95, agent.min_learning_rate)
                    
            self.training_metrics[agent_id]['learning_rate_adjustments'] += 1
    
    def get_performance_trend(self, agent_id: str) -> float:
        """Calculate performance trend for an agent"""
        if agent_id not in self.performance_history:
            return 0.0
            
        history = list(self.performance_history[agent_id])
        if len(history) < 2:
            return 0.0
            
        recent_accuracy = np.mean([h.accuracy for h in history[-10:]])
        older_accuracy = np.mean([h.accuracy for h in history[-20:-10]]) if len(history) >= 20 else recent_accuracy
        
        return recent_accuracy - older_accuracy
    
    async def share_knowledge_between_agents(self):
        """Share successful patterns between agents"""
        # Find best performing agents
        best_performers = []
        for agent_id in self.agents:
            if agent_id in self.performance_history:
                recent_performance = list(self.performance_history[agent_id])[-5:]
                if recent_performance:
                    avg_accuracy = np.mean([p.accuracy for p in recent_performance])
                    best_performers.append((agent_id, avg_accuracy))
        
        best_performers.sort(key=lambda x: x[1], reverse=True)
        
        # Share knowledge from top performers to others
        if len(best_performers) > 1:
            top_performer_id = best_performers[0][0]
            top_agent = self.agents[top_performer_id]
            
            for agent_id, accuracy in best_performers[1:]:
                if accuracy < self.accuracy_threshold:
                    await self.transfer_knowledge(top_agent, self.agents[agent_id])
    
    async def transfer_knowledge(self, source_agent: Any, target_agent: Any):
        """Transfer knowledge from high-performing agent to another"""
        try:
            # Transfer threat patterns
            if hasattr(source_agent, 'threat_patterns') and hasattr(target_agent, 'threat_patterns'):
                successful_patterns = [p for p in source_agent.threat_patterns 
                                     if p.get('success_rate', 0) > 0.8]
                target_agent.threat_patterns.extend(successful_patterns[-10:])  # Transfer top 10
            
            # Transfer experiences
            if hasattr(source_agent, 'experiences') and hasattr(target_agent, 'experiences'):
                successful_experiences = [e for e in source_agent.experiences[-50:] 
                                        if e.get('outcome') == 'success']
                target_agent.experiences.extend(successful_experiences[-5:])  # Transfer top 5
                
            self.logger.info(f"🔄 Transferred knowledge from {source_agent.name} to {target_agent.name}")
            
        except Exception as e:
            self.logger.error(f"❌ Error transferring knowledge: {e}")
    
    async def improve_underperforming_agents(self):
        """Apply additional improvements to underperforming agents"""
        for agent_id, agent in self.agents.items():
            if agent_id not in self.performance_history:
                continue
                
            recent_performance = list(self.performance_history[agent_id])[-10:]
            if not recent_performance:
                continue
                
            avg_accuracy = np.mean([p.accuracy for p in recent_performance])
            
            if avg_accuracy < self.accuracy_threshold:
                # Agent is underperforming - apply improvements
                await self.enhance_agent_capabilities(agent_id, agent, avg_accuracy)
    
    async def enhance_agent_capabilities(self, agent_id: str, agent: Any, current_accuracy: float):
        """Enhance capabilities of underperforming agent with specialized training"""
        try:
            # Increase sensitivity for threat detection
            if hasattr(agent, 'threat_threshold'):
                agent.threshold = max(agent.threat_threshold * 0.9, 0.1)
            
            # Generate specialized training data based on agent expertise
            synthetic_data = await self._generate_specialized_training_data(agent_id, agent)
            
            for data_point in synthetic_data:
                event = LearningEvent(
                    event_type=data_point.get('event_type', 'threat_detected'),
                    agent_id=agent_id,
                    data=data_point.get('data', {}),
                    confidence=data_point.get('confidence', 0.8)
                )
                self.add_learning_event(event)
            
            # Reset and retrain with focused data
            if hasattr(agent, 'reset_learning_state'):
                agent.reset_learning_state()
                
            self.logger.info(f"🔧 Enhanced {agent_id} with {len(synthetic_data)} specialized training samples (accuracy: {current_accuracy:.3f})")
            
        except Exception as e:
            self.logger.error(f"❌ Error enhancing agent {agent_id}: {e}")
    
    async def _generate_specialized_training_data(self, agent_id: str, agent: Any) -> List[Dict]:
        """Generate training data specialized for the agent's expertise"""
        synthetic_data = []
        
        try:
            # Use agent's specialized data generation if available
            if hasattr(agent, 'generate_behavioral_training_data'):
                synthetic_data.extend(agent.generate_behavioral_training_data(count=20))
            
            elif hasattr(agent, 'generate_external_training_data'):
                synthetic_data.extend(agent.generate_external_training_data(count=25))
            
            elif hasattr(agent, 'generate_synthetic_threats'):
                threats = agent.generate_synthetic_threats(count=30)
                for threat in threats:
                    synthetic_data.append({
                        'event_type': 'threat_detected',
                        'data': threat,
                        'confidence': 0.8,
                        'verified': True
                    })
            
            # Fallback: generate generic training data based on expertise
            if not synthetic_data:
                agent_metrics = self.training_metrics.get(agent_id, {})
                expertise = agent_metrics.get('expertise_areas', ['general_security'])
                synthetic_data = self._generate_generic_training_data(expertise, count=15)
        
        except Exception as e:
            self.logger.error(f"Error generating specialized training data for {agent_id}: {e}")
        
        return synthetic_data
    
    def _generate_generic_training_data(self, expertise_areas: List[str], count: int = 15) -> List[Dict]:
        """Generate generic training data based on expertise areas"""
        data = []
        
        for i in range(count):
            expertise = expertise_areas[i % len(expertise_areas)]
            
            if 'behavioral' in expertise or 'user' in expertise:
                data.append({
                    'event_type': 'user_behavior',
                    'data': {
                        'type': 'login_pattern',
                        'user_id': f'user_{i}',
                        'anomaly_score': 0.3 + (i % 3) * 0.2,
                        'frequency': i % 5 + 1
                    },
                    'confidence': 0.7
                })
            
            elif 'network' in expertise or 'external' in expertise:
                data.append({
                    'event_type': 'threat_detected',
                    'data': {
                        'type': 'network_scan',
                        'severity': 4 + (i % 4),
                        'source_ip': f'192.168.1.{i % 255}',
                        'port': 80 + (i % 1000)
                    },
                    'confidence': 0.75
                })
            
            else:  # General security
                data.append({
                    'event_type': 'threat_detected',
                    'data': {
                        'type': 'generic_threat',
                        'severity': 3 + (i % 5),
                        'category': 'security_event'
                    },
                    'confidence': 0.6
                })
        
        return data
    
    async def train_agent_immediate(self, agent_id: str, critical_event: LearningEvent):
        """Immediately train agent on critical event"""
        if agent_id not in self.agents:
            return
            
        try:
            await self.train_agent_batch(agent_id, [critical_event])
            self.logger.info(f"⚡ Immediate training completed for {agent_id} on {critical_event.event_type}")
        except Exception as e:
            self.logger.error(f"❌ Error in immediate training for {agent_id}: {e}")
    
    async def update_performance_metrics(self):
        """Update global performance metrics"""
        if not self.performance_history:
            return
            
        all_recent_metrics = []
        for agent_id in self.performance_history:
            recent = list(self.performance_history[agent_id])[-10:]
            all_recent_metrics.extend(recent)
        
        if all_recent_metrics:
            self.global_performance['average_accuracy'] = np.mean([m.accuracy for m in all_recent_metrics])
            
            # Calculate learning velocity (improvement rate)
            if len(all_recent_metrics) > 1:
                recent_accuracy = np.mean([m.accuracy for m in all_recent_metrics[-5:]])
                older_accuracy = np.mean([m.accuracy for m in all_recent_metrics[-10:-5]]) if len(all_recent_metrics) >= 10 else recent_accuracy
                self.global_performance['learning_velocity'] = recent_accuracy - older_accuracy
    
    def get_training_status(self) -> Dict[str, Any]:
        """Get current training system status"""
        return {
            'active_agents': len(self.agents),
            'training_queue_size': len(self.training_queue),
            'learning_events_total': len(self.learning_events),
            'global_performance': self.global_performance,
            'agent_metrics': {
                agent_id: {
                    'training_sessions': metrics['training_sessions'],
                    'last_training': metrics['last_training'].isoformat() if metrics['last_training'] else None,
                    'recent_accuracy': np.mean([m.accuracy for m in list(self.performance_history[agent_id])[-5:]]) if agent_id in self.performance_history and self.performance_history[agent_id] else 0.0
                }
                for agent_id, metrics in self.training_metrics.items()
            }
        }
    
    def stop_training(self):
        """Stop continuous training system"""
        self.training_active = False
        self.logger.info("🛑 Continuous training system stopped")

# Global continuous training system instance
continuous_trainer = ContinuousTrainingSystem()

async def start_continuous_training():
    """Start the continuous training system"""
    # Register existing agents
    learning_agent = LearningAgent("main_learning_agent")
    continuous_trainer.register_agent("learning_agent", learning_agent)
    
    try:
        behavioral_agent = BehavioralAnalyticsAgent()
        continuous_trainer.register_agent("behavioral_agent", behavioral_agent)
    except:
        pass
    
    try:
        external_agent = ExternalAgent()
        continuous_trainer.register_agent("external_agent", external_agent)
    except:
        pass
    
    # Start continuous training loop
    await continuous_trainer.continuous_training_loop()

def simulate_threat_detection(agent_id: str, threat_data: Dict[str, Any], verified: bool = True):
    """Simulate a threat detection for training purposes"""
    event = LearningEvent(
        event_type='threat_detected',
        agent_id=agent_id,
        data={**threat_data, 'verified': verified},
        confidence=threat_data.get('confidence', 0.8)
    )
    continuous_trainer.add_learning_event(event)

def report_false_positive(agent_id: str, detection_data: Dict[str, Any], feedback: str):
    """Report a false positive for immediate retraining"""
    event = LearningEvent(
        event_type='false_positive',
        agent_id=agent_id,
        data=detection_data,
        feedback=feedback,
        confidence=0.0
    )
    continuous_trainer.add_learning_event(event)

if __name__ == "__main__":
    print("🚀 GuardianShield Continuous Training System")
    print("=" * 50)
    print("Starting continuous learning for AI agents...")
    
    # Run the continuous training system
    asyncio.run(start_continuous_training())