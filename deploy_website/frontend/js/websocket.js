// GuardianShield Dashboard - WebSocket Real-time Connection

let ws = null;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;
const reconnectDelay = 3000;

// WebSocket connection management
function connectWebSocket() {
    console.log('🔌 Connecting to GuardianShield WebSocket...');
    
    // Use secure WebSocket if HTTPS, otherwise use WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/dashboard`;
    
    try {
        ws = new WebSocket(wsUrl);
        
        ws.onopen = handleWebSocketOpen;
        ws.onmessage = handleWebSocketMessage;
        ws.onclose = handleWebSocketClose;
        ws.onerror = handleWebSocketError;
        
    } catch (error) {
        console.error('Failed to create WebSocket connection:', error);
        scheduleReconnect();
    }
}

function handleWebSocketOpen(event) {
    console.log('✅ WebSocket connected successfully');
    reconnectAttempts = 0;
    
    // Update connection status in UI
    updateConnectionStatus('connected');
    
    // Send initial subscription message
    sendWebSocketMessage({
        type: 'subscribe',
        topics: ['agent_status', 'threat_updates', 'system_metrics', 'log_stream']
    });
    
    showNotification('Connection Established', 'Real-time monitoring is now active', 'success');
}

function handleWebSocketMessage(event) {
    try {
        const data = JSON.parse(event.data);
        console.log('📨 WebSocket message received:', data);
        
        // Route message to appropriate handler
        switch (data.type) {
            case 'agent_status_update':
                handleAgentStatusUpdate(data);
                break;
                
            case 'threat_detected':
                handleThreatDetected(data);
                break;
                
            case 'system_metrics':
                handleSystemMetrics(data);
                break;
                
            case 'log_entry':
                handleLogEntry(data);
                break;
                
            case 'agent_evolution':
                handleAgentEvolution(data);
                break;
                
            case 'emergency_alert':
                handleEmergencyAlert(data);
                break;
                
            case 'heartbeat':
                handleHeartbeat(data);
                break;
                
            default:
                console.log('Unknown message type:', data.type);
        }
        
    } catch (error) {
        console.error('Error parsing WebSocket message:', error);
    }
}

function handleWebSocketClose(event) {
    console.log('🔌 WebSocket connection closed:', event.code, event.reason);
    
    updateConnectionStatus('disconnected');
    
    if (event.code !== 1000) { // Not a normal closure
        showNotification('Connection Lost', 'Real-time monitoring disconnected', 'warning');
        scheduleReconnect();
    }
}

function handleWebSocketError(error) {
    console.error('❌ WebSocket error:', error);
    updateConnectionStatus('error');
}

function scheduleReconnect() {
    if (reconnectAttempts < maxReconnectAttempts) {
        reconnectAttempts++;
        console.log(`🔄 Attempting to reconnect... (${reconnectAttempts}/${maxReconnectAttempts})`);
        
        setTimeout(() => {
            connectWebSocket();
        }, reconnectDelay * reconnectAttempts);
    } else {
        console.error('❌ Max reconnection attempts reached');
        showNotification('Connection Failed', 'Unable to establish real-time connection', 'error');
    }
}

function sendWebSocketMessage(message) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(message));
    } else {
        console.warn('WebSocket not connected, cannot send message:', message);
    }
}

// Message handlers
function handleAgentStatusUpdate(data) {
    console.log('🤖 Agent status update:', data);
    
    const { agentId, status, metrics } = data.payload;
    
    // Update agent in local state
    const agent = DashboardState.agents.find(a => a.id === agentId);
    if (agent) {
        agent.status = status;
        if (metrics) {
            agent.actions = metrics.actions || agent.actions;
            agent.accuracy = metrics.accuracy || agent.accuracy;
            agent.evolutions = metrics.evolutions || agent.evolutions;
        }
        
        // Update UI if on agents page
        if (DashboardState.currentSection === 'agents') {
            refreshAgentGrid();
        }
        
        // Update stats
        updateAgentStats();
        
        // Show notification for status changes
        if (status === 'active') {
            showNotification('Agent Started', `${agent.name} is now active`, 'success');
        } else if (status === 'inactive') {
            showNotification('Agent Stopped', `${agent.name} has been stopped`, 'warning');
        } else if (status === 'error') {
            showNotification('Agent Error', `${agent.name} encountered an error`, 'error');
        }
    }
}

