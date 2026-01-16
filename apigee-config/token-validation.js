// SHIELD Token Purchase Validation JavaScript Policy
// Validates token purchase requests and enforces business rules

try {
    // Get request data
    var tokenType = context.getVariable("request.header.x-token-type");
    var amountUSD = parseFloat(context.getVariable("request.header.x-amount-usd"));
    var walletAddress = context.getVariable("wallet.address");
    var paymentMethod = context.getVariable("request.header.x-payment-method");
    
    // Define token configurations
    var tokenConfig = {
        "GUARD": {
            name: "Guardian Token",
            symbol: "GUARD",
            minimumUSD: 0.005,
            maximumUSD: 10000,
            decimals: 18,
            contractAddress: "0x..." // To be set
        },
        "SHIELD": {
            name: "Shield Token", 
            symbol: "SHIELD",
            minimumUSD: 0.025,
            maximumUSD: 50000,
            decimals: 18,
            contractAddress: "0x..." // To be set
        }
    };
    
    // Validate token type
    if (!tokenType || !tokenConfig[tokenType]) {
        throw new Error("Invalid token type. Supported types: GUARD, SHIELD");
    }
    
    var token = tokenConfig[tokenType];
    
    // Validate amount
    if (isNaN(amountUSD) || amountUSD <= 0) {
        throw new Error("Invalid purchase amount");
    }
    
    // Check minimum purchase amount
    if (amountUSD < token.minimumUSD) {
        throw new Error(`Minimum purchase amount for ${token.name} is $${token.minimumUSD}`);
    }
    
    // Check maximum purchase amount
    if (amountUSD > token.maximumUSD) {
        throw new Error(`Maximum purchase amount for ${token.name} is $${token.maximumUSD}`);
    }
    
    // Validate wallet address
    if (!walletAddress || !walletAddress.match(/^0x[a-fA-F0-9]{40}$/)) {
        throw new Error("Valid wallet address required");
    }
    
    // Validate payment method
    var supportedMethods = ["metamask", "walletconnect", "coinbase", "trust"];
    if (!paymentMethod || supportedMethods.indexOf(paymentMethod.toLowerCase()) === -1) {
        throw new Error("Unsupported payment method");
    }
    
    // Check daily purchase limits (example: $1000 per wallet per day)
    var dailyLimit = 1000;
    var dailyPurchaseKey = "daily_purchase:" + walletAddress + ":" + new Date().toISOString().split('T')[0];
    // Note: In production, this would check against a database or cache
    
    // Calculate token amount based on current price
    // This would typically fetch from a price oracle
    var tokenPriceUSD = token.symbol === "GUARD" ? 0.10 : 0.50; // Example prices
    var tokenAmount = amountUSD / tokenPriceUSD;
    
    // Set calculated values
    context.setVariable("token.config", JSON.stringify(token));
    context.setVariable("token.amount", tokenAmount);
    context.setVariable("token.price_usd", tokenPriceUSD);
    context.setVariable("purchase.amount_usd", amountUSD);
    context.setVariable("purchase.wallet_address", walletAddress);
    context.setVariable("purchase.payment_method", paymentMethod);
    
    // Generate unique transaction ID
    var txId = "SHIELD_" + Date.now() + "_" + Math.random().toString(36).substr(2, 9);
    context.setVariable("transaction.id", txId);
    
    // Set validation success
    context.setVariable("validation.success", true);
    context.setVariable("validation.token_type", tokenType);
    context.setVariable("validation.amount_valid", true);
    
    // Analytics event
    context.setVariable("analytics.event", "token_purchase_validated");
    context.setVariable("analytics.token_type", tokenType);
    context.setVariable("analytics.amount_usd", amountUSD);
    context.setVariable("analytics.wallet_address", walletAddress);
    context.setVariable("analytics.timestamp", Date.now());
    
    // Add purchase metadata to request
    context.setVariable("request.header.x-transaction-id", txId);
    context.setVariable("request.header.x-token-amount", tokenAmount.toString());
    context.setVariable("request.header.x-token-price", tokenPriceUSD.toString());
    
} catch (error) {
    // Validation failed
    context.setVariable("validation.success", false);
    context.setVariable("validation.error", error.message);
    
    // Analytics event for failed validation
    context.setVariable("analytics.event", "token_purchase_validation_failed");
    context.setVariable("analytics.error", error.message);
    context.setVariable("analytics.timestamp", Date.now());
    
    // Return validation error response
    context.setVariable("response.status.code", 400);
    context.setVariable("response.content", JSON.stringify({
        error: "Validation failed",
        message: error.message,
        details: {
            supported_tokens: ["GUARD", "SHIELD"],
            minimum_amounts: {
                "GUARD": "$0.005",
                "SHIELD": "$0.025"
            },
            supported_payment_methods: ["metamask", "walletconnect", "coinbase", "trust"]
        }
    }));
    context.setVariable("response.header.Content-Type", "application/json");
}