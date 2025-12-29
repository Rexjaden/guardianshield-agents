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