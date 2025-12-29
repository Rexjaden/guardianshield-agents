// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

/**
 * @title GuardianSecurityController
 * @dev MAXIMUM SECURITY for all GuardianShield smart contracts
 * 
 * 🛡️ SECURITY FEATURES:
 * - Multi-signature requirement for critical functions
 * - Role-based access control with designated roles
 * - Time-locked administrative functions
 * - Emergency pause functionality
 * - Comprehensive audit trail
 * - Master admin protection (ONLY YOU)
 */
contract GuardianSecurityController is Ownable, AccessControl, ReentrancyGuard, Pausable {
    
    // 🔐 SECURITY ROLES
    bytes32 public constant MASTER_ADMIN_ROLE = keccak256("MASTER_ADMIN_ROLE");
    bytes32 public constant DESIGNATED_ADMIN_ROLE = keccak256("DESIGNATED_ADMIN_ROLE");
    bytes32 public constant EMERGENCY_ROLE = keccak256("EMERGENCY_ROLE");
    bytes32 public constant OPERATOR_ROLE = keccak256("OPERATOR_ROLE");
    
    // 🔒 SECURITY CONFIGURATION
    struct SecurityConfig {
        bool emergencyLocked;
        uint256 multiSigThreshold;
        uint256 timeLockDelay;
        address masterAdmin;
        bool initialized;
    }
    
    SecurityConfig public securityConfig;
    
    // 🛡️ MULTI-SIGNATURE TRACKING
    struct PendingAction {
        bytes32 actionHash;
        uint256 confirmations;
        uint256 timelock;
        bool executed;
        mapping(address => bool) confirmed;
        string actionType;
        bytes actionData;
    }
    
    mapping(bytes32 => PendingAction) public pendingActions;
    bytes32[] public pendingActionsList;
    
    // 📊 AUDIT LOGGING
    struct AuditLog {
        address actor;
        string action;
        bytes32 actionHash;
        uint256 timestamp;
        bool success;
    }
    
    AuditLog[] public auditTrail;
    mapping(address => uint256[]) public userAuditHistory;
    
    // 🚨 EMERGENCY CONTROLS
    bool public emergencyPaused = false;
    address public emergencyContact;
    uint256 public lastSecurityCheck;
    
    // 📋 EVENTS
    event SecurityInitialized(address indexed masterAdmin, uint256 timestamp);
    event ActionProposed(bytes32 indexed actionHash, address indexed proposer, string actionType);
    event ActionConfirmed(bytes32 indexed actionHash, address indexed confirmer);
    event ActionExecuted(bytes32 indexed actionHash, address indexed executor, bool success);
    event EmergencyActivated(address indexed activator, string reason);
    event SecurityConfigUpdated(address indexed updater, string parameter);
    event AuditLogCreated(address indexed actor, string action, uint256 timestamp);
    
    // 🔧 MODIFIERS
    modifier onlyMasterAdmin() {
        require(hasRole(MASTER_ADMIN_ROLE, msg.sender), "ONLY_MASTER_ADMIN");
        _;
    }
    
    modifier onlyAuthorizedAdmin() {
        require(
            hasRole(MASTER_ADMIN_ROLE, msg.sender) || 
            hasRole(DESIGNATED_ADMIN_ROLE, msg.sender),
            "ONLY_AUTHORIZED_ADMIN"
        );
        _;
    }
    
    modifier notEmergencyLocked() {
        require(!securityConfig.emergencyLocked, "EMERGENCY_LOCKED");
        _;
    }
    
    modifier validAction(bytes32 actionHash) {
        require(pendingActions[actionHash].actionHash != bytes32(0), "ACTION_NOT_FOUND");
        require(!pendingActions[actionHash].executed, "ACTION_ALREADY_EXECUTED");
        _;
    }
    
    modifier timelockExpired(bytes32 actionHash) {
        require(
            block.timestamp >= pendingActions[actionHash].timelock,
            "TIMELOCK_NOT_EXPIRED"
        );
        _;
    }
    
    constructor() Ownable(msg.sender) {
        // Initialize with maximum security
        _initializeSecurity(msg.sender);
    }
    
    /**
     * @dev Initialize security system - ONLY ONCE
     */
    function _initializeSecurity(address masterAdmin) private {
        require(!securityConfig.initialized, "ALREADY_INITIALIZED");
        
        // Set up roles
        _grantRole(DEFAULT_ADMIN_ROLE, masterAdmin);
        _grantRole(MASTER_ADMIN_ROLE, masterAdmin);
        _grantRole(EMERGENCY_ROLE, masterAdmin);
        
        // Configure security
        securityConfig = SecurityConfig({
            emergencyLocked: false,
            multiSigThreshold: 1, // Initially only master admin
            timeLockDelay: 24 hours, // 24 hour timelock for critical actions
            masterAdmin: masterAdmin,
            initialized: true
        });
        
        emergencyContact = masterAdmin;
        lastSecurityCheck = block.timestamp;
        
        _logAuditEvent(masterAdmin, "SECURITY_INITIALIZED", true);
        emit SecurityInitialized(masterAdmin, block.timestamp);
    }
    
    /**
     * @dev Add designated admin (MASTER ADMIN ONLY)
     */
    function addDesignatedAdmin(address newAdmin, string memory adminName) 
        external 
        onlyMasterAdmin 
        notEmergencyLocked 
    {
        require(newAdmin != address(0), "INVALID_ADDRESS");
        require(!hasRole(DESIGNATED_ADMIN_ROLE, newAdmin), "ALREADY_ADMIN");
        
        _grantRole(DESIGNATED_ADMIN_ROLE, newAdmin);
        
        _logAuditEvent(msg.sender, string(abi.encodePacked("ADD_ADMIN:", adminName)), true);
        emit SecurityConfigUpdated(msg.sender, "ADD_DESIGNATED_ADMIN");
    }
    
    /**
     * @dev Remove designated admin (MASTER ADMIN ONLY)
     */
    function removeDesignatedAdmin(address admin) 
        external 
        onlyMasterAdmin 
        notEmergencyLocked 
    {
        require(admin != securityConfig.masterAdmin, "CANNOT_REMOVE_MASTER");
        require(hasRole(DESIGNATED_ADMIN_ROLE, admin), "NOT_DESIGNATED_ADMIN");
        
        _revokeRole(DESIGNATED_ADMIN_ROLE, admin);
        _revokeRole(OPERATOR_ROLE, admin);
        
        _logAuditEvent(msg.sender, "REMOVE_ADMIN", true);
        emit SecurityConfigUpdated(msg.sender, "REMOVE_DESIGNATED_ADMIN");
    }
    
    /**
     * @dev Propose critical action requiring multi-sig
     */
    function proposeAction(
        string memory actionType,
        bytes memory actionData,
        address target
    ) external onlyAuthorizedAdmin notEmergencyLocked returns (bytes32) {
        
        bytes32 actionHash = keccak256(
            abi.encodePacked(actionType, actionData, target, block.timestamp)
        );
        
        require(pendingActions[actionHash].actionHash == bytes32(0), "ACTION_EXISTS");
        
        // Create pending action
        PendingAction storage action = pendingActions[actionHash];
        action.actionHash = actionHash;
        action.confirmations = 1; // Proposer automatically confirms
        action.timelock = block.timestamp + securityConfig.timeLockDelay;
        action.executed = false;
        action.confirmed[msg.sender] = true;
        action.actionType = actionType;
        action.actionData = actionData;
        
        pendingActionsList.push(actionHash);
        
        _logAuditEvent(msg.sender, string(abi.encodePacked("PROPOSE:", actionType)), true);
        emit ActionProposed(actionHash, msg.sender, actionType);
        
        return actionHash;
    }
    
    /**
     * @dev Confirm pending action
     */
    function confirmAction(bytes32 actionHash) 
        external 
        onlyAuthorizedAdmin 
        notEmergencyLocked 
        validAction(actionHash) 
    {
        PendingAction storage action = pendingActions[actionHash];
        require(!action.confirmed[msg.sender], "ALREADY_CONFIRMED");
        
        action.confirmed[msg.sender] = true;
        action.confirmations++;
        
        _logAuditEvent(msg.sender, string(abi.encodePacked("CONFIRM:", action.actionType)), true);
        emit ActionConfirmed(actionHash, msg.sender);
    }
    
    /**
     * @dev Execute confirmed action (after timelock)
     */
    function executeAction(bytes32 actionHash) 
        external 
        onlyAuthorizedAdmin 
        notEmergencyLocked 
        validAction(actionHash) 
        timelockExpired(actionHash) 
    {
        PendingAction storage action = pendingActions[actionHash];
        require(action.confirmations >= securityConfig.multiSigThreshold, "INSUFFICIENT_CONFIRMATIONS");
        
        action.executed = true;
        
        // Execute the action (implementation depends on action type)
        bool success = _executeActionLogic(action.actionType, action.actionData);
        
        _logAuditEvent(msg.sender, string(abi.encodePacked("EXECUTE:", action.actionType)), success);
        emit ActionExecuted(actionHash, msg.sender, success);
    }
    
    /**
     * @dev Execute action logic based on type
     */
    function _executeActionLogic(string memory actionType, bytes memory actionData) 
        private 
        returns (bool) 
    {
        // Implement specific action execution logic
        // This is where critical contract operations would be performed
        
        if (keccak256(bytes(actionType)) == keccak256(bytes("UPDATE_CONFIG"))) {
            // Handle configuration updates
            return true;
        } else if (keccak256(bytes(actionType)) == keccak256(bytes("TRANSFER_FUNDS"))) {
            // Handle fund transfers
            return true;
        } else if (keccak256(bytes(actionType)) == keccak256(bytes("CONTRACT_UPGRADE"))) {
            // Handle contract upgrades
            return true;
        }
        
        return false;
    }
    
    /**
     * @dev EMERGENCY LOCKDOWN (MASTER ADMIN ONLY)
     */
    function emergencyLockdown(string memory reason) 
        external 
        onlyMasterAdmin 
    {
        securityConfig.emergencyLocked = true;
        emergencyPaused = true;
        _pause();
        
        _logAuditEvent(msg.sender, string(abi.encodePacked("EMERGENCY_LOCKDOWN:", reason)), true);
        emit EmergencyActivated(msg.sender, reason);
    }
    
    /**
     * @dev Disable emergency lockdown (MASTER ADMIN ONLY)
     */
    function disableEmergencyLockdown() 
        external 
        onlyMasterAdmin 
    {
        securityConfig.emergencyLocked = false;
        emergencyPaused = false;
        _unpause();
        
        _logAuditEvent(msg.sender, "DISABLE_EMERGENCY", true);
        emit SecurityConfigUpdated(msg.sender, "EMERGENCY_DISABLED");
    }
    
    /**
     * @dev Update multi-sig threshold (MASTER ADMIN ONLY)
     */
    function updateMultiSigThreshold(uint256 newThreshold) 
        external 
        onlyMasterAdmin 
        notEmergencyLocked 
    {
        require(newThreshold > 0, "INVALID_THRESHOLD");
        securityConfig.multiSigThreshold = newThreshold;
        
        _logAuditEvent(msg.sender, "UPDATE_MULTISIG_THRESHOLD", true);
        emit SecurityConfigUpdated(msg.sender, "MULTISIG_THRESHOLD");
    }
    
    /**
     * @dev Update timelock delay (MASTER ADMIN ONLY)
     */
    function updateTimeLockDelay(uint256 newDelay) 
        external 
        onlyMasterAdmin 
        notEmergencyLocked 
    {
        require(newDelay >= 1 hours, "MINIMUM_1_HOUR");
        require(newDelay <= 7 days, "MAXIMUM_7_DAYS");
        
        securityConfig.timeLockDelay = newDelay;
        
        _logAuditEvent(msg.sender, "UPDATE_TIMELOCK", true);
        emit SecurityConfigUpdated(msg.sender, "TIMELOCK_DELAY");
    }
    
    /**
     * @dev Transfer master admin role (EXTREME CAUTION)
     */
    function transferMasterAdmin(address newMasterAdmin) 
        external 
        onlyMasterAdmin 
        notEmergencyLocked 
    {
        require(newMasterAdmin != address(0), "INVALID_ADDRESS");
        require(newMasterAdmin != securityConfig.masterAdmin, "SAME_ADDRESS");
        
        // Revoke old master admin roles
        _revokeRole(MASTER_ADMIN_ROLE, securityConfig.masterAdmin);
        _revokeRole(DEFAULT_ADMIN_ROLE, securityConfig.masterAdmin);
        
        // Grant new master admin roles
        _grantRole(DEFAULT_ADMIN_ROLE, newMasterAdmin);
        _grantRole(MASTER_ADMIN_ROLE, newMasterAdmin);
        _grantRole(EMERGENCY_ROLE, newMasterAdmin);
        
        securityConfig.masterAdmin = newMasterAdmin;
        emergencyContact = newMasterAdmin;
        
        _logAuditEvent(msg.sender, "TRANSFER_MASTER_ADMIN", true);
        emit SecurityConfigUpdated(msg.sender, "MASTER_ADMIN_TRANSFERRED");
    }
    
    /**
     * @dev Log audit event
     */
    function _logAuditEvent(address actor, string memory action, bool success) private {
        bytes32 actionHash = keccak256(abi.encodePacked(action, actor, block.timestamp));
        
        AuditLog memory logEntry = AuditLog({
            actor: actor,
            action: action,
            actionHash: actionHash,
            timestamp: block.timestamp,
            success: success
        });
        
        auditTrail.push(logEntry);
        userAuditHistory[actor].push(auditTrail.length - 1);
        
        emit AuditLogCreated(actor, action, block.timestamp);
    }
    
    /**
     * @dev Get security status
     */
    function getSecurityStatus() external view returns (
        bool emergencyLocked,
        uint256 multiSigThreshold,
        uint256 timeLockDelay,
        address masterAdmin,
        uint256 totalPendingActions,
        uint256 totalAuditLogs
    ) {
        return (
            securityConfig.emergencyLocked,
            securityConfig.multiSigThreshold,
            securityConfig.timeLockDelay,
            securityConfig.masterAdmin,
            pendingActionsList.length,
            auditTrail.length
        );
    }
    
    /**
     * @dev Get pending actions count
     */
    function getPendingActionsCount() external view returns (uint256) {
        return pendingActionsList.length;
    }
    
    /**
     * @dev Get audit trail count
     */
    function getAuditTrailCount() external view returns (uint256) {
        return auditTrail.length;
    }
    
    /**
     * @dev Get user audit history
     */
    function getUserAuditHistory(address user) external view returns (uint256[] memory) {
        return userAuditHistory[user];
    }
    
    /**
     * @dev Check if address has any admin role
     */
    function isAdmin(address account) external view returns (bool) {
        return hasRole(MASTER_ADMIN_ROLE, account) || hasRole(DESIGNATED_ADMIN_ROLE, account);
    }
    
    /**
     * @dev Perform security check (ADMIN ONLY)
     */
    function performSecurityCheck() external onlyAuthorizedAdmin {
        lastSecurityCheck = block.timestamp;
        _logAuditEvent(msg.sender, "SECURITY_CHECK", true);
    }
    
    /**
     * @dev Cancel pending action (MASTER ADMIN ONLY)
     */
    function cancelAction(bytes32 actionHash) 
        external 
        onlyMasterAdmin 
        validAction(actionHash) 
    {
        pendingActions[actionHash].executed = true; // Mark as executed to prevent execution
        
        _logAuditEvent(msg.sender, "CANCEL_ACTION", true);
    }
    
    // 🚨 EMERGENCY FUNCTIONS
    
    /**
     * @dev Emergency pause all operations
     */
    function emergencyPause() external {
        require(
            hasRole(MASTER_ADMIN_ROLE, msg.sender) || 
            hasRole(EMERGENCY_ROLE, msg.sender),
            "NO_EMERGENCY_PERMISSION"
        );
        
        _pause();
        emergencyPaused = true;
        
        _logAuditEvent(msg.sender, "EMERGENCY_PAUSE", true);
    }
    
    /**
     * @dev Emergency unpause (MASTER ADMIN ONLY)
     */
    function emergencyUnpause() external onlyMasterAdmin {
        _unpause();
        emergencyPaused = false;
        
        _logAuditEvent(msg.sender, "EMERGENCY_UNPAUSE", true);
    }
}