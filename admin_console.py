"""
admin_console.py: Administrator console for reviewing and managing AI agent actions and code changes.
"""
import os
import json
from datetime import datetime

LOG_FILE = "agent_action_log.jsonl"

class AdminConsole:
    def __init__(self, log_file=LOG_FILE):
        self.log_file = log_file
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                pass

    def log_action(self, agent, action, details):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent,
            "action": action,
            "details": details
        }
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")

    def view_log(self, limit=20):
        with open(self.log_file, 'r') as f:
            lines = f.readlines()[-limit:]
            for line in lines:
                entry = json.loads(line)
                print(f"[{entry['timestamp']}] {entry['agent']} - {entry['action']}: {entry['details']}")

    def revert_last_action(self):
        # Placeholder: Implement logic to revert last action if possible
        print("Revert last action: Not yet implemented.")

    def approve_action(self, action_id):
        # Placeholder: Implement logic to approve a pending action
        print(f"Approve action {action_id}: Not yet implemented.")

    def edit_action(self, action_id, new_details):
        # Placeholder: Implement logic to edit a logged action
        print(f"Edit action {action_id}: Not yet implemented.")

    def provide_feedback(self, action_id, feedback, comment=None):
        # Log human feedback for a specific action
        feedback_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action_id": action_id,
            "feedback": feedback,
            "comment": comment
        }
        with open("agent_feedback_log.jsonl", 'a') as f:
            f.write(json.dumps(feedback_entry) + "\n")
        print(f"Feedback recorded for action {action_id}.")

    def view_behavior_anomalies(self, limit=20):
        try:
            with open("behavior_log.json", "r") as f:
                behavior_log = json.load(f)
            from agents.behavioral_analytics import BehavioralAnalytics
            ba = BehavioralAnalytics()
            ba.behavior_log = behavior_log
            anomalies = ba.analyze_behavior()
            print("Recent Behavioral Anomalies:")
            if anomalies:
                for idx, value, z in anomalies[-limit:]:
                    print(f"Index: {idx}, Value: {value}, Z-score: {z}")
            else:
                print("No anomalies detected.")
        except Exception as e:
            print(f"Error viewing behavioral anomalies: {e}")

    def evolve_agent_code(self, agent_file):
        from agents.genetic_evolver import GeneticEvolver, example_mutation, example_test
        evolver = GeneticEvolver(agent_file)
        result = evolver.evolve(example_mutation, example_test)
        print(f"Evolution result for {agent_file}: {result}")

    def rollback_agent_code(self, agent_file):
        import os
        backup_dir = "agents/evolution_backups"
        backup_file = os.path.join(backup_dir, f"{os.path.basename(agent_file)}.bak")
        from agents.genetic_evolver import GeneticEvolver
        evolver = GeneticEvolver(agent_file)
        evolver.restore_code(backup_file)
        print(f"Rolled back {agent_file} to previous version.")

    def view_security_audit_log(self, limit=20):
        with open(self.log_file, 'r') as f:
            lines = [json.loads(line) for line in f.readlines() if 'security_audit' in line][-limit:]
            for entry in lines:
                print(f"[{entry['timestamp']}] {entry['agent']} - Security Audit: {entry['details']}")

    def automated_response_to_audit(self):
        with open(self.log_file, 'r') as f:
            lines = [json.loads(line) for line in f.readlines() if 'security_audit' in line]
            for entry in lines[-5:]:  # Check last 5 audits
                details = entry['details']
                # Example: If findings indicate a threat, trigger countermeasures
                if any('threat' in str(d).lower() for d in details):
                    print(f"Automated response: Threat detected in audit by {entry['agent']}. Triggering countermeasures.")
                    # Call agent's auto_countermeasures (could be via API, subprocess, etc.)
                else:
                    print(f"Audit by {entry['agent']} is clean. No action needed.")

    def view_upgrade_log(self, limit=20):
        with open(self.log_file, 'r') as f:
            lines = [json.loads(line) for line in f.readlines() if 'upgrade' in line][-limit:]
            for entry in lines:
                print(f"[{entry['timestamp']}] {entry['agent']} - Upgrade: {entry['details']}")

    def run_full_upgrade_cycle(self):
        contract_address = input("Enter contract address: ")
        new_implementation = input("Enter new implementation address: ")
        agents = input("Enter agent addresses (comma separated): ").split(",")
        from agents.learning_agent import Sentinel
        sentinel = Sentinel("Sentinel")
        sentinel.propose_and_execute_upgrade_with_consensus(contract_address, new_implementation, agents)
        from agents.external_agent import Mediator
        mediator = Mediator("Mediator")
        mediator.propose_and_execute_upgrade_with_consensus(contract_address, new_implementation, agents)

if __name__ == "__main__":
    console = AdminConsole()
    print("GuardianShield Admin Console")
    print("1. View recent actions")
    print("2. Revert last action")
    print("3. Approve action")
    print("4. Edit action")
    print("5. Provide feedback on an action")
    print("6. View behavioral anomalies")
    print("7. Plot behavioral trends")
    print("8. Cluster behavioral data")
    print("9. Advanced anomaly detection (IQR)")
    print("10. Evolve agent code (genetic algorithm)")
    print("11. Rollback agent code to previous version")
    print("12. Advanced evolve agent code (deep mutation)")
    print("13. View security audit log")
    print("14. Run automated response to audit findings")
    print("15. View contract upgrade log")
    print("16. Run full contract upgrade cycle with agent consensus")
    choice = input("Select an option: ")
    if choice == "1":
        console.view_log()
    elif choice == "2":
        console.revert_last_action()
    elif choice == "3":
        action_id = input("Enter action ID: ")
        console.approve_action(action_id)
    elif choice == "4":
        action_id = input("Enter action ID: ")
        new_details = input("Enter new details: ")
        console.edit_action(action_id, new_details)
    elif choice == "5":
        action_id = input("Enter action ID: ")
        feedback = input("Enter feedback (approve/reject/correct): ")
        comment = input("Optional comment: ")
        console.provide_feedback(action_id, feedback, comment)
    elif choice == "6":
        console.view_behavior_anomalies()
    elif choice == "7":
        from agents.behavioral_analytics import BehavioralAnalytics
        ba = BehavioralAnalytics()
        ba.load_log()
        ba.plot_behavior_trends()
    elif choice == "8":
        from agents.behavioral_analytics import BehavioralAnalytics
        ba = BehavioralAnalytics()
        ba.load_log()
        ba.cluster_behavior()
    elif choice == "9":
        from agents.behavioral_analytics import BehavioralAnalytics
        ba = BehavioralAnalytics()
        ba.load_log()
        anomalies = ba.advanced_anomaly_detection()
        print("IQR Anomalies:", anomalies)
    elif choice == "10":
        agent_file = input("Enter agent file path (e.g., agents/learning_agent.py): ")
        console.evolve_agent_code(agent_file)
    elif choice == "11":
        agent_file = input("Enter agent file path (e.g., agents/learning_agent.py): ")
        console.rollback_agent_code(agent_file)
    elif choice == "12":
        agent_file = input("Enter agent file path (e.g., agents/learning_agent.py): ")
        from agents.genetic_evolver import GeneticEvolver
        evolver = GeneticEvolver(agent_file)
        result = evolver.evolve_advanced()
        print(f"Advanced evolution result for {agent_file}: {result}")
    elif choice == "13":
        console.view_security_audit_log()
    elif choice == "14":
        console.automated_response_to_audit()
    elif choice == "15":
        console.view_upgrade_log()
    elif choice == "16":
        console.run_full_upgrade_cycle()
    else:
        print("Invalid option.")
