/**
 * GuardianShield Web3 Integration
 * Connects the frontend to smart contracts for token sales and interactions
 */

class GuardianWeb3 {
    constructor() {
        this.provider = null;
        this.signer = null;
        this.contracts = {};
        this.isConnected = false;
        
        // Contract addresses (will be populated after deployment)
        this.addresses = {
            guardianToken: '',
            guardianTokenSale: '',
            guardianShieldToken: '',
            guardianStaking: '',
            guardianLiquidityPool: ''
        };
        
        // Contract ABIs (simplified for main functions)
        this.abis = {
            guardianToken: [
                "function name() view returns (string)",
                "function symbol() view returns (string)",
                "function balanceOf(address) view returns (uint256)",
                "function transfer(address to, uint256 amount) returns (bool)",
                "function approve(address spender, uint256 amount) returns (bool)"
            ],
            guardianTokenSale: [
                "function buyTokens(address referrer) payable",
                "function buyTokensWithToken(address token, uint256 amount, address referrer)",
                "function getCurrentSaleInfo() view returns (uint256, string, uint256, uint256, uint256, uint256, bool)",
                "function calculateTokens(uint256 ethAmount) view returns (uint256)",
                "function purchasedTokens(address) view returns (uint256)",
                "function totalContributed(address) view returns (uint256)"
            ],
            guardianShieldToken: [
                "function mintWithSerial(address to, uint256 serial, string uri)",
                "function balanceOf(address) view returns (uint256)",
                "function tokenOfOwnerByIndex(address owner, uint256 index) view returns (uint256)"
            ]
        };
        
        this.init();
    }
    
    async init() {
        this.availableWallets = this.detectWallets();
        console.log('Available wallets:', this.availableWallets);
        
        // Set up event listeners if any wallet is available
        if (this.availableWallets.length > 0) {
            this.setupWalletEventListeners();
        }
    }
    
    detectWallets() {
        const wallets = [];
        
        // MetaMask
        if (typeof window.ethereum !== 'undefined' && window.ethereum.isMetaMask) {
            wallets.push({
                id: 'metamask',
                name: 'MetaMask',
                icon: 'fab fa-firefox-browser',
                provider: window.ethereum
            });
        }
        
        // Coinbase Wallet
        if (typeof window.ethereum !== 'undefined' && window.ethereum.isCoinbaseWallet) {
            wallets.push({
                id: 'coinbase',
                name: 'Coinbase Wallet',
                icon: 'fab fa-bitcoin',
                provider: window.ethereum
            });
        }
        
        // Trust Wallet
        if (typeof window.ethereum !== 'undefined' && window.ethereum.isTrust) {
            wallets.push({
                id: 'trust',
                name: 'Trust Wallet',
                icon: 'fas fa-shield-alt',
                provider: window.ethereum
            });
        }
        
        // Generic Ethereum provider (fallback)
        if (typeof window.ethereum !== 'undefined' && wallets.length === 0) {
            wallets.push({
                id: 'ethereum',
                name: 'Ethereum Wallet',
                icon: 'fab fa-ethereum',
                provider: window.ethereum
            });
        }
        
        // WalletConnect (if available)
        if (typeof window.WalletConnect !== 'undefined') {
            wallets.push({
                id: 'walletconnect',
                name: 'WalletConnect',
                icon: 'fas fa-qrcode',
                provider: null // Will be initialized on connect
            });
        }
        
        return wallets;
    }
    
    setupWalletEventListeners() {
        if (window.ethereum) {
            // Listen for account changes
            window.ethereum.on('accountsChanged', (accounts) => {
                if (accounts.length === 0) {
                    this.disconnect();
                } else {
                    this.connectWallet();
                }
            });
            
            // Listen for network changes
            window.ethereum.on('chainChanged', () => {
                window.location.reload();
            });
        }
    }
    
