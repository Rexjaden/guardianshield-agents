#!/bin/bash
# 📜 GuardianShield Smart Contracts Package
# =========================================
# This script extracts the active Smart Contracts for the GuardianShield website.
# Use these in Remix IDE (remix.ethereum.org) or Hardhat.

WORK_DIR="guardianshield_contracts"

echo "📦 Setting up Smart Contract Workspace: $WORK_DIR..."

rm -rf $WORK_DIR
mkdir -p $WORK_DIR

# 1. GuardianTokenSale.sol (The Token Sale Engine)
echo "📄 Extracting GuardianTokenSale.sol..."
cat << 'SOLIDITY_EOF' > $WORK_DIR/GuardianTokenSale.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "./ChainlinkPriceOracle.sol";

interface IPriceOracle {
    function ethToUsd(uint256 ethAmount) external view returns (uint256 usdValue);
    function usdToEth(uint256 usdAmount) external view returns (uint256 ethValue);
    function getLatestPrice() external view returns (uint256 price, uint256 timestamp, bool success);
    function getTokenPriceInUsd(uint256 tokenPriceInEth) external view returns (uint256 tokenPriceInUsd);
}

/**
 * @title GuardianTokenSale
 * @dev Professional token sale contract with multiple payment methods and security features
 */
contract GuardianTokenSale is Ownable, ReentrancyGuard, Pausable {
    IERC20 public immutable guardToken;
    IPriceOracle public priceOracle;
    
    // Price feed configuration
    bool public useOracle = true;
    uint256 public fallbackEthPrice = 3000e8; // $3000 with 8 decimals
    
    // Sale Configuration
    struct SaleStage {
        uint256 price;          // Price per token in wei
        uint256 maxTokens;      // Maximum tokens for this stage
        uint256 soldTokens;     // Tokens sold in this stage
        bool active;            // Is this stage active
        string name;            // Stage name (e.g., "Pre-Sale", "Public Sale")
    }
    
    // Payment tokens accepted (USDC, USDT, etc.)
    mapping(address => bool) public acceptedTokens;
    mapping(address => uint256) public tokenDecimals;
    
    // Sale stages
    mapping(uint256 => SaleStage) public saleStages;
    uint256 public currentStage = 1;
    uint256 public totalStages = 0;
    
    // Purchase tracking
    mapping(address => uint256) public purchasedTokens;
    mapping(address => uint256) public totalContributed;
    
    // Treasury and limits
    address public treasury;
    address public guardianTreasury; // Multi-sig treasury contract
    uint256 public minPurchase = 0.01 ether;  // Minimum ETH purchase
    uint256 public maxPurchase = 10 ether;    // Maximum ETH purchase
    
    // Referral system
    mapping(address => address) public referrers;
    mapping(address => uint256) public referralRewards;
    uint256 public referralRate = 500; // 5% in basis points
    
    // Events
    event TokensPurchased(
        address indexed buyer, 
        uint256 ethAmount, 
        uint256 tokenAmount, 
        uint256 stage
    );
    event TokensPurchasedWithToken(
        address indexed buyer,
        address indexed token,
        uint256 tokenAmount,
        uint256 guardTokens,
        uint256 stage
    );
    event StageUpdated(uint256 indexed stage, uint256 price, uint256 maxTokens);
    event ReferralReward(address indexed referrer, address indexed buyer, uint256 reward);
    event PriceOracleUpdated(address indexed newOracle);
    event OracleToggled(bool enabled);
    event FallbackPriceUpdated(uint256 newPrice);
    
    constructor(
        address _guardToken,
        address _treasury,
        address _guardianTreasury,
        address _priceOracle
    ) Ownable(msg.sender) {
        guardToken = IERC20(_guardToken);
        treasury = _treasury;
        guardianTreasury = _guardianTreasury;
        
        if (_priceOracle != address(0)) {
            priceOracle = IPriceOracle(_priceOracle);
        }
        
        // Set up initial sale stages with USD-based pricing
        _setupInitialStages();
    }
    
    function _setupInitialStages() private {
        // Pre-Sale Stage - $0.001 per token (50% discount from $0.002)
        saleStages[1] = SaleStage({
            price: _usdToEthPrice(0.001 ether), // $0.001 per token
            maxTokens: 50_000_000 * 10**18,
            soldTokens: 0,
            active: true,
            name: "Pre-Sale"
        });
        
        // Public Sale Stage - $0.0015 per token (25% discount from $0.002)
        saleStages[2] = SaleStage({
            price: _usdToEthPrice(0.0015 ether), // $0.0015 per token
            maxTokens: 100_000_000 * 10**18,
            soldTokens: 0,
            active: false,
            name: "Public Sale"
        });
        
        // Final Sale Stage - $0.002 per token (normal price)
        saleStages[3] = SaleStage({
            price: _usdToEthPrice(0.002 ether), // $0.002 per token
            maxTokens: 150_000_000 * 10**18,
            soldTokens: 0,
            active: false,
            name: "Final Sale"
        });
        
        totalStages = 3;
    }
    
    /**
     * @dev Purchase tokens with ETH
     */
    function buyTokens(address referrer) external payable nonReentrant whenNotPaused {
        require(msg.value >= minPurchase, "Below minimum purchase");
        require(msg.value <= maxPurchase, "Above maximum purchase");
        
        SaleStage storage stage = saleStages[currentStage];
        require(stage.active, "Current stage not active");
        
        uint256 tokenAmount = (msg.value * 10**18) / stage.price;
        require(stage.soldTokens + tokenAmount <= stage.maxTokens, "Stage limit exceeded");
        
        // Update stage
        stage.soldTokens += tokenAmount;
        
        // Update buyer tracking
        purchasedTokens[msg.sender] += tokenAmount;
        totalContributed[msg.sender] += msg.value;
        
        // Handle referral
        if (referrer != address(0) && referrer != msg.sender) {
            referrers[msg.sender] = referrer;
            uint256 referralReward = (msg.value * referralRate) / 10000;
            referralRewards[referrer] += referralReward;
            
            // Send referral reward
            (bool referralSuccess, ) = referrer.call{value: referralReward}("");
            if (referralSuccess) {
                emit ReferralReward(referrer, msg.sender, referralReward);
            }
        }
        
        // Transfer tokens to buyer
        require(guardToken.transfer(msg.sender, tokenAmount), "Token transfer failed");
        
        // Send ETH to multi-sig treasury (minus referral if applicable)
        uint256 treasuryAmount = msg.value;
        if (referrers[msg.sender] != address(0)) {
            treasuryAmount -= (msg.value * referralRate) / 10000;
        }
        
        // Send to GuardianTreasury multi-sig contract
        (bool success, ) = guardianTreasury.call{value: treasuryAmount}("");
        require(success, "Treasury transfer failed");
        
        emit TokensPurchased(msg.sender, msg.value, tokenAmount, currentStage);
        
        // Check if stage is complete and advance
        if (stage.soldTokens >= stage.maxTokens) {
            _advanceStage();
        }
    }
    
    /**
     * @dev Purchase tokens with ERC-20 tokens (USDC, USDT, etc.)
     */
    function buyTokensWithToken(
        address token,
        uint256 tokenAmount,
        address referrer
    ) external nonReentrant whenNotPaused {
        require(acceptedTokens[token], "Token not accepted");
        require(tokenAmount > 0, "Invalid token amount");
        
        SaleStage storage stage = saleStages[currentStage];
        require(stage.active, "Current stage not active");
        
        // Calculate GUARD tokens based on USD value using oracle
        uint256 usdValue = tokenAmount;
        if (tokenDecimals[token] != 18) {
            usdValue = tokenAmount * (10**(18 - tokenDecimals[token]));
        }
        
        // Convert USD to ETH using oracle
        uint256 ethEquivalent = _usdToEth(usdValue);
        uint256 guardTokens = (ethEquivalent * 10**18) / stage.price;
        
        require(stage.soldTokens + guardTokens <= stage.maxTokens, "Stage limit exceeded");
        
        // Transfer payment token from buyer
        IERC20(token).transferFrom(msg.sender, treasury, tokenAmount);
        
        // Update tracking
        stage.soldTokens += guardTokens;
        purchasedTokens[msg.sender] += guardTokens;
        
        // Handle referral in tokens
        if (referrer != address(0) && referrer != msg.sender) {
            referrers[msg.sender] = referrer;
            uint256 referralReward = (guardTokens * referralRate) / 10000;
            referralRewards[referrer] += referralReward;
            
            require(guardToken.transfer(referrer, referralReward), "Referral reward failed");
            emit ReferralReward(referrer, msg.sender, referralReward);
        }
        
        // Transfer GUARD tokens to buyer
        require(guardToken.transfer(msg.sender, guardTokens), "Token transfer failed");
        
        emit TokensPurchasedWithToken(msg.sender, token, tokenAmount, guardTokens, currentStage);
        
        // Check if stage is complete
        if (stage.soldTokens >= stage.maxTokens) {
            _advanceStage();
        }
    }
    
    /**
     * @dev Advance to next sale stage
     */
    function _advanceStage() private {
        if (currentStage < totalStages) {
            saleStages[currentStage].active = false;
            currentStage++;
            if (currentStage <= totalStages) {
                saleStages[currentStage].active = true;
            }
        }
    }
    
    /**
     * @dev Get current sale information with oracle status
     */
    function getCurrentSaleInfo() external view returns (
        uint256 stage,
        string memory stageName,
        uint256 price,
        uint256 maxTokens,
        uint256 soldTokens,
        uint256 remainingTokens,
        bool active,
        uint256 priceInUsd,
        bool oracleActive
    ) {
        SaleStage memory currentSaleStage = saleStages[currentStage];
        (uint256 ethPrice, bool fromOracle) = getCurrentEthPrice();
        uint256 tokenPriceUsd = this.getTokenPriceInUsd(currentStage);
        
        return (
            currentStage,
            currentSaleStage.name,
            currentSaleStage.price,
            currentSaleStage.maxTokens,
            currentSaleStage.soldTokens,
            currentSaleStage.maxTokens - currentSaleStage.soldTokens,
            currentSaleStage.active,
            tokenPriceUsd,
            useOracle && fromOracle
        );
    }
    
    /**
     * @dev Calculate tokens for ETH amount
     */
    function calculateTokens(uint256 ethAmount) external view returns (uint256) {
        SaleStage memory stage = saleStages[currentStage];
        return (ethAmount * 10**18) / stage.price;
    }
    
    /**
     * @dev Get current ETH price in USD
     */
    function getCurrentEthPrice() public view returns (uint256 price, bool fromOracle) {
        if (useOracle && address(priceOracle) != address(0)) {
            (uint256 oraclePrice, , bool success) = priceOracle.getLatestPrice();
            if (success) {
                return (oraclePrice, true);
            }
        }
        return (fallbackEthPrice, false);
    }
    
    /**
     * @dev Convert USD amount to ETH using oracle or fallback
     */
    function _usdToEth(uint256 usdAmount) internal view returns (uint256) {
        if (useOracle && address(priceOracle) != address(0)) {
            try priceOracle.usdToEth(usdAmount) returns (uint256 ethAmount) {
                return ethAmount;
            } catch {
                // Fallback calculation
                return (usdAmount * (10**8)) / fallbackEthPrice;
            }
        } else {
            // Fallback calculation: USD (18 decimals) * 1e8 / price (8 decimals) = ETH (18 decimals)
            return (usdAmount * (10**8)) / fallbackEthPrice;
        }
    }
    
    /**
     * @dev Convert USD price to ETH price for token pricing
     */
    function _usdToEthPrice(uint256 usdPrice) internal view returns (uint256) {
        return _usdToEth(usdPrice);
    }
    
    /**
     * @dev Get token price in USD
     */
    function getTokenPriceInUsd(uint256 stage) external view returns (uint256) {
        require(stage > 0 && stage <= totalStages, "Invalid stage");
        SaleStage memory stageData = saleStages[stage];
        
        if (useOracle && address(priceOracle) != address(0)) {
            try priceOracle.getTokenPriceInUsd(stageData.price) returns (uint256 usdPrice) {
                return usdPrice;
            } catch {
                // Fallback calculation
                return (stageData.price * fallbackEthPrice) / (10**8);
            }
        } else {
            // Fallback calculation: ETH price * ETH amount / 1e8
            return (stageData.price * fallbackEthPrice) / (10**8);
        }
    }
    
    // Admin functions
    function addAcceptedToken(address token, uint256 decimals) external onlyOwner {
        acceptedTokens[token] = true;
        tokenDecimals[token] = decimals;
    }
    
    function removeAcceptedToken(address token) external onlyOwner {
        acceptedTokens[token] = false;
    }
    
    function updateSaleStage(
        uint256 stage,
        uint256 price,
        uint256 maxTokens,
        bool active,
        string calldata name
    ) external onlyOwner {
        require(stage > 0 && stage <= totalStages, "Invalid stage");
        saleStages[stage] = SaleStage(price, maxTokens, saleStages[stage].soldTokens, active, name);
        emit StageUpdated(stage, price, maxTokens);
    }
    
    function setCurrentStage(uint256 stage) external onlyOwner {
        require(stage > 0 && stage <= totalStages, "Invalid stage");
        saleStages[currentStage].active = false;
        currentStage = stage;
        saleStages[currentStage].active = true;
    }
    
    function setPurchaseLimits(uint256 min, uint256 max) external onlyOwner {
        minPurchase = min;
        maxPurchase = max;
    }
    
    function setReferralRate(uint256 rate) external onlyOwner {
        require(rate <= 1000, "Rate too high"); // Max 10%
        referralRate = rate;
    }
    
    function setTreasury(address _treasury) external onlyOwner {
        treasury = _treasury;
    }
    
    function setGuardianTreasury(address _guardianTreasury) external onlyOwner {
        require(_guardianTreasury != address(0), "Invalid treasury address");
        guardianTreasury = _guardianTreasury;
    }
    
    /**
     * @dev Set the price oracle contract
     */
    function setPriceOracle(address _priceOracle) external onlyOwner {
        require(_priceOracle != address(0), "Invalid oracle address");
        priceOracle = IPriceOracle(_priceOracle);
        emit PriceOracleUpdated(_priceOracle);
    }
    
    /**
     * @dev Toggle oracle usage on/off
     */
    function toggleOracle(bool _useOracle) external onlyOwner {
        useOracle = _useOracle;
        emit OracleToggled(_useOracle);
    }
    
    /**
     * @dev Set fallback ETH price (with 8 decimals)
     */
    function setFallbackEthPrice(uint256 _fallbackPrice) external onlyOwner {
        require(_fallbackPrice > 0, "Invalid price");
        fallbackEthPrice = _fallbackPrice;
        emit FallbackPriceUpdated(_fallbackPrice);
    }
    
    /**
     * @dev Update sale stage prices based on current USD rates
     */
    function updateStagesPricing() external onlyOwner {
        // Update all stages with current USD-to-ETH conversion
        if (totalStages >= 1) {
            saleStages[1].price = _usdToEthPrice(0.001 ether); // $0.001
        }
        if (totalStages >= 2) {
            saleStages[2].price = _usdToEthPrice(0.0015 ether); // $0.0015
        }
        if (totalStages >= 3) {
            saleStages[3].price = _usdToEthPrice(0.002 ether); // $0.002
        }
    }
    
    function withdrawTokens(address token, uint256 amount) external onlyOwner {
        IERC20(token).transfer(owner(), amount);
    }
    
    function emergencyWithdraw() external onlyOwner {
        (bool success, ) = owner().call{value: address(this).balance}("");
        require(success, "Withdrawal failed");
    }
    
    function pause() external onlyOwner {
        _pause();
    }
    
    function unpause() external onlyOwner {
        _unpause();
    }
}
SOLIDITY_EOF

