// GuardianShield Web3 Integration Library
// Supports multiple wallets: MetaMask, WalletConnect, Coinbase Wallet, Trust Wallet

class GuardianWalletManager {
    constructor(options = {}) {
        this.web3 = null;
        this.currentAccount = null;
        this.networkId = null;
        this.contracts = {};
        this.walletProvider = null;
        this.supportedNetworks = {
            1: { name: 'Ethereum Mainnet', rpc: 'https://mainnet.infura.io/v3/' },
            11155111: { name: 'Sepolia Testnet', rpc: 'https://sepolia.infura.io/v3/' },
            137: { name: 'Polygon Mainnet', rpc: 'https://polygon-rpc.com' },
            56: { name: 'BSC Mainnet', rpc: 'https://bsc-dataseed1.binance.org' },
            42161: { name: 'Arbitrum One', rpc: 'https://arb1.arbitrum.io/rpc' }
        };
        
        this.contractAddresses = {
            1: { // Mainnet
                tokenSale: '0x0000000000000000000000000000000000000000',
                token: '0x0000000000000000000000000000000000000000',
                priceOracle: '0x0000000000000000000000000000000000000000'
            },
            11155111: { // Sepolia
                tokenSale: '0x0000000000000000000000000000000000000000',
                token: '0x0000000000000000000000000000000000000000',
                priceOracle: '0x0000000000000000000000000000000000000000'
            },
            137: { // Polygon
                tokenSale: '0x0000000000000000000000000000000000000000',
                token: '0x0000000000000000000000000000000000000000',
                priceOracle: '0x0000000000000000000000000000000000000000'
            },
            31337: { // Hardhat Local
                tokenSale: '0x0000000000000000000000000000000000000000',
                token: '0x0000000000000000000000000000000000000000',
                priceOracle: '0x0000000000000000000000000000000000000000'
            }
        };
        
        this.eventCallbacks = {
            connected: [],
            disconnected: [],
            accountChanged: [],
            networkChanged: [],
            error: []
        };
        
        this.init();
    }
    
    init() {
        this.detectWallets();
        this.setupEventListeners();
    }
    
    detectWallets() {
        const wallets = [];
        
        // MetaMask
        if (typeof window.ethereum !== 'undefined' && window.ethereum.isMetaMask) {
            wallets.push({
                name: 'MetaMask',
                icon: '🦊',
                provider: window.ethereum,
                type: 'injected'
            });
        }
        
        // Coinbase Wallet
        if (typeof window.ethereum !== 'undefined' && window.ethereum.isCoinbaseWallet) {
            wallets.push({
                name: 'Coinbase Wallet',
                icon: '🔷',
                provider: window.ethereum,
                type: 'injected'
            });
        }
        
        // Trust Wallet
        if (typeof window.ethereum !== 'undefined' && window.ethereum.isTrust) {
            wallets.push({
                name: 'Trust Wallet',
                icon: '🛡️',
                provider: window.ethereum,
                type: 'injected'
            });
        }
        
        // WalletConnect (always available)
        wallets.push({
            name: 'WalletConnect',
            icon: '📱',
            provider: null,
            type: 'walletconnect'
        });
        
        this.availableWallets = wallets;
    }
    
    async connectWallet(walletType = 'auto') {
        try {
            if (walletType === 'auto') {
                walletType = this.availableWallets[0]?.type || 'injected';
            }
            
            if (walletType === 'injected') {
                return await this.connectInjectedWallet();
            } else if (walletType === 'walletconnect') {
                return await this.connectWalletConnect();
            }
        } catch (error) {
            this.emitEvent('error', error);
            throw error;
        }
    }
    
    async connectInjectedWallet() {
        if (typeof window.ethereum === 'undefined') {
            throw new Error('No injected wallet found. Please install MetaMask.');
        }
        
        this.walletProvider = window.ethereum;
        this.web3 = new Web3(window.ethereum);
        
        // Request account access
        const accounts = await window.ethereum.request({
            method: 'eth_requestAccounts',
        });
        
        if (accounts.length === 0) {
            throw new Error('No accounts found');
        }
        
        this.currentAccount = accounts[0];
        this.networkId = await this.web3.eth.net.getId();
        
        // Initialize contracts
        await this.initializeContracts();
        
        // Save connection state
        localStorage.setItem('guardianWalletConnected', 'true');
        localStorage.setItem('guardianWalletType', 'injected');
        
        this.emitEvent('connected', {
            account: this.currentAccount,
            network: this.networkId,
            provider: 'injected'
        });
        
        return {
            account: this.currentAccount,
            network: this.networkId,
            balance: await this.getBalance()
        };
    }
    
