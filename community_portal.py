"""
GuardianShield Community Portal
Foundation for user registration, wallet integration, and community features
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Dict, List, Any, Optional
import sqlite3
import hashlib
import jwt
import secrets
from datetime import datetime, timedelta
from pathlib import Path
import logging
import asyncio
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GuardianShield Community Portal",
    description="Secure community platform with wallet integration and DeFi features",
    version="1.0.0"
)

# Security
security = HTTPBearer()
JWT_SECRET = secrets.token_urlsafe(32)
JWT_ALGORITHM = "HS256"

# Database setup
def init_community_database():
    """Initialize community database with all necessary tables"""
    db_path = Path("community_portal.db")
    conn = sqlite3.connect(str(db_path))
    
    # User profiles table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            wallet_address TEXT UNIQUE NOT NULL,
            email TEXT,
            username TEXT UNIQUE,
            display_name TEXT,
            profile_image_url TEXT,
            bio TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_verified BOOLEAN DEFAULT FALSE,
            reputation_score INTEGER DEFAULT 0,
            security_level TEXT DEFAULT 'basic',
            preferences TEXT DEFAULT '{}',
            status TEXT DEFAULT 'active'
        )
    ''')
    
    # Wallet connections table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS wallet_connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            wallet_address TEXT NOT NULL,
            wallet_type TEXT NOT NULL,
            chain_id INTEGER NOT NULL,
            connection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_primary BOOLEAN DEFAULT FALSE,
            verification_status TEXT DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
        )
    ''')
    
    # Authentication sessions table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS auth_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            wallet_address TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            user_agent TEXT,
            ip_address TEXT,
            FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
        )
    ''')
    
    # Community activities table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS community_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            activity_type TEXT NOT NULL,
            activity_data TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reputation_impact INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
        )
    ''')
    
    conn.commit()
    return conn

# Pydantic models
class WalletConnectionRequest(BaseModel):
    wallet_address: str
    wallet_type: str  # 'metamask', 'walletconnect', 'coinbase', etc.
    chain_id: int
    signature: str
    message: str

class UserRegistration(BaseModel):
    wallet_address: str
    email: Optional[str] = None
    username: Optional[str] = None
    display_name: Optional[str] = None

class UserProfile(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    email: Optional[str] = None

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    wallet_address: str
    expires_in: int

# Database connection
db_conn = init_community_database()

# Utility functions
def generate_user_id() -> str:
    """Generate unique user ID"""
    return f"user_{secrets.token_urlsafe(16)}"

def create_jwt_token(user_id: str, wallet_address: str) -> str:
    """Create JWT token for user authentication"""
    payload = {
        "user_id": user_id,
        "wallet_address": wallet_address,
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def verify_wallet_signature(wallet_address: str, message: str, signature: str) -> bool:
    """Verify wallet signature (simplified implementation)"""
    # In production, this would use actual cryptographic verification
    # For now, we'll simulate verification
    expected_hash = hashlib.sha256(f"{wallet_address}{message}".encode()).hexdigest()
    return len(signature) > 100  # Simplified check

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    token = credentials.credentials
    payload = verify_jwt_token(token)
    
    cursor = db_conn.cursor()
    cursor.execute(
        "SELECT * FROM user_profiles WHERE user_id = ?",
        (payload["user_id"],)
    )
    user = cursor.fetchone()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user_id": user[1],
        "wallet_address": user[2],
        "email": user[3],
        "username": user[4],
        "display_name": user[5],
        "reputation_score": user[10],
        "security_level": user[11]
    }

# API Endpoints

@app.get("/")
async def community_portal_home():
    """Serve the community portal homepage"""
    return HTMLResponse(content=get_community_portal_html(), status_code=200)

@app.post("/api/auth/connect-wallet")
async def connect_wallet(request: WalletConnectionRequest):
    """Connect wallet and authenticate user"""
    
    # Verify wallet signature
    if not verify_wallet_signature(request.wallet_address, request.message, request.signature):
        raise HTTPException(status_code=400, detail="Invalid wallet signature")
    
    cursor = db_conn.cursor()
    
    # Check if user exists
    cursor.execute(
        "SELECT user_id FROM user_profiles WHERE wallet_address = ?",
        (request.wallet_address,)
    )
    existing_user = cursor.fetchone()
    
    if existing_user:
        user_id = existing_user[0]
        
        # Update last login
        cursor.execute(
            "UPDATE user_profiles SET last_login = ? WHERE user_id = ?",
            (datetime.now(), user_id)
        )
    else:
        # Create new user
        user_id = generate_user_id()
        cursor.execute(
            '''INSERT INTO user_profiles 
               (user_id, wallet_address, created_at, last_login)
               VALUES (?, ?, ?, ?)''',
            (user_id, request.wallet_address, datetime.now(), datetime.now())
        )
    
    # Record wallet connection
    cursor.execute(
        '''INSERT INTO wallet_connections 
           (user_id, wallet_address, wallet_type, chain_id, verification_status)
           VALUES (?, ?, ?, ?, 'verified')''',
        (user_id, request.wallet_address, request.wallet_type, request.chain_id)
    )
    
    # Create authentication session
    access_token = create_jwt_token(user_id, request.wallet_address)
    session_token = secrets.token_urlsafe(32)
    
    cursor.execute(
        '''INSERT INTO auth_sessions 
           (user_id, session_token, wallet_address, expires_at)
           VALUES (?, ?, ?, ?)''',
        (user_id, session_token, request.wallet_address, 
         datetime.now() + timedelta(hours=24))
    )
    
    db_conn.commit()
    
    # Log community activity
    await log_community_activity(user_id, "wallet_connected", {
        "wallet_type": request.wallet_type,
        "chain_id": request.chain_id
    })
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user_id,
        wallet_address=request.wallet_address,
        expires_in=86400  # 24 hours
    )

@app.post("/api/auth/register")
async def register_user(registration: UserRegistration, current_user = Depends(get_current_user)):
    """Complete user registration with additional profile information"""
    
    cursor = db_conn.cursor()
    
    # Update user profile
    cursor.execute(
        '''UPDATE user_profiles 
           SET email = ?, username = ?, display_name = ?
           WHERE user_id = ?''',
        (registration.email, registration.username, 
         registration.display_name, current_user["user_id"])
    )
    
    db_conn.commit()
    
    # Log activity
    await log_community_activity(current_user["user_id"], "profile_completed", {
        "username": registration.username,
        "has_email": bool(registration.email)
    })
    
    return {"message": "Registration completed successfully"}

@app.get("/api/user/profile")
async def get_user_profile(current_user = Depends(get_current_user)):
    """Get current user's profile"""
    
    cursor = db_conn.cursor()
    
    # Get full profile
    cursor.execute(
        "SELECT * FROM user_profiles WHERE user_id = ?",
        (current_user["user_id"],)
    )
    profile = cursor.fetchone()
    
    # Get wallet connections
    cursor.execute(
        "SELECT * FROM wallet_connections WHERE user_id = ?",
        (current_user["user_id"],)
    )
    wallets = cursor.fetchall()
    
    # Get recent activities
    cursor.execute(
        '''SELECT activity_type, activity_data, timestamp, reputation_impact 
           FROM community_activities 
           WHERE user_id = ? 
           ORDER BY timestamp DESC LIMIT 10''',
        (current_user["user_id"],)
    )
    activities = cursor.fetchall()
    
    return {
        "user_id": profile[1],
        "wallet_address": profile[2],
        "email": profile[3],
        "username": profile[4],
        "display_name": profile[5],
        "bio": profile[7],
        "created_at": profile[8],
        "last_login": profile[9],
        "is_verified": bool(profile[10]),
        "reputation_score": profile[11],
        "security_level": profile[12],
        "connected_wallets": len(wallets),
        "recent_activities": len(activities)
    }

