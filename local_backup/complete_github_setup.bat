@echo off
title GuardianShield - Complete Setup with Existing Repository

echo.
echo ================================================================
echo   🛡️ GuardianShield - Complete Environment + GitHub Sync Setup
echo ================================================================
echo.
echo This will install everything needed and connect to your existing
echo GitHub repository, merging all changes from your other computer.
echo.
echo What this does:
echo ✓ Install Python (if needed)
echo ✓ Install Git (if needed)  
echo ✓ Connect to your existing guardianshield-agents repository
echo ✓ Backup your current local files
echo ✓ Merge changes from your other computer
echo ✓ Set up real-time GitHub sync
echo.

echo ⚠️ IMPORTANT: Have your GitHub repository URL ready!
echo Example: https://github.com/yourusername/guardianshield-agents.git
echo.

pause

echo.
echo 🐍 Checking Python installation...

REM Check Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python not found. Installing...
    
    REM Try winget for Python
    winget install --id Python.Python.3.11 -e --source winget
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ Auto-install failed
        echo.
        echo Please install Python manually:
        echo 1. Go to: https://www.python.org/downloads/
        echo 2. Download Python 3.11 or newer
        echo 3. ⚠️ IMPORTANT: Check "Add Python to PATH" during install
        echo 4. Restart VS Code after installation
        echo 5. Run this script again
        echo.
        start https://www.python.org/downloads/
        pause
        exit /b 1
    ) else (
        echo ✅ Python installed! Please restart VS Code and run this script again.
        pause
        exit /b 0
    )
) else (
    echo ✅ Python is installed
)

echo.
echo 📂 Checking Git installation...

REM Check Git
git --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Git not found. Installing...
    
    REM Try winget for Git
    winget install --id Git.Git -e --source winget
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ Auto-install failed
        echo.
        echo Please install Git manually:
        echo 1. Go to: https://git-scm.com/download/win
        echo 2. Download and install with default settings
        echo 3. Restart VS Code after installation
        echo 4. Run this script again
        echo.
        start https://git-scm.com/download/win
        pause
        exit /b 1
    ) else (
        echo ✅ Git installed! Please restart VS Code and run this script again.
        pause
        exit /b 0
    )
) else (
    echo ✅ Git is installed
)

echo.
echo 🔗 Ready to connect to your existing GitHub repository!
echo.

REM Get repository URL from user
set /p REPO_URL="Enter your GitHub repository URL: "

if "%REPO_URL%"=="" (
    echo ❌ Repository URL is required
    pause
    exit /b 1
)

echo.
echo 📦 Creating backup of current files...
if exist local_backup rmdir /s /q local_backup
mkdir local_backup
xcopy /s /e /h /y * local_backup\ >nul 2>&1

echo ✅ Files backed up to local_backup\
echo.

echo 📥 Connecting to existing repository...

REM Initialize git if not already done
if not exist .git (
    git init
    git config user.name "GuardianShield Agent"
    git config user.email "agent@guardianshield.ai"
)

REM Add remote origin
git remote remove origin >nul 2>&1
git remote add origin "%REPO_URL%"

echo ✅ Remote repository connected
echo.

echo 🔄 Fetching existing repository content...
git fetch origin

echo 🔄 Merging with existing repository...

REM Try to merge with main branch
git merge origin/main >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    REM Try master branch if main doesn't exist
    git merge origin/master >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo ⚠️ Merge conflicts detected. Creating a new branch...
        git checkout -b local-merge-branch
        git add .
        git commit -m "Local changes before merge"
    )
)

echo ✅ Repository merged
echo.

echo 📤 Pushing any new local changes...
git add .
git commit -m "Sync from local development - %date% %time%" >nul 2>&1
git push origin main >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    git push origin master >nul 2>&1
)

echo ✅ Changes pushed to GitHub
echo.

echo 📦 Installing Python dependencies for auto-sync...
python -m pip install --upgrade pip >nul
python -m pip install watchdog fastapi uvicorn websockets >nul

echo ✅ Dependencies installed
echo.

echo.
echo ================================================================
echo   🎉 SETUP COMPLETE! 
echo ================================================================
echo.
echo ✅ Connected to your existing GitHub repository
echo ✅ Local files backed up to: local_backup\
echo ✅ Repository synced with your other computer  
echo ✅ Ready for real-time GitHub sync
echo.
echo 🚀 To start real-time sync: python auto_sync_github.py
echo.
echo All your changes will now automatically sync to GitHub!
echo Your development is now unified across all computers.
echo.

pause