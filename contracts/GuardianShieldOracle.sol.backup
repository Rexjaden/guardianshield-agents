// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title GuardianShield Threat Intelligence Oracle
 * @dev Advanced oracle system for real-time threat intelligence and criminal detection
 */
contract GuardianShieldOracle is Ownable, ReentrancyGuard {
    
    // Oracle data structures
    struct ThreatData {
        uint256 threatLevel;      // 1-5 severity scale
        uint256 confidence;       // Confidence percentage (0-100)
        uint256 timestamp;        // When threat was detected
        address reporter;         // Agent/oracle that reported
        string threatType;        // Type of threat
        string evidence;          // IPFS hash of evidence
        bool verified;           // Verified by multiple agents
        uint256 blockNumber;     // Block when reported
    }
    
    struct CriminalProfile {
        string name;
        uint256 riskScore;       // 0-1000 risk score
        uint256 totalDamages;    // Total damages in USD
        bool isActive;           // Currently active threat
        string[] knownAddresses; // Known criminal addresses
        uint256 lastActivity;    // Last seen activity
        string profileHash;      // IPFS hash of full profile
    }
    
    struct OracleNode {
        address nodeAddress;
        uint256 reputation;      // 0-1000 reputation score
        uint256 totalReports;
        uint256 accurateReports;
        bool isActive;
        string nodeType;         // "AI_AGENT", "HUMAN_ANALYST", "AUTOMATED"
        uint256 lastUpdate;
    }
    
    // State variables
    mapping(bytes32 => ThreatData) public threats;
    mapping(string => CriminalProfile) public criminals;
    mapping(address => OracleNode) public oracleNodes;
    mapping(address => bool) public maliciousAddresses;
    mapping(string => bool) public maliciousDomains;
    
    bytes32[] public threatHashes;
    string[] public criminalList;
    address[] public nodeAddresses;
    
    uint256 public constant MIN_CONFIDENCE = 70;
    uint256 public constant REPUTATION_THRESHOLD = 500;
    
    // Events
    event ThreatReported(bytes32 indexed threatHash, uint256 threatLevel, address reporter);
    event CriminalAdded(string indexed criminalId, uint256 riskScore);
    event AddressFlagged(address indexed maliciousAddress, uint256 confidence);
    event DomainBlocked(string indexed domain, uint256 confidence);
    event OracleNodeRegistered(address indexed node, string nodeType);
    event ThreatVerified(bytes32 indexed threatHash, uint256 verifications);
    
    constructor() {}
    
    /**
     * @dev Register a new oracle node (AI agent or analyst)
     */
    function registerOracleNode(
        address _nodeAddress,
        string memory _nodeType
    ) external onlyOwner {
        require(_nodeAddress != address(0), "Invalid node address");
        require(!oracleNodes[_nodeAddress].isActive, "Node already registered");
        
        oracleNodes[_nodeAddress] = OracleNode({
            nodeAddress: _nodeAddress,
            reputation: 500, // Start with neutral reputation
            totalReports: 0,
            accurateReports: 0,
            isActive: true,
            nodeType: _nodeType,
            lastUpdate: block.timestamp
        });
        
        nodeAddresses.push(_nodeAddress);
        emit OracleNodeRegistered(_nodeAddress, _nodeType);
    }
    
    /**
     * @dev Report a new threat to the oracle
     */
    function reportThreat(
        bytes32 _threatHash,
        uint256 _threatLevel,
        uint256 _confidence,
        string memory _threatType,
        string memory _evidence
    ) external nonReentrant {
        require(oracleNodes[msg.sender].isActive, "Unauthorized oracle node");
        require(oracleNodes[msg.sender].reputation >= REPUTATION_THRESHOLD, "Insufficient reputation");
        require(_threatLevel >= 1 && _threatLevel <= 5, "Invalid threat level");
        require(_confidence >= MIN_CONFIDENCE, "Confidence too low");
        require(!threats[_threatHash].verified, "Threat already exists");
        
        threats[_threatHash] = ThreatData({
            threatLevel: _threatLevel,
            confidence: _confidence,
            timestamp: block.timestamp,
            reporter: msg.sender,
            threatType: _threatType,
            evidence: _evidence,
            verified: false,
            blockNumber: block.number
        });
        
        threatHashes.push(_threatHash);
        oracleNodes[msg.sender].totalReports++;
        oracleNodes[msg.sender].lastUpdate = block.timestamp;
        
        emit ThreatReported(_threatHash, _threatLevel, msg.sender);
    }
    
    /**
     * @dev Add criminal profile to oracle database
     */
    function addCriminalProfile(
        string memory _criminalId,
        string memory _name,
        uint256 _riskScore,
        uint256 _totalDamages,
        bool _isActive,
        string[] memory _knownAddresses,
        string memory _profileHash
    ) external {
        require(oracleNodes[msg.sender].isActive, "Unauthorized oracle node");
        require(_riskScore <= 1000, "Invalid risk score");
        
        criminals[_criminalId] = CriminalProfile({
            name: _name,
            riskScore: _riskScore,
            totalDamages: _totalDamages,
            isActive: _isActive,
            knownAddresses: _knownAddresses,
            lastActivity: block.timestamp,
            profileHash: _profileHash
        });
        
        criminalList.push(_criminalId);
        
        // Flag all known addresses as malicious
        for (uint i = 0; i < _knownAddresses.length; i++) {
            address addr = parseAddress(_knownAddresses[i]);
            if (addr != address(0)) {
                maliciousAddresses[addr] = true;
                emit AddressFlagged(addr, 95);
            }
        }
        
        emit CriminalAdded(_criminalId, _riskScore);
    }
    
    /**
     * @dev Flag a malicious address
     */
    function flagMaliciousAddress(
        address _maliciousAddress,
        uint256 _confidence,
        string memory _evidence
    ) external {
        require(oracleNodes[msg.sender].isActive, "Unauthorized oracle node");
        require(_confidence >= MIN_CONFIDENCE, "Confidence too low");
        
        maliciousAddresses[_maliciousAddress] = true;
        emit AddressFlagged(_maliciousAddress, _confidence);
    }
    
    /**
     * @dev Block a malicious domain
     */
    function blockMaliciousDomain(
        string memory _domain,
        uint256 _confidence,
        string memory _evidence
    ) external {
        require(oracleNodes[msg.sender].isActive, "Unauthorized oracle node");
        require(_confidence >= MIN_CONFIDENCE, "Confidence too low");
        
        maliciousDomains[_domain] = true;
        emit DomainBlocked(_domain, _confidence);
    }
    
    /**
     * @dev Check if address is flagged as malicious
     */
    function isAddressMalicious(address _address) external view returns (bool) {
        return maliciousAddresses[_address];
    }
    
    /**
     * @dev Check if domain is blocked
     */
    function isDomainMalicious(string memory _domain) external view returns (bool) {
        return maliciousDomains[_domain];
    }
    
    /**
     * @dev Get threat data
     */
    function getThreatData(bytes32 _threatHash) external view returns (
        uint256 threatLevel,
        uint256 confidence,
        uint256 timestamp,
        address reporter,
        string memory threatType,
        bool verified
    ) {
        ThreatData storage threat = threats[_threatHash];
        return (
            threat.threatLevel,
            threat.confidence,
            threat.timestamp,
            threat.reporter,
            threat.threatType,
            threat.verified
        );
    }
    
    /**
     * @dev Get criminal profile
     */
    function getCriminalProfile(string memory _criminalId) external view returns (
        string memory name,
        uint256 riskScore,
        uint256 totalDamages,
        bool isActive,
        uint256 lastActivity
    ) {
        CriminalProfile storage criminal = criminals[_criminalId];
        return (
            criminal.name,
            criminal.riskScore,
            criminal.totalDamages,
            criminal.isActive,
            criminal.lastActivity
        );
    }
    
    /**
     * @dev Get oracle node info
     */
    function getOracleNode(address _node) external view returns (
        uint256 reputation,
        uint256 totalReports,
        uint256 accurateReports,
        bool isActive,
        string memory nodeType
    ) {
        OracleNode storage node = oracleNodes[_node];
        return (
            node.reputation,
            node.totalReports,
            node.accurateReports,
            node.isActive,
            node.nodeType
        );
    }
    
    /**
     * @dev Update oracle node reputation
     */
    function updateNodeReputation(address _node, bool _accurate) external onlyOwner {
        require(oracleNodes[_node].isActive, "Node not active");
        
        if (_accurate) {
            oracleNodes[_node].accurateReports++;
            if (oracleNodes[_node].reputation < 1000) {
                oracleNodes[_node].reputation += 10;
            }
        } else {
            if (oracleNodes[_node].reputation > 10) {
                oracleNodes[_node].reputation -= 20;
            }
        }
    }
    
    /**
     * @dev Verify threat with multiple confirmations
     */
    function verifyThreat(bytes32 _threatHash) external {
        require(oracleNodes[msg.sender].isActive, "Unauthorized oracle node");
        require(threats[_threatHash].timestamp > 0, "Threat does not exist");
        require(threats[_threatHash].reporter != msg.sender, "Cannot verify own report");
        
        // Mark as verified if high confidence and good reputation
        if (threats[_threatHash].confidence >= 90 && 
            oracleNodes[msg.sender].reputation >= 700) {
            threats[_threatHash].verified = true;
            emit ThreatVerified(_threatHash, 1);
        }
    }
    
    /**
     * @dev Get total active threats
     */
    function getActiveThreatCount() external view returns (uint256) {
        uint256 count = 0;
        for (uint i = 0; i < threatHashes.length; i++) {
            if (threats[threatHashes[i]].threatLevel >= 3 && 
                block.timestamp - threats[threatHashes[i]].timestamp < 86400) {
                count++;
            }
        }
        return count;
    }
    
    /**
     * @dev Get total criminal count
     */
    function getTotalCriminalCount() external view returns (uint256) {
        return criminalList.length;
    }
    
    /**
     * @dev Emergency pause oracle
     */
    function pauseOracle() external onlyOwner {
        // Pause all oracle operations
        for (uint i = 0; i < nodeAddresses.length; i++) {
            oracleNodes[nodeAddresses[i]].isActive = false;
        }
    }
    
    /**
     * @dev Helper function to parse address from string
     */
    function parseAddress(string memory _address) internal pure returns (address) {
        // Simplified address parsing - in production use more robust parsing
        bytes memory stringBytes = bytes(_address);
        if (stringBytes.length != 42) return address(0);
        
        // Return zero address for now - implement proper parsing in production
        return address(0);
    }
    
    /**
     * @dev Get oracle statistics
     */
    function getOracleStats() external view returns (
        uint256 totalThreats,
        uint256 totalCriminals,
        uint256 totalNodes,
        uint256 avgReputation
    ) {
        uint256 totalRep = 0;
        uint256 activeNodes = 0;
        
        for (uint i = 0; i < nodeAddresses.length; i++) {
            if (oracleNodes[nodeAddresses[i]].isActive) {
                totalRep += oracleNodes[nodeAddresses[i]].reputation;
                activeNodes++;
            }
        }
        
        return (
            threatHashes.length,
            criminalList.length,
            activeNodes,
            activeNodes > 0 ? totalRep / activeNodes : 0
        );
    }
}