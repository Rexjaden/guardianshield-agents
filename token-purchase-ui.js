/**
 * Token Purchase UI Setup
 * Handles the frontend interface for buying Guardian tokens
 */

function setupTokenPurchaseUI() {
    createTokenPurchaseHTML();
    setupEventListeners();
    updateSaleInfo();
    
    // Update sale info every 30 seconds
    setInterval(updateSaleInfo, 30000);
}

function createTokenPurchaseHTML() {
    const existingContainer = document.getElementById('tokenPurchaseContainer');
    if (existingContainer) return; // Already exists
    
    const container = document.createElement('div');
    container.id = 'tokenPurchaseContainer';
    container.innerHTML = `
        <div class="token-sale-widget">
            <div class="widget-header">
                <h2><i class="fas fa-coins"></i> Guardian Token Sale</h2>
                <div class="sale-status" id="saleStatus">
                    <span class="status-indicator"></span>
                    <span class="status-text">Loading...</span>
                </div>
            </div>
            
            <div class="wallet-section">
                <button id="connectWallet" class="connect-wallet-btn">
                    <i class="fas fa-wallet"></i>
                    Connect Wallet
                </button>
                <div id="walletInfo" class="wallet-info" style="display: none;">
                    <!-- Wallet info will be populated here -->
                </div>
            </div>
            
            <div class="sale-info-section" id="saleInfoSection">
                <div class="sale-stage" id="saleStage">
                    <h3>Current Stage: <span id="stageName">Loading...</span></h3>
                    <div class="stage-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" id="progressFill" style="width: 0%"></div>
                        </div>
                        <div class="progress-stats">
                            <span id="soldTokens">0</span> / <span id="maxTokens">0</span> GUARD sold
                        </div>
                    </div>
                </div>
                
                <div class="price-info">
                    <div class="current-price">
                        <span class="label">Current Price:</span>
                        <span class="price" id="currentPrice">0 ETH</span>
                    </div>
                    <div class="next-stage" id="nextStageInfo" style="display: none;">
                        <span class="label">Next Stage Price:</span>
                        <span class="price" id="nextPrice">0 ETH</span>
                    </div>
                </div>
            </div>
            
            <div class="purchase-section">
                <div class="input-group">
                    <label for="ethAmount">ETH Amount</label>
                    <div class="input-wrapper">
                        <input type="number" id="ethAmount" placeholder="0.1" min="0" step="0.001">
                        <span class="input-suffix">ETH</span>
                    </div>
                </div>
                
                <div class="token-calculation">
                    <div class="calculation-result">
                        You will receive: <span id="calculatedTokens">0</span> GUARD
                    </div>
                </div>
                
                <div class="referral-section">
                    <label for="referralAddress">Referral Address (Optional)</label>
                    <input type="text" id="referralAddress" placeholder="0x... (5% bonus for referrer)">
                </div>
                
                <button id="buyTokensBtn" class="buy-tokens-btn" disabled>
                    <i class="fas fa-shopping-cart"></i>
                    Buy Tokens
                </button>
                
                <div class="purchase-summary" id="purchaseSummary" style="display: none;">
                    <h4>Your Purchase History</h4>
                    <div id="purchaseStats">
                        <!-- Purchase stats will be populated here -->
                    </div>
                </div>
            </div>
            
            <div class="balance-section" id="balanceSection" style="display: none;">
                <h4>Your Balances</h4>
                <div class="balance-grid">
                    <div class="balance-item">
                        <span class="balance-label">ETH:</span>
                        <span class="balance-value" id="ethBalance">0</span>
                    </div>
                    <div class="balance-item">
                        <span class="balance-label">GUARD:</span>
                        <span class="balance-value" id="guardBalance">0</span>
                    </div>
                </div>
            </div>
            
            <div class="widget-footer">
                <div class="security-note">
                    <i class="fas fa-shield-alt"></i>
                    Secured by GuardianShield Smart Contracts
                </div>
            </div>
        </div>
    `;
    
    // Add the widget to the page
    document.body.appendChild(container);
}

function setupEventListeners() {
    // Connect wallet button
    const connectBtn = document.getElementById('connectWallet');
    connectBtn.addEventListener('click', async () => {
        try {
            await guardianWeb3.connectWallet();
        } catch (error) {
            console.error('Wallet connection failed:', error);
        }
    });
    
    // ETH amount input
    const ethAmountInput = document.getElementById('ethAmount');
    ethAmountInput.addEventListener('input', calculateTokens);
    
    // Buy tokens button
    const buyBtn = document.getElementById('buyTokensBtn');
    buyBtn.addEventListener('click', handleTokenPurchase);
    
    // Enable/disable buy button based on wallet connection
    updateBuyButtonState();
}

