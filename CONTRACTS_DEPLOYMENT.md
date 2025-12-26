# GuardianShield Smart Contracts Deployment Guide 🛡️

## 🚀 Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration:
# - PRIVATE_KEY: Your wallet private key (without 0x)
# - SEPOLIA_RPC_URL: Infura/Alchemy RPC URL
# - ETHERSCAN_API_KEY: For contract verification
# - INITIAL_SALE_ADDRESS: Address to receive initial tokens
```

### 3. Test Contracts
```bash
# Compile contracts
npm run compile

# Run tests
npm run test
```

### 4. Deploy to Testnet (Sepolia)
```bash
npm run deploy:sepolia
```

### 5. Deploy to Mainnet
```bash
npm run deploy:mainnet
```

### 6. Verify Contracts
```bash
npm run verify:sepolia  # or verify:mainnet
```

## 📋 Contract Overview

### Core Contracts

1. **GuardianToken (GUARD)** - ERC-20 Token
   - Total Supply: 5 billion tokens
   - Initial Supply: 300 million tokens
   - Staged minting for future releases

2. **GuardianShieldToken (GST)** - ERC-721 NFT
   - Unique serial number system
   - Theft prevention features
   - Metadata support (IPFS/Flare integration ready)

3. **GuardianStaking** - Staking Contract
   - Stake GUARD tokens to earn rewards
   - Configurable reward rate
   - Auto-compounding available

4. **GuardianLiquidityPool** - Liquidity Management
   - Automated liquidity provision
   - Fee collection and distribution
   - Integration with DEX protocols

5. **DMER** - Dynamic Morphing Entity Registry
   - AI agent registration and tracking
   - Evolutionary algorithm support
   - Performance metrics storage

6. **EvolutionaryUpgradeableContract** - Self-Improving Contract
   - Genetic algorithm implementation
   - Autonomous upgradeability
   - Fitness-based selection

## 🌐 Network Configuration

### Supported Networks

- **Ethereum Mainnet** (Chain ID: 1)
- **Sepolia Testnet** (Chain ID: 11155111)
- **Flare Network** (Chain ID: 14)
- **Coston2 Testnet** (Chain ID: 114)
- **Local Hardhat** (Chain ID: 1337)

### RPC Endpoints

```javascript
// Mainnet
https://mainnet.infura.io/v3/YOUR_PROJECT_ID

// Sepolia
https://sepolia.infura.io/v3/YOUR_PROJECT_ID

// Flare
https://flare-api.flare.network/ext/C/rpc

// Coston2 (Flare Testnet)
https://coston2-api.flare.network/ext/C/rpc
```

## 💰 Gas Optimization

The contracts are optimized for gas efficiency:
- Solidity 0.8.20 with optimizer enabled
- Minimal proxy patterns where applicable
- Batch operations for multiple actions
- Efficient storage layouts

## 🔐 Security Features

- OpenZeppelin battle-tested contracts
- Reentrancy protection
- Access control mechanisms
- Emergency pause functionality
- Multi-signature requirement for critical operations

## 📊 Deployment Costs (Estimated)

| Contract | Sepolia Gas | Mainnet Gas (30 gwei) |
|----------|-------------|----------------------|
| GuardianToken | ~1.2M | ~$25-30 |
| GuardianShieldToken | ~2.1M | ~$45-55 |
| GuardianStaking | ~1.5M | ~$30-40 |
| GuardianLiquidityPool | ~1.8M | ~$35-45 |
| DMER | ~1.0M | ~$20-25 |
| EvolutionaryContract | ~2.5M | ~$50-65 |
| **Total** | **~10.1M** | **~$205-260** |

## 🔄 Post-Deployment Steps

### 1. Contract Verification
```bash
npm run verify:sepolia  # Verify on block explorer
```

### 2. Initial Configuration
```bash
node scripts/interact.js  # Setup initial parameters
```

### 3. Frontend Integration
- Update contract addresses in frontend
- Configure Web3 provider settings
- Test all user flows

### 4. Token Distribution
- Set up initial token allocation
- Configure staking rewards
- Initialize liquidity pools

## 🛠️ Development Commands

```bash
# Start local blockchain
npm run node

# Deploy to local network
npm run deploy:localhost

# Run specific tests
npx hardhat test test/GuardianContracts.test.js

# Check contract size
npx hardhat size-contracts

# Generate gas report
REPORT_GAS=true npm test
```

## 📁 Directory Structure

```
contracts/              # Smart contract source files
├── GuardianToken.sol
├── GuardianShieldToken.sol
├── GuardianStaking.sol
├── GuardianLiquidityPool.sol
├── DMER.sol
└── EvolutionaryUpgradeableContract.sol

scripts/                # Deployment and interaction scripts
├── deploy.js           # Main deployment script
├── verify.js           # Contract verification
└── interact.js         # Post-deployment setup

test/                   # Contract tests
└── GuardianContracts.test.js

deployments/            # Deployment artifacts (auto-generated)
├── sepolia-latest.json
├── mainnet-latest.json
└── ...

artifacts/              # Compiled contracts (auto-generated)
cache/                  # Hardhat cache (auto-generated)
```

## 🚨 Important Notes

### Security Checklist
- [ ] Private keys stored securely (never commit to git)
- [ ] RPC URLs configured correctly
- [ ] Contract addresses verified on block explorer
- [ ] Initial token distribution completed
- [ ] Access controls properly configured
- [ ] Emergency procedures documented

### Mainnet Deployment Checklist
- [ ] Test thoroughly on testnet first
- [ ] Have sufficient ETH for gas fees
- [ ] Double-check all constructor parameters
- [ ] Verify contract source code after deployment
- [ ] Monitor first few transactions for issues
- [ ] Update documentation with contract addresses

## 🔗 Useful Links

- [Hardhat Documentation](https://hardhat.org/docs)
- [OpenZeppelin Contracts](https://docs.openzeppelin.com/contracts)
- [Etherscan Contract Verification](https://etherscan.io/verifyContract)
- [Flare Network Documentation](https://docs.flare.network/)

## 🆘 Troubleshooting

### Common Issues

1. **"Insufficient funds for gas"**
   - Ensure wallet has enough ETH for deployment
   - Check current gas prices and adjust accordingly

2. **"Contract verification failed"**
   - Verify constructor arguments match deployment
   - Check Solidity version and optimizer settings

3. **"Transaction underpriced"**
   - Increase gas price in network configuration
   - Wait for network congestion to reduce

4. **"Invalid private key"**
   - Ensure private key is correct (no 0x prefix in .env)
   - Check that private key corresponds to funded address

### Getting Help

- Check the GitHub Issues for known problems
- Join our Discord for community support
- Review Hardhat documentation for framework issues