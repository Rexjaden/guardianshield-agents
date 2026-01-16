#!/usr/bin/env python3
"""
Shield Token Image Setup Helper
Helps locate and move your shield token image to the correct location
"""
import os
import shutil
from pathlib import Path

def find_shield_token():
    """Find shield token image files"""
    current_dir = Path.cwd()
    shield_files = []
    
    # Search patterns
    patterns = [
        "shield-token.png",
        "shield-token.jpg", 
        "shield-token.jpeg",
        "ShieldToken.png",
        "shield_token.png"
    ]
    
    print("🔍 Searching for Shield Token image...")
    
    # Check current directory
    for pattern in patterns:
        files = list(current_dir.glob(pattern))
        if files:
            shield_files.extend(files)
    
    # Check subdirectories  
    for pattern in patterns:
        files = list(current_dir.glob(f"**/{pattern}"))
        if files:
            shield_files.extend(files)
    
    return shield_files

def move_shield_token(source_file):
    """Move shield token to correct location"""
    target_dir = Path("assets/images")
    target_dir.mkdir(parents=True, exist_ok=True)
    
    target_file = target_dir / "shield-token.png"
    
    try:
        shutil.copy2(source_file, target_file)
        print(f"✅ Shield Token copied successfully!")
        print(f"   From: {source_file}")
        print(f"   To:   {target_file}")
        return True
    except Exception as e:
        print(f"❌ Error copying file: {e}")
        return False

def main():
    print("🛡️ Shield Token Image Setup")
    print("=" * 30)
    
    # Find shield token files
    shield_files = find_shield_token()
    
    if not shield_files:
        print("❌ No shield token image found!")
        print("\n📋 To add your shield token:")
        print("1. Save your shield token image as 'shield-token.png'")
        print("2. Place it in this directory, or")
        print("3. Drag it into VS Code's assets/images/ folder")
        return
    
    print(f"✅ Found {len(shield_files)} shield token file(s):")
    for i, file in enumerate(shield_files, 1):
        print(f"   {i}. {file}")
    
    # Use the first file found
    source_file = shield_files[0]
    if move_shield_token(source_file):
        print("\n🚀 Ready to test!")
        print("   Open: http://localhost:5500/shield-token-test.html")
        print("   Your shield token should now load automatically!")

if __name__ == "__main__":
    main()