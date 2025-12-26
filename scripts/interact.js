const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  console.log("🛡️ GuardianShield Contract Interaction Tool");
  console.log("=".repeat(50));

  const network = await ethers.provider.getNetwork();
  const deploymentFile = path.join(__dirname, "..", "deployments", `${network.name}-latest.json`);
  
  if (!fs.existsSync(deploymentFile)) {
    console.error("❌ No deployment file found. Deploy contracts first.");
    process.exit(1);
  }
  
  const deployment = JSON.parse(fs.readFileSync(deploymentFile, "utf8"));
  const [signer] = await ethers.getSigners();
  
  console.log(`Network: ${network.name}`);
  console.log(`Signer: ${signer.address}`);
  console.log();

  // Load contract instances
  const contracts = {};
  
  try {
    contracts.guardianToken = await ethers.getContractAt(
      "GuardianToken", 
      deployment.contracts.GuardianToken.address
    );
    
    contracts.guardianShieldToken = await ethers.getContractAt(
      "GuardianShieldToken", 
      deployment.contracts.GuardianShieldToken.address
    );
    
    contracts.guardianStaking = await ethers.getContractAt(
      "GuardianStaking", 
      deployment.contracts.GuardianStaking.address
    );
    
    contracts.guardianLiquidityPool = await ethers.getContractAt(
      "GuardianLiquidityPool", 
      deployment.contracts.GuardianLiquidityPool.address
    );
    
    contracts.dmer = await ethers.getContractAt(
      "DMER", 
      deployment.contracts.DMER.address
    );
    
    contracts.evolutionaryContract = await ethers.getContractAt(
      "EvolutionaryUpgradeableContract", 
      deployment.contracts.EvolutionaryUpgradeableContract.address
    );

    console.log("✅ All contracts loaded successfully!");
    console.log();

    // Display contract information
    await displayContractInfo(contracts);
    
    // Perform initial setup if needed
    await performInitialSetup(contracts, signer);

  } catch (error) {
    console.error("❌ Error loading contracts:", error);
    process.exit(1);
  }
}

async function displayContractInfo(contracts) {
  console.log("📊 Contract Information:");
  console.log("-".repeat(30));
  
  try {
    // GuardianToken info
    const tokenName = await contracts.guardianToken.name();
    const tokenSymbol = await contracts.guardianToken.symbol();
    const totalSupply = await contracts.guardianToken.totalSupply();
    const maxSupply = await contracts.guardianToken.MAX_SUPPLY();
    
    console.log(`${tokenName} (${tokenSymbol}):`);
    console.log(`  Total Supply: ${ethers.formatEther(totalSupply)}`);
    console.log(`  Max Supply: ${ethers.formatEther(maxSupply)}`);
    console.log();
    
    // GuardianShieldToken info
    const nftName = await contracts.guardianShieldToken.name();
    const nftSymbol = await contracts.guardianShieldToken.symbol();
    
    console.log(`${nftName} (${nftSymbol}):`);
    console.log(`  ERC-721 NFT for GuardianShield protection`);
    console.log();
    
    // Staking info
    const stakingToken = await contracts.guardianStaking.guardToken();
    const rewardRate = await contracts.guardianStaking.rewardRate();
    
    console.log(`GuardianStaking:`);
    console.log(`  Staking Token: ${stakingToken}`);
    console.log(`  Reward Rate: ${ethers.formatEther(rewardRate)} tokens/second`);
    console.log();
    
  } catch (error) {
    console.error("Error fetching contract info:", error.message);
  }
}

async function performInitialSetup(contracts, signer) {
  console.log("⚙️ Initial Setup:");
  console.log("-".repeat(20));
  
  try {
    // Check if signer is owner of contracts
    const guardianTokenOwner = await contracts.guardianToken.owner();
    const isOwner = guardianTokenOwner.toLowerCase() === signer.address.toLowerCase();
    
    if (isOwner) {
      console.log("✅ You are the owner of the contracts");
      
      // Set up staking contract with some tokens for rewards
      const stakingBalance = await contracts.guardianToken.balanceOf(
        await contracts.guardianStaking.getAddress()
      );
      
      if (stakingBalance === 0n) {
        console.log("🔄 Setting up staking rewards...");
        const rewardAmount = ethers.parseEther("1000000"); // 1M tokens for rewards
        
        const tx = await contracts.guardianToken.transfer(
          await contracts.guardianStaking.getAddress(),
          rewardAmount
        );
        await tx.wait();
        
        console.log(`✅ Transferred ${ethers.formatEther(rewardAmount)} tokens to staking contract`);
      }
      
    } else {
      console.log(`ℹ️ Contract owner: ${guardianTokenOwner}`);
      console.log(`ℹ️ Your address: ${signer.address}`);
    }
    
    console.log();
    console.log("🎉 Setup completed successfully!");
    
  } catch (error) {
    console.error("Error during setup:", error.message);
  }
}

if (require.main === module) {
  main()
    .then(() => process.exit(0))
    .catch((error) => {
      console.error(error);
      process.exit(1);
    });
}

module.exports = { main };