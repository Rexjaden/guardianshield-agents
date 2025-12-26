const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
    console.log("\n🛡️  GuardianShield Smart Contract Deployment");
    console.log("==========================================");
    
    const network = hre.network.name;
    console.log(`📍 Network: ${network}`);
    
    // Get deployer account
    const [deployer] = await ethers.getSigners();
    const deployerAddress = await deployer.getAddress();
    const balance = await ethers.provider.getBalance(deployerAddress);
    
    console.log(`💳 Deployer: ${deployerAddress}`);
    console.log(`💰 Balance: ${ethers.formatEther(balance)} ETH`);
    
    // Check if we have enough ETH for deployment
    const minBalance = ethers.parseEther("0.005");
    if (balance < minBalance) {
        console.log("\n❌ Insufficient ETH for deployment!");
        console.log(`💸 Need at least: ${ethers.formatEther(minBalance)} ETH`);
        console.log("\n🆓 Get FREE Sepolia testnet ETH from:");
        console.log("   • https://sepoliafaucet.com");
        console.log("   • https://faucets.chain.link/sepolia");
        console.log("   • https://sepolia-faucet.pk910.de");
        console.log(`\n🎯 Your address: ${deployerAddress}`);
        process.exit(1);
    }
    
    console.log("\n✅ Sufficient ETH available for deployment!");
    console.log("\n🚀 Starting GuardianShield deployment...");
    
    // Get treasurer address from environment
    const treasurerAddress = process.env.TREASURER_ADDRESS;
    if (!treasurerAddress || treasurerAddress === "YOUR_TREASURER_ADDRESS_HERE") {
        console.log("❌ Please set TREASURER_ADDRESS in your .env file");
        process.exit(1);
    }
    
    console.log(`👑 Treasurer Address: ${treasurerAddress}`);
    
    // Deploy contracts in order
    const deployedContracts = {};
    
    try {
        // 1. Deploy GuardianToken (ERC-20)
        console.log("\n1️⃣ Deploying GuardianToken...");
        const GuardianToken = await ethers.getContractFactory("GuardianToken");
        const guardianToken = await GuardianToken.deploy();
        await guardianToken.waitForDeployment();
        const guardianTokenAddress = await guardianToken.getAddress();
        deployedContracts.guardianToken = guardianTokenAddress;
        console.log(`✅ GuardianToken deployed: ${guardianTokenAddress}`);
        
        // 2. Deploy GuardianTreasury
        console.log("\n2️⃣ Deploying GuardianTreasury...");
        const GuardianTreasury = await ethers.getContractFactory("GuardianTreasury");
        const guardianTreasury = await GuardianTreasury.deploy(treasurerAddress);
        await guardianTreasury.waitForDeployment();
        const guardianTreasuryAddress = await guardianTreasury.getAddress();
        deployedContracts.guardianTreasury = guardianTreasuryAddress;
        console.log(`✅ GuardianTreasury deployed: ${guardianTreasuryAddress}`);
        
        // 3. Deploy GuardianShieldToken (NFT)
        console.log("\n3️⃣ Deploying GuardianShieldToken...");
        const GuardianShieldToken = await ethers.getContractFactory("GuardianShieldToken");
        const guardianShieldToken = await GuardianShieldToken.deploy();
        await guardianShieldToken.waitForDeployment();
        const guardianShieldTokenAddress = await guardianShieldToken.getAddress();
        deployedContracts.guardianShieldToken = guardianShieldTokenAddress;
        console.log(`✅ GuardianShieldToken deployed: ${guardianShieldTokenAddress}`);
        
        // 4. Deploy GuardianStaking
        console.log("\n4️⃣ Deploying GuardianStaking...");
        const GuardianStaking = await ethers.getContractFactory("GuardianStaking");
        const guardianStaking = await GuardianStaking.deploy(guardianTokenAddress);
        await guardianStaking.waitForDeployment();
        const guardianStakingAddress = await guardianStaking.getAddress();
        deployedContracts.guardianStaking = guardianStakingAddress;
        console.log(`✅ GuardianStaking deployed: ${guardianStakingAddress}`);
        
        // 5. Deploy GuardianLiquidityPool
        console.log("\n5️⃣ Deploying GuardianLiquidityPool...");
        const GuardianLiquidityPool = await ethers.getContractFactory("GuardianLiquidityPool");
        const guardianLiquidityPool = await GuardianLiquidityPool.deploy(guardianTokenAddress);
        await guardianLiquidityPool.waitForDeployment();
        const guardianLiquidityPoolAddress = await guardianLiquidityPool.getAddress();
        deployedContracts.guardianLiquidityPool = guardianLiquidityPoolAddress;
        console.log(`✅ GuardianLiquidityPool deployed: ${guardianLiquidityPoolAddress}`);
        
        // 6. Deploy DMER
        console.log("\n6️⃣ Deploying DMER...");
        const DMER = await ethers.getContractFactory("DMER");
        const dmer = await DMER.deploy();
        await dmer.waitForDeployment();
        const dmerAddress = await dmer.getAddress();
        deployedContracts.dmer = dmerAddress;
        console.log(`✅ DMER deployed: ${dmerAddress}`);
        
        // 7. Deploy EvolutionaryUpgradeableContract
        console.log("\n7️⃣ Deploying EvolutionaryUpgradeableContract...");
        const EvolutionaryUpgradeableContract = await ethers.getContractFactory("EvolutionaryUpgradeableContract");
        const evolutionaryUpgradeable = await EvolutionaryUpgradeableContract.deploy();
        await evolutionaryUpgradeable.waitForDeployment();
        const evolutionaryUpgradeableAddress = await evolutionaryUpgradeable.getAddress();
        deployedContracts.evolutionaryUpgradeable = evolutionaryUpgradeableAddress;
        console.log(`✅ EvolutionaryUpgradeableContract deployed: ${evolutionaryUpgradeableAddress}`);
        
        // Save deployment addresses
        const fs = require('fs');
        const deploymentData = {
            network: network,
            timestamp: new Date().toISOString(),
            deployer: deployerAddress,
            treasurer: treasurerAddress,
            contracts: deployedContracts,
            transactionHashes: {}
        };
        
        fs.writeFileSync(`deployment-${network}.json`, JSON.stringify(deploymentData, null, 2));
        
        console.log("\n🎉 DEPLOYMENT COMPLETE!");
        console.log("==========================================");
        console.log("📋 Deployed Contracts:");
        Object.entries(deployedContracts).forEach(([name, address]) => {
            console.log(`   ${name}: ${address}`);
        });
        
        console.log(`\n📄 Deployment details saved to: deployment-${network}.json`);
        
        // Verify contracts on Etherscan if API key is available
        if (process.env.ETHERSCAN_API_KEY && network === 'sepolia') {
            console.log("\n🔍 Starting contract verification...");
            // Note: Verification will be done separately to handle timing
            console.log("⏱️  Run verification after 1-2 minutes:");
            console.log(`npx hardhat verify ${guardianTokenAddress} --network sepolia`);
        }
        
    } catch (error) {
        console.error("\n❌ Deployment failed:", error.message);
        process.exit(1);
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("❌ Script failed:", error);
        process.exit(1);
    });