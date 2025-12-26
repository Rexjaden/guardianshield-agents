#!/bin/bash
# Agent health check script

# Check if agent process is running and responsive
AGENT_TYPE=${AGENT_TYPE:-"main"}
PID_FILE="/tmp/agent_${AGENT_TYPE}.pid"

# Check if PID file exists and process is running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Agent $AGENT_TYPE is running (PID: $PID)"
        exit 0
    else
        echo "Agent $AGENT_TYPE PID file exists but process is not running"
        rm -f "$PID_FILE"
        exit 1
    fi
else
    # Check if agent is running by process name
    if pgrep -f "python.*${AGENT_TYPE}" > /dev/null; then
        echo "Agent $AGENT_TYPE is running"
        exit 0
    else
        echo "Agent $AGENT_TYPE is not running"
        exit 1
    fi
fi