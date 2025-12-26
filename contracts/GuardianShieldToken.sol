// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title GuardianShieldToken
 * @dev ERC-721 NFT with unique serial numbers, metadata, and event tracking for theft prevention.
 *      Designed for L1/L2 and future Flare integration (metadata, multi-chain, etc).
 */
contract GuardianShieldToken is ERC721, Ownable {
    // Serial number to tokenId mapping
    mapping(uint256 => uint256) public serialToTokenId;
    // TokenId to serial number mapping
    mapping(uint256 => uint256) public tokenIdToSerial;
    // Token metadata URI (can point to Flare or IPFS)
    mapping(uint256 => string) private _tokenURIs;
    // Blacklist for stolen tokens
    mapping(uint256 => bool) public isStolen;
    // Counter for token IDs
    uint256 private _nextTokenId = 1;

    event TokenMinted(address indexed to, uint256 indexed tokenId, uint256 serial, string tokenURI);
    event TokenFlaggedStolen(uint256 indexed tokenId, address indexed by);
    event TokenRecovered(uint256 indexed tokenId, address indexed by);

    constructor() ERC721("GuardianShieldToken", "GST") Ownable(msg.sender) {}

    /**
     * @dev Mint a new token with a unique serial number and metadata URI.
     */
    function mint(address to, uint256 serial, string memory tokenURI_) external onlyOwner returns (uint256) {
        require(serialToTokenId[serial] == 0, "Serial already used");
        uint256 tokenId = _nextTokenId;
        _nextTokenId++;
        _safeMint(to, tokenId);
        serialToTokenId[serial] = tokenId;
        tokenIdToSerial[tokenId] = serial;
        _setTokenURI(tokenId, tokenURI_);
        emit TokenMinted(to, tokenId, serial, tokenURI_);
        return tokenId;
    }

    /**
     * @dev Set the token URI (metadata pointer, e.g., Flare, IPFS).
     */
    function _setTokenURI(uint256 tokenId, string memory tokenURI_) internal {
        _tokenURIs[tokenId] = tokenURI_;
    }

    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        return _tokenURIs[tokenId];
    }

    /**
     * @dev Flag a token as stolen (can be extended for Flare/multi-chain reporting).
     */
    function flagStolen(uint256 tokenId) external onlyOwner {
        isStolen[tokenId] = true;
        emit TokenFlaggedStolen(tokenId, msg.sender);
    }

    /**
     * @dev Recover a stolen token (remove from blacklist).
     */
    function recoverToken(uint256 tokenId) external onlyOwner {
        isStolen[tokenId] = false;
        emit TokenRecovered(tokenId, msg.sender);
    }

    /**
     * @dev Override update to prevent transfer of stolen tokens.
     */
    function _update(address to, uint256 tokenId, address auth) internal override returns (address) {
        require(!isStolen[tokenId], "Token is flagged as stolen");
        return super._update(to, tokenId, auth);
    }

    // TODO: Add Flare integration hooks for metadata and multi-chain support
}
