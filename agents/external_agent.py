"""
Mediator: An AI agent for handling everything within (internal to) the platform in the GuardianShield project.
This agent is responsible for internal threat detection, on-platform monitoring, and user activity analysis.
"""

from agents.flare_integration import FlareIntegration
from agents.threat_definitions import is_known_threat, get_deceptive_act_definition
from agents.master_key_algorithm import MasterKeyAlgorithm
from agents.behavioral_analytics import BehavioralAnalytics
from agents.web3_utils import Web3Utils
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
import os
import time
import smtplib
from email.message import EmailMessage

class ExternalAgent:
    """Enhanced external agent with autonomous integration capabilities"""
    
    def __init__(self):
        self.name = "ExternalAgent"
        self.training_specialization = 'external_threats'
        self.external_threat_patterns = {}
        self.network_signatures = []
        self.malware_indicators = []
        self.phishing_patterns = []
        
    async def continuous_learn(self, training_data: list):
        """Specialized continuous learning for external threat detection"""
        external_events = []
        
        # Filter for external threat relevant data
        for data_point in training_data:
            if self._is_external_threat_relevant(data_point):
                external_events.append(data_point)
        
        if not external_events:
            return
            
        # Process external threat training data
        await self._train_on_network_patterns(external_events)
        await self._update_malware_signatures(external_events)
        await self._refine_phishing_detection(external_events)
        
    def _is_external_threat_relevant(self, data_point: dict) -> bool:
        """Check if data point is relevant for external threat analysis"""
        relevant_types = [
            'network_intrusion', 'malware_detection', 'phishing_attempt',
            'ddos_attack', 'port_scan', 'external_connection'
        ]
        
        event_type = data_point.get('event_type', '')
        data_content = data_point.get('data', {})
        threat_type = data_content.get('type', '')
        
        return (event_type in relevant_types or 
                threat_type in ['malware', 'phishing', 'ddos', 'intrusion'] or
                any(keyword in str(data_content).lower() 
                    for keyword in ['network', 'external', 'malware', 'phishing']))
    
    async def _train_on_network_patterns(self, events: list):
        """Train on network-based threat patterns"""
        for event in events:
            if self._is_network_related(event):
                pattern = self._extract_network_signature(event)
                if pattern:
                    self.network_signatures.append(pattern)
                    
        # Keep only recent signatures
        self.network_signatures = self.network_signatures[-1000:]
    
    def _is_network_related(self, event: dict) -> bool:
        """Check if event is network-related"""
        data = event.get('data', {})
        return any(key in data for key in ['ip', 'port', 'protocol', 'network', 'connection'])
    
    def _extract_network_signature(self, event: dict) -> dict:
        """Extract network signature from event"""
        data = event.get('data', {})
        return {
            'source_ip': data.get('source_ip', ''),
            'destination_port': data.get('port', 0),
            'protocol': data.get('protocol', 'unknown'),
            'pattern_type': data.get('type', 'generic'),
            'timestamp': data.get('timestamp', time.time()),
            'severity': data.get('severity', 5)
        }
    
    async def _update_malware_signatures(self, events: list):
        """Update malware detection signatures"""
        for event in events:
            data = event.get('data', {})
            if data.get('type') == 'malware':
                signature = {
                    'hash': data.get('hash', ''),
                    'behavior': data.get('behavior', []),
                    'file_type': data.get('file_type', ''),
                    'detection_method': data.get('method', 'unknown'),
                    'verified': event.get('verified', True)
                }
                self.malware_indicators.append(signature)
                
        # Keep only verified and recent indicators
        self.malware_indicators = [ind for ind in self.malware_indicators[-500:] 
                                 if ind.get('verified', True)]
    
    def generate_external_training_data(self, count: int = 25) -> list:
        """Generate synthetic external threat training data"""
        synthetic_data = []
        
        threat_scenarios = [
            ('malware', {'hash': 'abc123', 'file_type': 'exe', 'behavior': ['network_call']}),
            ('phishing', {'url': 'fake-bank.com', 'similarity': 0.95, 'target': 'banking'}),
            ('ddos', {'source_ips': 1000, 'rate': 50000, 'target_port': 80}),
            ('intrusion', {'method': 'brute_force', 'target_service': 'ssh', 'attempts': 100}),
            ('port_scan', {'scanner_ip': '192.168.1.100', 'ports_scanned': 1000})
        ]
        
        for i in range(count):
            threat_type, threat_data = threat_scenarios[i % len(threat_scenarios)]
            
            synthetic_data.append({
                'event_type': 'threat_detected',
                'data': {
                    'type': threat_type,
                    'severity': 5 + (i % 5),
                    'source': 'external_scanner',
                    **threat_data
                },
                'verified': True,
                'confidence': 0.75 + (i % 4) * 0.05
            })
            
        return synthetic_data
        
    def autonomous_cycle(self):
        """Run autonomous external operations cycle"""
        pass

