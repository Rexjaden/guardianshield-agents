#!/usr/bin/env python3
"""
GuardianShield Agent Physical Form Integration System
====================================================

Advanced system for integrating physical forms, avatars, and visual representations
for all four GuardianShield agents: Prometheus, Silva, Turlo, and Lirto.

This system is designed to accept, process, and manage physical forms
once uploaded by the user, creating immersive agent experiences.
"""

import asyncio
import json
import logging
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import hashlib
import uuid
import base64
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class AgentPhysicalForm:
    """Data class for agent physical form specifications"""
    agent_name: str
    form_type: str  # "avatar", "3d_model", "image", "animation"
    file_path: Optional[str] = None
    file_format: Optional[str] = None  # "png", "jpg", "glb", "fbx", "mp4", etc.
    dimensions: Optional[Dict[str, int]] = None  # width, height, depth
    color_scheme: Optional[Dict[str, str]] = None  # primary, secondary, accent colors
    characteristics: Optional[Dict[str, Any]] = None  # physical traits
    animation_capabilities: Optional[List[str]] = None  # supported animations
    interaction_points: Optional[List[Dict[str, Any]]] = None  # clickable/interactive areas
    metadata: Optional[Dict[str, Any]] = None  # additional form data
    creation_timestamp: float = 0
    last_updated: float = 0
    is_active: bool = True

