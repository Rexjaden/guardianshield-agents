#!/usr/bin/env python3
"""
GuardianShield Git Sync Setup
Automated Git installation and real-time GitHub synchronization setup
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path

class GitSyncSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.git_config = {
            "auto_commit": True,
            "auto_push": True,
            "commit_interval": 30,  # seconds
            "branch": "main"
        }
    
    def check_git_installation(self):
        """Check if Git is installed"""
        try:
            result = subprocess.run(['git', '--version'], 
                                  capture_output=True, text=True, check=True)
            print(f"✓ Git is installed: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("✗ Git is not installed or not in PATH")
            return False
    
    def install_git_windows(self):
        """Install Git on Windows using winget or provide instructions"""
        print("Installing Git for Windows...")
        
        try:
            # Try using winget (Windows Package Manager)
            result = subprocess.run([
                'winget', 'install', '--id', 'Git.Git', '-e', '--source', 'winget'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✓ Git installed successfully via winget")
                print("Please restart your terminal or VS Code for Git to be available in PATH")
                return True
            else:
                print("Winget installation failed, providing manual instructions...")
        except FileNotFoundError:
            print("Winget not available, providing manual instructions...")
        
        # Provide manual installation instructions
        print("\n" + "="*60)
        print("MANUAL GIT INSTALLATION REQUIRED")
        print("="*60)
        print("1. Download Git from: https://git-scm.com/download/win")
        print("2. Run the installer with default settings")
        print("3. Restart VS Code/Terminal after installation")
        print("4. Run this script again")
        print("="*60)
        return False
    
    def setup_git_repository(self):
        """Initialize or verify Git repository"""
        os.chdir(self.project_root)
        
        if not (self.project_root / '.git').exists():
            print("Initializing Git repository...")
            subprocess.run(['git', 'init'], check=True)
            
            # Set up initial configuration
            subprocess.run(['git', 'config', 'user.name', 'GuardianShield Agent'], check=True)
            subprocess.run(['git', 'config', 'user.email', 'agent@guardianshield.ai'], check=True)
            
            print("✓ Git repository initialized")
        else:
            print("✓ Git repository already exists")
    
    def create_gitignore(self):
        """Create comprehensive .gitignore file"""
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environment
venv/
env/
ENV/
.venv/
.env

# IDE
.vscode/settings.json
.idea/
*.swp
*.swo
*~

# Logs
*.log
logs/
agent_*.jsonl

# OS
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.temp
temp/

# API Keys & Secrets
.env.local
secrets.json
config/secrets/

# Node modules (if any frontend tools)
node_modules/

# Database
*.db
*.sqlite
*.sqlite3

# Backup files
*.bak
*.backup
"""
        
        gitignore_path = self.project_root / '.gitignore'
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)
        
        print("✓ .gitignore file created")
    
    def create_auto_sync_script(self):
        """Create automated sync script"""
        sync_script = '''#!/usr/bin/env python3
"""
GuardianShield Auto-Sync to GitHub
Real-time synchronization of all changes
"""

import os
import sys
import subprocess
import time
import json
from datetime import datetime
from pathlib import Path
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class GitAutoSync(FileSystemEventHandler):
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.last_commit_time = 0
        self.pending_changes = False
        self.commit_interval = 30  # seconds
        
        # Start background commit thread
        self.commit_thread = threading.Thread(target=self._commit_loop, daemon=True)
        self.commit_thread.start()
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        # Ignore certain files
        ignore_patterns = ['.git', '__pycache__', '.log', '.tmp']
        if any(pattern in event.src_path for pattern in ignore_patterns):
            return
        
        self.pending_changes = True
        print(f"📝 File changed: {event.src_path}")
    
    def _commit_loop(self):
        """Background thread for automated commits"""
        while True:
            time.sleep(self.commit_interval)
            
            if self.pending_changes:
                self._commit_and_push()
                self.pending_changes = False
    
    def _commit_and_push(self):
        """Commit and push changes to GitHub"""
        try:
            os.chdir(self.project_root)
            
            # Check if there are changes to commit
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True)
            
            if not result.stdout.strip():
                return  # No changes to commit
            
            # Add all changes
            subprocess.run(['git', 'add', '.'], check=True)
            
            # Create commit message with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_msg = f"Auto-sync: GuardianShield updates - {timestamp}"
            
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
            
            # Push to GitHub
            subprocess.run(['git', 'push', 'origin', 'main'], check=True)
            
            print(f"🚀 Changes pushed to GitHub at {timestamp}")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Git sync error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error during sync: {e}")

def main():
    """Main auto-sync function"""
    project_root = Path(__file__).parent
    
    print("🛡️ GuardianShield Auto-Sync Starting...")
    print(f"📁 Monitoring: {project_root}")
    print("🔄 Real-time GitHub synchronization active")
    print("Press Ctrl+C to stop")
    
    # Initialize file system watcher
    event_handler = GitAutoSync(project_root)
    observer = Observer()
    observer.schedule(event_handler, str(project_root), recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\\n🛑 Stopping auto-sync...")
        observer.stop()
    
    observer.join()

if __name__ == "__main__":
    main()
'''
        
        sync_script_path = self.project_root / 'auto_sync_github.py'
        with open(sync_script_path, 'w') as f:
            f.write(sync_script)
        
        print("✓ Auto-sync script created")
    
    def setup_github_remote(self):
        """Setup GitHub remote (requires manual input)"""
        print("\n" + "="*60)
        print("GITHUB REPOSITORY SETUP")
        print("="*60)
        print("To enable real-time GitHub sync, you need to:")
        print("1. Create a repository on GitHub named 'guardianshield-agents'")
        print("2. Get the repository URL (e.g., https://github.com/username/guardianshield-agents.git)")
        print("3. Run the following commands:")
        print("")
        print("   git remote add origin <YOUR_GITHUB_REPO_URL>")
        print("   git branch -M main")
        print("   git push -u origin main")
        print("")
        print("4. Then run: python auto_sync_github.py")
        print("="*60)
    
    def install_dependencies(self):
        """Install required Python packages for file watching"""
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'watchdog'], check=True)
            print("✓ Watchdog package installed for file monitoring")
        except subprocess.CalledProcessError:
            print("❌ Failed to install watchdog package")
    
    def run(self):
        """Main setup process"""
        print("🛡️ GuardianShield Git Sync Setup")
        print("="*50)
        
        # Check Git installation
        if not self.check_git_installation():
            if sys.platform == "win32":
                if not self.install_git_windows():
                    return False
            else:
                print("Please install Git for your operating system")
                return False
        
        # Setup Git repository
        try:
            self.setup_git_repository()
            self.create_gitignore()
            self.create_auto_sync_script()
            self.install_dependencies()
            self.setup_github_remote()
            
            print("\n✅ Git sync setup completed!")
            print("🔄 Run 'python auto_sync_github.py' to start real-time sync")
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False
        
        return True

if __name__ == "__main__":
    setup = GitSyncSetup()
    setup.run()