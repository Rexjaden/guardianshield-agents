@echo off
REM GuardianShield Deployment Manager - Windows Batch Script

if "%1"=="" goto usage

if /i "%1"=="coming-soon" goto coming_soon
if /i "%1"=="full-system" goto full_system
if /i "%1"=="stop" goto stop_all
if /i "%1"=="status" goto status

:usage
echo.
echo GuardianShield Deployment Manager
echo =================================
echo.
echo Usage: deploy.bat [command]
echo.
echo Commands:
echo   coming-soon   Deploy Coming Soon page only
echo   full-system   Deploy full GuardianShield system
echo   stop          Stop all containers
echo   status        Show current deployment status
echo.
echo Quick Start:
echo   deploy.bat coming-soon
echo.
goto end

:coming_soon
echo 🚀 Deploying Coming Soon page...
docker-compose -f docker-compose.coming-soon.yml up -d
timeout /t 3 /nobreak >nul
echo ✅ Coming Soon page deployed!
echo 🌐 Available at: http://localhost
goto end

:full_system
echo 🚀 Deploying Full GuardianShield System...
docker-compose -f docker-compose.core.yml --env-file .env.production up -d
echo 🔄 System starting... Please wait...
timeout /t 15 /nobreak >nul
echo ✅ Full system deployed!
echo 🌐 Main App: http://localhost:8000
goto end

:stop_all
echo 🛑 Stopping all containers...
docker-compose -f docker-compose.coming-soon.yml down >nul 2>&1
docker-compose -f docker-compose.core.yml --env-file .env.production down >nul 2>&1
echo ✅ All containers stopped
goto end

:status
echo 🔍 GuardianShield Status
echo ========================
docker ps --filter "name=guardianshield" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
goto end

:end