async function updateSaleInfo() {
    try {
        if (!guardianWeb3 || !guardianWeb3.contracts.guardianTokenSale) {
            return;
        }
        
        const saleInfo = await guardianWeb3.getSaleInfo();
        
        if (saleInfo) {
            // Update stage name
            document.getElementById('stageName').textContent = saleInfo.stageName;
            
            // Update progress
            const progress = (saleInfo.soldTokens / saleInfo.maxTokens) * 100;
            document.getElementById('progressFill').style.width = `${progress}%`;
            
            // Update sold/max tokens
            document.getElementById('soldTokens').textContent = formatTokenAmount(saleInfo.soldTokens);
            document.getElementById('maxTokens').textContent = formatTokenAmount(saleInfo.maxTokens);
            
            // Update current price
            const priceInEth = ethers.utils.formatEther(saleInfo.price);
            document.getElementById('currentPrice').textContent = `${priceInEth} ETH`;
            
            // Update sale status
            const statusElement = document.getElementById('saleStatus');
            if (saleInfo.active) {
                statusElement.innerHTML = `
                    <span class="status-indicator active"></span>
                    <span class="status-text">Active</span>
                `;
            } else {
                statusElement.innerHTML = `
                    <span class="status-indicator inactive"></span>
                    <span class="status-text">Ended</span>
                `;
            }
            
            // Update buy button state
            updateBuyButtonState(saleInfo.active);
        }
    } catch (error) {
        console.error('Failed to update sale info:', error);
    }
}

async function calculateTokens() {
    const ethAmountInput = document.getElementById('ethAmount');
    const calculatedTokensSpan = document.getElementById('calculatedTokens');
    
    const ethAmount = parseFloat(ethAmountInput.value) || 0;
    
    if (ethAmount <= 0) {
        calculatedTokensSpan.textContent = '0';
        return;
    }
    
    try {
        if (guardianWeb3 && guardianWeb3.contracts.guardianTokenSale) {
            const tokens = await guardianWeb3.calculateTokensForEth(ethAmount);
            calculatedTokensSpan.textContent = formatTokenAmount(tokens);
        }
    } catch (error) {
        console.error('Failed to calculate tokens:', error);
        calculatedTokensSpan.textContent = '0';
    }
}

async function handleTokenPurchase() {
    const ethAmount = parseFloat(document.getElementById('ethAmount').value);
    const referralAddress = document.getElementById('referralAddress').value.trim();
    
    if (!ethAmount || ethAmount <= 0) {
        guardianWeb3.showNotification('Please enter a valid ETH amount', 'error');
        return;
    }
    
    if (!guardianWeb3.isConnected) {
        guardianWeb3.showNotification('Please connect your wallet first', 'error');
        return;
    }
    
    try {
        // Validate referral address if provided
        let referrer = null;
        if (referralAddress) {
            if (ethers.utils.isAddress(referralAddress)) {
                referrer = referralAddress;
            } else {
                guardianWeb3.showNotification('Invalid referral address', 'error');
                return;
            }
        }
        
        // Disable buy button during purchase
        const buyBtn = document.getElementById('buyTokensBtn');
        const originalText = buyBtn.innerHTML;
        buyBtn.disabled = true;
        buyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        
        // Execute purchase
        await guardianWeb3.buyTokens(ethAmount, referrer);
        
        // Clear form
        document.getElementById('ethAmount').value = '';
        document.getElementById('referralAddress').value = '';
        
        // Update UI
        await updateSaleInfo();
        document.getElementById('calculatedTokens').textContent = '0';
        
        // Show purchase summary
        document.getElementById('purchaseSummary').style.display = 'block';
        
    } catch (error) {
        console.error('Purchase failed:', error);
    } finally {
        // Re-enable buy button
        const buyBtn = document.getElementById('buyTokensBtn');
        buyBtn.disabled = false;
        buyBtn.innerHTML = originalText;
    }
}

function updateBuyButtonState(saleActive = true) {
    const buyBtn = document.getElementById('buyTokensBtn');
    const ethAmount = parseFloat(document.getElementById('ethAmount').value) || 0;
    
    if (!guardianWeb3.isConnected) {
        buyBtn.disabled = true;
        buyBtn.innerHTML = '<i class="fas fa-wallet"></i> Connect Wallet First';
    } else if (!saleActive) {
        buyBtn.disabled = true;
        buyBtn.innerHTML = '<i class="fas fa-lock"></i> Sale Ended';
    } else if (ethAmount <= 0) {
        buyBtn.disabled = true;
        buyBtn.innerHTML = '<i class="fas fa-shopping-cart"></i> Enter ETH Amount';
    } else {
        buyBtn.disabled = false;
        buyBtn.innerHTML = '<i class="fas fa-shopping-cart"></i> Buy Tokens';
    }
}

function formatTokenAmount(amount) {
    const num = typeof amount === 'string' ? parseFloat(amount) : amount;
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toFixed(2);
}

// Utility function to add the token sale widget to any page
function addTokenSaleWidget(containerId) {
    const container = document.getElementById(containerId);
    if (container && !document.getElementById('tokenPurchaseContainer')) {
        setupTokenPurchaseUI();
        const widget = document.getElementById('tokenPurchaseContainer');
        container.appendChild(widget);
    }
}