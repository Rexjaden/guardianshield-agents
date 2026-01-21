// GuardianShield Token Sale Logic with Web3Modal
// Contract Address: 0x5D4AFA1d429820a88198F3F237bf85a31BE06B71
// Token: Guard Token (GAR)
// Chain: Ethereum Mainnet

const GUARD_TOKEN_ADDRESS = "0x5D4AFA1d429820a88198F3F237bf85a31BE06B71";
const TOKEN_PRICE_USD = 0.005;

// Minimal ABI for the Guard Token Contract
const GUARD_TOKEN_ABI = [
    "function buyTokens() external payable",
    "function saleActive() view returns (bool)",
    "function getLatestEthUsdPrice() view returns (int256)",
    "function balanceOf(address account) view returns (uint256)",
    "function decimals() view returns (uint8)",
    "function symbol() view returns (string)",
    "event Transfer(address indexed from, address indexed to, uint256 value)"
];

let web3Modal;
let provider;
let signer;
let guardTokenContract;
let userAddress;

// Initialize Web3Modal
function initWeb3Modal() {
    try {
        console.log("Initializing Web3Modal...");
        
        // Robust check for UMD globals with optional chaining
        const Web3ModalClass = window.Web3Modal?.default || window.Web3Modal;
        const WalletConnectProviderClass = window.WalletConnectProvider?.default || window.WalletConnectProvider;
        const CoinbaseWalletSDKClass = window.CoinbaseWalletSDK?.default || window.CoinbaseWalletSDK;

        if (!Web3ModalClass) {
            console.error("Critical: Web3Modal library not loaded.");
            return;
        }

        const providerOptions = {};

        // Only add WalletConnect if library successfully loaded
        if (WalletConnectProviderClass) {
            providerOptions.walletconnect = {
                package: WalletConnectProviderClass,
                options: {
                    rpc: {
                        1: "https://eth-mainnet.public.blastapi.io"
                    }
                }
            };
        } else {
            console.warn("WalletConnect library not detected - skipping.");
        }

        // Only add Coinbase Wallet if library successfully loaded
        if (CoinbaseWalletSDKClass) {
            providerOptions.coinbasewallet = {
                package: CoinbaseWalletSDKClass,
                options: {
                    appName: "GuardianShield AI",
                    infuraId: null,
                    rpc: "https://eth-mainnet.public.blastapi.io",
                    chainId: 1,
                    darkMode: true
                }
            };
        } else {
            console.warn("Coinbase Wallet library not detected - skipping.");
        }

        web3Modal = new Web3ModalClass({
            cacheProvider: true,
            providerOptions, 
            theme: "dark",
            disableInjectedProvider: false
        });
        
        console.log("Web3Modal initialized successfully.");
    } catch (e) {
        console.error("Error in initWeb3Modal:", e);
    }
}

async function initTokenSale() {
    console.log("Token Sale Script Loaded");
    
    // Attempt init, but don't crash the UI setup if it fails
    initWeb3Modal();
    
    const connectBtn = document.getElementById('connect-wallet-btn');
    const buyBtn = document.getElementById('buy-tokens-btn');
    const ethInput = document.getElementById('eth-amount');

    if (!document.getElementById('token-sale-section')) {
        console.warn("Token sale section not found on page. Script might be running on wrong page.");
        return;
    }

    if (connectBtn) {
        // Reset button state
        connectBtn.innerText = "Connect Wallet";
        connectBtn.disabled = false;
        // Remove old listeners to be safe (though difficult without reference, assumption: fresh load)
        connectBtn.addEventListener('click', () => {
             console.log("Connect button clicked");
             connectWallet();
        });
    } else {
        console.error("Connect button not found!");
    }
    
    if (buyBtn) buyBtn.addEventListener('click', buyTokens);
    if (ethInput) ethInput.addEventListener('input', updateTokenEstimate);

    // Auto-connect if cached provider exists and web3Modal was init
    if (web3Modal && web3Modal.cachedProvider) {
        console.log("Found cached provider, auto-connecting...");
        connectWallet();
    }
}

