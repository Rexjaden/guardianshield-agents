@echo off
title GuardianShield - Sync with Existing GitHub Repository

echo.
echo ================================================================
echo   🛡️ GuardianShield - Connect to Existing GitHub Repository
echo ================================================================
echo.
echo This will:
echo ✓ Install Git (if needed)
echo ✓ Connect to your existing GitHub repository  
echo ✓ Backup your current local files
echo ✓ Merge changes from your other computer
echo ✓ Push your local changes to GitHub
echo ✓ Set up real-time sync
echo.

echo ⚠️ IMPORTANT: Have your GitHub repository URL ready!
echo Example: https://github.com/yourusername/guardianshield-agents.git
echo.

pause

REM Check if Python is available
echo Checking Python...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python not found
    echo.
    echo Please install Python first:
    echo 1. Go to: https://www.python.org/downloads/
    echo 2. Download and install
    echo 3. ⚠️ IMPORTANT: Check "Add Python to PATH"
    echo 4. Restart VS Code
    echo 5. Run this script again
    echo.
    pause
    exit /b 1
)

echo ✅ Python is available
echo.

REM Run the Python sync script
echo 🚀 Starting repository sync...
python sync_with_github.py

echo.
echo 📋 Next Steps:
echo =============
echo.
echo 1. Check that your files merged correctly
echo 2. Start real-time sync: python auto_sync_github.py
echo 3. All future changes will auto-sync to GitHub!
echo.

pause