# GuardianShield SSL Certificate Setup Script (PowerShell)

Write-Host "Starting GuardianShield SSL Certificate Setup..." -ForegroundColor Green

# Function to check if docker network exists
function Test-DockerNetwork {
    param($NetworkName)
    try {
        $networks = docker network ls --format "{{.Name}}"
        return $networks -contains $NetworkName
    } catch {
        return $false
    }
}

# Create network if it doesn't exist
if (-not (Test-DockerNetwork "guardianshield-network")) {
    Write-Host "Creating Docker network..." -ForegroundColor Yellow
    docker network create guardianshield-network
}

# Stop any existing containers that might interfere
Write-Host "Stopping existing containers..." -ForegroundColor Yellow
try {
    docker stop guardianshield-proxy-temp 2>$null | Out-Null
    docker rm guardianshield-proxy-temp 2>$null | Out-Null
} catch {}

# Create necessary directories
Write-Host "Creating certificate directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "./certbot/conf" | Out-Null
New-Item -ItemType Directory -Force -Path "./certbot/www" | Out-Null  
New-Item -ItemType Directory -Force -Path "./certbot/logs" | Out-Null

# Start nginx with HTTP-only configuration for certificate validation
Write-Host "Starting HTTP-only nginx for certificate validation..." -ForegroundColor Yellow

try {
    $nginxContainer = docker run -d --name guardianshield-proxy-temp --network guardianshield-network -p 80:80 -v "${PWD}/nginx-temp.conf:/etc/nginx/nginx.conf:ro" -v "${PWD}/certbot/www:/var/www/certbot:ro" nginx:alpine

    if (-not $nginxContainer) {
        Write-Host "Failed to start temporary nginx server" -ForegroundColor Red
        exit 1
    }

    Write-Host "Temporary nginx server started" -ForegroundColor Green
    Start-Sleep -Seconds 5

    # Test domain accessibility
    Write-Host "Testing domain accessibility..." -ForegroundColor Yellow
    $domains = @("guardian-shield.io", "www.guardian-shield.io")

    foreach ($domain in $domains) {
        Write-Host "Testing $domain..." -ForegroundColor Gray
        try {
            $response = Invoke-WebRequest -Uri "http://$domain" -UseBasicParsing -TimeoutSec 10 -ErrorAction SilentlyContinue
            if ($response.StatusCode -in @(200, 301, 302)) {
                Write-Host "✅ $domain is accessible" -ForegroundColor Green
            } else {
                Write-Host "⚠️ $domain returned status: $($response.StatusCode)" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "⚠️ $domain may not be accessible" -ForegroundColor Yellow
        }
    }

    # Generate certificates using certbot
    Write-Host "Generating SSL certificates..." -ForegroundColor Yellow

    $certbotResult = docker run --rm --name guardianshield-certbot-temp --network guardianshield-network -v "${PWD}/certbot/conf:/etc/letsencrypt" -v "${PWD}/certbot/www:/var/www/certbot" -v "${PWD}/certbot/logs:/var/log/letsencrypt" certbot/certbot certonly --webroot --webroot-path=/var/www/certbot --email admin@guardian-shield.io --agree-tos --no-eff-email --staging -d guardian-shield.io -d www.guardian-shield.io --verbose

    # Check if certificates were generated
    if (Test-Path "./certbot/conf/live/guardian-shield.io/fullchain.pem") {
        Write-Host "SSL certificates generated successfully!" -ForegroundColor Green
        
        # Stop temporary nginx
        docker stop guardianshield-proxy-temp | Out-Null
        docker rm guardianshield-proxy-temp | Out-Null
        
        # Start production nginx with SSL
        Write-Host "Starting production nginx with SSL..." -ForegroundColor Yellow
        
        docker run -d --name guardianshield-proxy --network guardianshield-network -p 80:80 -p 443:443 -v "${PWD}/nginx.conf:/etc/nginx/nginx.conf:ro" -v "${PWD}/certbot/conf:/etc/ssl/certs:ro" -v "${PWD}/certbot/www:/var/www/certbot:ro" nginx:alpine
        
        Write-Host "GuardianShield is now running with SSL!" -ForegroundColor Green
        
    } else {
        Write-Host "SSL certificate generation failed - trying staging environment first" -ForegroundColor Yellow
        
        # For development, let's just start HTTP version
        docker stop guardianshield-proxy-temp | Out-Null
        docker rm guardianshield-proxy-temp | Out-Null
        
        docker run -d --name guardianshield-proxy --network guardianshield-network -p 80:80 -v "${PWD}/nginx-temp.conf:/etc/nginx/nginx.conf:ro" nginx:alpine
        
        Write-Host "Started HTTP-only version for development" -ForegroundColor Yellow
        Write-Host "Your site should be accessible at http://guardian-shield.io" -ForegroundColor Cyan
    }

} catch {
    Write-Host "Error during SSL setup: $($_.Exception.Message)" -ForegroundColor Red
    
    # Clean up
    try {
        docker stop guardianshield-proxy-temp 2>$null | Out-Null
        docker rm guardianshield-proxy-temp 2>$null | Out-Null
    } catch {}
    
    # Start basic HTTP server as fallback
    Write-Host "Starting fallback HTTP server..." -ForegroundColor Yellow
    docker run -d --name guardianshield-proxy --network guardianshield-network -p 80:80 -v "${PWD}/nginx-temp.conf:/etc/nginx/nginx.conf:ro" nginx:alpine
}

Write-Host "Setup complete!" -ForegroundColor Green