async function connectWallet() {
    if (!web3Modal) {
        alert("Wallet library not initialized. Please reload the page.");
        return;
    }
    try {
        console.log("Opening Web3Modal...");
        const instance = await web3Modal.connect();
        
        provider = new ethers.providers.Web3Provider(instance);
        signer = provider.getSigner();
        userAddress = await signer.getAddress();
        
        const network = await provider.getNetwork();
        
        // Subscribe to accounts change
        instance.on("accountsChanged", (accounts) => {
            handleAccountsChanged(accounts);
        });

        // Subscribe to chainId change
        instance.on("chainChanged", (chainId) => {
            window.location.reload();
        });

        // Check if on Mainnet (ChainId 1)
        if (network.chainId !== 1) {
            alert("Please switch your wallet to Ethereum Mainnet to purchase tokens.");
            // Try to request switch (works for MetaMask, sometimes others)
            try {
                await instance.request({
                    method: 'wallet_switchEthereumChain',
                    params: [{ chainId: '0x1' }],
                });
            } catch (err) {
                console.warn("Could not auto-switch network", err);
            }
            // Continue anyway to show UI, but warn
        }

        guardTokenContract = new ethers.Contract(GUARD_TOKEN_ADDRESS, GUARD_TOKEN_ABI, signer);

        updateUIConnected();
        await updateBalance();

    } catch (error) {
        console.error("Connection error:", error);
    }
}

function handleAccountsChanged(accounts) {
    if (accounts.length === 0) {
        console.log('Please connect to wallet.');
        updateUIDisconnected();
    } else {
        userAddress = accounts[0];
        updateUIConnected();
        updateBalance();
    }
}

function updateUIConnected() {
    const connectBtn = document.getElementById('connect-wallet-btn');
    const buySection = document.getElementById('buy-section');
    
    connectBtn.innerText = `Connected: ${userAddress.substring(0, 6)}...${userAddress.substring(38)}`;
    connectBtn.classList.add('connected');
    
    if(buySection) buySection.classList.remove('hidden');
}

function updateUIDisconnected() {
    const connectBtn = document.getElementById('connect-wallet-btn');
    const buySection = document.getElementById('buy-section');
    
    connectBtn.innerText = "Connect Wallet";
    connectBtn.classList.remove('connected');
    
    if(buySection) buySection.classList.add('hidden');
    
    // Clear Web3Modal cache
    if(web3Modal) web3Modal.clearCachedProvider();
}

async function updateBalance() {
    try {
        if (!guardTokenContract) return;
        const balance = await guardTokenContract.balanceOf(userAddress);
        const formattedBalance = ethers.utils.formatEther(balance);
        
        const balanceDisplay = document.getElementById('user-token-balance');
        if (balanceDisplay) {
            balanceDisplay.innerText = `${parseFloat(formattedBalance).toFixed(2)} GAR`;
        }
    } catch (error) {
        console.error("Error fetching balance:", error);
    }
}

async function updateTokenEstimate() {
    const ethAmount = document.getElementById('eth-amount').value;
    const tokenOutput = document.getElementById('token-estimate');
    
    if (!ethAmount || parseFloat(ethAmount) <= 0) {
        tokenOutput.innerText = "0 GAR";
        return;
    }

    try {
        let ethPriceUsd = 2500; // Fallback default
        
        if (guardTokenContract && provider && (await provider.getNetwork()).chainId === 1) {
             try {
                const price = await guardTokenContract.getLatestEthUsdPrice();
                ethPriceUsd = price.toNumber() / 100000000; // 8 decimals
             } catch(e) {
                 console.warn("Contract read failed, using default price", e);
             }
        }

        const usdValue = parseFloat(ethAmount) * ethPriceUsd;
        const tokens = usdValue / TOKEN_PRICE_USD;
        
        tokenOutput.innerText = `${Math.floor(tokens).toLocaleString()} GAR`;
    } catch (error) {
        console.error("Error calculating estimate:", error);
    }
}

async function buyTokens() {
    const ethAmount = document.getElementById('eth-amount').value;
    const buyBtn = document.getElementById('buy-tokens-btn');
    const statusMsg = document.getElementById('transaction-status');
    
    if (!ethAmount || parseFloat(ethAmount) <= 0) {
        alert("Please enter a valid ETH amount");
        return;
    }

    try {
        buyBtn.disabled = true;
        buyBtn.innerText = "Processing...";
        statusMsg.innerText = "Initiating transaction...";
        statusMsg.className = "status-msg processing";

        const tx = await guardTokenContract.buyTokens({
            value: ethers.utils.parseEther(ethAmount)
        });

        statusMsg.innerText = "Transaction sent! Waiting for confirmation...";
        
        await tx.wait();
        
        statusMsg.innerText = "Purchase successful! Welcome to GuardianShield.";
        statusMsg.className = "status-msg success";
        
        updateBalance();
        document.getElementById('eth-amount').value = '';
        document.getElementById('token-estimate').innerText = '0 GAR';
    } catch (error) {
        console.error("Purchase error:", error);
        statusMsg.innerText = "Transaction failed: " + (error.reason || error.message);
        statusMsg.className = "status-msg error";
    } finally {
        buyBtn.disabled = false;
        buyBtn.innerText = "Buy GAR Tokens";
    }
}

// Initialize on load
window.addEventListener('load', initTokenSale);
