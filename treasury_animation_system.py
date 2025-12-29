"""
Advanced Treasury Animation System
Comprehensive treasury management with stunning animations and real-time dashboard
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

# Import our enhanced graphics engine
from high_performance_graphics_engine import HighPerformanceGraphicsEngine

class TreasuryAnimationSystem:
    """Advanced treasury system with beautiful animations and comprehensive management"""
    
    def __init__(self):
        self.db_path = "databases/treasury_system.db"
        self.graphics_engine = HighPerformanceGraphicsEngine()
        self.treasury_balance = Decimal("0")
        self.total_staked = Decimal("0")
        self.active_animations = {}
        self.animation_thread = None
        self.running = False
        
        # Treasury configuration
        self.treasury_config = {
            "animation_fps": 120,
            "particle_count": 2000,
            "glow_intensity": 0.8,
            "rotation_speed": 1.5,
            "pulsation_rate": 2.0,
            "treasure_colors": ["#FFD700", "#FFA500", "#FF6347", "#32CD32", "#00CED1"]
        }
        
        # Initialize database
        self._initialize_database()
        
        # Start background animations
        self.start_treasury_animations()
    
    def _initialize_database(self):
        """Initialize treasury database with comprehensive tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Treasury transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS treasury_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_hash TEXT UNIQUE,
                transaction_type TEXT NOT NULL,
                amount DECIMAL(20,8) NOT NULL,
                token_symbol TEXT NOT NULL,
                from_address TEXT,
                to_address TEXT,
                timestamp DATETIME NOT NULL,
                status TEXT DEFAULT 'pending',
                gas_fee DECIMAL(20,8) DEFAULT 0,
                block_number INTEGER,
                description TEXT,
                category TEXT
            )
        """)
        
        # Treasury balances table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS treasury_balances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_symbol TEXT UNIQUE NOT NULL,
                balance DECIMAL(20,8) NOT NULL DEFAULT 0,
                locked_balance DECIMAL(20,8) NOT NULL DEFAULT 0,
                staked_balance DECIMAL(20,8) NOT NULL DEFAULT 0,
                last_updated DATETIME NOT NULL,
                apy_rate DECIMAL(10,4) DEFAULT 0,
                price_usd DECIMAL(20,8) DEFAULT 0
            )
        """)
        
        # Treasury allocations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS treasury_allocations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                allocation_name TEXT NOT NULL,
                percentage DECIMAL(10,4) NOT NULL,
                allocated_amount DECIMAL(20,8) NOT NULL,
                target_amount DECIMAL(20,8),
                allocation_type TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # Treasury performance metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS treasury_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                metric_value DECIMAL(20,8) NOT NULL,
                metric_type TEXT NOT NULL,
                recorded_at DATETIME NOT NULL,
                period_type TEXT DEFAULT 'daily'
            )
        """)
        
        conn.commit()
        conn.close()
    
    def start_treasury_animations(self):
        """Start background treasury animations"""
        if not self.running:
            self.running = True
            self.animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
            self.animation_thread.start()
    
    def _animation_loop(self):
        """Main animation loop for treasury visualizations"""
        while self.running:
            try:
                # Update treasury particle systems
                self._update_treasury_particles()
                
                # Animate treasure vault
                self._animate_treasure_vault()
                
                # Update performance visualizations
                self._update_performance_animations()
                
                # Sleep for frame timing
                time.sleep(1.0 / self.treasury_config["animation_fps"])
                
            except Exception as e:
                print(f"Animation loop error: {e}")
                time.sleep(0.1)
    
    def _update_treasury_particles(self):
        """Update treasury particle effects"""
        current_time = time.time()
        
        # Golden treasure particles
        treasure_particles = {
            "position": [0, 0, 0],
            "velocity": [0.1, 0.2, 0.0],
            "color": [1.0, 0.8, 0.0, 0.9],
            "size": 0.05,
            "life": 2.0,
            "emission_rate": 100
        }
        
        # Create sparkle effects around treasury
        sparkle_count = int(self.treasury_balance / 1000) if self.treasury_balance > 0 else 10
        for i in range(min(sparkle_count, 500)):
            angle = (i / sparkle_count) * 2 * math.pi
            radius = 2.0 + math.sin(current_time * 2 + i * 0.1) * 0.5
            
            x = math.cos(angle) * radius
            y = math.sin(current_time * 3 + i * 0.2) * 0.3
            z = math.sin(angle) * radius
            
            sparkle_particle = {
                "position": [x, y, z],
                "velocity": [0, 0.1, 0],
                "color": [1.0, 0.9, 0.3, 0.8],
                "size": 0.03,
                "life": 1.5
            }
    
    def _animate_treasure_vault(self):
        """Animate the main treasure vault visualization"""
        current_time = time.time()
        
        # Vault rotation animation
        rotation_y = current_time * self.treasury_config["rotation_speed"]
        
        # Pulsating glow based on treasury activity
        pulse_intensity = (math.sin(current_time * self.treasury_config["pulsation_rate"]) + 1) / 2
        glow_strength = self.treasury_config["glow_intensity"] * pulse_intensity
        
        # Dynamic vault size based on treasury balance
        vault_scale = 1.0 + float(self.treasury_balance) / 1000000 * 0.5
        
        vault_animation = {
            "rotation": [0, rotation_y, 0],
            "scale": [vault_scale, vault_scale, vault_scale],
            "glow_intensity": glow_strength,
            "timestamp": current_time
        }
        
        self.active_animations["treasure_vault"] = vault_animation
    
    def _update_performance_animations(self):
        """Update performance metric animations"""
        current_time = time.time()
        
        # Get recent performance data
        performance_metrics = self.get_treasury_performance_metrics()
        
        # Animate performance charts
        for metric_name, value in performance_metrics.items():
            animation_data = {
                "value": float(value),
                "animation_progress": (math.sin(current_time * 2) + 1) / 2,
                "color_intensity": min(float(value) / 1000000, 1.0),
                "timestamp": current_time
            }
            self.active_animations[f"performance_{metric_name}"] = animation_data
    
    async def add_treasury_funds(self, amount: Decimal, token: str, source: str, description: str = ""):
        """Add funds to treasury with animation"""
        try:
            # Trigger deposit animation
            await self._animate_fund_deposit(amount, token)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Record transaction
            cursor.execute("""
                INSERT INTO treasury_transactions 
                (transaction_type, amount, token_symbol, from_address, timestamp, description, category)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ("deposit", amount, token, source, datetime.now(), description, "incoming"))
            
            # Update balance
            cursor.execute("""
                INSERT OR REPLACE INTO treasury_balances 
                (token_symbol, balance, last_updated)
                VALUES (?, COALESCE((SELECT balance FROM treasury_balances WHERE token_symbol = ?), 0) + ?, ?)
            """, (token, token, amount, datetime.now()))
            
            conn.commit()
            conn.close()
            
            # Update cached balance
            self.treasury_balance += amount
            
            return True
            
        except Exception as e:
            print(f"Error adding treasury funds: {e}")
            return False
    
    async def _animate_fund_deposit(self, amount: Decimal, token: str):
        """Animate fund deposit with spectacular effects"""
        try:
            # Create deposit particle burst
            burst_particles = int(min(float(amount) / 100, 1000))
            
            for i in range(burst_particles):
                angle = (i / burst_particles) * 2 * math.pi
                velocity_x = math.cos(angle) * 2.0
                velocity_z = math.sin(angle) * 2.0
                
                deposit_particle = {
                    "position": [0, 5, 0],
                    "velocity": [velocity_x, -1.0, velocity_z],
                    "color": [0.2, 1.0, 0.2, 1.0],
                    "size": 0.08,
                    "life": 3.0,
                    "type": "deposit_burst"
                }
            
            # Play deposit sound effect (if audio system available)
            await self._play_treasury_sound("deposit")
            
            # Flash treasury glow
            self.treasury_config["glow_intensity"] = 1.5
            await asyncio.sleep(0.5)
            self.treasury_config["glow_intensity"] = 0.8
            
        except Exception as e:
            print(f"Deposit animation error: {e}")
    
    async def withdraw_treasury_funds(self, amount: Decimal, token: str, destination: str, description: str = ""):
        """Withdraw funds from treasury with animation"""
        try:
            # Check available balance
            available_balance = await self.get_token_balance(token)
            if available_balance < amount:
                raise ValueError("Insufficient treasury balance")
            
            # Trigger withdrawal animation
            await self._animate_fund_withdrawal(amount, token)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Record transaction
            cursor.execute("""
                INSERT INTO treasury_transactions 
                (transaction_type, amount, token_symbol, to_address, timestamp, description, category)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ("withdrawal", amount, token, destination, datetime.now(), description, "outgoing"))
            
            # Update balance
            cursor.execute("""
                UPDATE treasury_balances 
                SET balance = balance - ?, last_updated = ?
                WHERE token_symbol = ?
            """, (amount, datetime.now(), token))
            
            conn.commit()
            conn.close()
            
            # Update cached balance
            self.treasury_balance -= amount
            
            return True
            
        except Exception as e:
            print(f"Error withdrawing treasury funds: {e}")
            return False
    
    async def _animate_fund_withdrawal(self, amount: Decimal, token: str):
        """Animate fund withdrawal with visual effects"""
        try:
            # Create withdrawal particle stream
            stream_particles = int(min(float(amount) / 50, 500))
            
            for i in range(stream_particles):
                delay = i * 0.01
                await asyncio.sleep(delay)
                
                withdrawal_particle = {
                    "position": [0, 1, 0],
                    "velocity": [0, 2.0, 0],
                    "color": [1.0, 0.3, 0.3, 0.9],
                    "size": 0.06,
                    "life": 2.0,
                    "type": "withdrawal_stream"
                }
            
            # Dim treasury glow temporarily
            original_glow = self.treasury_config["glow_intensity"]
            self.treasury_config["glow_intensity"] = 0.3
            await asyncio.sleep(1.0)
            self.treasury_config["glow_intensity"] = original_glow
            
        except Exception as e:
            print(f"Withdrawal animation error: {e}")
    
    async def get_token_balance(self, token: str) -> Decimal:
        """Get current balance for a specific token"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT balance FROM treasury_balances WHERE token_symbol = ?", (token,))
        result = cursor.fetchone()
        
        conn.close()
        
        return Decimal(result[0]) if result else Decimal("0")
    
    def get_treasury_status(self) -> Dict[str, Any]:
        """Get comprehensive treasury status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get total balances
        cursor.execute("SELECT token_symbol, balance, staked_balance, price_usd FROM treasury_balances")
        balances = cursor.fetchall()
        
        # Get recent transactions
        cursor.execute("""
            SELECT transaction_type, amount, token_symbol, timestamp 
            FROM treasury_transactions 
            ORDER BY timestamp DESC 
            LIMIT 10
        """)
        recent_transactions = cursor.fetchall()
        
        # Calculate total USD value
        total_usd_value = Decimal("0")
        token_balances = {}
        
        for token, balance, staked, price in balances:
            token_balance = Decimal(balance) + Decimal(staked)
            token_balances[token] = {
                "balance": float(balance),
                "staked": float(staked),
                "total": float(token_balance),
                "usd_value": float(token_balance * Decimal(price))
            }
            total_usd_value += token_balance * Decimal(price)
        
        conn.close()
        
        return {
            "total_usd_value": float(total_usd_value),
            "token_balances": token_balances,
            "recent_transactions": [
                {
                    "type": tx[0],
                    "amount": float(tx[1]),
                    "token": tx[2],
                    "timestamp": tx[3]
                } for tx in recent_transactions
            ],
            "animation_status": {
                "active_animations": len(self.active_animations),
                "fps": self.treasury_config["animation_fps"],
                "particle_systems": self.treasury_config["particle_count"]
            }
        }
    
    def get_treasury_performance_metrics(self) -> Dict[str, Decimal]:
        """Get treasury performance metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate daily performance
        yesterday = datetime.now() - timedelta(days=1)
        cursor.execute("""
            SELECT SUM(CASE WHEN transaction_type = 'deposit' THEN amount ELSE -amount END) as net_flow
            FROM treasury_transactions 
            WHERE timestamp > ?
        """, (yesterday,))
        
        daily_flow = cursor.fetchone()[0] or Decimal("0")
        
        # Calculate weekly performance
        week_ago = datetime.now() - timedelta(days=7)
        cursor.execute("""
            SELECT SUM(CASE WHEN transaction_type = 'deposit' THEN amount ELSE -amount END) as net_flow
            FROM treasury_transactions 
            WHERE timestamp > ?
        """, (week_ago,))
        
        weekly_flow = cursor.fetchone()[0] or Decimal("0")
        
        conn.close()
        
        return {
            "daily_flow": daily_flow,
            "weekly_flow": weekly_flow,
            "total_balance": self.treasury_balance,
            "total_staked": self.total_staked
        }
    
    async def _play_treasury_sound(self, sound_type: str):
        """Play treasury sound effects (placeholder for audio integration)"""
        # This would integrate with an audio system
        print(f"🔊 Treasury sound: {sound_type}")
    
    def create_treasury_allocation(self, name: str, percentage: Decimal, allocation_type: str) -> bool:
        """Create a new treasury allocation"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            allocated_amount = self.treasury_balance * (percentage / Decimal("100"))
            
            cursor.execute("""
                INSERT INTO treasury_allocations 
                (allocation_name, percentage, allocated_amount, allocation_type, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (name, percentage, allocated_amount, allocation_type, datetime.now()))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error creating allocation: {e}")
            return False
    
    def get_treasury_allocations(self) -> List[Dict[str, Any]]:
        """Get all treasury allocations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT allocation_name, percentage, allocated_amount, allocation_type, created_at
            FROM treasury_allocations 
            WHERE is_active = 1
            ORDER BY created_at DESC
        """)
        
        allocations = []
        for row in cursor.fetchall():
            allocations.append({
                "name": row[0],
                "percentage": float(row[1]),
                "allocated_amount": float(row[2]),
                "type": row[3],
                "created_at": row[4]
            })
        
        conn.close()
        return allocations
    
    async def shutdown(self):
        """Shutdown treasury system gracefully"""
        self.running = False
        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join(timeout=1.0)
        print("🏛️ Treasury Animation System shut down")

