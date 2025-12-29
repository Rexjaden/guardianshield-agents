const hre = require("hardhat");

async function main() {
    console.log("\n🛡️ Deploying GuardianShield Security NFT Tokens...\n");

    // Get the deployer account
    const [deployer] = await hre.ethers.getSigners();
    console.log("Deploying contracts with account:", deployer.address);
    console.log("Account balance:", hre.ethers.formatEther(await hre.ethers.provider.getBalance(deployer.address)), "ETH");

    // Deploy GuardianTreasury first (if not already deployed)
    let treasuryAddress;
    
    try {
        // Try to get existing treasury address from deployment file
        const fs = require('fs');
        const deploymentPath = './contract-addresses.json';
        
        if (fs.existsSync(deploymentPath)) {
            const deploymentData = JSON.parse(fs.readFileSync(deploymentPath, 'utf8'));
            treasuryAddress = deploymentData.GuardianTreasury;
            console.log("Using existing Treasury address:", treasuryAddress);
        }
        
        if (!treasuryAddress) {
            console.log("Deploying GuardianTreasury...");
            const GuardianTreasury = await hre.ethers.getContractFactory("GuardianTreasury");
            const treasury = await GuardianTreasury.deploy();
            await treasury.waitForDeployment();
            treasuryAddress = await treasury.getAddress();
            console.log("✅ GuardianTreasury deployed to:", treasuryAddress);
        }
    } catch (error) {
        console.log("Treasury deployment error, using deployer as treasury:", error.message);
        treasuryAddress = deployer.address;
    }

    // Deploy GuardianShieldNFT
    console.log("\nDeploying GuardianShieldNFT...");
    const GuardianShieldNFT = await hre.ethers.getContractFactory("GuardianShieldNFT");
    const shieldNFT = await GuardianShieldNFT.deploy(treasuryAddress);
    await shieldNFT.waitForDeployment();
    
    const shieldNFTAddress = await shieldNFT.getAddress();
    console.log("✅ GuardianShieldNFT deployed to:", shieldNFTAddress);

    // Setup initial configuration
    console.log("\n⚙️ Setting up initial configuration...");
    
    // Add some authorized reporters (optional)
    try {
        const tx1 = await shieldNFT.addAuthorizedReporter(deployer.address);
        await tx1.wait();
        console.log("✅ Added deployer as authorized reporter");
    } catch (error) {
        console.log("⚠️ Note: Deployer already authorized");
    }

    // Test mint a shield token
    console.log("\n🔨 Test minting Shield Token...");
    try {
        const mintTx = await shieldNFT.mintShield(
            deployer.address,
            "Basic",
            "Test Shield Token #1",
            { value: hre.ethers.parseEther("0.01") }
        );
        await mintTx.wait();
        console.log("✅ Test Shield Token minted successfully");
        
        // Get token details
        const tokenDetails = await shieldNFT.getShieldDetails(1);
        console.log("📊 Token Details:");
        console.log("   Serial Number:", tokenDetails.serialNumber.toString());
        console.log("   Shield Type:", tokenDetails.shieldType);
        console.log("   Protection Level:", tokenDetails.protectionLevel.toString());
        console.log("   Original Owner:", tokenDetails.originalOwner);
        
    } catch (error) {
        console.log("⚠️ Test minting failed:", error.message);
    }

    // Display contract statistics
    console.log("\n📈 Contract Statistics:");
    try {
        const stats = await shieldNFT.getContractStats();
        console.log("   Total Minted:", stats._totalMinted.toString());
        console.log("   Total Burned:", stats._totalBurned.toString());
        console.log("   Total Recovered:", stats._totalRecovered.toString());
        console.log("   Total Supply:", stats._totalSupply.toString());
        console.log("   Next Serial Number:", stats._nextSerial.toString());
    } catch (error) {
        console.log("⚠️ Could not fetch statistics:", error.message);
    }

    // Save contract addresses
    const contractAddresses = {
        GuardianShieldNFT: shieldNFTAddress,
        GuardianTreasury: treasuryAddress,
        network: hre.network.name,
        deployer: deployer.address,
        deploymentTime: new Date().toISOString()
    };

    // Update existing addresses file or create new one
    const fs = require('fs');
    const path = require('path');
    const addressesPath = path.join(__dirname, '../contract-addresses.json');
    
    let existingAddresses = {};
    if (fs.existsSync(addressesPath)) {
        existingAddresses = JSON.parse(fs.readFileSync(addressesPath, 'utf8'));
    }
    
    const updatedAddresses = { ...existingAddresses, ...contractAddresses };
    fs.writeFileSync(addressesPath, JSON.stringify(updatedAddresses, null, 2));
    
    console.log("\n💾 Contract addresses saved to contract-addresses.json");

    // Create Shield NFT interaction script
    const interactionScript = `
// GuardianShield NFT Interaction Examples
const hre = require("hardhat");

async function interactWithShieldNFT() {
    const [signer] = await hre.ethers.getSigners();
    const shieldNFT = await hre.ethers.getContractAt("GuardianShieldNFT", "${shieldNFTAddress}");
    
    console.log("🛡️ GuardianShield NFT Interaction Examples\\n");
    
    // 1. Mint different shield types
    console.log("1. Minting different shield types...");
    
    // Basic Shield
    const basicTx = await shieldNFT.mintShield(
        signer.address, 
        "Basic", 
        "My Basic Shield",
        { value: hre.ethers.parseEther("0.01") }
    );
    await basicTx.wait();
    console.log("✅ Basic Shield minted");
    
    // Premium Shield
    const premiumTx = await shieldNFT.mintShield(
        signer.address, 
        "Premium", 
        "My Premium Shield",
        { value: hre.ethers.parseEther("0.05") }
    );
    await premiumTx.wait();
    console.log("✅ Premium Shield minted");
    
    // 2. Get user's tokens
    console.log("\\n2. Getting user's tokens...");
    const userTokens = await shieldNFT.getTokensOfOwner(signer.address);
    console.log("User owns", userTokens.length, "shield tokens");
    
    // 3. Display token details
    for (let i = 0; i < userTokens.length; i++) {
        const tokenId = userTokens[i];
        const details = await shieldNFT.getShieldDetails(tokenId);
        console.log(\`Token #\${tokenId}:\`);
        console.log(\`  Serial: #\${details.serialNumber}\`);
        console.log(\`  Type: \${details.shieldType}\`);
        console.log(\`  Protection: \${details.protectionLevel}%\`);
    }
    
    // 4. Demonstrate theft reporting (example)
    console.log("\\n4. Theft reporting example...");
    const lastTokenId = userTokens[userTokens.length - 1];
    
    // Report token as stolen
    const reportTx = await shieldNFT.reportStolen(lastTokenId);
    await reportTx.wait();
    console.log(\`✅ Token #\${lastTokenId} reported as stolen\`);
    
    // Check stolen status
    const stolenDetails = await shieldNFT.getShieldDetails(lastTokenId);
    console.log(\`Stolen status: \${stolenDetails.isStolen}\`);
    
    console.log("\\n🎉 Shield NFT interaction examples completed!");
}

// Run the interaction
interactWithShieldNFT()
    .then(() => process.exit(0))
    .catch(error => {
        console.error(error);
        process.exit(1);
    });
`;

    fs.writeFileSync(path.join(__dirname, '../scripts/interact-shield-nft.js'), interactionScript);
    console.log("📝 Interaction script created: scripts/interact-shield-nft.js");

    // Verification instructions
    console.log("\n🔍 To verify the contract on Etherscan:");
    console.log(`npx hardhat verify --network ${hre.network.name} ${shieldNFTAddress} "${treasuryAddress}"`);

    console.log("\n🎉 GuardianShield Security NFT deployment completed!");
    console.log("\n📋 Key Features:");
    console.log("   ✅ Unique serial numbers starting from #100001");
    console.log("   ✅ 4 shield types: Basic, Premium, Elite, Guardian");
    console.log("   ✅ Theft reporting and burn protocol");
    console.log("   ✅ Automatic remint to treasury for recovery");
    console.log("   ✅ Return to rightful owner functionality");
    console.log("   ✅ Complete tracking and metadata system");
    
    console.log("\n🚀 Next Steps:");
    console.log("   1. Run: node scripts/interact-shield-nft.js");
    console.log("   2. Add Shield NFT frontend integration");
    console.log("   3. Set up theft monitoring system");
    console.log("   4. Configure automated recovery processes");
    
    return {
        shieldNFT: shieldNFTAddress,
        treasury: treasuryAddress
    };
}

main()
    .then((addresses) => {
        console.log("\n✅ Deployment successful!");
        console.log("Shield NFT:", addresses.shieldNFT);
        console.log("Treasury:", addresses.treasury);
        process.exit(0);
    })
    .catch((error) => {
        console.error("❌ Deployment failed:", error);
        process.exit(1);
    });