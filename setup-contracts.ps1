# GuardianShield Smart Contract Setup Script
# Run this script to install all prerequisites for smart contract deployment

Write-Host "🛡️ GuardianShield Smart Contract Setup" -ForegroundColor Cyan
Write-Host ("=" * 50)

# Check if Node.js is installed
$nodeFound = $false
try {
    $nodeVersion = & node --version 2>$null
    if ($nodeVersion) {
        Write-Host "✅ Node.js already installed: $nodeVersion" -ForegroundColor Green
        $nodeFound = $true
    }
} catch {
    Write-Host "❌ Node.js not found. Installing Node.js..." -ForegroundColor Yellow
}

if (-not $nodeFound) {
    # Download and install Node.js LTS
    $nodeUrl = "https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi"
    $nodeMsi = "$env:TEMP\node-installer.msi"
    
    Write-Host "⬇️ Downloading Node.js v20.10.0..." -ForegroundColor Blue
    try {
        Invoke-WebRequest -Uri $nodeUrl -OutFile $nodeMsi
        Write-Host "📦 Installing Node.js..." -ForegroundColor Blue
        Start-Process -FilePath "msiexec.exe" -ArgumentList "/i `"$nodeMsi`" /quiet /norestart" -Wait
        
        Write-Host "✅ Node.js installed successfully!" -ForegroundColor Green
        Write-Host "⚠️ Please restart your PowerShell session to use Node.js" -ForegroundColor Yellow
        Write-Host "After restarting, run this script again to continue setup." -ForegroundColor Yellow
        exit
    } catch {
        Write-Host "❌ Failed to download/install Node.js: $_" -ForegroundColor Red
        Write-Host "Please install Node.js manually from https://nodejs.org" -ForegroundColor Yellow
        exit 1
    }
}

# Check npm version
try {
    $npmVersion = & npm --version 2>$null
    Write-Host "✅ npm version: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ npm not found" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📦 Installing smart contract dependencies..." -ForegroundColor Blue

try {
    # Install dependencies
    & npm install --save-dev "@nomicfoundation/hardhat-toolbox" "@nomicfoundation/hardhat-verify" "@openzeppelin/contracts" "hardhat" "hardhat-gas-reporter" "dotenv"
    
    Write-Host "✅ Dependencies installed successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install dependencies: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🔧 Setting up environment..." -ForegroundColor Blue

# Create .env from template if it doesn't exist
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "📄 Created .env file from template" -ForegroundColor Green
    Write-Host "⚠️ Please edit .env with your configuration:" -ForegroundColor Yellow
    Write-Host "   - PRIVATE_KEY: Your wallet private key (without 0x)" -ForegroundColor White
    Write-Host "   - SEPOLIA_RPC_URL: Infura/Alchemy RPC URL" -ForegroundColor White
    Write-Host "   - ETHERSCAN_API_KEY: For contract verification" -ForegroundColor White
    Write-Host "   - INITIAL_SALE_ADDRESS: Address to receive initial tokens" -ForegroundColor White
} else {
    Write-Host "📄 .env file already exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "🧪 Testing setup..." -ForegroundColor Blue

try {
    # Test compilation
    & npx hardhat compile
    Write-Host "✅ Contracts compiled successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Compilation failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "🎉 Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Edit .env file with your configuration" -ForegroundColor White
Write-Host "2. Run tests: npm test" -ForegroundColor White
Write-Host "3. Deploy to testnet: npm run deploy:sepolia" -ForegroundColor White
Write-Host "4. Deploy to mainnet: npm run deploy:mainnet" -ForegroundColor White
Write-Host ""
Write-Host "📖 See CONTRACTS_DEPLOYMENT.md for detailed instructions" -ForegroundColor White