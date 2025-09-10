"""
master_key_algorithm.py: Hybrid decision-making and learning core for GuardianShield agents.
Combines rule-based, knowledge-driven, and machine learning approaches for adaptive intelligence.
"""
import json
import random

class MasterKeyAlgorithm:
    def __init__(self, knowledge_base_path="knowledge_base.json"):
        self.knowledge = self.load_knowledge_base(knowledge_base_path)
        self.rules = [
            self.rule_detect_blacklist,
            self.rule_detect_phishing,
            self.rule_detect_malware,
        ]
        # Placeholder for ML model (could be loaded here)
        self.ml_model = None

    def load_knowledge_base(self, path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[MasterKeyAlgorithm] Error loading knowledge base: {e}")
            return {}

    def rule_detect_blacklist(self, data):
        # Check if any known blacklist item is present
        for source, items in self.knowledge.items():
            if items and isinstance(items, dict):
                for k, v in items.items():
                    if isinstance(v, str) and v in data:
                        return True, f"Blacklisted item from {source}: {v}"
                    elif isinstance(v, list):
                        for item in v:
                            if isinstance(item, str) and item in data:
                                return True, f"Blacklisted item from {source}: {item}"
        return False, None

    def rule_detect_phishing(self, data):
        # Simple keyword-based phishing detection
        phishing_keywords = ["login", "verify", "account", "password", "urgent", "update"]
        for keyword in phishing_keywords:
            if keyword in data.lower():
                return True, f"Phishing keyword detected: {keyword}"
        return False, None

    def rule_detect_malware(self, data):
        # Simple malware indicator detection
        malware_indicators = ["exe", "dll", "payload", "trojan", "worm", "virus"]
        for indicator in malware_indicators:
            if indicator in data.lower():
                return True, f"Malware indicator detected: {indicator}"
        return False, None

    def ml_predict(self, data):
        # Placeholder for ML-based anomaly detection
        # In production, use a trained model (e.g., sklearn, tensorflow, etc.)
        # Here, randomly flag as anomaly for demonstration
        if random.random() < 0.05:
            return True, "ML anomaly detected"
        return False, None

    def decide(self, data):
        # Run all rules
        for rule in self.rules:
            result, reason = rule(data)
            if result:
                return "threat", reason
        # Run ML model
        ml_result, ml_reason = self.ml_predict(data)
        if ml_result:
            return "anomaly", ml_reason
        return "safe", None

if __name__ == "__main__":
    mka = MasterKeyAlgorithm()
    test_data = "Suspicious login attempt from blacklisted IP."
    decision, reason = mka.decide(test_data)
    print(f"Decision: {decision}, Reason: {reason}")
