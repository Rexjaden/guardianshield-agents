# Multi-Wallet Integration Guide

## Overview
Your GuardianShield token sale now supports multiple wallet providers:
- **MetaMask** - Most popular browser wallet
- **Coinbase Wallet** - Major exchange wallet
- **Trust Wallet** - Mobile-first wallet
- **WalletConnect** - Universal wallet protocol
- **Generic Ethereum** - Any other Web3 wallet

## Quick Integration Steps

### 1. Add Required Scripts to Your HTML

```html
<!-- Ethers.js for Web3 interaction -->
<script src="https://cdn.ethers.io/lib/ethers-5.7.2.umd.min.js"></script>

<!-- WalletConnect Provider (Optional but recommended) -->
<script src="https://unpkg.com/@walletconnect/web3-provider@1.8.0/dist/umd/index.min.js"></script>

<!-- GuardianShield Web3 Integration -->
<script src="web3-integration.js"></script>
<script src="token-purchase-ui.js"></script>

<!-- Styling -->
<link rel="stylesheet" href="token-sale-styles.css">
```

### 2. Add Token Sale Widget to Any Page

```html
<!-- Add this div where you want the widget -->
<div id="tokenSaleContainer"></div>

<script>
document.addEventListener('DOMContentLoaded', () => {
    // Initialize the widget
    addTokenSaleWidget('tokenSaleContainer');
    
    // Set contract addresses after deployment
    const contractAddresses = {
        guardianToken: '0x...', // Your deployed token address
        guardianTokenSale: '0x...', // Your deployed sale address
        guardianShieldToken: '0x...', // Your deployed NFT address
        guardianStaking: '0x...', // Your deployed staking address
    };
    
    if (guardianWeb3) {
        guardianWeb3.setAddresses(contractAddresses);
    }
});
</script>
```

### 3. Integrate with Existing Frontend

To add the token sale widget to your existing GuardianShield frontend:

```html
<!-- In your condensed-frontend.html, add this section after the features -->
<section class="token-sale-section">
    <div class="container">
        <h2 style="text-align: center; margin-bottom: 2rem; color: #4CAF50;">
            <i class="fas fa-coins"></i> Guardian Token Sale
        </h2>
        <div id="tokenSaleContainer"></div>
    </div>
</section>
```

## Key Features

### ✅ Automatic Wallet Detection
- Scans for available wallets on page load
- Shows appropriate connection options
- Fallback to generic Web3 provider

### ✅ Smart Wallet Selection
- Modal popup with available wallets
- User-friendly interface
- Visual wallet icons and branding

### ✅ Enhanced User Experience
- Shows connected wallet name/type
- Easy disconnect functionality
- Real-time balance updates
- Transaction status tracking

### ✅ WalletConnect Support
- QR code scanning for mobile wallets
- Supports 100+ mobile wallets
- Secure bridge connection

## Advanced Configuration

### Custom Wallet Detection
```javascript
// Add custom wallet detection
guardianWeb3.detectWallets = function() {
    const wallets = [];
    
    // Your custom wallet detection logic
    if (window.myCustomWallet) {
        wallets.push({
            id: 'custom',
            name: 'My Custom Wallet',
            icon: 'fas fa-custom-icon',
            provider: window.myCustomWallet
        });
    }
    
    return [...wallets, ...this.detectWallets()];
};
```

### WalletConnect Configuration
```javascript
// Configure WalletConnect with your Infura project ID
const wcConfig = {
    infuraId: "YOUR_INFURA_PROJECT_ID",
    rpc: {
        1: "https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID",
        11155111: "https://sepolia.infura.io/v3/YOUR_INFURA_PROJECT_ID"
    }
};
```

## Wallet-Specific Features

### MetaMask
- Network switching
- Account switching detection
- Chain change handling

### Coinbase Wallet
- Mobile app integration
- Desktop browser support
- Enterprise features

### WalletConnect
- Mobile wallet scanning
- Deep linking support
- Session management

### Trust Wallet
- Mobile-first design
- DApp browser integration
- Multi-chain support

## Testing Checklist

- [ ] MetaMask connection works
- [ ] Coinbase Wallet connection works
- [ ] WalletConnect QR code appears
- [ ] Wallet selection modal displays properly
- [ ] Token purchase flow completes
- [ ] Balance updates correctly
- [ ] Disconnect functionality works
- [ ] Mobile responsive design
- [ ] Error handling works properly

## Troubleshooting

### Common Issues

1. **"No wallet found" error**
   - Ensure user has at least one Web3 wallet installed
   - Check browser compatibility

2. **WalletConnect not working**
   - Verify WalletConnect script is loaded
   - Check Infura project ID configuration

3. **Connection fails**
   - Check network configuration
   - Verify contract addresses are correct
   - Ensure wallet is on correct network

### Debug Mode
```javascript
// Enable debug logging
guardianWeb3.debug = true;
```

## Security Notes

- Always verify contract addresses on Etherscan
- Use HTTPS for production deployments
- Implement proper error handling
- Test on testnets before mainnet deployment
- Keep wallet libraries updated

## Next Steps

1. Deploy smart contracts to testnet
2. Update contract addresses in the code
3. Test with multiple wallet types
4. Deploy to production
5. Monitor user adoption and feedback