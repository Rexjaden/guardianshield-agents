#!/usr/bin/env node

// GuardianShield Deployment Success Checker
// Run this after completing Remix deployment

const { ethers } = require('ethers');

const SEPOLIA_RPC = 'https://ethereum-sepolia-rpc.publicnode.com';
const provider = new ethers.JsonRpcProvider(SEPOLIA_RPC);

async function checkDeployment(contractAddresses) {
    console.log("\n🔍 GuardianShield Deployment Verification");
    console.log("=========================================");
    
    const results = {};
    let totalContracts = Object.keys(contractAddresses).length;
    let successfulDeployments = 0;
    
    for (const [name, address] of Object.entries(contractAddresses)) {
        if (!address || address === "0x0000000000000000000000000000000000000000") {
            console.log(`⏳ ${name}: Not deployed yet`);
            results[name] = 'pending';
            continue;
        }
        
        try {
            const code = await provider.getCode(address);
            if (code !== "0x") {
                console.log(`✅ ${name}: Successfully deployed at ${address}`);
                results[name] = 'success';
                successfulDeployments++;
                
                // Get contract creation info
                try {
                    const balance = await provider.getBalance(address);
                    console.log(`   💰 Contract balance: ${ethers.formatEther(balance)} ETH`);
                } catch (e) {
                    // Balance check failed, but contract exists
                }
            } else {
                console.log(`❌ ${name}: No contract code found at ${address}`);
                results[name] = 'failed';
            }
        } catch (error) {
            console.log(`❌ ${name}: Verification failed - ${error.message}`);
            results[name] = 'error';
        }
    }
    
    console.log(`\n📊 Deployment Summary:`);
    console.log(`✅ Successful: ${successfulDeployments}/${totalContracts}`);
    console.log(`⏳ Pending: ${totalContracts - successfulDeployments}/${totalContracts}`);
    
    if (successfulDeployments === totalContracts) {
        console.log(`\n🎉 COMPLETE! All GuardianShield contracts deployed successfully!`);
        console.log(`🌐 Ready for frontend integration`);
        console.log(`📋 Ready for Etherscan verification`);
        return true;
    } else {
        console.log(`\n⚠️  Deployment in progress...`);
        return false;
    }
}

// Template addresses - replace with actual ones from Remix
const TEST_ADDRESSES = {
    guardianToken: "0x0000000000000000000000000000000000000000",
    guardianTreasury: "0x0000000000000000000000000000000000000000", 
    guardianShieldToken: "0x0000000000000000000000000000000000000000",
    guardianStaking: "0x0000000000000000000000000000000000000000",
    guardianLiquidityPool: "0x0000000000000000000000000000000000000000",
    dmer: "0x0000000000000000000000000000000000000000",
    evolutionaryUpgradeable: "0x0000000000000000000000000000000000000000"
};

// Run check if called directly
if (require.main === module) {
    checkDeployment(TEST_ADDRESSES)
        .then(() => process.exit(0))
        .catch(error => {
            console.error('Verification failed:', error);
            process.exit(1);
        });
}

module.exports = { checkDeployment };