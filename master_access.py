import getpass
import hashlib
import os
from datetime import datetime

MASTER_KEY = os.getenv('GUARDIAN_MASTER_KEY', '')
if not MASTER_KEY:
    print("❌ GUARDIAN_MASTER_KEY environment variable not set")
    exit(1)

def master_access():
    print("GuardianShield Master Access")
    print("=" * 35)
    
    key = getpass.getpass("Enter Master Key: ")
    
    if key == MASTER_KEY:
        print("MASTER ACCESS GRANTED")
        
        # Create admin session
        timestamp = datetime.now().isoformat()
        session_data = f"master_admin|{timestamp}"
        
        with open('.emergency_admin_session', 'w') as f:
            f.write(session_data)
        
        print("Master admin session created")
        print("Valid for emergency operations")
        
        return True
    else:
        print("ACCESS DENIED")
        return False

def revoke_access():
    """Revoke emergency access"""
    if os.path.exists('.emergency_admin_session'):
        os.remove('.emergency_admin_session')
        print("Emergency access revoked")
    
    if os.path.exists('.emergency_access_control'):
        os.remove('.emergency_access_control')
        print("Access control removed")

def show_status():
    """Show current access status"""
    print("Access Status:")
    
    if os.path.exists('.emergency_access_control'):
        print("   Emergency lockdown: ACTIVE")
    else:
        print("   Emergency lockdown: INACTIVE")
        
    if os.path.exists('.emergency_admin_session'):
        print("   Admin session: ACTIVE")
    else:
        print("   Admin session: INACTIVE")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "revoke":
            revoke_access()
        elif sys.argv[1] == "status":
            show_status()
    else:
        master_access()