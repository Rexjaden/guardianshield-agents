# 🚀 GuardianShield Smart Contract Deployment Guide

## 📋 Prerequisites

Before deploying to blockchain, ensure you have:

1. **✅ Compilation Success** - All contracts compiled successfully
2. **💰 Wallet with ETH** - For gas fees
3. **🔑 Private Key** - For deployment authorization 
4. **🏛️ Treasurer Address** - Multi-sig treasury partner
5. **🔍 Etherscan API Key** - For contract verification

## 🌐 Deployment Networks

### 🧪 **Sepolia Testnet** (Recommended for Testing)
- **Network**: Ethereum Sepolia Testnet
- **Explorer**: https://sepolia.etherscan.io
- **Free ETH**: Get testnet ETH from https://sepoliafaucet.com
- **RPC URL**: https://ethereum-sepolia-rpc.publicnode.com

### 🚀 **Mainnet** (Production)
- **Network**: Ethereum Mainnet
- **Explorer**: https://etherscan.io
- **Cost**: Real ETH required for gas fees (~$50-200 total)
- **RPC URL**: https://ethereum-rpc.publicnode.com

## ⚡ Quick Deployment Commands

### 🧪 Deploy to Sepolia Testnet
```bash
# Deploy all contracts to Sepolia testnet
npm run deploy:sepolia
```

### 🚀 Deploy to Mainnet
```bash
# Deploy all contracts to Ethereum mainnet
npm run deploy:mainnet
```

### 🔄 Compile Only
```bash
# Just compile contracts without deploying
npx hardhat compile
```

## 📊 What Gets Deployed

The deployment script will deploy these contracts in order:

1. **🪙 GuardianToken** (ERC-20) - Main utility token
2. **🏛️ GuardianTreasury** - Multi-signature treasury (2-of-2 approval)
3. **🛡️ GuardianShieldToken** (ERC-721) - NFT for security certificates
4. **💰 GuardianStaking** - Staking rewards system
5. **🌊 GuardianLiquidityPool** - Token liquidity management
6. **📊 DMER** - Decentralized Malicious Entity Registry
7. **🧬 EvolutionaryContract** - Upgradeable contract system
8. **💳 GuardianTokenSale** - Token sale contract

## 🔍 After Deployment

### Your contracts will be viewable at:
- **Sepolia**: `https://sepolia.etherscan.io/address/{CONTRACT_ADDRESS}`
- **Mainnet**: `https://etherscan.io/address/{CONTRACT_ADDRESS}`

### Deployment creates:
- `deployments/{network}-latest.json` - Latest deployment addresses
- `deployments/{network}-{timestamp}.json` - Timestamped backup

## 🛡️ Security Features

### 🏛️ **Multi-Signature Treasury**
- Requires BOTH owner (you) AND treasurer to access funds
- No single point of failure
- All transactions require 2-of-2 approval

### 🔒 **Access Control**
- Only contract owners can mint tokens
- Only authorized users can manage staking
- Pausable contracts for emergency stops

## 🔧 Configuration Required

Before deployment, update `.env` file:

```env
# Your wallet's private key (keep secure!)
PRIVATE_KEY=your_actual_private_key_here

# Treasurer wallet address (someone you trust)
TREASURER_ADDRESS=0x742d35Cc6634C0532925a3b8D4403ddf004ce9Ab

# Etherscan API key for contract verification
ETHERSCAN_API_KEY=your_etherscan_api_key_here

# Network RPC URLs (already configured)
SEPOLIA_RPC_URL=https://ethereum-sepolia-rpc.publicnode.com
MAINNET_RPC_URL=https://ethereum-rpc.publicnode.com
```

## 📈 Expected Gas Costs

### Sepolia Testnet (Free)
- Total Cost: **FREE** (testnet ETH)
- Get testnet ETH from faucet

### Ethereum Mainnet (Production)
- GuardianToken: ~$15-25
- GuardianTreasury: ~$20-30
- GuardianShieldToken: ~$15-25
- Other contracts: ~$10-15 each
- **Total: ~$100-200** (depending on gas prices)

## 🎯 Next Steps After Deployment

1. **✅ Verify Contracts** - Automatic verification on Etherscan
2. **📝 Update Frontend** - Use deployed contract addresses
3. **💰 Fund Treasury** - Send initial ETH to multi-sig treasury
4. **🚀 Launch Token Sale** - Begin public token distribution
5. **📊 Monitor** - Watch transactions on block explorer

## 🆘 Troubleshooting

### Common Issues:
- **Insufficient ETH**: Get more ETH for gas fees
- **Wrong Network**: Check if wallet is on correct network
- **RPC Issues**: Try different RPC URL if slow
- **Compilation Errors**: Run `npx hardhat compile` first

### Support:
- Check `hardhat.config.js` for network configuration
- Review deployment logs in terminal
- Verify contract addresses in `deployments/` folder

## 🔗 Important Links

- **Hardhat Docs**: https://hardhat.org/docs
- **OpenZeppelin**: https://docs.openzeppelin.com
- **Etherscan API**: https://docs.etherscan.io
- **Sepolia Faucet**: https://sepoliafaucet.com

---

## ⚠️ Security Reminders

1. **🔒 Never share your private key**
2. **💾 Backup your deployment files**
3. **🧪 Test on Sepolia before mainnet**
4. **👥 Trust your treasurer choice**
5. **📊 Monitor contracts after deployment**

Ready to deploy? Run `npm run deploy:sepolia` to get started! 🚀