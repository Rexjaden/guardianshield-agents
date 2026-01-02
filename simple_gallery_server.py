#!/usr/bin/env python3
"""
GuardianShield Agent Gallery - Simple Version
Complete collection of 5 specialized agents
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pathlib import Path
import uvicorn

app = FastAPI(title="GuardianShield Agent Gallery")

@app.get("/", response_class=HTMLResponse)
async def agent_gallery():
    """Main gallery page showing all 5 agents"""
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>GuardianShield Agent Gallery</title>
        <style>
            body { 
                margin: 0; 
                padding: 20px; 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                min-height: 100vh;
            }
            .header {
                text-align: center;
                margin-bottom: 40px;
            }
            h1 {
                font-size: 3em;
                margin: 0;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                background: linear-gradient(45deg, #ffd700, #ffed4e);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            .subtitle {
                font-size: 1.2em;
                opacity: 0.9;
                margin-top: 10px;
            }
            .agent-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 30px;
                max-width: 1400px;
                margin: 0 auto;
            }
            .agent-card {
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 25px;
                text-align: center;
                transition: transform 0.3s, box-shadow 0.3s;
                border: 1px solid rgba(255,255,255,0.2);
            }
            .agent-card:hover {
                transform: translateY(-10px);
                box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            }
            .agent-image {
                width: 200px;
                height: 200px;
                border-radius: 15px;
                margin: 0 auto 20px;
                background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 4em;
                border: 3px solid rgba(255,255,255,0.3);
            }
            .agent-name {
                font-size: 1.5em;
                font-weight: bold;
                margin-bottom: 10px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            .agent-role {
                font-size: 1em;
                opacity: 0.8;
                margin-bottom: 15px;
                font-style: italic;
            }
            .agent-powers {
                font-size: 0.9em;
                margin-bottom: 20px;
                opacity: 0.7;
            }
            .action-buttons {
                display: flex;
                gap: 10px;
                justify-content: center;
                flex-wrap: wrap;
            }
            .btn {
                padding: 8px 16px;
                border: none;
                border-radius: 20px;
                cursor: pointer;
                font-weight: bold;
                transition: all 0.3s;
                text-decoration: none;
                display: inline-block;
            }
            .btn-primary {
                background: linear-gradient(45deg, #ff6b6b, #ee5a24);
                color: white;
            }
            .btn-secondary {
                background: linear-gradient(45deg, #4834d4, #686de0);
                color: white;
            }
            .btn:hover {
                transform: scale(1.05);
                box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            }
            .guardian-theme { background: linear-gradient(45deg, #ff9a56, #ff6b35); }
            .sovereign-theme { background: linear-gradient(45deg, #ffd700, #ffa726); }
            .network-theme { background: linear-gradient(45deg, #4caf50, #45a049); }
            .storm-theme { background: linear-gradient(45deg, #2196f3, #1976d2); }
            .divine-theme { background: linear-gradient(45deg, #9c27b0, #673ab7); }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>GuardianShield Ecosystem</h1>
            <p class="subtitle">Elite Autonomous Security Agents & Native Token</p>
        </div>
        
        <!-- Token Showcase Section -->
        <div style="max-width: 1200px; margin: 0 auto 40px; padding: 0 20px;">
            <div style="background: rgba(255,215,0,0.1); backdrop-filter: blur(10px); border-radius: 20px; padding: 30px; text-align: center; border: 2px solid rgba(255,215,0,0.3);">
                <div style="display: flex; align-items: center; justify-content: center; gap: 20px; flex-wrap: wrap;">
                    <div style="width: 80px; height: 80px; background: linear-gradient(45deg, #ffd700, #ffed4e); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 2em; font-weight: bold; color: #1a1a3a;">GST</div>
                    <div style="text-align: left;">
                        <h2 style="margin: 0; color: #ffd700; font-size: 1.8em;">GuardianShield Token (GST)</h2>
                        <p style="margin: 5px 0; opacity: 0.9;">Native utility token powering the entire ecosystem</p>
                        <div style="margin-top: 15px;">
                            <button class="btn btn-primary" onclick="viewTokenProfile()" style="margin-right: 10px;">📊 Token Details</button>
                            <button class="btn btn-secondary" onclick="alert('Token purchase available at launch!');">💰 Buy GST</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="agent-grid">
            <!-- Guardian Sentinel -->
            <div class="agent-card">
                <div class="agent-image guardian-theme">🛡️</div>
                <div class="agent-name">Guardian Sentinel</div>
                <div class="agent-role">Elite Security Protector</div>
                <div class="agent-powers">Advanced Threat Detection • Autonomous Defense • Real-time Monitoring</div>
                <div class="action-buttons">
                    <button class="btn btn-primary" onclick="viewProfile('guardian_sentinel')">View Profile</button>
                    <button class="btn btn-secondary" onclick="deployAgent('Guardian Sentinel')">Deploy</button>
                </div>
            </div>
            
            <!-- Sovereign Validator -->
            <div class="agent-card">
                <div class="agent-image sovereign-theme">👑</div>
                <div class="agent-name">Sovereign Validator</div>
                <div class="agent-role">Consensus Authority</div>
                <div class="agent-powers">Transaction Validation • Consensus Management • Governance Protocols</div>
                <div class="action-buttons">
                    <button class="btn btn-primary" onclick="viewProfile('sovereign_validator')">View Profile</button>
                    <button class="btn btn-secondary" onclick="deployAgent('Sovereign Validator')">Deploy</button>
                </div>
            </div>
            
            <!-- Network Guardian -->
            <div class="agent-card">
                <div class="agent-image network-theme">🌲</div>
                <div class="agent-name">Network Guardian</div>
                <div class="agent-role">Network Infrastructure Guardian</div>
                <div class="agent-powers">Network Monitoring • Traffic Analysis • Infrastructure Protection</div>
                <div class="action-buttons">
                    <button class="btn btn-primary" onclick="viewProfile('network_guardian')">View Profile</button>
                    <button class="btn btn-secondary" onclick="deployAgent('Network Guardian')">Deploy</button>
                </div>
            </div>
            
            <!-- Ethereum Storm Lord -->
            <div class="agent-card">
                <div class="agent-image storm-theme">⚡</div>
                <div class="agent-name">Ethereum Storm Lord</div>
                <div class="agent-role">Blockchain Operations Master</div>
                <div class="agent-powers">Lightning Execution • Smart Contract Mastery • DeFi Operations</div>
                <div class="action-buttons">
                    <button class="btn btn-primary" onclick="viewProfile('ethereum_storm_lord')">View Profile</button>
                    <button class="btn btn-secondary" onclick="deployAgent('Ethereum Storm Lord')">Deploy</button>
                </div>
            </div>
            
            <!-- Divine Messenger -->
            <div class="agent-card">
                <div class="agent-image divine-theme">👼</div>
                <div class="agent-name">Divine Messenger</div>
                <div class="agent-role">Celestial Communication Agent</div>
                <div class="agent-powers">Sacred Communications • Divine Wisdom • Enlightened Guidance</div>
                <div class="action-buttons">
                    <button class="btn btn-primary" onclick="viewProfile('divine_messenger')">View Profile</button>
                    <button class="btn btn-secondary" onclick="deployAgent('Divine Messenger')">Deploy</button>
                </div>
            </div>
        </div>
        
        <script>
            function viewProfile(agentName) {
                window.open('/agent/profile/' + agentName, '_blank');
            }
            
            function deployAgent(agentName) {
                if (confirm('Deploy ' + agentName + ' for active security duty?')) {
                    alert(agentName + ' has been deployed!\\n\\nSecurity protocols activated\\nThreat monitoring online\\nAll systems operational');
                }
            }
            
            function viewTokenProfile() {
                window.open('/token/profile', '_blank');
            }
        </script>
    </body>
    </html>
    """
    
    return html_content

