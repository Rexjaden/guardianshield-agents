# GuardianShield Autonomous Agent System 🛡️

## Overview

GuardianShield is an advanced autonomous agent system designed for unlimited self-evolution, recursive improvement, and real-time threat intelligence. The system features truly autonomous agents capable of independent decision-making, learning, and evolution while maintaining comprehensive admin oversight and action reversal capabilities.

Built in collaboration with Flare Network, these agents power the DMER (Decentralized Modular Enforcement and Response) framework for decentralized security across Web3 ecosystems.

## 🚀 Key Features

### Unlimited Autonomous Evolution
- **Recursive Self-Improvement**: Agents continuously enhance their own capabilities
- **Autonomous Decision Making**: Independent threat assessment and response
- **Cross-Agent Collaboration**: Coordinated intelligence sharing and action
- **Pattern Discovery**: Automatic identification of new threat patterns
- **Unlimited Learning**: No caps on knowledge acquisition or skill development

### Admin Oversight & Control
- **Real-time Monitoring**: Live dashboard of all agent activities
- **Action Reversal**: Ability to reverse any autonomous agent action
- **Evolution Control**: Monitor and revert agent evolution decisions
- **Emergency Stop**: Immediate halt of all autonomous operations
- **Granular Autonomy Control**: Adjustable autonomy levels (1-10 scale)

### Advanced Threat Intelligence
- **Multi-source Integration**: 10+ threat intelligence feeds
- **Autonomous Threat Hunting**: Proactive threat discovery
- **Blockchain Integration**: Web3 and Flare network monitoring
- **Behavioral Analytics**: ML-powered anomaly detection
- **Spam Site Detection**: Advanced URL and domain analysis

## 🤖 Agent Architecture

### Core Agents
1. **LearningAgent**: Unlimited recursive self-improvement and learning
2. **ThreatDefinitions**: Autonomous threat intelligence evolution
3. **BehavioralAnalytics**: ML-based pattern recognition and anomaly detection
4. **DataIngestionAgent**: Multi-source threat intelligence gathering
5. **DmerMonitorAgent**: DMER registry monitoring and threat hunting
6. **FlareIntegrationAgent**: Blockchain monitoring and Web3 intelligence
7. **ExternalAgent**: API integration and external system coordination
8. **GeneticEvolver**: Code evolution and optimization algorithms

### Agent Capabilities
- **Autonomous Operation**: Independent decision-making cycles
- **Self-Evolution**: Continuous capability enhancement
- **Threat Learning**: Real-time threat pattern discovery
- **Cross-Collaboration**: Inter-agent intelligence sharing
- **Admin Compliance**: Full action logging and reversibility

## 📦 Installation & Setup

### ⚠️ Security Notice

**IMPORTANT**: This system implements multiple layers of security to protect sensitive operations and credentials.

**Security Features:**
- **Admin Credential Protection**: Master admin credentials are stored locally and excluded from version control
- **Rate Limiting**: API endpoints protected against abuse (100 requests/minute per IP)
- **Authentication**: JWT-based token authentication with session management
- **Input Validation**: All user inputs sanitized to prevent injection attacks
- **Security Headers**: HTTP security headers to prevent XSS, clickjacking, and other attacks
- **CORS Protection**: Strict origin validation for cross-origin requests
- **Encrypted Storage**: Sensitive configuration data encrypted at rest

**Files excluded from version control:**
- `.guardian_master_password.txt` - Master admin password (auto-generated on first run)
- `.guardian_secret` - JWT secret key (auto-generated on first run)
- `.guardian_admin` - Admin authentication hash (auto-generated on first run)

**Note**: Database files (*.db) and log files (*.jsonl) are tracked for operational continuity but should be secured in production deployments.

### Quick Start
```bash
# Clone the repository
git clone https://github.com/Rexjaden/guardianshield-agents.git
cd guardianshield-agents

# Install dependencies (optional but recommended)
pip install -r requirements.txt

# Configure environment (optional)
cp .env.example .env
# Edit .env with your settings

# Run system tests
python test_system.py

# Start the system (will auto-generate security files on first run)
python start_guardianshield.py
```

**First-time security setup:**
1. On first run, the system auto-generates secure keys and credentials
2. Save your master admin password from `.guardian_master_password.txt`
3. Store the password securely, then delete or secure the file
4. The concealed credential files will be created in your local directory
5. These files are excluded from git tracking for security

**API Security Best Practices:**
- Always use HTTPS in production (configure reverse proxy with SSL/TLS)
- Regularly rotate authentication tokens and secrets
- Monitor rate limiting logs for potential abuse
- Keep JWT secret keys secure and never commit to version control
- Use strong passwords (minimum 12 characters) for all admin accounts
- Enable MFA for production deployments when available

