#!/usr/bin/env python3
"""
GuardianShield NFT Builder Platform
Advanced NFT creation system with GUARD token integration
"""

import uvicorn
import sqlite3
import hashlib
import json
import base64
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# NFT Rarity and Type Enums
class NFTRarity(str, Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"  
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    MYTHIC = "mythic"

class NFTCategory(str, Enum):
    ART = "art"
    COLLECTIBLE = "collectible"
    GAMING = "gaming"
    MUSIC = "music"
    UTILITY = "utility"
    MEMBERSHIP = "membership"

# Pydantic Models
class NFTCreateRequest(BaseModel):
    name: str
    description: str
    category: NFTCategory
    rarity: NFTRarity
    guard_price: float
    royalty_percentage: float
    creator_address: str
    attributes: Dict[str, Any] = {}
    external_url: Optional[str] = None

class NFTMetadata(BaseModel):
    token_id: str
    name: str
    description: str
    image: str
    external_url: Optional[str]
    attributes: List[Dict[str, Any]]
    creator: str
    created_date: str
    guard_price: float
    rarity: NFTRarity
    category: NFTCategory

@dataclass
class NFTToken:
    token_id: str
    name: str
    description: str
    image_hash: str
    image_url: str
    creator_address: str
    owner_address: str
    guard_price: float
    royalty_percentage: float
    category: NFTCategory
    rarity: NFTRarity
    attributes: Dict[str, Any]
    created_timestamp: datetime
    last_sale_price: Optional[float]
    sale_count: int
    is_listed: bool
    external_url: Optional[str]

class NFTManager:
    """Manages NFT creation, storage, and marketplace operations"""
    
    def __init__(self, db_path: str = "nft_builder.db"):
        self.db_path = db_path
        self.init_database()
        
        # Create uploads directory
        Path("uploads/nfts").mkdir(parents=True, exist_ok=True)
    
    def init_database(self):
        """Initialize NFT database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # NFT tokens table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nft_tokens (
                token_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                image_hash TEXT NOT NULL,
                image_url TEXT NOT NULL,
                creator_address TEXT NOT NULL,
                owner_address TEXT NOT NULL,
                guard_price REAL NOT NULL,
                royalty_percentage REAL DEFAULT 5.0,
                category TEXT NOT NULL,
                rarity TEXT NOT NULL,
                attributes TEXT,
                created_timestamp TEXT NOT NULL,
                last_sale_price REAL,
                sale_count INTEGER DEFAULT 0,
                is_listed INTEGER DEFAULT 0,
                external_url TEXT
            )
        """)
        
        # NFT marketplace listings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nft_listings (
                listing_id TEXT PRIMARY KEY,
                token_id TEXT NOT NULL,
                seller_address TEXT NOT NULL,
                guard_price REAL NOT NULL,
                created_timestamp TEXT NOT NULL,
                expires_timestamp TEXT,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (token_id) REFERENCES nft_tokens (token_id)
            )
        """)
        
        # NFT collections
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nft_collections (
                collection_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                creator_address TEXT NOT NULL,
                banner_image TEXT,
                floor_price REAL DEFAULT 0,
                total_volume REAL DEFAULT 0,
                item_count INTEGER DEFAULT 0,
                created_timestamp TEXT NOT NULL
            )
        """)
        
        # NFT transaction history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nft_transactions (
                transaction_id TEXT PRIMARY KEY,
                token_id TEXT NOT NULL,
                from_address TEXT,
                to_address TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                guard_amount REAL,
                gas_fee REAL DEFAULT 0,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (token_id) REFERENCES nft_tokens (token_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def generate_token_id(self, name: str, creator: str) -> str:
        """Generate unique token ID"""
        timestamp = datetime.now().isoformat()
        data = f"{name}_{creator}_{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def calculate_image_hash(self, image_data: bytes) -> str:
        """Calculate SHA256 hash of image data"""
        return hashlib.sha256(image_data).hexdigest()
    
    def get_rarity_multiplier(self, rarity: NFTRarity) -> float:
        """Get price multiplier based on rarity"""
        multipliers = {
            NFTRarity.COMMON: 1.0,
            NFTRarity.UNCOMMON: 2.0,
            NFTRarity.RARE: 5.0,
            NFTRarity.EPIC: 10.0,
            NFTRarity.LEGENDARY: 25.0,
            NFTRarity.MYTHIC: 50.0
        }
        return multipliers.get(rarity, 1.0)
    
    async def create_nft(self, request: NFTCreateRequest, image_file: UploadFile) -> NFTToken:
        """Create a new NFT token"""
        # Read image data
        image_data = await image_file.read()
        image_hash = self.calculate_image_hash(image_data)
        
        # Generate token ID
        token_id = self.generate_token_id(request.name, request.creator_address)
        
        # Save image file
        image_filename = f"{token_id}_{image_file.filename}"
        image_path = Path("uploads/nfts") / image_filename
        
        with open(image_path, "wb") as f:
            f.write(image_data)
        
        image_url = f"/uploads/nfts/{image_filename}"
        
        # Apply rarity multiplier to price
        rarity_multiplier = self.get_rarity_multiplier(request.rarity)
        final_price = request.guard_price * rarity_multiplier
        
        # Create NFT token
        nft_token = NFTToken(
            token_id=token_id,
            name=request.name,
            description=request.description,
            image_hash=image_hash,
            image_url=image_url,
            creator_address=request.creator_address,
            owner_address=request.creator_address,
            guard_price=final_price,
            royalty_percentage=request.royalty_percentage,
            category=request.category,
            rarity=request.rarity,
            attributes=request.attributes,
            created_timestamp=datetime.now(),
            last_sale_price=None,
            sale_count=0,
            is_listed=False,
            external_url=request.external_url
        )
        
        # Save to database
        self.save_nft_token(nft_token)
        
        # Record creation transaction
        self.record_transaction(
            token_id=token_id,
            from_address=None,
            to_address=request.creator_address,
            transaction_type="mint",
            guard_amount=0
        )
        
        return nft_token
    
    def save_nft_token(self, nft: NFTToken):
        """Save NFT token to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO nft_tokens VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nft.token_id, nft.name, nft.description, nft.image_hash, nft.image_url,
            nft.creator_address, nft.owner_address, nft.guard_price, nft.royalty_percentage,
            nft.category.value, nft.rarity.value, json.dumps(nft.attributes),
            nft.created_timestamp.isoformat(), nft.last_sale_price, nft.sale_count,
            int(nft.is_listed), nft.external_url
        ))
        
        conn.commit()
        conn.close()
    
    def record_transaction(self, token_id: str, from_address: Optional[str], to_address: str, 
                         transaction_type: str, guard_amount: float):
        """Record NFT transaction"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        transaction_id = hashlib.sha256(f"{token_id}_{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        
        cursor.execute("""
            INSERT INTO nft_transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            transaction_id, token_id, from_address, to_address,
            transaction_type, guard_amount, 0, datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_all_nfts(self) -> List[Dict]:
        """Get all NFT tokens"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM nft_tokens ORDER BY created_timestamp DESC
        """)
        
        nfts = []
        for row in cursor.fetchall():
            nft = {
                'token_id': row[0],
                'name': row[1],
                'description': row[2],
                'image_hash': row[3],
                'image_url': row[4],
                'creator_address': row[5],
                'owner_address': row[6],
                'guard_price': row[7],
                'royalty_percentage': row[8],
                'category': row[9],
                'rarity': row[10],
                'attributes': json.loads(row[11]) if row[11] else {},
                'created_timestamp': row[12],
                'last_sale_price': row[13],
                'sale_count': row[14],
                'is_listed': bool(row[15]),
                'external_url': row[16]
            }
            nfts.append(nft)
        
        conn.close()
        return nfts
    
    def get_nft_by_id(self, token_id: str) -> Optional[Dict]:
        """Get NFT by token ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM nft_tokens WHERE token_id = ?", (token_id,))
        row = cursor.fetchone()
        
        if row:
            nft = {
                'token_id': row[0],
                'name': row[1],
                'description': row[2],
                'image_hash': row[3],
                'image_url': row[4],
                'creator_address': row[5],
                'owner_address': row[6],
                'guard_price': row[7],
                'royalty_percentage': row[8],
                'category': row[9],
                'rarity': row[10],
                'attributes': json.loads(row[11]) if row[11] else {},
                'created_timestamp': row[12],
                'last_sale_price': row[13],
                'sale_count': row[14],
                'is_listed': bool(row[15]),
                'external_url': row[16]
            }
            conn.close()
            return nft
        
        conn.close()
        return None
    
    def get_marketplace_stats(self) -> Dict:
        """Get marketplace statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total NFTs
        cursor.execute("SELECT COUNT(*) FROM nft_tokens")
        total_nfts = cursor.fetchone()[0]
        
        # Listed NFTs
        cursor.execute("SELECT COUNT(*) FROM nft_tokens WHERE is_listed = 1")
        listed_nfts = cursor.fetchone()[0]
        
        # Total volume
        cursor.execute("SELECT SUM(guard_amount) FROM nft_transactions WHERE transaction_type = 'sale'")
        total_volume = cursor.fetchone()[0] or 0
        
        # Average price
        cursor.execute("SELECT AVG(guard_price) FROM nft_tokens WHERE is_listed = 1")
        avg_price = cursor.fetchone()[0] or 0
        
        # Top categories
        cursor.execute("""
            SELECT category, COUNT(*) as count 
            FROM nft_tokens 
            GROUP BY category 
            ORDER BY count DESC 
            LIMIT 5
        """)
        top_categories = [{'category': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'total_nfts': total_nfts,
            'listed_nfts': listed_nfts,
            'total_volume': total_volume,
            'average_price': avg_price,
            'top_categories': top_categories
        }

# Initialize FastAPI app and NFT manager
app = FastAPI(title="GuardianShield NFT Builder", version="2.0.0")
nft_manager = NFTManager()

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/", response_class=HTMLResponse)
async def nft_builder_interface():
    """Serve the NFT Builder interface"""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GuardianShield NFT Builder</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            
            body {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #0a0e1a 0%, #1a2332 50%, #2d3e50 100%);
                color: #e0e6ed;
                min-height: 100vh;
                line-height: 1.6;
            }}
            
            .header {{
                background: linear-gradient(135deg, #2c3e50, #34495e);
                padding: 1.5rem 0;
                border-bottom: 3px solid #27ae60;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            }}
            
            .header-content {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 2rem;
                display: flex;
                align-items: center;
                gap: 1rem;
            }}
            
            .logo {{
                display: flex;
                align-items: center;
                gap: 1rem;
            }}
            
            .nft-icon {{
                width: 50px;
                height: 50px;
                background: linear-gradient(45deg, #e74c3c, #c0392b);
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.5rem;
                font-weight: bold;
                color: white;
                box-shadow: 0 4px 15px rgba(231, 76, 60, 0.3);
            }}
            
            .logo h1 {{
                color: #ecf0f1;
                font-size: 1.8rem;
                font-weight: 600;
            }}
            
            .main-content {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 3rem 2rem;
            }}
            
            .builder-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 3rem;
                margin-bottom: 3rem;
            }}
            
            .builder-section {{
                background: linear-gradient(135deg, #1e3c72, #2a5298);
                padding: 2rem;
                border-radius: 15px;
                border: 2px solid #3498db;
            }}
            
            .section-title {{
                color: #27ae60;
                font-size: 1.5rem;
                margin-bottom: 1.5rem;
                text-align: center;
                font-weight: 600;
            }}
            
            .form-group {{
                margin-bottom: 1.5rem;
            }}
            
            .form-label {{
                display: block;
                color: #ecf0f1;
                font-weight: 600;
                margin-bottom: 0.5rem;
                font-size: 0.9rem;
            }}
            
            .form-input, .form-select, .form-textarea {{
                width: 100%;
                padding: 12px 15px;
                border: 1px solid #34495e;
                border-radius: 8px;
                background: rgba(52, 73, 94, 0.8);
                color: #ecf0f1;
                font-size: 1rem;
            }}
            
            .form-input:focus, .form-select:focus, .form-textarea:focus {{
                outline: none;
                border-color: #3498db;
                box-shadow: 0 0 10px rgba(52, 152, 219, 0.3);
            }}
            
            .form-textarea {{
                min-height: 100px;
                resize: vertical;
            }}
            
            .file-upload {{
                border: 2px dashed #34495e;
                border-radius: 8px;
                padding: 2rem;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s ease;
            }}
            
            .file-upload:hover {{
                border-color: #3498db;
                background: rgba(52, 152, 219, 0.1);
            }}
            
            .file-upload.dragover {{
                border-color: #27ae60;
                background: rgba(39, 174, 96, 0.1);
            }}
            
            .rarity-selector {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 0.5rem;
                margin-top: 0.5rem;
            }}
            
            .rarity-option {{
                padding: 0.8rem;
                border: 1px solid #34495e;
                border-radius: 6px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s ease;
                font-size: 0.85rem;
            }}
            
            .rarity-option.common {{ background: linear-gradient(45deg, #95a5a6, #7f8c8d); }}
            .rarity-option.uncommon {{ background: linear-gradient(45deg, #27ae60, #2ecc71); }}
            .rarity-option.rare {{ background: linear-gradient(45deg, #3498db, #5dade2); }}
            .rarity-option.epic {{ background: linear-gradient(45deg, #9b59b6, #bb7ae8); }}
            .rarity-option.legendary {{ background: linear-gradient(45deg, #f39c12, #f1c40f); }}
            .rarity-option.mythic {{ background: linear-gradient(45deg, #e74c3c, #ec7063); }}
            
            .rarity-option:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            }}
            
            .rarity-option.selected {{
                border-color: #27ae60;
                box-shadow: 0 0 15px rgba(39, 174, 96, 0.5);
            }}
            
            .create-button {{
                width: 100%;
                padding: 15px;
                background: linear-gradient(45deg, #27ae60, #2ecc71);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 1.1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                margin-top: 1rem;
            }}
            
            .create-button:hover {{
                background: linear-gradient(45deg, #2ecc71, #58d68d);
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(39, 174, 96, 0.4);
            }}
            
            .create-button:disabled {{
                background: #7f8c8d;
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }}
            
            .marketplace-section {{
                background: linear-gradient(135deg, #2c3e50, #34495e);
                padding: 2rem;
                border-radius: 15px;
                border: 2px solid #e74c3c;
            }}
            
            .nft-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                gap: 2rem;
                margin-top: 2rem;
            }}
            
            .nft-card {{
                background: rgba(26, 35, 50, 0.8);
                border-radius: 12px;
                overflow: hidden;
                border: 1px solid rgba(231, 76, 60, 0.3);
                transition: all 0.3s ease;
                cursor: pointer;
            }}
            
            .nft-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 10px 30px rgba(231, 76, 60, 0.3);
                border-color: #e74c3c;
            }}
            
            .nft-image {{
                width: 100%;
                height: 200px;
                object-fit: cover;
                background: linear-gradient(45deg, #34495e, #2c3e50);
            }}
            
            .nft-info {{
                padding: 1.5rem;
            }}
            
            .nft-name {{
                font-size: 1.1rem;
                font-weight: 600;
                color: #ecf0f1;
                margin-bottom: 0.5rem;
            }}
            
            .nft-price {{
                color: #f39c12;
                font-size: 1.2rem;
                font-weight: bold;
            }}
            
            .nft-rarity {{
                display: inline-block;
                padding: 0.3rem 0.8rem;
                border-radius: 15px;
                font-size: 0.8rem;
                font-weight: 600;
                margin-top: 0.5rem;
            }}
            
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1.5rem;
                margin-bottom: 2rem;
            }}
            
            .stat-card {{
                background: rgba(26, 35, 50, 0.6);
                padding: 1.5rem;
                border-radius: 10px;
                text-align: center;
                border: 1px solid rgba(39, 174, 96, 0.3);
            }}
            
            .stat-value {{
                font-size: 2rem;
                font-weight: bold;
                color: #27ae60;
                margin-bottom: 0.5rem;
            }}
            
            .stat-label {{
                color: #bdc3c7;
                font-size: 0.9rem;
            }}
            
            @media (max-width: 768px) {{
                .builder-grid {{
                    grid-template-columns: 1fr;
                }}
                
                .main-content {{
                    padding: 2rem 1rem;
                }}
                
                .rarity-selector {{
                    grid-template-columns: repeat(2, 1fr);
                }}
                
                .stats-grid {{
                    grid-template-columns: repeat(2, 1fr);
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <div class="logo">
                    <div class="nft-icon">🎨</div>
                    <h1>NFT Builder Platform</h1>
                </div>
            </div>
        </div>
        
        <div class="main-content">
            <div class="builder-grid">
                <div class="builder-section">
                    <h2 class="section-title">🏗️ Create Your NFT</h2>
                    
                    <form id="nftForm" enctype="multipart/form-data">
                        <div class="form-group">
                            <label class="form-label">NFT Name</label>
                            <input type="text" class="form-input" id="nftName" placeholder="Enter NFT name" required>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Description</label>
                            <textarea class="form-textarea" id="nftDescription" placeholder="Describe your NFT..." required></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Category</label>
                            <select class="form-select" id="nftCategory" required>
                                <option value="">Select category...</option>
                                <option value="art">🎨 Art</option>
                                <option value="collectible">🏆 Collectible</option>
                                <option value="gaming">🎮 Gaming</option>
                                <option value="music">🎵 Music</option>
                                <option value="utility">🔧 Utility</option>
                                <option value="membership">👥 Membership</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Rarity Level</label>
                            <div class="rarity-selector">
                                <div class="rarity-option common" data-rarity="common">
                                    Common<br>1x Price
                                </div>
                                <div class="rarity-option uncommon" data-rarity="uncommon">
                                    Uncommon<br>2x Price
                                </div>
                                <div class="rarity-option rare" data-rarity="rare">
                                    Rare<br>5x Price
                                </div>
                                <div class="rarity-option epic" data-rarity="epic">
                                    Epic<br>10x Price
                                </div>
                                <div class="rarity-option legendary" data-rarity="legendary">
                                    Legendary<br>25x Price
                                </div>
                                <div class="rarity-option mythic" data-rarity="mythic">
                                    Mythic<br>50x Price
                                </div>
                            </div>
                            <input type="hidden" id="nftRarity" required>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Base Price (GUARD Tokens)</label>
                            <input type="number" class="form-input" id="guardPrice" placeholder="Enter base price" step="0.01" required>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Royalty Percentage</label>
                            <input type="number" class="form-input" id="royaltyPercent" placeholder="5.0" step="0.1" max="20" value="5.0" required>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Creator Address</label>
                            <input type="text" class="form-input" id="creatorAddress" placeholder="0x..." required>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">NFT Image</label>
                            <div class="file-upload" id="fileUpload">
                                <div>
                                    📁 Click or drag image here<br>
                                    <small>PNG, JPG, GIF up to 10MB</small>
                                </div>
                                <input type="file" id="nftImage" accept="image/*" style="display: none;" required>
                            </div>
                        </div>
                        
                        <button type="submit" class="create-button" id="createButton">
                            🚀 Create NFT
                        </button>
                    </form>
                </div>
                
                <div class="builder-section">
                    <h2 class="section-title">📊 Preview & Stats</h2>
                    
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value" id="totalNFTs">-</div>
                            <div class="stat-label">Total NFTs</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="totalVolume">-</div>
                            <div class="stat-label">Volume (GUARD)</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="avgPrice">-</div>
                            <div class="stat-label">Avg Price</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="listedNFTs">-</div>
                            <div class="stat-label">Listed NFTs</div>
                        </div>
                    </div>
                    
                    <div id="nftPreview" style="display: none;">
                        <h3 style="color: #27ae60; margin-bottom: 1rem;">Preview</h3>
                        <div class="nft-card">
                            <img id="previewImage" class="nft-image">
                            <div class="nft-info">
                                <div class="nft-name" id="previewName">NFT Name</div>
                                <div class="nft-price" id="previewPrice">0 GUARD</div>
                                <div class="nft-rarity" id="previewRarity">common</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="marketplace-section">
                <h2 class="section-title">🏪 NFT Marketplace</h2>
                <div class="nft-grid" id="nftGrid">
                    <!-- NFTs will be loaded here -->
                </div>
            </div>
        </div>
        
        <script>
            let selectedRarity = null;
            let rarityMultipliers = {{
                'common': 1.0,
                'uncommon': 2.0, 
                'rare': 5.0,
                'epic': 10.0,
                'legendary': 25.0,
                'mythic': 50.0
            }};
            
            // Rarity selection
            document.querySelectorAll('.rarity-option').forEach(option => {{
                option.addEventListener('click', function() {{
                    document.querySelectorAll('.rarity-option').forEach(opt => opt.classList.remove('selected'));
                    this.classList.add('selected');
                    selectedRarity = this.dataset.rarity;
                    document.getElementById('nftRarity').value = selectedRarity;
                    updatePreview();
                }});
            }});
            
            // File upload handling
            const fileUpload = document.getElementById('fileUpload');
            const fileInput = document.getElementById('nftImage');
            
            fileUpload.addEventListener('click', () => fileInput.click());
            
            fileUpload.addEventListener('dragover', (e) => {{
                e.preventDefault();
                fileUpload.classList.add('dragover');
            }});
            
            fileUpload.addEventListener('dragleave', () => {{
                fileUpload.classList.remove('dragover');
            }});
            
            fileUpload.addEventListener('drop', (e) => {{
                e.preventDefault();
                fileUpload.classList.remove('dragover');
                const files = e.dataTransfer.files;
                if (files.length > 0) {{
                    fileInput.files = files;
                    updatePreview();
                }}
            }});
            
            fileInput.addEventListener('change', updatePreview);
            
            // Form inputs preview update
            ['nftName', 'guardPrice'].forEach(id => {{
                document.getElementById(id).addEventListener('input', updatePreview);
            }});
            
            function updatePreview() {{
                const name = document.getElementById('nftName').value;
                const basePrice = parseFloat(document.getElementById('guardPrice').value) || 0;
                const file = fileInput.files[0];
                
                if (name || basePrice || selectedRarity || file) {{
                    document.getElementById('nftPreview').style.display = 'block';
                    
                    if (name) document.getElementById('previewName').textContent = name;
                    
                    if (basePrice && selectedRarity) {{
                        const finalPrice = basePrice * rarityMultipliers[selectedRarity];
                        document.getElementById('previewPrice').textContent = finalPrice.toFixed(2) + ' GUARD';
                    }}
                    
                    if (selectedRarity) {{
                        const rarityElement = document.getElementById('previewRarity');
                        rarityElement.textContent = selectedRarity.toUpperCase();
                        rarityElement.className = 'nft-rarity ' + selectedRarity;
                    }}
                    
                    if (file) {{
                        const reader = new FileReader();
                        reader.onload = (e) => {{
                            document.getElementById('previewImage').src = e.target.result;
                        }};
                        reader.readAsDataURL(file);
                    }}
                }}
            }}
            
            // Form submission
            document.getElementById('nftForm').addEventListener('submit', async (e) => {{
                e.preventDefault();
                
                const formData = new FormData();
                formData.append('name', document.getElementById('nftName').value);
                formData.append('description', document.getElementById('nftDescription').value);
                formData.append('category', document.getElementById('nftCategory').value);
                formData.append('rarity', selectedRarity);
                formData.append('guard_price', document.getElementById('guardPrice').value);
                formData.append('royalty_percentage', document.getElementById('royaltyPercent').value);
                formData.append('creator_address', document.getElementById('creatorAddress').value);
                formData.append('image', fileInput.files[0]);
                
                const button = document.getElementById('createButton');
                button.disabled = true;
                button.textContent = '🔄 Creating NFT...';
                
                try {{
                    const response = await fetch('/api/nft/create', {{
                        method: 'POST',
                        body: formData
                    }});
                    
                    if (response.ok) {{
                        const result = await response.json();
                        alert('NFT created successfully! Token ID: ' + result.token_id);
                        document.getElementById('nftForm').reset();
                        document.getElementById('nftPreview').style.display = 'none';
                        selectedRarity = null;
                        document.querySelectorAll('.rarity-option').forEach(opt => opt.classList.remove('selected'));
                        loadNFTs();
                        loadStats();
                    }} else {{
                        const error = await response.json();
                        alert('Error creating NFT: ' + error.detail);
                    }}
                }} catch (error) {{
                    alert('Error creating NFT: ' + error.message);
                }} finally {{
                    button.disabled = false;
                    button.textContent = '🚀 Create NFT';
                }}
            }});
            
            // Load NFTs
            async function loadNFTs() {{
                try {{
                    const response = await fetch('/api/nft/all');
                    const nfts = await response.json();
                    
                    const grid = document.getElementById('nftGrid');
                    grid.innerHTML = nfts.map(nft => `
                        <div class="nft-card" onclick="viewNFT('${{nft.token_id}}')">
                            <img src="${{nft.image_url}}" class="nft-image" alt="${{nft.name}}">
                            <div class="nft-info">
                                <div class="nft-name">${{nft.name}}</div>
                                <div class="nft-price">${{nft.guard_price}} GUARD</div>
                                <div class="nft-rarity ${{nft.rarity}}">${{nft.rarity.toUpperCase()}}</div>
                            </div>
                        </div>
                    `).join('');
                }} catch (error) {{
                    console.error('Error loading NFTs:', error);
                }}
            }}
            
            // Load marketplace stats
            async function loadStats() {{
                try {{
                    const response = await fetch('/api/nft/stats');
                    const stats = await response.json();
                    
                    document.getElementById('totalNFTs').textContent = stats.total_nfts;
                    document.getElementById('totalVolume').textContent = stats.total_volume.toFixed(2);
                    document.getElementById('avgPrice').textContent = stats.average_price.toFixed(2);
                    document.getElementById('listedNFTs').textContent = stats.listed_nfts;
                }} catch (error) {{
                    console.error('Error loading stats:', error);
                }}
            }}
            
            function viewNFT(tokenId) {{
                window.open(`/nft/${{tokenId}}`, '_blank');
            }}
            
            // Initialize
            loadNFTs();
            loadStats();
            
            // Auto-refresh every 30 seconds
            setInterval(() => {{
                loadNFTs();
                loadStats();
            }}, 30000);
        </script>
    </body>
    </html>
    """

@app.post("/api/nft/create")
async def create_nft(
    name: str = Form(...),
    description: str = Form(...),
    category: NFTCategory = Form(...),
    rarity: NFTRarity = Form(...),
    guard_price: float = Form(...),
    royalty_percentage: float = Form(...),
    creator_address: str = Form(...),
    external_url: Optional[str] = Form(None),
    image: UploadFile = File(...)
):
    """Create a new NFT"""
    try:
        # Validate image
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Check file size (10MB limit)
        contents = await image.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image too large (max 10MB)")
        
        # Reset file pointer
        await image.seek(0)
        
        request = NFTCreateRequest(
            name=name,
            description=description,
            category=category,
            rarity=rarity,
            guard_price=guard_price,
            royalty_percentage=royalty_percentage,
            creator_address=creator_address,
            external_url=external_url
        )
        
        nft_token = await nft_manager.create_nft(request, image)
        
        return {
            "success": True,
            "token_id": nft_token.token_id,
            "name": nft_token.name,
            "final_price": nft_token.guard_price,
            "rarity": nft_token.rarity.value,
            "image_url": nft_token.image_url
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NFT creation failed: {str(e)}")

@app.get("/api/nft/all")
async def get_all_nfts():
    """Get all NFT tokens"""
    try:
        nfts = nft_manager.get_all_nfts()
        return nfts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/nft/{token_id}")
async def get_nft(token_id: str):
    """Get specific NFT by token ID"""
    try:
        nft = nft_manager.get_nft_by_id(token_id)
        if not nft:
            raise HTTPException(status_code=404, detail="NFT not found")
        return nft
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/nft/stats")
async def get_marketplace_stats():
    """Get marketplace statistics"""
    try:
        stats = nft_manager.get_marketplace_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/nft/{token_id}", response_class=HTMLResponse)
async def nft_detail_page(token_id: str):
    """NFT detail page"""
    nft = nft_manager.get_nft_by_id(token_id)
    if not nft:
        raise HTTPException(status_code=404, detail="NFT not found")
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{nft['name']} - GuardianShield NFT</title>
        <style>
            body {{
                font-family: 'Inter', sans-serif;
                background: linear-gradient(135deg, #0a0e1a 0%, #1a2332 50%, #2d3e50 100%);
                color: #e0e6ed;
                margin: 0;
                padding: 2rem;
                min-height: 100vh;
            }}
            .container {{
                max-width: 1000px;
                margin: 0 auto;
                background: rgba(26, 35, 50, 0.8);
                border-radius: 20px;
                padding: 2rem;
                border: 2px solid #e74c3c;
            }}
            .nft-header {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 3rem;
                margin-bottom: 3rem;
            }}
            .nft-image {{
                width: 100%;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            }}
            .nft-details h1 {{
                font-size: 2.5rem;
                color: #27ae60;
                margin-bottom: 1rem;
            }}
            .nft-price {{
                font-size: 2rem;
                color: #f39c12;
                font-weight: bold;
                margin-bottom: 1rem;
            }}
            .nft-rarity {{
                display: inline-block;
                padding: 0.5rem 1rem;
                border-radius: 20px;
                font-weight: bold;
                margin-bottom: 1rem;
            }}
            .attributes {{
                background: rgba(52, 73, 94, 0.6);
                padding: 1.5rem;
                border-radius: 10px;
                margin-top: 2rem;
            }}
            .back-button {{
                background: linear-gradient(45deg, #3498db, #5dade2);
                color: white;
                padding: 0.8rem 1.5rem;
                border: none;
                border-radius: 8px;
                text-decoration: none;
                display: inline-block;
                margin-bottom: 2rem;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-button">← Back to Builder</a>
            
            <div class="nft-header">
                <div>
                    <img src="{nft['image_url']}" class="nft-image" alt="{nft['name']}">
                </div>
                <div class="nft-details">
                    <h1>{nft['name']}</h1>
                    <div class="nft-price">{nft['guard_price']} GUARD</div>
                    <div class="nft-rarity {nft['rarity']}">{nft['rarity'].upper()}</div>
                    <p>{nft['description']}</p>
                    
                    <div style="margin-top: 2rem;">
                        <p><strong>Creator:</strong> {nft['creator_address'][:10]}...</p>
                        <p><strong>Owner:</strong> {nft['owner_address'][:10]}...</p>
                        <p><strong>Category:</strong> {nft['category'].title()}</p>
                        <p><strong>Created:</strong> {nft['created_timestamp'][:10]}</p>
                        <p><strong>Royalty:</strong> {nft['royalty_percentage']}%</p>
                    </div>
                </div>
            </div>
            
            {f'<div class="attributes"><h3>Attributes</h3>{nft["attributes"]}</div>' if nft.get('attributes') else ''}
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    print("🎨 Starting GuardianShield NFT Builder Platform...")
    print("🚀 Builder available at: http://localhost:8007")
    print("📈 API documentation at: http://localhost:8007/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0", 
        port=8007,
        log_level="info"
    )