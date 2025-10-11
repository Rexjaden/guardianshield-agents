# 🛡️ GuardianShield Real-Time GitHub Sync Setup Guide

## Quick Installation Steps

### 1. Install Git
- Download: https://git-scm.com/download/win
- Install with default settings
- Restart VS Code after installation

### 2. Install Python  
- Download: https://www.python.org/downloads/
- **IMPORTANT**: Check "Add Python to PATH" during installation
- Restart VS Code after installation

### 3. Run Setup
After installing both Git and Python, run:
```powershell
.\quick_setup.ps1
```

### 4. Configure GitHub Repository
1. Create a new repository on GitHub named `guardianshield-agents`
2. Copy the repository URL (e.g., `https://github.com/yourusername/guardianshield-agents.git`)
3. Run these commands:
```bash
git remote add origin [YOUR_GITHUB_REPO_URL]
git add .
git commit -m "Initial GuardianShield commit with full frontend"
git branch -M main
git push -u origin main
```

### 5. Start Real-Time Sync
```bash
python auto_sync_github.py
```

## What the Auto-Sync Does

- **File Monitoring**: Watches all files in the project for changes
- **Automatic Commits**: Creates commits every 30 seconds when changes are detected
- **Real-Time Push**: Immediately pushes all commits to GitHub
- **Smart Filtering**: Ignores temporary files, logs, and build artifacts
- **Timestamp Messages**: Each commit includes a timestamp for tracking

## Manual Sync Commands

If you prefer manual control:
```bash
# Add all changes
git add .

# Commit with message
git commit -m "Your commit message"

# Push to GitHub
git push origin main
```

## Features Included in This Sync

✅ Complete frontend dashboard  
✅ Real-time WebSocket integration  
✅ Agent management system  
✅ Threat monitoring interface  
✅ Analytics and visualization  
✅ Enhanced API server  
✅ All Python backend agents  
✅ Smart contracts  
✅ Configuration files  

## Troubleshooting

**Git not found**: Install Git and restart terminal  
**Python not found**: Install Python with PATH option checked  
**Permission denied**: Ensure GitHub repository exists and you have access  
**Sync conflicts**: Use `git pull` first, then push again  

---
*Once setup is complete, every change you make will automatically appear on GitHub within 30 seconds!*