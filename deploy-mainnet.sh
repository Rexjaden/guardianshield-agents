#!/bin/bash
# GuardianShield Guard Token Deployment Script
# 
# Your Wallet: 0xF262b772c2EBf526a5cF8634CA92597583Ef38ee
# API Key: J8QD4YPCWIRT3G1WFGHIC7YWGDBJ4VMGZ4

echo "🚀 Deploying Guard Token (GAR) to Mainnet"
echo "=========================================="
echo "Wallet: 0xF262b772c2EBf526a5cF8634CA92597583Ef38ee"
echo "API Key: J8QD4YPCWIRT3G1WFGHIC7YWGDBJ4VMGZ4"
echo ""

# Set your private key as environment variable
export PRIVATE_KEY="YOUR_PRIVATE_KEY_HERE"

# Deploy to mainnet
npx hardhat run scripts/deploy-guard-token.js --network mainnet

echo ""
echo "✅ Deployment complete!"
echo "📍 Contract will be owned by: 0xF262b772c2EBf526a5cF8634CA92597583Ef38ee"