function handleThreatDetected(data) {
    console.log('⚠️ Threat detected:', data);
    
    const threat = data.payload;
    
    // Add to threats list
    DashboardState.threats.unshift({
        ...threat,
        timestamp: Date.now()
    });
    
    // Keep only latest 50 threats
    if (DashboardState.threats.length > 50) {
        DashboardState.threats = DashboardState.threats.slice(0, 50);
    }
    
    // Update stats
    DashboardState.stats.threatsBlocked++;
    if (threat.severity === 'high') {
        DashboardState.stats.alerts++;
    }
    
    // Update UI
    updateStats();
    updateThreatFeed();
    
    // Show notification
    const severityEmoji = threat.severity === 'high' ? '🚨' : 
                         threat.severity === 'medium' ? '⚠️' : 'ℹ️';
    
    showNotification(
        `${severityEmoji} Threat Detected`,
        `${threat.title} - ${threat.severity.toUpperCase()} severity`,
        threat.severity === 'high' ? 'error' : 'warning'
    );
    
    // Add to activity feed
    addActivityItem({
        icon: threat.severity === 'high' ? 'error' : 'warning',
        title: 'Threat Detected',
        description: threat.title,
        time: 'Just now'
    });
}

function handleSystemMetrics(data) {
    console.log('📊 System metrics update:', data);
    
    const metrics = data.payload;
    
    // Update performance metrics
    if (metrics.performance) {
        updatePerformanceMetrics(metrics.performance);
    }
    
    // Update resource usage
    if (metrics.resources) {
        updateResourceMetrics(metrics.resources);
    }
    
    // Update charts if on analytics page
    if (DashboardState.currentSection === 'analytics') {
        updateAnalyticsCharts(metrics);
    }
}

function handleLogEntry(data) {
    console.log('📝 New log entry:', data);
    
    const logEntry = data.payload;
    
    // Add to logs
    DashboardState.logs.unshift(logEntry);
    
    // Keep only latest 1000 logs
    if (DashboardState.logs.length > 1000) {
        DashboardState.logs = DashboardState.logs.slice(0, 1000);
    }
    
    // Update logs display if on logs page
    if (DashboardState.currentSection === 'logs') {
        updateLogs();
    }
    
    // Show notification for error logs
    if (logEntry.level === 'error') {
        showNotification('System Error', logEntry.message, 'error');
    }
}

function handleAgentEvolution(data) {
    console.log('🧬 Agent evolution:', data);
    
    const { agentId, evolutionData } = data.payload;
    
    // Update agent evolution count
    const agent = DashboardState.agents.find(a => a.id === agentId);
    if (agent) {
        agent.evolutions++;
        
        // Update accuracy if provided
        if (evolutionData.newAccuracy) {
            agent.accuracy = evolutionData.newAccuracy;
        }
        
        // Update UI
        if (DashboardState.currentSection === 'agents') {
            refreshAgentGrid();
        }
        
        // Update stats
        DashboardState.stats.evolutions++;
        updateStats();
        
        // Show notification
        showNotification(
            'Agent Evolution Complete',
            `${agent.name} has evolved with ${evolutionData.improvementPercentage}% improvement`,
            'success'
        );
        
        // Add to activity feed
        addActivityItem({
            icon: 'success',
            title: 'Evolution Complete',
            description: `${agent.name} evolved successfully`,
            time: 'Just now'
        });
    }
}

