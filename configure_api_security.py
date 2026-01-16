"""
GuardianShield API Security Configuration & Testing
Comprehensive security setup and validation for your API endpoints
"""

import sys
import os
import json
import time
import requests
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())

def main():
    print("🛡️ GuardianShield API Security Configuration")
    print("=" * 60)
    
    while True:
        print(f"\n🔧 Security Configuration Options:")
        print("1. 🔍 Test Current Security Status")
        print("2. 🔑 Create API Key for External Access")
        print("3. 🚫 Configure IP Allowlist for Admin Access")
        print("4. 🧪 Run Security Tests (Simulated Attacks)")
        print("5. 📊 View Security Metrics & Events")
        print("6. 🌐 Test Rate Limiting")
        print("7. ⚡ Configure DDoS Protection Settings")
        print("0. Exit")
        
        choice = input("\nSelect option (0-7): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            test_security_status()
        elif choice == "2":
            create_api_key()
        elif choice == "3":
            configure_ip_allowlist()
        elif choice == "4":
            run_security_tests()
        elif choice == "5":
            view_security_metrics()
        elif choice == "6":
            test_rate_limiting()
        elif choice == "7":
            configure_ddos_protection()
        else:
            print("❌ Invalid option")
    
    print("\n✅ Security configuration completed!")

def test_security_status():
    """Test current API security status"""
    print("\n🔍 Testing API Security Status...")
    
    try:
        # Test if API server is running
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API Server: Running")
        else:
            print("⚠️ API Server: Running but returned unexpected status")
        
        # Test security headers
        headers = response.headers
        security_checks = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
        }
        
        print("\n🔒 Security Headers:")
        for header, expected in security_checks.items():
            if header in headers:
                print(f"  ✅ {header}: Present")
            else:
                print(f"  ❌ {header}: Missing")
        
        # Test CORS configuration
        cors_test = requests.options("http://localhost:8000/api/auth/me", 
                                   headers={"Origin": "https://guardian-shield.io"}, 
                                   timeout=5)
        if "Access-Control-Allow-Origin" in cors_test.headers:
            print("  ✅ CORS: Configured")
        else:
            print("  ⚠️ CORS: Not detected in response")
            
    except requests.exceptions.ConnectionError:
        print("❌ API Server: Not running")
        print("💡 Start with: python api_server.py")
    except Exception as e:
        print(f"❌ Security test failed: {e}")

def create_api_key():
    """Create API key for external access"""
    print("\n🔑 Create API Key...")
    
    # This would need admin authentication in a real scenario
    print("⚠️ API key creation requires admin access to the running API server")
    print("📝 Steps to create API key:")
    print("1. Start your API server: python api_server.py")
    print("2. Login as master admin via web interface")
    print("3. Use POST /api/security/api-key endpoint")
    print("4. Or use admin console: python admin_console.py")
    
    # Show example curl command
    print("\n💻 Example API key creation (replace with your token):")
    print("curl -X POST http://localhost:8000/api/security/api-key \\")
    print("  -H 'Authorization: Bearer YOUR_ADMIN_TOKEN' \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{\"user\": \"api_user\", \"permissions\": [\"read\", \"agents\"], \"rate_limit\": 1000}'")

def configure_ip_allowlist():
    """Configure IP allowlist for admin access"""
    print("\n🚫 Configure IP Allowlist for Admin Access...")
    
    try:
        from advanced_api_security import advanced_security
        
        print("Current allowed IP ranges:")
        if advanced_security.allowed_ip_ranges:
            for ip_range in advanced_security.allowed_ip_ranges:
                print(f"  - {ip_range}")
        else:
            print("  - No restrictions (all IPs allowed)")
        
        print(f"\nOptions:")
        print("1. Add IP range (e.g., 192.168.1.0/24)")
        print("2. Add single IP (e.g., 203.0.113.1)")
        print("3. Clear all restrictions")
        print("4. Back to main menu")
        
        choice = input("Select option (1-4): ").strip()
        
        if choice == "1":
            ip_range = input("Enter IP range (CIDR format, e.g., 192.168.1.0/24): ").strip()
            if ip_range:
                advanced_security.allowed_ip_ranges.append(ip_range)
                print(f"✅ Added IP range: {ip_range}")
        elif choice == "2":
            ip = input("Enter IP address: ").strip()
            if ip:
                advanced_security.allowed_ip_ranges.append(f"{ip}/32")
                print(f"✅ Added IP: {ip}")
        elif choice == "3":
            advanced_security.allowed_ip_ranges.clear()
            print("✅ Cleared all IP restrictions")
    
    except Exception as e:
        print(f"❌ Configuration failed: {e}")

