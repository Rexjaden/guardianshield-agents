"""
🔒 GuardianShield Production SSL/HTTPS Security Setup
Critical security configuration for live deployment
"""

import os
import json
import subprocess
from datetime import datetime, timedelta

class SSLSecurityManager:
    def __init__(self):
        self.domain = "guardian-shield.io"
        self.ssl_dir = "ssl_certificates"
        self.nginx_config_dir = "nginx_config"
        
        # Create directories
        os.makedirs(self.ssl_dir, exist_ok=True)
        os.makedirs(self.nginx_config_dir, exist_ok=True)
    
    def generate_ssl_config(self):
        """Generate SSL configuration for production"""
        
        # SSL configuration for Nginx
        ssl_config = f"""
# GuardianShield SSL Configuration
# Strong SSL configuration for {self.domain}

server {{
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name {self.domain} www.{self.domain};
    
    # SSL Certificate paths (update with actual paths)
    ssl_certificate /etc/ssl/certs/{self.domain}.crt;
    ssl_certificate_key /etc/ssl/private/{self.domain}.key;
    
    # Strong SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # SSL optimization
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;
    
    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/ssl/certs/{self.domain}_chain.crt;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self'" always;
    
    # Rate limiting
    limit_req zone=api burst=20 nodelay;
    limit_req zone=login burst=5 nodelay;
    
    # Proxy to FastAPI application
    location / {{
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Proxy timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }}
    
    # Admin endpoints with additional security
    location /admin {{
        # IP whitelist (update with your admin IPs)
        allow 172.58.254.32;  # Your server IP
        allow 127.0.0.1;      # Localhost
        # allow YOUR_HOME_IP;   # Add your home/office IP
        deny all;
        
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
    
    # API endpoints with rate limiting
    location /api/ {{
        limit_req zone=api burst=30 nodelay;
        
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
    
    # Static files with long cache
    location /static/ {{
        alias /var/www/{self.domain}/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }}
    
    # Security.txt for vulnerability disclosure
    location /.well-known/security.txt {{
        alias /var/www/{self.domain}/.well-known/security.txt;
    }}
}}

# HTTP to HTTPS redirect
server {{
    listen 80;
    listen [::]:80;
    server_name {self.domain} www.{self.domain};
    
    # Redirect all HTTP traffic to HTTPS
    return 301 https://$server_name$request_uri;
}}

# Rate limiting zones
http {{
    # API rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=60r/m;
    
    # Login rate limiting
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    
    # General rate limiting
    limit_req_zone $binary_remote_addr zone=general:10m rate=100r/m;
}}
"""
        
        # Save SSL configuration
        config_file = os.path.join(self.nginx_config_dir, f"{self.domain}.conf")
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(ssl_config)
        
        print(f"✅ SSL configuration saved: {config_file}")
        return config_file
    
    def generate_lets_encrypt_script(self):
        """Generate Let's Encrypt certificate acquisition script"""
        
        script = f"""#!/bin/bash
# GuardianShield Let's Encrypt SSL Certificate Setup
# Run this script on your production server

echo "🔒 Setting up SSL certificates for {self.domain}"

# Install Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx -y

# Stop nginx temporarily
sudo systemctl stop nginx

# Obtain SSL certificate
sudo certbot certonly --standalone \\
    -d {self.domain} \\
    -d www.{self.domain} \\
    --email security@{self.domain} \\
    --agree-tos \\
    --non-interactive

# Install nginx configuration
sudo cp nginx_config/{self.domain}.conf /etc/nginx/sites-available/{self.domain}
sudo ln -s /etc/nginx/sites-available/{self.domain} /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Start nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Set up automatic certificate renewal
echo "0 0,12 * * * root python3 -c 'import random; import time; time.sleep(random.random() * 3600)' && certbot renew -q" | sudo tee -a /etc/crontab > /dev/null

echo "✅ SSL certificates installed successfully!"
echo "🔒 Your site is now secure at https://{self.domain}"

# Test SSL configuration
echo "🧪 Testing SSL configuration..."
curl -I https://{self.domain} || echo "⚠️ SSL test failed - check configuration"

echo "📊 SSL rating test (optional):"
echo "Visit: https://www.ssllabs.com/ssltest/analyze.html?d={self.domain}"
"""
        
        script_file = "setup_ssl_certificates.sh"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script)
        
        # Make executable
        os.chmod(script_file, 0o755)
        
        print(f"✅ Let's Encrypt setup script created: {script_file}")
        return script_file
    
    def generate_security_txt(self):
        """Generate security.txt file for vulnerability disclosure"""
        
        security_txt = f"""Contact: security@{self.domain}
Contact: https://{self.domain}/security
Expires: {(datetime.utcnow() + timedelta(days=365)).strftime('%Y-%m-%dT%H:%M:%S.000Z')}
Acknowledgments: https://{self.domain}/security/acknowledgments
Preferred-Languages: en
Canonical: https://{self.domain}/.well-known/security.txt
Policy: https://{self.domain}/security/policy

# GuardianShield Security Contact Information
# 
# If you have discovered a security vulnerability in GuardianShield,
# please report it to us responsibly. We appreciate your help in
# keeping our platform secure.
#
# Please include:
# - Description of the vulnerability
# - Steps to reproduce
# - Potential impact
# - Your contact information (optional)
#
# We will respond within 24 hours and work with you to address
# any security issues promptly.
"""
        
        # Create well-known directory
        os.makedirs(".well-known", exist_ok=True)
        
        security_file = ".well-known/security.txt"
        with open(security_file, 'w', encoding='utf-8') as f:
            f.write(security_txt)
        
        print(f"✅ Security disclosure file created: {security_file}")
        return security_file
    
    def generate_security_headers_middleware(self):
        """Generate enhanced security headers for FastAPI"""
        
        middleware_code = '''
"""
Enhanced Security Headers Middleware for Production
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class ProductionSecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Production-grade security headers middleware
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Strict Transport Security (HSTS)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # Content Security Policy (CSP)
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "img-src 'self' data: https: blob:; "
            "font-src 'self' data: https://fonts.gstatic.com; "
            "connect-src 'self' https: wss: ws:; "
            "media-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'; "
            "upgrade-insecure-requests"
        )
        response.headers["Content-Security-Policy"] = csp_policy
        
        # Additional security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=(), "
            "accelerometer=(), ambient-light-sensor=()"
        )
        
        # Cache control for sensitive pages
        if any(path in str(request.url.path) for path in ['/admin', '/api/auth', '/security']):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        # Server header removal (security through obscurity)
        if "Server" in response.headers:
            del response.headers["Server"]
        
        return response
'''
        
        middleware_file = "production_security_middleware.py"
        with open(middleware_file, 'w', encoding='utf-8') as f:
            f.write(middleware_code)
        
        print(f"✅ Production security middleware created: {middleware_file}")
        return middleware_file