    async connectWalletConnect() {
        try {
            const WalletConnectProvider = window.WalletConnect?.default || window.WalletConnectProvider;
            
            if (!WalletConnectProvider) {
                throw new Error('WalletConnect not available');
            }
            
            const provider = new WalletConnectProvider({
                rpc: {
                    1: this.supportedNetworks[1].rpc + process.env.INFURA_PROJECT_ID,
                    137: this.supportedNetworks[137].rpc,
                    56: this.supportedNetworks[56].rpc
                },
                chainId: 1,
                qrcodeModal: window.WalletConnectQRCodeModal?.default
            });
            
            await provider.enable();
            
            this.walletProvider = provider;
            this.web3 = new Web3(provider);
            
            const accounts = await this.web3.eth.getAccounts();
            this.currentAccount = accounts[0];
            this.networkId = await this.web3.eth.net.getId();
            
            // Initialize contracts
            await this.initializeContracts();
            
            // Save connection state
            localStorage.setItem('guardianWalletConnected', 'true');
            localStorage.setItem('guardianWalletType', 'walletconnect');
            
            this.emitEvent('connected', {
                account: this.currentAccount,
                network: this.networkId,
                provider: 'walletconnect'
            });
            
            return {
                account: this.currentAccount,
                network: this.networkId,
                balance: await this.getBalance()
            };
            
        } catch (error) {
            console.error('WalletConnect connection failed:', error);
            throw new Error('Failed to connect with WalletConnect');
        }
    }
    
    async disconnect() {
        if (this.walletProvider && this.walletProvider.disconnect) {
            await this.walletProvider.disconnect();
        }
        
        this.web3 = null;
        this.currentAccount = null;
        this.networkId = null;
        this.contracts = {};
        this.walletProvider = null;
        
        localStorage.removeItem('guardianWalletConnected');
        localStorage.removeItem('guardianWalletType');
        
        this.emitEvent('disconnected');
    }
    
    async initializeContracts() {
        if (!this.networkId || !this.contractAddresses[this.networkId]) {
            console.warn('Contracts not available for network:', this.networkId);
            return;
        }
        
        const addresses = this.contractAddresses[this.networkId];
        
        // Token Sale Contract
        if (addresses.tokenSale !== '0x0000000000000000000000000000000000000000') {
            this.contracts.tokenSale = new this.web3.eth.Contract([
                "function getCurrentSaleInfo() view returns (uint256, string, uint256, uint256, uint256, uint256, bool, uint256, bool)",
                "function calculateTokens(uint256) view returns (uint256)",
                "function buyTokens(address) payable",
                "function buyTokensWithToken(address, uint256, address)",
                "function getTokenPriceInUsd(uint256) view returns (uint256)"
            ], addresses.tokenSale);
        }
        
        // Guardian Token Contract
        if (addresses.token !== '0x0000000000000000000000000000000000000000') {
            this.contracts.token = new this.web3.eth.Contract([
                "function name() view returns (string)",
                "function symbol() view returns (string)",
                "function decimals() view returns (uint8)",
                "function totalSupply() view returns (uint256)",
                "function balanceOf(address) view returns (uint256)",
                "function transfer(address, uint256) returns (bool)",
                "function allowance(address, address) view returns (uint256)",
                "function approve(address, uint256) returns (bool)"
            ], addresses.token);
        }
        
        // Price Oracle Contract
        if (addresses.priceOracle !== '0x0000000000000000000000000000000000000000') {
            this.contracts.priceOracle = new this.web3.eth.Contract([
                "function getLatestPrice() view returns (uint256, uint256, bool)",
                "function ethToUsd(uint256) view returns (uint256)",
                "function usdToEth(uint256) view returns (uint256)",
                "function isPriceFeedHealthy() view returns (bool, string)"
            ], addresses.priceOracle);
        }
    }
    
    setupEventListeners() {
        if (typeof window.ethereum !== 'undefined') {
            // Account changes
            window.ethereum.on('accountsChanged', (accounts) => {
                if (accounts.length === 0) {
                    this.disconnect();
                } else if (accounts[0] !== this.currentAccount) {
                    this.currentAccount = accounts[0];
                    this.emitEvent('accountChanged', accounts[0]);
                }
            });
            
            // Network changes
            window.ethereum.on('chainChanged', (chainId) => {
                const networkId = parseInt(chainId, 16);
                this.networkId = networkId;
                this.initializeContracts();
                this.emitEvent('networkChanged', networkId);
            });
            
            // Disconnection
            window.ethereum.on('disconnect', () => {
                this.disconnect();
            });
        }
    }
    
    async getBalance(address = null) {
        if (!this.web3) return '0';
        
        const account = address || this.currentAccount;
        if (!account) return '0';
        
        const balance = await this.web3.eth.getBalance(account);
        return this.web3.utils.fromWei(balance, 'ether');
    }
    
    async getTokenBalance(address = null) {
        if (!this.contracts.token) return '0';
        
        const account = address || this.currentAccount;
        if (!account) return '0';
        
        const balance = await this.contracts.token.methods.balanceOf(account).call();
        return this.web3.utils.fromWei(balance, 'ether');
    }
    
