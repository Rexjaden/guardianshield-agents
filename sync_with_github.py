#!/usr/bin/env python3
"""
GuardianShield Repository Sync with Existing GitHub
Connects local development to existing GitHub repository
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import json

class GitHubRepoSync:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backup_dir = self.project_root / "local_backup"
        
    def check_git_installation(self):
        """Check if Git is installed"""
        try:
            result = subprocess.run(['git', '--version'], 
                                  capture_output=True, text=True, check=True)
            print(f"✅ Git is installed: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Git is not installed")
            return False
    
    def install_git_windows(self):
        """Attempt to install Git on Windows"""
        print("🔧 Installing Git for Windows...")
        
        try:
            # Try using winget
            result = subprocess.run([
                'winget', 'install', '--id', 'Git.Git', '-e', '--source', 'winget'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Git installed successfully via winget")
                print("🔄 Please restart VS Code for PATH updates to take effect")
                return True
            else:
                print("⚠️ Winget installation failed")
        except FileNotFoundError:
            print("⚠️ Winget not available")
        
        # Provide manual installation instructions
        print("\n" + "="*60)
        print("MANUAL GIT INSTALLATION REQUIRED")
        print("="*60)
        print("1. Download Git from: https://git-scm.com/download/win")
        print("2. Run the installer with default settings")
        print("3. Restart VS Code after installation")
        print("4. Run this script again")
        print("="*60)
        return False
    
    def backup_local_files(self):
        """Backup current local files before sync"""
        print("📦 Backing up current local files...")
        
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        
        self.backup_dir.mkdir()
        
        # Copy all files except .git and __pycache__
        for item in self.project_root.iterdir():
            if item.name not in ['.git', '__pycache__', 'local_backup']:
                if item.is_file():
                    shutil.copy2(item, self.backup_dir)
                elif item.is_dir():
                    shutil.copytree(item, self.backup_dir / item.name)
        
        print(f"✅ Local files backed up to: {self.backup_dir}")
    
    def clone_existing_repo(self, repo_url):
        """Clone the existing GitHub repository"""
        print(f"📥 Cloning existing repository: {repo_url}")
        
        # Create a temporary directory for cloning
        temp_clone = self.project_root / "temp_clone"
        
        try:
            # Clone the repository
            subprocess.run([
                'git', 'clone', repo_url, str(temp_clone)
            ], check=True)
            
            # Move .git directory to current location
            if (temp_clone / '.git').exists():
                if (self.project_root / '.git').exists():
                    shutil.rmtree(self.project_root / '.git')
                
                shutil.move(str(temp_clone / '.git'), str(self.project_root / '.git'))
                print("✅ Git repository connected")
            
            # Clean up temp directory
            shutil.rmtree(temp_clone)
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to clone repository: {e}")
            if temp_clone.exists():
                shutil.rmtree(temp_clone)
            return False
    
    def merge_local_changes(self):
        """Merge local changes with the repository"""
        print("🔄 Merging local changes with repository...")
        
        os.chdir(self.project_root)
        
        try:
            # Check status
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True)
            
            if result.stdout.strip():
                # There are changes to commit
                subprocess.run(['git', 'add', '.'], check=True)
                
                # Create commit with timestamp
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                commit_msg = f"Local development sync - {timestamp}"
                
                subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
                print("✅ Local changes committed")
            else:
                print("✅ No local changes to commit")
            
            # Try to pull latest changes
            try:
                subprocess.run(['git', 'pull', 'origin', 'main'], check=True)
                print("✅ Pulled latest changes from GitHub")
            except subprocess.CalledProcessError:
                try:
                    subprocess.run(['git', 'pull', 'origin', 'master'], check=True)
                    print("✅ Pulled latest changes from GitHub (master branch)")
                except subprocess.CalledProcessError:
                    print("⚠️ Could not pull changes - will push local changes")
            
            # Push changes
            try:
                subprocess.run(['git', 'push', 'origin', 'main'], check=True)
                print("✅ Pushed local changes to GitHub")
            except subprocess.CalledProcessError:
                try:
                    subprocess.run(['git', 'push', 'origin', 'master'], check=True)
                    print("✅ Pushed local changes to GitHub (master branch)")
                except subprocess.CalledProcessError:
                    print("❌ Failed to push changes - manual intervention may be required")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error during merge: {e}")
            return False
    
    def setup_auto_sync(self):
        """Install dependencies for auto-sync"""
        print("📦 Setting up auto-sync dependencies...")
        
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'watchdog'], check=True)
            print("✅ Auto-sync dependencies installed")
        except subprocess.CalledProcessError:
            print("⚠️ Failed to install some dependencies")
    
    def get_repo_url_from_user(self):
        """Get repository URL from user"""
        print("\n" + "="*60)
        print("GITHUB REPOSITORY CONNECTION")
        print("="*60)
        print("Please provide your existing GitHub repository URL.")
        print("Format examples:")
        print("  https://github.com/username/guardianshield-agents.git")
        print("  git@github.com:username/guardianshield-agents.git")
        print("")
        
        while True:
            repo_url = input("Enter your repository URL: ").strip()
            if repo_url and ('github.com' in repo_url and 'guardianshield-agents' in repo_url):
                return repo_url
            else:
                print("❌ Please enter a valid GitHub URL for guardianshield-agents")
    
    def run(self):
        """Main sync process"""
        print("🛡️ GuardianShield Repository Sync")
        print("=" * 50)
        print("This will connect your local development to your existing GitHub repository.")
        print("")
        
        # Check Git installation
        if not self.check_git_installation():
            if sys.platform == "win32":
                if not self.install_git_windows():
                    print("\n❌ Git installation required. Please install Git and run this script again.")
                    return False
            else:
                print("Please install Git for your operating system")
                return False
        
        # Get repository URL
        repo_url = self.get_repo_url_from_user()
        
        # Backup local files
        self.backup_local_files()
        
        # Clone existing repository
        if not self.clone_existing_repo(repo_url):
            print("❌ Failed to connect to repository")
            return False
        
        # Merge local changes
        if not self.merge_local_changes():
            print("❌ Failed to merge local changes")
            return False
        
        # Setup auto-sync
        self.setup_auto_sync()
        
        print("\n" + "✅" * 20)
        print("🎉 SYNC SETUP COMPLETE!")
        print("✅" * 20)
        print()
        print("Your local GuardianShield development is now connected to GitHub!")
        print()
        print("📂 Your original files are backed up in: local_backup/")
        print("🔄 Repository is now synced with your other computer")
        print("🚀 Start real-time sync with: python auto_sync_github.py")
        print()
        print("All future changes will be automatically synced to GitHub!")
        
        return True

if __name__ == "__main__":
    sync = GitHubRepoSync()
    sync.run()