@echo off
echo 🛡️ GuardianShield Smart Contract Quick Setup
echo ============================================
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js not found. Installing...
    echo.
    echo 📥 Downloading Node.js installer...
    
    REM Download Node.js installer
    powershell -Command "& {Invoke-WebRequest -Uri 'https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi' -OutFile '%TEMP%\node-installer.msi'}"
    
    if exist "%TEMP%\node-installer.msi" (
        echo 📦 Installing Node.js...
        msiexec /i "%TEMP%\node-installer.msi" /quiet /norestart
        
        echo ✅ Node.js installed!
        echo ⚠️ Please restart your command prompt and run this script again.
        pause
        exit /b 0
    ) else (
        echo ❌ Failed to download Node.js installer
        echo Please install Node.js manually from https://nodejs.org
        pause
        exit /b 1
    )
) else (
    echo ✅ Node.js is installed
)

REM Check npm
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ npm not found
    pause
    exit /b 1
) else (
    echo ✅ npm is available
)

echo.
echo 📦 Installing dependencies...
call npm install

if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo 🔧 Setting up environment...

REM Create .env if it doesn't exist
if not exist ".env" (
    copy ".env.example" ".env"
    echo ✅ Created .env file from template
    echo ⚠️ Please edit .env with your wallet configuration
) else (
    echo ✅ .env file already exists
)

echo.
echo 🧪 Testing compilation...
call npx hardhat compile

if %errorlevel% neq 0 (
    echo ❌ Compilation failed
    pause
    exit /b 1
)

echo.
echo 🎉 Setup complete!
echo.
echo 📋 Next steps:
echo 1. Edit .env file with your wallet details
echo 2. Run: npm test
echo 3. Deploy: npm run deploy:sepolia
echo.
echo See CONTRACTS_DEPLOYMENT.md for detailed instructions
echo.
pause