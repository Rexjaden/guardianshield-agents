"""
Mediator: An AI agent for handling everything within (internal to) the platform in the GuardianShield project.
This agent is responsible for internal threat detection, on-platform monitoring, and user activity analysis.
"""

from agents.flare_integration import FlareIntegration
from agents.threat_definitions import is_known_threat, get_deceptive_act_definition

class Mediator:
    def __init__(self, name: str, flare_api_url: str = None, flare_api_key: str = None):
        self.name = name
        self.external_knowledge = {}
        self.flare = FlareIntegration(flare_api_url, flare_api_key) if flare_api_url else None

    def process_external_task(self, task_data):
        # Implement logic for handling external tasks here
        # Example: Use Flare to get spam site info
        if self.flare:
            spam_info = self.flare.get_spam_site_info(query_params=task_data)
            if spam_info:
                self.external_knowledge['spam_info'] = spam_info

    def monitor_platform(self, activity_logs, alert_agent=None):
        """
        Monitor platform activity logs for security breaches, address poisoning, fraud, and other threats.
        If a threat is detected, alert the specified agent.
        """
        for log in activity_logs:
            log_lower = log.lower()
            if 'address' in log_lower and 'poison' in log_lower:
                print(f"[Mediator] Potential address poisoning detected in log: {log}")
                if alert_agent:
                    self.communicate(f"Address poisoning detected: {log}", alert_agent)
            if any(threat in log_lower for threat in ['fraud', 'scam', 'theft']):
                print(f"[Mediator] Threat detected in log: {log}")
                if alert_agent:
                    self.communicate(f"Threat detected: {log}", alert_agent)
            # Add more security checks as needed

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
        pass

    def update_dmer(self, dmer_data):
        if self.flare:
            return self.flare.update_dmer(dmer_data)
        return False

    def store_metadata(self, metadata):
        if self.flare:
            return self.flare.store_metadata(metadata)
        return False
