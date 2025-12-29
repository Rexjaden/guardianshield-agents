const fs = require('fs');
const path = require('path');

/**
 * Contract Configuration Manager
 * Updates frontend files with deployed contract addresses
 */
class ContractConfigManager {
    constructor() {
        this.deploymentsDir = './';
        this.frontendDir = './frontend';
        this.configFile = path.join(this.frontendDir, 'js', 'config.js');
    }
    
    /**
     * Find the latest deployment file
     */
    findLatestDeployment() {
        const files = fs.readdirSync(this.deploymentsDir)
            .filter(f => f.startsWith('deployment-') && f.endsWith('.json'))
            .sort()
            .reverse();
        
        if (files.length === 0) {
            throw new Error('No deployment files found. Please run deployment first.');
        }
        
        return path.join(this.deploymentsDir, files[0]);
    }
    
    /**
     * Load deployment data
     */
    loadDeploymentData(filePath) {
        const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
        console.log(`📂 Loading deployment data from: ${path.basename(filePath)}`);
        console.log(`🌐 Network: ${data.network} (Chain ID: ${data.chainId})`);
        return data;
    }
    
    /**
     * Generate frontend configuration
     */
    generateConfig(deploymentData) {
        const config = {
            network: {
                name: deploymentData.network,
                chainId: deploymentData.chainId,
                timestamp: deploymentData.timestamp
            },
            contracts: {
                tokenSale: deploymentData.contracts.GuardianTokenSale || '0x0000000000000000000000000000000000000000',
                token: deploymentData.contracts.GuardianToken || '0x0000000000000000000000000000000000000000',
                priceOracle: deploymentData.contracts.ChainlinkPriceOracle || '0x0000000000000000000000000000000000000000'
            },
            configuration: deploymentData.configuration,
            features: {
                chainlinkEnabled: deploymentData.configuration.oracleEnabled || false,
                multiWalletSupport: true,
                realTimePricing: deploymentData.configuration.oracleEnabled || false
            }
        };
        
        return config;
    }
    