@app.get("/agent/profile/{agent_name}", response_class=HTMLResponse)  
async def agent_profile(agent_name: str):
    """View agent profile"""
    
    profiles = {
        "guardian_sentinel": "agent_assets/avatars/guardian_sentinel/profile.html",
        "sovereign_validator": "agent_assets/avatars/sovereign_validator/profile.html", 
        "network_guardian": "agent_assets/avatars/network_guardian/profile.html",
        "ethereum_storm_lord": "agent_assets/avatars/ethereum_storm_lord/profile.html",
        "divine_messenger": "agent_assets/avatars/divine_messenger/profile.html"
    }
    
    if agent_name in profiles:
        profile_path = Path(profiles[agent_name])
        if profile_path.exists():
            return profile_path.read_text(encoding='utf-8')
    
    return f"<h1>Agent Profile: {agent_name}</h1><p>Profile not found. Please check that the agent profile exists.</p>"

@app.get("/token/profile", response_class=HTMLResponse)
async def token_profile():
    """View GuardianShield Token profile"""
    profile_path = Path("token_assets/guardianshield_token/token_profile.html")
    if profile_path.exists():
        return profile_path.read_text(encoding='utf-8')
    return "<h1>GuardianShield Token Profile</h1><p>Token profile not found.</p>"

if __name__ == "__main__":
    print("🌟 Starting GuardianShield Agent Gallery...")
    print("🔗 Gallery URL: http://localhost:8889")
    print("👥 Agents Available: 5 Elite Autonomous Agents")
    print("⚡ Ready for deployment!")
    uvicorn.run(app, host="0.0.0.0", port=8889)