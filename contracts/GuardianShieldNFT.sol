// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

/**
 * @title GuardianShieldNFT
 * @dev Security Shield Tokens with individual serial numbers, theft tracking, and burn/remint protocol
 */
contract GuardianShieldNFT is ERC721, ERC721Enumerable, ERC721URIStorage, Ownable, ReentrancyGuard, Pausable {
    
    // Shield token structure
    struct ShieldToken {
        uint256 serialNumber;      // Unique serial number
        string shieldType;         // Type of shield (Basic, Premium, Elite, etc.)
        uint256 protectionLevel;   // Protection level (1-100)
        uint256 mintTimestamp;     // When it was minted
        address originalOwner;     // Original owner for theft recovery
        bool isStolen;             // Theft status
        uint256 stolenTimestamp;   // When it was reported stolen
        string metadata;           // Additional metadata
    }
    
    // Token tracking
    mapping(uint256 => ShieldToken) public shieldTokens;
    mapping(uint256 => bool) private _serialNumberExists;
    mapping(address => uint256[]) private _userTokens;
    
    // Theft protection
    mapping(uint256 => address) public stolenTokenReporter;
    mapping(address => bool) public authorizedReporters;
    address public treasuryAddress;
    
    // Serial number management
    uint256 private _nextSerialNumber = 100001; // Start from 100001
    uint256 public totalMinted = 0;
    uint256 public totalBurned = 0;
    uint256 public totalRecovered = 0;
    
    // Shield types configuration
    mapping(string => uint256) public shieldTypeCost;
    mapping(string => uint256) public shieldTypeProtection;
    
    // Events
    event ShieldMinted(uint256 indexed tokenId, uint256 serialNumber, address indexed owner, string shieldType);
    event ShieldStolen(uint256 indexed tokenId, uint256 serialNumber, address indexed reporter, uint256 timestamp);
    event ShieldBurned(uint256 indexed tokenId, uint256 serialNumber, address indexed burner);
    event ShieldRecovered(uint256 indexed newTokenId, uint256 serialNumber, address indexed originalOwner);
    event ShieldTypeAdded(string shieldType, uint256 cost, uint256 protection);
    
    constructor(
        address _treasuryAddress
    ) ERC721("GuardianShield Security Token", "GSST") Ownable(msg.sender) {
        treasuryAddress = _treasuryAddress;
        authorizedReporters[msg.sender] = true;
        
        // Initialize shield types
        _initializeShieldTypes();
    }
    
    function _initializeShieldTypes() private {
        // Basic Shield
        shieldTypeCost["Basic"] = 0.01 ether;
        shieldTypeProtection["Basic"] = 25;
        
        // Premium Shield  
        shieldTypeCost["Premium"] = 0.05 ether;
        shieldTypeProtection["Premium"] = 50;
        
        // Elite Shield
        shieldTypeCost["Elite"] = 0.1 ether;
        shieldTypeProtection["Elite"] = 75;
        
        // Guardian Shield (Highest tier)
        shieldTypeCost["Guardian"] = 0.25 ether;
        shieldTypeProtection["Guardian"] = 100;
    }
    
    /**
     * @dev Mint a new Shield Token with unique serial number
     */
    function mintShield(
        address to,
        string memory shieldType,
        string memory metadata
    ) external payable nonReentrant whenNotPaused returns (uint256) {
        require(shieldTypeProtection[shieldType] > 0, "Invalid shield type");
        require(msg.value >= shieldTypeCost[shieldType], "Insufficient payment");
        
        uint256 tokenId = totalSupply() + 1;
        uint256 serialNumber = _generateSerialNumber();
        
        // Create shield token
        shieldTokens[tokenId] = ShieldToken({
            serialNumber: serialNumber,
            shieldType: shieldType,
            protectionLevel: shieldTypeProtection[shieldType],
            mintTimestamp: block.timestamp,
            originalOwner: to,
            isStolen: false,
            stolenTimestamp: 0,
            metadata: metadata
        });
        
        _serialNumberExists[serialNumber] = true;
        totalMinted++;
        
        // Mint the NFT
        _safeMint(to, tokenId);
        
        // Set token URI
        string memory tokenURIStr = _generateTokenURI(tokenId);
        _setTokenURI(tokenId, tokenURIStr);
        
        // Send payment to treasury
        if (msg.value > 0) {
            (bool success, ) = treasuryAddress.call{value: msg.value}("");
            require(success, "Treasury payment failed");
        }
        
        emit ShieldMinted(tokenId, serialNumber, to, shieldType);
        
        return tokenId;
    }
    
    /**
     * @dev Batch mint multiple shield tokens
     */
    function batchMintShields(
        address to,
        string[] memory shieldTypes,
        string[] memory metadataArray,
        uint256 quantity
    ) external payable nonReentrant whenNotPaused returns (uint256[] memory) {
        require(quantity > 0 && quantity <= 50, "Invalid quantity");
        require(shieldTypes.length == quantity, "Mismatched arrays");
        require(metadataArray.length == quantity, "Mismatched arrays");
        
        uint256 totalCost = 0;
        for (uint256 i = 0; i < quantity; i++) {
            require(shieldTypeProtection[shieldTypes[i]] > 0, "Invalid shield type");
            totalCost += shieldTypeCost[shieldTypes[i]];
        }
        require(msg.value >= totalCost, "Insufficient payment");
        
        uint256[] memory tokenIds = new uint256[](quantity);
        
        for (uint256 i = 0; i < quantity; i++) {
            uint256 tokenId = totalSupply() + 1 + i;
            uint256 serialNumber = _generateSerialNumber();
            
            // Create shield token
            shieldTokens[tokenId] = ShieldToken({
                serialNumber: serialNumber,
                shieldType: shieldTypes[i],
                protectionLevel: shieldTypeProtection[shieldTypes[i]],
                mintTimestamp: block.timestamp,
                originalOwner: to,
                isStolen: false,
                stolenTimestamp: 0,
                metadata: metadataArray[i]
            });
            
            _serialNumberExists[serialNumber] = true;
            totalMinted++;
            
            // Mint the NFT
            _safeMint(to, tokenId);
            
            // Set token URI
            string memory tokenURIStr = _generateTokenURI(tokenId);
            _setTokenURI(tokenId, tokenURIStr);
            
            tokenIds[i] = tokenId;
            
            emit ShieldMinted(tokenId, serialNumber, to, shieldTypes[i]);
        }
        
        return tokenIds;
    }
    
    /**
     * @dev Report a token as stolen
     */
    function reportStolen(uint256 tokenId) external {
        require(_ownerOf(tokenId) != address(0), "Token does not exist");
        require(
            ownerOf(tokenId) == msg.sender || authorizedReporters[msg.sender],
            "Not authorized to report"
        );
        require(!shieldTokens[tokenId].isStolen, "Already reported stolen");
        
        shieldTokens[tokenId].isStolen = true;
        shieldTokens[tokenId].stolenTimestamp = block.timestamp;
        stolenTokenReporter[tokenId] = msg.sender;
        
        emit ShieldStolen(
            tokenId,
            shieldTokens[tokenId].serialNumber,
            msg.sender,
            block.timestamp
        );
    }
    
    /**
     * @dev Burn a stolen token (only authorized reporters)
     */
    function burnStolenToken(uint256 tokenId) external nonReentrant {
        require(_ownerOf(tokenId) != address(0), "Token does not exist");
        require(authorizedReporters[msg.sender], "Not authorized to burn");
        require(shieldTokens[tokenId].isStolen, "Token not reported stolen");
        
        uint256 serialNumber = shieldTokens[tokenId].serialNumber;
        address originalOwner = shieldTokens[tokenId].originalOwner;
        
        // Burn the token
        _burn(tokenId);
        totalBurned++;
        
        emit ShieldBurned(tokenId, serialNumber, msg.sender);
        
        // Automatically remint to treasury for recovery
        _remintToTreasury(serialNumber, originalOwner, tokenId);
    }
    
    /**
     * @dev Internal function to remint burned token to treasury
     */
    function _remintToTreasury(uint256 originalSerialNumber, address originalOwner, uint256 burnedTokenId) private {
        uint256 newTokenId = totalSupply() + 1;
        ShieldToken memory originalToken = shieldTokens[burnedTokenId];
        
        // Create new token with same serial number
        shieldTokens[newTokenId] = ShieldToken({
            serialNumber: originalSerialNumber, // Keep original serial number
            shieldType: originalToken.shieldType,
            protectionLevel: originalToken.protectionLevel,
            mintTimestamp: block.timestamp, // New mint timestamp
            originalOwner: originalOwner, // Keep original owner reference
            isStolen: false, // Reset stolen status
            stolenTimestamp: 0,
            metadata: string(abi.encodePacked(originalToken.metadata, " [RECOVERED]"))
        });
        
        // Mint to treasury
        _safeMint(treasuryAddress, newTokenId);
        
        // Set token URI
        string memory tokenURIStr = _generateRecoveryTokenURI(newTokenId);
        _setTokenURI(newTokenId, tokenURIStr);
        
        totalRecovered++;
        
        emit ShieldRecovered(newTokenId, originalSerialNumber, originalOwner);
    }
    
    /**
     * @dev Return recovered token to rightful owner (treasury function)
     */
    function returnToOwner(uint256 tokenId, address rightfulOwner) external {
        require(msg.sender == treasuryAddress || owner() == msg.sender, "Only treasury or owner");
        require(_ownerOf(tokenId) != address(0), "Token does not exist");
        require(ownerOf(tokenId) == treasuryAddress, "Token not in treasury");
        require(shieldTokens[tokenId].originalOwner == rightfulOwner, "Not the rightful owner");
        
        // Transfer from treasury to rightful owner
        _transfer(treasuryAddress, rightfulOwner, tokenId);
        
        // Update metadata to show returned
        string memory currentURI = tokenURI(tokenId);
        string memory newURI = string(abi.encodePacked(currentURI, " [RETURNED]"));
        _setTokenURI(tokenId, newURI);
    }
    
    /**
     * @dev Generate unique serial number
     */
    function _generateSerialNumber() private returns (uint256) {
        uint256 serialNumber = _nextSerialNumber;
        _nextSerialNumber++;
        return serialNumber;
    }
    
    /**
     * @dev Generate token URI with shield information
     */
    function _generateTokenURI(uint256 tokenId) private view returns (string memory) {
        ShieldToken memory token = shieldTokens[tokenId];
        
        // Simplified JSON without base64 encoding to avoid stack depth issues
        string memory json = string(abi.encodePacked(
            '{"name":"GuardianShield #', _toString(token.serialNumber), '",',
            '"description":"Security Shield Token with theft protection",',
            '"attributes":[',
                '{"trait_type":"Serial Number","value":"', _toString(token.serialNumber), '"},',
                '{"trait_type":"Shield Type","value":"', token.shieldType, '"},',
                '{"trait_type":"Protection Level","value":', _toString(token.protectionLevel), '}',
            ']}'
        ));
        
        return json;
    }
    
    /**
     * @dev Generate recovery token URI
     */
    function _generateRecoveryTokenURI(uint256 tokenId) private view returns (string memory) {
        ShieldToken memory token = shieldTokens[tokenId];
        
        string memory json = string(abi.encodePacked(
            '{"name":"GuardianShield #', _toString(token.serialNumber), ' [RECOVERED]",',
            '"description":"Recovered Security Shield Token awaiting return to owner",',
            '"attributes":[',
                '{"trait_type":"Serial Number","value":"', _toString(token.serialNumber), '"},',
                '{"trait_type":"Shield Type","value":"', token.shieldType, '"},',
                '{"trait_type":"Status","value":"Recovered"}',
            ']}'
        ));
        
        return json;
    }
    
    /**
     * @dev Get token information by serial number
     */
    function getTokenBySerialNumber(uint256 serialNumber) external view returns (
        uint256 tokenId,
        address currentOwner,
        bool exists
    ) {
        if (!_serialNumberExists[serialNumber]) {
            return (0, address(0), false);
        }
        
        // Find token by serial number
        for (uint256 i = 1; i <= totalSupply(); i++) {
            if (_ownerOf(i) != address(0) && shieldTokens[i].serialNumber == serialNumber) {
                return (i, ownerOf(i), true);
            }
        }
        
        return (0, address(0), false);
    }
    
    /**
     * @dev Get all tokens owned by an address
     */
    function getTokensOfOwner(address owner) external view returns (uint256[] memory) {
        uint256 ownerTokenCount = balanceOf(owner);
        uint256[] memory tokenIds = new uint256[](ownerTokenCount);
        uint256 currentIndex = 0;
        
        for (uint256 i = 1; i <= totalSupply() && currentIndex < ownerTokenCount; i++) {
            if (_ownerOf(i) != address(0) && ownerOf(i) == owner) {
                tokenIds[currentIndex] = i;
                currentIndex++;
            }
        }
        
        return tokenIds;
    }
    
    /**
     * @dev Get shield token details
     */
    function getShieldDetails(uint256 tokenId) external view returns (ShieldToken memory) {
        require(_ownerOf(tokenId) != address(0), "Token does not exist");
        return shieldTokens[tokenId];
    }
    
    /**
     * @dev Add new shield type (owner only)
     */
    function addShieldType(
        string memory shieldType,
        uint256 cost,
        uint256 protection
    ) external onlyOwner {
        require(protection > 0 && protection <= 100, "Invalid protection level");
        
        shieldTypeCost[shieldType] = cost;
        shieldTypeProtection[shieldType] = protection;
        
        emit ShieldTypeAdded(shieldType, cost, protection);
    }
    
    /**
     * @dev Add authorized reporter
     */
    function addAuthorizedReporter(address reporter) external onlyOwner {
        authorizedReporters[reporter] = true;
    }
    
    /**
     * @dev Remove authorized reporter
     */
    function removeAuthorizedReporter(address reporter) external onlyOwner {
        authorizedReporters[reporter] = false;
    }
    
    /**
     * @dev Update treasury address
     */
    function updateTreasuryAddress(address newTreasury) external onlyOwner {
        treasuryAddress = newTreasury;
    }
    
    /**
     * @dev Get contract statistics
     */
    function getContractStats() external view returns (
        uint256 _totalMinted,
        uint256 _totalBurned,
        uint256 _totalRecovered,
        uint256 _totalSupply,
        uint256 _nextSerial
    ) {
        return (
            totalMinted,
            totalBurned,
            totalRecovered,
            totalSupply(),
            _nextSerialNumber
        );
    }
    
    // Utility functions - simplified to avoid stack depth issues
    function _toString(uint256 value) private pure returns (string memory) {
        if (value == 0) return "0";
        
        uint256 temp = value;
        uint256 digits;
        while (temp != 0) {
            digits++;
            temp /= 10;
        }
        bytes memory buffer = new bytes(digits);
        while (value != 0) {
            digits -= 1;
            buffer[digits] = bytes1(uint8(48 + uint256(value % 10)));
            value /= 10;
        }
        return string(buffer);
    }
    
    // Emergency functions
    function pause() external onlyOwner {
        _pause();
    }
    
    function unpause() external onlyOwner {
        _unpause();
    }
    
    function emergencyWithdraw() external onlyOwner {
        (bool success, ) = owner().call{value: address(this).balance}("");
        require(success, "Withdrawal failed");
    }
    
    // Required overrides
    function _update(address to, uint256 tokenId, address auth) 
        internal 
        override(ERC721, ERC721Enumerable) 
        returns (address) 
    {
        return super._update(to, tokenId, auth);
    }
    
    function _increaseBalance(address account, uint128 value) 
        internal 
        override(ERC721, ERC721Enumerable) 
    {
        super._increaseBalance(account, value);
    }
    
    function tokenURI(uint256 tokenId) 
        public 
        view 
        override(ERC721, ERC721URIStorage) 
        returns (string memory) 
    {
        return super.tokenURI(tokenId);
    }
    
    function supportsInterface(bytes4 interfaceId) 
        public 
        view 
        override(ERC721, ERC721Enumerable, ERC721URIStorage) 
        returns (bool) 
    {
        return super.supportsInterface(interfaceId);
    }
}