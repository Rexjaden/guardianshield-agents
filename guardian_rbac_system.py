"""
🛡️ GUARDIAN SHIELD ROLE-BASED ACCESS CONTROL SYSTEM
Advanced permission management with hierarchical roles and granular controls
"""

import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict
import logging

class PermissionLevel(Enum):
    """Permission levels from lowest to highest"""
    NONE = 0
    READ = 1
    WRITE = 2
    ADMIN = 3
    MASTER = 4

class ResourceType(Enum):
    """Types of resources that can be protected"""
    SYSTEM = "system"
    AGENTS = "agents" 
    CONTRACTS = "contracts"
    TOKENS = "tokens"
    ANALYTICS = "analytics"
    SECURITY = "security"
    AUDIT = "audit"
    USERS = "users"
    API = "api"
    BLOCKCHAIN = "blockchain"

@dataclass
class Permission:
    """Individual permission definition"""
    resource: ResourceType
    action: str
    level: PermissionLevel
    description: str
    
@dataclass
class Role:
    """Role definition with permissions"""
    name: str
    description: str
    permissions: List[Permission]
    inherits_from: Optional[str] = None
    created_at: datetime = None
    created_by: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class UserRole:
    """User role assignment"""
    username: str
    role_name: str
    granted_by: str
    granted_at: datetime
    expires_at: Optional[datetime] = None
    conditions: Optional[Dict[str, Any]] = None


