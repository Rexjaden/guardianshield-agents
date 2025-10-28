# ERC-8055 Testnet Testing Guide

## 🎯 Overview

This testnet testing suite validates the complete ERC-8055 security token functionality including:
- Serial-numbered token minting and tracking
- Agent-monitored theft/fraud detection  
- Burn events with serial preservation
- Reminting to treasury with intact serials
- Ownership verification through agent/wallet logs
- Multi-signature recovery workflows

## 🚀 Quick Start

### 1. Setup Environment
```bash
cd testnet
pip install -r requirements.txt
```

### 2. Configure Testnet Access
Edit `deploy.py` and add your:
- Infura API key
- Testnet private keys
- Treasury wallet address

### 3. Run Complete Test Suite
```bash
python run_tests.py
```

## 📋 Test Scenarios

### Scenario 1: Normal Minting
- **Purpose**: Verify serial numbering and batch assignment
- **Tests**: Token creation with unique serials (GS-8055-XXXXXX)
- **Expected**: 100% success rate, consistent execution times

### Scenario 2: Theft Detection & Burn
- **Purpose**: Test agent detection of suspicious patterns
- **Tests**: Rapid transfers, transfers to known bad addresses
- **Expected**: Auto-burn within 2-5 seconds of detection

### Scenario 3: Remint to Treasury
- **Purpose**: Verify serial preservation during remint
- **Tests**: Burned tokens reminted with original serials intact
- **Expected**: 100% serial preservation rate

### Scenario 4: Ownership Verification
- **Purpose**: Test verification through agent/wallet logs
- **Tests**: Cross-reference mint records with wallet history
- **Expected**: Accurate verification of original ownership

### Scenario 5: Ownership Recovery
- **Purpose**: Test complete recovery workflow
- **Tests**: Multi-sig approval and token return to verified owner
- **Expected**: Successful recovery with admin approval

## 🔍 Test Analysis

### Consistency Metrics
- **Success Rate**: Percentage of successful test executions
- **Execution Time Variance**: Standard deviation of response times
- **Agent Response Time**: Speed of threat detection and response
- **Serial Preservation**: Rate of serial number integrity maintenance

### Stability Criteria
- ✅ **Success Consistency**: All iterations pass or fail consistently
- ✅ **Time Stability**: Execution time variance < 1.0 second
- ✅ **Serial Integrity**: 100% serial preservation rate
- ✅ **Agent Reliability**: Response time variance < 0.5 seconds

## 📊 Expected Results

### Performance Benchmarks
- **Minting**: ~0.1-0.3s per token
- **Theft Detection**: ~1-3s response time
- **Burn Execution**: ~2-5s completion
- **Ownership Verification**: ~0.5-1s lookup time
- **Recovery Process**: ~10-30s with multi-sig

### Success Thresholds
- **Normal Operations**: 100% success rate
- **Security Events**: 95%+ detection accuracy
- **Recovery Operations**: 98%+ success rate
- **Serial Preservation**: 100% integrity

## 🛠️ Manual Testing

### Deploy Contract Only
```bash
python deploy.py
```

### Start Monitoring Agents
```bash
python monitoring_agents.py
```

### Run Specific Scenarios
```bash
python test_scenarios.py
```

## 📁 Output Files

- `deployment_sepolia.json`: Contract deployment details
- `agent_XXX_logs.jsonl`: Agent event logs (tamper-proof)
- `test_results.json`: Detailed test execution results
- `testnet_report_YYYYMMDD_HHMMSS.json`: Comprehensive analysis
- `testnet_agent.log`: Agent monitoring logs

## 🔧 Configuration

### Testnet Settings
- **Network**: Sepolia (recommended for testing)
- **Batch Size**: 300,000,000 tokens per batch
- **Agent Assignment**: 1 agent per batch
- **Treasury**: Configurable address for reminted tokens

### Security Parameters
- **Detection Threshold**: 0.8 confidence for auto-burn
- **Multi-sig Requirement**: 2 of 3 admin signatures
- **Agent Response Target**: <3 seconds
- **Log Anchoring**: On-chain hash storage

## 🚨 Troubleshooting

### Common Issues
1. **Deployment Fails**: Check Infura key and account balance
2. **Agent Timeout**: Verify RPC connection and contract address
3. **Test Inconsistency**: Review gas prices and network congestion
4. **Serial Mismatch**: Validate remint logic and storage

### Debug Mode
Add debug logging:
```python
logging.getLogger().setLevel(logging.DEBUG)
```

## ✅ Success Criteria

Before mainnet deployment, ensure:
- [ ] All 5 scenarios pass consistently across 5+ iterations
- [ ] Agent response times under 3 seconds
- [ ] 100% serial number preservation
- [ ] Zero false positive burns
- [ ] Complete ownership recovery workflow

## 📞 Support

For issues or questions:
- Repository: [guardianshield-agents](https://github.com/Rexjaden/guardianshield-agents)
- Branch: `erc-8055-clean`
- Contact: rex@guardiannshield.io