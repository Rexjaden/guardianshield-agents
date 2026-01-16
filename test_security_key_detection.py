"""
Simple Security Key Detection Test
Tests if K51T Titan Security Key can be detected
"""

import sys
import os

def test_security_key_detection():
    print("🔍 Testing Security Key Detection")
    print("=" * 40)
    
    # Test Windows USB device detection
    try:
        import subprocess
        result = subprocess.run([
            'powershell', '-Command',
            "Get-PnpDevice | Where-Object {$_.InstanceId -like '*VID_18D1*'} | Format-List FriendlyName, Status, Present"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and result.stdout.strip():
            print("✅ Google devices detected:")
            print(result.stdout)
            return True
        else:
            print("⚠️ No Google security keys detected")
            return False
            
    except Exception as e:
        print(f"❌ Detection failed: {e}")
        return False

def test_fido2_import():
    print("\n📦 Testing FIDO2 Library Import")
    print("=" * 40)
    
    try:
        from fido2.hid import CtapHidDevice
        from fido2.client import Fido2Client
        print("✅ FIDO2 libraries imported successfully")
        
        # Try to list devices
        try:
            devices = list(CtapHidDevice.list_devices())
            print(f"✅ Found {len(devices)} FIDO2 devices")
            for i, device in enumerate(devices):
                print(f"  {i+1}. Device: {device}")
            return len(devices) > 0
        except Exception as e:
            print(f"⚠️ Device enumeration failed: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ FIDO2 import failed: {e}")
        return False

def main():
    print("🛡️ GuardianShield K51T Security Key Detection Test")
    print("=" * 60)
    
    # Test 1: Windows device detection
    windows_detected = test_security_key_detection()
    
    # Test 2: FIDO2 library test
    fido2_working = test_fido2_import()
    
    print("\n📊 Test Results:")
    print("=" * 30)
    print(f"Windows Detection: {'✅ PASS' if windows_detected else '❌ FAIL'}")
    print(f"FIDO2 Library: {'✅ PASS' if fido2_working else '❌ FAIL'}")
    
    if windows_detected and fido2_working:
        print("\n🎉 Your K51T Titan Security Key is ready!")
        print("🔧 Next steps:")
        print("   1. Insert your security key")
        print("   2. Set up web-based registration")
        print("   3. Test authentication flow")
    elif windows_detected:
        print("\n⚠️ Key detected but FIDO2 libraries need fixing")
        print("💡 Try: pip install --upgrade cryptography fido2")
    else:
        print("\n❌ Security key not detected")
        print("💡 Ensure your K51T Titan key is inserted and recognized")

if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")