    async connectWallet(walletId = null) {
        try {
            if (this.availableWallets.length === 0) {
                throw new Error('No wallet found. Please install a Web3 wallet like MetaMask, Coinbase Wallet, or Trust Wallet.');
            }
            
            // If no specific wallet requested, show wallet selection
            if (!walletId) {
                this.showWalletSelection();
                return;
            }
            
            const selectedWallet = this.availableWallets.find(w => w.id === walletId);
            if (!selectedWallet) {
                throw new Error(`Wallet ${walletId} not found`);
            }
            
            console.log(`Connecting to ${selectedWallet.name}...`);
            this.selectedWallet = selectedWallet;
            
            // Handle different wallet types
            if (walletId === 'walletconnect') {
                await this.connectWalletConnect();
            } else {
                await this.connectEthereumWallet(selectedWallet);
            }
            
            return this.currentAddress;
        } catch (error) {
            console.error('Failed to connect wallet:', error);
            this.showNotification('Failed to connect wallet: ' + error.message, 'error');
            throw error;
        }
    }
    
    async connectEthereumWallet(wallet) {
        this.provider = new ethers.providers.Web3Provider(wallet.provider);
        
        // Request account access
        await wallet.provider.request({ method: 'eth_requestAccounts' });
        this.signer = this.provider.getSigner();
        const address = await this.signer.getAddress();
        
        this.isConnected = true;
        this.currentAddress = address;
        console.log(`${wallet.name} connected:`, address);
        
        // Update UI
        this.updateWalletUI(address, wallet.name);
        
        // Initialize contracts if addresses are set
        if (this.addresses.guardianToken) {
            await this.initializeContracts();
        }
    }
    
    async connectWalletConnect() {
        try {
            // Initialize WalletConnect provider
            const WalletConnectProvider = window.WalletConnectProvider?.default || window.WalletConnectProvider;
            
            if (!WalletConnectProvider) {
                throw new Error('WalletConnect not available');
            }
            
            const wcProvider = new WalletConnectProvider({
                infuraId: "your-infura-id", // Replace with actual Infura ID
                rpc: {
                    1: "https://mainnet.infura.io/v3/your-infura-id",
                    11155111: "https://sepolia.infura.io/v3/your-infura-id"
                }
            });
            
            await wcProvider.enable();
            
            this.provider = new ethers.providers.Web3Provider(wcProvider);
            this.signer = this.provider.getSigner();
            const address = await this.signer.getAddress();
            
            this.isConnected = true;
            this.currentAddress = address;
            this.selectedWallet = { id: 'walletconnect', name: 'WalletConnect' };
            
            console.log('WalletConnect connected:', address);
            this.updateWalletUI(address, 'WalletConnect');
            
            // Initialize contracts
            if (this.addresses.guardianToken) {
                await this.initializeContracts();
            }
        } catch (error) {
            console.error('WalletConnect connection failed:', error);
            throw error;
        }
    }
    
    async initializeContracts() {
        try {
            if (!this.signer) {
                throw new Error('Wallet not connected');
            }
            
            // Initialize contract instances
            this.contracts.guardianToken = new ethers.Contract(
                this.addresses.guardianToken,
                this.abis.guardianToken,
                this.signer
            );
            
            this.contracts.guardianTokenSale = new ethers.Contract(
                this.addresses.guardianTokenSale,
                this.abis.guardianTokenSale,
                this.signer
            );
            
            this.contracts.guardianShieldToken = new ethers.Contract(
                this.addresses.guardianShieldToken,
                this.abis.guardianShieldToken,
                this.signer
            );
            
            console.log('Contracts initialized');
            await this.updateBalances();
        } catch (error) {
            console.error('Failed to initialize contracts:', error);
        }
    }
    
