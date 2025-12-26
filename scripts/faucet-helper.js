const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
    console.log("\n💧 GuardianShield Testnet Faucet Helper");
    console.log("=====================================");
    
    const network = hre.network.name;
    console.log(`📍 Network: ${network}`);
    
    if (network !== 'sepolia') {
        console.log("❌ This script is for Sepolia testnet only!");
        process.exit(1);
    }
    
    // Get deployer account
    const [deployer] = await ethers.getSigners();
    const deployerAddress = await deployer.getAddress();
    const balance = await ethers.provider.getBalance(deployerAddress);
    
    console.log(`💳 Your Address: ${deployerAddress}`);
    console.log(`💰 Current Balance: ${ethers.formatEther(balance)} ETH`);
    
    const minBalance = ethers.parseEther("0.005");
    const recommendedBalance = ethers.parseEther("0.02");
    
    if (balance >= recommendedBalance) {
        console.log("✅ You have sufficient ETH for deployment!");
        console.log("🚀 Ready to deploy GuardianShield contracts!");
        return;
    }
    
    if (balance >= minBalance) {
        console.log("⚠️  You have minimum ETH but we recommend more for safety");
    } else {
        console.log("❌ Insufficient ETH for deployment!");
    }
    
    console.log(`💸 Recommended: ${ethers.formatEther(recommendedBalance)} ETH`);
    console.log(`💸 Minimum: ${ethers.formatEther(minBalance)} ETH`);
    
    console.log("\n🆓 FREE Sepolia Testnet ETH Faucets:");
    console.log("=====================================");
    console.log("1. 🌊 Sepolia PoW Faucet (Most Reliable):");
    console.log("   https://sepolia-faucet.pk910.de");
    console.log("   💡 Mine for a few minutes to get 0.05+ ETH");
    console.log("");
    console.log("2. 🔗 Chainlink Faucet (Quick):");
    console.log("   https://faucets.chain.link/sepolia");
    console.log("   💡 Need Twitter account, gives 0.1 ETH");
    console.log("");
    console.log("3. 💧 Official Sepolia Faucet:");
    console.log("   https://sepoliafaucet.com");
    console.log("   💡 Requires GitHub/Twitter, gives 0.05 ETH");
    console.log("");
    console.log("4. 🏗️ Alchemy Faucet:");
    console.log("   https://sepoliafaucet.com");
    console.log("   💡 Need Alchemy account, gives 0.5 ETH");
    
    console.log("\n📋 Instructions:");
    console.log("=====================================");
    console.log("1. Copy your address (already copied below):");
    console.log(`   ${deployerAddress}`);
    console.log("");
    console.log("2. Visit one of the faucets above");
    console.log("3. Paste your address and request ETH");
    console.log("4. Wait 1-5 minutes for confirmation");
    console.log("5. Run this script again to check balance");
    console.log("6. Once you have enough ETH, run deployment:");
    console.log("   npx hardhat run scripts/deploy-complete.js --network sepolia");
    
    // Copy address to clipboard if possible
    console.log("\n📎 Address copied to output for easy copying!");
    console.log("📎 Select and copy: " + deployerAddress);
    
    // Show QR code info
    console.log("\n📱 For mobile wallets, use this QR code address:");
    console.log(deployerAddress);
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("❌ Script failed:", error);
        process.exit(1);
    });