@echo off
echo 🛡️ GuardianShield Git Setup for Windows
echo ========================================

REM Check if Git is installed
git --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Git not found. Installing Git...
    
    REM Try winget first
    winget install --id Git.Git -e --source winget
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ Winget installation failed.
        echo 📥 Please download Git manually from: https://git-scm.com/download/win
        echo 🔄 Then restart this script after installation.
        pause
        exit /b 1
    )
    
    echo ✅ Git installed! Please restart your terminal/VS Code.
    pause
    exit /b 0
)

echo ✅ Git is already installed

REM Initialize repository if needed
if not exist .git (
    echo 📁 Initializing Git repository...
    git init
    git config user.name "GuardianShield Agent"
    git config user.email "agent@guardianshield.ai"
)

echo 🔄 Running Python setup script...
python setup_git_sync.py

echo ✅ Setup complete!
echo 🚀 To start real-time GitHub sync, run: python auto_sync_github.py
pause