// GuardianShield Contract Configuration
// Auto-generated on 2025-12-29T00:35:23.584Z

const GuardianConfig = {
    network: {
        name: 'hardhat',
        chainId: 1337,
        deployedAt: '2025-12-29T00:27:09.228Z'
    },
    
    contracts: {
        tokenSale: '0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512',
        token: '0x5FbDB2315678afecb367f032d93F642f64180aa3',
        priceOracle: '0x0000000000000000000000000000000000000000'
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
        chainlinkEnabled: false,
        multiWalletSupport: true,
        realTimePricing: false
    },
    
    supportedNetworks: {
        1: {
            name: 'Ethereum Mainnet',
            rpc: 'https://mainnet.infura.io/v3/',
            explorer: 'https://etherscan.io',
            contracts: {
                tokenSale: '0x0000000000000000000000000000000000000000',
                token: '0x0000000000000000000000000000000000000000',
                priceOracle: '0x0000000000000000000000000000000000000000'
            }
        },
        11155111: {
            name: 'Sepolia Testnet',
            rpc: 'https://sepolia.infura.io/v3/',
            explorer: 'https://sepolia.etherscan.io',
            contracts: {
                tokenSale: '0x0000000000000000000000000000000000000000',
                token: '0x0000000000000000000000000000000000000000',
                priceOracle: '0x0000000000000000000000000000000000000000'
            }
        },
        137: {
            name: 'Polygon Mainnet',
            rpc: 'https://polygon-rpc.com',
            explorer: 'https://polygonscan.com',
            contracts: {
                tokenSale: '0x0000000000000000000000000000000000000000',
                token: '0x0000000000000000000000000000000000000000',
                priceOracle: '0x0000000000000000000000000000000000000000'
            }
        },
        31337: {
            name: 'Hardhat Local',
            rpc: 'http://127.0.0.1:8545',
            explorer: 'http://localhost:8545',
            contracts: {
                tokenSale: '0x0000000000000000000000000000000000000000',
                token: '0x0000000000000000000000000000000000000000',
                priceOracle: '0x0000000000000000000000000000000000000000'
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
}