@app.put("/api/user/profile")
async def update_user_profile(profile_update: UserProfile, current_user = Depends(get_current_user)):
    """Update user profile"""
    
    cursor = db_conn.cursor()
    
    cursor.execute(
        '''UPDATE user_profiles 
           SET display_name = ?, bio = ?, email = ?
           WHERE user_id = ?''',
        (profile_update.display_name, profile_update.bio, 
         profile_update.email, current_user["user_id"])
    )
    
    db_conn.commit()
    
    await log_community_activity(current_user["user_id"], "profile_updated", {
        "updated_fields": ["display_name", "bio", "email"]
    })
    
    return {"message": "Profile updated successfully"}

@app.get("/api/community/stats")
async def get_community_stats():
    """Get community statistics"""
    
    cursor = db_conn.cursor()
    
    # Total users
    cursor.execute("SELECT COUNT(*) FROM user_profiles")
    total_users = cursor.fetchone()[0]
    
    # Active users (logged in last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    cursor.execute(
        "SELECT COUNT(*) FROM user_profiles WHERE last_login > ?",
        (week_ago,)
    )
    active_users = cursor.fetchone()[0]
    
    # Verified users
    cursor.execute("SELECT COUNT(*) FROM user_profiles WHERE is_verified = 1")
    verified_users = cursor.fetchone()[0]
    
    # Total wallet connections
    cursor.execute("SELECT COUNT(*) FROM wallet_connections")
    total_wallets = cursor.fetchone()[0]
    
    # Recent activities
    cursor.execute(
        "SELECT COUNT(*) FROM community_activities WHERE timestamp > ?",
        (week_ago,)
    )
    recent_activities = cursor.fetchone()[0]
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "verified_users": verified_users,
        "total_wallet_connections": total_wallets,
        "recent_activities": recent_activities,
        "community_health": min(100, (active_users / max(total_users, 1)) * 100)
    }