function handleEmergencyAlert(data) {
    console.log('🚨 Emergency alert:', data);
    
    const alert = data.payload;
    
    // Show prominent notification
    showNotification(
        '🚨 EMERGENCY ALERT',
        alert.message,
        'error'
    );
    
    // Update alerts count
    DashboardState.stats.alerts++;
    updateStats();
    
    // Flash the emergency stop button
    const emergencyBtn = document.querySelector('.btn-emergency');
    if (emergencyBtn) {
        emergencyBtn.classList.add('flash');
        setTimeout(() => {
            emergencyBtn.classList.remove('flash');
        }, 5000);
    }
}

function handleHeartbeat(data) {
    // Silent heartbeat handling
    updateConnectionStatus('connected');
}

// Utility functions
function updateConnectionStatus(status) {
    const indicator = document.querySelector('.connection-status');
    if (indicator) {
        indicator.className = `connection-status ${status}`;
        indicator.title = `Connection: ${status}`;
    }
    
    // Update system status indicator
    const systemIndicator = document.querySelector('.status-indicator');
    if (systemIndicator) {
        if (status === 'connected') {
            systemIndicator.classList.remove('offline');
            systemIndicator.classList.add('online');
        } else {
            systemIndicator.classList.remove('online');
            systemIndicator.classList.add('offline');
        }
    }
}

function addActivityItem(activity) {
    const activityList = document.getElementById('agent-activity-list');
    if (!activityList) return;
    
    const activityHTML = `
        <div class="activity-item">
            <div class="activity-icon ${activity.icon}">
                <i class="fas fa-${activity.icon === 'success' ? 'check' : 
                                    activity.icon === 'warning' ? 'exclamation-triangle' : 
                                    activity.icon === 'error' ? 'times' : 'info-circle'}"></i>
            </div>
            <div class="activity-content">
                <div class="activity-title">${activity.title}</div>
                <div class="activity-description">${activity.description}</div>
            </div>
            <div class="activity-time">${activity.time}</div>
        </div>
    `;
    
    activityList.insertAdjacentHTML('afterbegin', activityHTML);
    
    // Remove old items if too many
    const items = activityList.querySelectorAll('.activity-item');
    if (items.length > 20) {
        items[items.length - 1].remove();
    }
}

function updatePerformanceMetrics(performance) {
    // Update performance chart if visible
    if (window.performanceChart) {
        // Add new data point to chart
        const chart = window.performanceChart;
        chart.data.labels.push(new Date().toLocaleTimeString());
        chart.data.datasets[0].data.push(performance.cpuUsage);
        chart.data.datasets[1].data.push(performance.memoryUsage);
        
        // Keep only last 20 data points
        if (chart.data.labels.length > 20) {
            chart.data.labels.shift();
            chart.data.datasets.forEach(dataset => {
                dataset.data.shift();
            });
        }
        
        chart.update();
    }
}

function updateResourceMetrics(resources) {
    // Update resource usage displays
    const cpuElement = document.getElementById('cpu-usage');
    const memoryElement = document.getElementById('memory-usage');
    const diskElement = document.getElementById('disk-usage');
    
    if (cpuElement) cpuElement.textContent = `${resources.cpu}%`;
    if (memoryElement) memoryElement.textContent = `${resources.memory}%`;
    if (diskElement) diskElement.textContent = `${resources.disk}%`;
}

function updateAnalyticsCharts(metrics) {
    // Update various analytics charts with new data
    console.log('Updating analytics charts with:', metrics);
}

// Connection management functions
function reconnectWebSocket() {
    if (ws) {
        ws.close();
    }
    reconnectAttempts = 0;
    connectWebSocket();
}

function disconnectWebSocket() {
    if (ws) {
        ws.close(1000, 'Manual disconnect');
        ws = null;
    }
}

// Export functions for global use
window.connectWebSocket = connectWebSocket;
window.reconnectWebSocket = reconnectWebSocket;
window.disconnectWebSocket = disconnectWebSocket;
window.sendWebSocketMessage = sendWebSocketMessage;

// Handle page unload
window.addEventListener('beforeunload', () => {
    disconnectWebSocket();
});