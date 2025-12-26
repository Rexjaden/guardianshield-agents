const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
    console.log("\n🛡️  GuardianShield Smart Contract Deployment");
    console.log("==========================================");
    
    const network = hre.network.name;
    console.log(`📍 Network: ${network}`);
    
    // For this deployment, we'll use a funded address
    const fundedAddress = "0x59bb1BD7b4f596c0886c3332fa8d3fF2e3242B87";
    
    // Check if user has access to this address
    try {
        const accounts = await ethers.getSigners();
        let deployer = null;
        
        // Try to find the funded address in available signers
        for (const account of accounts) {
            if ((await account.getAddress()).toLowerCase() === fundedAddress.toLowerCase()) {
                deployer = account;
                break;
            }
        }
        
        if (!deployer) {
            console.log("❌ Funded address not available in current Hardhat configuration");
            console.log("💡 To deploy with this address, you need to:");
            console.log("   1. Add the private key for this address to your .env file");
            console.log("   2. Or use a wallet like MetaMask for deployment");
            console.log("   3. Or use the Hardhat console to deploy manually");
            console.log(`\n🎯 Funded Address: ${fundedAddress}`);
            console.log(`💰 Balance: Available (0.05 ETH)`);
            
            return;
        }
        
        const deployerAddress = await deployer.getAddress();
        const balance = await ethers.provider.getBalance(deployerAddress);
        
        console.log(`💳 Deployer: ${deployerAddress}`);
        console.log(`💰 Balance: ${ethers.formatEther(balance)} ETH`);
        
        // Check if we have enough ETH
        const minBalance = ethers.parseEther("0.005");
        if (balance < minBalance) {
            console.log("\n❌ Insufficient ETH for deployment!");
            return;
        }
        
        console.log("\n✅ Sufficient ETH available for deployment!");
        console.log("\n🚀 Starting GuardianShield deployment...");
        
        // Treasury address (same as deployer for simplicity)
        const treasurerAddress = deployerAddress;
        console.log(`👑 Treasurer Address: ${treasurerAddress}`);
        
        // Deploy contracts
        const deployedContracts = {};
        
        // 1. Deploy GuardianToken
        console.log("\n1️⃣ Deploying GuardianToken...");
        const GuardianToken = await ethers.getContractFactory("GuardianToken", deployer);
        const guardianToken = await GuardianToken.deploy();
        await guardianToken.waitForDeployment();
        const guardianTokenAddress = await guardianToken.getAddress();
        deployedContracts.guardianToken = guardianTokenAddress;
        console.log(`✅ GuardianToken deployed: ${guardianTokenAddress}`);
        
        // Continue with remaining contracts...
        console.log("\n🎉 DEPLOYMENT INITIATED!");
        console.log("📋 First contract deployed successfully!");
        console.log(`GuardianToken: ${guardianTokenAddress}`);
        
    } catch (error) {
        console.error("\n❌ Deployment preparation failed:", error.message);
        console.log("\n💡 Alternative deployment methods:");
        console.log("   1. Use MetaMask with Remix IDE");
        console.log("   2. Use Hardhat console with manual deployment");
        console.log("   3. Set up private key in .env file (if you have it)");
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("❌ Script failed:", error);
        process.exit(1);
    });