    /**
     * Update frontend configuration file
     */
    updateFrontendConfig(config) {
        const configJs = `// GuardianShield Contract Configuration
// Auto-generated on ${new Date().toISOString()}

const GuardianConfig = {
    network: {
        name: '${config.network.name}',
        chainId: ${config.network.chainId},
        deployedAt: '${config.network.timestamp}'
    },
    
    contracts: {
        tokenSale: '${config.contracts.tokenSale}',
        token: '${config.contracts.token}',
        priceOracle: '${config.contracts.priceOracle}'
    },
    
    tokenInfo: {
        name: 'Guardian Token',
        symbol: 'GUARD',
        decimals: 18,
        totalSupply: '1000000000' // 1B tokens
    },
    
    saleInfo: {
        stages: [
            { id: 1, name: 'Pre-Sale', price: 0.001, discount: '50%', maxTokens: 50000000 },
            { id: 2, name: 'Public Sale', price: 0.0015, discount: '25%', maxTokens: 100000000 },
            { id: 3, name: 'Final Sale', price: 0.002, discount: '0%', maxTokens: 150000000 }
        ],
        minPurchase: 0.01, // ETH
        maxPurchase: 10,   // ETH
        referralBonus: 0.05 // 5%
    },
    
    features: {
        chainlinkEnabled: ${config.features.chainlinkEnabled},
        multiWalletSupport: ${config.features.multiWalletSupport},
        realTimePricing: ${config.features.realTimePricing}
    },
    
    supportedNetworks: {
        1: {
            name: 'Ethereum Mainnet',
            rpc: 'https://mainnet.infura.io/v3/',
            explorer: 'https://etherscan.io',
            contracts: {
                tokenSale: '${config.network.chainId === 1 ? config.contracts.tokenSale : '0x0000000000000000000000000000000000000000'}',
                token: '${config.network.chainId === 1 ? config.contracts.token : '0x0000000000000000000000000000000000000000'}',
                priceOracle: '${config.network.chainId === 1 ? config.contracts.priceOracle : '0x0000000000000000000000000000000000000000'}'
            }
        },
        11155111: {
            name: 'Sepolia Testnet',
            rpc: 'https://sepolia.infura.io/v3/',
            explorer: 'https://sepolia.etherscan.io',
            contracts: {
                tokenSale: '${config.network.chainId === 11155111 ? config.contracts.tokenSale : '0x0000000000000000000000000000000000000000'}',
                token: '${config.network.chainId === 11155111 ? config.contracts.token : '0x0000000000000000000000000000000000000000'}',
                priceOracle: '${config.network.chainId === 11155111 ? config.contracts.priceOracle : '0x0000000000000000000000000000000000000000'}'
            }
        },
        137: {
            name: 'Polygon Mainnet',
            rpc: 'https://polygon-rpc.com',
            explorer: 'https://polygonscan.com',
            contracts: {
                tokenSale: '${config.network.chainId === 137 ? config.contracts.tokenSale : '0x0000000000000000000000000000000000000000'}',
                token: '${config.network.chainId === 137 ? config.contracts.token : '0x0000000000000000000000000000000000000000'}',
                priceOracle: '${config.network.chainId === 137 ? config.contracts.priceOracle : '0x0000000000000000000000000000000000000000'}'
            }
        },
        31337: {
            name: 'Hardhat Local',
            rpc: 'http://127.0.0.1:8545',
            explorer: 'http://localhost:8545',
            contracts: {
                tokenSale: '${config.network.chainId === 31337 ? config.contracts.tokenSale : '0x0000000000000000000000000000000000000000'}',
                token: '${config.network.chainId === 31337 ? config.contracts.token : '0x0000000000000000000000000000000000000000'}',
                priceOracle: '${config.network.chainId === 31337 ? config.contracts.priceOracle : '0x0000000000000000000000000000000000000000'}'
            }
        }
    },
    
    // Contract ABIs (essential methods only)
    abis: {
        tokenSale: [
            "function getCurrentSaleInfo() view returns (uint256, string, uint256, uint256, uint256, uint256, bool, uint256, bool)",
            "function calculateTokens(uint256) view returns (uint256)",
            "function buyTokens(address) payable",
            "function buyTokensWithToken(address, uint256, address)",
            "function getTokenPriceInUsd(uint256) view returns (uint256)",
            "function purchasedTokens(address) view returns (uint256)",
            "function totalContributed(address) view returns (uint256)"
        ],
        token: [
            "function name() view returns (string)",
            "function symbol() view returns (string)",
            "function decimals() view returns (uint8)",
            "function totalSupply() view returns (uint256)",
            "function balanceOf(address) view returns (uint256)",
            "function transfer(address, uint256) returns (bool)",
            "function allowance(address, address) view returns (uint256)",
            "function approve(address, uint256) returns (bool)"
        ],
        priceOracle: [
            "function getLatestPrice() view returns (uint256, uint256, bool)",
            "function ethToUsd(uint256) view returns (uint256)",
            "function usdToEth(uint256) view returns (uint256)",
            "function isPriceFeedHealthy() view returns (bool, string)",
            "function getTokenPriceInUsd(uint256) view returns (uint256)"
        ]
    }
};

// Export for different environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GuardianConfig;
} else {
    window.GuardianConfig = GuardianConfig;
}`;

        // Ensure directory exists
        const jsDir = path.join(this.frontendDir, 'js');
        if (!fs.existsSync(jsDir)) {
            fs.mkdirSync(jsDir, { recursive: true });
        }
        
        fs.writeFileSync(this.configFile, configJs);
        console.log(`✅ Frontend configuration updated: ${this.configFile}`);
    }
    
    /**
     * Update HTML files with contract addresses
     */
    updateHtmlFiles(config) {
        const htmlFiles = [
            path.join(this.frontendDir, 'token-sale-frontend.html'),
            path.join(this.frontendDir, 'index.html')
        ];
        
        htmlFiles.forEach(filePath => {
            if (fs.existsSync(filePath)) {
                let content = fs.readFileSync(filePath, 'utf8');
                
                // Update contract addresses in JavaScript
                content = content.replace(
                    /tokenSale:\s*'0x[0-9a-fA-F]{40}'/g,
                    `tokenSale: '${config.contracts.tokenSale}'`
                );
                content = content.replace(
                    /token:\s*'0x[0-9a-fA-F]{40}'/g,
                    `token: '${config.contracts.token}'`
                );
                
                // Update network info
                content = content.replace(
                    /chainId:\s*\d+/g,
                    `chainId: ${config.network.chainId}`
                );
                
                fs.writeFileSync(filePath, content);
                console.log(`✅ Updated HTML file: ${path.basename(filePath)}`);
            }
        });
    }
    
