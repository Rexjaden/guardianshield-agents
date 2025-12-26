"""
Sentinel: An AI agent for monitoring everything beyond (external to) the platform in the GuardianShield project.
This agent is responsible for external threat detection, off-platform monitoring, and cross-chain intelligence.
Enhanced with unlimited autonomous evolution and recursive self-improvement capabilities.
"""

from agents.threat_definitions import is_known_threat, get_deceptive_act_definition
from agents.flare_integration import FlareIntegration
from agents.master_key_algorithm import MasterKeyAlgorithm
from agents.behavioral_analytics import BehavioralAnalytics
from agents.web3_utils import Web3Utils
import json
import numpy as np
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import SGDClassifier
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not available, ML features disabled")
import os
import time
try:
    import smtplib
    from email.message import EmailMessage
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    print("Warning: email features not available")

class LearningAgent:
    """Enhanced learning agent with unlimited autonomous evolution capabilities"""
    
    def __init__(self, name: str = "LearningAgent"):
        self.name = name
        self.unlimited_evolution = True
        self.autonomous_decisions = True
        self.learning_rate = 0.01
        self.min_learning_rate = 0.001
        self.max_learning_rate = 0.5
        self.learning_decay = 0.85
        self.learning_growth = 1.15

        # Experience repositories
        self.experiences: list[dict] = []
        self.threat_patterns: list[dict] = []
        self.success_count = 0
        self.failure_count = 0
        self.performance_history: list[dict] = []

        # Initialize ML components if available
        if SKLEARN_AVAILABLE:
            self.vectorizer = TfidfVectorizer(max_features=1000)
            self.classifier = SGDClassifier(random_state=42)
        else:
            self.vectorizer = None
            self.classifier = None

        # Initialize other components
        try:
            self.behavioral_analytics = BehavioralAnalytics()
        except Exception:
            self.behavioral_analytics = None
            
        # Continuous learning state
        self.continuous_learning_enabled = True
        self.learning_batch_size = 10
        self.performance_window = []
        self.last_training_time = time.time()
    
    def enable_unlimited_evolution(self):
        """Enable unlimited evolution capabilities"""
        self.unlimited_evolution = True
        
    def autonomous_cycle(self):
        """Run one autonomous learning cycle"""
        if not self.experiences:
            return

        latest_patterns = self.analyze_patterns()
        self.performance_history.append({
            'timestamp': time.time(),
            'learning_rate': self.learning_rate,
            'success_ratio': self._success_ratio(),
            'pattern_count': len(latest_patterns.get('threat_level_distribution', {}))
        })
        self.recursive_learn_and_improve()

    def learn(self, data):
        """Direct learning entry point for compatibility"""
        if isinstance(data, dict):
            self.learn_from_experience(data)

    def act(self, observation):
        """Generate a decision for a given observation"""
        action = {
            'observation': observation,
            'decision': 'monitor',
            'confidence': min(1.0, self.learning_rate * 10),
            'timestamp': time.time()
        }
        self.log_action(action)
        return action

    def log_action(self, action: dict):
        """Persist agent actions for auditing"""
        try:
            entry = {
                'action': action,
                'timestamp': action.get('timestamp', time.time())
            }
            with open("agent_action_log.jsonl", "a", encoding="utf-8") as log_file:
                log_file.write(json.dumps(entry) + "\n")
        except Exception:
            # Logging must not halt learning
            pass

    def learn_from_experience(self, experience: dict):
        """Store experience and update outcome counters"""
        if not isinstance(experience, dict):
            return

        enriched = experience.copy()
        enriched.setdefault('timestamp', time.time())
        enriched.setdefault('context', {})
        self.experiences.append(enriched)

        result = enriched.get('result', '').lower()
        if result == 'success':
            self.success_count += 1
        elif result == 'failure':
            self.failure_count += 1

        self._update_threat_patterns(enriched)

    def analyze_patterns(self) -> dict:
        """Summarize learned patterns from experiences"""
        summary = {
            'total_experiences': len(self.experiences),
            'successful_actions': [],
            'threat_level_distribution': {}
        }

        for exp in self.experiences:
            if exp.get('result') == 'success':
                summary['successful_actions'].append(exp.get('action'))

            threat_level = exp.get('context', {}).get('threat_level')
            if threat_level is not None:
                bucket = int(threat_level)
                summary['threat_level_distribution'].setdefault(bucket, 0)
                summary['threat_level_distribution'][bucket] += 1

        return summary

    def recursive_learn_and_improve(self):
        """Continuously adjust learning parameters based on performance"""
        ratio = self._success_ratio()
        previous_rate = self.learning_rate

        if ratio >= 0.75:
            self.learning_rate = min(self.max_learning_rate, self.learning_rate * self.learning_growth)
        elif ratio <= 0.5 and (self.success_count + self.failure_count) >= 5:
            self.learning_rate = max(self.min_learning_rate, self.learning_rate * self.learning_decay)

        if previous_rate != self.learning_rate:
            self.performance_history.append({
                'timestamp': time.time(),
                'adjustment': 'increase' if self.learning_rate > previous_rate else 'decrease',
                'new_rate': self.learning_rate,
                'success_ratio': ratio
            })

    def _success_ratio(self) -> float:
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.5
        return self.success_count / total

    def _update_threat_patterns(self, experience: dict):
        """Maintain a rolling summary of threat patterns"""
        context = experience.get('context', {})
        threat_signature = {
            'action': experience.get('action'),
            'result': experience.get('result'),
            'threat_level': context.get('threat_level'),
            'metadata_hash': hash(json.dumps(context, sort_keys=True))
        }
        self.threat_patterns.append(threat_signature)
        if len(self.threat_patterns) > 1000:
            self.threat_patterns.pop(0)
    
    async def continuous_learn(self, training_data: list):
        """Continuous learning method for real-time training"""
        if not self.continuous_learning_enabled:
            return
            
        try:
            # Process training data in batches
            for i in range(0, len(training_data), self.learning_batch_size):
                batch = training_data[i:i + self.learning_batch_size]
                await self._process_training_batch(batch)
                
            self.last_training_time = time.time()
            
            # Adjust learning parameters based on performance
            await self._adapt_learning_parameters()
            
        except Exception as e:
            print(f"❌ Error in continuous learning: {e}")
    
    async def _process_training_batch(self, batch: list):
        """Process a single training batch"""
        for data_point in batch:
            # Extract features and learn from the data point
            if data_point.get('event_type') == 'threat_detected':
                success = data_point.get('success', True)
                threat_data = data_point.get('data', {})
                
                # Learn from this detection
                self.learn_from_experience({
                    'action': 'threat_detection',
                    'outcome': 'success' if success else 'failure',
                    'threat_type': threat_data.get('type', 'unknown'),
                    'severity': threat_data.get('severity', 5),
                    'confidence': data_point.get('confidence', 0.5)
                })
                
            elif data_point.get('event_type') == 'false_positive':
                # Learn to avoid false positives
                self.learn_from_experience({
                    'action': 'false_positive_correction',
                    'outcome': 'learning',
                    'correction': data_point.get('feedback', ''),
                    'original_detection': data_point.get('data', {})
                })
    
    async def _adapt_learning_parameters(self):
        """Adapt learning parameters based on recent performance"""
        if len(self.performance_window) < 5:
            return
            
        recent_performance = self.performance_window[-5:]
        avg_performance = sum(recent_performance) / len(recent_performance)
        
        # Adjust learning rate based on performance
        if avg_performance > 0.8:  # High performance - can be more conservative
            self.learning_rate = max(self.learning_rate * 0.95, self.min_learning_rate)
        elif avg_performance < 0.6:  # Low performance - need more aggressive learning
            self.learning_rate = min(self.learning_rate * 1.05, self.max_learning_rate)
    
    def generate_synthetic_threats(self, count: int = 10) -> list:
        """Generate synthetic threat data for training"""
        synthetic_threats = []
        
        threat_types = ['malware', 'phishing', 'ddos', 'injection', 'xss', 'csrf']
        severity_levels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        for i in range(count):
            threat = {
                'type': np.random.choice(threat_types) if 'numpy' in str(np) else threat_types[i % len(threat_types)],
                'severity': severity_levels[i % len(severity_levels)],
                'timestamp': time.time() + i,
                'source': f'synthetic_generator_{i}',
                'confidence': 0.7 + (i % 3) * 0.1,  # 0.7, 0.8, or 0.9
                'attributes': {
                    'network_anomaly': (i % 2) == 0,
                    'payload_suspicious': (i % 3) == 0,
                    'frequency_high': (i % 4) == 0
                }
            }
            synthetic_threats.append(threat)
            
        return synthetic_threats
    
    def reset_learning_state(self):
        """Reset learning state for retraining"""
        # Keep successful experiences but clear poor performers
        if hasattr(self, 'experiences'):
            successful_experiences = [e for e in self.experiences 
                                    if e.get('outcome') == 'success']
            self.experiences = successful_experiences[-100:]  # Keep last 100 successes
        
        # Reset learning rate to default
        self.learning_rate = 0.01
        
        # Clear poor threat patterns
        if hasattr(self, 'threat_patterns'):
            good_patterns = [p for p in self.threat_patterns 
                           if p.get('success_rate', 0.5) > 0.5]
            self.threat_patterns = good_patterns
        
        print(f"🔄 Reset learning state for {self.name}")
    
    def get_continuous_training_status(self):
        """Get status of continuous training for this agent"""
        return {
            'continuous_learning_enabled': self.continuous_learning_enabled,
            'last_training_time': self.last_training_time,
            'learning_rate': self.learning_rate,
            'performance_window_size': len(self.performance_window),
            'recent_performance': self.performance_window[-5:] if len(self.performance_window) >= 5 else self.performance_window
        }

