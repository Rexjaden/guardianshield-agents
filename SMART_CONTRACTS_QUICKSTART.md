# 🛡️ GuardianShield Smart Contracts - Quick Start Guide

## ✅ Node.js Installation Complete!

Node.js has been successfully installed on your system. Now follow these steps:

## 🚀 Step-by-Step Deployment Guide

### 1. **Restart PowerShell** (Important!)
Close this PowerShell window and open a new one to refresh the PATH environment.

### 2. **Navigate back to project directory**
```powershell
cd "C:\Users\rexxr\Documents\GitHub\guardianshield-agents"
```

### 3. **Install smart contract dependencies**
```powershell
npm install
```

### 4. **Set up your wallet configuration**
```powershell
# Copy the environment template
cp .env.example .env

# Edit .env with your details (use any text editor)
notepad .env
```

**Required .env configuration:**
```bash
# Your wallet private key (get from MetaMask/other wallet)
PRIVATE_KEY=your_private_key_without_0x_prefix

# Get free RPC URL from Infura or Alchemy
SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/YOUR_PROJECT_ID

# Get free API key from Etherscan
ETHERSCAN_API_KEY=your_etherscan_api_key

# Your wallet address to receive initial tokens
INITIAL_SALE_ADDRESS=0xYourWalletAddress
```

### 5. **Test the setup**
```powershell
# Compile contracts
npm run compile

# Run tests
npm run test
```

### 6. **Deploy to Sepolia testnet** (Recommended first)
```powershell
npm run deploy:sepolia
```

### 7. **Deploy to mainnet** (After testing)
```powershell
npm run deploy:mainnet
```

### 8. **Verify contracts**
```powershell
npm run verify:sepolia  # or verify:mainnet
```

## 🔧 Getting Your Configuration Values

### **Private Key** (from MetaMask)
1. Open MetaMask
2. Click account menu → Account Details → Export Private Key
3. Copy the key (remove "0x" prefix when pasting to .env)

### **Infura RPC URL** (Free)
1. Go to [infura.io](https://infura.io)
2. Sign up for free account
3. Create new project
4. Copy the Sepolia endpoint URL

### **Etherscan API Key** (Free)
1. Go to [etherscan.io](https://etherscan.io)
2. Sign up for free account
3. API Keys → Create new key
4. Copy the API key

## 💰 Deployment Costs

| Network | Estimated Cost |
|---------|---------------|
| Sepolia (Testnet) | **FREE** (get test ETH from faucet) |
| Ethereum Mainnet | ~$200-300 (depends on gas) |
| Flare Network | ~$5-10 (very low gas fees) |

## 🆓 Get Test ETH for Sepolia

1. **Sepolia Faucet**: https://sepoliafaucet.com/
2. **Alchemy Faucet**: https://sepoliafaucet.com/
3. **ChainLink Faucet**: https://faucets.chain.link/

## 📋 Your Contract Addresses (After Deployment)

The deployment will create a file `deployments/sepolia-latest.json` with all contract addresses:

- **GuardianToken (GUARD)**: `0x...` (ERC-20 Token)
- **GuardianShieldToken (GST)**: `0x...` (NFT)
- **GuardianStaking**: `0x...` (Staking Contract)
- **GuardianLiquidityPool**: `0x...` (Liquidity)
- **DMER**: `0x...` (AI Agent Registry)
- **EvolutionaryContract**: `0x...` (Self-Improving Contract)

## 🔗 Next Steps After Deployment

1. **Update Frontend**: Add contract addresses to your frontend
2. **Verify on Etherscan**: Contracts will be automatically verified
3. **Set Initial Liquidity**: Add liquidity to the pool
4. **Configure Staking**: Set up reward distribution
5. **Test All Functions**: Mint tokens, stake, create NFTs

## 🆘 Troubleshooting

### "Insufficient funds"
- Ensure your wallet has enough ETH for gas fees
- For testnet: Get free ETH from faucets above

### "Invalid private key"
- Remove "0x" prefix from private key in .env
- Ensure private key is correct (64 characters)

### "RPC URL error"
- Check Infura/Alchemy project ID is correct
- Ensure network endpoint is for Sepolia (not mainnet)

### "Compilation failed"
- Run `npm install` to ensure all dependencies installed
- Check that Node.js version is 16+ (`node --version`)

## 🎉 Ready to Deploy!

Once you've completed steps 1-4 above, your smart contracts will be ready for deployment to either Sepolia testnet or Ethereum mainnet.

**Recommended flow:**
1. Deploy to Sepolia first ✅
2. Test all functions ✅
3. Deploy to mainnet 🚀