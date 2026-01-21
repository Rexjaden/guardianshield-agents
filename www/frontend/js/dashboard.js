// GuardianShield Dashboard - Main JavaScript

// Global state management
const DashboardState = {
    currentSection: 'dashboard',
    isNotificationPanelOpen: false,
    isSidebarCollapsed: false,
    agents: [],
    threats: [],
    logs: [],
    settings: {
        autonomyLevel: 10,
        autoEvolution: true,
        criticalThreshold: 8,
        monitoringInterval: 30
    },
    stats: {
        activeAgents: 8,
        threatsBlocked: 247,
        evolutions: 15,
        alerts: 3
    }
};

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    connectWebSocket();
    startRealTimeUpdates();
});

function initializeDashboard() {
    console.log('🛡️ GuardianShield Dashboard Initializing...');
    
    // Load initial data
    loadAgentData();
    loadThreatData();
    loadLogData();
    loadNotifications();
    
    // Setup event listeners
    setupEventListeners();
    
    // Initialize charts
    initializeCharts();
    
    // Start real-time updates
    updateStats();
    updateAgentActivity();
    updateThreatFeed();
    
    console.log('✅ Dashboard initialized successfully');
}

function setupEventListeners() {
    // Sidebar toggle
    document.addEventListener('click', function(e) {
        if (e.target.closest('.sidebar-toggle')) {
            toggleSidebar();
        }
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + E for emergency stop
        if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
            e.preventDefault();
            emergencyStop();
        }
        
        // Ctrl/Cmd + N for notifications
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            toggleNotifications();
        }
        
        // Escape to close panels
        if (e.key === 'Escape') {
            if (DashboardState.isNotificationPanelOpen) {
                toggleNotifications();
            }
        }
    });
    
    // Auto-save settings
    document.querySelectorAll('#settings-section input, #settings-section select').forEach(input => {
        input.addEventListener('change', function() {
            saveSettings();
        });
    });
}

// Navigation functions
function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Show selected section
    const targetSection = document.getElementById(`${sectionName}-section`);
    if (targetSection) {
        targetSection.classList.add('active');
    }
    
    // Update navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    const activeNavItem = document.querySelector(`a[onclick*="${sectionName}"]`).closest('.nav-item');
    if (activeNavItem) {
        activeNavItem.classList.add('active');
    }
    
    // Update page title and breadcrumb
    const titleMap = {
        'dashboard': 'Dashboard',
        'agents': 'Agent Management',
        'threats': 'Threat Monitoring',
        'analytics': 'Analytics & Insights',
        'logs': 'System Logs',
        'settings': 'System Settings'
    };
    
    document.getElementById('page-title').textContent = titleMap[sectionName] || 'Dashboard';
    document.getElementById('breadcrumb-current').textContent = titleMap[sectionName] || 'Dashboard';
    
    // Update state
    DashboardState.currentSection = sectionName;
    
    // Section-specific initialization
    switch(sectionName) {
        case 'agents':
            refreshAgentGrid();
            break;
        case 'threats':
            refreshThreatDashboard();
            break;
        case 'analytics':
            refreshAnalytics();
            break;
        case 'logs':
            refreshLogs();
            break;
        case 'settings':
            loadSettingsForm();
            break;
    }
}

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('collapsed');
    DashboardState.isSidebarCollapsed = !DashboardState.isSidebarCollapsed;
    
    // Save preference
    localStorage.setItem('sidebarCollapsed', DashboardState.isSidebarCollapsed);
}

function toggleNotifications() {
    const panel = document.getElementById('notification-panel');
    panel.classList.toggle('open');
    DashboardState.isNotificationPanelOpen = !DashboardState.isNotificationPanelOpen;
    
    if (DashboardState.isNotificationPanelOpen) {
        loadNotifications();
    }
}

