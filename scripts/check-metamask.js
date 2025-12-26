const { ethers } = require('ethers');

async function checkMetaMaskBalance() {
    try {
        const address = "0xF262b772c2EBf526a5cF8634CA92597583Ef38ee";
        
        console.log('\n💰 MetaMask Address Balance Checker');
        console.log('====================================');
        console.log('📍 Network: Sepolia Testnet');
        console.log(`🔍 Checking: ${address}`);
        
        // Connect to Sepolia testnet
        const provider = new ethers.JsonRpcProvider('https://sepolia.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161');
        const balance = await provider.getBalance(address);
        const balanceInEth = ethers.formatEther(balance);
        
        console.log(`💰 Current Balance: ${balanceInEth} ETH`);
        
        if (parseFloat(balanceInEth) >= 0.01) {
            console.log('✅ EXCELLENT! This address has enough ETH for deployment!');
            console.log('🚀 Ready to deploy GuardianShield contracts immediately!');
        } else if (parseFloat(balanceInEth) > 0) {
            console.log('⚠️  LOW BALANCE: You have some ETH but may need more for deployment');
            console.log('💡 Recommended: Get at least 0.01 ETH for safe deployment');
        } else {
            console.log('❌ NO ETH: This address needs ETH from faucet');
            console.log('🔗 Get ETH from: https://sepolia-faucet.pk910.de');
        }
        
    } catch (error) {
        console.error('❌ Error checking balance:', error.message);
    }
}

checkMetaMaskBalance();