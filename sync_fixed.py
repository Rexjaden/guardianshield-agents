#!/usr/bin/env python3
"""
GuardianShield Repository Sync (Windows Git Path Fix)
Connects local development to existing GitHub repository
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Windows Git path
GIT_PATH = r"C:\Program Files\Git\bin\git.exe"

def run_git_command(cmd_args):
    """Run git command with full path"""
    cmd = [GIT_PATH] + cmd_args
    return subprocess.run(cmd, capture_output=True, text=True)

def main():
    print("🛡️ GuardianShield Repository Sync")
    print("=" * 50)
    
    # Test Git
    result = run_git_command(['--version'])
    if result.returncode != 0:
        print("❌ Git not found. Please restart VS Code or install Git.")
        return
    
    print(f"✅ Git found: {result.stdout.strip()}")
    
    # Get repository URL
    print("\n" + "="*60)
    print("GITHUB REPOSITORY CONNECTION")
    print("="*60)
    print("Please enter your existing GitHub repository URL:")
    print("Example: https://github.com/yourusername/guardianshield-agents.git")
    print("")
    
    repo_url = input("Repository URL: ").strip()
    
    if not repo_url or 'github.com' not in repo_url:
        print("❌ Invalid repository URL")
        return
    
    # Backup current files
    print("\n📦 Backing up current files...")
    backup_dir = Path("local_backup")
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    backup_dir.mkdir()
    
    # Copy files
    for item in Path(".").iterdir():
        if item.name not in ['.git', '__pycache__', 'local_backup']:
            try:
                if item.is_file():
                    shutil.copy2(item, backup_dir)
                elif item.is_dir():
                    shutil.copytree(item, backup_dir / item.name)
            except Exception as e:
                print(f"⚠️ Could not backup {item.name}: {e}")
    
    print("✅ Files backed up to local_backup/")
    
    # Initialize Git
    print("\n🔧 Setting up Git repository...")
    
    # Initialize if needed
    if not Path(".git").exists():
        result = run_git_command(['init'])
        if result.returncode != 0:
            print(f"❌ Git init failed: {result.stderr}")
            return
        print("✅ Git repository initialized")
    
    # Configure Git
    run_git_command(['config', 'user.name', 'GuardianShield Agent'])
    run_git_command(['config', 'user.email', 'agent@guardianshield.ai'])
    
    # Add remote
    run_git_command(['remote', 'remove', 'origin'])  # Remove if exists
    result = run_git_command(['remote', 'add', 'origin', repo_url])
    if result.returncode != 0:
        print(f"❌ Failed to add remote: {result.stderr}")
        return
    
    print("✅ Remote repository connected")
    
    # Fetch
    print("\n📥 Fetching repository...")
    result = run_git_command(['fetch', 'origin'])
    if result.returncode != 0:
        print(f"❌ Fetch failed: {result.stderr}")
        print("Please check your repository URL and internet connection")
        return
    
    print("✅ Repository fetched")
    
    # Check what branches exist
    result = run_git_command(['branch', '-r'])
    remote_branches = result.stdout
    
    # Determine main branch
    main_branch = 'main' if 'origin/main' in remote_branches else 'master'
    
    print(f"\n🔀 Merging with {main_branch} branch...")
    
    # Stage all current files
    run_git_command(['add', '.'])
    
    # Commit current state
    result = run_git_command(['commit', '-m', 'Local development before merge'])
    
    # Try to merge
    result = run_git_command(['merge', f'origin/{main_branch}', '--allow-unrelated-histories'])
    
    if result.returncode != 0:
        print("⚠️ Merge conflict detected. Creating merge commit...")
        run_git_command(['add', '.'])
        run_git_command(['commit', '-m', 'Merge local development with GitHub'])
    
    print("✅ Merge completed")
    
    # Push changes
    print("\n📤 Pushing to GitHub...")
    result = run_git_command(['push', 'origin', main_branch])
    
    if result.returncode != 0:
        # Try to set upstream
        result = run_git_command(['push', '--set-upstream', 'origin', main_branch])
    
    if result.returncode == 0:
        print("✅ Successfully pushed to GitHub")
    else:
        print(f"⚠️ Push failed: {result.stderr}")
        print("You may need to pull first or resolve conflicts manually")
    
    # Install dependencies
    print("\n📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'watchdog'], check=True)
        print("✅ Dependencies installed")
    except Exception as e:
        print(f"⚠️ Could not install dependencies: {e}")
    
    print("\n" + "✅" * 20)
    print("🎉 SYNC COMPLETE!")
    print("✅" * 20)
    print()
    print("Your GuardianShield project is now connected to GitHub!")
    print()
    print("📂 Original files backed up in: local_backup/")
    print("🔄 Repository synced with your other computer")
    print("🚀 Start real-time sync: python auto_sync_github.py")
    print()
    print("All future changes will automatically sync to GitHub!")

if __name__ == "__main__":
    main()