// Emergency functions
function emergencyStop() {
    if (confirm('⚠️ This will immediately stop all autonomous agents. Are you sure?')) {
        console.log('🚨 Emergency stop initiated');
        
        // Show loading state
        const emergencyBtn = document.querySelector('.btn-emergency');
        const originalText = emergencyBtn.innerHTML;
        emergencyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Stopping...';
        emergencyBtn.disabled = true;
        
        // Call API to stop agents
        fetch('/api/emergency-stop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log('Emergency stop response:', data);
            showNotification('Emergency Stop', 'All agents have been stopped', 'error');
            updateSystemStatus('offline');
        })
        .catch(error => {
            console.error('Emergency stop failed:', error);
            showNotification('Emergency Stop Failed', 'Failed to stop agents', 'error');
        })
        .finally(() => {
            emergencyBtn.innerHTML = originalText;
            emergencyBtn.disabled = false;
        });
    }
}

// Data loading functions
function loadAgentData() {
    // Simulate agent data - replace with actual API call
    DashboardState.agents = [
        {
            id: 'learning_agent',
            name: 'Learning Agent',
            status: 'active',
            actions: 1247,
            evolutions: 5,
            accuracy: 94.5,
            autonomyLevel: 10
        },
        {
            id: 'behavioral_analytics',
            name: 'Behavioral Analytics',
            status: 'active',
            actions: 892,
            evolutions: 3,
            accuracy: 96.2,
            autonomyLevel: 9
        },
        {
            id: 'threat_definitions',
            name: 'Threat Definitions',
            status: 'active',
            actions: 445,
            evolutions: 7,
            accuracy: 89.1,
            autonomyLevel: 10
        },
        {
            id: 'data_ingestion',
            name: 'Data Ingestion',
            status: 'active',
            actions: 2156,
            evolutions: 2,
            accuracy: 91.8,
            autonomyLevel: 8
        },
        {
            id: 'dmer_monitor',
            name: 'DMER Monitor',
            status: 'active',
            actions: 567,
            evolutions: 4,
            accuracy: 93.7,
            autonomyLevel: 9
        },
        {
            id: 'external_agent',
            name: 'External Agent',
            status: 'active',
            actions: 334,
            evolutions: 1,
            accuracy: 87.9,
            autonomyLevel: 7
        },
        {
            id: 'flare_integration',
            name: 'Flare Integration',
            status: 'active',
            actions: 123,
            evolutions: 6,
            accuracy: 95.3,
            autonomyLevel: 10
        },
        {
            id: 'genetic_evolver',
            name: 'Genetic Evolver',
            status: 'active',
            actions: 78,
            evolutions: 12,
            accuracy: 88.4,
            autonomyLevel: 10
        }
    ];
}

function loadThreatData() {
    // Simulate threat data - replace with actual API call
    DashboardState.threats = [
        {
            id: 'threat_001',
            title: 'Suspicious Contract Deployment',
            description: 'Potential honeypot contract detected on Ethereum mainnet',
            severity: 'high',
            timestamp: Date.now() - 120000,
            source: 'behavioral_analytics'
        },
        {
            id: 'threat_002',
            title: 'Address Poisoning Attempt',
            description: 'Similar address pattern detected in recent transactions',
            severity: 'medium',
            timestamp: Date.now() - 300000,
            source: 'threat_definitions'
        },
        {
            id: 'threat_003',
            title: 'Anomalous Transaction Pattern',
            description: 'Unusual transaction frequency detected from known address',
            severity: 'low',
            timestamp: Date.now() - 450000,
            source: 'dmer_monitor'
        }
    ];
}

function loadLogData() {
    // Simulate log data - replace with actual API call
    DashboardState.logs = [
        {
            timestamp: new Date().toISOString(),
            level: 'info',
            message: 'Learning Agent completed evolution cycle #5',
            source: 'learning_agent'
        },
        {
            timestamp: new Date(Date.now() - 30000).toISOString(),
            level: 'warn',
            message: 'High threat activity detected in sector 7',
            source: 'threat_definitions'
        },
        {
            timestamp: new Date(Date.now() - 60000).toISOString(),
            level: 'error',
            message: 'Failed to connect to external threat feed',
            source: 'data_ingestion'
        }
    ];
}