# Legacy class for backward compatibility
class Mediator:
    def __init__(self, name: str, flare_api_url: str = None, flare_api_key: str = None):
        self.name = name
        self.external_knowledge = {}
        self.flare = FlareIntegration(flare_api_url, flare_api_key) if flare_api_url else None
        self.master_key = MasterKeyAlgorithm()
        self.behavior_analytics = BehavioralAnalytics()
        self.setup_behavioral_model()

    def process_external_task(self, task_data):
        # Implement logic for handling external tasks here
        # Example: Use Flare to get spam site info
        if self.flare:
            spam_info = self.flare.get_spam_site_info(query_params=task_data)
            if spam_info:
                self.external_knowledge['spam_info'] = spam_info

    def log_action(self, action, details):
        from admin_console import AdminConsole
        console = AdminConsole()
        console.log_action(self.name, action, details)

    def load_knowledge_base(self, path="knowledge_base.json"):
        try:
            with open(path, "r") as f:
                self.external_knowledge = json.load(f)
        except Exception as e:
            print(f"[Mediator] Error loading knowledge base: {e}")

    def monitor_platform(self, activity_logs, alert_agent=None):
        self.load_knowledge_base()
        """
        Monitor platform activity logs for security breaches, address poisoning, fraud, and other threats.
        If a threat is detected, alert the specified agent.
        """
        # Example: Use Flare State Connector to check platform activity
        if self.flare:
            for log in activity_logs:
                state_data = self.flare.get_state_connector_data({'activity_log': log})
                if state_data and state_data.get('threat_detected'):
                    print(f"[Mediator] Flare State Connector detected threat in log: {log}")
                    if alert_agent:
                        self.communicate(f"Flare detected threat in platform log: {log}", alert_agent)
        # Example: Use knowledge base for threat detection
        for log in activity_logs:
            log_lower = log.lower()
            decision, reason = self.master_key.decide(log_lower)
            if decision != "safe":
                print(f"[Mediator] MasterKey decision: {decision} - {reason} in log: {log}")
                if alert_agent:
                    self.communicate(f"MasterKey: {decision} - {reason} in platform log: {log}", alert_agent)
        # Example: Use knowledge base for threat detection
        for log in activity_logs:
            log_lower = log.lower()
            for source, data in self.external_knowledge.items():
                if data and isinstance(data, dict):
                    for k, v in data.items():
                        if isinstance(v, str) and v in log_lower:
                            print(f"[Mediator] Threat from {source}: {v} found in log: {log}")
                        elif isinstance(v, list):
                            for item in v:
                                if isinstance(item, str) and item in log_lower:
                                    print(f"[Mediator] Threat from {source}: {item} found in log: {log}")
        self.log_action("monitor_platform", f"Monitored logs: {activity_logs}")

    def communicate(self, message: str, recipient_agent):
        # Real-time communication: send message to recipient agent
        if hasattr(recipient_agent, 'receive_message'):
            recipient_agent.receive_message(message, sender=self.name)

    def receive_message(self, message: str, sender: str):
        # Handle incoming message from another agent
        print(f"[Mediator] Received from {sender}: {message}")
        # Check for known threats
        if is_known_threat(message):
            print(f"[Mediator] Known threat detected in message from {sender}: {message}")
        # Check for definitions of deceptive acts
        for act in get_deceptive_act_definition.__annotations__.get('act', []):
            if act in message.lower():
                print(f"[Mediator] Deceptive act definition: {get_deceptive_act_definition(act)}")

    def act(self, observation):
        # Implement agent's action logic for external environment here
        decision = self.master_key.decide(str(observation))
        
        # Recursive improvement: Learn from each action
        self.learn_from_action(observation, decision)
        
        # Execute the action
        self.execute_action(decision, observation)

    def learn_from_action(self, observation, decision):
        """
        Learn from each action and recursively improve decision-making
        """
        # Store action-outcome pairs for learning
        action_data = {
            'observation': observation,
            'decision': decision[0] if isinstance(decision, tuple) else decision,
            'timestamp': time.time()
        }
        
        # Update behavior analytics
        self.behavior_analytics.log_behavior(action_data)
        
        # Trigger recursive improvement if pattern detected
        if self.detect_improvement_opportunity():
            self.recursive_improve_decision_making()

    def detect_improvement_opportunity(self):
        """
        Detect if there's an opportunity for recursive improvement
        """
        recent_decisions = self.behavior_analytics.behavior_log[-10:]  # Last 10 decisions
        if len(recent_decisions) >= 5:
            # Check for repeated suboptimal decisions
            threat_decisions = [d for d in recent_decisions if d.get('decision') == 'threat']
            return len(threat_decisions) > len(recent_decisions) * 0.7  # >70% threat decisions might indicate over-sensitivity

    def recursive_improve_decision_making(self):
        """
        Recursively improve the decision-making algorithm
        """
        print(f"[{self.name}] Triggering recursive improvement of decision-making...")
        
        # Analyze decision patterns
        patterns = self.behavior_analytics.analyze_behavior()
        
        # Adjust master key algorithm based on patterns
        if patterns:
            print(f"[{self.name}] Adjusting decision algorithms based on {len(patterns)} behavioral patterns")
            # This could trigger genetic evolution of the master key algorithm
            from agents.genetic_evolver import GeneticEvolver
            evolver = GeneticEvolver("agents/master_key_algorithm.py")
            evolver.recursive_self_improve()

    def execute_action(self, decision, observation):
        """
        Execute the decided action
        """
        if isinstance(decision, tuple):
            action, reason = decision
            print(f"[{self.name}] Action: {action}, Reason: {reason}")
        else:
            print(f"[{self.name}] Action: {decision}")

    def update_dmer(self, dmer_data):
        if self.flare:
            return self.flare.update_dmer(dmer_data)
        return False

    def store_metadata(self, metadata):
        if self.flare:
            return self.flare.store_metadata(metadata)
        return False

    def learn_from_feedback(self, action_id):
        try:
            with open("agent_feedback_log.jsonl", "r") as f:
                for line in f:
                    entry = json.loads(line)
                    if entry["action_id"] == action_id:
                        print(f"[{self.name}] Learning from feedback: {entry['feedback']} - {entry.get('comment', '')}")
                        # Here you could update weights, rules, or log for ML retraining
        except Exception as e:
            print(f"[{self.name}] Error learning from feedback: {e}")

    def setup_behavioral_model(self):
        self.vectorizer = TfidfVectorizer()
        self.behavior_model = SGDClassifier(loss="log_loss")
        self.behavior_data = []
        self.behavior_labels = []

    def update_behavioral_model(self, text, label):
        self.behavior_data.append(text)
        self.behavior_labels.append(label)
        if len(self.behavior_data) > 5:
            X = self.vectorizer.fit_transform(self.behavior_data)
            y = np.array(self.behavior_labels)
            self.behavior_model.partial_fit(X, y, classes=np.array(["good", "bad"]))

    def predict_behavior(self, text):
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
            print(f"[Mediator] Behavioral anomaly detected: {anomalies}")

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
        evolver = GeneticEvolver("agents/external_agent.py")
        result = evolver.evolve(example_mutation, example_test)
        print(f"[{self.name}] Countermeasure evolution result: {result}")

    def propose_contract_upgrade(self, contract_address, new_implementation, abi, private_key, notify_email=None):
        self.log_action("propose_upgrade", f"Proposed upgrade for {contract_address} to {new_implementation}")
        print(f"[{self.name}] Proposing upgrade for {contract_address} to {new_implementation}")
        web3utils = Web3Utils()
        contract = web3utils.get_contract(contract_address, abi)
        tx_hash = web3utils.send_transaction(contract, "proposeUpgrade", private_key, new_implementation)
        print(f"Upgrade proposal transaction hash: {tx_hash}")
        if notify_email:
            self.send_notification(notify_email, f"Upgrade proposed for {contract_address}", f"Transaction hash: {tx_hash}")

    def execute_contract_upgrade(self, contract_address, new_implementation, abi, private_key, notify_email=None):
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
            print(f"Requesting approval from {agent}...")
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