# 2. ChainlinkPriceOracle.sol (The Pricing Logic)
echo "📄 Extracting ChainlinkPriceOracle.sol..."
cat << 'SOLIDITY_EOF' > $WORK_DIR/ChainlinkPriceOracle.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@chainlink/contracts/src/v0.8/shared/interfaces/AggregatorV3Interface.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title ChainlinkPriceOracle
 * @dev Chainlink price oracle integration for ETH/USD price feeds
 */
contract ChainlinkPriceOracle is Ownable {
    AggregatorV3Interface internal immutable ethUsdPriceFeed;
    
    // Fallback price in case oracle fails (in USD with 8 decimals)
    uint256 public fallbackPrice = 3000_00000000; // $3000 USD
    uint256 public constant PRICE_DECIMALS = 8;
    uint256 public constant STALENESS_THRESHOLD = 3600; // 1 hour in seconds
    
    // Events
    event PriceUpdated(int256 price, uint256 timestamp);
    event FallbackPriceUsed(uint256 price, string reason);
    event FallbackPriceSet(uint256 oldPrice, uint256 newPrice);
    
    constructor(address _priceFeedAddress) Ownable(msg.sender) {
        // ETH/USD Price Feed addresses:
        // Mainnet: 0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419
        // Sepolia: 0x694AA1769357215DE4FAC081bf1f309aDC325306
        // Polygon: 0xF9680D99D6C9589e2a93a78A04A279e509205945
        ethUsdPriceFeed = AggregatorV3Interface(_priceFeedAddress);
    }
    
    /**
     * @dev Get the latest ETH price in USD
     * @return price The current price with 8 decimal places
     * @return timestamp When the price was last updated
     * @return success Whether the price fetch was successful
     */
    function getLatestPrice() public view returns (uint256 price, uint256 timestamp, bool success) {
        try ethUsdPriceFeed.latestRoundData() returns (
            uint80 roundId,
            int256 answer,
            uint256 startedAt,
            uint256 updatedAt,
            uint80 answeredInRound
        ) {
            // Check if price is positive and recent
            if (answer > 0 && updatedAt > 0) {
                // Check if price is not stale (within threshold)
                if (block.timestamp - updatedAt <= STALENESS_THRESHOLD) {
                    return (uint256(answer), updatedAt, true);
                }
            }
            // If we reach here, data is stale or invalid
            return (fallbackPrice, block.timestamp, false);
        } catch {
            // If oracle call fails, return fallback price
            return (fallbackPrice, block.timestamp, false);
        }
    }
    
    /**
     * @dev Convert ETH amount to USD value
     * @param ethAmount Amount of ETH in wei (18 decimals)
     * @return usdValue USD value with 18 decimals for consistency
     */
    function ethToUsd(uint256 ethAmount) external view returns (uint256 usdValue) {
        (uint256 ethPrice, , bool success) = getLatestPrice();
        
        if (!success) {
            ethPrice = fallbackPrice;
        }
        
        // ETH amount (18 decimals) * ETH price (8 decimals) / 1e8 = USD value (18 decimals)
        usdValue = (ethAmount * ethPrice) / (10**PRICE_DECIMALS);
        
        return usdValue;
    }
    
    /**
     * @dev Convert USD amount to ETH value
     * @param usdAmount Amount of USD with 18 decimals
     * @return ethValue ETH value in wei (18 decimals)
     */
    function usdToEth(uint256 usdAmount) external view returns (uint256 ethValue) {
        (uint256 ethPrice, , bool success) = getLatestPrice();
        
        if (!success) {
            ethPrice = fallbackPrice;
        }
        
        // USD amount (18 decimals) * 1e8 / ETH price (8 decimals) = ETH value (18 decimals)
        ethValue = (usdAmount * (10**PRICE_DECIMALS)) / ethPrice;
        
        return ethValue;
    }
    
    /**
     * @dev Get price feed information
     */
    function getPriceFeedInfo() external view returns (
        string memory description,
        uint256 decimals,
        uint256 version
    ) {
        description = ethUsdPriceFeed.description();
        decimals = ethUsdPriceFeed.decimals();
        version = ethUsdPriceFeed.version();
    }
    
    /**
     * @dev Check if price feed is healthy
     */
    function isPriceFeedHealthy() external view returns (bool healthy, string memory status) {
        (uint256 price, uint256 timestamp, bool success) = getLatestPrice();
        
        if (!success) {
            return (false, "Price feed failed or stale");
        }
        
        if (price == fallbackPrice) {
            return (false, "Using fallback price");
        }
        
        return (true, "Price feed healthy");
    }
    
    /**
     * @dev Emergency function to set fallback price
     */
    function setFallbackPrice(uint256 _fallbackPrice) external onlyOwner {
        require(_fallbackPrice > 0, "Invalid fallback price");
        uint256 oldPrice = fallbackPrice;
        fallbackPrice = _fallbackPrice;
        emit FallbackPriceSet(oldPrice, _fallbackPrice);
    }
    
    /**
     * @dev Get historical price data (if available)
     */
    function getHistoricalPrice(uint80 _roundId) external view returns (
        uint256 price,
        uint256 timestamp,
        bool success
    ) {
        try ethUsdPriceFeed.getRoundData(_roundId) returns (
            uint80 roundId,
            int256 answer,
            uint256 startedAt,
            uint256 updatedAt,
            uint80 answeredInRound
        ) {
            if (answer > 0) {
                return (uint256(answer), updatedAt, true);
            }
            return (0, 0, false);
        } catch {
            return (0, 0, false);
        }
    }
    
    /**
     * @dev Calculate token price in USD based on ETH price
     * @param tokenPriceInEth Price per token in ETH (wei)
     * @return tokenPriceInUsd Price per token in USD (18 decimals)
     */
    function getTokenPriceInUsd(uint256 tokenPriceInEth) external view returns (uint256 tokenPriceInUsd) {
        return this.ethToUsd(tokenPriceInEth);
    }
}
SOLIDITY_EOF

# 3. GuardianShieldToken.sol (The Token Itself - Example)
echo "📄 Extracting GuardianShieldToken.sol..."
cat << 'SOLIDITY_EOF' > $WORK_DIR/GuardianShieldToken.sol
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

SOLIDITY_EOF

echo ""
echo "✅ Contracts Extracted Successfully!"
echo "---------------------------------------------------"
echo "📂 Location: $WORK_DIR/"
echo "---------------------------------------------------"
echo "👉 HOW TO USE:"
echo "1. Go to https://remix.ethereum.org"
echo "2. Create new files in Remix with the same names."
echo "3. Copy the content from the files in '$WORK_DIR' to Remix."
echo "4. Compile and Deploy."
echo "---------------------------------------------------"
