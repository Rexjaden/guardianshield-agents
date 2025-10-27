// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title ERC-8055 Security Monitoring & DAO Governance
 * @notice Implements trusted/DAO-governed agent registration, burn/reverse logic, and tamper-proof logs.
 */

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract GuardianShield8055 is ERC721Enumerable, Ownable, AccessControl {
    bytes32 public constant AGENT_ROLE = keccak256("AGENT_ROLE");
    bytes32 public constant DAO_ROLE = keccak256("DAO_ROLE");
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");

    struct BurnEvent {
        uint256 tokenId;
        address originalOwner;
        uint256 timestamp;
        bool reversed;
    }

    mapping(uint256 => BurnEvent) public burnEvents;
    mapping(uint256 => bool) public isBurned;
    mapping(uint256 => bool) public isReminted;
    mapping(uint256 => address) public pendingReturn;

    event AgentRegistered(address indexed agent, bool trusted);
    event TokenBurned(uint256 indexed tokenId, address indexed owner);
    event TokenReminted(uint256 indexed tokenId, address indexed to);
    event OwnerVerificationRequested(uint256 indexed tokenId, address indexed claimant);
    event OwnerVerified(uint256 indexed tokenId, address indexed owner);
    event LogTamperProof(bytes32 indexed logHash, string logType, uint256 timestamp);

    address public treasury;

    constructor(address _treasury) ERC721("GuardianShield8055", "GS8055") {
        treasury = _treasury;
        _setupRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _setupRole(ADMIN_ROLE, msg.sender);
    }

    // --- Agent Management ---
    function registerAgent(address agent, bool trusted) external onlyRole(ADMIN_ROLE) {
        if (trusted) {
            _grantRole(AGENT_ROLE, agent);
        } else {
            _grantRole(DAO_ROLE, agent);
        }
        emit AgentRegistered(agent, trusted);
    }

    // --- Burn Logic ---
    function agentBurn(uint256 tokenId) external onlyRole(AGENT_ROLE) {
        address owner = ownerOf(tokenId);
        require(!isBurned[tokenId], "Already burned");
        _burn(tokenId);
        isBurned[tokenId] = true;
        burnEvents[tokenId] = BurnEvent(tokenId, owner, block.timestamp, false);
        emit TokenBurned(tokenId, owner);
    }

    // --- Burn Reversal & Remint ---
    function reverseBurn(uint256 tokenId) external onlyRole(ADMIN_ROLE) {
        require(isBurned[tokenId], "Not burned");
        require(!isReminted[tokenId], "Already reminted");
        _safeMint(treasury, tokenId);
        isReminted[tokenId] = true;
        burnEvents[tokenId].reversed = true;
        pendingReturn[tokenId] = burnEvents[tokenId].originalOwner;
        emit TokenReminted(tokenId, treasury);
    }

    // --- Owner Verification ---
    function requestOwnerVerification(uint256 tokenId) external {
        require(isReminted[tokenId], "Not reminted");
        require(msg.sender == pendingReturn[tokenId], "Not original owner");
        emit OwnerVerificationRequested(tokenId, msg.sender);
    }

    function adminVerifyOwner(uint256 tokenId, address owner) external onlyRole(ADMIN_ROLE) {
        require(pendingReturn[tokenId] == owner, "Not pending owner");
        _transfer(treasury, owner, tokenId);
        emit OwnerVerified(tokenId, owner);
    }

    // --- Tamper-Proof Logging (hash anchoring) ---
    function logTamperProof(bytes32 logHash, string calldata logType) external onlyRole(AGENT_ROLE) {
        emit LogTamperProof(logHash, logType, block.timestamp);
    }
}
