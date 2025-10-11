@echo off
title GuardianShield GitHub Sync Installer

echo.
echo ==================================================
echo   🛡️ GuardianShield Real-Time GitHub Sync Setup
echo ==================================================
echo.

echo This installer will:
echo ✓ Check for Git and Python
echo ✓ Initialize Git repository  
echo ✓ Create .gitignore file
echo ✓ Install Python dependencies
echo ✓ Set up auto-sync system
echo.

pause

REM Check Git
echo Checking Git installation...
git --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Git not found
    echo.
    echo Please install Git first:
    echo 1. Go to: https://git-scm.com/download/win
    echo 2. Download and install with default settings
    echo 3. Restart VS Code
    echo 4. Run this installer again
    echo.
    pause
    exit /b 1
) else (
    echo ✅ Git is installed
)

REM Check Python
echo Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python not found
    echo.
    echo Please install Python first:
    echo 1. Go to: https://www.python.org/downloads/
    echo 2. Download and install
    echo 3. ⚠️ IMPORTANT: Check "Add Python to PATH" 
    echo 4. Restart VS Code
    echo 5. Run this installer again
    echo.
    pause
    exit /b 1
) else (
    echo ✅ Python is installed
)

echo.
echo 🔧 Setting up Git repository...

REM Initialize Git if needed
if not exist .git (
    git init
    git config user.name "GuardianShield Agent"
    git config user.email "agent@guardianshield.ai"
    echo ✅ Git repository initialized
) else (
    echo ✅ Git repository already exists
)

REM Create .gitignore
echo Creating .gitignore...
(
echo # Python
echo __pycache__/
echo *.pyc
echo *.pyo
echo *.log
echo .env
echo venv/
echo env/
echo.
echo # IDE
echo .vscode/settings.json
echo .idea/
echo.
echo # OS  
echo .DS_Store
echo Thumbs.db
echo.
echo # Temporary
echo *.tmp
echo *.temp
echo.
echo # Logs
echo agent_*.jsonl
) > .gitignore
echo ✅ .gitignore created

REM Install Python dependencies
echo.
echo 📦 Installing Python dependencies...
python -m pip install --upgrade pip
python -m pip install watchdog fastapi uvicorn websockets
echo ✅ Dependencies installed

echo.
echo 🎯 NEXT STEPS:
echo =============
echo.
echo 1. Create a GitHub repository named "guardianshield-agents"
echo.
echo 2. Copy the repository URL (e.g., https://github.com/username/guardianshield-agents.git)
echo.
echo 3. Run these commands:
echo    git remote add origin [YOUR_REPO_URL]
echo    git add .
echo    git commit -m "Initial GuardianShield commit with full dashboard"
echo    git branch -M main  
echo    git push -u origin main
echo.
echo 4. Start real-time sync:
echo    python auto_sync_github.py
echo.
echo ✅ Setup complete! Follow the steps above to connect to GitHub.
echo.

pause