function loadNotifications() {
    const notifications = [
        {
            id: 'notif_1',
            title: 'Agent Evolution Complete',
            message: 'Learning Agent has successfully completed evolution cycle #5 with 12% performance improvement',
            time: '2 minutes ago',
            read: false
        },
        {
            id: 'notif_2',
            title: 'High Severity Threat Detected',
            message: 'Potential honeypot contract detected on Ethereum mainnet requiring immediate attention',
            time: '5 minutes ago',
            read: false
        },
        {
            id: 'notif_3',
            title: 'System Update Available',
            message: 'GuardianShield v2.1.3 is available with enhanced threat detection capabilities',
            time: '1 hour ago',
            read: true
        }
    ];
    
    const notificationList = document.querySelector('.notification-list');
    if (notificationList) {
        notificationList.innerHTML = notifications.map(notif => `
            <div class="notification-item ${!notif.read ? 'unread' : ''}">
                <div class="notification-title">${notif.title}</div>
                <div class="notification-message">${notif.message}</div>
                <div class="notification-time">${notif.time}</div>
            </div>
        `).join('');
    }
    
    // Update notification badge
    const unreadCount = notifications.filter(n => !n.read).length;
    const badge = document.querySelector('.notification-badge');
    if (badge) {
        badge.textContent = unreadCount;
        badge.style.display = unreadCount > 0 ? 'block' : 'none';
    }
}

// Real-time update functions
function startRealTimeUpdates() {
    // Update stats every 30 seconds
    setInterval(updateStats, 30000);
    
    // Update agent activity every 5 seconds
    setInterval(updateAgentActivity, 5000);
    
    // Update threat feed every 10 seconds
    setInterval(updateThreatFeed, 10000);
    
    // Update logs every 15 seconds
    setInterval(updateLogs, 15000);
}

function updateStats() {
    // Simulate stat updates
    document.getElementById('active-agents').textContent = DashboardState.stats.activeAgents;
    document.getElementById('threats-blocked').textContent = DashboardState.stats.threatsBlocked;
    document.getElementById('evolutions').textContent = DashboardState.stats.evolutions;
    document.getElementById('alerts').textContent = DashboardState.stats.alerts;
}

function updateAgentActivity() {
    const activityList = document.getElementById('agent-activity-list');
    if (!activityList) return;
    
    // Simulate new activities
    const activities = [
        {
            icon: 'success',
            title: 'Threat Neutralized',
            description: 'Learning Agent successfully blocked phishing attempt',
            time: 'Just now'
        },
        {
            icon: 'info',
            title: 'Evolution in Progress',
            description: 'Behavioral Analytics upgrading pattern recognition',
            time: '2m ago'
        },
        {
            icon: 'warning',
            title: 'High Severity Alert',
            description: 'Suspicious contract deployment detected',
            time: '5m ago'
        }
    ];
    
    activityList.innerHTML = activities.map(activity => `
        <div class="activity-item">
            <div class="activity-icon ${activity.icon}">
                <i class="fas fa-${activity.icon === 'success' ? 'check' : activity.icon === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
            </div>
            <div class="activity-content">
                <div class="activity-title">${activity.title}</div>
                <div class="activity-description">${activity.description}</div>
            </div>
            <div class="activity-time">${activity.time}</div>
        </div>
    `).join('');
}

function updateThreatFeed() {
    const threatFeed = document.getElementById('threat-feed');
    if (!threatFeed) return;
    
    threatFeed.innerHTML = DashboardState.threats.map(threat => `
        <div class="threat-item">
            <div class="threat-header">
                <div class="threat-title">${threat.title}</div>
                <span class="threat-severity ${threat.severity}">${threat.severity.toUpperCase()}</span>
            </div>
            <div class="threat-description">${threat.description}</div>
            <div class="threat-time">${formatTime(threat.timestamp)}</div>
        </div>
    `).join('');
}

