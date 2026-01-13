import os
from datetime import datetime

def check_security_status():
    print("GuardianShield Security Status")
    print("=" * 40)
    print(f"Time: {datetime.now()}")
    print()
    
    # Check for emergency mode
    if os.path.exists('.emergency_access_control'):
        print("EMERGENCY MODE: ACTIVE")
        print("All vulnerable endpoints BLOCKED")
    else:
        print("EMERGENCY MODE: INACTIVE")
    
    # Check for admin session
    if os.path.exists('.emergency_admin_session'):
        print("Emergency admin session: ACTIVE")
    else:
        print("Emergency admin session: INACTIVE")
    
    print()
    print("Security Recommendations:")
    print("1. Implement authentication on all API endpoints")
    print("2. Add input validation and SQL parameterization")  
    print("3. Move secrets to environment variables")
    print("4. Enable HTTPS and rate limiting")
    print()

if __name__ == "__main__":
    check_security_status()