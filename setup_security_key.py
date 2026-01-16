"""
GuardianShield Security Key Setup Script
Sets up K51T Titan Security Key as the only access method (with password)
"""

import asyncio
import json
import sys
import os
import time
from datetime import datetime

# Add current directory to path to import our modules
sys.path.append(os.getcwd())

def main():
    print("🛡️ GuardianShield K51T Titan Security Key Setup")
    print("=" * 60)
    
    try:
        # Import security manager
        from security_manager import SecurityManager, SECURITY_KEY_AVAILABLE
        
        if not SECURITY_KEY_AVAILABLE:
            print("❌ FIDO2/WebAuthn libraries not available!")
            print("Run: pip install fido2 webauthn cryptography cbor2")
            return False
        
        # Initialize security manager
        sm = SecurityManager()
        print("✅ Security Manager initialized")
        
        # Check if security keys are detected
        keys = sm.security_key_manager.detect_security_keys()
        print(f"🔍 Detected {len(keys)} security key(s):")
        for i, key in enumerate(keys):
            print(f"  {i+1}. {key.get('product_name', 'Unknown')} by {key.get('manufacturer', 'Unknown')}")
        
        if not keys:
            print("⚠️ No security keys detected. Please:")
            print("  1. Insert your K51T Titan Security Key")
            print("  2. Ensure it's properly recognized by Windows")
            print("  3. Run this script again")
            return False
        
        # Test master admin password
        print(f"\n🔐 Testing master admin password...")
        test_password = os.getenv('GUARDIAN_TEST_PASSWORD', '')
        
        if not sm.authenticate_master_admin(test_password):
            print("❌ Master admin password verification failed!")
            return False
        
        print("✅ Master admin password verified")
        
        # Check current security key status
        admin_keys = sm.get_admin_security_keys()
        print(f"\n📋 Currently registered admin security keys: {len(admin_keys)}")
        
        for key in admin_keys:
            print(f"  - {key.get('nickname', 'Unnamed')} (Last used: {key.get('last_used', 'Never')})")
        
        # Setup menu
        while True:
            print(f"\n🔧 Security Key Setup Options:")
            print("1. Register new K51T Titan Security Key")
            print("2. Enable security key requirement (password + key)")
            print("3. Test current security key authentication")
            print("4. Show security key status")
            print("5. Remove security key requirement (password only)")
            print("0. Exit")
            
            choice = input("\nSelect option (0-5): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                register_new_key(sm)
            elif choice == "2":
                enable_requirement(sm)
            elif choice == "3":
                test_authentication(sm)
            elif choice == "4":
                show_status(sm)
            elif choice == "5":
                disable_requirement(sm)
            else:
                print("❌ Invalid option, please try again")
        
        print("\n✅ Setup completed!")
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

def register_new_key(sm):
    """Register a new security key"""
    print("\n🔑 Registering new security key...")
    print("This will create a WebAuthn registration challenge.")
    print("Note: In a web browser, this would trigger the browser's WebAuthn UI.")
    print("For testing, we'll simulate the process.")
    
    try:
        # Start registration
        registration_data = sm.register_admin_security_key()
        print("✅ Registration challenge created!")
        print(f"Challenge ID: {registration_data['challenge_id']}")
        
        print("\n📝 Registration Options:")
        options = registration_data['options']['publicKey']
        print(f"  - RP: {options['rp']['name']} ({options['rp']['id']})")
        print(f"  - User: {options['user']['name']}")
        print(f"  - Challenge: {options['challenge'][:32]}...")
        print(f"  - Timeout: {options['timeout']}ms")
        
        print("\n⚠️ In a real web environment:")
        print("  1. Insert your K51T Titan Security Key")
        print("  2. Navigate to the admin login page")
        print("  3. Browser will prompt you to touch your security key")
        print("  4. Key will be registered after verification")
        
        print("\n🔧 For now, the registration challenge is created and ready.")
        print("Integration with web frontend is needed to complete registration.")
        
    except Exception as e:
        print(f"❌ Registration failed: {e}")

def enable_requirement(sm):
    """Enable security key requirement"""
    print("\n🔒 Enabling security key requirement...")
    
    admin_keys = sm.get_admin_security_keys()
    if not admin_keys:
        print("⚠️ No security keys registered for admin user!")
        print("Please register a security key first (option 1)")
        return
    
    try:
        sm.enable_security_key_requirement()
        print("✅ Security key requirement ENABLED")
        print("🔐 Admin login now requires: Password + Security Key")
        print(f"📱 {len(admin_keys)} security key(s) are authorized")
        
    except Exception as e:
        print(f"❌ Failed to enable requirement: {e}")

def disable_requirement(sm):
    """Disable security key requirement"""
    print("\n🔓 Disabling security key requirement...")
    
    confirm = input("⚠️ This will allow password-only admin access. Continue? (y/N): ")
    if confirm.lower() != 'y':
        print("Cancelled.")
        return
    
    try:
        sm.disable_security_key_requirement()
        print("✅ Security key requirement DISABLED")
        print("🔐 Admin login now requires: Password only")
        print("⚠️ Consider re-enabling for maximum security")
        
    except Exception as e:
        print(f"❌ Failed to disable requirement: {e}")

def test_authentication(sm):
    """Test security key authentication"""
    print("\n🧪 Testing security key authentication...")
    
    if not sm.security_key_required:
        print("⚠️ Security key requirement is currently DISABLED")
        print("Enable it first (option 2) to test authentication")
        return
    
    admin_keys = sm.get_admin_security_keys()
    if not admin_keys:
        print("❌ No security keys registered!")
        return
    
    print("🔐 Testing password + security key authentication...")
    
    try:
        # Test password first
        password_valid, challenge_data = sm.authenticate_master_admin_with_key("Annielou07051953")
        
        if not password_valid:
            print("❌ Password authentication failed")
            return
        
        print("✅ Password authentication successful")
        
        if challenge_data:
            print("✅ Security key challenge created!")
            print(f"Challenge ID: {challenge_data['challenge_id']}")
            print("📱 In a web browser, you would now touch your security key")
            print("🔧 Challenge is ready for frontend integration")
        else:
            print("⚠️ No security key challenge (may be disabled or unavailable)")
            
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")

def show_status(sm):
    """Show current security key status"""
    print("\n📊 Security Key Status:")
    print("-" * 40)
    
    # Security key availability
    if sm.security_key_manager:
        print("✅ FIDO2/WebAuthn support: Available")
    else:
        print("❌ FIDO2/WebAuthn support: Not available")
        return
    
    # Requirement status
    if sm.security_key_required:
        print("🔒 Security key requirement: ENABLED")
        print("   Admin login requires: Password + Security Key")
    else:
        print("🔓 Security key requirement: DISABLED") 
        print("   Admin login requires: Password only")
    
    # Detected hardware
    keys = sm.security_key_manager.detect_security_keys()
    print(f"🔍 Detected security keys: {len(keys)}")
    for i, key in enumerate(keys):
        print(f"   {i+1}. {key.get('product_name', 'Unknown')} by {key.get('manufacturer', 'Unknown')}")
    
    # Registered credentials
    admin_keys = sm.get_admin_security_keys()
    print(f"🔑 Registered admin keys: {len(admin_keys)}")
    for key in admin_keys:
        created = key.get('created_at', 'Unknown')[:10]  # Just the date
        last_used = key.get('last_used', 'Never')[:10] if key.get('last_used') != 'Never' else 'Never'
        print(f"   - {key.get('nickname', 'Unnamed')} (Created: {created}, Last used: {last_used})")
    
    # Active challenges
    active_challenges = len(sm.security_key_manager.active_challenges)
    print(f"⏳ Active challenges: {active_challenges}")

if __name__ == "__main__":
    print("🚀 Starting GuardianShield Security Key Setup...")
    success = main()
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("🔐 Your K51T Titan Security Key is ready to use with GuardianShield")
    else:
        print("\n❌ Setup encountered issues. Please check the errors above.")
    
    input("\nPress Enter to exit...")