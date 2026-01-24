#!/bin/bash
# 🚀 Robust Server Launcher for Port 8081

# 1. Force Clean Port
echo "🧹 Cleaning port 8081..."
if command -v fuser &> /dev/null; then
    fuser -k 8081/tcp > /dev/null 2>&1
fi
if command -v lsof &> /dev/null; then
    PID=$(lsof -t -i:8081 2>/dev/null)
    if [ ! -z "$PID" ]; then
        kill -9 $PID 2>/dev/null
    fi
fi

# 2. Check Directory
if [ -d "guardianshield_website" ]; then
    cd guardianshield_website
    echo "📂 Entered directory: guardianshield_website"
else
    echo "⚠️ Directory 'guardianshield_website' not found!"
    echo "   Running deployment for you now..."
    # Download deployment if missing
    curl -O https://raw.githubusercontent.com/Rexjaden/guardianshield-agents/main/DEPLOY_WEBSITE_PACKAGE.sh
    sh DEPLOY_WEBSITE_PACKAGE.sh
    cd guardianshield_website
fi

# 3. Start Server
echo "---------------------------------------------------"
echo "✅ STARTING SERVER ON PORT 8081"
echo "---------------------------------------------------"
echo "👉 Click 'Web Preview' -> 'Change Port' -> 8081"
echo "👉 Press Ctrl+C to stop"
echo "---------------------------------------------------"

# Run Python server bound to all interfaces
python3 -m http.server 8081 --bind 0.0.0.0
