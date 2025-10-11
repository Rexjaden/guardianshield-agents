# GuardianShield - Connect to Existing GitHub Repository
Write-Host "🛡️ GuardianShield - Connect to Existing GitHub Repository" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will:" -ForegroundColor Yellow
Write-Host "✓ Install Git (if needed)"
Write-Host "✓ Connect to your existing GitHub repository"
Write-Host "✓ Backup your current local files"
Write-Host "✓ Merge changes from your other computer"
Write-Host "✓ Push your local changes to GitHub"
Write-Host "✓ Set up real-time sync"
Write-Host ""
Write-Host "⚠️ IMPORTANT: Have your GitHub repository URL ready!" -ForegroundColor Red
Write-Host "Example: https://github.com/yourusername/guardianshield-agents.git" -ForegroundColor Yellow
Write-Host ""

Read-Host "Press Enter to continue"

# Check if Python is available
Write-Host "Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python is available: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python first:" -ForegroundColor Yellow
    Write-Host "1. Go to: https://www.python.org/downloads/"
    Write-Host "2. Download and install"
    Write-Host "3. ⚠️ IMPORTANT: Check 'Add Python to PATH'"
    Write-Host "4. Restart VS Code"
    Write-Host "5. Run this script again"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit
}

Write-Host ""

# Run the Python sync script
Write-Host "🚀 Starting repository sync..." -ForegroundColor Green
python sync_with_github.py

Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Cyan
Write-Host "============="
Write-Host ""
Write-Host "1. Check that your files merged correctly"
Write-Host "2. Start real-time sync: python auto_sync_github.py" -ForegroundColor Green
Write-Host "3. All future changes will auto-sync to GitHub!" -ForegroundColor Green
Write-Host ""

Read-Host "Press Enter to continue"