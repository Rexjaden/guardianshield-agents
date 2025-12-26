const hre = require("hardhat");

async function main() {
    console.log("\n🔍 GuardianShield Contract Verification");
    console.log("=====================================");
    
    const network = hre.network.name;
    console.log(`📍 Network: ${network}`);
    
    if (network !== 'sepolia') {
        console.log("❌ This script is for Sepolia testnet only!");
        process.exit(1);
    }
    
    // Load deployment addresses
    const fs = require('fs');
    let deploymentData;
    
    try {
        const deploymentFile = `deployment-${network}.json`;
        deploymentData = JSON.parse(fs.readFileSync(deploymentFile, 'utf8'));
        console.log(`📄 Loaded deployment data from ${deploymentFile}`);
    } catch (error) {
        console.error("❌ Could not load deployment file. Please deploy contracts first.");
        console.error("💡 Run: npx hardhat run scripts/deploy-complete.js --network sepolia");
        process.exit(1);
    }
    
    const contracts = deploymentData.contracts;
    const verificationResults = {};
    
    console.log("\n🚀 Starting contract verification on Etherscan...\n");
    
    // Verify GuardianToken
    if (contracts.guardianToken) {
        try {
            console.log("1️⃣ Verifying GuardianToken...");
            await hre.run("verify:verify", {
                address: contracts.guardianToken,
                constructorArguments: [],
            });
            verificationResults.guardianToken = "✅ Verified";
            console.log(`✅ GuardianToken verified: ${contracts.guardianToken}`);
        } catch (error) {
            verificationResults.guardianToken = `❌ Failed: ${error.message}`;
            console.log(`❌ GuardianToken verification failed: ${error.message}`);
        }
        await new Promise(resolve => setTimeout(resolve, 2000)); // Rate limit delay
    }
    
    // Verify GuardianTreasury
    if (contracts.guardianTreasury) {
        try {
            console.log("\n2️⃣ Verifying GuardianTreasury...");
            await hre.run("verify:verify", {
                address: contracts.guardianTreasury,
                constructorArguments: [deploymentData.treasurer],
            });
            verificationResults.guardianTreasury = "✅ Verified";
            console.log(`✅ GuardianTreasury verified: ${contracts.guardianTreasury}`);
        } catch (error) {
            verificationResults.guardianTreasury = `❌ Failed: ${error.message}`;
            console.log(`❌ GuardianTreasury verification failed: ${error.message}`);
        }
        await new Promise(resolve => setTimeout(resolve, 2000));
    }
    
    // Verify GuardianShieldToken
    if (contracts.guardianShieldToken) {
        try {
            console.log("\n3️⃣ Verifying GuardianShieldToken...");
            await hre.run("verify:verify", {
                address: contracts.guardianShieldToken,
                constructorArguments: [],
            });
            verificationResults.guardianShieldToken = "✅ Verified";
            console.log(`✅ GuardianShieldToken verified: ${contracts.guardianShieldToken}`);
        } catch (error) {
            verificationResults.guardianShieldToken = `❌ Failed: ${error.message}`;
            console.log(`❌ GuardianShieldToken verification failed: ${error.message}`);
        }
        await new Promise(resolve => setTimeout(resolve, 2000));
    }
    
    // Verify GuardianStaking
    if (contracts.guardianStaking) {
        try {
            console.log("\n4️⃣ Verifying GuardianStaking...");
            await hre.run("verify:verify", {
                address: contracts.guardianStaking,
                constructorArguments: [contracts.guardianToken],
            });
            verificationResults.guardianStaking = "✅ Verified";
            console.log(`✅ GuardianStaking verified: ${contracts.guardianStaking}`);
        } catch (error) {
            verificationResults.guardianStaking = `❌ Failed: ${error.message}`;
            console.log(`❌ GuardianStaking verification failed: ${error.message}`);
        }
        await new Promise(resolve => setTimeout(resolve, 2000));
    }
    
    // Verify GuardianLiquidityPool
    if (contracts.guardianLiquidityPool) {
        try {
            console.log("\n5️⃣ Verifying GuardianLiquidityPool...");
            await hre.run("verify:verify", {
                address: contracts.guardianLiquidityPool,
                constructorArguments: [contracts.guardianToken],
            });
            verificationResults.guardianLiquidityPool = "✅ Verified";
            console.log(`✅ GuardianLiquidityPool verified: ${contracts.guardianLiquidityPool}`);
        } catch (error) {
            verificationResults.guardianLiquidityPool = `❌ Failed: ${error.message}`;
            console.log(`❌ GuardianLiquidityPool verification failed: ${error.message}`);
        }
        await new Promise(resolve => setTimeout(resolve, 2000));
    }
    
    // Verify DMER
    if (contracts.dmer) {
        try {
            console.log("\n6️⃣ Verifying DMER...");
            await hre.run("verify:verify", {
                address: contracts.dmer,
                constructorArguments: [],
            });
            verificationResults.dmer = "✅ Verified";
            console.log(`✅ DMER verified: ${contracts.dmer}`);
        } catch (error) {
            verificationResults.dmer = `❌ Failed: ${error.message}`;
            console.log(`❌ DMER verification failed: ${error.message}`);
        }
        await new Promise(resolve => setTimeout(resolve, 2000));
    }
    
    // Verify EvolutionaryUpgradeableContract
    if (contracts.evolutionaryUpgradeable) {
        try {
            console.log("\n7️⃣ Verifying EvolutionaryUpgradeableContract...");
            await hre.run("verify:verify", {
                address: contracts.evolutionaryUpgradeable,
                constructorArguments: [],
            });
            verificationResults.evolutionaryUpgradeable = "✅ Verified";
            console.log(`✅ EvolutionaryUpgradeableContract verified: ${contracts.evolutionaryUpgradeable}`);
        } catch (error) {
            verificationResults.evolutionaryUpgradeable = `❌ Failed: ${error.message}`;
            console.log(`❌ EvolutionaryUpgradeableContract verification failed: ${error.message}`);
        }
    }
    
    // Summary
    console.log("\n🎉 VERIFICATION COMPLETE!");
    console.log("==========================================");
    console.log("📋 Verification Results:");
    Object.entries(verificationResults).forEach(([contract, result]) => {
        console.log(`   ${contract}: ${result}`);
    });
    
    // Save verification results
    deploymentData.verification = {
        timestamp: new Date().toISOString(),
        network: network,
        results: verificationResults
    };
    
    fs.writeFileSync(`deployment-${network}.json`, JSON.stringify(deploymentData, null, 2));
    console.log(`\n📄 Verification results saved to: deployment-${network}.json`);
    
    // Show Etherscan links
    console.log("\n🔗 Etherscan Links:");
    console.log("==========================================");
    Object.entries(contracts).forEach(([name, address]) => {
        console.log(`${name}: https://sepolia.etherscan.io/address/${address}`);
    });
    
    console.log("\n🎯 Next Steps:");
    console.log("• Visit Etherscan links to view verified contracts");
    console.log("• Update frontend with deployed contract addresses");
    console.log("• Test contract interactions on the Web3 frontend");
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("❌ Verification failed:", error);
        process.exit(1);
    });