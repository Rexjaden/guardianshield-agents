const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
    console.log("\n⏰ GuardianShield Balance Monitor");
    console.log("=================================");
    
    const network = hre.network.name;
    if (network !== 'sepolia') {
        console.log("❌ This script is for Sepolia testnet only!");
        process.exit(1);
    }
    
    const [deployer] = await ethers.getSigners();
    const deployerAddress = await deployer.getAddress();
    const minBalance = ethers.parseEther("0.005");
    
    console.log(`📍 Monitoring: ${deployerAddress}`);
    console.log(`💸 Target: ${ethers.formatEther(minBalance)} ETH minimum`);
    console.log(`🔄 Checking every 10 seconds...\n`);
    
    let checkCount = 0;
    const maxChecks = 180; // 30 minutes max
    
    while (checkCount < maxChecks) {
        try {
            const balance = await ethers.provider.getBalance(deployerAddress);
            const balanceEth = parseFloat(ethers.formatEther(balance));
            
            checkCount++;
            const timestamp = new Date().toLocaleTimeString();
            
            console.log(`[${timestamp}] Check ${checkCount}: ${balanceEth.toFixed(6)} ETH`);
            
            if (balance >= minBalance) {
                console.log("\n🎉 SUCCESS! Sufficient ETH received!");
                console.log("=======================================");
                console.log(`💰 Final Balance: ${balanceEth.toFixed(6)} ETH`);
                console.log(`✅ Ready for deployment!`);
                console.log("\n🚀 Run deployment now:");
                console.log("npx hardhat run scripts/deploy-complete.js --network sepolia");
                break;
            }
            
            if (checkCount % 6 === 0) { // Every minute
                console.log(`⏳ Still waiting... (${Math.floor(checkCount/6)} min elapsed)`);
                if (checkCount === 12) { // After 2 minutes
                    console.log("💡 Faucets can take 2-5 minutes. Keep waiting...");
                }
            }
            
            await new Promise(resolve => setTimeout(resolve, 10000)); // Wait 10 seconds
            
        } catch (error) {
            console.error(`❌ Error checking balance: ${error.message}`);
            await new Promise(resolve => setTimeout(resolve, 10000));
        }
    }
    
    if (checkCount >= maxChecks) {
        console.log("\n⏰ Monitor timeout reached (30 minutes)");
        console.log("💡 Try running the faucet helper again or try a different faucet");
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("❌ Monitor failed:", error);
        process.exit(1);
    });