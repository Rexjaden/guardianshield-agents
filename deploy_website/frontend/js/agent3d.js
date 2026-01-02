/**
 * GuardianShield 3D Agent Visualization Engine
 * Advanced 3D/4D representations of autonomous agents
 */

class Agent3DRenderer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.agents = new Map();
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.animationFrame = null;
        this.time = 0;
        
        this.init();
    }
    
    init() {
        // Create Three.js scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x0a0a0a);
        
        // Setup camera
        this.camera = new THREE.PerspectiveCamera(
            75, 
            this.container.clientWidth / this.container.clientHeight, 
            0.1, 
            1000
        );
        this.camera.position.set(0, 5, 10);
        
        // Create renderer
        this.renderer = new THREE.WebGLRenderer({ 
            antialias: true, 
            alpha: true 
        });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.container.appendChild(this.renderer.domElement);
        
        // Add lighting
        this.setupLighting();
        
        // Add controls
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        
        // Start animation loop
        this.animate();
        
        // Handle resize
        window.addEventListener('resize', () => this.onWindowResize());
    }
    
    setupLighting() {
        // Ambient light
        const ambientLight = new THREE.AmbientLight(0x404040, 0.3);
        this.scene.add(ambientLight);
        
        // Main directional light
        const directionalLight = new THREE.DirectionalLight(0x00ffff, 1);
        directionalLight.position.set(10, 10, 5);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        this.scene.add(directionalLight);
        
        // Secondary light for rim lighting
        const rimLight = new THREE.DirectionalLight(0xff00ff, 0.5);
        rimLight.position.set(-10, 5, -5);
        this.scene.add(rimLight);
        
        // Point lights for atmosphere
        const pointLight1 = new THREE.PointLight(0x00ff00, 0.3, 20);
        pointLight1.position.set(5, 3, 5);
        this.scene.add(pointLight1);
        
        const pointLight2 = new THREE.PointLight(0xff0000, 0.3, 20);
        pointLight2.position.set(-5, 3, -5);
        this.scene.add(pointLight2);
    }
    
    createAgent3D(agentData) {
        const agentGroup = new THREE.Group();
        
        // Core agent body (geometric form based on agent type)
        const core = this.createAgentCore(agentData.type);
        agentGroup.add(core);
        
        // Energy field/aura
        const energyField = this.createEnergyField(agentData);
        agentGroup.add(energyField);
        
        // Data streams
        const dataStreams = this.createDataStreams(agentData);
        agentGroup.add(dataStreams);
        
        // Neural network visualization
        const neuralNet = this.createNeuralNetwork(agentData);
        agentGroup.add(neuralNet);
        
        // Status indicators
        const statusIndicators = this.createStatusIndicators(agentData);
        agentGroup.add(statusIndicators);
        
        // Position agent
        const position = this.getAgentPosition(agentData.id);
        agentGroup.position.set(position.x, position.y, position.z);
        
        // Add to scene and store reference
        this.scene.add(agentGroup);
        this.agents.set(agentData.id, {
            group: agentGroup,
            core: core,
            energyField: energyField,
            dataStreams: dataStreams,
            neuralNet: neuralNet,
            statusIndicators: statusIndicators,
            data: agentData
        });
        
        return agentGroup;
    }
    
    createAgentCore(agentType) {
        let geometry, material;
        
        switch(agentType) {
            case 'master_key':
                // Dodecahedron for master key algorithm
                geometry = new THREE.DodecahedronGeometry(1, 0);
                material = new THREE.MeshPhongMaterial({
                    color: 0xffd700,
                    emissive: 0x332200,
                    transparent: true,
                    opacity: 0.8
                });
                break;
                
            case 'threat_monitor':
                // Octahedron for threat monitoring
                geometry = new THREE.OctahedronGeometry(1, 0);
                material = new THREE.MeshPhongMaterial({
                    color: 0xff4444,
                    emissive: 0x220000,
                    transparent: true,
                    opacity: 0.8
                });
                break;
                
            case 'behavioral_analytics':
                // Icosahedron for behavioral analytics
                geometry = new THREE.IcosahedronGeometry(1, 0);
                material = new THREE.MeshPhongMaterial({
                    color: 0x44ff44,
                    emissive: 0x002200,
                    transparent: true,
                    opacity: 0.8
                });
                break;
                
            case 'learning_agent':
                // Tetrahedron for learning
                geometry = new THREE.TetrahedronGeometry(1, 0);
                material = new THREE.MeshPhongMaterial({
                    color: 0x4444ff,
                    emissive: 0x000022,
                    transparent: true,
                    opacity: 0.8
                });
                break;
                
            case 'genetic_evolver':
                // Complex geometry for evolution
                geometry = new THREE.TorusKnotGeometry(0.8, 0.3, 100, 16);
                material = new THREE.MeshPhongMaterial({
                    color: 0xff44ff,
                    emissive: 0x220022,
                    transparent: true,
                    opacity: 0.8
                });
                break;
                
            case 'data_ingestion':
                // Cylinder for data processing
                geometry = new THREE.CylinderGeometry(0.5, 1, 1.5, 8);
                material = new THREE.MeshPhongMaterial({
                    color: 0x44ffff,
                    emissive: 0x002222,
                    transparent: true,
                    opacity: 0.8
                });
                break;
                
            case 'external_agent':
                // Sphere for external connections
                geometry = new THREE.SphereGeometry(1, 16, 16);
                material = new THREE.MeshPhongMaterial({
                    color: 0xffff44,
                    emissive: 0x222200,
                    transparent: true,
                    opacity: 0.8
                });
                break;
                
            default:
                // Default cube
                geometry = new THREE.BoxGeometry(1, 1, 1);
                material = new THREE.MeshPhongMaterial({
                    color: 0x888888,
                    emissive: 0x111111,
                    transparent: true,
                    opacity: 0.8
                });
        }
        
        const mesh = new THREE.Mesh(geometry, material);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        
        return mesh;
    }
    
    createEnergyField(agentData) {
        const fieldGroup = new THREE.Group();
        
        // Outer energy ring
        const ringGeometry = new THREE.RingGeometry(1.5, 2, 32);
        const ringMaterial = new THREE.MeshBasicMaterial({
            color: this.getAgentColor(agentData.type),
            transparent: true,
            opacity: 0.3,
            side: THREE.DoubleSide
        });
        const ring = new THREE.Mesh(ringGeometry, ringMaterial);
        ring.rotation.x = Math.PI / 2;
        fieldGroup.add(ring);
        
        // Energy particles
        const particleCount = 50;
        const particles = new THREE.BufferGeometry();
        const positions = new Float32Array(particleCount * 3);
        const colors = new Float32Array(particleCount * 3);
        
        for(let i = 0; i < particleCount * 3; i += 3) {
            const radius = 1.5 + Math.random() * 0.5;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.random() * Math.PI;
            
            positions[i] = radius * Math.sin(phi) * Math.cos(theta);
            positions[i + 1] = radius * Math.sin(phi) * Math.sin(theta);
            positions[i + 2] = radius * Math.cos(phi);
            
            const color = new THREE.Color(this.getAgentColor(agentData.type));
            colors[i] = color.r;
            colors[i + 1] = color.g;
            colors[i + 2] = color.b;
        }
        
        particles.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        particles.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        
        const particleMaterial = new THREE.PointsMaterial({
            size: 0.05,
            vertexColors: true,
            transparent: true,
            opacity: 0.8
        });
        
        const particleSystem = new THREE.Points(particles, particleMaterial);
        fieldGroup.add(particleSystem);
        
        return fieldGroup;
    }
    
    createDataStreams(agentData) {
        const streamGroup = new THREE.Group();
        const streamCount = 6;
        
        for(let i = 0; i < streamCount; i++) {
            const curve = new THREE.CatmullRomCurve3([
                new THREE.Vector3(0, 0, 0),
                new THREE.Vector3(
                    Math.cos(i * Math.PI * 2 / streamCount) * 2,
                    Math.sin(i * 0.5) * 2,
                    Math.sin(i * Math.PI * 2 / streamCount) * 2
                ),
                new THREE.Vector3(
                    Math.cos(i * Math.PI * 2 / streamCount) * 4,
                    Math.sin(i * 0.5) * 4,
                    Math.sin(i * Math.PI * 2 / streamCount) * 4
                )
            ]);
            
            const tubeGeometry = new THREE.TubeGeometry(curve, 50, 0.02, 8, false);
            const tubeMaterial = new THREE.MeshBasicMaterial({
                color: this.getAgentColor(agentData.type),
                transparent: true,
                opacity: 0.6
            });
            
            const tube = new THREE.Mesh(tubeGeometry, tubeMaterial);
            streamGroup.add(tube);
        }
        
        return streamGroup;
    }
    
    createNeuralNetwork(agentData) {
        const networkGroup = new THREE.Group();
        const nodeCount = 12;
        const nodes = [];
        
        // Create neural nodes
        for(let i = 0; i < nodeCount; i++) {
            const nodeGeometry = new THREE.SphereGeometry(0.05, 8, 8);
            const nodeMaterial = new THREE.MeshBasicMaterial({
                color: 0xffffff,
                transparent: true,
                opacity: 0.8
            });
            
            const node = new THREE.Mesh(nodeGeometry, nodeMaterial);
            const radius = 2.5;
            const theta = (i / nodeCount) * Math.PI * 2;
            const phi = Math.sin(i * 0.5) * 0.5;
            
            node.position.set(
                radius * Math.cos(theta),
                phi,
                radius * Math.sin(theta)
            );
            
            nodes.push(node);
            networkGroup.add(node);
        }
        
        // Create connections between nodes
        for(let i = 0; i < nodeCount; i++) {
            for(let j = i + 1; j < nodeCount; j++) {
                if(Math.random() > 0.7) { // 30% connection probability
                    const points = [nodes[i].position, nodes[j].position];
                    const lineGeometry = new THREE.BufferGeometry().setFromPoints(points);
                    const lineMaterial = new THREE.LineBasicMaterial({
                        color: this.getAgentColor(agentData.type),
                        transparent: true,
                        opacity: 0.3
                    });
                    
                    const line = new THREE.Line(lineGeometry, lineMaterial);
                    networkGroup.add(line);
                }
            }
        }
        
        return networkGroup;
    }
    
    createStatusIndicators(agentData) {
        const indicatorGroup = new THREE.Group();
        
        // Health indicator
        const healthGeometry = new THREE.RingGeometry(0.8, 0.9, 16);
        const healthMaterial = new THREE.MeshBasicMaterial({
            color: agentData.health > 0.7 ? 0x00ff00 : agentData.health > 0.3 ? 0xffff00 : 0xff0000,
            transparent: true,
            opacity: 0.8,
            side: THREE.DoubleSide
        });
        const healthRing = new THREE.Mesh(healthGeometry, healthMaterial);
        healthRing.rotation.x = Math.PI / 2;
        healthRing.position.y = -2;
        indicatorGroup.add(healthRing);
        
        // Activity indicator
        const activityGeometry = new THREE.BoxGeometry(0.1, agentData.activity * 2, 0.1);
        const activityMaterial = new THREE.MeshBasicMaterial({
            color: this.getAgentColor(agentData.type),
            transparent: true,
            opacity: 0.9
        });
        const activityBar = new THREE.Mesh(activityGeometry, activityMaterial);
        activityBar.position.set(2.5, 0, 0);
        indicatorGroup.add(activityBar);
        
        return indicatorGroup;
    }
    
    getAgentColor(agentType) {
        const colors = {
            'master_key': 0xffd700,
            'threat_monitor': 0xff4444,
            'behavioral_analytics': 0x44ff44,
            'learning_agent': 0x4444ff,
            'genetic_evolver': 0xff44ff,
            'data_ingestion': 0x44ffff,
            'external_agent': 0xffff44,
            'default': 0x888888
        };
        return colors[agentType] || colors.default;
    }
    
    getAgentPosition(agentId) {
        // Arrange agents in a circle
        const agents = ['master_key', 'threat_monitor', 'behavioral_analytics', 'learning_agent', 
                       'genetic_evolver', 'data_ingestion', 'external_agent'];
        const index = agents.indexOf(agentId) || 0;
        const radius = 8;
        const angle = (index / agents.length) * Math.PI * 2;
        
        return {
            x: radius * Math.cos(angle),
            y: 0,
            z: radius * Math.sin(angle)
        };
    }
    
    updateAgent(agentId, newData) {
        const agent = this.agents.get(agentId);
        if (!agent) return;
        
        // Update status indicators
        const healthRing = agent.statusIndicators.children[0];
        if (healthRing) {
            healthRing.material.color.setHex(
                newData.health > 0.7 ? 0x00ff00 : 
                newData.health > 0.3 ? 0xffff00 : 0xff0000
            );
        }
        
        const activityBar = agent.statusIndicators.children[1];
        if (activityBar) {
            activityBar.scale.y = newData.activity;
        }
        
        // Update stored data
        agent.data = { ...agent.data, ...newData };
    }
    
    animate() {
        this.animationFrame = requestAnimationFrame(() => this.animate());
        
        this.time += 0.01;
        
        // Animate all agents
        this.agents.forEach((agent, agentId) => {
            // Rotate core
            agent.core.rotation.x += 0.005;
            agent.core.rotation.y += 0.01;
            
            // Animate energy field
            agent.energyField.rotation.y += 0.02;
            
            // Animate data streams
            agent.dataStreams.rotation.y += 0.015;
            
            // Animate neural network
            agent.neuralNet.rotation.x += 0.008;
            
            // Floating motion
            agent.group.position.y = Math.sin(this.time + agent.data.id.length) * 0.2;
        });
        
        // Update controls
        this.controls.update();
        
        // Render scene
        this.renderer.render(this.scene, this.camera);
    }
    
    onWindowResize() {
        this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    }
    
    destroy() {
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }
        if (this.renderer) {
            this.renderer.dispose();
        }
    }
}

