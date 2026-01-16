// Web3 Wallet Authentication JavaScript Policy
// Validates Ethereum wallet signatures for SHIELD Token purchases

var ethUtil = require('ethereumjs-util');
var crypto = require('crypto');

try {
    // Get request headers
    var walletAddress = context.getVariable("request.header.x-wallet-address");
    var signature = context.getVariable("request.header.x-wallet-signature");
    var message = context.getVariable("request.header.x-signed-message");
    var timestamp = context.getVariable("request.header.x-timestamp");
    
    // Validate required headers
    if (!walletAddress || !signature || !message) {
        context.setVariable("auth.error", "Missing required Web3 authentication headers");
        context.setVariable("auth.success", false);
        throw new Error("Web3 authentication failed: Missing headers");
    }
    
    // Check timestamp to prevent replay attacks (5 minute window)
    var currentTime = Date.now();
    var messageTime = parseInt(timestamp);
    var timeDiff = Math.abs(currentTime - messageTime);
    
    if (timeDiff > 300000) { // 5 minutes in milliseconds
        context.setVariable("auth.error", "Request timestamp too old");
        context.setVariable("auth.success", false);
        throw new Error("Web3 authentication failed: Expired timestamp");
    }
    
    // Prepare message for signature verification
    var messageBuffer = Buffer.from(message, 'utf8');
    var prefixedMessage = '\u0019Ethereum Signed Message:\n' + messageBuffer.length + message;
    var msgHash = ethUtil.keccak256(Buffer.from(prefixedMessage));
    
    // Parse signature
    var sigBuffer = Buffer.from(signature.substring(2), 'hex');
    var r = sigBuffer.slice(0, 32);
    var s = sigBuffer.slice(32, 64);
    var v = sigBuffer[64];
    
    // Recover public key
    var publicKey = ethUtil.ecrecover(msgHash, v, r, s);
    var recoveredAddress = ethUtil.publicToAddress(publicKey);
    var addressHex = '0x' + recoveredAddress.toString('hex');
    
    // Verify address matches
    if (addressHex.toLowerCase() !== walletAddress.toLowerCase()) {
        context.setVariable("auth.error", "Wallet signature verification failed");
        context.setVariable("auth.success", false);
        throw new Error("Web3 authentication failed: Invalid signature");
    }
    
    // Authentication successful
    context.setVariable("auth.success", true);
    context.setVariable("wallet.address", walletAddress.toLowerCase());
    context.setVariable("wallet.verified", true);
    context.setVariable("auth.method", "web3_signature");
    
    // Generate session token for subsequent requests
    var sessionToken = crypto.randomBytes(32).toString('hex');
    context.setVariable("session.token", sessionToken);
    
    // Log successful authentication
    context.setVariable("analytics.event", "web3_auth_success");
    context.setVariable("analytics.wallet_address", walletAddress.toLowerCase());
    context.setVariable("analytics.timestamp", currentTime);
    
} catch (error) {
    // Log authentication failure
    context.setVariable("auth.success", false);
    context.setVariable("auth.error", error.message);
    context.setVariable("analytics.event", "web3_auth_failure");
    context.setVariable("analytics.error", error.message);
    
    // Return authentication error response
    context.setVariable("response.status.code", 401);
    context.setVariable("response.content", JSON.stringify({
        error: "Authentication failed",
        message: "Web3 wallet signature verification failed"
    }));
    context.setVariable("response.header.Content-Type", "application/json");
}