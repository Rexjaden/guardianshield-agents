#!/bin/bash
# GuardianShield Mainnet VALIDATOR Launcher
# Launches secure validator nodes that can sign blocks
# Usage: ./launch-mainnet-validators.sh [COUNT] [START_PORT_P2P] [START_PORT_RPC]

COUNT=${1:-3}            # Default to 3 validators (they are heavier)
START_PORT_P2P=${2:-26656}
START_PORT_RPC=${3:-26657}
IMAGE_NAME="guardianshield-validator:mainnet"

echo "🛡️  Initializing Mainnet VALIDATOR Swarm..."
echo "Targeting: $COUNT validators"

# 1. Build the Secure Validator Image
echo "🏰 Building Ultra-Secure Validator Image..."
docker build -f Dockerfile.validator -t $IMAGE_NAME .

# 2. Network setup (share with bootnodes)
docker network create guardianshield-mainnet-net 2>/dev/null || true

# 3. Launch Validators
for ((i=1; i<=COUNT; i++)); do
    # Calculate unique ports
    P2P_PORT=$((START_PORT_P2P + (i * 10))) # Spaced out ports
    RPC_PORT=$((START_PORT_RPC + (i * 10))) 
    
    NODE_ID="guardian_validator_mainnet_$(printf "%03d" $i)"
    CONTAINER_NAME="validator-mainnet-$i"
    
    # Generate a temporary private key for this session
    VALIDATOR_KEY=$(openssl rand -hex 32)
    
    echo "Starting VALIDATOR $i ($CONTAINER_NAME)..."
    echo "   - P2P Port: $P2P_PORT"
    echo "   - RPC Port: $RPC_PORT"
    
    # Remove existing
    docker rm -f $CONTAINER_NAME 2>/dev/null

    docker run -d \
        --name $CONTAINER_NAME \
        --network guardianshield-mainnet-net \
        --restart unless-stopped \
        -p $P2P_PORT:26656 \
        -p $RPC_PORT:26657 \
        -e NODE_ID=$NODE_ID \
        -e MODE=validator \
        -e CHAIN_ID=guardianshield-mainnet \
        -e VALIDATOR_PRIVATE_KEY=$VALIDATOR_KEY \
        -e CONSENSUS=proof_of_stake \
        $IMAGE_NAME

    echo "✅ $CONTAINER_NAME is Active & Signing Blocks."
done

echo "🎉 Validator Swarm Active."
docker ps | grep validator-mainnet