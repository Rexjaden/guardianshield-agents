#!/usr/bin/env python3
"""
Quick AI Avatar Addition Template
Use this to quickly add your next AI avatars
"""

import asyncio
import json
from datetime import datetime
from integrate_ai_avatars import AIAvatarIntegrator

async def add_new_avatar():
    """Template for adding a new avatar - customize the avatar_data below"""
    
    integrator = AIAvatarIntegrator()
    
    # 🎨 CUSTOMIZE THIS SECTION FOR EACH NEW AVATAR
    avatar_data = {
        "agent_name": "network_sentinel",  # Change this
        "display_name": "Network Sentinel",  # Change this
        "description": "Advanced AI guardian specializing in network security and threat prevention.",  # Customize
        "avatar_type": "cybernetic_guardian",  # Options: "ethereal_guardian", "cybernetic_guardian", "mystical_sentinel", "digital_warrior"
        "primary_colors": ["#FF6B35", "#F7931E", "#FFB84D"],  # Customize colors based on your image
        "special_effects": ["cyber_glow", "data_streams", "holographic", "shield_energy"],  # Customize effects
        "symbolic_elements": ["network_nodes", "data_patterns", "shield_matrix", "cyber_armor"],  # Customize symbols
        "role": "Network Security Specialist & Threat Hunter",  # Customize role
        "power_level": "elite",  # Options: "novice", "advanced", "elite", "legendary", "maximum"
        "lore": "Forged in the digital realm, this sentinel patrols the network boundaries...",  # Write custom lore
        "capabilities": {
            "network_monitoring": "real_time",
            "threat_analysis": "advanced_ai",
            "response_speed": "microseconds",
            "data_processing": "quantum_level",
            "pattern_recognition": "neural_network",
            "intrusion_detection": "omnipresent"
        },
        "visual_characteristics": {
            "stance": "alert_monitoring",
            "aura": "cyber_energy_field",
            "expression": "focused_vigilance",
            "build": "sleek_digital_form",
            "clothing": "cyber_armor_suit",
            "accessories": ["hud_visor", "data_gauntlets", "network_crown"]
        },
        "created_at": datetime.now().isoformat(),
        "avatar_id": "network_sentinel"  # Should match agent_name
    }
    
    # Add the avatar
    avatar = await integrator.add_avatar_from_description(avatar_data)
    await integrator.generate_master_showcase()
    
    print(f"✅ Successfully integrated: {avatar.display_name}")
    print(f"🎨 Showcase: ai_avatars/{avatar.avatar_id}/showcase.html")
    print(f"🔗 Integration: ai_avatars/{avatar.avatar_id}/integration.js")
    print(f"💫 Animations: ai_avatars/{avatar.avatar_id}/animations.css")
    
    # Show all integrated avatars
    print(f"\n📊 Total Avatars Integrated: {len(integrator.avatars)}")
    
    return avatar

# Quick avatar presets for common types
AVATAR_PRESETS = {
    "cybernetic_guardian": {
        "avatar_type": "cybernetic_guardian",
        "primary_colors": ["#00FF41", "#39FF14", "#32CD32"],
        "special_effects": ["cyber_glow", "data_streams", "holographic", "matrix_code"],
        "power_level": "elite"
    },
    
    "mystical_sentinel": {
        "avatar_type": "mystical_sentinel", 
        "primary_colors": ["#9932CC", "#8A2BE2", "#4B0082"],
        "special_effects": ["mystical_aura", "arcane_energy", "dimensional_rifts", "spell_casting"],
        "power_level": "legendary"
    },
    
    "digital_warrior": {
        "avatar_type": "digital_warrior",
        "primary_colors": ["#FF4500", "#DC143C", "#B22222"],
        "special_effects": ["combat_ready", "weapon_energy", "battle_aura", "tactical_display"],
        "power_level": "maximum"
    },
    
    "quantum_oracle": {
        "avatar_type": "quantum_oracle",
        "primary_colors": ["#00CED1", "#20B2AA", "#48D1CC"],
        "special_effects": ["quantum_field", "probability_waves", "time_distortion", "cosmic_awareness"],
        "power_level": "transcendent"
    }
}

def show_avatar_template_guide():
    """Show guidance for customizing avatars"""
    
    print("🎨 AI Avatar Integration Guide")
    print("=" * 50)
    print("\n📋 Steps to add your next avatar:")
    print("1. Save your avatar image to the project folder")
    print("2. Update avatar_data in add_new_avatar() function")
    print("3. Choose appropriate colors, effects, and characteristics")
    print("4. Run: python quick_avatar_template.py")
    print("\n🎭 Available Avatar Types:")
    for preset, data in AVATAR_PRESETS.items():
        print(f"   • {preset}: {data['avatar_type']} (Power: {data['power_level']})")
    
    print(f"\n🌈 Color Suggestions:")
    print("   • Blue/Cyan: ['#00D4FF', '#0099CC', '#66E5FF'] - Tech/Electric")  
    print("   • Green/Matrix: ['#00FF41', '#39FF14', '#32CD32'] - Cyber/Digital")
    print("   • Purple/Mystic: ['#9932CC', '#8A2BE2', '#4B0082'] - Magic/Mystical") 
    print("   • Red/Combat: ['#FF4500', '#DC143C', '#B22222'] - Battle/Warrior")
    print("   • Gold/Divine: ['#FFD700', '#FFA500', '#FF8C00'] - Divine/Sacred")

if __name__ == "__main__":
    print("🚀 Quick AI Avatar Integration")
    print("Choose an option:")
    print("1. Add new avatar (customize the template)")
    print("2. Show integration guide")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        asyncio.run(add_new_avatar())
    elif choice == "2":
        show_avatar_template_guide()
    else:
        print("Invalid choice. Run again and choose 1 or 2.")