#!/bin/bash

# ==============================================================================
# GUARDIANSHIELD - GOOGLE CLOUD VM SETUP SCRIPT
# Run this script inside your fresh Google Cloud VM (Ubuntu/Debian)
# ==============================================================================

echo "🛡️  STARTING GUARDIANSHIELD CLOUD SETUP..."

# 1. Update System
echo "🔄 Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install Docker & Docker Compose
echo "🐳 Installing Docker..."
sudo apt-get install -y docker.io docker-compose git

# 3. Start Docker Service
sudo systemctl start docker
sudo systemctl enable docker

# 4. Clone Repository
# Note: If your repo is private, you will need to provide a Personal Access Token
echo "qc Cloning GuardianShield Repository..."
# Using the HTTPS URL provided in your instructions
git clone https://github.com/Rexjaden/guardianshield-agents.git
cd guardianshield-agents

# 5. Setup Configuration
echo "⚙️  Applying Google Cloud Configuration..."
# We use the special GCP compose file we created
# We also create a basic production .env if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Created default .env file. YOU SHOULD EDIT THIS WITH REAL SECRETS LATER."
fi

# 6. Deploy
echo "🚀 Launching GuardianShield on Google Cloud..."
# Using the GCP-specific compose file that excludes mining/desktop tools
sudo docker-compose -f docker-compose.gcp.yml up -d

echo "============================================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo "   Your website should be accessible at: http://<EXTERNAL-IP>"
echo "   Run 'sudo docker ps' to check status."
echo "============================================================"
