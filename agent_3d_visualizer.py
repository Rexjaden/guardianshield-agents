#!/usr/bin/env python3
"""
GuardianShield 3D Agent Visualization System
Handles 3D models, avatars, and visual representations for agents
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging

@dataclass
class Agent3DModel:
    """3D model representation for an agent"""
    agent_name: str
    model_path: str
    texture_path: Optional[str] = None
    animation_path: Optional[str] = None
    position: tuple = (0, 0, 0)
    rotation: tuple = (0, 0, 0)
    scale: float = 1.0
    metadata: Dict[str, Any] = None

class Agent3DVisualizer:
    """Main class for managing 3D agent visualizations"""
    
    def __init__(self, assets_dir: str = "agent_assets/3d_models"):
        self.assets_dir = Path(assets_dir)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        
        self.models: Dict[str, Agent3DModel] = {}
        self.supported_formats = ['.glb', '.gltf', '.obj', '.fbx', '.dae']
        self.texture_formats = ['.png', '.jpg', '.jpeg', '.webp', '.tga']
        
        self.logger = logging.getLogger("Agent3DVisualizer")
        
    async def load_agent_models(self):
        """Scan and load all available 3D models for agents"""
        try:
            if not self.assets_dir.exists():
                self.logger.info(f"Creating assets directory: {self.assets_dir}")
                return
                
            for agent_dir in self.assets_dir.iterdir():
                if agent_dir.is_dir():
                    await self.load_agent_model(agent_dir.name)
                    
        except Exception as e:
            self.logger.error(f"Error loading agent models: {e}")
    
    async def load_agent_model(self, agent_name: str) -> Optional[Agent3DModel]:
        """Load 3D model for a specific agent"""
        agent_path = self.assets_dir / agent_name
        
        if not agent_path.exists():
            self.logger.warning(f"No 3D assets found for agent: {agent_name}")
            return None
            
        # Look for model files
        model_file = None
        texture_file = None
        animation_file = None
        metadata_file = agent_path / "metadata.json"
        
        # Find model file
        for ext in self.supported_formats:
            potential_model = agent_path / f"{agent_name}{ext}"
            if potential_model.exists():
                model_file = str(potential_model)
                break
                
        if not model_file:
            # Look for any model file in the directory
            for file in agent_path.iterdir():
                if file.suffix.lower() in self.supported_formats:
                    model_file = str(file)
                    break
                    
        if not model_file:
            self.logger.warning(f"No 3D model file found for agent: {agent_name}")
            return None
            
        # Find texture file
        for ext in self.texture_formats:
            potential_texture = agent_path / f"{agent_name}{ext}"
            if potential_texture.exists():
                texture_file = str(potential_texture)
                break
                
        # Load metadata if exists
        metadata = {}
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading metadata for {agent_name}: {e}")
        
        # Create agent 3D model
        agent_model = Agent3DModel(
            agent_name=agent_name,
            model_path=model_file,
            texture_path=texture_file,
            animation_path=animation_file,
            metadata=metadata
        )
        
        self.models[agent_name] = agent_model
        self.logger.info(f"Loaded 3D model for agent: {agent_name}")
        
        return agent_model
    
    def get_agent_model(self, agent_name: str) -> Optional[Agent3DModel]:
        """Get 3D model for an agent"""
        return self.models.get(agent_name)
    
    def list_available_agents(self) -> List[str]:
        """List all agents with 3D models"""
        return list(self.models.keys())
    
    async def add_agent_model(self, agent_name: str, model_data: bytes, 
                            model_format: str, texture_data: bytes = None):
        """Add a new 3D model for an agent"""
        agent_dir = self.assets_dir / agent_name
        agent_dir.mkdir(exist_ok=True)
        
        # Save model file
        model_path = agent_dir / f"{agent_name}.{model_format}"
        with open(model_path, 'wb') as f:
            f.write(model_data)
            
        # Save texture if provided
        texture_path = None
        if texture_data:
            texture_path = agent_dir / f"{agent_name}_texture.png"
            with open(texture_path, 'wb') as f:
                f.write(texture_data)
                
        # Create metadata
        metadata = {
            "created_at": asyncio.get_event_loop().time(),
            "format": model_format,
            "has_texture": texture_data is not None
        }
        
        metadata_path = agent_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        # Load the model
        await self.load_agent_model(agent_name)
        
    def generate_web_viewer_html(self, agent_name: str) -> str:
        """Generate HTML for web-based 3D viewer"""
        model = self.get_agent_model(agent_name)
        if not model:
            return f"<p>No 3D model available for agent: {agent_name}</p>"
            
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{agent_name} 3D Agent</title>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
            <style>
                body {{ margin: 0; background: #000; }}
                #container {{ width: 100vw; height: 100vh; }}
                #info {{ position: absolute; top: 10px; left: 10px; color: white; }}
            </style>
        </head>
        <body>
            <div id="container"></div>
            <div id="info">
                <h2>{agent_name} Agent</h2>
                <p>3D Model: {os.path.basename(model.model_path)}</p>
            </div>
            
            <script>
                // Three.js 3D viewer setup
                const scene = new THREE.Scene();
                const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
                const renderer = new THREE.WebGLRenderer();
                
                renderer.setSize(window.innerWidth, window.innerHeight);
                document.getElementById('container').appendChild(renderer.domElement);
                
                // Lighting
                const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
                scene.add(ambientLight);
                
                const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
                directionalLight.position.set(1, 1, 1);
                scene.add(directionalLight);
                
                // Load model
                const loader = new THREE.GLTFLoader();
                loader.load('{model.model_path}', function(gltf) {{
                    scene.add(gltf.scene);
                    
                    // Position camera
                    camera.position.z = 5;
                    
                    // Animation loop
                    function animate() {{
                        requestAnimationFrame(animate);
                        gltf.scene.rotation.y += 0.01;
                        renderer.render(scene, camera);
                    }}
                    animate();
                }});
                
                // Handle window resize
                window.addEventListener('resize', function() {{
                    camera.aspect = window.innerWidth / window.innerHeight;
                    camera.updateProjectionMatrix();
                    renderer.setSize(window.innerWidth, window.innerHeight);
                }});
            </script>
        </body>
        </html>
        """
        
        return html
    
    async def create_agent_showcase(self) -> str:
        """Create an HTML showcase of all agents"""
        await self.load_agent_models()
        
        agents_html = ""
        for agent_name in self.list_available_agents():
            model = self.get_agent_model(agent_name)
            agents_html += f"""
            <div class="agent-card">
                <h3>{agent_name}</h3>
                <div class="model-preview" data-agent="{agent_name}">
                    <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjIwMCIgaGVpZ2h0PSIxNTAiIGZpbGw9IiNmMGYwZjAiLz4KPHRleHQgeD0iMTAwIiB5PSI3NSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE0IiBmaWxsPSIjMzMzIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+M0QgTW9kZWw8L3RleHQ+Cjwvc3ZnPgo=" 
                         alt="{agent_name} 3D Model">
                </div>
                <p>Model: {os.path.basename(model.model_path) if model else 'Not loaded'}</p>
                <button onclick="viewAgent('{agent_name}')">View 3D</button>
            </div>
            """
            
        showcase_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>GuardianShield Agents 3D Showcase</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                h1 {{ text-align: center; color: #333; }}
                .agents-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }}
                .agent-card {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
                .model-preview {{ width: 100%; height: 150px; background: #eee; border-radius: 4px; margin: 10px 0; }}
                .model-preview img {{ width: 100%; height: 100%; object-fit: cover; border-radius: 4px; }}
                button {{ background: #007bff; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }}
                button:hover {{ background: #0056b3; }}
                .no-agents {{ text-align: center; color: #666; margin: 50px 0; }}
            </style>
        </head>
        <body>
            <h1>🛡️ GuardianShield Agents 3D Gallery</h1>
            
            <div class="agents-grid">
                {agents_html if agents_html else '<div class="no-agents">No 3D agent models found. Add some 3D models to get started!</div>'}
            </div>
            
            <script>
                function viewAgent(agentName) {{
                    window.open(`/agent/3d/${{agentName}}`, '_blank');
                }}
            </script>
        </body>
        </html>
        """
        
        return showcase_html

# Usage example and setup
async def setup_agent_3d_system():
    """Setup the 3D agent visualization system"""
    visualizer = Agent3DVisualizer()
    
    # Create directory structure
    os.makedirs("agent_assets/3d_models", exist_ok=True)
    
    # Create example metadata for agents
    agent_names = [
        "behavioral_agent", "learning_agent", "dmer_agent", 
        "security_agent", "network_agent", "validator_agent"
    ]
    
    for agent_name in agent_names:
        agent_dir = Path(f"agent_assets/3d_models/{agent_name}")
        agent_dir.mkdir(exist_ok=True)
        
        # Create placeholder metadata
        metadata = {
            "agent_type": agent_name,
            "description": f"3D visualization for {agent_name}",
            "capabilities": ["3d_rendering", "animation", "interaction"],
            "created_at": "2026-01-02"
        }
        
        with open(agent_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
    
    return visualizer

if __name__ == "__main__":
    async def main():
        visualizer = await setup_agent_3d_system()
        await visualizer.load_agent_models()
        
        # Generate showcase
        showcase = await visualizer.create_agent_showcase()
        with open("agent_3d_showcase.html", 'w', encoding='utf-8') as f:
            f.write(showcase)
            
        print("✅ 3D Agent Visualization System Setup Complete!")
        print(f"📁 Assets directory: {visualizer.assets_dir}")
        print(f"🎭 Available agents: {visualizer.list_available_agents()}")
        print("📄 Generated: agent_3d_showcase.html")
        
    asyncio.run(main())