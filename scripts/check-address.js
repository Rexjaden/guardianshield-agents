const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
    console.log("\n💰 Address Balance Checker");
    console.log("===========================");
    
    const network = hre.network.name;
    console.log(`📍 Network: ${network}`);
    
    const addressToCheck = "0x59bb1BD7b4f596c0886c3332fa8d3fF2e3242B87";
    console.log(`🔍 Checking: ${addressToCheck}`);
    
    try {
        const balance = await ethers.provider.getBalance(addressToCheck);
        const balanceEth = parseFloat(ethers.formatEther(balance));
        
        console.log(`💰 Current Balance: ${balanceEth.toFixed(6)} ETH`);
        
        const minBalance = ethers.parseEther("0.005");
        const recommendedBalance = ethers.parseEther("0.02");
        
        if (balance >= recommendedBalance) {
            console.log("✅ EXCELLENT! This address has plenty of ETH for deployment!");
            console.log("🚀 Ready to deploy GuardianShield contracts immediately!");
        } else if (balance >= minBalance) {
            console.log("✅ SUFFICIENT! This address has enough ETH for deployment!");
            console.log("⚠️  Recommended to have more for safety, but this will work.");
        } else {
            console.log("❌ Insufficient ETH for deployment.");
            console.log(`💸 Need: ${ethers.formatEther(minBalance)} ETH minimum`);
            console.log(`💸 Recommended: ${ethers.formatEther(recommendedBalance)} ETH`);
        }
        
        // Check if this is a contract
        const code = await ethers.provider.getCode(addressToCheck);
        if (code !== "0x") {
            console.log("⚠️  NOTE: This appears to be a contract address, not an EOA.");
        }
        
    } catch (error) {
        console.error(`❌ Error checking balance: ${error.message}`);
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("❌ Script failed:", error);
        process.exit(1);
    });