// 4D Hypercube Agent Representation
class Agent4DRenderer extends Agent3DRenderer {
    constructor(containerId) {
        super(containerId);
        this.hypercubeTime = 0;
    }
    
    createAgent4D(agentData) {
        const agent3D = this.createAgent3D(agentData);
        
        // Add 4D hypercube visualization
        const hypercube = this.createHypercube(agentData);
        agent3D.add(hypercube);
        
        // Store 4D reference
        const agentRef = this.agents.get(agentData.id);
        agentRef.hypercube = hypercube;
        
        return agent3D;
    }
    
    createHypercube(agentData) {
        const hypercubeGroup = new THREE.Group();
        
        // Create 8 vertices of a tesseract projected to 3D
        const vertices = this.getTesseractVertices();
        const edges = this.getTesseractEdges();
        
        // Create vertex spheres
        vertices.forEach((vertex, i) => {
            const vertexGeometry = new THREE.SphereGeometry(0.03, 8, 8);
            const vertexMaterial = new THREE.MeshBasicMaterial({
                color: this.getAgentColor(agentData.type),
                transparent: true,
                opacity: 0.6
            });
            
            const vertexMesh = new THREE.Mesh(vertexGeometry, vertexMaterial);
            vertexMesh.position.set(vertex.x, vertex.y, vertex.z);
            hypercubeGroup.add(vertexMesh);
        });
        
        // Create edge lines
        edges.forEach(edge => {
            const points = [vertices[edge[0]], vertices[edge[1]]];
            const lineGeometry = new THREE.BufferGeometry().setFromPoints(points);
            const lineMaterial = new THREE.LineBasicMaterial({
                color: this.getAgentColor(agentData.type),
                transparent: true,
                opacity: 0.4
            });
            
            const line = new THREE.Line(lineGeometry, lineMaterial);
            hypercubeGroup.add(line);
        });
        
        hypercubeGroup.scale.setScalar(3);
        return hypercubeGroup;
    }
    