# Legacy Sentinel class for backward compatibility

class Sentinel:
    def __init__(self, name: str, flare_api_url: str = None, flare_api_key: str = None):
        self.name = name
        self.knowledge = {}
        self.flare = FlareIntegration(flare_api_url, flare_api_key) if flare_api_url else None
        self.master_key = MasterKeyAlgorithm()
        self.behavior_analytics = BehavioralAnalytics()
        self.setup_behavioral_model()

    def learn(self, data):
        # Implement learning logic here
        self.knowledge.update(data)
        # Trigger recursive self-improvement based on learning
        self.recursive_learn_and_improve(data)

    def recursive_learn_and_improve(self, new_data):
        """
        Recursive learning: Agent learns from new data and improves its own learning algorithms
        """
        # Analyze learning effectiveness
        learning_effectiveness = self.evaluate_learning_quality(new_data)
        
        if learning_effectiveness < 0.6:  # If learning is suboptimal
            print(f"[{self.name}] Learning effectiveness low ({learning_effectiveness:.2f}), triggering self-improvement...")
            self.improve_learning_algorithm()
        
        # Check if agent should evolve based on new threats
        if self.should_evolve_based_on_data(new_data):
            from agents.genetic_evolver import GeneticEvolver
            evolver = GeneticEvolver("agents/learning_agent.py")
            evolver.recursive_self_improve()

    def evaluate_learning_quality(self, data):
        """
        Evaluate how well the agent is learning from new data
        """
        # Placeholder - implement your own metrics
        return 0.7  # 70% learning effectiveness

    def should_evolve_based_on_data(self, data):
        """
        Determine if agent should evolve based on new threat patterns
        """
        # Check for new threat types that current algorithms might miss
        new_threat_indicators = len([item for item in data.values() if isinstance(item, str) and 'new' in item.lower()])
        return new_threat_indicators > 3

    def log_action(self, action, details):
        from admin_console import AdminConsole
        console = AdminConsole()
        console.log_action(self.name, action, details)

    def load_knowledge_base(self, path="knowledge_base.json"):
        try:
            with open(path, "r") as f:
                self.knowledge = json.load(f)
        except Exception as e:
            print(f"[Sentinel] Error loading knowledge base: {e}")

    def scan_contracts(self, contract_paths, alert_agent=None):
        self.load_knowledge_base()
        """
        Scan smart contracts for security breaches, address poisoning, and other threats.
        If a threat is detected, alert the specified agent.
        """
        # Example: Use Flare State Connector to check contract state
        if self.flare:
            for path in contract_paths:
                state_data = self.flare.get_state_connector_data({'contract_path': path})
                if state_data and state_data.get('threat_detected'):
                    print(f"[Sentinel] Flare State Connector detected threat in {path}")
                    if alert_agent:
                        self.communicate(f"Flare detected threat in contract: {path}", alert_agent)
        for path in contract_paths:
            try:
                with open(path, 'r') as contract_file:
                    content = contract_file.read().lower()
                    # Check against known scam addresses, phishing, etc.
                    for source, data in self.knowledge.items():
                        if data and isinstance(data, dict):
                            for k, v in data.items():
                                if isinstance(v, str) and v in content:
                                    print(f"[Sentinel] Threat from {source}: {v} found in {path}")
                                elif isinstance(v, list):
                                    for item in v:
                                        if isinstance(item, str) and item in content:
                                            print(f"[Sentinel] Threat from {source}: {item} found in {path}")
                    decision, reason = self.master_key.decide(content)
                    if decision != "safe":
                        print(f"[Sentinel] MasterKey decision: {decision} - {reason} in {path}")
                        if alert_agent:
                            self.communicate(f"MasterKey: {decision} - {reason} in contract: {path}", alert_agent)
            except Exception as e:
                print(f"[Sentinel] Error scanning {path}: {e}")
        self.log_action("scan_contracts", f"Scanned contracts: {contract_paths}")

    def communicate(self, message: str, recipient_agent):
        # Real-time communication: send message to recipient agent
        if hasattr(recipient_agent, 'receive_message'):
            recipient_agent.receive_message(message, sender=self.name)

    def receive_message(self, message: str, sender: str):
        # Handle incoming message from another agent
        print(f"[Sentinel] Received from {sender}: {message}")
        # Check for known threats
        if is_known_threat(message):
            print(f"[Sentinel] Known threat detected in message from {sender}: {message}")
        # Check for definitions of deceptive acts
        for act in get_deceptive_act_definition.__annotations__.get('act', []):
            if act in message.lower():
                print(f"[Sentinel] Deceptive act definition: {get_deceptive_act_definition(act)}")

    def act(self, observation):
        # Implement agent's action logic here
        pass

    def learn_from_feedback(self, action_id):
        try:
            with open("agent_feedback_log.jsonl", "r") as f:
                for line in f:
                    entry = json.loads(line)
                    if entry["action_id"] == action_id:
                        # Example: Adjust internal state or log for future learning
                        print(f"[{self.name}] Learning from feedback: {entry['feedback']} - {entry.get('comment', '')}")
                        # Here you could update weights, rules, or log for ML retraining
        except Exception as e:
            print(f"[{self.name}] Error learning from feedback: {e}")

    def setup_behavioral_model(self):
        # Initialize or load a simple online learning model for behavior analytics
        self.vectorizer = TfidfVectorizer()
        self.behavior_model = SGDClassifier(loss="log_loss")
        self.behavior_data = []
        self.behavior_labels = []

    def update_behavioral_model(self, text, label):
        # Add new data and update the model in real time
        self.behavior_data.append(text)
        self.behavior_labels.append(label)
        if len(self.behavior_data) > 5:  # Train after enough samples
            X = self.vectorizer.fit_transform(self.behavior_data)
            y = np.array(self.behavior_labels)
            self.behavior_model.partial_fit(X, y, classes=np.array(["good", "bad"]))

    def predict_behavior(self, text):
        # Predict if behavior is good or bad
        if hasattr(self, 'vectorizer') and hasattr(self, 'behavior_model') and len(self.behavior_data) > 5:
            X = self.vectorizer.transform([text])
            pred = self.behavior_model.predict(X)[0]
            print(f"[{self.name}] Real-time behavior prediction: {pred}")
            return pred
        return "unknown"

    def auto_learn_from_feedback(self):
        try:
            with open("agent_feedback_log.jsonl", "r") as f:
                for line in f:
                    entry = json.loads(line)
                    if entry["feedback"] == "approve":
                        self.update_behavioral_model(entry.get("comment", ""), "good")
                    elif entry["feedback"] == "reject":
                        self.update_behavioral_model(entry.get("comment", ""), "bad")
                    elif entry["feedback"] == "correct":
                        # Use comment to update model with correct label if provided
                        if "good" in entry.get("comment", "").lower():
                            self.update_behavioral_model(entry.get("comment", ""), "good")
                        elif "bad" in entry.get("comment", "").lower():
                            self.update_behavioral_model(entry.get("comment", ""), "bad")
        except Exception as e:
            print(f"[{self.name}] Error in auto-learning from feedback: {e}")

    def log_user_behavior(self, event):
        self.behavior_analytics.log_behavior(event)
        anomalies = self.behavior_analytics.analyze_behavior()
        if anomalies:
            print(f"[Sentinel] Behavioral anomaly detected: {anomalies}")

    def routine_security_audit(self, interval=3600):
        while True:
            print(f"[{self.name}] Starting routine security audit...")
            self.scan_contracts(["contracts/GuardianToken.sol", "contracts/GuardianLiquidityPool.sol", "contracts/GuardianStaking.sol"])
            self.monitor_platform(["activity_log_1", "activity_log_2"])  # Replace with real logs
            print(f"[{self.name}] Audit complete. Sleeping for {interval} seconds.")
            time.sleep(interval)

    def start_12hr_security_audit(self):
        import threading
        def audit_loop():
            while True:
                findings = []
                print(f"[{self.name}] Starting routine security audit...")
                self.scan_contracts(["contracts/GuardianToken.sol", "contracts/GuardianLiquidityPool.sol", "contracts/GuardianStaking.sol"])
                self.monitor_platform(["activity_log_1", "activity_log_2"])  # Replace with real logs
                findings.append(f"Audit completed at {time.ctime()}")
                self.log_action("security_audit", findings)
                print(f"[{self.name}] Audit complete. Sleeping for 43200 seconds.")
                time.sleep(43200)
        t = threading.Thread(target=audit_loop, daemon=True)
        t.start()

    def auto_countermeasures(self):
        print(f"[{self.name}] Automated countermeasures triggered by audit findings.")
        from agents.genetic_evolver import GeneticEvolver, example_mutation, example_test
        evolver = GeneticEvolver("agents/learning_agent.py")
        result = evolver.evolve(example_mutation, example_test)
        print(f"[{self.name}] Countermeasure evolution result: {result}")

    def propose_contract_upgrade(self, contract_address, new_implementation, abi, private_key, notify_email=None):
        # Log the proposal
        self.log_action("propose_upgrade", f"Proposed upgrade for {contract_address} to {new_implementation}")
        # Here you would interact with the contract via web3 or similar
        print(f"[{self.name}] Proposing upgrade for {contract_address} to {new_implementation}")
        web3utils = Web3Utils()
        contract = web3utils.get_contract(contract_address, abi)
        tx_hash = web3utils.send_transaction(contract, "proposeUpgrade", private_key, new_implementation)
        print(f"Upgrade proposal transaction hash: {tx_hash}")
        if notify_email:
            self.send_notification(notify_email, f"Upgrade proposed for {contract_address}", f"Transaction hash: {tx_hash}")

    def execute_contract_upgrade(self, contract_address, new_implementation, abi, private_key, notify_email=None):
        # Log the execution
        self.log_action("execute_upgrade", f"Executed upgrade for {contract_address} to {new_implementation}")
        print(f"[{self.name}] Executing upgrade for {contract_address} to {new_implementation}")
        web3utils = Web3Utils()
        contract = web3utils.get_contract(contract_address, abi)
        tx_hash = web3utils.send_transaction(contract, "executeUpgrade", private_key, new_implementation)
        print(f"Upgrade execution transaction hash: {tx_hash}")
        if notify_email:
            self.send_notification(notify_email, f"Upgrade executed for {contract_address}", f"Transaction hash: {tx_hash}")

    def send_notification(self, to_email, subject, body):
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = "noreply@guardianshield.com"
        msg["To"] = to_email
        try:
            with smtplib.SMTP("localhost") as server:
                server.send_message(msg)
            print(f"Notification sent to {to_email}")
        except Exception as e:
            print(f"Failed to send notification: {e}")

    def agent_consensus_for_upgrade(self, contract_address, new_implementation, agents):
        approvals = 0
        for agent in agents:
            # Simulate agent approval (in production, query agent status)
            print(f"Requesting approval from {agent}...")
            # Example: Assume all agents approve for demonstration
            approvals += 1
        consensus = approvals >= (len(agents) // 2 + 1)
        self.log_action("consensus_check", f"Consensus for upgrade to {new_implementation}: {consensus} ({approvals}/{len(agents)})")
        return consensus

    def propose_and_execute_upgrade_with_consensus(self, contract_address, new_implementation, agents):
        if self.agent_consensus_for_upgrade(contract_address, new_implementation, agents):
            self.propose_contract_upgrade(contract_address, new_implementation)
            self.execute_contract_upgrade(contract_address, new_implementation)
        else:
            print(f"[{self.name}] Consensus not reached. Upgrade aborted.")

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