    async getSaleInfo() {
        if (!this.contracts.tokenSale) {
            throw new Error('Token sale contract not initialized');
        }
        
        const info = await this.contracts.tokenSale.methods.getCurrentSaleInfo().call();
        return {
            stage: info[0],
            stageName: info[1],
            priceInEth: this.web3.utils.fromWei(info[2], 'ether'),
            maxTokens: this.web3.utils.fromWei(info[3], 'ether'),
            soldTokens: this.web3.utils.fromWei(info[4], 'ether'),
            remainingTokens: this.web3.utils.fromWei(info[5], 'ether'),
            active: info[6],
            priceInUsd: info.length > 7 ? this.web3.utils.fromWei(info[7], 'ether') : '0',
            oracleActive: info.length > 8 ? info[8] : false
        };
    }
    
    async calculateTokensForEth(ethAmount) {
        if (!this.contracts.tokenSale) {
            throw new Error('Token sale contract not initialized');
        }
        
        const amountWei = this.web3.utils.toWei(ethAmount.toString(), 'ether');
        const tokens = await this.contracts.tokenSale.methods.calculateTokens(amountWei).call();
        return this.web3.utils.fromWei(tokens, 'ether');
    }
    
    async purchaseTokensWithEth(ethAmount, referralAddress = '0x0000000000000000000000000000000000000000') {
        if (!this.contracts.tokenSale || !this.currentAccount) {
            throw new Error('Wallet not connected or contract not initialized');
        }
        
        const amountWei = this.web3.utils.toWei(ethAmount.toString(), 'ether');
        
        const tx = await this.contracts.tokenSale.methods.buyTokens(referralAddress).send({
            from: this.currentAccount,
            value: amountWei
        });
        
        return tx;
    }
    
    async getCurrentEthPrice() {
        if (!this.contracts.priceOracle) {
            return { price: 3000, timestamp: Date.now(), success: false };
        }
        
        try {
            const result = await this.contracts.priceOracle.methods.getLatestPrice().call();
            return {
                price: Number(result[0]) / 1e8, // Convert from 8 decimals
                timestamp: Number(result[1]) * 1000, // Convert to milliseconds
                success: result[2]
            };
        } catch (error) {
            return { price: 3000, timestamp: Date.now(), success: false };
        }
    }
    
    async switchNetwork(networkId) {
        if (!this.walletProvider || !this.walletProvider.request) {
            throw new Error('Cannot switch network with current provider');
        }
        
        const network = this.supportedNetworks[networkId];
        if (!network) {
            throw new Error('Unsupported network');
        }
        
        try {
            await this.walletProvider.request({
                method: 'wallet_switchEthereumChain',
                params: [{ chainId: '0x' + networkId.toString(16) }],
            });
        } catch (switchError) {
            // This error code indicates that the chain has not been added to MetaMask
            if (switchError.code === 4902) {
                await this.addNetwork(networkId);
            } else {
                throw switchError;
            }
        }
    }
    
    async addNetwork(networkId) {
        const network = this.supportedNetworks[networkId];
        if (!network || !this.walletProvider) return;
        
        const chainConfig = {
            chainId: '0x' + networkId.toString(16),
            chainName: network.name,
            rpcUrls: [network.rpc],
            nativeCurrency: {
                name: networkId === 137 ? 'MATIC' : 'ETH',
                symbol: networkId === 137 ? 'MATIC' : 'ETH',
                decimals: 18
            }
        };
        
        await this.walletProvider.request({
            method: 'wallet_addEthereumChain',
            params: [chainConfig]
        });
    }
    
    // Event system
    on(eventName, callback) {
        if (this.eventCallbacks[eventName]) {
            this.eventCallbacks[eventName].push(callback);
        }
    }
    
    off(eventName, callback) {
        if (this.eventCallbacks[eventName]) {
            const index = this.eventCallbacks[eventName].indexOf(callback);
            if (index > -1) {
                this.eventCallbacks[eventName].splice(index, 1);
            }
        }
    }
    
    emitEvent(eventName, data = null) {
        if (this.eventCallbacks[eventName]) {
            this.eventCallbacks[eventName].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error('Event callback error:', error);
                }
            });
        }
    }
    
    // Utility methods
    isConnected() {
        return !!(this.currentAccount && this.web3);
    }
    
    getShortAddress(address = null) {
        const addr = address || this.currentAccount;
        if (!addr) return '';
        return addr.slice(0, 6) + '...' + addr.slice(-4);
    }
    
    getNetworkName(networkId = null) {
        const id = networkId || this.networkId;
        return this.supportedNetworks[id]?.name || `Network ${id}`;
    }
    
    // Auto-reconnect on page load
    async tryAutoReconnect() {
        if (localStorage.getItem('guardianWalletConnected') === 'true') {
            const walletType = localStorage.getItem('guardianWalletType') || 'injected';
            try {
                await this.connectWallet(walletType);
                return true;
            } catch (error) {
                console.warn('Auto-reconnect failed:', error);
                localStorage.removeItem('guardianWalletConnected');
                localStorage.removeItem('guardianWalletType');
                return false;
            }
        }
        return false;
    }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GuardianWalletManager;
} else {
    window.GuardianWalletManager = GuardianWalletManager;
}