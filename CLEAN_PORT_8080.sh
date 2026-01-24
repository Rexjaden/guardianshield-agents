#!/bin/bash
# 🧹 Port 8080 Cleaner
# ====================
# This script forcefully terminates any process using port 8080.
# Useful when 'python3 -m http.server' is stuck running.

echo "🔍 Scanning Port 8080..."

# Method 1: fuser (Fastest)
if command -v fuser &> /dev/null; then
    fuser -k 8080/tcp > /dev/null 2>&1
fi

# Method 2: lsof (Standard)
if command -v lsof &> /dev/null; then
    PID=$(lsof -t -i:8080 2>/dev/null)
    if [ ! -z "$PID" ]; then
        echo "💥 Killing stuck process (PID: $PID)..."
        kill -9 $PID 2>/dev/null
    fi
fi

# Verification
sleep 1
if command -v lsof &> /dev/null; then
    CHECK=$(lsof -t -i:8080)
    if [ -z "$CHECK" ]; then
        echo "✅ Port 8080 is CLEARED and ready for use."
    else
        echo "❌ Port 8080 is still in use. Try running this script again."
    fi
else
    # Fallback if tools missing
    echo "✅ cleanup commands executed."
fi
