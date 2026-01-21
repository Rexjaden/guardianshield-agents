/**
 * GuardianShield 3D Agent Integration
 * Connects 3D agent visualizations with the main dashboard
 */

class AgentVisualizationManager {
    constructor() {
        this.agent3DRenderer = null;
        this.agent4DRenderer = null;
        this.currentMode = '3d';
        this.isInitialized = false;
        
        this.agentTypes = [
            'master_key',
            'threat_monitor', 
            'behavioral_analytics',
            'learning_agent',
            'genetic_evolver',
            'data_ingestion',
            'external_agent'
        ];
        
        this.mockAgentData = this.generateMockAgentData();
    }
    
    init() {
        if (this.isInitialized) return;
        
        // Create 3D visualization container
        this.create3DContainer();
        
        // Initialize Three.js
        this.loadThreeJS().then(() => {
            this.setup3DRenderer();
            this.setupControls();
            this.startVisualization();
            this.isInitialized = true;
        });
    }
    
    create3DContainer() {
        // Find or create agents section
        let agentsSection = document.getElementById('agents-section');
        if (!agentsSection) {
            agentsSection = document.createElement('div');
            agentsSection.id = 'agents-section';
            agentsSection.className = 'dashboard-section';
            document.querySelector('.dashboard-grid').appendChild(agentsSection);
        }
        
        // Create 3D visualization container
        const container = document.createElement('div');
        container.innerHTML = `
            <div class="section-header">
                <h2>🛡️ Agent 3D Visualization</h2>
                <div class="agent-3d-controls">
                    <button id="toggle-3d-4d" class="btn btn-primary">Switch to 4D</button>
                    <button id="reset-camera" class="btn btn-secondary">Reset View</button>
                    <select id="agent-focus" class="form-select">
                        <option value="">Focus Agent</option>
                        <option value="master_key">Master Key Algorithm</option>
                        <option value="threat_monitor">Threat Monitor</option>
                        <option value="behavioral_analytics">Behavioral Analytics</option>
                        <option value="learning_agent">Learning Agent</option>
                        <option value="genetic_evolver">Genetic Evolver</option>
                        <option value="data_ingestion">Data Ingestion</option>
                        <option value="external_agent">External Agent</option>
                    </select>
                </div>
            </div>
            <div id="agent-3d-container" class="agent-3d-viewport">
                <div class="loading-spinner">
                    <div class="spinner"></div>
                    <p>Loading 3D Agents...</p>
                </div>
            </div>
            <div class="agent-3d-stats">
                <div class="stat-grid">
                    <div class="stat-item">
                        <span class="stat-label">Active Agents</span>
                        <span class="stat-value" id="active-agents-count">7</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Total Operations</span>
                        <span class="stat-value" id="total-operations">1,247</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Average Health</span>
                        <span class="stat-value" id="average-health">94%</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Network Load</span>
                        <span class="stat-value" id="network-load">73%</span>
                    </div>
                </div>
            </div>
        `;
        
        agentsSection.appendChild(container);
    }
    
    async loadThreeJS() {
        return new Promise((resolve, reject) => {
            // Load Three.js
            const script1 = document.createElement('script');
            script1.src = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';
            script1.onload = () => {
                // Load OrbitControls
                const script2 = document.createElement('script');
                script2.src = 'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js';
                script2.onload = resolve;
                script2.onerror = reject;
                document.head.appendChild(script2);
            };
            script1.onerror = reject;
            document.head.appendChild(script1);
        });
    }
    
    setup3DRenderer() {
        // Initialize 3D renderer
        this.agent3DRenderer = new Agent3DRenderer('agent-3d-container');
        
        // Create all agents
        this.agentTypes.forEach(agentType => {
            const agentData = this.mockAgentData[agentType];
            this.agent3DRenderer.createAgent3D(agentData);
        });
        
        // Hide loading spinner
        const spinner = document.querySelector('.loading-spinner');
        if (spinner) spinner.style.display = 'none';
    }
    
    setupControls() {
        // 3D/4D toggle
        const toggle3D4D = document.getElementById('toggle-3d-4d');
        if (toggle3D4D) {
            toggle3D4D.addEventListener('click', () => this.toggle3D4D());
        }
        
        // Reset camera
        const resetCamera = document.getElementById('reset-camera');
        if (resetCamera) {
            resetCamera.addEventListener('click', () => this.resetCamera());
        }
        
        // Agent focus
        const agentFocus = document.getElementById('agent-focus');
        if (agentFocus) {
            agentFocus.addEventListener('change', (e) => this.focusAgent(e.target.value));
        }
    }
    
    toggle3D4D() {
        const button = document.getElementById('toggle-3d-4d');
        const container = document.getElementById('agent-3d-container');
        
        if (this.currentMode === '3d') {
            // Switch to 4D
            this.currentMode = '4d';
            button.textContent = 'Switch to 3D';
            
            // Destroy 3D renderer
            if (this.agent3DRenderer) {
                this.agent3DRenderer.destroy();
            }
            
            // Create 4D renderer
            container.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Loading 4D Visualization...</p></div>';
            
            setTimeout(() => {
                this.agent4DRenderer = new Agent4DRenderer('agent-3d-container');
                
                // Create all agents in 4D
                this.agentTypes.forEach(agentType => {
                    const agentData = this.mockAgentData[agentType];
                    this.agent4DRenderer.createAgent4D(agentData);
                });
                
                const spinner = document.querySelector('.loading-spinner');
                if (spinner) spinner.style.display = 'none';
            }, 1000);
            
        } else {
            // Switch to 3D
            this.currentMode = '3d';
            button.textContent = 'Switch to 4D';
            
            // Destroy 4D renderer
            if (this.agent4DRenderer) {
                this.agent4DRenderer.destroy();
            }
            
            // Recreate 3D renderer
            container.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Loading 3D Visualization...</p></div>';
            
            setTimeout(() => {
                this.setup3DRenderer();
            }, 1000);
        }
    }
    
