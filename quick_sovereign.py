#!/usr/bin/env python3
"""
Quick setup for Sovereign Validator
"""

import json
import os

# Create the directory
os.makedirs("agent_assets/avatars/sovereign_validator", exist_ok=True)

# Simple metadata
metadata = {
    "agent_name": "sovereign_validator",
    "type": "2d_artwork",
    "description": "The Sovereign Validator - Divine King of Consensus. A majestic bearded ruler wreathed in cosmic flames.",
    "role": "supreme_validator",
    "powers": ["Divine Consensus", "Royal Decree", "Flame Staff Authority", "Sacred Triangle", "Cosmic Wisdom"]
}

# Save it
with open("agent_assets/avatars/sovereign_validator/metadata.json", 'w') as f:
    json.dump(metadata, f, indent=2)

print("👑 Sovereign Validator created!")
print("📁 Directory: agent_assets/avatars/sovereign_validator/")
print("💾 Metadata saved!")
print("\n🎯 Next: Save your divine king image as 'sovereign_validator_avatar.png'")