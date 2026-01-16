"""
GuardianShield Source Code Protection Setup
Complete security setup to prevent unauthorized access to your repository
"""

import sys
import os
import json
import subprocess
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())

def main():
    print("🔐 GuardianShield Source Code Protection Setup")
    print("=" * 60)
    
    while True:
        print(f"\n🛡️ Source Code Security Options:")
        print("1. 🔍 Scan for Exposed Secrets")
        print("2. 🚫 Setup .gitignore Security Rules") 
        print("3. 🔑 Configure Token Security")
        print("4. 📊 Generate Security Report")
        print("5. 🔄 Rotate All Tokens (Emergency)")
        print("6. 🌐 Setup GitHub Repository Protection")
        print("7. 🔒 Create Secure Environment Template")
        print("8. 📋 View Token Access Logs")
        print("0. Exit")
        
        choice = input("\nSelect option (0-8): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            scan_exposed_secrets()
        elif choice == "2":
            setup_gitignore_rules()
        elif choice == "3":
            configure_token_security()
        elif choice == "4":
            generate_security_report()
        elif choice == "5":
            emergency_token_rotation()
        elif choice == "6":
            setup_github_protection()
        elif choice == "7":
            create_secure_env_template()
        elif choice == "8":
            view_access_logs()
        else:
            print("❌ Invalid option")
    
    print("\n✅ Source code protection setup completed!")

def scan_exposed_secrets():
    """Scan for potentially exposed secrets"""
    print("\n🔍 Scanning for Exposed Secrets...")
    
    try:
        from token_security_manager import token_security_manager
        
        result = token_security_manager.scan_for_exposed_secrets()
        
        print(f"📊 Scan Results:")
        print(f"  Total secrets found: {result['total_secrets_found']}")
        
        if result['secrets']:
            print(f"\n⚠️ Potential secrets found:")
            for secret in result['secrets'][:10]:  # Show first 10
                print(f"  - {secret['file']}:{secret['line']} [{secret['type']}]")
                print(f"    Context: {secret['context']}")
            
            if len(result['secrets']) > 10:
                print(f"  ... and {len(result['secrets']) - 10} more")
            
            print(f"\n🔧 Recommendations:")
            for rec in result['recommendations']:
                print(f"  • {rec}")
        else:
            print("✅ No exposed secrets detected!")
    
    except Exception as e:
        print(f"❌ Scan failed: {e}")

def setup_gitignore_rules():
    """Setup .gitignore with security rules"""
    print("\n🚫 Setting up .gitignore Security Rules...")
    
    try:
        from token_security_manager import token_security_manager
        
        result = token_security_manager.create_gitignore_security_rules()
        print(f"✅ {result}")
        
        # Show current .gitignore contents
        if os.path.exists('.gitignore'):
            print(f"\n📄 Current .gitignore file:")
            with open('.gitignore', 'r') as f:
                lines = f.readlines()
                for i, line in enumerate(lines[-20:], start=max(1, len(lines)-19)):
                    print(f"  {i:2}: {line.rstrip()}")
    
    except Exception as e:
        print(f"❌ Setup failed: {e}")

def configure_token_security():
    """Configure token security settings"""
    print("\n🔑 Configure Token Security...")
    
    try:
        from token_security_manager import token_security_manager
        
        config = token_security_manager.config
        
        print(f"Current Token Security Configuration:")
        print(f"  🔄 Token Rotation: Every {config['token_rotation_hours']} hours")
        print(f"  🔒 MFA Required: {config['require_mfa_for_tokens']}")
        print(f"  📍 IP Restrictions: {len(config['allowed_ip_ranges'])} ranges configured")
        print(f"  ⚠️ Max Failed Attempts: {config['max_failed_attempts']}")
        
        print(f"\nOptions:")
        print("1. Change token rotation frequency")
        print("2. Add IP restriction")
        print("3. Generate new secure API token")
        print("4. View active tokens")
        print("5. Back to main menu")
        
        choice = input("Select option (1-5): ").strip()
        
        if choice == "1":
            hours = input(f"Current rotation: {config['token_rotation_hours']} hours. New value: ")
            if hours.isdigit():
                config['token_rotation_hours'] = int(hours)
                token_security_manager._save_security_config(config)
                print(f"✅ Token rotation set to {hours} hours")
        
        elif choice == "2":
            ip_range = input("Enter IP range (e.g., 192.168.1.0/24 or single IP): ").strip()
            if ip_range:
                if '/' not in ip_range and '.' in ip_range:
                    ip_range += '/32'  # Single IP
                config['allowed_ip_ranges'].append(ip_range)
                token_security_manager._save_security_config(config)
                print(f"✅ Added IP restriction: {ip_range}")
        
        elif choice == "3":
            token_type = input("Token type (api/admin/service): ").strip() or "api"
            permissions = input("Permissions (comma-separated): ").strip().split(',')
            permissions = [p.strip() for p in permissions if p.strip()]
            
            if not permissions:
                permissions = ['read']
            
            token_result = token_security_manager.generate_secure_token(
                token_type, permissions, expires_hours=24
            )
            
            print(f"✅ Generated secure token:")
            print(f"  Token: {token_result['token']}")
            print(f"  ID: {token_result['token_id']}")
            print(f"  Expires: {token_result['expires']}")
            print(f"  ⚠️ SAVE THIS TOKEN - It cannot be retrieved again!")
        
        elif choice == "4":
            token_security_manager._load_encrypted_tokens()
            active_tokens = token_security_manager.active_tokens
            
            if active_tokens:
                print(f"Active Tokens ({len(active_tokens)}):")
                for token_id, data in active_tokens.items():
                    created = data['created'][:19]  # Remove microseconds
                    expires = data['expires'][:19]
                    print(f"  - {token_id[:16]}... [{data['type']}]")
                    print(f"    Created: {created}, Expires: {expires}")
                    print(f"    Permissions: {', '.join(data['permissions'])}")
                    print(f"    Access Count: {data.get('access_count', 0)}")
            else:
                print("No active tokens found")
    
    except Exception as e:
        print(f"❌ Configuration failed: {e}")

def generate_security_report():
    """Generate comprehensive security report"""
    print("\n📊 Generating Security Report...")
    
    try:
        from token_security_manager import token_security_manager
        
        report = token_security_manager.get_security_report()
        
        print(f"🛡️ GuardianShield Security Report")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        print(f"📊 Token Status:")
        print(f"  Active Tokens: {report['tokens']['active']}")
        print(f"  Expired Tokens: {report['tokens']['expired']}")
        print(f"  Revoked Tokens: {report['tokens']['revoked']}")
        print(f"  Total Created: {report['tokens']['total_created']}")
        
        print(f"\n📈 Access Activity:")
        print(f"  Events (24h): {report['access_activity']['events_last_24h']}")
        print(f"  Logging Active: {'✅' if report['access_activity']['log_file_exists'] else '❌'}")
        
        print(f"\n🔧 Configuration:")
        print(f"  Token Rotation: {report['configuration']['token_rotation_hours']} hours")
        print(f"  IP Restrictions: {'✅' if report['configuration']['ip_restrictions_enabled'] else '❌'}")
        print(f"  MFA Required: {'✅' if report['configuration']['mfa_required'] else '❌'}")
        
        if report['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in report['recommendations']:
                print(f"  • {rec}")
    
    except Exception as e:
        print(f"❌ Report generation failed: {e}")

def emergency_token_rotation():
    """Emergency rotation of all tokens"""
    print("\n🔄 Emergency Token Rotation...")
    
    confirm = input("⚠️ This will invalidate ALL active tokens. Continue? (y/N): ")
    if confirm.lower() != 'y':
        print("Cancelled.")
        return
    
    try:
        from token_security_manager import token_security_manager
        
        rotated_count = token_security_manager.rotate_all_tokens("emergency_manual")
        print(f"✅ Rotated {rotated_count} tokens")
        print("🔒 All previous tokens are now invalid")
        print("💡 Generate new tokens for continued access")
    
    except Exception as e:
        print(f"❌ Token rotation failed: {e}")

def setup_github_protection():
    """Setup GitHub repository protection"""
    print("\n🌐 Setup GitHub Repository Protection...")
    
    try:
        from token_security_manager import token_security_manager
        
        result = token_security_manager.setup_github_protection()
        
        if "error" in result:
            print(f"❌ {result['error']}")
            return
        
        print(f"📊 GitHub Protection Status:")
        if "current_branch" in result:
            print(f"  Current Branch: {result['current_branch']}")
        
        print(f"\n🔧 Recommended GitHub Settings:")
        for rec in result.get('recommendations', []):
            print(f"  • {rec}")
        
        print(f"\n💻 Manual GitHub Setup Steps:")
        print("1. Go to your GitHub repository settings")
        print("2. Navigate to 'Branches' section")
        print("3. Add branch protection rule for 'main'")
        print("4. Enable: 'Require pull request reviews before merging'")
        print("5. Enable: 'Dismiss stale PR reviews when new commits are pushed'")
        print("6. Enable: 'Require status checks to pass before merging'")
        print("7. Enable: 'Require signed commits'")
        print("8. Consider: 'Restrict pushes that create files' for sensitive paths")
        
    except Exception as e:
        print(f"❌ GitHub protection setup failed: {e}")

def create_secure_env_template():
    """Create secure environment template"""
    print("\n🔒 Create Secure Environment Template...")
    
    env_template = """# GuardianShield Secure Environment Configuration
# NEVER commit this file to version control!

# Master Admin Credentials
GUARDIAN_MASTER_PASSWORD=your_secure_password_here

# API Security
GUARDIAN_SECRET_KEY=generate_with_secrets.token_urlsafe(64)
GUARDIAN_API_ENCRYPTION_KEY=generate_with_fernet.generate_key()

# Database Configuration  
DATABASE_URL=your_database_connection_string
REDIS_URL=your_redis_connection_string

# External API Keys (if needed)
# EXTERNAL_API_KEY=your_external_api_key
# EXTERNAL_SECRET=your_external_secret

# Security Settings
ALLOWED_IP_RANGES=127.0.0.1/32,192.168.1.0/24
TOKEN_ROTATION_HOURS=24
REQUIRE_MFA=true

# Logging and Monitoring
LOG_LEVEL=INFO
SECURITY_ALERT_EMAIL=security@yourdomain.com

# Production Settings
ENVIRONMENT=production
DEBUG=false
"""
    
    env_file = ".env.template"
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_template)
        
        print(f"✅ Created secure environment template: {env_file}")
        print("🔧 Instructions:")
        print("1. Copy .env.template to .env")
        print("2. Replace all placeholder values with actual secrets")
        print("3. Ensure .env is in your .gitignore file")
        print("4. Set appropriate file permissions (600)")
        print("5. Never commit .env files to version control")
        
        # Check if .env already exists
        if os.path.exists('.env'):
            print("⚠️ .env file already exists - review and update as needed")
        
    except Exception as e:
        print(f"❌ Template creation failed: {e}")

def view_access_logs():
    """View recent token access logs"""
    print("\n📋 Token Access Logs...")
    
    log_file = "token_access_log.jsonl"
    
    if not os.path.exists(log_file):
        print("📝 No access logs found yet")
        return
    
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        print(f"Recent Token Access Events (last 20):")
        print("-" * 60)
        
        for line in lines[-20:]:
            try:
                event = json.loads(line.strip())
                timestamp = event['timestamp'][:19]  # Remove microseconds
                event_type = event['event_type']
                token_hash = event['token_hash']
                
                print(f"{timestamp} | {event_type:20} | {token_hash}")
                
                # Show additional details for important events
                if event_type in ['token_access_invalid', 'token_access_ip_denied']:
                    details = event.get('details', {})
                    if 'client_ip' in details:
                        print(f"                     IP: {details['client_ip']}")
                
            except Exception:
                continue
        
        print(f"\nTotal log entries: {len(lines)}")
    
    except Exception as e:
        print(f"❌ Failed to read access logs: {e}")

if __name__ == "__main__":
    print("🚀 Starting GuardianShield Source Code Protection Setup...")
    main()
    input("\nPress Enter to exit...")