    resetCamera() {
        const renderer = this.currentMode === '3d' ? this.agent3DRenderer : this.agent4DRenderer;
        if (renderer && renderer.camera) {
            renderer.camera.position.set(0, 5, 10);
            renderer.controls.reset();
        }
    }
    
    focusAgent(agentId) {
        if (!agentId) return;
        
        const renderer = this.currentMode === '3d' ? this.agent3DRenderer : this.agent4DRenderer;
        if (!renderer) return;
        
        const agent = renderer.agents.get(agentId);
        if (agent) {
            const position = agent.group.position;
            renderer.camera.position.set(
                position.x + 5,
                position.y + 3,
                position.z + 5
            );
            renderer.controls.target.copy(position);
        }
    }
    
    startVisualization() {
        // Start real-time updates
        this.updateLoop();
        
        // Start data simulation
        this.simulateAgentData();
    }
    
    updateLoop() {
        // Update stats
        this.updateStats();
        
        // Update agent data
        this.updateAgentStates();
        
        // Schedule next update
        setTimeout(() => this.updateLoop(), 1000);
    }
    
    updateStats() {
        const activeCount = document.getElementById('active-agents-count');
        const totalOps = document.getElementById('total-operations');
        const avgHealth = document.getElementById('average-health');
        const networkLoad = document.getElementById('network-load');
        
        if (activeCount) {
            const active = this.agentTypes.filter(type => 
                this.mockAgentData[type].health > 0.1
            ).length;
            activeCount.textContent = active;
        }
        
        if (totalOps) {
            const current = parseInt(totalOps.textContent.replace(',', ''));
            totalOps.textContent = (current + Math.floor(Math.random() * 5)).toLocaleString();
        }
        
        if (avgHealth) {
            const totalHealth = this.agentTypes.reduce((sum, type) => 
                sum + this.mockAgentData[type].health, 0
            );
            const average = Math.round((totalHealth / this.agentTypes.length) * 100);
            avgHealth.textContent = `${average}%`;
        }
        
        if (networkLoad) {
            const load = 60 + Math.random() * 30;
            networkLoad.textContent = `${Math.round(load)}%`;
        }
    }
    
    updateAgentStates() {
        const renderer = this.currentMode === '3d' ? this.agent3DRenderer : this.agent4DRenderer;
        if (!renderer) return;
        
        this.agentTypes.forEach(agentType => {
            const agentData = this.mockAgentData[agentType];
            
            // Simulate health fluctuations
            agentData.health += (Math.random() - 0.5) * 0.02;
            agentData.health = Math.max(0, Math.min(1, agentData.health));
            
            // Simulate activity changes
            agentData.activity += (Math.random() - 0.5) * 0.1;
            agentData.activity = Math.max(0, Math.min(1, agentData.activity));
            
            // Update 3D representation
            renderer.updateAgent(agentType, agentData);
        });
    }
    
    simulateAgentData() {
        // Simulate various agent events
        const events = [
            'Threat detected and neutralized',
            'Learning algorithm updated',
            'Genetic evolution completed',
            'Data ingestion rate optimized',
            'Behavioral pattern analyzed',
            'External connection established',
            'Master key algorithm evolved'
        ];
        
        setInterval(() => {
            const event = events[Math.floor(Math.random() * events.length)];
            const agentType = this.agentTypes[Math.floor(Math.random() * this.agentTypes.length)];
            
            // Create notification
            this.createNotification(`Agent ${agentType}: ${event}`);
        }, 5000);
    }
    
    createNotification(message) {
        // Add to existing notification system if available
        if (window.DashboardState && window.DashboardState.addNotification) {
            window.DashboardState.addNotification(message, 'info');
        } else {
            console.log(`🛡️ ${message}`);
        }
    }
    
    generateMockAgentData() {
        const data = {};
        
        this.agentTypes.forEach(agentType => {
            data[agentType] = {
                id: agentType,
                type: agentType,
                health: 0.7 + Math.random() * 0.3,
                activity: 0.5 + Math.random() * 0.5,
                status: 'active',
                lastUpdate: new Date(),
                operations: Math.floor(Math.random() * 1000),
                efficiency: 0.8 + Math.random() * 0.2
            };
        });
        
        return data;
    }
    
    destroy() {
        if (this.agent3DRenderer) {
            this.agent3DRenderer.destroy();
        }
        if (this.agent4DRenderer) {
            this.agent4DRenderer.destroy();
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Wait for dashboard to be ready
    setTimeout(() => {
        window.agentVisualizationManager = new AgentVisualizationManager();
        window.agentVisualizationManager.init();
    }, 1000);
});

// Export for global access
window.AgentVisualizationManager = AgentVisualizationManager;