@app.get("/api/community/leaderboard")
async def get_community_leaderboard(limit: int = 20):
    """Get community reputation leaderboard"""
    
    cursor = db_conn.cursor()
    cursor.execute(
        '''SELECT user_id, username, display_name, reputation_score, security_level
           FROM user_profiles 
           WHERE status = 'active'
           ORDER BY reputation_score DESC 
           LIMIT ?''',
        (limit,)
    )
    
    leaderboard = []
    for i, row in enumerate(cursor.fetchall(), 1):
        leaderboard.append({
            "rank": i,
            "user_id": row[0],
            "username": row[1] or "Anonymous",
            "display_name": row[2] or "Guardian Member",
            "reputation_score": row[3],
            "security_level": row[4]
        })
    
    return {"leaderboard": leaderboard}

async def log_community_activity(user_id: str, activity_type: str, activity_data: Dict[str, Any], reputation_impact: int = 0):
    """Log community activity for user"""
    
    cursor = db_conn.cursor()
    cursor.execute(
        '''INSERT INTO community_activities 
           (user_id, activity_type, activity_data, reputation_impact)
           VALUES (?, ?, ?, ?)''',
        (user_id, activity_type, json.dumps(activity_data), reputation_impact)
    )
    
    # Update user reputation
    if reputation_impact != 0:
        cursor.execute(
            '''UPDATE user_profiles 
               SET reputation_score = reputation_score + ?
               WHERE user_id = ?''',
            (reputation_impact, user_id)
        )
    
    db_conn.commit()

