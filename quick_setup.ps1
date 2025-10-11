Write-Host "GuardianShield GitHub Sync Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Check if Git is available
$gitInstalled = $false
try {
    git --version | Out-Null
    $gitInstalled = $true
    Write-Host "Git is installed" -ForegroundColor Green
} catch {
    Write-Host "Git is not installed" -ForegroundColor Red
    Write-Host "Please install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
}

# Check if Python is available
$pythonInstalled = $false
try {
    python --version | Out-Null
    $pythonInstalled = $true
    Write-Host "Python is installed" -ForegroundColor Green
} catch {
    Write-Host "Python is not installed" -ForegroundColor Red
    Write-Host "Please install Python from: https://www.python.org/downloads/" -ForegroundColor Yellow
}

# Initialize Git if available
if ($gitInstalled) {
    if (!(Test-Path ".git")) {
        Write-Host "Initializing Git repository..." -ForegroundColor Yellow
        git init
        git config user.name "GuardianShield Agent"
        git config user.email "agent@guardianshield.ai"
        Write-Host "Git repository initialized" -ForegroundColor Green
    } else {
        Write-Host "Git repository already exists" -ForegroundColor Green
    }
}

# Create .gitignore
Write-Host "Creating .gitignore file..." -ForegroundColor Yellow
$gitignoreContent = "# Python`n__pycache__/`n*.pyc`n*.pyo`n*.log`n.env`nvenv/`nenv/`n`n# IDE`n.vscode/`n.idea/`n`n# OS`n.DS_Store`nThumbs.db"
$gitignoreContent | Out-File -FilePath ".gitignore" -Encoding UTF8 -Force
Write-Host ".gitignore created" -ForegroundColor Green

# Install Python dependencies
if ($pythonInstalled) {
    Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
    python -m pip install watchdog fastapi uvicorn websockets
    Write-Host "Dependencies installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Cyan
Write-Host "1. Create a GitHub repository named 'guardianshield-agents'"
Write-Host "2. Add the remote: git remote add origin [YOUR_REPO_URL]"
Write-Host "3. Push code: git add . && git commit -m 'Initial commit' && git push -u origin main"
Write-Host "4. Start auto-sync: python auto_sync_github.py"
Write-Host ""

Read-Host "Press Enter to continue"