"""
admin_console.py: Administrative monitoring and control console for autonomous GuardianShield agents.
Provides oversight, monitoring, and reversal capabilities for self-evolving agents.
"""
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOG_FILE = "agent_action_log.jsonl"
EVOLUTION_LOG_FILE = "agent_evolution_log.jsonl"
DECISION_LOG_FILE = "agent_decision_log.jsonl"

class AdminConsole:
    """Administrative console for monitoring and controlling autonomous agents"""
    
    def __init__(self, log_file=LOG_FILE):
        self.log_file = log_file
        self.evolution_log_file = EVOLUTION_LOG_FILE
        self.decision_log_file = DECISION_LOG_FILE
        self.initialize_log_files()
        
        # Admin control settings
        self.monitoring_active = True
        self.auto_approval_enabled = False
        self.critical_action_threshold = 8  # Actions above this severity require admin approval
        self.agent_autonomy_level = 10  # 1-10 scale, 10 = full autonomy
        
        # Agent state tracking
        self.agent_states = {}
        self.pending_reversals = {}
        self.blocked_actions = {}

    def initialize_log_files(self):
        """Initialize log files if they don't exist"""
        for log_file in [self.log_file, self.evolution_log_file, self.decision_log_file]:
            if not os.path.exists(log_file):
                with open(log_file, 'w') as f:
                    pass

    def log_action(self, agent: str, action: str, details: Dict, severity: int = 5):
        """Log agent action with enhanced metadata for monitoring"""
        action_id = f"{agent}_{int(time.time())}_{hash(str(details)) % 10000}"
        
        entry = {
            "action_id": action_id,
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent,
            "action": action,
            "details": details,
            "severity": severity,
            "reversible": details.get("reversible", True),
            "auto_approved": severity < self.critical_action_threshold,
            "admin_reviewed": False,
            "status": "executed" if severity < self.critical_action_threshold else "pending_review"
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")
            
        # Log for real-time monitoring
        logger.info(f"[{agent}] Action logged: {action} (Severity: {severity}, ID: {action_id})")
        
        # Alert if high severity
        if severity >= self.critical_action_threshold:
            self.alert_high_severity_action(entry)
        
        return action_id

    def log_evolution_decision(self, agent: str, evolution_type: str, details: Dict):
        """Log autonomous evolution decisions made by agents"""
        evolution_id = f"evolution_{agent}_{int(time.time())}"
        
        entry = {
            "evolution_id": evolution_id,
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent,
            "evolution_type": evolution_type,
            "details": details,
            "reversible": True,
            "performance_impact": details.get("performance_impact", "unknown"),
            "confidence": details.get("confidence", 0.5)
        }
        
        with open(self.evolution_log_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")
            
        logger.info(f"[{agent}] Evolution logged: {evolution_type} (ID: {evolution_id})")

    def log_autonomous_decision(self, agent: str, decision_type: str, reasoning: Dict, outcome: Dict):
        """Log autonomous decisions made by agents with full reasoning chain"""
        decision_id = f"decision_{agent}_{int(time.time())}_{hash(str(reasoning)) % 1000}"
        
        entry = {
            "decision_id": decision_id,
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent,
            "decision_type": decision_type,
            "reasoning": reasoning,
            "outcome": outcome,
            "confidence_level": reasoning.get("confidence", 0.5),
            "factors_considered": reasoning.get("factors", []),
            "alternative_options": reasoning.get("alternatives", []),
            "risk_assessment": reasoning.get("risk_level", "medium"),
            "reversible": outcome.get("reversible", True)
        }
        
        with open(self.decision_log_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")
            
        logger.info(f"[{agent}] Decision logged: {decision_type} (Confidence: {reasoning.get('confidence', 'N/A')})")

    def alert_high_severity_action(self, entry: Dict):
        """Alert admin of high-severity actions requiring attention"""
        print(f"\n🚨 HIGH SEVERITY ALERT 🚨")
        print(f"Agent: {entry['agent']}")
        print(f"Action: {entry['action']}")
        print(f"Severity: {entry['severity']}/10")
        print(f"Action ID: {entry['action_id']}")
        print(f"Time: {entry['timestamp']}")
        print(f"Details: {json.dumps(entry['details'], indent=2)}")
        print(f"Status: {entry['status']}")
        print("=" * 50)

    def view_real_time_monitoring(self, last_minutes: int = 30):
        """Real-time monitoring dashboard for agent activities"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=last_minutes)
        
        print(f"\n🖥️  REAL-TIME AGENT MONITORING (Last {last_minutes} minutes)")
        print("=" * 60)
        
        # Recent actions
        recent_actions = self.get_recent_entries(self.log_file, cutoff_time)
        if recent_actions:
            print(f"\n📋 RECENT ACTIONS ({len(recent_actions)} total):")
            for action in recent_actions[-10:]:  # Show last 10
                severity_indicator = "🔴" if action['severity'] >= 8 else "🟡" if action['severity'] >= 5 else "🟢"
                print(f"{severity_indicator} [{action['timestamp'][-8:]}] {action['agent']}: {action['action']}")
        
        # Recent evolutions
        recent_evolutions = self.get_recent_entries(self.evolution_log_file, cutoff_time)
        if recent_evolutions:
            print(f"\n🧬 AUTONOMOUS EVOLUTIONS ({len(recent_evolutions)} total):")
            for evolution in recent_evolutions[-5:]:
                print(f"🔄 [{evolution['timestamp'][-8:]}] {evolution['agent']}: {evolution['evolution_type']}")
        
        # Recent decisions
        recent_decisions = self.get_recent_entries(self.decision_log_file, cutoff_time)
        if recent_decisions:
            print(f"\n🧠 AUTONOMOUS DECISIONS ({len(recent_decisions)} total):")
            for decision in recent_decisions[-5:]:
                confidence = decision.get('confidence_level', 'N/A')
                risk = decision.get('risk_assessment', 'unknown')
                print(f"💭 [{decision['timestamp'][-8:]}] {decision['agent']}: {decision['decision_type']} (Confidence: {confidence}, Risk: {risk})")

    def get_recent_entries(self, log_file: str, cutoff_time: datetime) -> List[Dict]:
        """Get recent entries from log file"""
        recent_entries = []
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    entry = json.loads(line.strip())
                    entry_time = datetime.fromisoformat(entry['timestamp'])
                    if entry_time > cutoff_time:
                        recent_entries.append(entry)
        except Exception as e:
            logger.error(f"Error reading {log_file}: {e}")
        
        return recent_entries

    def view_agent_autonomy_stats(self):
        """View comprehensive agent autonomy and performance statistics"""
        print("\n🤖 AGENT AUTONOMY STATISTICS")
        print("=" * 50)
        
        # Analyze actions by agent
        agent_stats = {}
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    entry = json.loads(line.strip())
                    agent = entry['agent']
                    if agent not in agent_stats:
                        agent_stats[agent] = {
                            "total_actions": 0,
                            "high_severity_actions": 0,
                            "autonomous_actions": 0,
                            "avg_severity": 0,
                            "severities": []
                        }
                    
                    agent_stats[agent]["total_actions"] += 1
                    agent_stats[agent]["severities"].append(entry['severity'])
                    
                    if entry['severity'] >= self.critical_action_threshold:
                        agent_stats[agent]["high_severity_actions"] += 1
                    
                    if entry.get('auto_approved', False):
                        agent_stats[agent]["autonomous_actions"] += 1
            
            # Calculate averages and display
            for agent, stats in agent_stats.items():
                if stats["severities"]:
                    stats["avg_severity"] = sum(stats["severities"]) / len(stats["severities"])
                    autonomy_rate = (stats["autonomous_actions"] / stats["total_actions"]) * 100
                    
                    print(f"\n🤖 {agent}:")
                    print(f"   Total Actions: {stats['total_actions']}")
                    print(f"   Autonomous Actions: {stats['autonomous_actions']} ({autonomy_rate:.1f}%)")
                    print(f"   High Severity Actions: {stats['high_severity_actions']}")
                    print(f"   Average Severity: {stats['avg_severity']:.2f}/10")
                    
        except Exception as e:
            logger.error(f"Error analyzing agent stats: {e}")

    def revert_action(self, action_id: str, reason: str = "Admin override") -> bool:
        """Revert a specific agent action"""
        try:
            # Find the action
            action_entry = None
            with open(self.log_file, 'r') as f:
                for line in f:
                    entry = json.loads(line.strip())
                    if entry.get('action_id') == action_id:
                        action_entry = entry
                        break
            
            if not action_entry:
                print(f"❌ Action {action_id} not found")
                return False
            
            if not action_entry.get('reversible', True):
                print(f"❌ Action {action_id} is not reversible")
                return False
            
            # Execute reversal based on action type
            success = self._execute_reversal(action_entry)
            
            if success:
                # Log the reversal
                reversal_entry = {
                    "action_id": f"reversal_{action_id}_{int(time.time())}",
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent": "ADMIN",
                    "action": "revert_action",
                    "details": {
                        "reverted_action_id": action_id,
                        "reason": reason,
                        "original_action": action_entry['action'],
                        "original_agent": action_entry['agent']
                    },
                    "severity": 9,
                    "reversible": False
                }
                
                with open(self.log_file, 'a') as f:
                    f.write(json.dumps(reversal_entry) + "\n")
                
                print(f"✅ Successfully reverted action {action_id}")
                print(f"   Original action: {action_entry['action']} by {action_entry['agent']}")
                print(f"   Reason: {reason}")
                return True
            else:
                print(f"❌ Failed to revert action {action_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error reverting action {action_id}: {e}")
            return False

    def _execute_reversal(self, action_entry: Dict) -> bool:
        """Execute the actual reversal of an action"""
        action_type = action_entry['action']
        agent_name = action_entry['agent']
        details = action_entry['details']
        
        try:
            # Import and instantiate the agent that performed the action
            if agent_name == "LearningAgent":
                from agents.learning_agent import LearningAgent
                agent = LearningAgent()
            elif agent_name == "GeneticEvolver":
                from agents.genetic_evolver import GeneticEvolver
                agent = GeneticEvolver()
            elif agent_name == "threat_definitions_agent":
                from agents.threat_definitions import evolving_threats
                if action_type == "learn_new_threat":
                    evolution_hash = details.get("hash")
                    return evolving_threats.revert_evolution(evolution_hash)
            
            # Add more agent-specific reversal logic here
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing reversal: {e}")
            return False

    def emergency_stop_all_agents(self):
        """Emergency stop for all autonomous agent activities"""
        print("🛑 EMERGENCY STOP ACTIVATED")
        print("   All autonomous agent activities halted")
        print("   Manual intervention required to resume")
        
        emergency_entry = {
            "action_id": f"emergency_stop_{int(time.time())}",
            "timestamp": datetime.utcnow().isoformat(),
            "agent": "ADMIN",
            "action": "emergency_stop",
            "details": {"reason": "Admin emergency stop"},
            "severity": 10,
            "reversible": True
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(emergency_entry) + "\n")
        
        # Create emergency stop file that agents check
        with open("emergency_stop.flag", "w") as f:
            f.write(json.dumps(emergency_entry))

    def resume_agent_operations(self):
        """Resume agent operations after emergency stop"""
        try:
            if os.path.exists("emergency_stop.flag"):
                os.remove("emergency_stop.flag")
                
            print("✅ Agent operations resumed")
            print("   All agents can now operate autonomously")
            
            resume_entry = {
                "action_id": f"resume_operations_{int(time.time())}",
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "ADMIN",
                "action": "resume_operations",
                "details": {"reason": "Admin resumed operations"},
                "severity": 7,
                "reversible": True
            }
            
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(resume_entry) + "\n")
                
        except Exception as e:
            logger.error(f"Error resuming operations: {e}")

    def set_agent_autonomy_level(self, level: int):
        """Set overall agent autonomy level (1-10 scale)"""
        if 1 <= level <= 10:
            self.agent_autonomy_level = level
            self.critical_action_threshold = 11 - level  # Higher autonomy = higher threshold
            
            print(f"🎛️  Agent autonomy set to level {level}/10")
            print(f"   Critical action threshold: {self.critical_action_threshold}/10")
        else:
            print("❌ Autonomy level must be between 1 and 10")

    def view_pending_actions(self):
        """View actions pending admin approval"""
        print("\n⏳ ACTIONS PENDING APPROVAL")
        print("=" * 40)
        
        pending_count = 0
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    entry = json.loads(line.strip())
                    if entry.get('status') == 'pending_review':
                        pending_count += 1
                        print(f"\n🔍 Action ID: {entry['action_id']}")
                        print(f"   Agent: {entry['agent']}")
                        print(f"   Action: {entry['action']}")
                        print(f"   Severity: {entry['severity']}/10")
                        print(f"   Time: {entry['timestamp']}")
                        print(f"   Details: {json.dumps(entry['details'], indent=4)}")
        
            if pending_count == 0:
                print("No actions pending approval")
                
        except Exception as e:
            logger.error(f"Error viewing pending actions: {e}")

    # Legacy methods for backward compatibility
    def view_log(self, limit=20):
        """View recent agent actions (legacy method)"""
        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()[-limit:]
                for line in lines:
                    entry = json.loads(line)
                    print(f"[{entry['timestamp']}] {entry['agent']} - {entry['action']}: {entry['details']}")
        except Exception as e:
            logger.error(f"Error viewing log: {e}")

    def provide_feedback(self, action_id, feedback, comment=None):
        """Provide feedback on agent actions (legacy method)"""
        feedback_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action_id": action_id,
            "feedback": feedback,
            "comment": comment
        }
        with open("agent_feedback_log.jsonl", 'a') as f:
            f.write(json.dumps(feedback_entry) + "\n")
        print(f"Feedback recorded for action {action_id}.")

# Enhanced menu system
if __name__ == "__main__":
    console = AdminConsole()
    
    while True:
        print("\n" + "="*60)
        print("🛡️  GUARDIANSHIELD ADMIN CONTROL CONSOLE")
        print("="*60)
        print("📊 MONITORING & OVERSIGHT:")
        print("1.  Real-time agent monitoring")
        print("2.  View agent autonomy statistics")
        print("3.  View pending actions")
        print("4.  View recent actions log")
        print("")
        print("🔄 CONTROL & INTERVENTION:")
        print("5.  Revert specific action")
        print("6.  Set agent autonomy level")
        print("7.  Emergency stop all agents")
        print("8.  Resume agent operations")
        print("")
        print("✅ ACTION MANAGEMENT:")
        print("9.  Provide feedback on action")
        print("")
        print("0.  Exit console")
        print("="*60)
        
        choice = input("Select option: ").strip()
        
        if choice == "1":
            minutes = input("Enter monitoring window (minutes, default 30): ") or "30"
            console.view_real_time_monitoring(int(minutes))
            
        elif choice == "2":
            console.view_agent_autonomy_stats()
            
        elif choice == "3":
            console.view_pending_actions()
            
        elif choice == "4":
            limit = input("Enter number of entries (default 20): ") or "20"
            console.view_log(int(limit))
            
        elif choice == "5":
            action_id = input("Enter action ID to revert: ")
            reason = input("Enter reason for reversal: ") or "Admin override"
            console.revert_action(action_id, reason)
            
        elif choice == "6":
            level = input("Enter autonomy level (1-10): ")
            try:
                console.set_agent_autonomy_level(int(level))
            except ValueError:
                print("❌ Please enter a valid number between 1 and 10")
                
        elif choice == "7":
            confirm = input("⚠️  Confirm emergency stop? (yes/no): ").lower()
            if confirm == "yes":
                console.emergency_stop_all_agents()
                
        elif choice == "8":
            confirm = input("Resume agent operations? (yes/no): ").lower()
            if confirm == "yes":
                console.resume_agent_operations()
                
        elif choice == "9":
            action_id = input("Enter action ID: ")
            feedback = input("Enter feedback (approve/reject/correct): ")
            comment = input("Optional comment: ")
            console.provide_feedback(action_id, feedback, comment)
            
        elif choice == "0":
            print("👋 Exiting GuardianShield Admin Console")
            break
            
        else:
            print("❌ Invalid option. Please try again.")
        
        input("\nPress Enter to continue...")