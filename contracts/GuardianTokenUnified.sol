// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title GuardianToken (Unified GUARD Token)
 * @dev Single contract handling both token economics and shield functionality
 * Combines ERC20 token with built-in shield/protection features
 */
contract GuardianToken is ERC20, ERC20Burnable, ERC20Permit, Ownable, ReentrancyGuard {
    
    // Token Economics
    uint256 public constant MAX_SUPPLY = 5_000_000_000 * 10**18; // 5 billion tokens
    uint256 public constant INITIAL_STAGE_SUPPLY = 300_000_000 * 10**18; // 300M initial
    uint256 public totalMinted;
    
    // Shield Protection System
    struct Shield {
        uint256 tokenId;
        uint256 serialNumber;
        string metadataURI;
        bool isActive;
        uint256 protectionLevel; // 1-100 (percentage protection)
        uint256 createdAt;
        bool isStolen;
    }
    
    // Shield Management
    mapping(address => Shield[]) public userShields; // User's active shields
    mapping(uint256 => address) public shieldOwner; // Shield serial to owner
    mapping(uint256 => Shield) public shields; // Shield data by serial
    mapping(address => bool) public isProtected; // Address protection status
    mapping(address => uint256) public protectionLevel; // Address protection percentage
    
    uint256 private _nextShieldId = 1;
    uint256 public shieldMintCost = 1000 * 10**18; // 1000 GUARD tokens to mint shield
    uint256 public maxShieldsPerUser = 10;
    
    // Events
    event StageMint(address indexed to, uint256 amount, uint256 totalMinted);
    event ShieldMinted(address indexed owner, uint256 serialNumber, uint256 protectionLevel, string metadataURI);
    event ShieldActivated(address indexed owner, uint256 serialNumber);
    event ShieldDeactivated(address indexed owner, uint256 serialNumber);
    event ShieldFlaggedStolen(uint256 serialNumber, address indexed by);
    event ShieldRecovered(uint256 serialNumber, address indexed by);
    event ProtectionUpdated(address indexed user, uint256 newLevel);
    
    constructor(address initialOwner) 
        ERC20("Guardian Token", "GUARD") 
        ERC20Permit("Guardian Token")
        Ownable(initialOwner) 
    {
        // Mint initial supply to owner for sale contract
        _mint(initialOwner, INITIAL_STAGE_SUPPLY);
        totalMinted = INITIAL_STAGE_SUPPLY;
        emit StageMint(initialOwner, INITIAL_STAGE_SUPPLY, totalMinted);
    }
    
    /**
     * @dev Mint tokens for next sale stage. Only owner can call.
     */
    function mintStage(address to, uint256 amount) external onlyOwner {
        require(totalSupply() + amount <= MAX_SUPPLY, "Exceeds max supply");
        _mint(to, amount);
        totalMinted += amount;
        emit StageMint(to, amount, totalMinted);
    }
    
    /**
     * @dev Mint a Guardian Shield NFT-like protection using tokens
     * Burns tokens to create shield with protection level
     */
    function mintShield(
        uint256 serialNumber, 
        string memory metadataURI,
        uint256 protectionLevel_
    ) external nonReentrant {
        require(balanceOf(msg.sender) >= shieldMintCost, "Insufficient GUARD tokens");
        require(shieldOwner[serialNumber] == address(0), "Serial number already used");
        require(protectionLevel_ > 0 && protectionLevel_ <= 100, "Invalid protection level");
        require(userShields[msg.sender].length < maxShieldsPerUser, "Max shields per user exceeded");
        
        // Burn tokens to mint shield
        _burn(msg.sender, shieldMintCost);
        
        // Create shield
        Shield memory newShield = Shield({
            tokenId: _nextShieldId,
            serialNumber: serialNumber,
            metadataURI: metadataURI,
            isActive: true,
            protectionLevel: protectionLevel_,
            createdAt: block.timestamp,
            isStolen: false
        });
        
        shields[serialNumber] = newShield;
        shieldOwner[serialNumber] = msg.sender;
        userShields[msg.sender].push(newShield);
        
        // Update user protection
        _updateUserProtection(msg.sender);
        
        _nextShieldId++;
        
        emit ShieldMinted(msg.sender, serialNumber, protectionLevel_, metadataURI);
    }
    
    /**
     * @dev Activate or deactivate shield protection
     */
    function toggleShield(uint256 serialNumber) external {
        require(shieldOwner[serialNumber] == msg.sender, "Not shield owner");
        
        Shield storage shield = shields[serialNumber];
        shield.isActive = !shield.isActive;
        
        // Update user shields array
        Shield[] storage userShieldArray = userShields[msg.sender];
        for (uint i = 0; i < userShieldArray.length; i++) {
            if (userShieldArray[i].serialNumber == serialNumber) {
                userShieldArray[i].isActive = shield.isActive;
                break;
            }
        }
        
        _updateUserProtection(msg.sender);
        
        if (shield.isActive) {
            emit ShieldActivated(msg.sender, serialNumber);
        } else {
            emit ShieldDeactivated(msg.sender, serialNumber);
        }
    }
    
    /**
     * @dev Flag shield as stolen (can be called by owner or authorized addresses)
     */
    function flagShieldStolen(uint256 serialNumber) external {
        require(
            shieldOwner[serialNumber] == msg.sender || owner() == msg.sender,
            "Not authorized to flag"
        );
        
        Shield storage shield = shields[serialNumber];
        shield.isStolen = true;
        shield.isActive = false;
        
        _updateUserProtection(shieldOwner[serialNumber]);
        
        emit ShieldFlaggedStolen(serialNumber, msg.sender);
    }
    
    /**
     * @dev Recover stolen shield (owner only)
     */
    function recoverShield(uint256 serialNumber) external onlyOwner {
        Shield storage shield = shields[serialNumber];
        shield.isStolen = false;
        shield.isActive = true;
        
        _updateUserProtection(shieldOwner[serialNumber]);
        
        emit ShieldRecovered(serialNumber, msg.sender);
    }
    
    /**
     * @dev Internal function to update user protection level
     */
    function _updateUserProtection(address user) internal {
        Shield[] memory userShieldArray = userShields[user];
        uint256 totalProtection = 0;
        uint256 activeShields = 0;
        
        for (uint i = 0; i < userShieldArray.length; i++) {
            if (userShieldArray[i].isActive && !userShieldArray[i].isStolen) {
                totalProtection += userShieldArray[i].protectionLevel;
                activeShields++;
            }
        }
        
        // Calculate average protection level (max 100%)
        uint256 avgProtection = activeShields > 0 ? totalProtection / activeShields : 0;
        if (avgProtection > 100) avgProtection = 100;
        
        protectionLevel[user] = avgProtection;
        isProtected[user] = avgProtection > 0;
        
        emit ProtectionUpdated(user, avgProtection);
    }
    
    /**
     * @dev Get user's active shields
     */
    function getUserShields(address user) external view returns (Shield[] memory) {
        return userShields[user];
    }
    
    /**
     * @dev Get user's active shield count
     */
    function getActiveShieldCount(address user) external view returns (uint256) {
        Shield[] memory userShieldArray = userShields[user];
        uint256 count = 0;
        
        for (uint i = 0; i < userShieldArray.length; i++) {
            if (userShieldArray[i].isActive && !userShieldArray[i].isStolen) {
                count++;
            }
        }
        
        return count;
    }
    
    /**
     * @dev Transfer with protection check
     * Protected users have reduced transfer amounts if protection is active
     */
    function transfer(address to, uint256 amount) public override returns (bool) {
        if (isProtected[msg.sender] && protectionLevel[msg.sender] > 0) {
            // Apply protection: reduce transfer amount based on protection level
            uint256 protectedAmount = (amount * (100 - protectionLevel[msg.sender])) / 100;
            return super.transfer(to, protectedAmount);
        }
        return super.transfer(to, amount);
    }
    
    /**
     * @dev TransferFrom with protection check
     */
    function transferFrom(address from, address to, uint256 amount) public override returns (bool) {
        if (isProtected[from] && protectionLevel[from] > 0) {
            // Apply protection: reduce transfer amount based on protection level  
            uint256 protectedAmount = (amount * (100 - protectionLevel[from])) / 100;
            return super.transferFrom(from, to, protectedAmount);
        }
        return super.transferFrom(from, to, amount);
    }
    
    /**
     * @dev Set shield mint cost (owner only)
     */
    function setShieldMintCost(uint256 newCost) external onlyOwner {
        shieldMintCost = newCost;
    }
    
    /**
     * @dev Set max shields per user (owner only)
     */
    function setMaxShieldsPerUser(uint256 newMax) external onlyOwner {
        maxShieldsPerUser = newMax;
    }
    
    /**
     * @dev Get shield info by serial number
     */
    function getShieldInfo(uint256 serialNumber) external view returns (Shield memory) {
        return shields[serialNumber];
    }
    
    /**
     * @dev Check if address is protected
     */
    function getProtectionInfo(address user) external view returns (bool protected, uint256 level, uint256 activeShields) {
        return (
            isProtected[user], 
            protectionLevel[user], 
            this.getActiveShieldCount(user)
        );
    }
}