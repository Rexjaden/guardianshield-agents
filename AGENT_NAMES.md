# GuardianShield Agent Names 🛡️

## Agent Identity Mapping

| Original Name | Personalized Name | Specialization | Class Location |
|---------------|-------------------|----------------|----------------|
| `learning_agent` | **Prometheus** 🔥 | Google Cloud Platform & Google Ecosystem Mastery | `agents/learning_agent.py` |
| `external_agent` | **Silva** 🌲 | Ethereum & Blockchain Protocols Expert | `agents/external_agent.py` |
| `behavioral_agent` | **Turlo** 🧠 | Web2/Web3 Technologies & Security Analytics | `agents/behavioral_analytics.py` |
| `blockchain_agent` | **Lirto** ⛓️ | Comprehensive Blockchain & Cryptocurrency Master | `blockchain_mastery_orchestrator.py` |

## Agent Characteristics

### 🔥 **Prometheus** (Learning Agent)
- **Domain**: Google Cloud Platform mastery
- **Personality**: Methodical learner, deep technical analysis
- **Expertise**: GCP services, infrastructure, security, AI/ML
- **Memory Database**: `prometheus_memory.db`

### 🌲 **Silva** (External Agent) 
- **Domain**: Ethereum & blockchain protocols
- **Personality**: External threat hunter, cross-chain intelligence
- **Expertise**: Smart contracts, DeFi, Layer 2, consensus mechanisms
- **Memory Database**: `silva_memory.db`

### 🧠 **Turlo** (Behavioral Agent)
- **Domain**: Web2/Web3 technologies & behavioral analysis
- **Personality**: Pattern recognition specialist, user behavior analyst
- **Expertise**: Frontend/backend frameworks, security patterns, anomaly detection
- **Memory Database**: `turlo_memory.db`

### ⛓️ **Lirto** (Blockchain Agent) 
- **Domain**: Comprehensive blockchain & cryptocurrency mastery
- **Personality**: Token strategist, DeFi architect, exclusive advisor
- **Expertise**: Guard/Shield Token success, tokenomics, institutional adoption
- **Memory Database**: `lirto_memory.db`
- **Special Access**: User-exclusive with authentication required

## Updated File References

### Files Updated with New Agent Names:
- ✅ `blockchain_mastery_orchestrator.py`
- ✅ `agent_learning_orchestrator.py` 
- ✅ `advanced_deep_learning_orchestrator.py`
- ✅ `agents/learning_agent.py`
- ✅ `agents/external_agent.py`
- ✅ `agents/behavioral_analytics.py`

### Memory Storage System:
```python
self.memory_dbs = {
    'prometheus': self._init_memory_db('prometheus'),
    'silva': self._init_memory_db('silva'), 
    'turlo': self._init_memory_db('turlo'),
    'lirto': self._init_memory_db('lirto')
}
```

## Authentication for Lirto (Blockchain Agent)

Lirto has exclusive access controls:
```python
# Authenticate with Lirto
lirto.authenticate_user("primary_user", "guardian_shield_master")
```

## Usage Examples

```python
# Access agents by their new names
prometheus = LearningAgent(name="Prometheus")
silva = ExternalAgent()  # name automatically set to "Silva"
turlo = BehavioralAnalyticsAgent()  # name automatically set to "Turlo"
lirto = BlockchainMasteryAgent()  # name automatically set to "Lirto"
```

---

**Note**: All agent personalities and capabilities remain unchanged - only their names have been personalized for better user interaction and identification. 🚀