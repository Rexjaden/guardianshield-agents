@echo off
setlocal EnableDelayedExpansion

echo 🛡️ GuardianShield Complete Environment Setup
echo ===========================================

REM Check Python installation
echo 🐍 Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python not found. Installing Python...
    
    REM Try winget for Python
    winget install --id Python.Python.3.11 -e --source winget
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ Winget Python installation failed.
        echo 📥 Please install Python manually from: https://www.python.org/downloads/
        echo ⚠️ Make sure to check "Add Python to PATH" during installation
        pause
        exit /b 1
    )
    
    echo ✅ Python installed! Refreshing environment...
    call refreshenv
)

echo ✅ Python check complete

REM Check Git installation
echo 📂 Checking Git installation...
git --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Git not found. Installing Git...
    
    REM Try winget for Git
    winget install --id Git.Git -e --source winget
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ Winget Git installation failed.
        echo 📥 Please install Git manually from: https://git-scm.com/download/win
        pause
        exit /b 1
    )
    
    echo ✅ Git installed! Refreshing environment...
    call refreshenv
)

echo ✅ Git check complete

REM Initialize Git repository
echo 📁 Setting up Git repository...
if not exist .git (
    git init
    git config user.name "GuardianShield Agent"
    git config user.email "agent@guardianshield.ai"
    echo ✅ Git repository initialized
) else (
    echo ✅ Git repository already exists
)

REM Create .gitignore
echo 📝 Creating .gitignore...
(
echo # Python
echo __pycache__/
echo *.py[cod]
echo *$py.class
echo *.so
echo .Python
echo build/
echo develop-eggs/
echo dist/
echo downloads/
echo eggs/
echo .eggs/
echo lib/
echo lib64/
echo parts/
echo sdist/
echo var/
echo wheels/
echo *.egg-info/
echo .installed.cfg
echo *.egg
echo MANIFEST
echo.
echo # Virtual Environment
echo venv/
echo env/
echo ENV/
echo .venv/
echo .env
echo.
echo # IDE
echo .vscode/settings.json
echo .idea/
echo *.swp
echo *.swo
echo *~
echo.
echo # Logs
echo *.log
echo logs/
echo agent_*.jsonl
echo.
echo # OS
echo .DS_Store
echo Thumbs.db
echo.
echo # Temporary files
echo *.tmp
echo *.temp
echo temp/
echo.
echo # API Keys ^& Secrets
echo .env.local
echo secrets.json
echo config/secrets/
echo.
echo # Database
echo *.db
echo *.sqlite
echo *.sqlite3
echo.
echo # Backup files
echo *.bak
echo *.backup
) > .gitignore

echo ✅ .gitignore created

REM Install Python dependencies
echo 📦 Installing Python dependencies...
python -m pip install --upgrade pip
python -m pip install watchdog fastapi uvicorn websockets

echo.
echo 🎯 NEXT STEPS FOR GITHUB SYNC:
echo ===============================
echo 1. Create a new repository on GitHub named 'guardianshield-agents'
echo 2. Copy the repository URL (e.g., https://github.com/yourusername/guardianshield-agents.git)
echo 3. Run these commands in order:
echo.
echo    git remote add origin [YOUR_GITHUB_REPO_URL]
echo    git add .
echo    git commit -m "Initial GuardianShield commit"
echo    git branch -M main
echo    git push -u origin main
echo.
echo 4. Then start real-time sync with:
echo    python auto_sync_github.py
echo.
echo ✅ Environment setup complete!
pause