def run_security_tests():
    """Run simulated security tests"""
    print("\n🧪 Running Security Tests (Simulated Attacks)...")
    
    base_url = "http://localhost:8000"
    
    tests = [
        {
            "name": "SQL Injection Test",
            "endpoint": "/api/auth/login",
            "method": "POST",
            "data": {
                "username": "admin' OR '1'='1",
                "password": "test"
            }
        },
        {
            "name": "XSS Test", 
            "endpoint": "/health",
            "method": "GET",
            "params": {"test": "<script>alert('xss')</script>"}
        },
        {
            "name": "Rate Limit Test",
            "endpoint": "/health",
            "method": "GET",
            "count": 105  # Exceed default 100 req/min
        }
    ]
    
    for test in tests:
        print(f"\n🔍 {test['name']}:")
        
        try:
            if test['name'] == "Rate Limit Test":
                # Test rate limiting
                success_count = 0
                for i in range(test['count']):
                    response = requests.get(f"{base_url}{test['endpoint']}", timeout=1)
                    if response.status_code == 200:
                        success_count += 1
                    elif response.status_code == 429:
                        print(f"  ✅ Rate limit triggered after {success_count} requests")
                        break
                    time.sleep(0.01)  # Small delay between requests
                
                if success_count >= test['count']:
                    print(f"  ⚠️ Rate limiting may not be working (all {success_count} requests succeeded)")
            else:
                # Test injection attacks
                if test['method'] == 'POST':
                    response = requests.post(
                        f"{base_url}{test['endpoint']}", 
                        json=test['data'],
                        timeout=5
                    )
                else:
                    response = requests.get(
                        f"{base_url}{test['endpoint']}", 
                        params=test.get('params', {}),
                        timeout=5
                    )
                
                if response.status_code == 403:
                    print("  ✅ Attack blocked by security filter")
                elif response.status_code == 401:
                    print("  ✅ Attack rejected (authentication required)")
                elif response.status_code == 400:
                    print("  ✅ Attack rejected (bad request)")
                else:
                    print(f"  ⚠️ Response: {response.status_code} (check if properly handled)")
                    
        except requests.exceptions.ConnectionError:
            print("  ❌ API server not running")
            break
        except Exception as e:
            print(f"  ❌ Test failed: {e}")

def view_security_metrics():
    """View security metrics and recent events"""
    print("\n📊 Security Metrics & Events...")
    
    try:
        from advanced_api_security import advanced_security
        
        print("Current Security Status:")
        print(f"  🚫 Blocked IPs: {len(advanced_security.blocked_ips)}")
        print(f"  ⚠️ Suspicious IPs: {len(advanced_security.suspicious_ips)}")
        print(f"  🔑 Active API Keys: {len([k for k in advanced_security.api_keys.values() if k['active']])}")
        
        if advanced_security.blocked_ips:
            print(f"\nBlocked IPs:")
            for ip, until_time in advanced_security.blocked_ips.items():
                remaining = max(0, int(until_time - time.time()))
                print(f"  - {ip} (unblocks in {remaining}s)")
        
        # Show recent security events if file exists
        if os.path.exists('security_events.jsonl'):
            print(f"\nRecent Security Events:")
            with open('security_events.jsonl', 'r') as f:
                lines = f.readlines()[-10:]  # Last 10 events
                for line in lines:
                    try:
                        event = json.loads(line.strip())
                        timestamp = event['timestamp'][:19]  # Remove microseconds
                        print(f"  - {timestamp}: {event['type']} from {event['ip']}")
                    except:
                        continue
        else:
            print("\n📝 No security events logged yet")
            
    except Exception as e:
        print(f"❌ Failed to view metrics: {e}")

def test_rate_limiting():
    """Test rate limiting configuration"""
    print("\n🌐 Testing Rate Limiting...")
    
    base_url = "http://localhost:8000"
    
    print("Sending rapid requests to test rate limiting...")
    success_count = 0
    rate_limited = False
    
    try:
        for i in range(120):  # Try to exceed 100 req/min limit
            response = requests.get(f"{base_url}/health", timeout=1)
            
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                print(f"✅ Rate limiting activated after {success_count} requests")
                print("✅ Rate limiting is working correctly")
                rate_limited = True
                break
            
            if i % 20 == 0:
                print(f"  Sent {i + 1} requests...")
            
            time.sleep(0.01)  # Small delay to prevent overwhelming
        
        if not rate_limited:
            print(f"⚠️ Rate limiting may not be active (completed all {success_count} requests)")
            print("💡 Check if enhanced rate limiter is properly configured")
    
    except requests.exceptions.ConnectionError:
        print("❌ API server not running")
    except Exception as e:
        print(f"❌ Rate limit test failed: {e}")

def configure_ddos_protection():
    """Configure DDoS protection settings"""
    print("\n⚡ Configure DDoS Protection Settings...")
    
    try:
        from advanced_api_security import advanced_security
        
        print("Current DDoS Protection Settings:")
        print(f"Rate Limits:")
        for endpoint_type, limits in advanced_security.rate_limits.items():
            print(f"  - {endpoint_type}: {limits['requests']} requests per {limits['window']}s")
        
        print(f"\nOptions:")
        print("1. Adjust default rate limit")
        print("2. Adjust auth endpoint rate limit") 
        print("3. Adjust admin endpoint rate limit")
        print("4. View current blocked IPs")
        print("5. Back to main menu")
        
        choice = input("Select option (1-5): ").strip()
        
        if choice == "1":
            requests = input(f"Current default: {advanced_security.rate_limits['default']['requests']} req/min. New value: ")
            if requests.isdigit():
                advanced_security.rate_limits['default']['requests'] = int(requests)
                print(f"✅ Updated default rate limit to {requests} req/min")
        elif choice == "2":
            requests = input(f"Current auth: {advanced_security.rate_limits['auth']['requests']} req/min. New value: ")
            if requests.isdigit():
                advanced_security.rate_limits['auth']['requests'] = int(requests)
                print(f"✅ Updated auth rate limit to {requests} req/min")
        elif choice == "3":
            requests = input(f"Current admin: {advanced_security.rate_limits['admin']['requests']} req/min. New value: ")
            if requests.isdigit():
                advanced_security.rate_limits['admin']['requests'] = int(requests)
                print(f"✅ Updated admin rate limit to {requests} req/min")
        elif choice == "4":
            if advanced_security.blocked_ips:
                print("Currently blocked IPs:")
                for ip, until_time in advanced_security.blocked_ips.items():
                    remaining = max(0, int(until_time - time.time()))
                    print(f"  - {ip} (unblocks in {remaining}s)")
            else:
                print("No IPs currently blocked")
    
    except Exception as e:
        print(f"❌ Configuration failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting GuardianShield API Security Configuration...")
    main()
    input("\nPress Enter to exit...")