    async buyTokens(ethAmount, referrer = null) {
        try {
            if (!this.contracts.guardianTokenSale) {
                throw new Error('Token sale contract not initialized');
            }
            
            const value = ethers.utils.parseEther(ethAmount.toString());
            const referrerAddress = referrer || ethers.constants.AddressZero;
            
            this.showNotification('Processing transaction...', 'info');
            
            const tx = await this.contracts.guardianTokenSale.buyTokens(referrerAddress, {
                value: value,
                gasLimit: 300000
            });
            
            this.showNotification('Transaction sent! Waiting for confirmation...', 'info');
            
            const receipt = await tx.wait();
            
            this.showNotification('Tokens purchased successfully!', 'success');
            await this.updateBalances();
            
            return receipt;
        } catch (error) {
            console.error('Token purchase failed:', error);
            this.showNotification('Token purchase failed: ' + error.message, 'error');
            throw error;
        }
    }
    
    async getSaleInfo() {
        try {
            if (!this.contracts.guardianTokenSale) {
                return null;
            }
            
            const saleInfo = await this.contracts.guardianTokenSale.getCurrentSaleInfo();
            
            return {
                stage: saleInfo[0].toNumber(),
                stageName: saleInfo[1],
                price: saleInfo[2],
                maxTokens: saleInfo[3],
                soldTokens: saleInfo[4],
                remainingTokens: saleInfo[5],
                active: saleInfo[6]
            };
        } catch (error) {
            console.error('Failed to get sale info:', error);
            return null;
        }
    }
    
    async calculateTokensForEth(ethAmount) {
        try {
            if (!this.contracts.guardianTokenSale) {
                return 0;
            }
            
            const value = ethers.utils.parseEther(ethAmount.toString());
            const tokens = await this.contracts.guardianTokenSale.calculateTokens(value);
            return ethers.utils.formatEther(tokens);
        } catch (error) {
            console.error('Failed to calculate tokens:', error);
            return 0;
        }
    }
    
    async updateBalances() {
        try {
            if (!this.signer || !this.contracts.guardianToken) {
                return;
            }
            
            const address = await this.signer.getAddress();
            
            // Get ETH balance
            const ethBalance = await this.provider.getBalance(address);
            const ethFormatted = ethers.utils.formatEther(ethBalance);
            
            // Get GUARD token balance
            const guardBalance = await this.contracts.guardianToken.balanceOf(address);
            const guardFormatted = ethers.utils.formatEther(guardBalance);
            
            // Get purchase history
            const purchased = await this.contracts.guardianTokenSale.purchasedTokens(address);
            const contributed = await this.contracts.guardianTokenSale.totalContributed(address);
            
            // Update UI
            this.updateBalanceUI({
                eth: ethFormatted,
                guard: guardFormatted,
                purchased: ethers.utils.formatEther(purchased),
                contributed: ethers.utils.formatEther(contributed)
            });
            
        } catch (error) {
            console.error('Failed to update balances:', error);
        }
    }
    
