"""
Advanced Token POS (Point of Sale) System
Comprehensive payment processing with stunning animations and user-friendly interface
"""

import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
import math
import threading
import time
import uuid
import qrcode
import io
import base64
from PIL import Image

# Import our enhanced graphics engine
from high_performance_graphics_engine import HighPerformanceGraphicsEngine

class TokenPOSSystem:
    """Advanced POS system for token payments with beautiful animations"""
    
    def __init__(self):
        self.db_path = "databases/pos_system.db"
        self.graphics_engine = HighPerformanceGraphicsEngine()
        self.active_transactions = {}
        self.payment_processors = {}
        self.animation_thread = None
        self.running = False
        
        # POS configuration
        self.pos_config = {
            "animation_fps": 120,
            "payment_timeout": 300,  # 5 minutes
            "supported_tokens": ["GUARD", "USDC", "USDT", "ETH", "BTC"],
            "payment_colors": {
                "GUARD": "#FFD700",
                "USDC": "#2775CA", 
                "USDT": "#26A17B",
                "ETH": "#627EEA",
                "BTC": "#F7931A"
            },
            "animation_intensity": 0.8,
            "particle_count": 500
        }
        
        # Payment methods
        self.payment_methods = {
            "wallet_connect": {"name": "Wallet Connect", "icon": "🔗", "enabled": True},
            "metamask": {"name": "MetaMask", "icon": "🦊", "enabled": True},
            "qr_code": {"name": "QR Code", "icon": "📱", "enabled": True},
            "nfc": {"name": "NFC", "icon": "📡", "enabled": True},
            "hardware_wallet": {"name": "Hardware Wallet", "icon": "🔐", "enabled": True}
        }
        
        # Initialize database
        self._initialize_database()
        
        # Start background animations
        self.start_pos_animations()
    
    def _initialize_database(self):
        """Initialize POS database with comprehensive tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Payment transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pos_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT UNIQUE NOT NULL,
                merchant_id TEXT NOT NULL,
                customer_address TEXT,
                amount DECIMAL(20,8) NOT NULL,
                token_symbol TEXT NOT NULL,
                usd_amount DECIMAL(20,8) NOT NULL,
                payment_method TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at DATETIME NOT NULL,
                confirmed_at DATETIME,
                tx_hash TEXT,
                block_number INTEGER,
                gas_fee DECIMAL(20,8) DEFAULT 0,
                description TEXT,
                metadata TEXT
            )
        """)
        
        # Merchant accounts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pos_merchants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                merchant_id TEXT UNIQUE NOT NULL,
                merchant_name TEXT NOT NULL,
                wallet_address TEXT NOT NULL,
                api_key TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'active',
                created_at DATETIME NOT NULL,
                settings TEXT,
                total_volume DECIMAL(20,8) DEFAULT 0,
                transaction_count INTEGER DEFAULT 0
            )
        """)
        
        # Payment methods table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pos_payment_methods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                merchant_id TEXT NOT NULL,
                method_type TEXT NOT NULL,
                method_config TEXT NOT NULL,
                is_enabled BOOLEAN DEFAULT 1,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (merchant_id) REFERENCES pos_merchants (merchant_id)
            )
        """)
        
        # Token prices table (for USD conversion)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS token_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_symbol TEXT NOT NULL,
                price_usd DECIMAL(20,8) NOT NULL,
                last_updated DATETIME NOT NULL,
                source TEXT DEFAULT 'chainlink'
            )
        """)
        
        # Daily sales analytics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pos_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                merchant_id TEXT NOT NULL,
                date DATE NOT NULL,
                total_volume DECIMAL(20,8) DEFAULT 0,
                transaction_count INTEGER DEFAULT 0,
                unique_customers INTEGER DEFAULT 0,
                average_transaction DECIMAL(20,8) DEFAULT 0,
                top_token TEXT,
                UNIQUE(merchant_id, date)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def start_pos_animations(self):
        """Start background POS animations"""
        if not self.running:
            self.running = True
            self.animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
            self.animation_thread.start()
    
    def _animation_loop(self):
        """Main animation loop for POS visualizations"""
        while self.running:
            try:
                # Update payment animations
                self._update_payment_animations()
                
                # Animate transaction processing
                self._animate_transaction_flow()
                
                # Update success/failure animations
                self._update_status_animations()
                
                # Sleep for frame timing
                time.sleep(1.0 / self.pos_config["animation_fps"])
                
            except Exception as e:
                print(f"POS animation loop error: {e}")
                time.sleep(0.1)
    
    def _update_payment_animations(self):
        """Update payment processing animations"""
        current_time = time.time()
        
        for tx_id, transaction in self.active_transactions.items():
            if transaction["status"] == "processing":
                # Create payment processing animation
                progress = (current_time - transaction["start_time"]) / 10.0  # 10 second animation
                progress = min(progress, 1.0)
                
                # Circular progress animation
                angle = progress * 2 * math.pi
                x = math.cos(angle) * 1.5
                z = math.sin(angle) * 1.5
                
                payment_particle = {
                    "position": [x, 0.5, z],
                    "velocity": [0, 0.1, 0],
                    "color": self._get_token_color(transaction["token"]),
                    "size": 0.08,
                    "life": 1.0,
                    "type": "payment_processing"
                }
    
    def _animate_transaction_flow(self):
        """Animate transaction data flow"""
        current_time = time.time()
        
        # Create data flow particles
        for i in range(10):
            flow_particle = {
                "position": [-2.0 + i * 0.4, 0, 0],
                "velocity": [2.0, 0, 0],
                "color": [0.2, 0.8, 1.0, 0.7],
                "size": 0.04,
                "life": 2.0,
                "type": "data_flow"
            }
    
    def _update_status_animations(self):
        """Update transaction status animations"""
        current_time = time.time()
        
        for tx_id, transaction in self.active_transactions.items():
            if transaction["status"] == "success":
                # Success burst animation
                self._create_success_burst(transaction)
            elif transaction["status"] == "failed":
                # Failure animation
                self._create_failure_animation(transaction)
    
    def _create_success_burst(self, transaction):
        """Create success particle burst"""
        burst_count = 50
        for i in range(burst_count):
            angle = (i / burst_count) * 2 * math.pi
            velocity_x = math.cos(angle) * 3.0
            velocity_z = math.sin(angle) * 3.0
            
            success_particle = {
                "position": [0, 1, 0],
                "velocity": [velocity_x, 2.0, velocity_z],
                "color": [0.2, 1.0, 0.2, 1.0],
                "size": 0.06,
                "life": 2.5,
                "type": "success_burst"
            }
    
    def _create_failure_animation(self, transaction):
        """Create failure animation effect"""
        # Red warning particles
        for i in range(20):
            failure_particle = {
                "position": [0, 1, 0],
                "velocity": [0, -0.5, 0],
                "color": [1.0, 0.2, 0.2, 0.9],
                "size": 0.05,
                "life": 1.5,
                "type": "failure_warning"
            }
    
    def _get_token_color(self, token_symbol: str) -> List[float]:
        """Get color for token animation"""
        color_hex = self.pos_config["payment_colors"].get(token_symbol, "#FFFFFF")
        # Convert hex to RGB float values
        rgb = tuple(int(color_hex[i:i+2], 16) for i in (1, 3, 5))
        return [rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0, 1.0]
    
    async def create_payment_request(self, 
                                   merchant_id: str, 
                                   amount: Decimal, 
                                   token: str = "GUARD",
                                   description: str = "",
                                   metadata: Dict = None) -> Dict[str, Any]:
        """Create a new payment request with animation"""
        try:
            transaction_id = str(uuid.uuid4())
            
            # Get current token price
            token_price = await self.get_token_price(token)
            usd_amount = amount * token_price
            
            # Store transaction
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO pos_transactions 
                (transaction_id, merchant_id, amount, token_symbol, usd_amount, 
                 payment_method, created_at, description, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (transaction_id, merchant_id, amount, token, usd_amount, 
                  "pending", datetime.now(), description, json.dumps(metadata or {})))
            
            conn.commit()
            conn.close()
            
            # Add to active transactions for animation
            self.active_transactions[transaction_id] = {
                "id": transaction_id,
                "amount": amount,
                "token": token,
                "usd_amount": usd_amount,
                "status": "created",
                "start_time": time.time(),
                "merchant_id": merchant_id
            }
            
            # Generate QR code for payment
            payment_url = f"guardianshield://pay/{transaction_id}"
            qr_code_data = self._generate_qr_code(payment_url)
            
            # Trigger creation animation
            await self._animate_payment_creation(transaction_id)
            
            return {
                "transaction_id": transaction_id,
                "amount": float(amount),
                "token": token,
                "usd_amount": float(usd_amount),
                "qr_code": qr_code_data,
                "payment_url": payment_url,
                "expires_at": (datetime.now() + timedelta(seconds=self.pos_config["payment_timeout"])).isoformat(),
                "status": "created"
            }
            
        except Exception as e:
            print(f"Error creating payment request: {e}")
            return None
    
    def _generate_qr_code(self, data: str) -> str:
        """Generate QR code for payment"""
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            print(f"Error generating QR code: {e}")
            return ""
    
    async def _animate_payment_creation(self, transaction_id: str):
        """Animate payment request creation"""
        try:
            # Creation sparkle effect
            for i in range(30):
                angle = (i / 30) * 2 * math.pi
                x = math.cos(angle) * 0.5
                z = math.sin(angle) * 0.5
                
                creation_particle = {
                    "position": [x, 0, z],
                    "velocity": [0, 1.0, 0],
                    "color": [0.8, 0.8, 1.0, 0.9],
                    "size": 0.04,
                    "life": 1.0,
                    "type": "creation_sparkle"
                }
                
                await asyncio.sleep(0.02)  # Stagger creation
            
        except Exception as e:
            print(f"Payment creation animation error: {e}")
    
    async def process_payment(self, 
                            transaction_id: str, 
                            customer_address: str,
                            payment_method: str,
                            tx_hash: str = None) -> Dict[str, Any]:
        """Process a payment transaction with animation"""
        try:
            # Update transaction status
            if transaction_id in self.active_transactions:
                self.active_transactions[transaction_id]["status"] = "processing"
                self.active_transactions[transaction_id]["customer_address"] = customer_address
            
            # Trigger processing animation
            await self._animate_payment_processing(transaction_id)
            
            # Simulate payment processing (in real implementation, this would verify blockchain transaction)
            await asyncio.sleep(2.0)  # Simulated processing time
            
            # Update database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE pos_transactions 
                SET customer_address = ?, payment_method = ?, status = 'confirmed', 
                    confirmed_at = ?, tx_hash = ?
                WHERE transaction_id = ?
            """, (customer_address, payment_method, datetime.now(), tx_hash, transaction_id))
            
            conn.commit()
            conn.close()
            
            # Update active transaction
            if transaction_id in self.active_transactions:
                self.active_transactions[transaction_id]["status"] = "success"
            
            # Trigger success animation
            await self._animate_payment_success(transaction_id)
            
            # Update merchant analytics
            await self._update_merchant_analytics(transaction_id)
            
            return {
                "transaction_id": transaction_id,
                "status": "confirmed",
                "tx_hash": tx_hash,
                "confirmed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error processing payment: {e}")
            
            # Mark as failed
            if transaction_id in self.active_transactions:
                self.active_transactions[transaction_id]["status"] = "failed"
            
            await self._animate_payment_failure(transaction_id)
            return {"transaction_id": transaction_id, "status": "failed", "error": str(e)}
    
    async def _animate_payment_processing(self, transaction_id: str):
        """Animate payment processing stage"""
        try:
            transaction = self.active_transactions.get(transaction_id)
            if not transaction:
                return
            
            # Processing wave animation
            for wave in range(3):
                for i in range(20):
                    angle = (i / 20) * 2 * math.pi + wave * 2
                    radius = 1.0 + wave * 0.3
                    x = math.cos(angle) * radius
                    z = math.sin(angle) * radius
                    
                    processing_particle = {
                        "position": [x, 0.2, z],
                        "velocity": [0, 0.5, 0],
                        "color": self._get_token_color(transaction["token"]),
                        "size": 0.05,
                        "life": 1.5,
                        "type": "processing_wave"
                    }
                
                await asyncio.sleep(0.2)
            
        except Exception as e:
            print(f"Processing animation error: {e}")
    
    async def _animate_payment_success(self, transaction_id: str):
        """Animate successful payment completion"""
        try:
            # Success explosion effect
            for i in range(100):
                angle = (i / 100) * 2 * math.pi
                velocity_x = math.cos(angle) * 4.0
                velocity_z = math.sin(angle) * 4.0
                velocity_y = 3.0 + math.random() * 2.0
                
                success_particle = {
                    "position": [0, 1, 0],
                    "velocity": [velocity_x, velocity_y, velocity_z],
                    "color": [0.2, 1.0, 0.2, 1.0],
                    "size": 0.08,
                    "life": 3.0,
                    "type": "success_explosion"
                }
            
            # Play success sound
            await self._play_pos_sound("success")
            
        except Exception as e:
            print(f"Success animation error: {e}")
    
    async def _animate_payment_failure(self, transaction_id: str):
        """Animate payment failure"""
        try:
            # Failure shake effect
            for i in range(10):
                shake_particle = {
                    "position": [math.random() * 0.2 - 0.1, 1, math.random() * 0.2 - 0.1],
                    "velocity": [0, -1.0, 0],
                    "color": [1.0, 0.2, 0.2, 0.9],
                    "size": 0.06,
                    "life": 1.0,
                    "type": "failure_shake"
                }
                await asyncio.sleep(0.1)
            
            # Play failure sound
            await self._play_pos_sound("failure")
            
        except Exception as e:
            print(f"Failure animation error: {e}")
    
    async def get_token_price(self, token: str) -> Decimal:
        """Get current token price in USD"""
        # This would connect to price oracles in real implementation
        price_map = {
            "GUARD": Decimal("2.50"),
            "USDC": Decimal("1.00"),
            "USDT": Decimal("1.00"),
            "ETH": Decimal("2500.00"),
            "BTC": Decimal("45000.00")
        }
        return price_map.get(token, Decimal("1.00"))
    
    def get_pos_status(self) -> Dict[str, Any]:
        """Get comprehensive POS system status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get daily stats
        today = datetime.now().date()
        cursor.execute("""
            SELECT COUNT(*), SUM(usd_amount) 
            FROM pos_transactions 
            WHERE DATE(created_at) = ? AND status = 'confirmed'
        """, (today,))
        daily_stats = cursor.fetchone()
        
        # Get top tokens
        cursor.execute("""
            SELECT token_symbol, COUNT(*), SUM(amount) 
            FROM pos_transactions 
            WHERE status = 'confirmed' 
            GROUP BY token_symbol 
            ORDER BY COUNT(*) DESC
        """)
        token_stats = cursor.fetchall()
        
        # Get recent transactions
        cursor.execute("""
            SELECT transaction_id, amount, token_symbol, usd_amount, status, created_at
            FROM pos_transactions 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        recent_transactions = cursor.fetchall()
        
        conn.close()
        
        return {
            "daily_transactions": daily_stats[0] or 0,
            "daily_volume": float(daily_stats[1] or 0),
            "active_transactions": len(self.active_transactions),
            "supported_tokens": self.pos_config["supported_tokens"],
            "payment_methods": self.payment_methods,
            "top_tokens": [
                {
                    "token": row[0],
                    "transaction_count": row[1], 
                    "total_amount": float(row[2])
                } for row in token_stats
            ],
            "recent_transactions": [
                {
                    "id": row[0],
                    "amount": float(row[1]),
                    "token": row[2],
                    "usd_amount": float(row[3]),
                    "status": row[4],
                    "created_at": row[5]
                } for row in recent_transactions
            ],
            "animation_status": {
                "fps": self.pos_config["animation_fps"],
                "particle_count": self.pos_config["particle_count"],
                "active_animations": len(self.active_transactions)
            }
        }
    
    async def _update_merchant_analytics(self, transaction_id: str):
        """Update merchant analytics data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get transaction details
            cursor.execute("""
                SELECT merchant_id, usd_amount FROM pos_transactions 
                WHERE transaction_id = ?
            """, (transaction_id,))
            result = cursor.fetchone()
            
            if result:
                merchant_id, usd_amount = result
                today = datetime.now().date()
                
                # Update daily analytics
                cursor.execute("""
                    INSERT OR REPLACE INTO pos_analytics 
                    (merchant_id, date, total_volume, transaction_count)
                    VALUES (?, ?, 
                        COALESCE((SELECT total_volume FROM pos_analytics WHERE merchant_id = ? AND date = ?), 0) + ?,
                        COALESCE((SELECT transaction_count FROM pos_analytics WHERE merchant_id = ? AND date = ?), 0) + 1)
                """, (merchant_id, today, merchant_id, today, usd_amount, merchant_id, today))
                
                conn.commit()
            
            conn.close()
            
        except Exception as e:
            print(f"Error updating analytics: {e}")
    
    async def _play_pos_sound(self, sound_type: str):
        """Play POS sound effects"""
        # This would integrate with an audio system
        sound_map = {
            "success": "🔔 Success!",
            "failure": "❌ Failed!",
            "processing": "⏳ Processing..."
        }
        print(f"🔊 POS Sound: {sound_map.get(sound_type, sound_type)}")
    
    def register_merchant(self, merchant_name: str, wallet_address: str) -> Dict[str, str]:
        """Register a new merchant"""
        try:
            merchant_id = str(uuid.uuid4())
            api_key = str(uuid.uuid4())
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO pos_merchants 
                (merchant_id, merchant_name, wallet_address, api_key, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (merchant_id, merchant_name, wallet_address, api_key, datetime.now()))
            
            conn.commit()
            conn.close()
            
            return {
                "merchant_id": merchant_id,
                "api_key": api_key,
                "status": "registered"
            }
            
        except Exception as e:
            print(f"Error registering merchant: {e}")
            return {"error": str(e)}
    
    async def shutdown(self):
        """Shutdown POS system gracefully"""
        self.running = False
        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join(timeout=1.0)
        print("💳 Token POS System shut down")

# Demonstration function
async def demonstrate_pos_system():
    """Demonstrate the token POS system"""
    print("\n💳 TOKEN POS SYSTEM DEMONSTRATION")
    print("="*60)
    
    pos = TokenPOSSystem()
    
    print("✅ POS system initialized with animations")
    
    # Register a merchant
    print("\n🏪 Registering merchant...")
    merchant = pos.register_merchant("Coffee Shop", "0x1234567890abcdef")
    merchant_id = merchant["merchant_id"]
    print(f"   ✅ Merchant registered: {merchant_id}")
    
    # Create payment request
    print("\n💰 Creating payment request...")
    payment = await pos.create_payment_request(
        merchant_id=merchant_id,
        amount=Decimal("10.50"),
        token="GUARD",
        description="Coffee and pastry"
    )
    
    if payment:
        print(f"   ✅ Payment created: {payment['transaction_id']}")
        print(f"   💵 Amount: {payment['amount']} {payment['token']} (${payment['usd_amount']:.2f})")
    
    # Simulate payment processing
    print("\n🔄 Processing payment...")
    result = await pos.process_payment(
        transaction_id=payment['transaction_id'],
        customer_address="0xcustomer123",
        payment_method="metamask",
        tx_hash="0xtransactionhash123"
    )
    
    if result["status"] == "confirmed":
        print("   ✅ Payment processed successfully!")
    
    # Show system status
    status = pos.get_pos_status()
    print(f"\n📊 POS System Status:")
    print(f"   📈 Daily Transactions: {status['daily_transactions']}")
    print(f"   💵 Daily Volume: ${status['daily_volume']:,.2f}")
    print(f"   🎮 Active Animations: {status['active_animations']}")
    print(f"   ⚡ Animation FPS: {status['animation_status']['fps']}")
    
    await pos.shutdown()
    print("✅ POS demonstration completed!")

if __name__ == "__main__":
    asyncio.run(demonstrate_pos_system())