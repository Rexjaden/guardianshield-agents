// GuardianShield Dashboard - Agents Management

// Agent management functions
function refreshAgentGrid() {
    const agentsGrid = document.getElementById('agents-grid');
    if (!agentsGrid) return;
    
    agentsGrid.innerHTML = DashboardState.agents.map(agent => createAgentCard(agent)).join('');
}

function createAgentCard(agent) {
    const statusColor = agent.status === 'active' ? 'success' : 
                       agent.status === 'error' ? 'danger' : 'muted';
    
    return `
        <div class="agent-card" data-agent-id="${agent.id}">
            <div class="agent-header">
                <div class="agent-name">
                    <i class="fas fa-robot"></i>
                    ${agent.name}
                </div>
                <span class="agent-status ${agent.status}">${agent.status.toUpperCase()}</span>
            </div>
            
            <div class="agent-metrics">
                <div class="agent-metric">
                    <div class="agent-metric-value">${agent.actions}</div>
                    <div class="agent-metric-label">Actions</div>
                </div>
                <div class="agent-metric">
                    <div class="agent-metric-value">${agent.evolutions}</div>
                    <div class="agent-metric-label">Evolutions</div>
                </div>
                <div class="agent-metric">
                    <div class="agent-metric-value">${agent.accuracy}%</div>
                    <div class="agent-metric-label">Accuracy</div>
                </div>
                <div class="agent-metric">
                    <div class="agent-metric-value">${agent.autonomyLevel}/10</div>
                    <div class="agent-metric-label">Autonomy</div>
                </div>
            </div>
            
            <div class="agent-progress">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${agent.accuracy}%"></div>
                </div>
                <span class="progress-label">Performance: ${agent.accuracy}%</span>
            </div>
            
            <div class="agent-actions">
                <button class="agent-action-btn ${agent.status === 'active' ? 'danger' : 'primary'}" 
                        onclick="toggleAgent('${agent.id}')">
                    <i class="fas fa-${agent.status === 'active' ? 'stop' : 'play'}"></i>
                    ${agent.status === 'active' ? 'Stop' : 'Start'}
                </button>
                <button class="agent-action-btn" onclick="configureAgent('${agent.id}')">
                    <i class="fas fa-cog"></i>
                    Configure
                </button>
                <button class="agent-action-btn" onclick="viewAgentLogs('${agent.id}')">
                    <i class="fas fa-file-alt"></i>
                    Logs
                </button>
                <button class="agent-action-btn" onclick="evolveAgent('${agent.id}')">
                    <i class="fas fa-dna"></i>
                    Evolve
                </button>
            </div>
        </div>
    `;
}