def main():
    print("🔒 GuardianShield Production SSL/HTTPS Security Setup")
    print("=" * 55)
    
    ssl_manager = SSLSecurityManager()
    
    print("\\n📋 Generating production security configurations...")
    
    # Generate SSL configuration
    ssl_config = ssl_manager.generate_ssl_config()
    
    # Generate Let's Encrypt script
    ssl_script = ssl_manager.generate_lets_encrypt_script()
    
    # Generate security.txt
    security_txt = ssl_manager.generate_security_txt()
    
    # Generate security middleware
    middleware = ssl_manager.generate_security_headers_middleware()
    
    print(f"\\n✅ Production SSL Security Setup Complete!")
    print("=" * 45)
    
    print(f"\\n📁 Files Created:")
    print(f"  • {ssl_config} - Nginx SSL configuration")
    print(f"  • {ssl_script} - Let's Encrypt setup script")  
    print(f"  • {security_txt} - Security disclosure policy")
    print(f"  • {middleware} - Enhanced security middleware")
    
    print(f"\\n🚀 Next Steps:")
    print("1. Upload files to your production server")
    print("2. Run setup_ssl_certificates.sh on server")
    print("3. Update api_server.py to use production_security_middleware")
    print("4. Test SSL configuration at: https://www.ssllabs.com/ssltest/")
    print("5. Submit domain to HSTS preload list")
    
    print(f"\\n⚠️ Important:")
    print("• Update IP whitelist in nginx config with your admin IPs")
    print("• Test certificate renewal: sudo certbot renew --dry-run")
    print("• Monitor SSL certificate expiration dates")
    print("• Set up monitoring for SSL certificate renewal")

if __name__ == "__main__":
    main()