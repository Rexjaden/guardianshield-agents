// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title GuardianLiquidityPool
 * @dev Basic liquidity pool contract for GUARD tokens (for DEX integration).
 */
contract GuardianLiquidityPool is Ownable {
    IERC20 public immutable guardToken;
    IERC20 public immutable shieldToken; // Paired staking token: SHIELD

    uint256 public totalLiquidity;
    mapping(address => uint256) public liquidity;

    event LiquidityAdded(address indexed provider, uint256 guardAmount, uint256 shieldAmount);
    event LiquidityRemoved(address indexed provider, uint256 guardAmount, uint256 shieldAmount);

    constructor(address _guardToken, address _shieldToken) {
        guardToken = IERC20(_guardToken);
        shieldToken = IERC20(_shieldToken);
    }

    function addLiquidity(uint256 guardAmount, uint256 shieldAmount) external {
        guardToken.transferFrom(msg.sender, address(this), guardAmount);
        shieldToken.transferFrom(msg.sender, address(this), shieldAmount);
        liquidity[msg.sender] += guardAmount; // Simplified
        totalLiquidity += guardAmount;
        emit LiquidityAdded(msg.sender, guardAmount, shieldAmount);
    }

    function removeLiquidity(uint256 amount) external {
        require(liquidity[msg.sender] >= amount, "Not enough liquidity");
        liquidity[msg.sender] -= amount;
        totalLiquidity -= amount;
        guardToken.transfer(msg.sender, amount);
        // Shield token withdrawal logic needed
        emit LiquidityRemoved(msg.sender, amount, 0);
    }
}