function toggleAgent(agentId) {
    const agent = DashboardState.agents.find(a => a.id === agentId);
    if (!agent) return;
    
    const newStatus = agent.status === 'active' ? 'inactive' : 'active';
    const action = newStatus === 'active' ? 'start' : 'stop';
    
    if (confirm(`Are you sure you want to ${action} ${agent.name}?`)) {
        console.log(`${action}ing agent: ${agentId}`);
        
        // Update UI immediately
        agent.status = newStatus;
        refreshAgentGrid();
        
        // Call API
        fetch(`/api/agents/${agentId}/${action}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log(`Agent ${action} response:`, data);
            showNotification(
                `Agent ${action === 'start' ? 'Started' : 'Stopped'}`,
                `${agent.name} has been ${action === 'start' ? 'started' : 'stopped'} successfully`,
                'success'
            );
            
            // Update stats
            updateAgentStats();
        })
        .catch(error => {
            console.error(`Agent ${action} failed:`, error);
            // Revert status on error
            agent.status = agent.status === 'active' ? 'inactive' : 'active';
            refreshAgentGrid();
            showNotification(
                `Agent ${action} Failed`,
                `Failed to ${action} ${agent.name}`,
                'error'
            );
        });
    }
}

function configureAgent(agentId) {
    const agent = DashboardState.agents.find(a => a.id === agentId);
    if (!agent) return;
    
    console.log(`Configuring agent: ${agentId}`);
    
    // Create and show configuration modal
    showAgentConfigModal(agent);
}

function showAgentConfigModal(agent) {
    // Create modal HTML
    const modalHTML = `
        <div class="modal-overlay" id="agent-config-modal">
            <div class="modal-container">
                <div class="modal-header">
                    <h3>Configure ${agent.name}</h3>
                    <button class="modal-close" onclick="closeAgentConfigModal()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <div class="modal-content">
                    <div class="config-section">
                        <h4>Agent Parameters</h4>
                        
                        <div class="config-item">
                            <label for="agent-autonomy">Autonomy Level (1-10)</label>
                            <input type="range" id="agent-autonomy" min="1" max="10" 
                                   value="${agent.autonomyLevel}" onchange="updateAgentAutonomy(this.value)">
                            <span id="agent-autonomy-value">${agent.autonomyLevel}</span>
                        </div>
                        
                        <div class="config-item">
                            <label for="agent-learning-rate">Learning Rate</label>
                            <input type="number" id="agent-learning-rate" min="0.01" max="1" 
                                   step="0.01" value="0.1">
                        </div>
                        
                        <div class="config-item">
                            <label for="agent-confidence-threshold">Confidence Threshold</label>
                            <input type="number" id="agent-confidence-threshold" min="0.1" max="1" 
                                   step="0.1" value="0.7">
                        </div>
                        
                        <div class="config-item">
                            <label>
                                <input type="checkbox" id="agent-auto-evolve" checked>
                                Enable Auto Evolution
                            </label>
                        </div>
                        
                        <div class="config-item">
                            <label>
                                <input type="checkbox" id="agent-cross-collaborate" checked>
                                Enable Cross-Agent Collaboration
                            </label>
                        </div>
                    </div>
                    
                    <div class="config-section">
                        <h4>Performance Metrics</h4>
                        <div class="metrics-grid">
                            <div class="metric-item">
                                <span class="metric-label">Total Actions</span>
                                <span class="metric-value">${agent.actions}</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">Evolutions</span>
                                <span class="metric-value">${agent.evolutions}</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">Accuracy</span>
                                <span class="metric-value">${agent.accuracy}%</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">Uptime</span>
                                <span class="metric-value">99.7%</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="modal-footer">
                    <button class="btn-secondary" onclick="closeAgentConfigModal()">Cancel</button>
                    <button class="btn-primary" onclick="saveAgentConfig('${agent.id}')">Save Configuration</button>
                </div>
            </div>
        </div>
    `;
    
    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Show modal with animation
    setTimeout(() => {
        document.getElementById('agent-config-modal').classList.add('show');
    }, 10);
}

function closeAgentConfigModal() {
    const modal = document.getElementById('agent-config-modal');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.remove();
        }, 300);
    }
}

function updateAgentAutonomy(value) {
    document.getElementById('agent-autonomy-value').textContent = value;
}

function saveAgentConfig(agentId) {
    const config = {
        autonomyLevel: parseInt(document.getElementById('agent-autonomy').value),
        learningRate: parseFloat(document.getElementById('agent-learning-rate').value),
        confidenceThreshold: parseFloat(document.getElementById('agent-confidence-threshold').value),
        autoEvolve: document.getElementById('agent-auto-evolve').checked,
        crossCollaborate: document.getElementById('agent-cross-collaborate').checked
    };
    
    console.log(`Saving config for agent ${agentId}:`, config);
    
    // Call API to save configuration
    fetch(`/api/agents/${agentId}/config`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(config)
    })
    .then(response => response.json())
    .then(data => {
        console.log('Agent config saved:', data);
        showNotification('Configuration Saved', 'Agent configuration updated successfully', 'success');
        
        // Update local data
        const agent = DashboardState.agents.find(a => a.id === agentId);
        if (agent) {
            agent.autonomyLevel = config.autonomyLevel;
        }
        
        refreshAgentGrid();
        closeAgentConfigModal();
    })
    .catch(error => {
        console.error('Failed to save agent config:', error);
        showNotification('Configuration Failed', 'Failed to save agent configuration', 'error');
    });
}

function viewAgentLogs(agentId) {
    const agent = DashboardState.agents.find(a => a.id === agentId);
    if (!agent) return;
    
    console.log(`Viewing logs for agent: ${agentId}`);
    
    // Switch to logs section and filter by agent
    showSection('logs');
    
    // Apply agent filter (implementation would depend on log system)
    setTimeout(() => {
        const searchInput = document.getElementById('log-search');
        if (searchInput) {
            searchInput.value = agent.id;
            searchLogs();
        }
    }, 100);
}

function evolveAgent(agentId) {
    const agent = DashboardState.agents.find(a => a.id === agentId);
    if (!agent) return;
    
    if (confirm(`Trigger evolution for ${agent.name}? This will initiate autonomous improvement.`)) {
        console.log(`Triggering evolution for agent: ${agentId}`);
        
        // Update UI to show evolution in progress
        const agentCard = document.querySelector(`[data-agent-id="${agentId}"]`);
        if (agentCard) {
            const evolveBtn = agentCard.querySelector('[onclick*="evolveAgent"]');
            if (evolveBtn) {
                evolveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Evolving...';
                evolveBtn.disabled = true;
            }
        }
        
        // Call API to trigger evolution
        fetch(`/api/agents/${agentId}/evolve`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log('Agent evolution response:', data);
            showNotification(
                'Evolution Started',
                `${agent.name} evolution initiated successfully`,
                'success'
            );
            
            // Update evolution count
            agent.evolutions += 1;
            refreshAgentGrid();
        })
        .catch(error => {
            console.error('Agent evolution failed:', error);
            showNotification('Evolution Failed', `Failed to evolve ${agent.name}`, 'error');
            refreshAgentGrid();
        });
    }
}

function deployNewAgent() {
    console.log('Deploying new agent...');
    
    // Show deployment modal
    showAgentDeploymentModal();
}

function showAgentDeploymentModal() {
    const modalHTML = `
        <div class="modal-overlay" id="agent-deploy-modal">
            <div class="modal-container">
                <div class="modal-header">
                    <h3>Deploy New Agent</h3>
                    <button class="modal-close" onclick="closeAgentDeployModal()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <div class="modal-content">
                    <div class="deploy-section">
                        <h4>Agent Type</h4>
                        <select id="agent-type" class="form-select">
                            <option value="threat_hunter">Threat Hunter</option>
                            <option value="anomaly_detector">Anomaly Detector</option>
                            <option value="behavioral_analyst">Behavioral Analyst</option>
                            <option value="pattern_recognizer">Pattern Recognizer</option>
                            <option value="custom">Custom Agent</option>
                        </select>
                    </div>
                    
                    <div class="deploy-section">
                        <h4>Configuration</h4>
                        <div class="config-item">
                            <label for="new-agent-name">Agent Name</label>
                            <input type="text" id="new-agent-name" placeholder="Enter agent name">
                        </div>
                        
                        <div class="config-item">
                            <label for="new-agent-autonomy">Initial Autonomy Level</label>
                            <input type="range" id="new-agent-autonomy" min="1" max="10" value="5">
                            <span id="new-agent-autonomy-value">5</span>
                        </div>
                        
                        <div class="config-item">
                            <label>
                                <input type="checkbox" id="new-agent-auto-start" checked>
                                Start automatically after deployment
                            </label>
                        </div>
                    </div>
                </div>
                
                <div class="modal-footer">
                    <button class="btn-secondary" onclick="closeAgentDeployModal()">Cancel</button>
                    <button class="btn-primary" onclick="executeAgentDeployment()">Deploy Agent</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    setTimeout(() => {
        document.getElementById('agent-deploy-modal').classList.add('show');
        document.getElementById('new-agent-autonomy').addEventListener('input', function() {
            document.getElementById('new-agent-autonomy-value').textContent = this.value;
        });
    }, 10);
}

function closeAgentDeployModal() {
    const modal = document.getElementById('agent-deploy-modal');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.remove();
        }, 300);
    }
}

