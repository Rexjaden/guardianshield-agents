# Quick GitHub Sync - ERC-8055 Development
Write-Host "🔄 Syncing to GitHub..." -ForegroundColor Green

# Add all changes
git add -A

# Check if there are changes to commit
$status = git status --porcelain
if ($status) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    git commit -m "🛡️ ERC-8055 Update - $timestamp"
    git push origin erc-8055-clean
    Write-Host "✅ Successfully synced to GitHub!" -ForegroundColor Green
} else {
    Write-Host "✅ Already up to date!" -ForegroundColor Green
}

# Show status
Write-Host "📊 Branch: $(git branch --show-current)" -ForegroundColor Cyan
Write-Host "📊 Last commit: $(git log --oneline -1)" -ForegroundColor Cyan