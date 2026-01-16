#!/bin/bash
# DHI-ClamAV Startup Script

set -e

echo "Starting DHI-ClamAV Security Engine..."

# Create necessary directories
mkdir -p /var/run/clamav /var/log/clamav /app/logs /app/quarantine /app/temp

# Fix permissions
sudo chown -R clamav:clamav /var/run/clamav /var/log/clamav /var/lib/clamav 2>/dev/null || true
chown -R clamav-user:clamav-user /app/logs /app/quarantine /app/temp 2>/dev/null || true

# Update virus signatures if needed
echo "Checking virus signatures..."
if [ ! -f /var/lib/clamav/main.cvd ] || [ ! -f /var/lib/clamav/daily.cvd ]; then
    echo "Downloading initial virus signatures..."
    freshclam --quiet || {
        echo "Warning: Initial signature download failed, continuing with cached signatures..."
    }
fi

# Start ClamAV daemon
echo "Starting ClamAV daemon..."
clamd --config-file=/etc/clamav/clamd.conf &
CLAMD_PID=$!

# Wait for ClamAV daemon to start
echo "Waiting for ClamAV daemon to initialize..."
for i in {1..30}; do
    if clamdscan --version > /dev/null 2>&1; then
        echo "ClamAV daemon started successfully"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Error: ClamAV daemon failed to start"
        exit 1
    fi
    sleep 2
done

# Start freshclam for automatic updates
echo "Starting FreshClam for automatic updates..."
freshclam --daemon --config-file=/etc/clamav/freshclam.conf &
FRESHCLAM_PID=$!

# Function to handle shutdown
cleanup() {
    echo "Shutting down DHI-ClamAV..."
    
    # Stop Python API server
    if [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null || true
        wait $API_PID 2>/dev/null || true
    fi
    
    # Stop FreshClam
    if [ ! -z "$FRESHCLAM_PID" ]; then
        kill $FRESHCLAM_PID 2>/dev/null || true
        wait $FRESHCLAM_PID 2>/dev/null || true
    fi
    
    # Stop ClamAV daemon
    if [ ! -z "$CLAMD_PID" ]; then
        kill $CLAMD_PID 2>/dev/null || true
        wait $CLAMD_PID 2>/dev/null || true
    fi
    
    echo "DHI-ClamAV stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Start the Python API server
echo "Starting DHI-ClamAV API server..."
cd /app
python3 dhi_clamav_api.py &
API_PID=$!

echo "DHI-ClamAV started successfully"
echo "- ClamAV daemon PID: $CLAMD_PID"  
echo "- FreshClam PID: $FRESHCLAM_PID"
echo "- API server PID: $API_PID"
echo "- API server listening on port 8080"
echo "- ClamAV daemon listening on port 3310"

# Wait for any process to exit
wait -n

# If we get here, one of the processes exited unexpectedly
echo "Error: One of the processes exited unexpectedly"
cleanup