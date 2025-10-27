# GitHub Sync Strategy for ERC-8055 Development
# This script ensures all changes are automatically synced to GitHub

Write-Host "🔄 GitHub Sync Check - ERC-8055 Development" -ForegroundColor Green
Write-Host "=" * 50

# Check git status
Write-Host "`n📋 Checking current status..." -ForegroundColor Yellow
git status --porcelain

if ($LASTEXITCODE -eq 0) {
    $changes = git status --porcelain
    if ($changes) {
        Write-Host "📁 Changes detected - preparing to sync..." -ForegroundColor Cyan
        
        # Add all changes
        git add -A
        
        # Get timestamp for commit message
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        
        # Commit with descriptive message
        git commit -m "🛡️ ERC-8055 Development Update - $timestamp

- Automated sync of all ERC-8055 related changes
- Ensuring GitHub repository stays current
- Maintaining development continuity"
        
        # Push to current branch
        $currentBranch = git branch --show-current
        Write-Host "🚀 Pushing to GitHub branch: $currentBranch" -ForegroundColor Green
        git push origin $currentBranch
        
        Write-Host "✅ Successfully synced to GitHub!" -ForegroundColor Green
    } else {
        Write-Host "✅ Repository is already up to date with GitHub" -ForegroundColor Green
    }
} else {
    Write-Host "❌ Git status check failed" -ForegroundColor Red
}

# Show current branch and remote status
Write-Host "`n📊 Repository Status:" -ForegroundColor Yellow
Write-Host "Branch: $(git branch --show-current)" -ForegroundColor White
Write-Host "Remote: $(git remote get-url origin)" -ForegroundColor White
Write-Host "Last Commit: $(git log --oneline -1)" -ForegroundColor White

Write-Host "`n🛡️ ERC-8055 files protected and synced!" -ForegroundColor Magenta