    getTesseractVertices() {
        // 4D tesseract vertices projected to 3D
        const w = 0.5; // 4th dimension coordinate
        return [
            new THREE.Vector3(-1, -1, -1), new THREE.Vector3(1, -1, -1),
            new THREE.Vector3(1, 1, -1), new THREE.Vector3(-1, 1, -1),
            new THREE.Vector3(-1, -1, 1), new THREE.Vector3(1, -1, 1),
            new THREE.Vector3(1, 1, 1), new THREE.Vector3(-1, 1, 1),
            new THREE.Vector3(-w, -w, -w), new THREE.Vector3(w, -w, -w),
            new THREE.Vector3(w, w, -w), new THREE.Vector3(-w, w, -w),
            new THREE.Vector3(-w, -w, w), new THREE.Vector3(w, -w, w),
            new THREE.Vector3(w, w, w), new THREE.Vector3(-w, w, w)
        ];
    }
    
    getTesseractEdges() {
        // Tesseract edge connections
        return [
            [0,1], [1,2], [2,3], [3,0], // front face
            [4,5], [5,6], [6,7], [7,4], // back face
            [0,4], [1,5], [2,6], [3,7], // connecting edges
            [8,9], [9,10], [10,11], [11,8], // inner front face
            [12,13], [13,14], [14,15], [15,12], // inner back face
            [8,12], [9,13], [10,14], [11,15], // inner connecting edges
            [0,8], [1,9], [2,10], [3,11], // outer to inner front
            [4,12], [5,13], [6,14], [7,15] // outer to inner back
        ];
    }
    
    animate() {
        super.animate();
        
        this.hypercubeTime += 0.02;
        
        // Animate 4D hypercubes
        this.agents.forEach((agent, agentId) => {
            if (agent.hypercube) {
                // Rotate through 4D space
                agent.hypercube.rotation.x = Math.sin(this.hypercubeTime) * 0.5;
                agent.hypercube.rotation.y = Math.cos(this.hypercubeTime * 0.7) * 0.5;
                agent.hypercube.rotation.z = Math.sin(this.hypercubeTime * 1.3) * 0.5;
                
                // Scale pulsing
                const scale = 1 + Math.sin(this.hypercubeTime * 2) * 0.1;
                agent.hypercube.scale.setScalar(scale * 3);
            }
        });
    }
}

// Export classes
window.Agent3DRenderer = Agent3DRenderer;
window.Agent4DRenderer = Agent4DRenderer;