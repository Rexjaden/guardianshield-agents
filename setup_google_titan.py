"""
Google Titan Security Key Setup for GuardianShield
Simple setup script for K51T Titan key integration
"""

import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

def main():
    print("🛡️ GuardianShield Google Titan Security Key Setup")
    print("=" * 60)
    
    try:
        from google_titan_manager import GoogleTitanKeyManager, EnhancedSecurityManager
        from security_manager import security_manager
        
        # Initialize managers
        titan_manager = GoogleTitanKeyManager()
        enhanced_sm = EnhancedSecurityManager(security_manager)
        
        print("✅ Titan Key Manager initialized")
        
        # Check current status
        status = titan_manager.get_status()
        print(f"\n📊 Current Status:")
        print(f"  🔍 Google Titan Key Detected: {'✅ YES' if status['titan_key_detected'] else '❌ NO'}")
        print(f"  🔑 Registered Keys: {status['registered_keys']}")
        print(f"  🔒 Requirement Enabled: {'✅ YES' if status['requirement_enabled'] else '❌ NO'}")
        
        if status['last_detection']:
            print(f"  📱 Device Info: {status['last_detection'][0]['FriendlyName']}")
        
        if not status['titan_key_detected']:
            print("\n⚠️ Please ensure your Google Titan Security Key is inserted")
            return False
        
        # Setup menu
        while True:
            print(f"\n🔧 Setup Options:")
            print("1. Register Google Titan Security Key")
            print("2. Enable Titan key requirement (Password + Key)")
            print("3. Test authentication (Password + Key)")
            print("4. Disable Titan key requirement (Password only)")
            print("5. Show detailed status")
            print("0. Exit")
            
            choice = input("\nSelect option (0-5): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                register_key(titan_manager)
            elif choice == "2":
                enable_requirement(titan_manager)
            elif choice == "3":
                test_authentication(enhanced_sm)
            elif choice == "4":
                disable_requirement(titan_manager)
            elif choice == "5":
                show_detailed_status(titan_manager)
            else:
                print("❌ Invalid option")
        
        print("\n✅ Setup completed!")
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

def register_key(titan_manager):
    """Register the Titan security key"""
    print("\n🔑 Registering Google Titan Security Key...")
    
    try:
        result = titan_manager.register_titan_key("master_admin")
        
        if result["success"]:
            print("✅ Registration successful!")
            print(f"  Key ID: {result['key_id']}")
            print(f"  Devices detected: {result['device_count']}")
            print("🔐 Your Titan key is now registered for admin access")
        else:
            print("❌ Registration failed")
            
    except Exception as e:
        print(f"❌ Registration error: {e}")

def enable_requirement(titan_manager):
    """Enable Titan key requirement"""
    print("\n🔒 Enabling Titan Key Requirement...")
    
    try:
        titan_manager.enable_titan_key_requirement()
        print("✅ Titan key requirement ENABLED")
        print("🔐 Admin login now requires: Password + Titan Key")
        print("📱 Your Google Titan key must be inserted and present")
        
    except Exception as e:
        print(f"❌ Failed to enable requirement: {e}")

def disable_requirement(titan_manager):
    """Disable Titan key requirement"""
    print("\n🔓 Disabling Titan Key Requirement...")
    
    confirm = input("⚠️ This allows password-only admin access. Continue? (y/N): ")
    if confirm.lower() != 'y':
        print("Cancelled.")
        return
    
    try:
        titan_manager.disable_titan_key_requirement()
        print("✅ Titan key requirement DISABLED")
        print("🔐 Admin login now requires: Password only")
        
    except Exception as e:
        print(f"❌ Failed to disable requirement: {e}")

def test_authentication(enhanced_sm):
    """Test password + Titan key authentication"""
    print("\n🧪 Testing Password + Titan Key Authentication...")
    
    password = os.getenv('GUARDIAN_TEST_PASSWORD', '')  # Load from environment
    print("🔐 Testing with master admin password...")
    
    try:
        success, message = enhanced_sm.authenticate_admin_with_titan(password)
        
        if success:
            print(f"✅ {message}")
            print("🎉 Authentication successful!")
        else:
            print(f"❌ {message}")
            
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")

def show_detailed_status(titan_manager):
    """Show detailed status information"""
    print("\n📊 Detailed Status:")
    print("-" * 50)
    
    status = titan_manager.get_status()
    detection = titan_manager.detect_google_titan_key()
    
    print(f"Hardware Detection:")
    print(f"  - Google Titan Key Present: {'✅ YES' if status['titan_key_detected'] else '❌ NO'}")
    print(f"  - Device Count: {status['device_count']}")
    
    if detection['devices']:
        for i, device in enumerate(detection['devices']):
            print(f"  - Device {i+1}: {device['FriendlyName']} (Status: {device['Status']})")
    
    print(f"\nRegistration Status:")
    print(f"  - Registered Keys: {status['registered_keys']}")
    
    for key_info in status['registered_key_info']:
        print(f"    * {key_info['nickname']}")
        print(f"      Registered: {key_info['registered_at']}")
        print(f"      Last Used: {key_info['last_used']}")
    
    print(f"\nSecurity Settings:")
    print(f"  - Requirement Enabled: {'✅ YES' if status['requirement_enabled'] else '❌ NO'}")
    
    if status['requirement_enabled']:
        print("  - Admin Access: Password + Titan Key Required")
    else:
        print("  - Admin Access: Password Only")

if __name__ == "__main__":
    print("🚀 Starting Google Titan Security Key Setup...")
    success = main()
    
    if success:
        print("\n🎉 Your Google Titan Security Key is ready!")
        print("🔐 Enhanced security for GuardianShield admin access")
    else:
        print("\n⚠️ Setup needs attention - check messages above")
    
    input("\nPress Enter to exit...")