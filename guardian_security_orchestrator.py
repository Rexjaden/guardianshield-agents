"""
🔐 GUARDIAN SHIELD INTEGRATION LAYER
Centralized security orchestration and integration
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

# Import all security components
from guardian_security_system import GuardianSecuritySystem, AuthMethod
from guardian_rbac_system import GuardianRoleBasedAccessControl, UserRole, Permission
from guardian_audit_system import GuardianAuditSystem, EventCategory
from admin_console import AdminConsole

class GuardianSecurityOrchestrator:
    """
    🛡️ GUARDIAN SHIELD SECURITY ORCHESTRATOR
    
    Central coordination point for all security systems:
    - Authentication & Authorization
    - Role-based Access Control  
    - Comprehensive Audit Logging
    - Admin Console Integration
    - Real-time Threat Monitoring
    """
    
    def __init__(self):
        print("\n🔐 Initializing Guardian Shield Security Orchestrator...")
        
        # Initialize core security systems
        self.auth_system = GuardianSecuritySystem()
        self.rbac_system = GuardianRoleBasedAccessControl()
        self.audit_system = GuardianAuditSystem()
        self.admin_console = AdminConsole()
        
        # Security state
        self.active_sessions = {}
        self.security_alerts = []
        
        # Configure logging
        self.logger = logging.getLogger('GuardianOrchestrator')
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - ORCHESTRATOR - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        print("✅ Security Orchestrator initialized successfully!")
        
    def authenticate_user(self, username: str, password: str, totp_token: str = None,
                         source_ip: str = "127.0.0.1", user_agent: str = "Unknown") -> Dict[str, Any]:
        """
        🔐 COMPREHENSIVE USER AUTHENTICATION
        Integrates multi-factor auth with audit logging and session management
        """
        
        start_time = time.time()
        
        # Log authentication attempt
        event_id = self.audit_system.log_event(
            EventCategory.AUTHENTICATION, 'login_attempt', username, 'Unknown',
            source_ip, 'authentication_system', 'login', 'PENDING',
            {'user_agent': user_agent, 'has_totp': totp_token is not None}
        )
        
        try:
            # Attempt authentication
            auth_result = self.auth_system.authenticate_user(
                username, password, totp_token
            )
            
            if auth_result['success']:
                # Get user role for RBAC
                user_role = self._get_user_role(username)
                
                # Create session
                session_token = self._create_secure_session(
                    username, user_role, source_ip, user_agent
                )
                
                # Log successful authentication
                self.audit_system.log_event(
                    EventCategory.AUTHENTICATION, 'login_success', username, user_role.value,
                    source_ip, 'authentication_system', 'login', 'SUCCESS',
                    {
                        'session_duration': time.time() - start_time,
                        'auth_method': 'password_mfa',
                        'user_agent': user_agent
                    },
                    session_token
                )
                
                self.logger.info(f"✅ Successful authentication: {username} from {source_ip}")
                
                return {
                    'success': True,
                    'session_token': session_token,
                    'user_role': user_role.value,
                    'permissions': self.rbac_system.get_user_permissions(username),
                    'message': 'Authentication successful'
                }
                
            else:
                # Log failed authentication
                self.audit_system.log_event(
                    EventCategory.AUTHENTICATION, 'login_failed', username, 'Unknown',
                    source_ip, 'authentication_system', 'login', 'FAILURE',
                    {
                        'failure_reason': auth_result.get('message', 'Unknown'),
                        'user_agent': user_agent
                    }
                )
                
                self.logger.warning(f"❌ Failed authentication: {username} from {source_ip}")
                
                return {
                    'success': False,
                    'message': auth_result.get('message', 'Authentication failed')
                }
                
        except Exception as e:
            # Log authentication error
            self.audit_system.log_event(
                EventCategory.AUTHENTICATION, 'login_error', username, 'Unknown',
                source_ip, 'authentication_system', 'login', 'ERROR',
                {
                    'error_message': str(e),
                    'user_agent': user_agent
                }
            )
            
            self.logger.error(f"🚨 Authentication error for {username}: {e}")
            
            return {
                'success': False,
                'message': 'Authentication system error'
            }
            
    def authorize_action(self, session_token: str, resource: str, action: str,
                        source_ip: str = "127.0.0.1") -> Dict[str, Any]:
        """
        🛡️ COMPREHENSIVE ACTION AUTHORIZATION
        Validates session, checks permissions, and logs all access attempts
        """
        
        # Validate session
        session_info = self._validate_session(session_token)
        if not session_info:
            self.audit_system.log_event(
                EventCategory.AUTHORIZATION, 'invalid_session', 'unknown', 'Unknown',
                source_ip, resource, action, 'FAILURE',
                {'session_token': session_token[:8] + '...', 'reason': 'invalid_session'}
            )
            
            return {
                'success': False,
                'message': 'Invalid or expired session'
            }
            
        username = session_info['username']
        user_role = UserRole(session_info['role'])
        
        try:
            # Check RBAC permissions
            has_permission = self.rbac_system.check_permission(
                username, resource, Permission.from_string(action)
            )
            
            if has_permission:
                # Log successful authorization
                self.audit_system.log_event(
                    EventCategory.AUTHORIZATION, 'access_granted', username, user_role.value,
                    source_ip, resource, action, 'SUCCESS',
                    {
                        'permission_check': True,
                        'resource_access': True
                    },
                    session_token
                )
                
                return {
                    'success': True,
                    'message': 'Access granted'
                }
                
            else:
                # Log authorization failure
                self.audit_system.log_event(
                    EventCategory.AUTHORIZATION, 'access_denied', username, user_role.value,
                    source_ip, resource, action, 'FAILURE',
                    {
                        'permission_check': False,
                        'required_permission': action,
                        'user_permissions': [p.value for p in self.rbac_system.get_user_permissions(username)]
                    },
                    session_token
                )
                
                self.logger.warning(f"🚫 Access denied: {username} -> {resource}:{action}")
                
                return {
                    'success': False,
                    'message': 'Insufficient permissions'
                }
                
        except Exception as e:
            # Log authorization error
            self.audit_system.log_event(
                EventCategory.AUTHORIZATION, 'authorization_error', username, user_role.value,
                source_ip, resource, action, 'ERROR',
                {'error_message': str(e)}
            )
            
            self.logger.error(f"🚨 Authorization error for {username}: {e}")
            
            return {
                'success': False,
                'message': 'Authorization system error'
            }
            
    def secure_admin_action(self, session_token: str, admin_action: str, 
                           params: Dict[str, Any], source_ip: str = "127.0.0.1") -> Dict[str, Any]:
        """
        🔐 SECURE ADMIN ACTION EXECUTION
        High-security wrapper for administrative operations
        """
        
        session_info = self._validate_session(session_token)
        if not session_info or UserRole(session_info['role']) not in [UserRole.MASTER_ADMIN, UserRole.DESIGNATED_ADMIN]:
            self.audit_system.log_event(
                EventCategory.SECURITY, 'unauthorized_admin_access', 
                session_info['username'] if session_info else 'unknown', 
                session_info['role'] if session_info else 'Unknown',
                source_ip, 'admin_system', admin_action, 'FAILURE',
                {'attempted_action': admin_action, 'params': params}
            )
            
            return {
                'success': False,
                'message': 'Admin privileges required'
            }
            
        username = session_info['username']
        user_role = session_info['role']
        
        # Log admin action attempt
        self.audit_system.log_event(
            EventCategory.SYSTEM_ACCESS, 'admin_action_start', username, user_role,
            source_ip, 'admin_system', admin_action, 'PENDING',
            {
                'admin_operation': True,
                'action_params': params,
                'sensitive_operation': True
            },
            session_token
        )
        
        try:
            # Execute admin action with extra security
            result = self._execute_admin_action(admin_action, params, username)
            
            # Log successful admin action
            self.audit_system.log_event(
                EventCategory.SYSTEM_ACCESS, 'admin_action_success', username, user_role,
                source_ip, 'admin_system', admin_action, 'SUCCESS',
                {
                    'admin_operation': True,
                    'action_result': result,
                    'sensitive_operation': True
                },
                session_token
            )
            
            self.logger.info(f"✅ Admin action completed: {admin_action} by {username}")
            
            return {
                'success': True,
                'result': result,
                'message': 'Admin action completed successfully'
            }
            
        except Exception as e:
            # Log admin action failure
            self.audit_system.log_event(
                EventCategory.SYSTEM_ACCESS, 'admin_action_error', username, user_role,
                source_ip, 'admin_system', admin_action, 'ERROR',
                {
                    'admin_operation': True,
                    'error_message': str(e),
                    'sensitive_operation': True
                },
                session_token
            )
            
            self.logger.error(f"🚨 Admin action failed: {admin_action} by {username}: {e}")
            
            return {
                'success': False,
                'message': f'Admin action failed: {str(e)}'
            }
            
    def get_security_status(self, session_token: str) -> Dict[str, Any]:
        """
        📊 GET COMPREHENSIVE SECURITY STATUS
        Only available to admin users
        """
        
        session_info = self._validate_session(session_token)
        if not session_info or UserRole(session_info['role']) not in [UserRole.MASTER_ADMIN, UserRole.DESIGNATED_ADMIN]:
            return {
                'success': False,
                'message': 'Admin access required'
            }
            
        try:
            # Get dashboard data from audit system
            dashboard = self.audit_system.get_security_dashboard(24)
            
            # Add additional security metrics
            security_status = {
                'active_sessions': len(self.active_sessions),
                'failed_logins_24h': dashboard.get('risk_distribution', {}).get('high', 0),
                'security_alerts': len(self.security_alerts),
                'system_health': 'SECURE',
                'audit_dashboard': dashboard,
                'last_updated': datetime.now().isoformat()
            }
            
            return {
                'success': True,
                'security_status': security_status
            }
            
        except Exception as e:
            self.logger.error(f"Error getting security status: {e}")
            return {
                'success': False,
                'message': 'Error retrieving security status'
            }
            
    def emergency_lockdown(self, session_token: str, reason: str, 
                          source_ip: str = "127.0.0.1") -> Dict[str, Any]:
        """
        🚨 EMERGENCY SYSTEM LOCKDOWN
        Only available to master admin
        """
        
        session_info = self._validate_session(session_token)
        if not session_info or UserRole(session_info['role']) != UserRole.MASTER_ADMIN:
            return {
                'success': False,
                'message': 'Master admin access required for emergency lockdown'
            }
            
        username = session_info['username']
        
        # Log emergency lockdown
        self.audit_system.log_event(
            EventCategory.SECURITY, 'emergency_lockdown', username, 'MASTER_ADMIN',
            source_ip, 'security_system', 'emergency_lockdown', 'SUCCESS',
            {
                'lockdown_reason': reason,
                'initiated_by': username,
                'emergency_action': True,
                'system_wide_impact': True
            },
            session_token
        )
        
        # Terminate all sessions except master admin
        terminated_sessions = 0
        for token, session in list(self.active_sessions.items()):
            if session['role'] != 'MASTER_ADMIN':
                del self.active_sessions[token]
                terminated_sessions += 1
                
        self.logger.critical(f"🚨 EMERGENCY LOCKDOWN initiated by {username}: {reason}")
        
        return {
            'success': True,
            'message': 'Emergency lockdown activated',
            'terminated_sessions': terminated_sessions
        }
        
    def _get_user_role(self, username: str) -> UserRole:
        """Determine user role - integrate with your user database"""
        # For demo purposes, hardcode some roles
        admin_users = ['admin', 'administrator', 'guardian_admin']
        if username in admin_users:
            return UserRole.MASTER_ADMIN
        else:
            return UserRole.OPERATOR
            
    def _create_secure_session(self, username: str, user_role: UserRole, 
                             source_ip: str, user_agent: str) -> str:
        """Create secure session with comprehensive tracking"""
        
        session_token = self.auth_system._generate_session_token(username)
        
        self.active_sessions[session_token] = {
            'username': username,
            'role': user_role.value,
            'source_ip': source_ip,
            'user_agent': user_agent,
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat()
        }
        
        return session_token
        
    def _validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Validate session token and update last activity"""
        
        if session_token in self.active_sessions:
            session_info = self.active_sessions[session_token]
            session_info['last_activity'] = datetime.now().isoformat()
            return session_info
            
        return None
        
    def _execute_admin_action(self, action: str, params: Dict[str, Any], username: str) -> Any:
        """Execute administrative action with proper security"""
        
        if action == 'create_user':
            return self._admin_create_user(params, username)
        elif action == 'modify_permissions':
            return self._admin_modify_permissions(params, username)
        elif action == 'system_config':
            return self._admin_system_config(params, username)
        else:
            raise ValueError(f"Unknown admin action: {action}")
            
    def _admin_create_user(self, params: Dict[str, Any], admin_user: str) -> Dict[str, Any]:
        """Create new user with proper validation"""
        
        username = params.get('username')
        role = params.get('role', 'OPERATOR')
        
        if not username:
            raise ValueError("Username is required")
            
        # Create user in auth system
        result = self.auth_system.create_user(username, params.get('password'))
        
        # Set user role in RBAC system
        self.rbac_system.assign_user_role(username, UserRole(role))
        
        return {
            'username': username,
            'role': role,
            'created_by': admin_user,
            'status': 'created'
        }
        
    def _admin_modify_permissions(self, params: Dict[str, Any], admin_user: str) -> Dict[str, Any]:
        """Modify user permissions"""
        
        username = params.get('username')
        new_role = params.get('role')
        
        if not username or not new_role:
            raise ValueError("Username and role are required")
            
        # Update role in RBAC system
        self.rbac_system.assign_user_role(username, UserRole(new_role))
        
        return {
            'username': username,
            'new_role': new_role,
            'modified_by': admin_user,
            'status': 'updated'
        }
        
    def _admin_system_config(self, params: Dict[str, Any], admin_user: str) -> Dict[str, Any]:
        """Modify system configuration"""
        
        config_key = params.get('key')
        config_value = params.get('value')
        
        if not config_key:
            raise ValueError("Configuration key is required")
            
        # Store configuration (implement proper config management)
        return {
            'config_key': config_key,
            'config_value': config_value,
            'modified_by': admin_user,
            'status': 'updated'
        }


def main():
    """Test the security orchestrator"""
    print("\n🛡️ TESTING GUARDIAN SHIELD SECURITY ORCHESTRATOR")
    print("=" * 60)
    
    # Initialize orchestrator
    orchestrator = GuardianSecurityOrchestrator()
    
    print("\n1️⃣ Testing user authentication...")
    
    # Test authentication (will fail without proper setup)
    auth_result = orchestrator.authenticate_user(
        'admin', 'test_password', source_ip='192.168.1.100'
    )
    print(f"   Authentication result: {auth_result['success']}")
    
    if auth_result['success']:
        session_token = auth_result['session_token']
        
        print("\n2️⃣ Testing authorization...")
        
        # Test authorization
        auth_result = orchestrator.authorize_action(
            session_token, 'admin_panel', 'read'
        )
        print(f"   Authorization result: {auth_result['success']}")
        
        print("\n3️⃣ Testing security status...")
        
        # Get security status
        status = orchestrator.get_security_status(session_token)
        if status['success']:
            print(f"   Active sessions: {status['security_status']['active_sessions']}")
            
    print("\n🎉 Security orchestrator test completed!")
    

if __name__ == "__main__":
    main()