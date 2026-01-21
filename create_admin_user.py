import json
import hashlib
import os
from datetime import datetime

def create_admin_user(username, password):
    # Hash format used by SecurityManager
    # provided_hash = hashlib.sha256(f"guardian_user_{password}".encode()).hexdigest()
    password_hash = hashlib.sha256(f"guardian_user_{password}".encode()).hexdigest()
    
    user_data = {
        "role": "admin",
        "permissions": ["all", "monitoring", "control"],
        "created": datetime.now().isoformat(),
        "active": True,
        "password_hash": password_hash
    }
    
    users_file = ".guardian_authorized_users.json"
    
    # Load existing users
    if os.path.exists(users_file):
        try:
            with open(users_file, 'r') as f:
                users = json.load(f)
        except:
            users = {}
    else:
        users = {}
        
    # Add/Update user
    users[username] = user_data
    
    # Check for master_admin (required by some logic)
    if "master_admin" not in users:
         users["master_admin"] = {
            "role": "master",
            "permissions": ["all"],
            "created": datetime.now().isoformat(),
            "active": True
            # master_admin uses a different file for password usually, but adding here doesn't hurt
        }

    with open(users_file, 'w') as f:
        json.dump(users, f, indent=2)
        
    print(f"✅ Created/Updated Admin User: '{username}'")
    print(f"✅ Password set to: '{password}'")
    print(f"📁 Saved to {users_file}")

if __name__ == "__main__":
    create_admin_user("admin", "GuardShield2026!")