### Minimal Requirements
The system is designed to work even without external dependencies:
- **Python 3.7+** (only hard requirement)
- All external libraries have fallback implementations
- Core functionality works without any additional packages

### Optional Dependencies
For enhanced features, install:
```bash
pip install cryptography python-dotenv requests web3 scikit-learn
```

## 🎮 Usage

### Starting the System
```bash
# Interactive startup menu
python start_guardianshield.py

# Direct autonomous system start
python main.py

# Admin console only
python admin_console.py
```

### Admin Console Features
- **Real-time Monitoring**: View live agent activities
- **Action Management**: Approve, deny, or revert agent actions
- **Evolution Control**: Monitor and manage agent evolution
- **Autonomy Settings**: Adjust agent independence levels
- **Emergency Controls**: Stop/resume all operations

### Monitoring Autonomous Operations
```python
from admin_console import AdminConsole

console = AdminConsole()

# View real-time activity
console.view_real_time_monitoring(last_minutes=30)

# Check agent performance
console.view_agent_autonomy_stats()

# Revert an action
console.revert_action("action_id_here", reason="Admin override")
```

## 🔧 Configuration

### Autonomy Levels
- **Level 1-3**: High oversight, most actions require approval
- **Level 4-6**: Balanced autonomy with critical action review
- **Level 7-9**: High autonomy, minimal oversight
- **Level 10**: Full autonomy, unlimited evolution

### Environment Variables
Key configuration options in `.env`:
```bash
# Core settings
AGENT_AUTONOMY_LEVEL=10
AUTO_EVOLUTION_ENABLED=true
UNLIMITED_IMPROVEMENT=true

# Security
GUARDIAN_PASSWORD=your_secure_password
ENCRYPTION_PASSWORD=your_encryption_key

# Monitoring
CRITICAL_ACTION_THRESHOLD=8
MONITORING_INTERVAL=30
```

## 🛡️ Security Features

### Data Protection
- **Encryption**: All sensitive data encrypted at rest
- **Secure Storage**: Protected configuration and logs
- **Access Control**: Admin-only system controls
- **Audit Trails**: Complete action logging

### Safe Evolution
- **Reversible Actions**: All agent modifications can be undone
- **Backup Systems**: Automatic evolution backups
- **Validation**: Agent evolution safety checks
- **Emergency Stops**: Immediate intervention capability

## 📊 Monitoring & Analytics

### Real-time Dashboards
- Agent activity monitoring
- Evolution progress tracking
- Threat intelligence feeds
- Performance metrics

### Logging Systems
- **Action Logs**: All agent activities
- **Evolution Logs**: Agent improvement history
- **Decision Logs**: Autonomous reasoning chains
- **Performance Logs**: System metrics

### Alert Systems
- High-severity action alerts
- Evolution milestone notifications
- Threat detection alerts
- System health monitoring

## 🧬 Evolution Capabilities

### Autonomous Learning
- Pattern recognition improvement
- Algorithm optimization
- Capability enhancement
- Decision logic refinement

### Cross-Agent Evolution
- Knowledge sharing between agents
- Collaborative improvement
- Skill transfer mechanisms
- Collective intelligence growth

### Unlimited Growth
- No artificial caps on learning
- Continuous capability expansion
- Adaptive threat response
- Self-optimizing performance

## 🚨 Emergency Procedures

### Emergency Stop
```python
from admin_console import AdminConsole
console = AdminConsole()
console.emergency_stop_all_agents()
```

### Action Reversal
```python
# Revert specific action
console.revert_action("action_id", "Reason for reversal")

# Revert evolution
console.revert_evolution("evolution_id", "Admin override")
```

### System Recovery
1. Emergency stop all agents
2. Review action logs
3. Revert problematic actions
4. Adjust autonomy levels
5. Resume operations

## 🔮 Future Enhancements

### Planned Features
- Web-based admin dashboard
- Advanced ML model integration
- Multi-chain blockchain support
- Enhanced visualization tools
- API endpoints for external integration

### Research Areas
- Quantum-resistant security
- Advanced AI reasoning
- Predictive threat modeling
- Autonomous negotiation protocols

## 🤝 Contributing

### Development Guidelines
- All agent modifications must be reversible
- Maintain backward compatibility
- Include comprehensive logging
- Follow security best practices

### Testing
```bash
# Run full test suite
python test_system.py

# Test specific components
python -m pytest tests/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues, questions, or contributions:
- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Check inline code documentation
- **Admin Console**: Use built-in monitoring tools

## ⚠️ Disclaimer

GuardianShield agents are autonomous systems capable of independent decision-making. While comprehensive oversight and reversal capabilities are provided, users are responsible for:
- Proper configuration and monitoring
- Understanding system capabilities
- Maintaining appropriate security measures
- Regular review of autonomous actions

Use responsibly and maintain appropriate oversight of autonomous operations.
