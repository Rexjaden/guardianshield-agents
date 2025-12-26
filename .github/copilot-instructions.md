# GuardianShield Autonomous Agent System 🛡️

## Overview
This is a self-evolving autonomous agent system for Web3 threat intelligence and security. Agents continuously learn, adapt, and improve their capabilities while maintaining admin oversight. The system integrates with Flare Network's DMER framework for decentralized security.

## Core Architecture

### Agent Orchestration
- **Main Entry Point**: `main.py` → `AutonomousAgentOrchestrator` class
- **Admin Console**: `admin_console.py` → Full monitoring, action reversal, evolution control  
- **API Server**: `api_server.py` → FastAPI with WebSocket support for real-time agent communication

### Agent Types & Patterns
All agents follow autonomous learning patterns with these core components:
- `agents/learning_agent.py` - Base recursive self-improvement with `LearningAgent` class
- `agents/behavioral_analytics.py` - ML-powered pattern recognition 
- `agents/data_ingestion.py` - Multi-source threat intelligence gathering
- `agents/dmer_monitor_agent.py` - DMER registry monitoring and threat hunting
- `agents/external_agent.py` - External API integration with autonomous capabilities
- `agents/flare_integration.py` - Blockchain monitoring and Web3 intelligence

**Key Pattern**: Each agent implements `autonomous_cycle()`, `continuous_learn()`, and performance tracking with `self.performance_window`.

### Data Flow Architecture
1. **Ingestion**: `agents/data_ingestion.py` → Multiple threat intel feeds via `external_monitoring_targets.json`
2. **Analysis**: Behavioral analytics + ML pattern recognition  
3. **Decision**: Autonomous agent consensus with admin oversight via `AdminConsole`
4. **Action**: Logged to `agent_action_log.jsonl` with reversal capabilities
5. **Learning**: Experience stored, parameters auto-adjusted via `recursive_learn_and_improve()`

## Critical Development Workflows

### Agent Development Standard Structure
```python
class MyAgent:
    def __init__(self):
        self.autonomous_decisions = True
        self.learning_rate = 0.01  # Auto-adjusts based on performance
        self.performance_window = []  # Rolling performance metrics
        self.continuous_learning_enabled = True
        
    async def continuous_learn(self, training_data: list):
        # Agent-specific learning implementation with batch processing
        for i in range(0, len(training_data), self.learning_batch_size):
            batch = training_data[i:i + self.learning_batch_size]
            await self._process_training_batch(batch)
        
    def autonomous_cycle(self):
        # Independent decision-making cycle - called by orchestrator
        self.analyze_patterns()
        self.recursive_learn_and_improve()
```

### Testing & Validation Workflows
- **Quick Validation**: `python test_system.py` (dry run validation)
- **Full Test Suite**: `pytest tests/` (comprehensive agent testing)
- **Agent Training Data**: Each agent has `generate_*_training_data()` methods for synthetic data

### Deployment Patterns
- **Docker**: Multi-service with `docker-compose.yml` (API, agents, DB, Redis, PostgreSQL)
- **Environment**: Copy `.env.example` → `.env` with your configuration (151 environment variables)
- **Smart Contracts**: Deploy via `npm run deploy:sepolia` or `deploy:mainnet` (8 contracts including DMER.sol)
- **Local Development**: `docker-compose up` for full stack or `python main.py` for agent-only mode

## Web3 & Blockchain Integration

### Smart Contracts (`contracts/`)
- `DMER.sol` - Decentralized threat registry
- `GuardianShieldToken.sol` - Native token with staking
- `EvolutionaryUpgradeableContract.sol` - Agent consensus upgrades
- `GuardianTreasury.sol`, `GuardianLiquidityPool.sol` - DeFi components

### Flare Network Integration
- Real-time blockchain monitoring via `agents/flare_integration.py`
- DMER registry sync through `agents/dmer_monitor_agent.py`
- Multi-chain security hub in `agents/multichain_security_hub.py`

## Autonomous Learning System

### Key Characteristics
- **Self-Evolution**: Agents modify their own parameters based on success/failure rates
- **Recursive Improvement**: `recursive_learn_and_improve()` continuously adjusts learning rates
- **Experience Storage**: All decisions logged with outcomes for pattern analysis
- **Performance Windows**: Rolling performance tracking with automatic parameter adjustment

### Admin Oversight
```python
# All autonomous decisions are logged and reversible
console = AdminConsole()
console.revert_agent_action(action_id)  # Undo any agent decision
console.pause_agent_evolution()         # Stop autonomous improvements
console.get_agent_performance()         # Real-time monitoring
```

## Project-Specific Conventions

### Logging Pattern
All agents use structured JSONL logging:
- `agent_action_log.jsonl` - Every agent decision
- `agent_evolution_log.jsonl` - Self-improvement events  
- `agent_decision_log.jsonl` - Decision reasoning

### Error Handling Philosophy
Agents never halt on ML/learning errors - they degrade gracefully and continue operating with reduced capabilities.

### Performance Tracking
```python
# Standard pattern across all agents
self.performance_window = []  # Rolling performance metrics
self.learning_rate = 0.01     # Auto-adjusts based on success_ratio()
```

## Integration Points

### External APIs & Services
- **Threat Intel**: 10+ feeds via `external_monitoring_targets.json`
- **Email Integration**: `email_integration.py` for notifications
- **Payment Gateway**: `crypto_payment_gateway.py` for token purchases

### Cross-Agent Communication
Agents collaborate through shared databases:
- `threat_intelligence.db` - Threat patterns and intelligence
- `analytics.db` - Behavioral analysis data
- `security_orchestration.db` - Cross-agent coordination

## Quick Start Commands
```bash
# Setup environment
python setup_environment.py

# Run system tests  
python test_system.py

# Start agent orchestrator
python main.py

# Launch admin dashboard
python analytics_dashboard.py

# Deploy contracts (testnet)
npm run deploy:sepolia
```