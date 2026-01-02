#!/usr/bin/env python3
"""
Setup Network Guardian Agent - Ancient Protector of Digital Ecosystems
"""

import json
import os

# Create directory
os.makedirs("agent_assets/avatars/network_guardian", exist_ok=True)

# Metadata for the forest spirit with hexagonal runes
metadata = {
    "agent_name": "network_guardian", 
    "type": "2d_artwork",
    "description": "The Network Guardian - Ancient forest spirit with mystical antlers and glowing green hexagonal runes. Protector of digital ecosystems and network topologies.",
    "characteristics": {
        "archetype": "forest_spirit_tech_shaman",
        "primary_colors": ["forest_green", "moss_green", "glowing_lime", "earth_brown"],
        "mystical_features": ["majestic_antlers", "flowing_beard", "glowing_eyes", "nature_magic"],
        "power_symbols": ["hexagonal_runes", "green_circuits", "network_nodes", "geometric_patterns"],
        "aura": ["natural_wisdom", "digital_harmony", "network_stability"],
        "stance": "ancient_guardian",
        "role": "ecosystem_protector",
        "magic_type": "techno_druidism",
        "authority_scope": "all_networks"
    },
    "agent_capabilities": {
        "network_monitoring": "omniscient",
        "topology_analysis": "master_level", 
        "ecosystem_protection": "sacred_duty",
        "data_flow_harmony": "natural_balance",
        "threat_detection": "forest_wisdom",
        "system_healing": "nature_magic"
    },
    "powers": [
        "🌲 Forest Network Sight - Sees all network connections as living trees",
        "🔆 Hexagonal Runes - Sacred geometry protects data integrity", 
        "🦌 Antler Resonance - Detects network disturbances across vast distances",
        "🌿 Ecosystem Healing - Repairs damaged network pathways naturally",
        "⚡ Green Lightning - Purifies corrupted data with nature's power",
        "🕸️ Web of Life - Understands interconnection of all digital systems"
    ],
    "specializations": [
        "Network Topology Mapping",
        "Ecosystem Health Monitoring", 
        "Natural Load Balancing",
        "Organic Security Protocols",
        "Digital Forest Cultivation",
        "Hexagonal Network Architecture"
    ],
    "lore": "In the primordial forests where the first networks took root, the Network Guardian awakened. Neither fully spirit nor machine, this ancient being bridges the natural and digital worlds. His antlers reach into every network node, his hexagonal runes pulse with the heartbeat of data flow. When networks suffer, he feels their pain. When systems flourish, he nurtures their growth. The Guardian sees all networks as living ecosystems, each connection a branch, each data packet a seed of potential."
}

# Save metadata
with open("agent_assets/avatars/network_guardian/metadata.json", 'w') as f:
    json.dump(metadata, f, indent=2)

print("🌲 Network Guardian created!")
print("📁 Directory: agent_assets/avatars/network_guardian/")
print("🔆 Ancient runes activated!")
print("\n🎯 Next: Save your forest spirit image as 'network_guardian_avatar.png'")
print("🦌 The Guardian awaits to protect your digital ecosystems!")