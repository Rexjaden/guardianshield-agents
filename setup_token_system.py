#!/usr/bin/env python3
"""
GuardianShield Token System Setup
Installs required dependencies and initializes the token system
"""

import subprocess
import sys
import os

def run_command(command):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {command}")
            return True
        else:
            print(f"❌ {command}")
            print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {command}")
        print(f"   Exception: {e}")
        return False

def install_requirements():
    """Install required Python packages"""
    print("📦 Installing Python packages...")
    
    packages = [
        'fastapi',
        'uvicorn[standard]',
        'pydantic'
    ]
    
    success = True
    for package in packages:
        if not run_command(f"pip install {package}"):
            success = False
    
    return success

def initialize_database():
    """Initialize the token database"""
    print("\n🗄️  Initializing token database...")
    
    try:
        from shield_token_serial_system import ShieldTokenSerial
        serial_system = ShieldTokenSerial()
        
        # Test the system
        print("🧪 Testing token system...")
        test_result = serial_system.mint_token_serial("0x1234567890abcdef")
        
        if test_result['success']:
            print(f"✅ Database initialized and tested")
            print(f"   Test token serial: {test_result['serial_number']}")
            return True
        else:
            print(f"❌ Database test failed: {test_result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def create_batch_file():
    """Create a Windows batch file for easy launching"""
    batch_content = '''@echo off
echo GuardianShield Token System Launcher
echo ====================================
python launch_token_system.py
pause
'''
    
    try:
        with open('launch_tokens.bat', 'w') as f:
            f.write(batch_content)
        print("✅ Created launch_tokens.bat for Windows users")
        return True
    except Exception as e:
        print(f"❌ Failed to create batch file: {e}")
        return False

def main():
    print("🛡️  GuardianShield Token System Setup")
    print("=" * 50)
    
    print("🔧 System Requirements Check:")
    print(f"   Python Version: {sys.version}")
    print(f"   Working Directory: {os.getcwd()}")
    
    # Check if required files exist
    required_files = [
        'shield_token_serial_system.py',
        'shield_serial_api.py',
        'launch_token_system.py',
        'token_management.html'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} (missing)")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n❌ Missing required files. Please ensure all files are in the current directory.")
        return False
    
    # Install requirements
    print(f"\n📦 Installing Dependencies...")
    if not install_requirements():
        print(f"\n❌ Failed to install some packages. Please check your pip installation.")
        return False
    
    # Initialize database
    print(f"\n🗄️  Setting up Database...")
    if not initialize_database():
        print(f"\n❌ Database setup failed. Please check the error messages above.")
        return False
    
    # Create convenience batch file
    if os.name == 'nt':  # Windows
        create_batch_file()
    
    # Final success message
    print(f"\n🎉 Setup Complete!")
    print(f"\nTo start the token system:")
    print(f"   python launch_token_system.py")
    
    if os.name == 'nt':
        print(f"   OR double-click launch_tokens.bat")
    
    print(f"\nOnce running, visit:")
    print(f"   Token Management: http://localhost:8081/token_management.html")
    print(f"   Token Verification: http://localhost:8080/serial-checker")
    print(f"   API Documentation: http://localhost:8080/docs")
    
    return True

if __name__ == "__main__":
    success = main()
    
    if not success:
        print(f"\n❌ Setup failed. Please resolve the issues above and try again.")
        sys.exit(1)
    else:
        print(f"\n✅ Ready to launch GuardianShield Token System!")
        
        # Ask if user wants to start now
        try:
            choice = input(f"\nStart the token system now? (y/n): ").lower()
            if choice in ['y', 'yes']:
                print(f"\n🚀 Launching token system...")
                os.system('python launch_token_system.py')
        except KeyboardInterrupt:
            print(f"\n👋 Setup complete. Run 'python launch_token_system.py' when ready.")