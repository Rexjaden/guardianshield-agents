#!/usr/bin/env python3
"""
setup_environment.py: Environment setup and validation helper for GuardianShield
"""

import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """Check if Python version meets requirements"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.7+")
        return False

def check_optional_dependencies():
    """Check which optional dependencies are available"""
    optional_deps = {
        'cryptography': 'Enhanced security features',
        'web3': 'Blockchain integration',
        'fastapi': 'API server functionality',
        'scikit-learn': 'Machine learning capabilities',
        'requests': 'HTTP requests',
        'aiohttp': 'Async HTTP operations'
    }
    
    available = {}
    print("\n🔍 Checking optional dependencies:")
    
    for dep, description in optional_deps.items():
        try:
            __import__(dep)
            print(f"✅ {dep:15} - {description}")
            available[dep] = True
        except ImportError:
            print(f"⚠️  {dep:15} - {description} (optional, will use fallback)")
            available[dep] = False
    
    return available

def install_dependencies():
    """Install dependencies if user wants to"""
    print("\n📦 Would you like to install optional dependencies for enhanced features?")
    print("1. Yes - Install all recommended dependencies")
    print("2. Minimal - Install only core dependencies") 
    print("3. No - Continue with current setup")
    
    choice = input("Choice (1-3): ").strip()
    
    if choice == "1":
        print("📥 Installing all dependencies...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ Dependencies installed successfully!")
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies. You can install manually with:")
            print("   pip install -r requirements.txt")
    elif choice == "2":
        core_deps = ["fastapi", "uvicorn", "requests", "cryptography"]
        print("📥 Installing core dependencies...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + core_deps)
            print("✅ Core dependencies installed!")
        except subprocess.CalledProcessError:
            print("❌ Failed to install core dependencies")

def create_env_file():
    """Create basic .env file if it doesn't exist"""
    env_file = Path(".env")
    if not env_file.exists():
        print("\n📄 Creating basic .env configuration file...")
        env_content = """# GuardianShield Configuration
# Agent settings
AGENT_AUTONOMY_LEVEL=10
AUTO_EVOLUTION_ENABLED=true
UNLIMITED_IMPROVEMENT=true

# Security
GUARDIAN_PASSWORD=change_this_password
ENCRYPTION_PASSWORD=change_this_encryption_key

# Monitoring
CRITICAL_ACTION_THRESHOLD=8
MONITORING_INTERVAL=30

# API Settings
API_HOST=localhost
API_PORT=8000
"""
        env_file.write_text(env_content)
        print("✅ Created .env file with default settings")
        print("🔒 Please update passwords in .env file before production use!")

def main():
    """Main setup function"""
    print("🛡️  GuardianShield Environment Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        print("\n❌ Python version incompatible. Please upgrade to Python 3.7+")
        return False
    
    # Check dependencies
    available_deps = check_optional_dependencies()
    
    # Show system status
    print(f"\n📊 System Status:")
    print(f"✅ Core system: Ready (requires only Python 3.7+)")
    available_count = sum(available_deps.values())
    total_count = len(available_deps)
    print(f"🔧 Optional features: {available_count}/{total_count} available")
    
    if available_count < total_count:
        install_dependencies()
    
    # Create env file
    create_env_file()
    
    print("\n🎯 Setup Complete!")
    print("Next steps:")
    print("1. Review and update .env file settings")
    print("2. Run: python start_guardianshield.py")
    print("3. Or run tests: python test_system.py")
    
    return True

if __name__ == "__main__":
    main()