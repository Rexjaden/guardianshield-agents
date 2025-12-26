#!/usr/bin/env node
// Post-deployment address updater
// Run this after completing Remix deployment

const fs = require('fs');
const readline = require('readline');

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

console.log("\n🎉 GuardianShield Post-Deployment Setup");
console.log("=======================================");
console.log("Enter the deployed contract addresses:");

const contracts = [
    { name: 'guardianToken', display: 'GuardianToken' },
    { name: 'guardianTreasury', display: 'GuardianTreasury' },
    { name: 'guardianShieldToken', display: 'GuardianShieldToken' },
    { name: 'guardianStaking', display: 'GuardianStaking' },
    { name: 'guardianLiquidityPool', display: 'GuardianLiquidityPool' },
    { name: 'dmer', display: 'DMER' },
    { name: 'evolutionaryUpgradeable', display: 'EvolutionaryUpgradeableContract' }
];

let addresses = {};
let currentContract = 0;

function askForAddress() {
    if (currentContract >= contracts.length) {
        // All addresses collected, save them
        saveDeploymentData();
        return;
    }
    
    const contract = contracts[currentContract];
    rl.question(`${currentContract + 1}. ${contract.display} address: `, (address) => {
        if (address && address.startsWith('0x') && address.length === 42) {
            addresses[contract.name] = address;
            console.log(`✅ ${contract.display}: ${address}`);
        } else {
            console.log("❌ Invalid address format. Please enter a valid Ethereum address (0x...)");
            askForAddress();
            return;
        }
        
        currentContract++;
        askForAddress();
    });
}

function saveDeploymentData() {
    console.log("\n💾 Saving deployment data...");
    
    // Create deployment record
    const deploymentData = {
        network: "sepolia",
        timestamp: new Date().toISOString(),
        deployer: "0x59bb1BD7b4f596c0886c3332fa8d3fF2e3242B87",
        treasurer: "0x59bb1BD7b4f596c0886c3332fa8d3fF2e3242B87",
        contracts: addresses,
        etherscanLinks: {}
    };
    
    // Generate Etherscan links
    Object.entries(addresses).forEach(([name, address]) => {
        deploymentData.etherscanLinks[name] = `https://sepolia.etherscan.io/address/${address}`;
    });
    
    // Save deployment file
    fs.writeFileSync('deployment-sepolia.json', JSON.stringify(deploymentData, null, 2));
    
    // Update frontend config
    const frontendConfig = `// Auto-generated GuardianShield contract addresses
window.GUARDIAN_CONTRACTS = ${JSON.stringify(addresses, null, 2)};

window.GUARDIAN_NETWORK = {
    chainId: 11155111,
    name: 'sepolia',
    rpcUrl: 'https://ethereum-sepolia-rpc.publicnode.com'
};

console.log('🛡️ GuardianShield contracts loaded:', window.GUARDIAN_CONTRACTS);`;
    
    fs.writeFileSync('frontend/contracts-config.js', frontendConfig);
    
    // Update Web3 frontend
    const web3Html = fs.readFileSync('frontend/web3.html', 'utf8');
    const updatedHtml = web3Html.replace(
        '</head>',
        `    <script src="contracts-config.js"></script>\n</head>`
    );
    fs.writeFileSync('frontend/web3.html', updatedHtml);
    
    console.log("\n🎉 SUCCESS! Deployment completed!");
    console.log("================================");
    console.log("✅ Deployment record: deployment-sepolia.json");
    console.log("✅ Frontend config: frontend/contracts-config.js");
    console.log("✅ Web3 frontend: frontend/web3.html (updated)");
    
    console.log("\n🔗 Etherscan Links:");
    Object.entries(addresses).forEach(([name, address]) => {
        console.log(`${name}: https://sepolia.etherscan.io/address/${address}`);
    });
    
    console.log("\n🚀 Next Steps:");
    console.log("1. Verify contracts on Etherscan");
    console.log("2. Test Web3 frontend with live contracts");
    console.log("3. Set up Docker containers");
    
    rl.close();
}

// Start the address collection
askForAddress();