function updateLogs() {
    const logsDisplay = document.getElementById('logs-display');
    if (!logsDisplay || DashboardState.currentSection !== 'logs') return;
    
    logsDisplay.innerHTML = DashboardState.logs.map(log => `
        <div class="log-entry">
            <div class="log-timestamp">${formatTimestamp(log.timestamp)}</div>
            <div class="log-level ${log.level}">${log.level.toUpperCase()}</div>
            <div class="log-message">[${log.source}] ${log.message}</div>
        </div>
    `).join('');
}

// Utility functions
function formatTime(timestamp) {
    const now = Date.now();
    const diff = now - timestamp;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return `${Math.floor(diff / 86400000)}d ago`;
}

function formatTimestamp(timestamp) {
    return new Date(timestamp).toLocaleTimeString();
}

function showNotification(title, message, type = 'info') {
    // Create and show notification
    console.log(`[${type.toUpperCase()}] ${title}: ${message}`);
    
    // You could implement a toast notification system here
}

function updateSystemStatus(status) {
    const indicator = document.querySelector('.status-indicator');
    const statusText = document.querySelector('.system-status span');
    
    if (indicator && statusText) {
        indicator.className = `status-indicator ${status}`;
        statusText.textContent = status === 'online' ? 'System Online' : 'System Offline';
    }
}

// Button action functions (placeholders)
function refreshAgentActivity() {
    console.log('Refreshing agent activity...');
    updateAgentActivity();
}

function pauseFeed() {
    console.log('Pausing threat feed...');
}

function clearFeed() {
    console.log('Clearing threat feed...');
    document.getElementById('threat-feed').innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 2rem;">Feed cleared</p>';
}

function updatePerformanceChart(timeRange) {
    console.log(`Updating performance chart for: ${timeRange}`);
}

function deployNewAgent() {
    console.log('Deploying new agent...');
}

function exportThreats() {
    console.log('Exporting threat data...');
}

function clearLogs() {
    if (confirm('Are you sure you want to clear all logs?')) {
        document.getElementById('logs-display').innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 2rem;">Logs cleared</p>';
        DashboardState.logs = [];
    }
}

function filterLogs() {
    const filter = document.getElementById('log-level-filter').value;
    console.log(`Filtering logs by: ${filter}`);
    // Implementation for log filtering
}

function searchLogs() {
    const query = document.getElementById('log-search').value;
    console.log(`Searching logs for: ${query}`);
    // Implementation for log searching
}

// Settings functions
function updateAutonomyLevel(level) {
    DashboardState.settings.autonomyLevel = parseInt(level);
    document.getElementById('autonomy-value').textContent = level;
    console.log(`Autonomy level updated to: ${level}`);
}

function toggleAutoEvolution(enabled) {
    DashboardState.settings.autoEvolution = enabled;
    console.log(`Auto evolution ${enabled ? 'enabled' : 'disabled'}`);
}

function updateThreshold(threshold) {
    DashboardState.settings.criticalThreshold = parseInt(threshold);
    console.log(`Critical threshold updated to: ${threshold}`);
}

function updateInterval(interval) {
    DashboardState.settings.monitoringInterval = parseInt(interval);
    console.log(`Monitoring interval updated to: ${interval}s`);
}

function saveSettings() {
    console.log('Saving settings...', DashboardState.settings);
    // Save to backend/localStorage
}

function loadSettingsForm() {
    document.getElementById('autonomy-level').value = DashboardState.settings.autonomyLevel;
    document.getElementById('autonomy-value').textContent = DashboardState.settings.autonomyLevel;
    document.getElementById('auto-evolution').checked = DashboardState.settings.autoEvolution;
    document.getElementById('critical-threshold').value = DashboardState.settings.criticalThreshold;
    document.getElementById('monitoring-interval').value = DashboardState.settings.monitoringInterval;
}

// Export for use in other modules
window.DashboardState = DashboardState;
window.showSection = showSection;
window.toggleSidebar = toggleSidebar;
window.toggleNotifications = toggleNotifications;
window.emergencyStop = emergencyStop;