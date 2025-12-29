"""
🔐 GUARDIAN SHIELD SECURITY INTEGRATION
Simple integration layer to coordinate all security components without duplication
"""

import logging
from typing import Dict, Any, Optional

# Import existing components
try:
    from admin_console import AdminConsole
    from guardian_security_system import GuardianSecuritySystem, AuthMethod
    from guardian_rbac_system import GuardianRoleBasedAccessControl, UserRole, Permission
    from guardian_audit_system import GuardianAuditSystem, EventCategory
    SECURITY_AVAILABLE = True
except ImportError as e:
    SECURITY_AVAILABLE = False
    print(f"⚠️ Security components not fully available: {e}")

class GuardianSecurityManager:
    """
    🛡️ UNIFIED SECURITY MANAGER
    
    Simple coordination layer that:
    - Uses existing AdminConsole (no duplication)
    - Coordinates security components
    - Provides unified security interface
    - Maintains single point of control
    """
    
    def __init__(self):
        self.logger = logging.getLogger('GuardianSecurity')
        
        # Initialize existing admin console (no duplication)
        self.admin_console = AdminConsole()
        
        # Reference to security systems (if available)
        if SECURITY_AVAILABLE:
            self.auth_system = self.admin_console.auth_system if hasattr(self.admin_console, 'auth_system') else None
            self.rbac_system = self.admin_console.rbac_system if hasattr(self.admin_console, 'rbac_system') else None
            self.audit_system = self.admin_console.audit_system if hasattr(self.admin_console, 'audit_system') else None
            self.security_enabled = self.admin_console.security_enabled
        else:
            self.auth_system = None
            self.rbac_system = None
            self.audit_system = None
            self.security_enabled = False
            
        self.logger.info("🔐 Security Manager initialized - delegating to existing AdminConsole")
    
    def launch_secure_admin_console(self):
        """
        🚀 LAUNCH SECURE ADMIN CONSOLE
        Uses existing admin_console.py with integrated security
        """
        print("\n🔐 LAUNCHING GUARDIAN SHIELD SECURE ADMIN CONSOLE")
        print("=" * 55)
        
        if self.security_enabled:
            print("✅ Full security features enabled")
            print("   - Multi-factor authentication")
            print("   - Role-based access control")
            print("   - Comprehensive audit logging")
            print("   - Real-time threat monitoring")
        else:
            print("⚠️ Basic mode - security features limited")
            
        print("\n🚀 Starting admin console...")
        print("   (Use Ctrl+C to exit)")
        
        # Launch the existing admin console directly
        try:
            import subprocess
            import sys
            subprocess.run([sys.executable, 'admin_console.py'], cwd='.')
                
        except Exception as e:
            self.logger.error(f"Error launching admin console: {e}")
            print(f"❌ Error launching admin console: {e}")
            print("\n💡 You can also run directly: python admin_console.py")
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get comprehensive security status"""
        
        status = {
            'security_enabled': self.security_enabled,
            'admin_console_available': True,
            'components': {
                'authentication': bool(self.auth_system),
                'authorization': bool(self.rbac_system), 
                'audit_logging': bool(self.audit_system)
            }
        }
        
        if self.security_enabled and self.admin_console.current_user:
            status.update({
                'current_user': self.admin_console.current_user,
                'current_role': self.admin_console.current_role.value if self.admin_console.current_role else None,
                'session_valid': self.admin_console.check_session_valid()
            })
            
        return status
    
    def emergency_lockdown(self, reason: str = "Security Manager Override"):
        """
        🚨 EMERGENCY LOCKDOWN
        Delegates to existing admin console functionality
        """
        print(f"\n🚨 EMERGENCY LOCKDOWN INITIATED: {reason}")
        
        if self.admin_console:
            try:
                self.admin_console.emergency_stop_all_agents()
                self.logger.critical(f"Emergency lockdown executed: {reason}")
                return True
            except Exception as e:
                self.logger.error(f"Error executing emergency lockdown: {e}")
                return False
        else:
            print("❌ Admin console not available for emergency lockdown")
            return False


def main():
    """Quick security integration test"""
    print("\n🔐 GUARDIAN SHIELD SECURITY INTEGRATION TEST")
    print("=" * 50)
    
    # Initialize security manager
    manager = GuardianSecurityManager()
    
    # Show security status
    status = manager.get_security_status()
    print(f"\n📊 Security Status:")
    print(f"   Security Enabled: {status['security_enabled']}")
    print(f"   Admin Console: {status['admin_console_available']}")
    print(f"   Components: {status['components']}")
    
    print(f"\n✅ Security integration ready!")
    print(f"   Use existing admin_console.py for all admin operations")
    print(f"   All security features integrated without duplication")
    
    # Optionally launch admin console
    launch = input("\n🚀 Launch secure admin console? (y/n): ").lower().strip()
    if launch == 'y':
        manager.launch_secure_admin_console()


if __name__ == "__main__":
    main()