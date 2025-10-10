#!/usr/bin/env python3
"""
start_guardianshield.py: Simple startup script for GuardianShield autonomous agents.
"""

import sys
import os

def main():
    """Start GuardianShield system with options"""
    print("🛡️  GuardianShield Autonomous Agent System")
    print("=" * 50)
    print("1. Start full autonomous system")
    print("2. Start admin console only")
    print("3. Run system tests")
    print("4. Exit")
    print("=" * 50)
    
    choice = input("Select option (1-4): ").strip()
    
    if choice == "1":
        print("🚀 Starting full autonomous system...")
        print("💡 Press Ctrl+C to stop")
        from main import main as start_main
        start_main()
        
    elif choice == "2":
        print("🖥️  Starting admin console...")
        os.system("py admin_console.py")
        
    elif choice == "3":
        print("🧪 Running system tests...")
        os.system("py test_system.py")
        
    elif choice == "4":
        print("👋 Goodbye!")
        return
        
    else:
        print("❌ Invalid option. Please select 1-4.")
        main()

if __name__ == "__main__":
    main()