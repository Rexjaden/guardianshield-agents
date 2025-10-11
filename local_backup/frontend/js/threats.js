// GuardianShield Dashboard - Threat Monitoring

function refreshThreatDashboard() {
    updateThreatMap();
    updateThreatTimeline();
    updateThreatStats();
}

function updateThreatMap() {
    const mapContainer = document.getElementById('threat-map-container');
    if (!mapContainer) return;
    
    // Simulate threat map visualization
    mapContainer.innerHTML = `
        <div class="threat-map-placeholder">
            <i class="fas fa-globe" style="font-size: 3rem; color: var(--primary-color); margin-bottom: 1rem;"></i>
            <p>Global Threat Distribution</p>
            <div class="threat-regions">
                <div class="threat-region">
                    <span class="region-name">North America</span>
                    <span class="threat-count high">23 threats</span>
                </div>
                <div class="threat-region">
                    <span class="region-name">Europe</span>
                    <span class="threat-count medium">15 threats</span>
                </div>
                <div class="threat-region">
                    <span class="region-name">Asia Pacific</span>
                    <span class="threat-count low">8 threats</span>
                </div>
            </div>
        </div>
    `;
}

function updateThreatTimeline() {
    const timelineList = document.getElementById('threat-timeline-list');
    if (!timelineList) return;
    
    const recentThreats = DashboardState.threats.slice(0, 10);
    
    timelineList.innerHTML = recentThreats.map(threat => `
        <div class="timeline-item threat-${threat.severity}">
            <div class="timeline-content">
                <strong>${threat.title}</strong>
                <p>${threat.description}</p>
            </div>
            <div class="timeline-time">${formatTime(threat.timestamp)}</div>
        </div>
    `).join('');
}

function updateThreatStats() {
    const highThreats = DashboardState.threats.filter(t => t.severity === 'high').length;
    const mediumThreats = DashboardState.threats.filter(t => t.severity === 'medium').length;
    const lowThreats = DashboardState.threats.filter(t => t.severity === 'low').length;
    
    // Update threat severity distribution
    const statsContainer = document.getElementById('threat-severity-stats');
    if (statsContainer) {
        statsContainer.innerHTML = `
            <div class="severity-stat">
                <span class="severity-label high">High</span>
                <span class="severity-count">${highThreats}</span>
            </div>
            <div class="severity-stat">
                <span class="severity-label medium">Medium</span>
                <span class="severity-count">${mediumThreats}</span>
            </div>
            <div class="severity-stat">
                <span class="severity-label low">Low</span>
                <span class="severity-count">${lowThreats}</span>
            </div>
        `;
    }
}

function exportThreats() {
    console.log('Exporting threat data...');
    
    const exportData = {
        exportTime: new Date().toISOString(),
        totalThreats: DashboardState.threats.length,
        threats: DashboardState.threats.map(threat => ({
            ...threat,
            exportedAt: new Date().toISOString()
        }))
    };
    
    // Create and download JSON file
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `guardianshield-threats-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    
    URL.revokeObjectURL(url);
    
    showNotification('Export Complete', 'Threat data exported successfully', 'success');
}

// Export for global use
window.refreshThreatDashboard = refreshThreatDashboard;
window.exportThreats = exportThreats;