#!/usr/bin/env python3
"""
start_guardianshield.py: Enhanced startup script for GuardianShield autonomous agents.
"""

import sys
import os
import subprocess

def check_python_availability():
    """Check which Python commands are available"""
    python_commands = ['python', 'python3', 'py']
    
    for cmd in python_commands:
        try:
            result = subprocess.run([cmd, '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return cmd
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue
    
    return None

def run_python_script(script_name, python_cmd='python'):
    """Run a Python script with the best available Python command"""
    try:
        if python_cmd:
            subprocess.run([python_cmd, script_name])
        else:
            print(f"❌ Could not find Python interpreter to run {script_name}")
            print("Please ensure Python 3.7+ is installed and available in PATH")
    except Exception as e:
        print(f"❌ Error running {script_name}: {e}")

def main():
    """Start GuardianShield system with options"""
    print("🛡️  GuardianShield Autonomous Agent System")
    print("=" * 50)
    
    # Check Python availability
    python_cmd = check_python_availability()
    if not python_cmd:
        print("❌ Python not found! Please install Python 3.7+ or run setup_environment.py")
        input("Press Enter to exit...")
        return
    
    print("✅ Using Python command: {python_cmd}")
    print("=" * 50)
    print("1. Start full autonomous system")
    print("2. Start admin console only") 
    print("3. Launch web dashboard")
    print("4. Run system tests")
    print("5. Setup environment")
    print("6. Exit")
    print("=" * 50)
    
    choice = input("Select option (1-6): ").strip()
    
    if choice == "1":
        print("🚀 Starting full autonomous system...")
        print("💡 Press Ctrl+C to stop")
        from main import main as start_main
        start_main()
        
    elif choice == "2":
        print("🖥️  Starting admin console...")
        run_python_script("admin_console.py", python_cmd)
        
    elif choice == "3":
        print("🌐 Launching web dashboard...")
        run_python_script("launch_dashboard.py", python_cmd)
        
    elif choice == "4":
        print("🧪 Running system tests...")
        run_python_script("test_system.py", python_cmd)
        
    elif choice == "5":
        print("🔧 Running environment setup...")
        run_python_script("setup_environment.py", python_cmd)
        
    elif choice == "6":
        print("👋 Goodbye!")
        return
        
    else:
        print("❌ Invalid option. Please select 1-6.")
        main()

if __name__ == "__main__":
    main()