# Demonstration function
async def demonstrate_treasury_system():
    """Demonstrate the treasury animation system"""
    print("\n🏛️ TREASURY ANIMATION SYSTEM DEMONSTRATION")
    print("="*60)
    
    treasury = TreasuryAnimationSystem()
    
    print("✅ Treasury system initialized with animations")
    
    # Demonstrate adding funds with animation
    print("\n💰 Adding funds to treasury...")
    await treasury.add_treasury_funds(
        Decimal("50000"), 
        "GUARD", 
        "0x1234567890abcdef", 
        "Initial treasury funding"
    )
    
    await treasury.add_treasury_funds(
        Decimal("25000"), 
        "USDC", 
        "0xabcdef1234567890", 
        "Stablecoin reserve"
    )
    
    # Show treasury status
    status = treasury.get_treasury_status()
    print(f"\n📊 Treasury Status:")
    print(f"   💵 Total USD Value: ${status['total_usd_value']:,.2f}")
    print(f"   🎮 Active Animations: {status['animation_status']['active_animations']}")
    print(f"   ⚡ Animation FPS: {status['animation_status']['fps']}")
    
    # Create allocations
    print("\n📊 Creating treasury allocations...")
    treasury.create_treasury_allocation("Development Fund", Decimal("30"), "development")
    treasury.create_treasury_allocation("Marketing Fund", Decimal("20"), "marketing")
    treasury.create_treasury_allocation("Security Reserve", Decimal("25"), "security")
    
    allocations = treasury.get_treasury_allocations()
    print(f"   ✅ Created {len(allocations)} allocations")
    
    # Demonstrate withdrawal with animation
    print("\n💸 Withdrawing funds from treasury...")
    await treasury.withdraw_treasury_funds(
        Decimal("5000"), 
        "GUARD", 
        "0xdestination123", 
        "Development expense"
    )
    
    # Final status
    final_status = treasury.get_treasury_status()
    print(f"\n🏆 Final Treasury Status:")
    print(f"   💵 Total USD Value: ${final_status['total_usd_value']:,.2f}")
    print(f"   📈 Recent Transactions: {len(final_status['recent_transactions'])}")
    
    await treasury.shutdown()
    print("✅ Treasury demonstration completed!")

if __name__ == "__main__":
    asyncio.run(demonstrate_treasury_system())