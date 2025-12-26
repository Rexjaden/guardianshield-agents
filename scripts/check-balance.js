const { ethers } = require("hardhat");

async function checkBalance() {
    const [deployer] = await ethers.getSigners();
    const balance = await ethers.provider.getBalance(deployer.address);
    const balanceETH = ethers.formatEther(balance);
    
    console.log("=".repeat(50));
    console.log("🛡️  GuardianShield Deployment Balance Check");
    console.log("=".repeat(50));
    console.log(`📍 Wallet Address: ${deployer.address}`);
    console.log(`💰 Current Balance: ${balanceETH} ETH`);
    console.log();
    
    const requiredETH = 0.005; // Estimated requirement
    const hasEnough = parseFloat(balanceETH) >= requiredETH;
    
    console.log(`✅ Required for deployment: ~${requiredETH} ETH`);
    console.log(`${hasEnough ? '✅' : '❌'} Status: ${hasEnough ? 'READY TO DEPLOY!' : 'NEED MORE ETH'}`);
    
    if (!hasEnough) {
        console.log();
        console.log("🆓 Get FREE testnet ETH from:");
        console.log("   • https://sepoliafaucet.com");
        console.log("   • https://faucets.chain.link/sepolia");
        console.log("   • https://sepolia-faucet.pk910.de");
        console.log();
        console.log(`🎯 Enter your address: ${deployer.address}`);
    } else {
        console.log();
        console.log("🚀 Ready to deploy! Run:");
        console.log("   npm run deploy:sepolia");
    }
    console.log("=".repeat(50));
}

checkBalance()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });