#!/bin/bash
# GuardianShield Secure Node Management Setup
# Rex Judon Rogers - Quick Setup Script

echo "🛡️  Setting up secure node communication..."

# Create SSH key pair for nodes
if [ ! -f ~/.ssh/guardianshield_rsa ]; then
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/guardianshield_rsa -N "" -C "rex@guardianshield-nodes"
    echo "✅ SSH key created"
fi

# Install CLI tool
sudo cp guardian-cli.py /usr/local/bin/guardian
sudo chmod 755 /usr/local/bin/guardian

# Setup SSH config
mkdir -p ~/.ssh
cp config/ssh-config ~/.ssh/config_guardianshield
echo "Include ~/.ssh/config_guardianshield" >> ~/.ssh/config

echo "✅ Secure node communication setup complete!"
echo
echo "🚀 QUICK COMMANDS:"
echo "   guardian auth          - Test authentication"
echo "   guardian list          - List all nodes" 
echo "   guardian status        - Node status report"
echo "   guardian security      - Security report"
echo "   ssh guardian-us-east   - Direct SSH to US East node"
echo
echo "🌐 Management Dashboard: file://$(pwd)/dashboard.html"
echo "🔑 API Key: e988169a6a8b0c14504a..."
