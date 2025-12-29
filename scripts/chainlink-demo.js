const { ethers } = require("hardhat");

async function main() {
    console.log("🔗 GuardianShield Chainlink Integration Demo");
    console.log("=" .repeat(50));
    
    // Get deployment info from the latest deployment
    const fs = require('fs');
    const files = fs.readdirSync('.').filter(f => f.startsWith('deployment-') && f.endsWith('.json'));
    
    if (files.length === 0) {
        console.log("❌ No deployment files found. Please run deployment first.");
        return;
    }
    
    const latestFile = files.sort().pop();
    const deploymentInfo = JSON.parse(fs.readFileSync(latestFile, 'utf8'));
    
    console.log(`📂 Using deployment: ${latestFile}`);
    console.log(`🌐 Network: ${deploymentInfo.network}`);
    console.log(`🔗 Oracle Enabled: ${deploymentInfo.configuration.oracleEnabled}`);
    
    // Get contract instances
    const tokenSale = await ethers.getContractAt("GuardianTokenSale", deploymentInfo.contracts.GuardianTokenSale);
    const guardToken = await ethers.getContractAt("ERC20Mock", deploymentInfo.contracts.GuardianToken);
    
    let priceOracle = null;
    if (deploymentInfo.contracts.ChainlinkPriceOracle) {
        priceOracle = await ethers.getContractAt("ChainlinkPriceOracle", deploymentInfo.contracts.ChainlinkPriceOracle);
    }
    
    console.log("\\n🏪 TOKEN SALE INFORMATION");
    console.log("-".repeat(30));
    
    // Get current sale info
    const saleInfo = await tokenSale.getCurrentSaleInfo();
    console.log(`📈 Current Stage: ${saleInfo[0]} - ${saleInfo[1]}`);
    console.log(`💰 Token Price: ${ethers.formatEther(saleInfo[2])} ETH`);
    console.log(`🎯 Stage Capacity: ${ethers.formatEther(saleInfo[3])} GUARD`);
    console.log(`💎 Tokens Sold: ${ethers.formatEther(saleInfo[4])} GUARD`);
    console.log(`🔄 Remaining: ${ethers.formatEther(saleInfo[5])} GUARD`);
    console.log(`✅ Stage Active: ${saleInfo[6]}`);
    
    if (saleInfo.length > 7) {
        console.log(`💵 Price in USD: $${ethers.formatEther(saleInfo[7])}`);
        console.log(`🔗 Oracle Active: ${saleInfo[8]}`);
    }
    
    // Oracle information
    if (priceOracle) {
        console.log("\\n📈 CHAINLINK ORACLE INFORMATION");
        console.log("-".repeat(30));
        
        try {
            const [price, timestamp, success] = await priceOracle.getLatestPrice();
            console.log(`💰 Current ETH Price: $${(Number(price) / 1e8).toFixed(2)}`);
            console.log(`⏰ Last Updated: ${new Date(Number(timestamp) * 1000).toLocaleString()}`);
            console.log(`✅ Oracle Status: ${success ? '🟢 Healthy' : '🟡 Using Fallback'}`);
            
            const [healthy, status] = await priceOracle.isPriceFeedHealthy();
            console.log(`🏥 Health Check: ${healthy ? '🟢' : '🔴'} ${status}`);
            
            // Test conversions
            const ethAmount = ethers.parseEther("1");
            const usdValue = await priceOracle.ethToUsd(ethAmount);
            console.log(`🔄 1 ETH = $${ethers.formatEther(usdValue)}`);
            
            const usdAmount = ethers.parseEther("3000");
            const ethValue = await priceOracle.usdToEth(usdAmount);
            console.log(`🔄 $3000 = ${ethers.formatEther(ethValue)} ETH`);
            
        } catch (error) {
            console.log(`⚠️  Oracle Error: ${error.message}`);
        }
    } else {
        console.log("\\n⚠️  ORACLE NOT DEPLOYED");
        console.log("-".repeat(30));
        console.log("🔄 Using fallback pricing mechanism");
        
        const fallbackPrice = await tokenSale.fallbackEthPrice();
        console.log(`📊 Fallback ETH Price: $${(Number(fallbackPrice) / 1e8).toFixed(2)}`);
    }
    
    // Show all stage pricing
    console.log("\\n💰 ALL STAGE PRICING");
    console.log("-".repeat(30));
    
    for (let stage = 1; stage <= 3; stage++) {
        try {
            const stagePrice = await tokenSale.getTokenPriceInUsd(stage);
            const stageInfo = await tokenSale.saleStages(stage);
            
            console.log(`Stage ${stage} (${stageInfo.name}):`);
            console.log(`  💵 USD Price: $${ethers.formatEther(stagePrice)}`);
            console.log(`  ⚡ ETH Price: ${ethers.formatEther(stageInfo.price)} ETH`);
            console.log(`  🎯 Max Tokens: ${ethers.formatEther(stageInfo.maxTokens)} GUARD`);
            console.log(`  📊 Progress: ${ethers.formatEther(stageInfo.soldTokens)}/${ethers.formatEther(stageInfo.maxTokens)}`);
            console.log(`  ✅ Active: ${stageInfo.active}`);
            console.log("");
        } catch (error) {
            console.log(`  ⚠️  Error getting stage ${stage} info: ${error.message}`);
        }
    }
    
    // Test purchase simulation
    console.log("\\n🛒 PURCHASE SIMULATION");
    console.log("-".repeat(30));
    
    const ethPurchaseAmount = ethers.parseEther("0.1"); // 0.1 ETH
    try {
        const expectedTokens = await tokenSale.calculateTokens(ethPurchaseAmount);
        console.log(`💰 Purchase Amount: ${ethers.formatEther(ethPurchaseAmount)} ETH`);
        console.log(`🎁 Expected Tokens: ${ethers.formatEther(expectedTokens)} GUARD`);
        
        // Calculate cost per token
        const costPerToken = ethPurchaseAmount / expectedTokens * BigInt(10**18);
        console.log(`📊 Cost per Token: ${ethers.formatEther(costPerToken)} ETH`);
        
        // Show USD equivalent if oracle available
        if (priceOracle) {
            try {
                const usdValue = await priceOracle.ethToUsd(ethPurchaseAmount);
                console.log(`💵 USD Equivalent: $${ethers.formatEther(usdValue)}`);
                
                const usdPerToken = usdValue / expectedTokens * BigInt(10**18);
                console.log(`📊 USD per Token: $${ethers.formatEther(usdPerToken)}`);
            } catch (error) {
                console.log(`⚠️  USD conversion error: ${error.message}`);
            }
        }
    } catch (error) {
        console.log(`⚠️  Purchase simulation error: ${error.message}`);
    }
    
    console.log("\\n✨ INTEGRATION FEATURES");
    console.log("-".repeat(30));
    console.log("🔗 Real-time ETH/USD pricing via Chainlink");
    console.log("💰 USD-based token pricing ($0.001, $0.0015, $0.002)");
    console.log("🔄 Automatic price conversion");
    console.log("🛡️  Fallback pricing for network compatibility");
    console.log("⚙️  Admin controls for oracle management");
    console.log("📊 Multi-stage sale progression");
    console.log("🎯 Referral system integration");
    console.log("💎 ERC-20 token compatibility");
    
    console.log("\\n🚀 Ready for mainnet deployment with live Chainlink pricing!");
}

if (require.main === module) {
    main()
        .then(() => process.exit(0))
        .catch((error) => {
            console.error(error);
            process.exit(1);
        });
}

module.exports = main;