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