class PhysicalFormManager:
    """Manages physical forms and visual representations for all agents"""
    
    def __init__(self, forms_directory: str = "agent_physical_forms"):
        self.forms_dir = Path(forms_directory)
        self.forms_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for each agent
        self.agent_dirs = {}
        for agent in ['prometheus', 'silva', 'turlo', 'lirto']:
            agent_dir = self.forms_dir / agent
            agent_dir.mkdir(exist_ok=True)
            self.agent_dirs[agent] = agent_dir
        
        # Initialize forms database
        self.forms_db = self._init_forms_database()
        
        # Current active forms for each agent
        self.active_forms = {
            'prometheus': None,
            'silva': None,
            'turlo': None,
            'lirto': None
        }
        
        # Form processing capabilities
        self.supported_formats = {
            'image': ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'],
            '3d_model': ['glb', 'gltf', 'fbx', 'obj', 'dae', 'blend'],
            'animation': ['mp4', 'webm', 'gif', 'mov', 'avi'],
            'avatar': ['vrm', 'vroid', 'ready_player_me']
        }
        
        logger.info(f"Physical Form Manager initialized")
        logger.info(f"Agent directories created: {list(self.agent_dirs.keys())}")
    
    def _init_forms_database(self) -> sqlite3.Connection:
        """Initialize database for storing physical form data"""
        db_path = self.forms_dir / "agent_forms.db"
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS agent_forms (
                id TEXT PRIMARY KEY,
                agent_name TEXT NOT NULL,
                form_type TEXT NOT NULL,
                file_path TEXT,
                file_format TEXT,
                dimensions TEXT,
                color_scheme TEXT,
                characteristics TEXT,
                animation_capabilities TEXT,
                interaction_points TEXT,
                metadata TEXT,
                creation_timestamp REAL NOT NULL,
                last_updated REAL DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                file_size_bytes INTEGER DEFAULT 0,
                file_hash TEXT
            );
            
            CREATE TABLE IF NOT EXISTS form_interactions (
                id TEXT PRIMARY KEY,
                agent_name TEXT NOT NULL,
                form_id TEXT NOT NULL,
                interaction_type TEXT NOT NULL,
                interaction_data TEXT NOT NULL,
                timestamp REAL NOT NULL,
                user_id TEXT,
                session_id TEXT
            );
            
            CREATE TABLE IF NOT EXISTS form_animations (
                id TEXT PRIMARY KEY,
                agent_name TEXT NOT NULL,
                form_id TEXT NOT NULL,
                animation_name TEXT NOT NULL,
                animation_type TEXT NOT NULL,
                trigger_conditions TEXT,
                duration_seconds REAL DEFAULT 1.0,
                loop_enabled BOOLEAN DEFAULT FALSE,
                animation_data TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_agent_forms ON agent_forms(agent_name);
            CREATE INDEX IF NOT EXISTS idx_form_type ON agent_forms(form_type);
            CREATE INDEX IF NOT EXISTS idx_active_forms ON agent_forms(is_active);
        """)
        
        conn.commit()
        return conn
    
    def get_agent_form_directory(self, agent_name: str) -> Path:
        """Get the directory path for a specific agent's forms"""
        return self.agent_dirs.get(agent_name.lower())
    
    def register_physical_form(self, form_data: AgentPhysicalForm) -> str:
        """Register a new physical form for an agent"""
        form_id = str(uuid.uuid4())
        timestamp = time.time()
        
        # Update timestamps
        form_data.creation_timestamp = timestamp
        form_data.last_updated = timestamp
        
        # Calculate file hash if file exists
        file_hash = None
        file_size = 0
        if form_data.file_path and os.path.exists(form_data.file_path):
            file_hash = self._calculate_file_hash(form_data.file_path)
            file_size = os.path.getsize(form_data.file_path)
        
        # Store in database
        self.forms_db.execute("""
            INSERT INTO agent_forms
            (id, agent_name, form_type, file_path, file_format, dimensions,
             color_scheme, characteristics, animation_capabilities, 
             interaction_points, metadata, creation_timestamp, last_updated,
             is_active, file_size_bytes, file_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            form_id, form_data.agent_name, form_data.form_type,
            form_data.file_path, form_data.file_format,
            json.dumps(form_data.dimensions) if form_data.dimensions else None,
            json.dumps(form_data.color_scheme) if form_data.color_scheme else None,
            json.dumps(form_data.characteristics) if form_data.characteristics else None,
            json.dumps(form_data.animation_capabilities) if form_data.animation_capabilities else None,
            json.dumps(form_data.interaction_points) if form_data.interaction_points else None,
            json.dumps(form_data.metadata) if form_data.metadata else None,
            timestamp, timestamp, form_data.is_active, file_size, file_hash
        ))
        
        self.forms_db.commit()
        
        # Set as active form if none exists or if explicitly requested
        if not self.active_forms[form_data.agent_name] or form_data.is_active:
            self.set_active_form(form_data.agent_name, form_id)
        
        logger.info(f"Registered physical form {form_id} for agent {form_data.agent_name}")
        return form_id
    
    def upload_physical_form(self, agent_name: str, file_path: str, 
                           form_type: str = None, metadata: Dict[str, Any] = None) -> str:
        """Upload and process a physical form file for an agent"""
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Form file not found: {file_path}")
        
        agent_name = agent_name.lower()
        if agent_name not in self.agent_dirs:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        # Detect form type and format from file
        file_ext = Path(file_path).suffix.lower().lstrip('.')
        detected_form_type = self._detect_form_type(file_ext)
        
        if not detected_form_type:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        form_type = form_type or detected_form_type
        
        # Copy file to agent directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{agent_name}_{form_type}_{timestamp}.{file_ext}"
        destination_path = self.agent_dirs[agent_name] / new_filename
        
        # Copy file (in production, you'd use shutil.copy2)
        with open(file_path, 'rb') as src, open(destination_path, 'wb') as dst:
            dst.write(src.read())
        
        # Extract metadata from file
        extracted_metadata = self._extract_file_metadata(destination_path)
        if metadata:
            extracted_metadata.update(metadata)
        
        # Create form data
        form_data = AgentPhysicalForm(
            agent_name=agent_name,
            form_type=form_type,
            file_path=str(destination_path),
            file_format=file_ext,
            metadata=extracted_metadata
        )
        
        # Auto-detect characteristics based on agent
        form_data.characteristics = self._generate_agent_characteristics(agent_name)
        form_data.color_scheme = self._generate_agent_colors(agent_name)
        
        # Register the form
        form_id = self.register_physical_form(form_data)
        
        logger.info(f"Uploaded physical form for {agent_name}: {new_filename}")
        return form_id
    
    def set_active_form(self, agent_name: str, form_id: str):
        """Set the active physical form for an agent"""
        agent_name = agent_name.lower()
        
        # Deactivate all current forms for this agent
        self.forms_db.execute("""
            UPDATE agent_forms 
            SET is_active = FALSE 
            WHERE agent_name = ?
        """, (agent_name,))
        
        # Activate the specified form
        self.forms_db.execute("""
            UPDATE agent_forms 
            SET is_active = TRUE, last_updated = ?
            WHERE id = ? AND agent_name = ?
        """, (time.time(), form_id, agent_name))
        
        self.forms_db.commit()
        
        # Update local cache
        self.active_forms[agent_name] = form_id
        
        logger.info(f"Set active form for {agent_name}: {form_id}")
    
    def get_active_form(self, agent_name: str) -> Optional[AgentPhysicalForm]:
        """Get the currently active physical form for an agent"""
        agent_name = agent_name.lower()
        
        cursor = self.forms_db.execute("""
            SELECT * FROM agent_forms 
            WHERE agent_name = ? AND is_active = TRUE
            ORDER BY last_updated DESC 
            LIMIT 1
        """, (agent_name,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        # Convert row to AgentPhysicalForm
        return self._row_to_form_data(row)
    
    def get_all_agent_forms(self, agent_name: str) -> List[AgentPhysicalForm]:
        """Get all physical forms for an agent"""
        agent_name = agent_name.lower()
        
        cursor = self.forms_db.execute("""
            SELECT * FROM agent_forms 
            WHERE agent_name = ?
            ORDER BY creation_timestamp DESC
        """, (agent_name,))
        
        forms = []
        for row in cursor.fetchall():
            forms.append(self._row_to_form_data(row))
        
        return forms
    
    def add_animation(self, agent_name: str, form_id: str, animation_name: str,
                     animation_type: str, animation_data: Dict[str, Any] = None) -> str:
        """Add an animation to an agent's physical form"""
        animation_id = str(uuid.uuid4())
        
        self.forms_db.execute("""
            INSERT INTO form_animations
            (id, agent_name, form_id, animation_name, animation_type,
             trigger_conditions, duration_seconds, loop_enabled, animation_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            animation_id, agent_name.lower(), form_id, animation_name,
            animation_type, json.dumps({}), 1.0, False,
            json.dumps(animation_data) if animation_data else '{}'
        ))
        
        self.forms_db.commit()
        logger.info(f"Added animation {animation_name} to {agent_name} form {form_id}")
        return animation_id
    
    def get_agent_animations(self, agent_name: str, form_id: str = None) -> List[Dict]:
        """Get all animations for an agent's forms"""
        agent_name = agent_name.lower()
        
        query = """
            SELECT * FROM form_animations 
            WHERE agent_name = ?
        """
        params = [agent_name]
        
        if form_id:
            query += " AND form_id = ?"
            params.append(form_id)
        
        query += " ORDER BY animation_name"
        
        cursor = self.forms_db.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        
        animations = []
        for row in cursor.fetchall():
            animation = dict(zip(columns, row))
            # Parse JSON fields
            for field in ['trigger_conditions', 'animation_data']:
                if animation[field]:
                    animation[field] = json.loads(animation[field])
            animations.append(animation)
        
        return animations
    
    def _detect_form_type(self, file_extension: str) -> Optional[str]:
        """Detect form type based on file extension"""
        for form_type, extensions in self.supported_formats.items():
            if file_extension in extensions:
                return form_type
        return None
    
    def _extract_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from uploaded file"""
        metadata = {
            'filename': file_path.name,
            'file_size': os.path.getsize(file_path),
            'upload_timestamp': time.time()
        }
        
        # Add format-specific metadata extraction here
        file_ext = file_path.suffix.lower()
        
        if file_ext in ['.png', '.jpg', '.jpeg']:
            # For images, you could extract dimensions using PIL
            metadata['extracted_type'] = 'image'
            
        elif file_ext in ['.glb', '.gltf']:
            # For 3D models, you could extract model info
            metadata['extracted_type'] = '3d_model'
            
        elif file_ext in ['.mp4', '.webm']:
            # For videos, you could extract duration, fps, etc.
            metadata['extracted_type'] = 'animation'
        
        return metadata
    
    def _generate_agent_characteristics(self, agent_name: str) -> Dict[str, Any]:
        """Generate default physical characteristics based on agent personality"""
        characteristics = {
            'prometheus': {
                'personality_traits': ['methodical', 'analytical', 'reliable'],
                'visual_style': 'professional_technical',
                'preferred_poses': ['thinking', 'analyzing', 'presenting'],
                'energy_level': 'focused_intensity',
                'interaction_style': 'informative_guidance'
            },
            'silva': {
                'personality_traits': ['alert', 'protective', 'adaptive'],
                'visual_style': 'guardian_warrior',
                'preferred_poses': ['vigilant', 'defensive', 'scanning'],
                'energy_level': 'high_awareness',
                'interaction_style': 'protective_advisory'
            },
            'turlo': {
                'personality_traits': ['observant', 'analytical', 'responsive'],
                'visual_style': 'modern_analyst',
                'preferred_poses': ['observing', 'analyzing', 'responding'],
                'energy_level': 'calm_alertness',
                'interaction_style': 'behavioral_insights'
            },
            'lirto': {
                'personality_traits': ['strategic', 'exclusive', 'masterful'],
                'visual_style': 'elite_advisor',
                'preferred_poses': ['commanding', 'strategic', 'exclusive'],
                'energy_level': 'confident_authority',
                'interaction_style': 'exclusive_consultation'
            }
        }
        
        return characteristics.get(agent_name, {})
    
    def _generate_agent_colors(self, agent_name: str) -> Dict[str, str]:
        """Generate default color schemes based on agent identity"""
        color_schemes = {
            'prometheus': {
                'primary': '#FF6B35',      # Fire orange
                'secondary': '#F7931E',    # Bright orange  
                'accent': '#FFE66D',       # Warm yellow
                'background': '#2C1810',   # Dark warm
                'text': '#FFFFFF'
            },
            'silva': {
                'primary': '#4F7942',      # Forest green
                'secondary': '#6B8E5A',    # Sage green
                'accent': '#8FBC8F',       # Light green
                'background': '#1C2C1C',   # Dark green
                'text': '#E8F5E8'
            },
            'turlo': {
                'primary': '#4169E1',      # Royal blue
                'secondary': '#6495ED',    # Cornflower blue
                'accent': '#87CEEB',       # Sky blue
                'background': '#0F1419',   # Dark blue
                'text': '#F0F8FF'
            },
            'lirto': {
                'primary': '#8A2BE2',      # Blue violet
                'secondary': '#9370DB',    # Medium purple
                'accent': '#DDA0DD',       # Plum
                'background': '#2E0854',   # Dark purple
                'text': '#F8F0FF'
            }
        }
        
        return color_schemes.get(agent_name, {})
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _row_to_form_data(self, row) -> AgentPhysicalForm:
        """Convert database row to AgentPhysicalForm object"""
        columns = ['id', 'agent_name', 'form_type', 'file_path', 'file_format',
                  'dimensions', 'color_scheme', 'characteristics', 
                  'animation_capabilities', 'interaction_points', 'metadata',
                  'creation_timestamp', 'last_updated', 'is_active',
                  'file_size_bytes', 'file_hash']
        
        data = dict(zip(columns, row))
        
        # Parse JSON fields
        for field in ['dimensions', 'color_scheme', 'characteristics',
                     'animation_capabilities', 'interaction_points', 'metadata']:
            if data[field]:
                data[field] = json.loads(data[field])
        
        return AgentPhysicalForm(
            agent_name=data['agent_name'],
            form_type=data['form_type'],
            file_path=data['file_path'],
            file_format=data['file_format'],
            dimensions=data['dimensions'],
            color_scheme=data['color_scheme'],
            characteristics=data['characteristics'],
            animation_capabilities=data['animation_capabilities'],
            interaction_points=data['interaction_points'],
            metadata=data['metadata'],
            creation_timestamp=data['creation_timestamp'],
            last_updated=data['last_updated'],
            is_active=bool(data['is_active'])
        )


class AgentVisualizationEngine:
    """Engine for rendering and displaying agent physical forms"""
    
    def __init__(self, form_manager: PhysicalFormManager):
        self.form_manager = form_manager
        self.rendering_cache = {}
        self.active_visualizations = {}
        
    def render_agent(self, agent_name: str, context: str = "default") -> Dict[str, Any]:
        """Render an agent's current physical form"""
        active_form = self.form_manager.get_active_form(agent_name)
        
        if not active_form:
            return {
                'status': 'no_form',
                'message': f"No physical form available for {agent_name}",
                'placeholder': self._get_placeholder_representation(agent_name)
            }
        
        rendering_data = {
            'agent_name': agent_name,
            'form_id': None,  # Would be extracted from active_form
            'form_type': active_form.form_type,
            'file_path': active_form.file_path,
            'characteristics': active_form.characteristics,
            'color_scheme': active_form.color_scheme,
            'context': context,
            'render_timestamp': time.time()
        }
        
        # Add context-specific rendering parameters
        if context == "interaction":
            rendering_data['interactive_elements'] = active_form.interaction_points
        elif context == "presentation":
            rendering_data['presentation_mode'] = True
            
        return rendering_data
    
    def _get_placeholder_representation(self, agent_name: str) -> Dict[str, Any]:
        """Get placeholder representation when no physical form is available"""
        characteristics = self.form_manager._generate_agent_characteristics(agent_name)
        color_scheme = self.form_manager._generate_agent_colors(agent_name)
        
        return {
            'type': 'placeholder',
            'agent_name': agent_name.title(),
            'characteristics': characteristics,
            'color_scheme': color_scheme,
            'placeholder_icon': f"🔥🌲🧠⛓️"[['prometheus', 'silva', 'turlo', 'lirto'].index(agent_name)],
            'description': f"Physical form for {agent_name.title()} ready for upload"
        }


def create_form_integration_system() -> tuple[PhysicalFormManager, AgentVisualizationEngine]:
    """Create and initialize the complete physical form integration system"""
    
    print("🎭 INITIALIZING PHYSICAL FORM INTEGRATION SYSTEM")
    print("=" * 60)
    
    # Initialize components
    form_manager = PhysicalFormManager()
    visualization_engine = AgentVisualizationEngine(form_manager)
    
    print("✅ Physical Form Manager initialized")
    print("✅ Agent Visualization Engine initialized")
    print("✅ Agent directories created for all 4 agents")
    print("✅ Form database initialized")
    print("✅ Supported formats loaded:")
    
    for form_type, formats in form_manager.supported_formats.items():
        print(f"   📁 {form_type}: {', '.join(formats)}")
    
    print("\n🎨 AGENT VISUAL PROFILES READY:")
    for agent in ['prometheus', 'silva', 'turlo', 'lirto']:
        colors = form_manager._generate_agent_colors(agent)
        characteristics = form_manager._generate_agent_characteristics(agent)
        print(f"   {agent.title()}: {colors['primary']} | {characteristics.get('visual_style', 'default')}")
    
    print(f"\n💾 Form Storage: {form_manager.forms_dir}")
    print("🔄 Ready to accept physical form uploads!")
    
    return form_manager, visualization_engine


async def main():
    """Main function to initialize the physical form system"""
    print("🛡️ GuardianShield Agent Physical Form Integration System")
    print("Preparing system for agent physical form uploads...")
    
    try:
        # Initialize the system
        form_manager, visualization_engine = create_form_integration_system()
        
        # Display current status for all agents
        print(f"\n📊 CURRENT AGENT FORM STATUS:")
        for agent_name in ['prometheus', 'silva', 'turlo', 'lirto']:
            active_form = form_manager.get_active_form(agent_name)
            if active_form:
                print(f"   {agent_name.title()}: ✅ Active form ({active_form.form_type})")
            else:
                placeholder = visualization_engine._get_placeholder_representation(agent_name)
                icon = placeholder['placeholder_icon']
                print(f"   {agent_name.title()}: {icon} Ready for form upload")
        
        print(f"\n" + "="*60)
        print("🎭 PHYSICAL FORM SYSTEM READY!")
        print("📤 Upload agent forms using the upload_physical_form() method")
        print("🎨 System will auto-detect form types and apply agent characteristics")
        print("💾 All forms will be stored with metadata and version control")
        print("🔄 Forms can be updated and switched dynamically")
        
        return {
            'form_manager': form_manager,
            'visualization_engine': visualization_engine,
            'status': 'ready_for_uploads',
            'agent_directories': form_manager.agent_dirs,
            'supported_formats': form_manager.supported_formats
        }
        
    except Exception as e:
        logger.error(f"Physical form system initialization failed: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return None


if __name__ == "__main__":
    result = asyncio.run(main())