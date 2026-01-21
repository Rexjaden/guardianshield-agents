const { ethers, upgrades } = require("hardhat");

// GuardianShield Configuration
const GUARDIAN_API_KEY = "J8QD4YPCWIRT3G1WFGHIC7YWGDBJ4VMGZ4";
const GUARDIAN_WALLET = '0xF262b772c2EBf526a5cF8634CA92597583Ef38ee';

// Chainlink Price Feed Addresses (ETH/USD)
const CHAINLINK_ETH_USD = {
    mainnet: '0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419',
    sepolia: '0x694AA1769357215DE4FAC081bf1f309aDC325306',
    polygon: '0xAB594600376Ec9fD91F8e885dADF0CE036862dE0',
    arbitrum: '0x639Fe6ab55C921f74e7fac1ee960C0B6293ba612'
};

async function main() {
    console.log('🚀 Deploying Guard Token (UUPS Upgradeable)...');
    console.log('=' .repeat(50));
    
    const [deployer] = await ethers.getSigners();
    const network = await ethers.provider.getNetwork();
    
    console.log(`📍 Network: ${network.name} (Chain ID: ${network.chainId})`);
    console.log(`👤 Deployer: ${deployer.address}`);
    console.log(`💰 Balance: ${ethers.formatEther(await deployer.provider.getBalance(deployer.address))} ETH`);
    console.log(`🎯 Guardian Wallet: ${GUARDIAN_WALLET}`);
    
    // Get Chainlink price feed address for current network
    let priceFeedAddress;
    switch (network.chainId.toString()) {
        case '1': // Mainnet
            priceFeedAddress = CHAINLINK_ETH_USD.mainnet;
            break;
        case '11155111': // Sepolia
            priceFeedAddress = CHAINLINK_ETH_USD.sepolia;
            break;
        case '137': // Polygon
            priceFeedAddress = CHAINLINK_ETH_USD.polygon;
            break;
        case '42161': // Arbitrum
            priceFeedAddress = CHAINLINK_ETH_USD.arbitrum;
            break;
        default:
            // Fallback for local/testnet - deploy mock price feed
            console.log('⚠️  Unknown network, deploying mock price feed...');
            const MockV3Aggregator = await ethers.getContractFactory('MockV3Aggregator');
            const mockPriceFeed = await MockV3Aggregator.deploy(8, 2000_00000000); // $2000 ETH
            await mockPriceFeed.deployed();
            priceFeedAddress = mockPriceFeed.address;
            console.log(`📊 Mock Price Feed deployed: ${priceFeedAddress}`);
    }
    
    console.log(`📊 Chainlink ETH/USD Price Feed: ${priceFeedAddress}`);
    
    // Deploy the implementation and proxy
    console.log('\n🔨 Deploying Guard Token...');
    const GuardToken = await ethers.getContractFactory('GuardToken');
    
    const logoURI = 'https://guardianshield.io/assets/guard-token-logo.png';
    
    const guardToken = await upgrades.deployProxy(
        GuardToken,
        [priceFeedAddress, logoURI],
        {
            initializer: 'initialize',
            kind: 'uups'
        }
    );
    
    await guardToken.deployed();
    
    console.log(`✅ Guard Token Proxy deployed: ${guardToken.address}`);
    
    // Get implementation address
    const implementationAddress = await upgrades.erc1967.getImplementationAddress(guardToken.address);
    console.log(`🔧 Implementation address: ${implementationAddress}`);
    
    // Verify deployment
    console.log('\n🔍 Verifying deployment...');
    const name = await guardToken.name();
    const symbol = await guardToken.symbol();
    const decimals = await guardToken.decimals();
    const totalSupply = await guardToken.totalSupply();
    const maxSupply = await guardToken.MAX_SUPPLY();
    const owner = await guardToken.owner();
    const saleActive = await guardToken.saleActive();
    
    console.log(`📋 Token Details:`);
    console.log(`   Name: ${name}`);
    console.log(`   Symbol: ${symbol}`);
    console.log(`   Decimals: ${decimals}`);
    console.log(`   Total Supply: ${ethers.utils.formatEther(totalSupply)} GAR`);
    console.log(`   Max Supply: ${ethers.utils.formatEther(maxSupply)} GAR`);
    console.log(`   Owner: ${owner}`);
    console.log(`   Sale Active: ${saleActive}`);
    
    // Set treasurer if different from owner
    if (deployer.address !== GUARDIAN_WALLET) {
        console.log('\n🏦 Setting treasurer...');
        const setTreasurerTx = await guardToken.setTreasurer(GUARDIAN_WALLET);
        await setTreasurerTx.wait();
        console.log(`✅ Treasurer set to: ${GUARDIAN_WALLET}`);
    }
    
    // Test price feed
    console.log('\n💱 Testing price feed...');
    try {
        const ethPrice = await guardToken.getLatestEthUsdPrice();
        console.log(`📈 Current ETH/USD Price: $${(ethPrice / 1e8).toFixed(2)}`);
    } catch (error) {
        console.log(`⚠️  Price feed error: ${error.message}`);
    }
    
    console.log('\n🎉 Deployment Summary:');
    console.log('=' .repeat(50));
    console.log(`🔗 Guard Token Address: ${guardToken.address}`);
    console.log(`🔧 Implementation: ${implementationAddress}`);
    console.log(`📊 Price Feed: ${priceFeedAddress}`);
    console.log(`👤 Owner: ${owner}`);
    console.log(`🏦 Treasurer: ${await guardToken.treasurer()}`);
    console.log(`🏪 Sale Active: ${saleActive}`);
    console.log(`📈 Token Price: $0.005 USD per GAR`);
    
    // Save deployment info
    const deploymentInfo = {
        network: network.name,
        chainId: network.chainId.toString(),
        guardToken: guardToken.address,
        implementation: implementationAddress,
        priceFeed: priceFeedAddress,
        owner: owner,
        treasurer: await guardToken.treasurer(),
        deployer: deployer.address,
        deployedAt: new Date().toISOString(),
        contractDetails: {
            name: name,
            symbol: symbol,
            decimals: decimals,
            totalSupply: totalSupply.toString(),
            maxSupply: maxSupply.toString(),
            saleActive: saleActive,
            tokenPriceUSD: '0.005'
        }
    };
    
    const fs = require('fs');
    fs.writeFileSync(
        `deployment-guard-token-${network.chainId}.json`,
        JSON.stringify(deploymentInfo, null, 2)
    );
    
    console.log(`💾 Deployment info saved to: deployment-guard-token-${network.chainId}.json`);
    
    return guardToken;
}

// Error handling
main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error('\n❌ Deployment failed:');
        console.error(error);
        process.exit(1);
    });

module.exports = { main };