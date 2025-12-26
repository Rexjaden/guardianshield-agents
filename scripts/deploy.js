const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  console.log("🛡️ GuardianShield Smart Contract Deployment Starting...");
  console.log("=".repeat(60));

  // Get deployment parameters
  const [deployer] = await ethers.getSigners();
  const network = await ethers.provider.getNetwork();
  
  console.log(`Deploying to network: ${network.name} (Chain ID: ${network.chainId})`);
  console.log(`Deployer address: ${deployer.address}`);
  console.log(`Deployer balance: ${ethers.formatEther(await ethers.provider.getBalance(deployer.address))} ETH`);
  
  // Treasury configuration - REPLACE WITH YOUR ACTUAL ADDRESSES
  const treasurerAddress = process.env.TREASURER_ADDRESS || "0x742d35Cc6634C0532925a3b8D4403ddf004ce9Ab";  // Replace with actual treasurer
  console.log(`🏛️ Treasury will be managed by:`);
  console.log(`   Owner (You): ${deployer.address}`);
  console.log(`   Treasurer: ${treasurerAddress}`);
  console.log();

  const deploymentResults = {
    network: network.name,
    chainId: network.chainId.toString(),
    deployer: deployer.address,
    timestamp: new Date().toISOString(),
    contracts: {}
  };

  try {
    // 1. Deploy GuardianToken (ERC-20)
    console.log("📦 Deploying GuardianToken (ERC-20)...");
    const initialSaleAddress = process.env.INITIAL_SALE_ADDRESS || deployer.address;
    
    const GuardianToken = await ethers.getContractFactory("GuardianToken");
    const guardianToken = await GuardianToken.deploy(initialSaleAddress);
    await guardianToken.waitForDeployment();
    
    const guardianTokenAddress = await guardianToken.getAddress();
    console.log(`✅ GuardianToken deployed to: ${guardianTokenAddress}`);
    
    deploymentResults.contracts.GuardianToken = {
      address: guardianTokenAddress,
      constructorArgs: [initialSaleAddress]
    };

    // 2. Deploy GuardianTreasury (Multi-sig Treasury)
    console.log("\n🏛️ Deploying GuardianTreasury (Multi-sig)...");
    
    if (treasurerAddress === "0x742d35Cc6634C0532925a3b8D4403ddf004ce9Ab") {
      console.log("⚠️  WARNING: Using example treasurer address. Please update TREASURER_ADDRESS in .env file!");
    }
    
    const GuardianTreasury = await ethers.getContractFactory("GuardianTreasury");
    const guardianTreasury = await GuardianTreasury.deploy(treasurerAddress);
    await guardianTreasury.waitForDeployment();
    
    const guardianTreasuryAddress = await guardianTreasury.getAddress();
    console.log(`✅ GuardianTreasury deployed to: ${guardianTreasuryAddress}`);
    console.log(`   Owner: ${deployer.address}`);
    console.log(`   Treasurer: ${treasurerAddress}`);
    
    deploymentResults.contracts.GuardianTreasury = {
      address: guardianTreasuryAddress,
      constructorArgs: [treasurerAddress]
    };

    // 3. Deploy GuardianShieldToken (ERC-721 NFT)
    console.log("\n🛡️ Deploying GuardianShieldToken (ERC-721)...");
    
    const GuardianShieldToken = await ethers.getContractFactory("GuardianShieldToken");
    const guardianShieldToken = await GuardianShieldToken.deploy();
    await guardianShieldToken.waitForDeployment();
    
    const guardianShieldTokenAddress = await guardianShieldToken.getAddress();
    console.log(`✅ GuardianShieldToken deployed to: ${guardianShieldTokenAddress}`);
    
    deploymentResults.contracts.GuardianShieldToken = {
      address: guardianShieldTokenAddress,
      constructorArgs: []
    };

    // 3. Deploy GuardianStaking
    console.log("\n💰 Deploying GuardianStaking...");
    const rewardRate = process.env.REWARD_RATE || "1000000000000000000"; // 1 token per second
    
    const GuardianStaking = await ethers.getContractFactory("GuardianStaking");
    const guardianStaking = await GuardianStaking.deploy(guardianTokenAddress, rewardRate);
    await guardianStaking.waitForDeployment();
    
    const guardianStakingAddress = await guardianStaking.getAddress();
    console.log(`✅ GuardianStaking deployed to: ${guardianStakingAddress}`);
    
    deploymentResults.contracts.GuardianStaking = {
      address: guardianStakingAddress,
      constructorArgs: [guardianTokenAddress, rewardRate]
    };

    // 4. Deploy GuardianLiquidityPool
    console.log("\n🌊 Deploying GuardianLiquidityPool...");
    
    const GuardianLiquidityPool = await ethers.getContractFactory("GuardianLiquidityPool");
    const guardianLiquidityPool = await GuardianLiquidityPool.deploy(guardianTokenAddress, guardianShieldTokenAddress);
    await guardianLiquidityPool.waitForDeployment();
    
    const guardianLiquidityPoolAddress = await guardianLiquidityPool.getAddress();
    console.log(`✅ GuardianLiquidityPool deployed to: ${guardianLiquidityPoolAddress}`);
    
    deploymentResults.contracts.GuardianLiquidityPool = {
      address: guardianLiquidityPoolAddress,
      constructorArgs: [guardianTokenAddress, guardianShieldTokenAddress]
    };

    // 5. Deploy DMER
    console.log("\n📊 Deploying DMER (Dynamic Morphing Entity Registry)...");
    
    const DMER = await ethers.getContractFactory("DMER");
    const dmer = await DMER.deploy();
    await dmer.waitForDeployment();
    
    const dmerAddress = await dmer.getAddress();
    console.log(`✅ DMER deployed to: ${dmerAddress}`);
    
    deploymentResults.contracts.DMER = {
      address: dmerAddress,
      constructorArgs: []
    };

    // 6. Deploy EvolutionaryUpgradeableContract
    console.log("\n🧬 Deploying EvolutionaryUpgradeableContract...");
    
    const EvolutionaryUpgradeableContract = await ethers.getContractFactory("EvolutionaryUpgradeableContract");
    
    // Constructor parameters: _logic, _admin, _data, _agents, _threshold
    const logicAddress = dmerAddress; // Use DMER as initial logic contract
    const adminAddress = deployer.address;
    const initData = "0x"; // Empty initialization data
    const agentAddresses = [deployer.address]; // Initial agent addresses
    const threshold = 1; // Initial consensus threshold
    
    const evolutionaryContract = await EvolutionaryUpgradeableContract.deploy(
      logicAddress,
      adminAddress, 
      initData,
      agentAddresses,
      threshold
    );
    await evolutionaryContract.waitForDeployment();
    
    const evolutionaryContractAddress = await evolutionaryContract.getAddress();
    console.log(`✅ EvolutionaryUpgradeableContract deployed to: ${evolutionaryContractAddress}`);
    
    deploymentResults.contracts.EvolutionaryUpgradeableContract = {
      address: evolutionaryContractAddress,
      constructorArgs: [logicAddress, adminAddress, initData, agentAddresses, threshold]
    };

    // 7. Deploy GuardianTokenSale
    console.log("\n💰 Deploying GuardianTokenSale...");
    
    const GuardianTokenSale = await ethers.getContractFactory("GuardianTokenSale");
    const guardianTokenSale = await GuardianTokenSale.deploy(
      guardianTokenAddress,
      deployer.address, // Fallback treasury address
      guardianTreasuryAddress // Multi-sig treasury
    );
    await guardianTokenSale.waitForDeployment();
    
    const guardianTokenSaleAddress = await guardianTokenSale.getAddress();
    console.log(`✅ GuardianTokenSale deployed to: ${guardianTokenSaleAddress}`);
    console.log(`   Connected to Treasury: ${guardianTreasuryAddress}`);
    
    deploymentResults.contracts.GuardianTokenSale = {
      address: guardianTokenSaleAddress,
      constructorArgs: [guardianTokenAddress, deployer.address, guardianTreasuryAddress]
    };

    // Transfer tokens to sale contract for distribution
    console.log("\n🔄 Setting up token sale...");
    const saleTokenAmount = ethers.parseEther("300000000"); // 300M tokens for sale
    await guardianToken.transfer(guardianTokenSaleAddress, saleTokenAmount);
    console.log(`✅ Transferred ${ethers.formatEther(saleTokenAmount)} GUARD tokens to sale contract`);

    // Save deployment results
    const deploymentsDir = path.join(__dirname, "..", "deployments");
    if (!fs.existsSync(deploymentsDir)) {
      fs.mkdirSync(deploymentsDir);
    }
    
    const deploymentFile = path.join(deploymentsDir, `${network.name}-${Date.now()}.json`);
    fs.writeFileSync(deploymentFile, JSON.stringify(deploymentResults, null, 2));
    
    // Update latest deployment file
    const latestFile = path.join(deploymentsDir, `${network.name}-latest.json`);
    fs.writeFileSync(latestFile, JSON.stringify(deploymentResults, null, 2));

    console.log("\n" + "=".repeat(60));
    console.log("🎉 DEPLOYMENT COMPLETE!");
    console.log("=".repeat(60));
    console.log(`📄 Deployment details saved to: ${deploymentFile}`);
    console.log();
    console.log("📋 Contract Addresses:");
    console.log(`GuardianToken (ERC-20): ${guardianTokenAddress}`);
    console.log(`GuardianShieldToken (NFT): ${guardianShieldTokenAddress}`);
    console.log(`GuardianStaking: ${guardianStakingAddress}`);
    console.log(`GuardianLiquidityPool: ${guardianLiquidityPoolAddress}`);
    console.log(`DMER: ${dmerAddress}`);
    console.log(`EvolutionaryContract: ${evolutionaryContractAddress}`);
    console.log(`GuardianTokenSale: ${guardianTokenSaleAddress}`);
    console.log();
    console.log("🔗 Next Steps:");
    console.log("1. Verify contracts on block explorer");
    console.log("2. Update frontend with contract addresses");
    console.log("3. Set up initial token distribution");
    console.log("4. Configure staking rewards");
    console.log();

    return deploymentResults;

  } catch (error) {
    console.error("❌ Deployment failed:", error);
    process.exit(1);
  }
}

// Execute deployment
if (require.main === module) {
  main()
    .then(() => process.exit(0))
    .catch((error) => {
      console.error(error);
      process.exit(1);
    });
}

module.exports = { main };