    updateWalletUI(address, walletName = 'Wallet') {
        const shortAddress = `${address.slice(0, 6)}...${address.slice(-4)}`;
        
        // Update connect button
        const connectBtn = document.getElementById('connectWallet');
        if (connectBtn) {
            connectBtn.innerHTML = `
                <i class="fas fa-wallet"></i>
                ${shortAddress}
            `;
            connectBtn.classList.add('connected');
        }
        
        // Show wallet info
        const walletInfo = document.getElementById('walletInfo');
        if (walletInfo) {
            walletInfo.style.display = 'block';
            walletInfo.innerHTML = `
                <div class="wallet-address">
                    <i class="${this.selectedWallet?.icon || 'fas fa-wallet'}"></i>
                    <div class="wallet-details">
                        <div class="wallet-name">${walletName}</div>
                        <div class="wallet-addr">${shortAddress}</div>
                    </div>
                    <button class="disconnect-btn" onclick="guardianWeb3.disconnect()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
        }
        
        // Hide wallet selection if shown
        const walletSelection = document.getElementById('walletSelection');
        if (walletSelection) {
            walletSelection.style.display = 'none';
        }
    }
    
    showWalletSelection() {
        let walletSelection = document.getElementById('walletSelection');
        
        if (!walletSelection) {
            walletSelection = document.createElement('div');
            walletSelection.id = 'walletSelection';
            walletSelection.className = 'wallet-selection-modal';
            document.body.appendChild(walletSelection);
        }
        
        const walletButtons = this.availableWallets.map(wallet => `
            <button class="wallet-option" onclick="guardianWeb3.connectWallet('${wallet.id}')">
                <i class="${wallet.icon}"></i>
                <span>${wallet.name}</span>
                <i class="fas fa-arrow-right"></i>
            </button>
        `).join('');
        
        walletSelection.innerHTML = `
            <div class="wallet-selection-content">
                <div class="wallet-selection-header">
                    <h3><i class="fas fa-wallet"></i> Connect Wallet</h3>
                    <button class="close-btn" onclick="guardianWeb3.closeWalletSelection()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="wallet-selection-body">
                    <p>Choose your preferred wallet to connect:</p>
                    <div class="wallet-options">
                        ${walletButtons}
                    </div>
                    <div class="wallet-selection-footer">
                        <small>Don't have a wallet? 
                            <a href="https://metamask.io" target="_blank">Get MetaMask</a>
                        </small>
                    </div>
                </div>
            </div>
            <div class="wallet-selection-overlay" onclick="guardianWeb3.closeWalletSelection()"></div>
        `;
        
        walletSelection.style.display = 'flex';
    }
    
    closeWalletSelection() {
        const walletSelection = document.getElementById('walletSelection');
        if (walletSelection) {
            walletSelection.style.display = 'none';
        }
    }
    
    updateBalanceUI(balances) {
        // Update ETH balance
        const ethBalance = document.getElementById('ethBalance');
        if (ethBalance) {
            ethBalance.textContent = parseFloat(balances.eth).toFixed(4);
        }
        
        // Update GUARD balance
        const guardBalance = document.getElementById('guardBalance');
        if (guardBalance) {
            guardBalance.textContent = parseFloat(balances.guard).toFixed(2);
        }
        
        // Update purchase stats
        const purchaseStats = document.getElementById('purchaseStats');
        if (purchaseStats) {
            purchaseStats.innerHTML = `
                <div class="stat-item">
                    <span>GUARD Purchased:</span>
                    <span>${parseFloat(balances.purchased).toFixed(2)}</span>
                </div>
                <div class="stat-item">
                    <span>ETH Contributed:</span>
                    <span>${parseFloat(balances.contributed).toFixed(4)}</span>
                </div>
            `;
        }
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${this.getNotificationIcon(type)}"></i>
                <span>${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
        
        // Add close button functionality
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => notification.remove());
    }
    
    getNotificationIcon(type) {
        switch (type) {
            case 'success': return 'check-circle';
            case 'error': return 'exclamation-triangle';
            case 'warning': return 'exclamation-circle';
            default: return 'info-circle';
        }
    }
    
    disconnect() {
        // Disconnect WalletConnect if active
        if (this.selectedWallet?.id === 'walletconnect' && this.provider?.provider?.disconnect) {
            this.provider.provider.disconnect();
        }
        
        this.isConnected = false;
        this.signer = null;
        this.contracts = {};
        this.selectedWallet = null;
        this.currentAddress = null;
        
        // Update UI
        const connectBtn = document.getElementById('connectWallet');
        if (connectBtn) {
            connectBtn.innerHTML = `
                <i class="fas fa-wallet"></i>
                Connect Wallet
            `;
            connectBtn.classList.remove('connected');
        }
        
        const walletInfo = document.getElementById('walletInfo');
        if (walletInfo) {
            walletInfo.style.display = 'none';
        }
        
        this.showNotification('Wallet disconnected', 'info');
    }
    
    // Set contract addresses after deployment
    setAddresses(addresses) {
        this.addresses = { ...this.addresses, ...addresses };
        
        // Initialize contracts if wallet is connected
        if (this.isConnected) {
            this.initializeContracts();
        }
    }
}

// Initialize Web3 when page loads
let guardianWeb3;

document.addEventListener('DOMContentLoaded', () => {
    guardianWeb3 = new GuardianWeb3();
    
    // Set up event listeners for token purchase form
    setupTokenPurchaseUI();
});