def get_community_portal_html():
    """Generate community portal HTML"""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GuardianShield Community Portal</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0a0e1a 0%, #1a2332 50%, #2d3e50 100%);
            color: #e0e6ed;
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        .header {
            background: rgba(16, 24, 32, 0.95);
            padding: 1.5rem 2rem;
            border-bottom: 3px solid #3498db;
            backdrop-filter: blur(15px);
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        
        .header-content {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .logo h1 {
            background: linear-gradient(45deg, #3498db, #9b59b6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2rem;
            font-weight: 700;
        }
        
        .shield-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(45deg, #3498db, #9b59b6);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
        }
        
        .nav-buttons {
            display: flex;
            gap: 1rem;
        }
        
        .btn {
            padding: 0.8rem 1.5rem;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .btn-primary {
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(52, 152, 219, 0.4);
        }
        
        .btn-secondary {
            background: rgba(255, 255, 255, 0.1);
            color: #e0e6ed;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        
        .hero {
            padding: 4rem 2rem;
            text-align: center;
            background: radial-gradient(circle at center, rgba(52, 152, 219, 0.1) 0%, transparent 70%);
        }
        
        .hero-content {
            max-width: 800px;
            margin: 0 auto;
        }
        
        .hero h2 {
            font-size: 3.5rem;
            margin-bottom: 1.5rem;
            background: linear-gradient(45deg, #3498db, #9b59b6, #e74c3c);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1.2;
        }
        
        .hero p {
            font-size: 1.3rem;
            color: #bdc3c7;
            margin-bottom: 2.5rem;
            line-height: 1.6;
        }
        
        .cta-buttons {
            display: flex;
            gap: 1.5rem;
            justify-content: center;
            flex-wrap: wrap;
        }
        
        .features {
            padding: 4rem 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-top: 3rem;
        }
        
        .feature-card {
            background: rgba(26, 35, 50, 0.8);
            border-radius: 16px;
            padding: 2rem;
            border: 1px solid rgba(52, 152, 219, 0.3);
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }
        
        .feature-card:hover {
            transform: translateY(-8px);
            border-color: #3498db;
            box-shadow: 0 20px 40px rgba(52, 152, 219, 0.2);
        }
        
        .feature-icon {
            width: 60px;
            height: 60px;
            background: linear-gradient(45deg, #3498db, #9b59b6);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8rem;
            margin-bottom: 1.5rem;
        }
        
        .feature-card h3 {
            color: #3498db;
            margin-bottom: 1rem;
            font-size: 1.4rem;
        }
        
        .feature-card p {
            color: #bdc3c7;
            line-height: 1.6;
        }
        
        .stats {
            background: rgba(16, 24, 32, 0.9);
            padding: 3rem 2rem;
            margin: 4rem 0;
        }
        
        .stats-content {
            max-width: 1200px;
            margin: 0 auto;
            text-align: center;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }
        
        .stat-item {
            padding: 1.5rem;
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: 700;
            color: #3498db;
            margin-bottom: 0.5rem;
        }
        
        .stat-label {
            color: #bdc3c7;
            font-size: 1.1rem;
        }
        
        .wallet-section {
            background: rgba(26, 35, 50, 0.8);
            margin: 2rem;
            border-radius: 16px;
            padding: 2rem;
            border: 1px solid rgba(52, 152, 219, 0.3);
            text-align: center;
            display: none;
        }
        
        .wallet-options {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 2rem;
        }
        
        .wallet-option {
            background: rgba(44, 62, 80, 0.6);
            border: 2px solid transparent;
            border-radius: 12px;
            padding: 1.5rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .wallet-option:hover {
            border-color: #3498db;
            transform: translateY(-2px);
        }
        
        .wallet-icon {
            width: 48px;
            height: 48px;
            margin: 0 auto 1rem;
            background: linear-gradient(45deg, #3498db, #9b59b6);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
        }
        
        @media (max-width: 768px) {
            .hero h2 { font-size: 2.5rem; }
            .cta-buttons { flex-direction: column; align-items: center; }
            .header-content { flex-direction: column; gap: 1rem; }
            .nav-buttons { flex-wrap: wrap; justify-content: center; }
        }
        
        .pulse {
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(52, 152, 219, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(52, 152, 219, 0); }
            100% { box-shadow: 0 0 0 0 rgba(52, 152, 219, 0); }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <div class="logo">
                <div class="shield-icon">🛡️</div>
                <h1>GuardianShield</h1>
            </div>
            <div class="nav-buttons">
                <a href="#features" class="btn btn-secondary">Features</a>
                <a href="#stats" class="btn btn-secondary">Stats</a>
                <button onclick="showWalletConnect()" class="btn btn-primary pulse">Connect Wallet</button>
            </div>
        </div>
    </div>
    
    <div class="hero">
        <div class="hero-content">
            <h2>Welcome to the Guardian Community</h2>
            <p>Join the most advanced decentralized security ecosystem. Protect your assets, earn rewards, and shape the future of Web3 security together.</p>
            <div class="cta-buttons">
                <button onclick="showWalletConnect()" class="btn btn-primary">🚀 Join the Community</button>
                <button onclick="showFeatures()" class="btn btn-secondary">📚 Learn More</button>
            </div>
        </div>
    </div>
    
    <div class="wallet-section" id="walletSection">
        <h3>Connect Your Wallet</h3>
        <p>Choose your preferred wallet to join the GuardianShield community</p>
        <div class="wallet-options">
            <div class="wallet-option" onclick="connectWallet('metamask')">
                <div class="wallet-icon">🦊</div>
                <h4>MetaMask</h4>
                <p>Most popular Web3 wallet</p>
            </div>
            <div class="wallet-option" onclick="connectWallet('walletconnect')">
                <div class="wallet-icon">🔗</div>
                <h4>WalletConnect</h4>
                <p>Connect any mobile wallet</p>
            </div>
            <div class="wallet-option" onclick="connectWallet('coinbase')">
                <div class="wallet-icon">🔵</div>
                <h4>Coinbase Wallet</h4>
                <p>Easy and secure</p>
            </div>
        </div>
    </div>
    
    <div class="features" id="features">
        <div style="text-align: center; margin-bottom: 3rem;">
            <h2 style="font-size: 2.5rem; color: #3498db;">Why Join GuardianShield?</h2>
            <p style="font-size: 1.2rem; color: #bdc3c7;">Revolutionary security meets community governance</p>
        </div>
        
        <div class="features-grid">
            <div class="feature-card">
                <div class="feature-icon">🤖</div>
                <h3>AI-Powered Security</h3>
                <p>Advanced artificial intelligence monitors threats across multiple blockchains with 94.2% accuracy, protecting your assets 24/7.</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">💰</div>
                <h3>Earn While Protected</h3>
                <p>Stake your tokens in our secure treasury and earn competitive returns while contributing to ecosystem security.</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">🎨</div>
                <h3>NFT Builder</h3>
                <p>Create unique NFTs with AI assistance and deploy them securely across multiple blockchains with built-in protection.</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">🌐</div>
                <h3>Multi-Chain Coverage</h3>
                <p>Comprehensive security across Ethereum, BSC, Polygon, Avalanche, and Arbitrum with cross-chain threat detection.</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">🏆</div>
                <h3>Community Governance</h3>
                <p>Participate in ecosystem decisions, earn reputation rewards, and help shape the future of decentralized security.</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon">🔒</div>
                <h3>Zero-Trust Security</h3>
                <p>Military-grade encryption, quantum-resistant protocols, and continuous security audits ensure maximum protection.</p>
            </div>
        </div>
    </div>
    
    <div class="stats" id="stats">
        <div class="stats-content">
            <h2 style="font-size: 2.5rem; color: #3498db; margin-bottom: 1rem;">Community Impact</h2>
            <p style="color: #bdc3c7; font-size: 1.2rem;">Real numbers from our growing ecosystem</p>
            
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-number">$2.3B</div>
                    <div class="stat-label">Assets Protected</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">847</div>
                    <div class="stat-label">Threats Blocked (24h)</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">99.94%</div>
                    <div class="stat-label">System Uptime</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">94.2%</div>
                    <div class="stat-label">Detection Accuracy</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">5</div>
                    <div class="stat-label">Blockchain Networks</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">127ms</div>
                    <div class="stat-label">Response Time</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function showWalletConnect() {
            const walletSection = document.getElementById('walletSection');
            walletSection.style.display = walletSection.style.display === 'none' ? 'block' : 'none';
            
            if (walletSection.style.display === 'block') {
                walletSection.scrollIntoView({ behavior: 'smooth' });
            }
        }
        
        function showFeatures() {
            document.getElementById('features').scrollIntoView({ behavior: 'smooth' });
        }
        
        async function connectWallet(walletType) {
            console.log(`Connecting to ${walletType}...`);
            
            try {
                // Check if wallet is available
                if (walletType === 'metamask' && typeof window.ethereum === 'undefined') {
                    alert('Please install MetaMask to continue');
                    return;
                }
                
                // Request wallet connection
                let accounts;
                if (walletType === 'metamask') {
                    accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
                } else {
                    alert(`${walletType} integration coming soon!`);
                    return;
                }
                
                if (accounts.length > 0) {
                    const walletAddress = accounts[0];
                    const chainId = await window.ethereum.request({ method: 'eth_chainId' });
                    
                    // Create signature message
                    const message = `Welcome to GuardianShield! Sign this message to verify your wallet ownership. Timestamp: ${Date.now()}`;
                    
                    // Request signature
                    const signature = await window.ethereum.request({
                        method: 'personal_sign',
                        params: [message, walletAddress]
                    });
                    
                    // Send to backend
                    const response = await fetch('/api/auth/connect-wallet', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            wallet_address: walletAddress,
                            wallet_type: walletType,
                            chain_id: parseInt(chainId, 16),
                            signature: signature,
                            message: message
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        // Store authentication token
                        localStorage.setItem('guardianshield_token', data.access_token);
                        localStorage.setItem('guardianshield_user', JSON.stringify({
                            user_id: data.user_id,
                            wallet_address: data.wallet_address
                        }));
                        
                        alert('Successfully connected to GuardianShield!');
                        
                        // Redirect to dashboard (when available)
                        // window.location.href = '/dashboard';
                        
                        // For now, update UI
                        updateUIForConnectedUser(data);
                        
                    } else {
                        alert(`Connection failed: ${data.detail}`);
                    }
                }
                
            } catch (error) {
                console.error('Wallet connection error:', error);
                alert('Failed to connect wallet. Please try again.');
            }
        }
        
        function updateUIForConnectedUser(userData) {
            const navButtons = document.querySelector('.nav-buttons');
            navButtons.innerHTML = `
                <span style="color: #27ae60; font-weight: 600;">
                    ✅ Connected: ${userData.wallet_address.slice(0, 6)}...${userData.wallet_address.slice(-4)}
                </span>
                <a href="/dashboard" class="btn btn-primary">Dashboard</a>
            `;
            
            document.getElementById('walletSection').style.display = 'none';
        }
        
        // Check if user is already connected
        window.addEventListener('load', function() {
            const token = localStorage.getItem('guardianshield_token');
            const user = localStorage.getItem('guardianshield_user');
            
            if (token && user) {
                const userData = JSON.parse(user);
                updateUIForConnectedUser(userData);
            }
        });
        
        // Smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                document.querySelector(this.getAttribute('href')).scrollIntoView({
                    behavior: 'smooth'
                });
            });
        });
    </script>
</body>
</html>
    '''

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting GuardianShield Community Portal...")
    print("🌐 Portal available at: http://localhost:8003")
    print("📚 API documentation at: http://localhost:8003/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0", 
        port=8003,
        log_level="info"
    )