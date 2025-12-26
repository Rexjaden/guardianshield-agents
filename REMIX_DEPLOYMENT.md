# GuardianShield Remix Deployment Guide
# Deploy to Sepolia with your funded address: 0x59bb1BD7b4f596c0886c3332fa8d3fF2e3242B87

## 🚀 Quick Deployment Steps:

### 1. Open Remix IDE
- Go to https://remix.ethereum.org
- Connect MetaMask wallet
- Switch to Sepolia network
- Ensure you're using the funded address: 0x59bb1BD7b4f596c0886c3332fa8d3fF2e3242B87

### 2. Upload Contract Files
Upload these files to Remix from your contracts/ folder:
- GuardianToken.sol
- GuardianTreasury.sol  
- GuardianShieldToken.sol
- GuardianStaking.sol
- GuardianLiquidityPool.sol
- DMER.sol
- EvolutionaryUpgradeableContract.sol

### 3. Deployment Order:
1. GuardianToken (no constructor args)
2. GuardianTreasury (constructor: your address)
3. GuardianShieldToken (no constructor args) 
4. GuardianStaking (constructor: GuardianToken address)
5. GuardianLiquidityPool (constructor: GuardianToken address)
6. DMER (no constructor args)
7. EvolutionaryUpgradeableContract (no constructor args)

### 4. After Deployment:
- Save all contract addresses
- Verify contracts on Etherscan
- Update frontend with deployed addresses

## 📋 Constructor Arguments:
- GuardianTreasury: 0x59bb1BD7b4f596c0886c3332fa8d3fF2e3242B87
- GuardianStaking: [GuardianToken address from step 1]
- GuardianLiquidityPool: [GuardianToken address from step 1]

## 💰 Gas Estimates:
- Total deployment cost: ~0.02-0.03 ETH
- Your balance: 0.05 ETH ✅ Sufficient!