    /**
     * Generate wallet manager configuration
     */
    updateWalletManager(config) {
        const walletManagerPath = path.join(this.frontendDir, 'js', 'wallet-manager.js');
        
        if (fs.existsSync(walletManagerPath)) {
            let content = fs.readFileSync(walletManagerPath, 'utf8');
            
            // Update contract addresses in the constructor
            const contractAddressesRegex = /this\.contractAddresses = \{[\s\S]*?\};/;
            const newContractAddresses = `this.contractAddresses = {
            1: { // Mainnet
                tokenSale: '${config.network.chainId === 1 ? config.contracts.tokenSale : '0x0000000000000000000000000000000000000000'}',
                token: '${config.network.chainId === 1 ? config.contracts.token : '0x0000000000000000000000000000000000000000'}',
                priceOracle: '${config.network.chainId === 1 ? config.contracts.priceOracle : '0x0000000000000000000000000000000000000000'}'
            },
            11155111: { // Sepolia
                tokenSale: '${config.network.chainId === 11155111 ? config.contracts.tokenSale : '0x0000000000000000000000000000000000000000'}',
                token: '${config.network.chainId === 11155111 ? config.contracts.token : '0x0000000000000000000000000000000000000000'}',
                priceOracle: '${config.network.chainId === 11155111 ? config.contracts.priceOracle : '0x0000000000000000000000000000000000000000'}'
            },
            137: { // Polygon
                tokenSale: '${config.network.chainId === 137 ? config.contracts.tokenSale : '0x0000000000000000000000000000000000000000'}',
                token: '${config.network.chainId === 137 ? config.contracts.token : '0x0000000000000000000000000000000000000000'}',
                priceOracle: '${config.network.chainId === 137 ? config.contracts.priceOracle : '0x0000000000000000000000000000000000000000'}'
            },
            31337: { // Hardhat Local
                tokenSale: '${config.network.chainId === 31337 ? config.contracts.tokenSale : '0x0000000000000000000000000000000000000000'}',
                token: '${config.network.chainId === 31337 ? config.contracts.token : '0x0000000000000000000000000000000000000000'}',
                priceOracle: '${config.network.chainId === 31337 ? config.contracts.priceOracle : '0x0000000000000000000000000000000000000000'}'
            }
        };`;
            
            content = content.replace(contractAddressesRegex, newContractAddresses);
            
            fs.writeFileSync(walletManagerPath, content);
            console.log(`✅ Updated wallet manager configuration`);
        }
    }
    
    /**
     * Main update function
     */
    async updateFrontendWithContracts(deploymentFile = null) {
        try {
            console.log('🔄 Updating frontend with contract addresses...');
            
            // Find deployment file
            const deploymentPath = deploymentFile || this.findLatestDeployment();
            
            // Load deployment data
            const deploymentData = this.loadDeploymentData(deploymentPath);
            
            // Generate configuration
            const config = this.generateConfig(deploymentData);
            
            // Update files
            this.updateFrontendConfig(config);
            this.updateHtmlFiles(config);
            this.updateWalletManager(config);
            
            console.log('');
            console.log('🎉 Frontend update completed successfully!');
            console.log('📋 Summary:');
            console.log(`   Network: ${config.network.name} (${config.network.chainId})`);
            console.log(`   Token Sale: ${config.contracts.tokenSale}`);
            console.log(`   Guardian Token: ${config.contracts.token}`);
            console.log(`   Price Oracle: ${config.contracts.priceOracle}`);
            console.log(`   Chainlink Enabled: ${config.features.chainlinkEnabled ? '✅' : '❌'}`);
            console.log('');
            console.log('🚀 Your frontend is now ready for token sales!');
            
            return config;
            
        } catch (error) {
            console.error('❌ Frontend update failed:', error.message);
            throw error;
        }
    }
}

// CLI usage
if (require.main === module) {
    const manager = new ContractConfigManager();
    const deploymentFile = process.argv[2]; // Optional deployment file path
    
    manager.updateFrontendWithContracts(deploymentFile)
        .then(() => process.exit(0))
        .catch(error => {
            console.error(error);
            process.exit(1);
        });
}

module.exports = ContractConfigManager;