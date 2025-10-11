#!/usr/bin/env python3
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

# Try to import watchdog, install if missing
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("📦 Installing watchdog for file monitoring...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'watchdog'])
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

class GitAutoSync(FileSystemEventHandler):
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.last_commit_time = 0
        self.pending_changes = False
        self.commit_interval = 30  # seconds
        self.ignore_patterns = [
            '.git', '__pycache__', '.pyc', '.pyo', '.log', '.tmp', 
            '.temp', '.bak', '.backup', 'node_modules', '.env'
        ]
        
        # Start background commit thread
        self.commit_thread = threading.Thread(target=self._commit_loop, daemon=True)
        self.commit_thread.start()
        
        print(f"📁 Monitoring: {self.project_root}")
        print(f"⏱️ Commit interval: {self.commit_interval} seconds")
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        # Ignore certain files and patterns
        if any(pattern in event.src_path for pattern in self.ignore_patterns):
            return
        
        self.pending_changes = True
        relative_path = os.path.relpath(event.src_path, self.project_root)
        print(f"📝 File changed: {relative_path}")
    
    def on_created(self, event):
        if not event.is_directory:
            self.on_modified(event)
    
    def on_moved(self, event):
        if not event.is_directory:
            self.pending_changes = True
            print(f"📁 File moved: {event.dest_path}")
    
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
            
            # Create commit message with timestamp and file count
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            changed_files = result.stdout.strip().split('\n')
            file_count = len([f for f in changed_files if f.strip()])
            
            # Create detailed commit message
            commit_msg = f"🛡️ GuardianShield Auto-Sync: {file_count} file(s) updated - {timestamp}"
            
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
            
            # Push to GitHub (try main, then master for compatibility)
            try:
                subprocess.run(['git', 'push', 'origin', 'main'], check=True)
                branch = 'main'
            except subprocess.CalledProcessError:
                try:
                    subprocess.run(['git', 'push', 'origin', 'master'], check=True)
                    branch = 'master'
                except subprocess.CalledProcessError:
                    raise Exception("Failed to push to both main and master branches")
            
            print(f"🚀 {file_count} file(s) synced to GitHub ({branch}) at {timestamp}")
            
            # Show which files were synced
            for file_line in changed_files[:5]:  # Show first 5 files
                if file_line.strip():
                    status = file_line[:2]
                    filename = file_line[3:].strip()
                    status_icon = "📝" if "M" in status else "➕" if "A" in status else "❌" if "D" in status else "🔄"
                    print(f"   {status_icon} {filename}")
            
            if len(changed_files) > 5:
                print(f"   ... and {len(changed_files) - 5} more files")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Git sync error: {e}")
            # Try to pull and retry once
            try:
                print("🔄 Attempting to resolve conflicts...")
                subprocess.run(['git', 'pull', 'origin', 'main'], check=True)
                subprocess.run(['git', 'push', 'origin', 'main'], check=True)
                print("✅ Resolved conflict and synced successfully")
            except:
                print("⚠️ Manual intervention required - check git status")
                print("   Run: git status")
                print("   Then: git pull origin main")
        except Exception as e:
            print(f"❌ Unexpected error during sync: {e}")

def check_git_setup():
    """Check if Git is properly configured"""
    try:
        # Check if git is available
        subprocess.run(['git', '--version'], capture_output=True, check=True)
        
        # Check if we're in a git repository
        subprocess.run(['git', 'status'], capture_output=True, check=True)
        
        # Check if remote origin exists
        result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True)
        if 'origin' not in result.stdout:
            print("⚠️ No GitHub remote configured!")
            print("   Run: git remote add origin [YOUR_GITHUB_REPO_URL]")
            return False
        
        print("✅ Git configuration verified")
        return True
        
    except subprocess.CalledProcessError:
        print("❌ Git not properly configured")
        print("   Please run the setup script first: .\quick_setup.ps1")
        return False
    except FileNotFoundError:
        print("❌ Git not installed")
        print("   Please install Git from: https://git-scm.com/download/win")
        return False

def main():
    """Main auto-sync function"""
    project_root = Path(__file__).parent
    
    print("🛡️ GuardianShield Auto-Sync Starting...")
    print("=" * 50)
    
    # Check Git setup
    if not check_git_setup():
        print("\n❌ Setup required before starting auto-sync")
        print("Please follow the GITHUB_SYNC_SETUP.md guide")
        input("Press Enter to exit...")
        return
    
    print("🔄 Real-time GitHub synchronization active")
    print("Press Ctrl+C to stop\n")
    
    # Initialize file system watcher
    event_handler = GitAutoSync(project_root)
    observer = Observer()
    observer.schedule(event_handler, str(project_root), recursive=True)
    observer.start()
    
    try:
        # Do an initial sync of any pending changes
        event_handler._commit_and_push()
        
        # Keep running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping auto-sync...")
        observer.stop()
    
    observer.join()
    print("👋 Auto-sync stopped. All changes have been saved to GitHub!")

if __name__ == "__main__":
    main()