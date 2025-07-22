"""
main.py: Entry point to run both internal and external AI agents simultaneously.
"""

from agents.learning_agent import Sentinel
from agents.external_agent import Mediator
from agents.dmer_monitor_agent import DMERMonitorAgent
from agents.utils import log_event


def main():
    # Initialize agents
    sentinel = Sentinel(name="Sentinel")
    mediator = Mediator(name="Mediator")
    dmer_agent = DMERMonitorAgent(name="DMERMonitorAgent")

    # Example: Simulate both agents working simultaneously
    log_event("Starting GuardianShield agents...")

    # Simulate internal agent task
    sentinel.learn({"example": "internal data"})
    sentinel.act("internal observation")

    # Simulate external agent task
    mediator.process_external_task({"example": "external data"})
    mediator.act("external observation")

    # Simulate DMER monitoring
    dmer_agent.monitor({"dmer": "sample data"})
    dmer_agent.report()

    # Simulate real-time communication for threat detection
    threat_message = "Potential fraud detected on chain X."
    mediator.communicate(threat_message, sentinel)
    sentinel.communicate("Spam site identified on chain Y.", mediator)

    # Test: Sentinel scans contracts and alerts Mediator
    contract_paths = [
        "contracts/GuardianToken.sol",
        "contracts/GuardianShieldToken.sol",
        "contracts/GuardianStaking.sol",
        "contracts/GuardianLiquidityPool.sol"
    ]
    sentinel.scan_contracts(contract_paths, alert_agent=mediator)

    # Test: Mediator monitors platform logs and alerts Sentinel
    activity_logs = [
        "User 0x1234 performed a transfer.",
        "Address poisoning attempt detected in transaction.",
        "Potential fraud in staking contract.",
        "Normal platform activity."
    ]
    mediator.monitor_platform(activity_logs, alert_agent=sentinel)

    log_event("All agents completed their tasks.")


if __name__ == "__main__":
    main()