function executeAgentDeployment() {
    const config = {
        type: document.getElementById('agent-type').value,
        name: document.getElementById('new-agent-name').value,
        autonomyLevel: parseInt(document.getElementById('new-agent-autonomy').value),
        autoStart: document.getElementById('new-agent-auto-start').checked
    };
    
    if (!config.name.trim()) {
        alert('Please enter a name for the agent');
        return;
    }
    
    console.log('Deploying new agent:', config);
    
    // Simulate deployment
    const newAgent = {
        id: `agent_${Date.now()}`,
        name: config.name,
        status: config.autoStart ? 'active' : 'inactive',
        actions: 0,
        evolutions: 0,
        accuracy: 85.0,
        autonomyLevel: config.autonomyLevel
    };
    
    DashboardState.agents.push(newAgent);
    DashboardState.stats.activeAgents += config.autoStart ? 1 : 0;
    
    refreshAgentGrid();
    updateStats();
    closeAgentDeployModal();
    
    showNotification(
        'Agent Deployed',
        `${config.name} has been deployed successfully`,
        'success'
    );
}

function updateAgentStats() {
    const activeCount = DashboardState.agents.filter(a => a.status === 'active').length;
    DashboardState.stats.activeAgents = activeCount;
    updateStats();
}

// Export functions for global use
window.toggleAgent = toggleAgent;
window.configureAgent = configureAgent;
window.viewAgentLogs = viewAgentLogs;
window.evolveAgent = evolveAgent;
window.deployNewAgent = deployNewAgent;
window.refreshAgentGrid = refreshAgentGrid;