const { ethers } = require("hardhat");

// Chainlink ETH/USD Price Feed addresses for different networks
const PRICE_FEED_ADDRESSES = {
    // Ethereum Mainnet
    1: "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419",
    // Sepolia Testnet
    11155111: "0x694AA1769357215DE4FAC081bf1f309aDC325306",
    // Polygon Mainnet
    137: "0xF9680D99D6C9589e2a93a78A04A279e509205945",
    // Polygon Mumbai Testnet
    80001: "0xd0D5e3DB44DE05E9F294BB0a3bEEaF030DE24Ada",
    // BSC Mainnet
    56: "0x0567F2323251f0Aab15c8dFb1967E4e8A7D42aeE",
    // BSC Testnet
    97: "0x2514895c72f50D8bd4B4F9b1110F0D6bD2c97526",
    // Arbitrum Mainnet
    42161: "0x639Fe6ab55C921f74e7fac1ee960C0B6293ba612",
    // Arbitrum Sepolia
    421614: "0xd30e2101a97dcbAeBCBC04F14C3f624E67A35165",
    // Flare Network Mainnet
    14: "0x0000000000000000000000000000000000000000", // Placeholder - Flare doesn't have Chainlink yet
    // Flare Testnet (Coston2)
    114: "0x0000000000000000000000000000000000000000"  // Placeholder
};

