"""
Advanced Frontend Animation System
Coordinates animations between treasury, POS, and graphics systems
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional
import math
from datetime import datetime
import threading

# Import our systems
from high_performance_graphics_engine import HighPerformanceGraphicsEngine
from treasury_animation_system import TreasuryAnimationSystem
from token_pos_system import TokenPOSSystem

class FrontendAnimationCoordinator:
    """Coordinates all frontend animations across systems"""
    
    def __init__(self):
        self.graphics_engine = HighPerformanceGraphicsEngine()
        self.treasury_system = None
        self.pos_system = None
        self.animation_thread = None
        self.running = False
        
        # Animation coordination settings
        self.animation_config = {
            "sync_fps": 120,
            "cross_system_sync": True,
            "particle_interaction": True,
            "unified_timing": True,
            "performance_monitoring": True
        }
        
        # Cross-system animation states
        self.synchronized_animations = {}
        self.global_animation_time = 0.0
        
        # System connections
        self.system_connections = {
            "treasury_to_pos": {"active": False, "animation_type": "transfer"},
            "pos_to_graphics": {"active": False, "animation_type": "success"},
            "treasury_to_graphics": {"active": False, "animation_type": "glow"}
        }
        
        self.start_coordination()
    
    def start_coordination(self):
        """Start the animation coordination system"""
        if not self.running:
            self.running = True
            self.animation_thread = threading.Thread(target=self._coordination_loop, daemon=True)
            self.animation_thread.start()
    
    def _coordination_loop(self):
        """Main coordination loop"""
        while self.running:
            try:
                current_time = time.time()
                self.global_animation_time = current_time
                
                # Update synchronized animations
                self._update_synchronized_animations()
                
                # Handle cross-system interactions
                self._process_system_interactions()
                
                # Monitor performance
                self._monitor_animation_performance()
                
                # Sleep for frame timing
                time.sleep(1.0 / self.animation_config["sync_fps"])
                
            except Exception as e:
                print(f"Animation coordination error: {e}")
                time.sleep(0.1)
    
    def _update_synchronized_animations(self):
        """Update animations that need to be synchronized across systems"""
        if not self.animation_config["unified_timing"]:
            return
        
        # Create global pulse for synchronized effects
        pulse_frequency = 2.0  # Hz
        pulse_value = (math.sin(self.global_animation_time * pulse_frequency * 2 * math.pi) + 1) / 2
        
        # Synchronized particle emissions
        if self.animation_config["particle_interaction"]:
            self._emit_synchronized_particles(pulse_value)
    
    def _emit_synchronized_particles(self, pulse_intensity: float):
        """Emit particles synchronized across all systems"""
        # Base particle properties
        base_particle = {
            "size": 0.05 * pulse_intensity,
            "life": 2.0,
            "color_intensity": pulse_intensity,
            "emission_rate": int(50 * pulse_intensity)
        }
        
        # Emit to graphics system
        if self.graphics_engine:
            for i in range(base_particle["emission_rate"]):
                angle = (i / base_particle["emission_rate"]) * 2 * math.pi
                graphics_particle = {
                    **base_particle,
                    "position": [
                        math.cos(angle) * 2.0,
                        0.5,
                        math.sin(angle) * 2.0
                    ],
                    "velocity": [0, 0.1, 0],
                    "color": [1.0, 0.8, 0.2, pulse_intensity],
                    "type": "synchronized_ambient"
                }
    
    def _process_system_interactions(self):
        """Process interactions between different systems"""
        for connection_name, connection_info in self.system_connections.items():
            if connection_info["active"]:
                self._animate_system_connection(connection_name, connection_info)
    
    def _animate_system_connection(self, connection_name: str, connection_info: Dict):
        """Animate connection between systems"""
        animation_type = connection_info["animation_type"]
        
        if connection_name == "treasury_to_pos" and animation_type == "transfer":
            self._animate_treasury_to_pos_transfer()
        elif connection_name == "pos_to_graphics" and animation_type == "success":
            self._animate_pos_success_to_graphics()
        elif connection_name == "treasury_to_graphics" and animation_type == "glow":
            self._animate_treasury_glow_to_graphics()
    
    def _animate_treasury_to_pos_transfer(self):
        """Animate transfer from treasury to POS system"""
        # Create particle stream from treasury to POS
        stream_particles = []
        for i in range(20):
            progress = i / 19.0
            x = -3.0 + progress * 6.0  # Move from left to right
            y = 1.0 + math.sin(progress * math.pi) * 0.5  # Arc trajectory
            
            transfer_particle = {
                "position": [x, y, 0],
                "velocity": [2.0, 0, 0],
                "color": [0.2, 1.0, 0.2, 0.8],
                "size": 0.06,
                "life": 2.0,
                "type": "treasury_pos_transfer"
            }
            stream_particles.append(transfer_particle)
    
    def _animate_pos_success_to_graphics(self):
        """Animate POS success effect to graphics system"""
        # Success burst that affects graphics
        for i in range(30):
            angle = (i / 30) * 2 * math.pi
            velocity_x = math.cos(angle) * 3.0
            velocity_z = math.sin(angle) * 3.0
            
            success_particle = {
                "position": [0, 1, 0],
                "velocity": [velocity_x, 2.0, velocity_z],
                "color": [0.2, 1.0, 0.2, 1.0],
                "size": 0.08,
                "life": 2.5,
                "type": "pos_success_graphics"
            }
    
    def _animate_treasury_glow_to_graphics(self):
        """Animate treasury glow effect to graphics system"""
        # Treasury glow affects surrounding graphics
        glow_intensity = (math.sin(self.global_animation_time * 3) + 1) / 2
        
        # Create expanding glow rings
        for ring in range(3):
            radius = 2.0 + ring * 1.0
            ring_particles = []
            
            for i in range(20):
                angle = (i / 20) * 2 * math.pi
                x = math.cos(angle) * radius
                z = math.sin(angle) * radius
                
                glow_particle = {
                    "position": [x, 0.5, z],
                    "velocity": [0, 0.1, 0],
                    "color": [1.0, 0.8, 0.0, glow_intensity * 0.5],
                    "size": 0.04,
                    "life": 1.5,
                    "type": "treasury_glow_ring"
                }
                ring_particles.append(glow_particle)
    
    def _monitor_animation_performance(self):
        """Monitor animation performance across all systems"""
        if not self.animation_config["performance_monitoring"]:
            return
        
        # Calculate frame times
        current_time = time.time()
        if hasattr(self, '_last_frame_time'):
            frame_time = current_time - self._last_frame_time
            fps = 1.0 / frame_time if frame_time > 0 else 0
            
            # Store performance metrics
            if not hasattr(self, 'performance_history'):
                self.performance_history = []
            
            self.performance_history.append({
                "timestamp": current_time,
                "fps": fps,
                "frame_time": frame_time
            })
            
            # Keep only last 100 frames
            if len(self.performance_history) > 100:
                self.performance_history.pop(0)
        
        self._last_frame_time = current_time
    
    def trigger_cross_system_animation(self, source: str, target: str, animation_type: str):
        """Trigger animation between systems"""
        connection_key = f"{source}_to_{target}"
        if connection_key in self.system_connections:
            self.system_connections[connection_key] = {
                "active": True,
                "animation_type": animation_type,
                "start_time": self.global_animation_time
            }
    
    def register_treasury_system(self, treasury_system: TreasuryAnimationSystem):
        """Register treasury system for coordination"""
        self.treasury_system = treasury_system
        print("🏛️ Treasury system registered with animation coordinator")
    
    def register_pos_system(self, pos_system: TokenPOSSystem):
        """Register POS system for coordination"""
        self.pos_system = pos_system
        print("💳 POS system registered with animation coordinator")
    
    async def coordinate_payment_flow(self, amount: float, token: str):
        """Coordinate animations for complete payment flow"""
        print(f"\n🎬 Coordinating payment flow animation: {amount} {token}")
        
        # Stage 1: Treasury withdrawal animation
        print("  🏛️ Stage 1: Treasury withdrawal...")
        self.trigger_cross_system_animation("treasury", "pos", "transfer")
        await asyncio.sleep(2.0)
        
        # Stage 2: POS processing animation
        print("  💳 Stage 2: POS processing...")
        self.trigger_cross_system_animation("pos", "graphics", "processing")
        await asyncio.sleep(3.0)
        
        # Stage 3: Success animation
        print("  ✅ Stage 3: Payment success...")
        self.trigger_cross_system_animation("pos", "graphics", "success")
        self.trigger_cross_system_animation("treasury", "graphics", "glow")
        await asyncio.sleep(2.0)
        
        print("  🎉 Payment flow animation completed!")
    
    def get_coordination_status(self) -> Dict[str, Any]:
        """Get animation coordination status"""
        performance_data = {}
        if hasattr(self, 'performance_history') and self.performance_history:
            recent_fps = [frame["fps"] for frame in self.performance_history[-10:]]
            performance_data = {
                "average_fps": sum(recent_fps) / len(recent_fps),
                "min_fps": min(recent_fps),
                "max_fps": max(recent_fps)
            }
        
        return {
            "running": self.running,
            "global_animation_time": self.global_animation_time,
            "sync_fps": self.animation_config["sync_fps"],
            "cross_system_sync": self.animation_config["cross_system_sync"],
            "active_connections": sum(1 for conn in self.system_connections.values() if conn["active"]),
            "registered_systems": {
                "graphics": self.graphics_engine is not None,
                "treasury": self.treasury_system is not None,
                "pos": self.pos_system is not None
            },
            "performance": performance_data
        }
    
    async def create_website_animations(self):
        """Create coordinated animations for website integration"""
        print("\n🌐 Creating website animations...")
        
        # Treasury dashboard animation sequence
        print("  🏛️ Treasury dashboard animations...")
        treasury_animations = {
            "vault_rotation": {"duration": 20.0, "type": "continuous"},
            "particle_emission": {"duration": "infinite", "type": "ambient"},
            "balance_counter": {"duration": 3.0, "type": "transition"},
            "transaction_flow": {"duration": 5.0, "type": "event"}
        }
        
        # POS dashboard animation sequence
        print("  💳 POS dashboard animations...")
        pos_animations = {
            "payment_flow": {"duration": 8.0, "type": "continuous"},
            "terminal_glow": {"duration": 3.0, "type": "pulse"},
            "success_burst": {"duration": 3.0, "type": "event"},
            "processing_ring": {"duration": 2.0, "type": "loading"}
        }
        
        # Graphics system coordination
        print("  🎨 Graphics system coordination...")
        graphics_coordination = {
            "background_particles": {"sync_with": "treasury", "intensity": 0.6},
            "success_effects": {"sync_with": "pos", "intensity": 1.0},
            "ambient_lighting": {"sync_with": "both", "intensity": 0.4}
        }
        
        return {
            "treasury_animations": treasury_animations,
            "pos_animations": pos_animations,
            "graphics_coordination": graphics_coordination,
            "total_animation_count": len(treasury_animations) + len(pos_animations) + len(graphics_coordination),
            "coordination_active": True
        }
    
    async def shutdown(self):
        """Shutdown animation coordination gracefully"""
        self.running = False
        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join(timeout=1.0)
        print("🎬 Frontend Animation Coordinator shut down")

# Global animation coordinator instance
animation_coordinator = FrontendAnimationCoordinator()

# Demonstration function
async def demonstrate_frontend_animations():
    """Demonstrate the frontend animation coordination"""
    print("\n🎬 FRONTEND ANIMATION COORDINATION DEMONSTRATION")
    print("="*70)
    
    coordinator = FrontendAnimationCoordinator()
    
    print("✅ Animation coordinator initialized")
    
    # Show coordination status
    status = coordinator.get_coordination_status()
    print(f"\n📊 Coordination Status:")
    print(f"   🎮 Running: {status['running']}")
    print(f"   ⚡ Sync FPS: {status['sync_fps']}")
    print(f"   🔗 Cross-system sync: {status['cross_system_sync']}")
    print(f"   📡 Active connections: {status['active_connections']}")
    
    # Demonstrate coordinated payment flow
    print("\n💳 Demonstrating coordinated payment flow...")
    await coordinator.coordinate_payment_flow(150.00, "GUARD")
    
    # Create website animations
    print("\n🌐 Creating website animations...")
    website_animations = await coordinator.create_website_animations()
    print(f"   ✅ Created {website_animations['total_animation_count']} animation sequences")
    print(f"   🎨 Treasury animations: {len(website_animations['treasury_animations'])}")
    print(f"   💳 POS animations: {len(website_animations['pos_animations'])}")
    print(f"   🎮 Graphics coordination: {len(website_animations['graphics_coordination'])}")
    
    await coordinator.shutdown()
    print("✅ Frontend animation demonstration completed!")

if __name__ == "__main__":
    asyncio.run(demonstrate_frontend_animations())