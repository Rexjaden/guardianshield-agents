#!/bin/bash
# GuardianShield Mainnet Bootnode Launcher
# Launches multiple containerized bootnodes for the mainnet
# Usage: ./launch-mainnet-bootnodes.sh [COUNT] [START_PORT]

COUNT=${1:-5}          # Default to 5 nodes
START_PORT=${2:-26656} # Default start port TCP
IMAGE_NAME="guardianshield-bootnode:mainnet"

echo "🚀 initializing mainnet bootnode launcher..."
echo "targeting: $COUNT nodes starting at port $START_PORT"

# 1. Build the lightweight bootnode image
echo "📦 building bootnode image..."
docker build -f Dockerfile.bootnode -t $IMAGE_NAME .

# 2. Network setup
docker network create guardianshield-mainnet-net 2>/dev/null || true

# 3. Launch nodes
for ((i=1; i<=COUNT; i++)); do
    PORT=$((START_PORT + i - 1))
    NODE_ID="guardian_bootnode_mainnet_$(printf "%03d" $i)"
    CONTAINER_NAME="bootnode-mainnet-$i"
    
    echo "Starting node $i ($CONTAINER_NAME) on port $PORT..."
    
    # Remove existing if any
    docker rm -f $CONTAINER_NAME 2>/dev/null

    docker run -d \
        --name $CONTAINER_NAME \
        --network guardianshield-mainnet-net \
        --restart unless-stopped \
        -p $PORT:26656 \
        -e BOOTNODE_ID=$NODE_ID \
        -e MODE=bootnode \
        -e CHAIN_ID=guardianshield-mainnet \
        -e DISCOVERY_ONLY=true \
        -e MAX_PEERS=500 \
        $IMAGE_NAME

    echo "✅ $CONTAINER_NAME is running with ID: $NODE_ID"
done

echo "🎉 Successfully launched $COUNT mainnet bootnodes!"
echo "Global P2P Network Active."
docker ps | grep bootnode-mainnet