async function main() {
    console.log("🚀 Starting GuardianShield Token Sale deployment with Chainlink integration...");
    
    const [deployer] = await ethers.getSigners();
    const network = await ethers.provider.getNetwork();
    const chainId = Number(network.chainId);
    
    console.log(`📋 Network: ${network.name} (Chain ID: ${chainId})`);
    console.log(`👤 Deployer: ${deployer.address}`);
    console.log(`💰 Balance: ${ethers.formatEther(await ethers.provider.getBalance(deployer.address))} ETH`);
    
    // Get Chainlink price feed address for this network
    const priceFeedAddress = PRICE_FEED_ADDRESSES[chainId];
    
    if (!priceFeedAddress || priceFeedAddress === "0x0000000000000000000000000000000000000000") {
        console.log("⚠️  Warning: No Chainlink price feed available for this network");
        console.log("⚠️  The oracle will be disabled and fallback pricing will be used");
    } else {
        console.log(`🔗 Using Chainlink ETH/USD Price Feed: ${priceFeedAddress}`);
    }
    
    try {
        // Step 1: Deploy ChainlinkPriceOracle (if price feed is available)
        let priceOracleAddress = ethers.ZeroAddress;
        
        if (priceFeedAddress && priceFeedAddress !== "0x0000000000000000000000000000000000000000") {
            console.log("\\n📈 Deploying ChainlinkPriceOracle...");
            const ChainlinkPriceOracle = await ethers.getContractFactory("ChainlinkPriceOracle");
            const priceOracle = await ChainlinkPriceOracle.deploy(priceFeedAddress);
            await priceOracle.waitForDeployment();
            
            priceOracleAddress = await priceOracle.getAddress();
            console.log(`✅ ChainlinkPriceOracle deployed to: ${priceOracleAddress}`);
            
            // Test the oracle
            try {
                const [price, timestamp, success] = await priceOracle.getLatestPrice();
                console.log(`📊 Current ETH Price: $${(Number(price) / 1e8).toFixed(2)}`);
                console.log(`⏰ Price Timestamp: ${new Date(Number(timestamp) * 1000).toISOString()}`);
                console.log(`✅ Oracle Status: ${success ? 'Healthy' : 'Using Fallback'}`);
            } catch (error) {
                console.log(`⚠️  Oracle test failed: ${error.message}`);
            }
        }
        
        // Step 2: Deploy GuardianToken (using ERC20Mock for testing)
        console.log("\\n🪙 Deploying GuardianToken...");
        const GuardianToken = await ethers.getContractFactory("ERC20Mock");
        const guardToken = await GuardianToken.deploy(
            "Guardian Token",
            "GUARD", 
            ethers.parseEther("1000000000") // 1B tokens
        );
        await guardToken.waitForDeployment();
        
        const guardTokenAddress = await guardToken.getAddress();
        console.log(`✅ GuardianToken deployed to: ${guardTokenAddress}`);
        
        // Step 3: Set up treasury addresses
        const treasury = deployer.address; // Simple treasury for now
        const guardianTreasury = deployer.address; // Multi-sig treasury (replace with actual multi-sig)
        
        console.log(`🏛️  Treasury: ${treasury}`);
        console.log(`🏛️  Guardian Treasury: ${guardianTreasury}`);
        
        // Step 4: Deploy GuardianTokenSale with Chainlink integration
        console.log("\\n💰 Deploying GuardianTokenSale...");
        const GuardianTokenSale = await ethers.getContractFactory("GuardianTokenSale");
        const tokenSale = await GuardianTokenSale.deploy(
            guardTokenAddress,
            treasury,
            guardianTreasury,
            priceOracleAddress
        );
        await tokenSale.waitForDeployment();
        
        const tokenSaleAddress = await tokenSale.getAddress();
        console.log(`✅ GuardianTokenSale deployed to: ${tokenSaleAddress}`);
        
        // Step 5: Transfer tokens to sale contract
        console.log("\\n🔄 Transferring tokens to sale contract...");
        const transferAmount = ethers.parseEther("500000000"); // 500M tokens
        await guardToken.transfer(tokenSaleAddress, transferAmount);
        console.log(`✅ Transferred ${ethers.formatEther(transferAmount)} GUARD tokens to sale contract`);
        
        // Step 6: Get current sale info
        console.log("\\n📊 Current Sale Information:");
        try {
            const saleInfo = await tokenSale.getCurrentSaleInfo();
            console.log(`📈 Stage: ${saleInfo[0]} - ${saleInfo[1]}`);
            console.log(`💰 Price per token: ${ethers.formatEther(saleInfo[2])} ETH`);
            console.log(`🎯 Max Tokens: ${ethers.formatEther(saleInfo[3])}`);
            console.log(`💎 Sold Tokens: ${ethers.formatEther(saleInfo[4])}`);
            console.log(`🔄 Remaining: ${ethers.formatEther(saleInfo[5])}`);
            console.log(`✅ Active: ${saleInfo[6]}`);
            
            if (saleInfo.length > 7) {
                console.log(`💵 Price in USD: $${ethers.formatEther(saleInfo[7])}`);
                console.log(`🔗 Oracle Active: ${saleInfo[8]}`);
            }
        } catch (error) {
            console.log(`⚠️  Error getting sale info: ${error.message}`);
        }
        
        console.log("\\n🎉 Deployment completed successfully!");
        console.log("📋 Summary:");
        console.log(`🪙 GuardianToken: ${guardTokenAddress}`);
        console.log(`📈 ChainlinkPriceOracle: ${priceOracleAddress || 'Not deployed (no price feed)'}`);
        console.log(`💰 GuardianTokenSale: ${tokenSaleAddress}`);
        
        // Verification commands
        console.log("\\n🔍 Verification commands:");
        if (priceOracleAddress !== ethers.ZeroAddress) {
            console.log(`npx hardhat verify --network ${network.name} ${priceOracleAddress} ${priceFeedAddress}`);
        }
        console.log(`npx hardhat verify --network ${network.name} ${guardTokenAddress} "Guardian Token" "GUARD" "${ethers.parseEther("1000000000")}"`);
        console.log(`npx hardhat verify --network ${network.name} ${tokenSaleAddress} ${guardTokenAddress} ${treasury} ${guardianTreasury} ${priceOracleAddress}`);
        
        // Save deployment info
        const deploymentInfo = {
            network: network.name,
            chainId: chainId,
            timestamp: new Date().toISOString(),
            contracts: {
                GuardianToken: guardTokenAddress,
                ChainlinkPriceOracle: priceOracleAddress || null,
                GuardianTokenSale: tokenSaleAddress
            },
            configuration: {
                priceFeedAddress: priceFeedAddress || null,
                treasury: treasury,
                guardianTreasury: guardianTreasury,
                oracleEnabled: priceOracleAddress !== ethers.ZeroAddress
            }
        };
        
        const fs = require('fs');
        const filename = `deployment-${network.name}-${Date.now()}.json`;
        fs.writeFileSync(filename, JSON.stringify(deploymentInfo, null, 2));
        
        console.log(`💾 Deployment info saved to ${filename}`);
        
    } catch (error) {
        console.error("❌ Deployment failed:");
        console.error(error);
        process.exit(1);
    }
}

// Execute deployment
if (require.main === module) {
    main()
        .then(() => process.exit(0))
        .catch((error) => {
            console.error(error);
            process.exit(1);
        });
}

module.exports = main;