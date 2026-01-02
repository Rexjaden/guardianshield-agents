#!/usr/bin/env python3
"""
GuardianShield Agent Avatar System
Handles both 2D artwork and 3D models for agent visualization
"""

import os
import base64
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import asyncio
import logging

@dataclass
class AgentAvatar:
    """Agent avatar representation supporting both 2D and 3D"""
    agent_name: str
    avatar_type: str  # "2d_artwork", "3d_model", "hybrid"
    primary_image: str  # Path to main image/model
    thumbnail: Optional[str] = None
    description: str = ""
    metadata: Dict[str, Any] = None
    
class AgentAvatarManager:
    """Manages agent avatars and visual representations"""
    
    def __init__(self, assets_dir: str = "agent_assets"):
        self.assets_dir = Path(assets_dir)
        self.avatars_dir = self.assets_dir / "avatars"
        self.avatars_dir.mkdir(parents=True, exist_ok=True)
        
        self.avatars: Dict[str, AgentAvatar] = {}
        self.logger = logging.getLogger("AgentAvatarManager")
    
    async def add_2d_avatar_from_attachment(self, agent_name: str, image_data: str, 
                                          description: str = "") -> AgentAvatar:
        """Add a 2D avatar from base64 image data"""
        
        # Create agent directory
        agent_dir = self.avatars_dir / agent_name
        agent_dir.mkdir(exist_ok=True)
        
        # Decode and save the image
        try:
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
                
            image_bytes = base64.b64decode(image_data)
            
            # Save main image
            image_path = agent_dir / f"{agent_name}_avatar.png"
            with open(image_path, 'wb') as f:
                f.write(image_bytes)
            
            # Create thumbnail (save as smaller version for now)
            thumbnail_path = agent_dir / f"{agent_name}_thumbnail.png"
            with open(thumbnail_path, 'wb') as f:
                f.write(image_bytes)  # For now, same as main
            
            # Create metadata
            metadata = {
                "created_at": "2026-01-02",
                "type": "2d_artwork",
                "description": description or f"Avatar artwork for {agent_name}",
                "characteristics": self._analyze_image_characteristics(agent_name),
                "file_size": len(image_bytes),
                "format": "png"
            }
            
            metadata_path = agent_dir / "metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Create avatar object
            avatar = AgentAvatar(
                agent_name=agent_name,
                avatar_type="2d_artwork",
                primary_image=str(image_path),
                thumbnail=str(thumbnail_path),
                description=description,
                metadata=metadata
            )
            
            self.avatars[agent_name] = avatar
            self.logger.info(f"Added 2D avatar for {agent_name}")
            
            return avatar
            
        except Exception as e:
            self.logger.error(f"Error adding 2D avatar for {agent_name}: {e}")
            raise
    
    def _analyze_image_characteristics(self, agent_name: str) -> Dict[str, Any]:
        """Analyze image and return characteristics based on agent name"""
        # This could be enhanced with actual image analysis
        characteristics = {
            "style": "dark_fantasy",
            "color_scheme": ["dark", "orange", "black"],
            "armor_type": "heavy",
            "weapon": "sword",
            "effects": ["fire", "glowing_elements"],
            "pose": "standing_ready"
        }
        
        # Customize based on agent type
        if "security" in agent_name.lower() or "guardian" in agent_name.lower():
            characteristics.update({
                "role": "protector",
                "threat_level": "high",
                "defensive_stance": True
            })
        elif "learning" in agent_name.lower():
            characteristics.update({
                "role": "scholar_warrior",
                "intelligence_focus": True
            })
        
        return characteristics
    
    async def load_all_avatars(self):
        """Load all existing avatars"""
        if not self.avatars_dir.exists():
            return
            
        for agent_dir in self.avatars_dir.iterdir():
            if agent_dir.is_dir():
                await self._load_avatar(agent_dir.name)
    
    async def _load_avatar(self, agent_name: str):
        """Load a specific agent's avatar"""
        agent_dir = self.avatars_dir / agent_name
        metadata_file = agent_dir / "metadata.json"
        
        if not metadata_file.exists():
            return
            
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Find primary image
            for ext in ['.png', '.jpg', '.jpeg']:
                image_path = agent_dir / f"{agent_name}_avatar{ext}"
                if image_path.exists():
                    break
            else:
                return
            
            thumbnail_path = agent_dir / f"{agent_name}_thumbnail.png"
            
            avatar = AgentAvatar(
                agent_name=agent_name,
                avatar_type=metadata.get("type", "2d_artwork"),
                primary_image=str(image_path),
                thumbnail=str(thumbnail_path) if thumbnail_path.exists() else None,
                description=metadata.get("description", ""),
                metadata=metadata
            )
            
            self.avatars[agent_name] = avatar
            
        except Exception as e:
            self.logger.error(f"Error loading avatar for {agent_name}: {e}")
    
    def get_avatar(self, agent_name: str) -> Optional[AgentAvatar]:
        """Get avatar for an agent"""
        return self.avatars.get(agent_name)
    
    def list_avatars(self) -> List[str]:
        """List all agents with avatars"""
        return list(self.avatars.keys())
    
    def generate_avatar_gallery_html(self) -> str:
        """Generate HTML gallery of all agent avatars"""
        
        if not self.avatars:
            return """
            <div class="no-avatars">
                <h3>No Agent Avatars Found</h3>
                <p>Upload some agent artwork to get started!</p>
            </div>
            """
        
        avatar_cards = ""
        for agent_name, avatar in self.avatars.items():
            # Convert image to base64 for embedding
            try:
                with open(avatar.primary_image, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode()
                image_src = f"data:image/png;base64,{image_data}"
            except:
                image_src = "/static/placeholder.png"
            
            characteristics = avatar.metadata.get("characteristics", {})
            char_tags = " ".join([f"<span class='tag'>{k}: {v}</span>" for k, v in list(characteristics.items())[:3]])
            
            avatar_cards += f"""
            <div class="avatar-card" data-agent="{agent_name}">
                <div class="avatar-image">
                    <img src="{image_src}" alt="{agent_name} Avatar">
                </div>
                <div class="avatar-info">
                    <h3>{agent_name.replace('_', ' ').title()}</h3>
                    <p class="description">{avatar.description[:100]}...</p>
                    <div class="characteristics">
                        {char_tags}
                    </div>
                    <div class="avatar-actions">
                        <button onclick="viewAvatar('{agent_name}')">View Details</button>
                        <button onclick="deployAgent('{agent_name}')">Deploy Agent</button>
                    </div>
                </div>
            </div>
            """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>🛡️ GuardianShield Agent Gallery</title>
            <style>
                body {{ 
                    font-family: 'Segoe UI', Arial, sans-serif; 
                    margin: 0; 
                    padding: 20px; 
                    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                    color: #fff;
                }}
                
                h1 {{ 
                    text-align: center; 
                    color: #ff6b35; 
                    text-shadow: 0 0 10px rgba(255, 107, 53, 0.5);
                    margin-bottom: 30px;
                }}
                
                .gallery-grid {{ 
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); 
                    gap: 25px; 
                    max-width: 1400px;
                    margin: 0 auto;
                }}
                
                .avatar-card {{ 
                    background: linear-gradient(145deg, #2a2a2a, #1e1e1e);
                    border-radius: 12px; 
                    padding: 20px; 
                    box-shadow: 0 8px 25px rgba(0,0,0,0.3);
                    border: 1px solid #444;
                    transition: transform 0.3s, box-shadow 0.3s;
                }}
                
                .avatar-card:hover {{
                    transform: translateY(-5px);
                    box-shadow: 0 12px 35px rgba(255, 107, 53, 0.2);
                    border-color: #ff6b35;
                }}
                
                .avatar-image {{
                    width: 100%;
                    height: 250px;
                    border-radius: 8px;
                    overflow: hidden;
                    margin-bottom: 15px;
                }}
                
                .avatar-image img {{ 
                    width: 100%; 
                    height: 100%; 
                    object-fit: cover; 
                    transition: transform 0.3s;
                }}
                
                .avatar-card:hover .avatar-image img {{
                    transform: scale(1.05);
                }}
                
                .avatar-info h3 {{ 
                    color: #ff6b35; 
                    margin: 0 0 10px 0; 
                    font-size: 1.3em;
                }}
                
                .description {{ 
                    color: #ccc; 
                    font-size: 0.9em; 
                    line-height: 1.4;
                    margin-bottom: 15px;
                }}
                
                .characteristics {{ 
                    margin: 15px 0; 
                }}
                
                .tag {{ 
                    background: rgba(255, 107, 53, 0.1);
                    color: #ff6b35;
                    padding: 3px 8px; 
                    border-radius: 12px; 
                    font-size: 0.75em;
                    border: 1px solid rgba(255, 107, 53, 0.3);
                    margin-right: 5px;
                    display: inline-block;
                    margin-bottom: 5px;
                }}
                
                .avatar-actions {{ 
                    display: flex; 
                    gap: 10px; 
                    margin-top: 15px;
                }}
                
                button {{ 
                    background: linear-gradient(135deg, #ff6b35, #ff8f65);
                    color: white; 
                    border: none; 
                    padding: 8px 16px; 
                    border-radius: 6px; 
                    cursor: pointer; 
                    font-size: 0.9em;
                    transition: background 0.3s, transform 0.2s;
                }}
                
                button:hover {{ 
                    background: linear-gradient(135deg, #e55a2b, #ff6b35);
                    transform: translateY(-2px);
                }}
                
                .stats {{ 
                    text-align: center; 
                    margin: 30px 0; 
                    color: #aaa;
                }}
            </style>
        </head>
        <body>
            <h1>🛡️ GuardianShield Agent Gallery</h1>
            
            <div class="stats">
                <p>Active Agents: {len(self.avatars)} | Ready for Deployment</p>
            </div>
            
            <div class="gallery-grid">
                {avatar_cards}
            </div>
            
            <script>
                function viewAvatar(agentName) {{
                    window.open(`/agent/profile/${{agentName}}`, '_blank');
                }}
                
                function deployAgent(agentName) {{
                    if (confirm(`Deploy ${{agentName}} agent?`)) {{
                        fetch(`/api/agent/${{agentName}}/deploy`, {{method: 'POST'}})
                        .then(response => response.json())
                        .then(data => alert(data.message))
                        .catch(error => alert('Deployment failed: ' + error));
                    }}
                }}
            </script>
        </body>
        </html>
        """

# Example usage with the attached image
async def setup_guardian_avatar():
    """Setup the guardian agent avatar from the attached image"""
    manager = AgentAvatarManager()
    
    # This would be called with the actual image data from the attachment
    # For now, creating placeholder structure
    
    print("🎭 Agent Avatar System Ready!")
    print(f"📁 Avatars directory: {manager.avatars_dir}")
    
    return manager

if __name__ == "__main__":
    asyncio.run(setup_guardian_avatar())