class GuardianRoleBasedAccessControl:
    """
    🔐 COMPREHENSIVE ROLE-BASED ACCESS CONTROL SYSTEM
    
    Features:
    - Hierarchical role inheritance
    - Granular permission control
    - Time-based access controls
    - Conditional permissions
    - Real-time permission checking
    - Comprehensive audit logging
    - Dynamic permission updates
    """
    
    def __init__(self):
        self.roles: Dict[str, Role] = {}
        self.user_roles: Dict[str, List[UserRole]] = {}
        self.permission_cache: Dict[str, Dict] = {}
        self.access_logs: List[Dict] = []
        
        # Initialize default roles and permissions
        self._initialize_default_roles()
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup permission logging"""
        self.logger = logging.getLogger('GuardianRBAC')
        self.logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler('guardian_permissions.log')
        formatter = logging.Formatter('%(asctime)s - RBAC - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
    def _initialize_default_roles(self):
        """Initialize the default role hierarchy"""
        
        # 👑 MASTER ADMIN ROLE (Supreme access)
        master_permissions = [
            Permission(ResourceType.SYSTEM, "full_control", PermissionLevel.MASTER, "Complete system control"),
            Permission(ResourceType.SECURITY, "emergency_lockdown", PermissionLevel.MASTER, "Emergency system lockdown"),
            Permission(ResourceType.SECURITY, "manage_admins", PermissionLevel.MASTER, "Add/remove administrators"),
            Permission(ResourceType.SECURITY, "security_config", PermissionLevel.MASTER, "Modify security settings"),
            Permission(ResourceType.USERS, "manage_all", PermissionLevel.MASTER, "Manage all user accounts"),
            Permission(ResourceType.AUDIT, "view_all", PermissionLevel.MASTER, "View all audit logs"),
            Permission(ResourceType.CONTRACTS, "deploy", PermissionLevel.MASTER, "Deploy smart contracts"),
            Permission(ResourceType.TOKENS, "mint_burn", PermissionLevel.MASTER, "Mint and burn tokens"),
            Permission(ResourceType.AGENTS, "full_control", PermissionLevel.MASTER, "Full agent control"),
            Permission(ResourceType.ANALYTICS, "full_access", PermissionLevel.MASTER, "Complete analytics access"),
            Permission(ResourceType.API, "admin_endpoints", PermissionLevel.MASTER, "Access admin API endpoints"),
            Permission(ResourceType.BLOCKCHAIN, "admin_operations", PermissionLevel.MASTER, "Blockchain admin operations"),
        ]
        
        self.roles["MASTER_ADMIN"] = Role(
            name="MASTER_ADMIN",
            description="Master Administrator - Supreme system access",
            permissions=master_permissions,
            created_by="SYSTEM"
        )
        
        # 🔧 DESIGNATED ADMIN ROLE
        admin_permissions = [
            Permission(ResourceType.SYSTEM, "monitor", PermissionLevel.ADMIN, "Monitor system status"),
            Permission(ResourceType.AGENTS, "manage", PermissionLevel.ADMIN, "Manage agents"),
            Permission(ResourceType.CONTRACTS, "interact", PermissionLevel.ADMIN, "Interact with contracts"),
            Permission(ResourceType.TOKENS, "transfer", PermissionLevel.ADMIN, "Transfer tokens"),
            Permission(ResourceType.ANALYTICS, "view", PermissionLevel.ADMIN, "View analytics"),
            Permission(ResourceType.AUDIT, "view_own", PermissionLevel.READ, "View own audit logs"),
            Permission(ResourceType.API, "standard_endpoints", PermissionLevel.ADMIN, "Access standard API"),
            Permission(ResourceType.BLOCKCHAIN, "read_operations", PermissionLevel.READ, "Read blockchain data"),
        ]
        
        self.roles["DESIGNATED_ADMIN"] = Role(
            name="DESIGNATED_ADMIN", 
            description="Designated Administrator - Standard admin access",
            permissions=admin_permissions,
            created_by="SYSTEM"
        )
        
        # ⚙️ OPERATOR ROLE
        operator_permissions = [
            Permission(ResourceType.AGENTS, "operate", PermissionLevel.WRITE, "Operate agents"),
            Permission(ResourceType.ANALYTICS, "view", PermissionLevel.READ, "View analytics"),
            Permission(ResourceType.TOKENS, "view", PermissionLevel.READ, "View token information"),
            Permission(ResourceType.CONTRACTS, "view", PermissionLevel.READ, "View contract data"),
            Permission(ResourceType.API, "user_endpoints", PermissionLevel.WRITE, "Access user API"),
            Permission(ResourceType.BLOCKCHAIN, "read_operations", PermissionLevel.READ, "Read blockchain data"),
        ]
        
        self.roles["OPERATOR"] = Role(
            name="OPERATOR",
            description="System Operator - Limited operational access", 
            permissions=operator_permissions,
            created_by="SYSTEM"
        )
        
        # 👀 VIEWER ROLE
        viewer_permissions = [
            Permission(ResourceType.ANALYTICS, "view", PermissionLevel.READ, "View analytics"),
            Permission(ResourceType.TOKENS, "view", PermissionLevel.READ, "View token information"),
            Permission(ResourceType.CONTRACTS, "view", PermissionLevel.READ, "View contract data"),
            Permission(ResourceType.API, "read_endpoints", PermissionLevel.READ, "Read-only API access"),
            Permission(ResourceType.BLOCKCHAIN, "read_operations", PermissionLevel.READ, "Read blockchain data"),
        ]
        
        self.roles["VIEWER"] = Role(
            name="VIEWER",
            description="Read-Only Viewer - View access only",
            permissions=viewer_permissions,
            created_by="SYSTEM"
        )
        
        # 🚫 GUEST ROLE (Minimal access)
        guest_permissions = [
            Permission(ResourceType.SYSTEM, "status", PermissionLevel.READ, "View system status"),
            Permission(ResourceType.API, "public_endpoints", PermissionLevel.READ, "Public API access only"),
        ]
        
        self.roles["GUEST"] = Role(
            name="GUEST",
            description="Guest Access - Minimal read-only access",
            permissions=guest_permissions,
            created_by="SYSTEM"
        )
        
    def create_custom_role(self, role_name: str, description: str, permissions: List[Permission], 
                          created_by: str, inherits_from: Optional[str] = None) -> bool:
        """
        🎯 CREATE CUSTOM ROLE
        """
        try:
            if role_name in self.roles:
                raise ValueError(f"Role '{role_name}' already exists")
                
            # Validate inheritance
            if inherits_from and inherits_from not in self.roles:
                raise ValueError(f"Parent role '{inherits_from}' does not exist")
                
            new_role = Role(
                name=role_name,
                description=description,
                permissions=permissions,
                inherits_from=inherits_from,
                created_by=created_by
            )
            
            self.roles[role_name] = new_role
            
            self._log_access_event("ROLE_CREATED", {
                "role_name": role_name,
                "created_by": created_by,
                "permissions_count": len(permissions)
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create role {role_name}: {e}")
            return False
            
    def assign_role_to_user(self, username: str, role_name: str, granted_by: str,
                           expires_at: Optional[datetime] = None,
                           conditions: Optional[Dict[str, Any]] = None) -> bool:
        """
        👤 ASSIGN ROLE TO USER
        """
        try:
            if role_name not in self.roles:
                raise ValueError(f"Role '{role_name}' does not exist")
                
            user_role = UserRole(
                username=username,
                role_name=role_name,
                granted_by=granted_by,
                granted_at=datetime.now(),
                expires_at=expires_at,
                conditions=conditions
            )
            
            if username not in self.user_roles:
                self.user_roles[username] = []
                
            self.user_roles[username].append(user_role)
            
            # Clear permission cache for this user
            self._clear_user_cache(username)
            
            self._log_access_event("ROLE_ASSIGNED", {
                "username": username,
                "role_name": role_name,
                "granted_by": granted_by,
                "expires_at": expires_at.isoformat() if expires_at else None
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to assign role {role_name} to {username}: {e}")
            return False
            
    def revoke_user_role(self, username: str, role_name: str, revoked_by: str) -> bool:
        """
        🚫 REVOKE USER ROLE
        """
        try:
            if username not in self.user_roles:
                return False
                
            original_count = len(self.user_roles[username])
            
            self.user_roles[username] = [
                ur for ur in self.user_roles[username] 
                if ur.role_name != role_name
            ]
            
            if len(self.user_roles[username]) < original_count:
                self._clear_user_cache(username)
                
                self._log_access_event("ROLE_REVOKED", {
                    "username": username,
                    "role_name": role_name,
                    "revoked_by": revoked_by
                })
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to revoke role {role_name} from {username}: {e}")
            return False
            
    def check_permission(self, username: str, resource: ResourceType, action: str, 
                        required_level: PermissionLevel = PermissionLevel.READ,
                        context: Optional[Dict[str, Any]] = None) -> bool:
        """
        🔍 CHECK USER PERMISSION
        
        This is the core permission checking function
        """
        try:
            # Check cache first
            cache_key = f"{username}_{resource.value}_{action}_{required_level.value}"
            if cache_key in self.permission_cache:
                cached_result = self.permission_cache[cache_key]
                if cached_result["expires"] > time.time():
                    return cached_result["allowed"]
                    
            # Get user's effective permissions
            user_permissions = self._get_user_permissions(username)
            
            # Check if user has required permission
            allowed = self._has_permission(user_permissions, resource, action, required_level)
            
            # Apply conditional logic if needed
            if allowed and context:
                allowed = self._check_conditions(username, resource, action, context)
                
            # Cache the result (5 minute cache)
            self.permission_cache[cache_key] = {
                "allowed": allowed,
                "expires": time.time() + 300  # 5 minutes
            }
            
            # Log permission check
            self._log_access_event("PERMISSION_CHECK", {
                "username": username,
                "resource": resource.value,
                "action": action,
                "required_level": required_level.value,
                "allowed": allowed
            })
            
            return allowed
            
        except Exception as e:
            self.logger.error(f"Permission check failed for {username}: {e}")
            return False
            
    def _get_user_permissions(self, username: str) -> List[Permission]:
        """Get all effective permissions for a user"""
        all_permissions = []
        
        if username not in self.user_roles:
            return all_permissions
            
        for user_role in self.user_roles[username]:
            # Check if role assignment is still valid
            if not self._is_role_assignment_valid(user_role):
                continue
                
            # Get role permissions
            role = self.roles.get(user_role.role_name)
            if not role:
                continue
                
            all_permissions.extend(role.permissions)
            
            # Add inherited permissions
            inherited_permissions = self._get_inherited_permissions(role)
            all_permissions.extend(inherited_permissions)
            
        # Remove duplicates
        unique_permissions = []
        seen = set()
        for perm in all_permissions:
            perm_key = f"{perm.resource.value}_{perm.action}"
            if perm_key not in seen:
                unique_permissions.append(perm)
                seen.add(perm_key)
                
        return unique_permissions
        
    def _get_inherited_permissions(self, role: Role) -> List[Permission]:
        """Get permissions from inherited roles"""
        inherited_permissions = []
        
        if role.inherits_from:
            parent_role = self.roles.get(role.inherits_from)
            if parent_role:
                inherited_permissions.extend(parent_role.permissions)
                # Recursively get permissions from parent's parents
                inherited_permissions.extend(self._get_inherited_permissions(parent_role))
                
        return inherited_permissions
        
    def _has_permission(self, user_permissions: List[Permission], resource: ResourceType, 
                       action: str, required_level: PermissionLevel) -> bool:
        """Check if user permissions include the required permission"""
        
        for permission in user_permissions:
            if (permission.resource == resource and 
                (permission.action == action or permission.action == "full_control") and
                permission.level.value >= required_level.value):
                return True
                
        return False
        
    def _is_role_assignment_valid(self, user_role: UserRole) -> bool:
        """Check if a role assignment is still valid"""
        
        # Check expiration
        if user_role.expires_at and datetime.now() > user_role.expires_at:
            return False
            
        # Check conditions (if any)
        if user_role.conditions:
            # Implement condition checking logic here
            pass
            
        return True
        
    def _check_conditions(self, username: str, resource: ResourceType, action: str,
                         context: Dict[str, Any]) -> bool:
        """Check conditional permissions"""
        
        # Example conditional logic:
        # - Time-based restrictions
        # - IP-based restrictions
        # - Resource-specific restrictions
        
        # For now, return True (allow all)
        # This can be extended with complex conditional logic
        return True
        
    def _clear_user_cache(self, username: str):
        """Clear permission cache for a user"""
        keys_to_remove = [
            key for key in self.permission_cache.keys() 
            if key.startswith(f"{username}_")
        ]
        for key in keys_to_remove:
            del self.permission_cache[key]
            
    def get_user_roles(self, username: str) -> List[Dict[str, Any]]:
        """Get all roles assigned to a user"""
        if username not in self.user_roles:
            return []
            
        user_roles = []
        for user_role in self.user_roles[username]:
            if self._is_role_assignment_valid(user_role):
                role_info = asdict(user_role)
                role_info["granted_at"] = role_info["granted_at"].isoformat()
                if role_info["expires_at"]:
                    role_info["expires_at"] = role_info["expires_at"].isoformat()
                user_roles.append(role_info)
                
        return user_roles
        
    def get_role_permissions(self, role_name: str) -> List[Dict[str, Any]]:
        """Get all permissions for a role"""
        if role_name not in self.roles:
            return []
            
        role = self.roles[role_name]
        all_permissions = role.permissions.copy()
        
        # Add inherited permissions
        inherited_permissions = self._get_inherited_permissions(role)
        all_permissions.extend(inherited_permissions)
        
        # Convert to dict format
        permissions = []
        for perm in all_permissions:
            permissions.append({
                "resource": perm.resource.value,
                "action": perm.action,
                "level": perm.level.value,
                "description": perm.description
            })
            
        return permissions
        
    def list_all_roles(self) -> List[Dict[str, Any]]:
        """List all available roles"""
        roles = []
        for role_name, role in self.roles.items():
            roles.append({
                "name": role.name,
                "description": role.description,
                "permissions_count": len(role.permissions),
                "inherits_from": role.inherits_from,
                "created_at": role.created_at.isoformat() if role.created_at else None,
                "created_by": role.created_by
            })
            
        return roles
        
    def get_permission_matrix(self, username: str) -> Dict[str, Dict[str, bool]]:
        """Get a comprehensive permission matrix for a user"""
        user_permissions = self._get_user_permissions(username)
        
        matrix = {}
        for resource in ResourceType:
            matrix[resource.value] = {}
            
            # Common actions for each resource type
            actions = self._get_resource_actions(resource)
            
            for action in actions:
                for level in PermissionLevel:
                    if level == PermissionLevel.NONE:
                        continue
                        
                    has_perm = self._has_permission(user_permissions, resource, action, level)
                    matrix[resource.value][f"{action}_{level.name.lower()}"] = has_perm
                    
        return matrix
        
    def _get_resource_actions(self, resource: ResourceType) -> List[str]:
        """Get common actions for a resource type"""
        common_actions = {
            ResourceType.SYSTEM: ["monitor", "configure", "restart", "shutdown"],
            ResourceType.AGENTS: ["view", "create", "modify", "delete", "operate"],
            ResourceType.CONTRACTS: ["view", "deploy", "interact", "upgrade"],
            ResourceType.TOKENS: ["view", "transfer", "mint", "burn"],
            ResourceType.ANALYTICS: ["view", "export", "configure"],
            ResourceType.SECURITY: ["view", "configure", "emergency_lockdown"],
            ResourceType.AUDIT: ["view", "export", "configure"],
            ResourceType.USERS: ["view", "create", "modify", "delete"],
            ResourceType.API: ["access", "admin_access", "configure"],
            ResourceType.BLOCKCHAIN: ["read", "write", "admin"]
        }
        
        return common_actions.get(resource, ["view", "modify"])
        
    def _log_access_event(self, event_type: str, data: Dict[str, Any]):
        """Log access control events"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        }
        
        self.access_logs.append(event)
        
        # Keep only recent logs (memory management)
        if len(self.access_logs) > 1000:
            self.access_logs = self.access_logs[-500:]
            
        self.logger.info(f"RBAC_EVENT: {event_type} - {json.dumps(data)}")
        
    def get_access_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent access logs"""
        return self.access_logs[-limit:]
        
    def cleanup_expired_roles(self) -> int:
        """Clean up expired role assignments"""
        cleaned_count = 0
        
        for username, user_roles in self.user_roles.items():
            original_count = len(user_roles)
            
            # Filter out expired roles
            valid_roles = [
                ur for ur in user_roles
                if self._is_role_assignment_valid(ur)
            ]
            
            if len(valid_roles) < original_count:
                self.user_roles[username] = valid_roles
                cleaned_count += original_count - len(valid_roles)
                self._clear_user_cache(username)
                
        if cleaned_count > 0:
            self._log_access_event("ROLES_CLEANED", {"expired_roles": cleaned_count})
            
        return cleaned_count


# 🛡️ PERMISSION DECORATORS FOR EASY INTEGRATION
class require_permission:
    """Decorator to require specific permissions for function access"""
    
    def __init__(self, resource: ResourceType, action: str, 
                 level: PermissionLevel = PermissionLevel.READ):
        self.resource = resource
        self.action = action
        self.level = level
        
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            # In a real implementation, you would get the current user from context
            # For now, this is a placeholder
            current_user = kwargs.get('current_user', 'anonymous')
            
            # Get RBAC instance (in practice, this would be injected)
            rbac = getattr(wrapper, '_rbac_instance', None)
            if not rbac:
                raise PermissionError("RBAC system not configured")
                
            if not rbac.check_permission(current_user, self.resource, self.action, self.level):
                raise PermissionError(f"Access denied: {self.resource.value}.{self.action}")
                
            return func(*args, **kwargs)
            
        return wrapper


# Example usage and testing
def main():
    """Test the RBAC system"""
    print("\n🛡️ TESTING GUARDIAN SHIELD RBAC SYSTEM")
    print("=" * 50)
    
    # Initialize RBAC
    rbac = GuardianRoleBasedAccessControl()
    
    # Assign roles to test users
    print("\n👤 Assigning roles...")
    rbac.assign_role_to_user("master_admin", "MASTER_ADMIN", "SYSTEM")
    rbac.assign_role_to_user("john_admin", "DESIGNATED_ADMIN", "master_admin")
    rbac.assign_role_to_user("jane_operator", "OPERATOR", "master_admin")
    rbac.assign_role_to_user("bob_viewer", "VIEWER", "john_admin")
    
    # Test permissions
    print("\n🔍 Testing permissions...")
    
    users = ["master_admin", "john_admin", "jane_operator", "bob_viewer", "anonymous"]
    
    test_cases = [
        (ResourceType.SECURITY, "emergency_lockdown", PermissionLevel.MASTER),
        (ResourceType.AGENTS, "manage", PermissionLevel.ADMIN),
        (ResourceType.ANALYTICS, "view", PermissionLevel.READ),
        (ResourceType.SYSTEM, "monitor", PermissionLevel.READ),
    ]
    
    for user in users:
        print(f"\n👤 Testing permissions for: {user}")
        for resource, action, level in test_cases:
            has_permission = rbac.check_permission(user, resource, action, level)
            status = "✅ ALLOWED" if has_permission else "❌ DENIED"
            print(f"   {resource.value}.{action} ({level.name}): {status}")
            
    # Display role information
    print(f"\n📋 Available roles: {len(rbac.list_all_roles())}")
    for role in rbac.list_all_roles():
        print(f"   • {role['name']}: {role['description']}")
        
    print(f"\n📊 Permission checks logged: {len(rbac.get_access_logs())}")
    
    print("\n🎉 RBAC system test completed!")
    

if __name__ == "__main__":
    main()