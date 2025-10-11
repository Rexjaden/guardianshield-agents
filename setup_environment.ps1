# GuardianShield Complete Environment Setup (PowerShell)
Write-Host "🛡️ GuardianShield Complete Environment Setup" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan

# Check Python installation
Write-Host "🐍 Checking Python installation..." -ForegroundColor Yellow
$pythonCheck = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCheck) {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python is installed: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Python not found. Installing Python..." -ForegroundColor Red
    Write-Host " Please install Python from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "⚠️ Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
}

# Check Git installation  
Write-Host "📂 Checking Git installation..." -ForegroundColor Yellow
$gitCheck = Get-Command git -ErrorAction SilentlyContinue
if ($gitCheck) {
    $gitVersion = git --version 2>&1
    Write-Host "✅ Git is installed: $gitVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Git not found. Please install Git..." -ForegroundColor Red
    Write-Host "📥 Download Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
}

# Initialize Git repository
Write-Host "📁 Setting up Git repository..." -ForegroundColor Yellow
if (!(Test-Path ".git")) {
    if ($gitCheck) {
        git init
        git config user.name "GuardianShield Agent"
        git config user.email "agent@guardianshield.ai"
        Write-Host "✅ Git repository initialized" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Cannot initialize Git repository - Git not available" -ForegroundColor Yellow
    }
} else {
    Write-Host "✅ Git repository already exists" -ForegroundColor Green
}

# Create .gitignore
Write-Host "📝 Creating .gitignore..." -ForegroundColor Yellow
$gitignoreContent = @"
# Python
__pycache__/
*.py[cod]
*`$py.class
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

# Database
*.db
*.sqlite
*.sqlite3

# Backup files
*.bak
*.backup
"@

$gitignoreContent | Out-File -FilePath ".gitignore" -Encoding UTF8
Write-Host "✅ .gitignore created" -ForegroundColor Green

# Install Python dependencies
Write-Host "📦 Installing Python dependencies..." -ForegroundColor Yellow
if ($pythonCheck) {
    try {
        python -m pip install --upgrade pip
        python -m pip install watchdog fastapi uvicorn websockets
        Write-Host "✅ Dependencies installed successfully!" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Some dependencies may have failed to install" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️ Cannot install dependencies - Python not available" -ForegroundColor Yellow
}

# Instructions for GitHub setup
Write-Host ""
Write-Host "🎯 NEXT STEPS FOR GITHUB SYNC:" -ForegroundColor Cyan
Write-Host "===============================" -ForegroundColor Cyan
Write-Host "1. Create a new repository on GitHub named 'guardianshield-agents'"
Write-Host "2. Copy the repository URL (e.g., https://github.com/yourusername/guardianshield-agents.git)"
Write-Host "3. Run these commands in order:"
Write-Host ""
Write-Host "   git remote add origin [YOUR_GITHUB_REPO_URL]" -ForegroundColor Yellow
Write-Host "   git add ." -ForegroundColor Yellow
Write-Host "   git commit -m 'Initial GuardianShield commit'" -ForegroundColor Yellow
Write-Host "   git branch -M main" -ForegroundColor Yellow
Write-Host "   git push -u origin main" -ForegroundColor Yellow
Write-Host ""
Write-Host "4. Then start real-time sync with:" -ForegroundColor Green
Write-Host "   python auto_sync_github.py" -ForegroundColor Green
Write-Host ""
Write-Host "✅ Environment setup complete!" -ForegroundColor Green

Read-Host "Press Enter to continue"