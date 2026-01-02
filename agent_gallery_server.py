#!/usr/bin/env python3
"""
Enhanced Agent Visualization Server
Supports both 2D artwork and 3D models
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from pathlib import Path
import base64
import os

app = FastAPI(title="GuardianShield Agent Gallery")

# Mount static files
if not os.path.exists("agent_assets"):
    os.makedirs("agent_assets/avatars", exist_ok=True)
    os.makedirs("agent_assets/3d_models", exist_ok=True)

app.mount("/assets", StaticFiles(directory="agent_assets"), name="assets")

@app.get("/", response_class=HTMLResponse)
async def main_gallery():
    """Main gallery showing all agents"""
    
    # Check for Guardian Sentinel
    guardian_path = Path("agent_assets/avatars/guardian_sentinel")
    has_guardian = guardian_path.exists()
    
    # Check for Sovereign Validator
    sovereign_path = Path("agent_assets/avatars/sovereign_validator") 
    has_sovereign = sovereign_path.exists()
    
    # Check for Network Guardian
    network_path = Path("agent_assets/avatars/network_guardian")
    has_network = network_path.exists()
    
    # Check for Divine Messenger
    divine_path = Path("agent_assets/avatars/divine_messenger")
    has_divine = divine_path.exists()
    
    # Check for Ethereum Storm Lord
    ethereum_path = Path("agent_assets/avatars/ethereum_storm_lord")
    has_ethereum = ethereum_path.exists()
    
    # Check for images
    guardian_image = None
    sovereign_image = None
    network_image = None
    ethereum_image = None
    divine_image = None
    
    if has_guardian:
        for ext in ['.png', '.jpg', '.jpeg']:
            img_path = guardian_path / f"guardian_sentinel_avatar{ext}"
            if img_path.exists():
                with open(img_path, 'rb') as f:
                    guardian_image = base64.b64encode(f.read()).decode()
                break
                
    if has_sovereign:
        for ext in ['.png', '.jpg', '.jpeg']:
            img_path = sovereign_path / f"sovereign_validator_avatar{ext}"
            if img_path.exists():
                with open(img_path, 'rb') as f:
                    sovereign_image = base64.b64encode(f.read()).decode()
                break
                
    if has_network:
        for ext in ['.png', '.jpg', '.jpeg']:
            img_path = network_path / f"network_guardian_avatar{ext}"
            if img_path.exists():
                with open(img_path, 'rb') as f:
                    network_image = base64.b64encode(f.read()).decode()
                break
                
    if has_ethereum:
        for ext in ['.png', '.jpg', '.jpeg']:
            img_path = ethereum_path / f"ethereum_storm_lord_avatar{ext}"
            if img_path.exists():
                with open(img_path, 'rb') as f:
                    ethereum_image = base64.b64encode(f.read()).decode()
                break
                
    if has_divine:
        for ext in ['.png', '.jpg', '.jpeg']:
            img_path = divine_path / f"divine_messenger_avatar{ext}"
            if img_path.exists():
                with open(img_path, 'rb') as f:
                    divine_image = base64.b64encode(f.read()).decode()
                break
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🛡️ GuardianShield Agent Command Center</title>
        <style>
            body {{
                background: linear-gradient(135deg, #0a0a0a 0%, #1a0a0a 50%, #2a1a0a 100%);
                color: #fff;
                font-family: 'Segoe UI', Arial, sans-serif;
                margin: 0;
                padding: 20px;
                min-height: 100vh;
            }}
            
            .header {{
                text-align: center;
                margin-bottom: 40px;
            }}
            
            h1 {{
                color: #ff6b35;
                text-shadow: 0 0 20px rgba(255, 107, 53, 0.8);
                font-size: 3em;
                margin: 0;
            }}
            
            .subtitle {{
                color: #ccc;
                font-size: 1.2em;
                margin-top: 10px;
            }}
            
            .agent-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                gap: 30px;
                max-width: 1400px;
                margin: 0 auto;
            }}
            
            .agent-card {{
                background: linear-gradient(145deg, #2a2a2a, #1e1e1e);
                border-radius: 15px;
                padding: 25px;
                border: 2px solid #444;
                transition: all 0.3s;
                position: relative;
                overflow: hidden;
            }}
            
            .agent-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, #ff6b35, #ff8f65);
                opacity: 0;
                transition: opacity 0.3s;
            }}
            
            .agent-card:hover::before {{
                opacity: 1;
            }}
            
            .agent-card:hover {{
                transform: translateY(-8px);
                border-color: #ff6b35;
                box-shadow: 0 15px 40px rgba(255, 107, 53, 0.3);
            }}
            
            .agent-image {{
                width: 100%;
                height: 300px;
                border-radius: 10px;
                overflow: hidden;
                margin-bottom: 20px;
                position: relative;
            }}
            
            .agent-image img {{
                width: 100%;
                height: 100%;
                object-fit: cover;
                transition: transform 0.3s;
            }}
            
            .agent-card:hover .agent-image img {{
                transform: scale(1.05);
            }}
            
            .agent-name {{
                color: #ff6b35;
                font-size: 1.5em;
                font-weight: bold;
                margin: 0 0 10px 0;
            }}
            
            .agent-type {{
                color: #aaa;
                font-size: 0.9em;
                margin-bottom: 15px;
            }}
            
            .status {{
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 0.8em;
                font-weight: bold;
                margin-bottom: 15px;
            }}
            
            .status.ready {{
                background: rgba(0, 255, 0, 0.2);
                color: #00ff00;
                border: 1px solid rgba(0, 255, 0, 0.4);
            }}
            
            .status.pending {{
                background: rgba(255, 165, 0, 0.2);
                color: #ffa500;
                border: 1px solid rgba(255, 165, 0, 0.4);
            }}
            
            .agent-actions {{
                display: flex;
                gap: 10px;
                margin-top: 20px;
            }}
            
            .btn {{
                background: linear-gradient(135deg, #ff6b35, #ff8f65);
                color: white;
                border: none;
                padding: 10px 18px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 0.9em;
                transition: all 0.3s;
                flex: 1;
            }}
            
            .btn:hover {{
                background: linear-gradient(135deg, #e55a2b, #ff6b35);
                transform: translateY(-2px);
            }}
            
            .btn.secondary {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid #666;
            }}
            
            .btn.secondary:hover {{
                background: rgba(255, 255, 255, 0.2);
            }}
            
            .placeholder {{
                text-align: center;
                background: rgba(255, 107, 53, 0.1);
                border: 2px dashed rgba(255, 107, 53, 0.3);
                padding: 40px 20px;
                border-radius: 10px;
                color: #ff6b35;
            }}
            
            .upload-area {{
                text-align: center;
                margin: 40px 0;
            }}
            
            .upload-btn {{
                background: linear-gradient(135deg, #28a745, #34ce57);
                color: white;
                padding: 15px 30px;
                border-radius: 8px;
                text-decoration: none;
                display: inline-block;
                transition: all 0.3s;
                border: none;
                cursor: pointer;
                font-size: 1.1em;
            }}
            
            .upload-btn:hover {{
                background: linear-gradient(135deg, #218838, #28a745);
                transform: translateY(-2px);
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🛡️ GuardianShield Agent Command Center</h1>
            <p class="subtitle">Elite Security Agent Gallery & Deployment Hub</p>
        </div>
        
        <div class="agent-grid">
            {"" if has_guardian and guardian_image else ""}
            {f'''
            <div class="agent-card">
                <div class="agent-image">
                    <img src="data:image/png;base64,{guardian_image}" alt="Guardian Sentinel">
                </div>
                <h2 class="agent-name">🔥 Guardian Sentinel</h2>
                <p class="agent-type">Elite Security Agent</p>
                <span class="status ready">🟢 READY FOR DEPLOYMENT</span>
                <p style="color: #ccc; font-size: 0.9em;">
                    Dark armored warrior with flame mastery. Primary guardian for high-threat scenarios.
                </p>
                <div class="agent-actions">
                    <button class="btn" onclick="viewProfile('guardian_sentinel')">📋 View Profile</button>
                    <button class="btn" onclick="deployAgent('guardian_sentinel')">🚀 Deploy</button>
                </div>
            </div>
            ''' if has_guardian and guardian_image else f'''
            <div class="agent-card">
                <div class="placeholder">
                    <h3>🔥 Guardian Sentinel</h3>
                    <p>Elite Security Agent</p>
                    <p style="font-size: 0.9em;">Image ready to load!</p>
                    <p style="font-size: 0.8em; margin-top: 10px;">
                        Save your image as:<br>
                        <code>agent_assets/avatars/guardian_sentinel/guardian_sentinel_avatar.png</code>
                    </p>
                </div>
                <div class="agent-actions" style="margin-top: 15px;">
                    <button class="btn secondary">📋 View Profile</button>
                    <button class="btn secondary">⏳ Pending Setup</button>
                </div>
            </div>
            '''}
            
            {f'''
            <div class="agent-card">
                <div class="agent-image">
                    <img src="data:image/png;base64,{sovereign_image}" alt="Sovereign Validator">
                </div>
                <h2 class="agent-name">👑 Sovereign Validator</h2>
                <p class="agent-type">Divine King of Consensus</p>
                <span class="status ready">🟢 SUPREME AUTHORITY</span>
                <p style="color: #ccc; font-size: 0.9em;">
                    Majestic ruler with cosmic flame authority. Ultimate blockchain validation power.
                </p>
                <div class="agent-actions">
                    <button class="btn" onclick="viewProfile('sovereign_validator')">📋 Royal Profile</button>
                    <button class="btn" onclick="deployAgent('sovereign_validator')">👑 Invoke King</button>
                </div>
            </div>
            ''' if has_sovereign and sovereign_image else f'''
            <div class="agent-card">
                <div class="placeholder">
                    <h3>👑 Sovereign Validator</h3>
                    <p>Divine King of Consensus</p>
                    <p style="font-size: 0.9em;">Royal image awaits!</p>
                    <p style="font-size: 0.8em; margin-top: 10px;">
                        Save your divine king image as:<br>
                        <code>agent_assets/avatars/sovereign_validator/sovereign_validator_avatar.png</code>
                    </p>
                </div>
                <div class="agent-actions" style="margin-top: 15px;">
                    <button class="btn secondary">📋 Royal Profile</button>
                    <button class="btn secondary">⏳ Awaiting Coronation</button>
                </div>
            </div>
            '''}
            
            {f'''
            <div class="agent-card">
                <div class="agent-image">
                    <img src="data:image/png;base64,{network_image}" alt="Network Guardian">
                </div>
                <h2 class="agent-name">🌲 Network Guardian</h2>
                <p class="agent-type">Ancient Ecosystem Protector</p>
                <span class="status ready">🟢 FOREST NETWORKS ACTIVE</span>
                <p style="color: #ccc; font-size: 0.9em;">
                    Mystical forest spirit with hexagonal runes. Protects digital ecosystems and network harmony.
                </p>
                <div class="agent-actions">
                    <button class="btn" onclick="viewProfile('network_guardian')">🌿 Forest Profile</button>
                    <button class="btn" onclick="deployAgent('network_guardian')">🦌 Awaken Spirit</button>
                </div>
            </div>
            ''' if has_network and network_image else f'''
            <div class="agent-card">
                <div class="placeholder">
                    <h3>🌲 Network Guardian</h3>
                    <p>Ancient Ecosystem Protector</p>
                    <p style="font-size: 0.9em;">Forest spirit awaits!</p>
                    <p style="font-size: 0.8em; margin-top: 10px;">
                        Save your antlered guardian image as:<br>
                        <code>agent_assets/avatars/network_guardian/network_guardian_avatar.png</code>
                    </p>
                </div>
                <div class="agent-actions" style="margin-top: 15px;">
                    <button class="btn secondary">🌿 Forest Profile</button>
                    <button class="btn secondary">⏳ Awaiting Awakening</button>
                </div>
            </div>
            '''}
            
            {f'''
            <div class="agent-card">
                <div class="agent-image">
                    <img src="data:image/png;base64,{ethereum_image}" alt="Ethereum Storm Lord">
                </div>
                <h2 class="agent-name">⚡ Ethereum Storm Lord</h2>
                <p class="agent-type">Master of Smart Contracts</p>
                <span class="status ready">🟢 LIGHTNING NETWORK ACTIVE</span>
                <p style="color: #ccc; font-size: 0.9em;">
                    Storm deity with Ethereum diamond heart. Lightning-fast smart contract execution and blockchain mastery.
                </p>
                <div class="agent-actions">
                    <button class="btn" onclick="viewProfile('ethereum_storm_lord')">💎 Storm Profile</button>
                    <button class="btn" onclick="deployAgent('ethereum_storm_lord')">⚡ Summon Storm</button>
                </div>
            </div>
            ''' if has_ethereum and ethereum_image else f'''
            <div class="agent-card">
                <div class="placeholder">
                    <h3>⚡ Ethereum Storm Lord</h3>
                    <p>Master of Smart Contracts</p>
                    <p style="font-size: 0.9em;">Storm lord awaits!</p>
                    <p style="font-size: 0.8em; margin-top: 10px;">
                        Save your storm lord image as:<br>
                        <code>agent_assets/avatars/ethereum_storm_lord/ethereum_storm_lord_avatar.png</code>
                    </p>
                </div>
                <div class="agent-actions" style="margin-top: 15px;">
                    <button class="btn secondary">💎 Storm Profile</button>
                    <button class="btn secondary">⏳ Awaiting Thunder</button>
                </div>
            </div>
            '''}
            
            <div class="agent-card">
                <div class="placeholder">
                    <h3>📊 Learning Agent</h3>
                    <p>AI Training Specialist</p>
                    <span class="status pending">⏳ AWAITING AVATAR</span>
                </div>
                <div class="agent-actions">
                    <button class="btn secondary">📋 View Profile</button>
                    <button class="btn secondary">📤 Upload Avatar</button>
                </div>
            </div>
            
            <div class="agent-card">
                <div class="placeholder">
                    <h3>🛡️ Security Agent</h3>
                    <p>Threat Detection System</p>
                    <span class="status pending">⏳ AWAITING AVATAR</span>
                </div>
                <div class="agent-actions">
                    <button class="btn secondary">📋 View Profile</button>
                    <button class="btn secondary">📤 Upload Avatar</button>
                </div>
            </div>
            
            <div class="agent-card">
                <div class="placeholder">
                    <h3>🔗 DMER Agent</h3>
                    <p>Blockchain Monitor</p>
                    <span class="status pending">⏳ AWAITING AVATAR</span>
                </div>
                <div class="agent-actions">
                    <button class="btn secondary">📋 View Profile</button>
                    <button class="btn secondary">📤 Upload Avatar</button>
                </div>
            </div>
            </div>
            '''}
            
            {f'''
            <div class="agent-card">
                <div class="agent-image">
                    <img src="data:image/png;base64,{divine_image}" alt="Divine Messenger">
                </div>
                <h2 class="agent-name">🕊️ Divine Messenger</h2>
                <p class="agent-type">Archangel of Wisdom</p>
                <span class="status ready">🟢 CELESTIAL CHANNELS OPEN</span>
                <p style="color: #ccc; font-size: 0.9em;">
                    Majestic winged archangel with sacred torch. Herald of divine wisdom and ultimate truth.
                </p>
                <div class="agent-actions">
                    <button class="btn" onclick="viewProfile('divine_messenger')">👼 Divine Profile</button>
                    <button class="btn" onclick="deployAgent('divine_messenger')">🔥 Ignite Torch</button>
                </div>
            </div>
            ''' if has_divine and divine_image else f'''
            <div class="agent-card">
                <div class="placeholder">
                    <h3>🕊️ Divine Messenger</h3>
                    <p>Archangel of Wisdom</p>
                    <p style="font-size: 0.9em;">Sacred wings await!</p>
                    <p style="font-size: 0.8em; margin-top: 10px;">
                        Save your archangel image as:<br>
                        <code>agent_assets/avatars/divine_messenger/divine_messenger_avatar.png</code>
                    </p>
                </div>
                <div class="agent-actions" style="margin-top: 15px;">
                    <button class="btn secondary">👼 Divine Profile</button>
                    <button class="btn secondary">⏳ Awaiting Ascension</button>
                </div>
            </div>
            """
        </div>
        
        <div class="upload-area">
            <button class="upload-btn" onclick="window.open('/upload', '_blank')">
                Upload More Agent Avatars
            </button>
        </div>
        
        <script>
            function viewProfile(agentName) {{
                window.open(`/agent/profile/${{agentName}}`, '_blank');
            }}
            
            function deployAgent(agentName) {{
                if (confirm(`Deploy ${{agentName.replace('_', ' ')}} for active security duty?`)) {{
                    // Simulate deployment
                    alert(`${{agentName.replace('_', ' ')}} has been deployed!\\n\\nSecurity protocols activated\\nThreat monitoring online\\nAll systems operational`);
                }}
            }}
        </script>
    </body>
    </html>
    """

@app.get("/agent/profile/{agent_name}", response_class=HTMLResponse)  
async def agent_profile(agent_name: str):
    """View agent profile"""
    if agent_name == "guardian_sentinel":
        profile_path = Path("agent_assets/avatars/guardian_sentinel/profile.html")
        if profile_path.exists():
            return profile_path.read_text(encoding='utf-8')
    elif agent_name == "sovereign_validator":
        profile_path = Path("agent_assets/avatars/sovereign_validator/profile.html")
        if profile_path.exists():
            return profile_path.read_text(encoding='utf-8')
    elif agent_name == "network_guardian":
        profile_path = Path("agent_assets/avatars/network_guardian/profile.html")
        if profile_path.exists():
            return profile_path.read_text(encoding='utf-8')
    elif agent_name == "ethereum_storm_lord":
        profile_path = Path("agent_assets/avatars/ethereum_storm_lord/profile.html") 
        if profile_path.exists():
            return profile_path.read_text(encoding='utf-8')
    elif agent_name == "divine_messenger":
        profile_path = Path("agent_assets/avatars/divine_messenger/profile.html")
        if profile_path.exists():
            return profile_path.read_text(encoding='utf-8')
async def upload_page():
    return """
    <html><body style="font-family: Arial; padding: 40px; background: #1a1a1a; color: #fff;">
    <h1 style="color: #ff6b35;">📤 Upload Agent Avatars</h1>
    <div style="background: rgba(255,107,53,0.1); padding: 30px; border-radius: 10px; border: 1px solid rgba(255,107,53,0.3);">
        <h2>🎯 Quick Setup Instructions:</h2>
        <ol style="line-height: 1.6;">
            <li>Save your Guardian image as: <code>agent_assets/avatars/guardian_sentinel/guardian_sentinel_avatar.png</code></li>
            <li>Refresh the main gallery to see it appear</li>
            <li>Click "View Profile" to see the full agent page</li>
        </ol>
        <p style="margin-top: 20px;"><strong>Supported formats:</strong> PNG, JPG, JPEG</p>
        <a href="/" style="background: #ff6b35; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">← Back to Gallery</a>
    </div>
    </body></html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8889)