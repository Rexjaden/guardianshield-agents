// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title GuardianStaking
 * @dev Simple staking contract for GUARD tokens.
 */
contract GuardianStaking is Ownable {
    IERC20 public immutable guardToken;
    uint256 public rewardRate; // e.g., tokens per block or per second

    struct StakeInfo {
        uint256 amount;
        uint256 rewardDebt;
        uint256 lastStaked;
    }

    mapping(address => StakeInfo) public stakes;

    event Staked(address indexed user, uint256 amount);
    event Unstaked(address indexed user, uint256 amount);
    event RewardClaimed(address indexed user, uint256 amount);

    constructor(address _guardToken, uint256 _rewardRate) {
        guardToken = IERC20(_guardToken);
        rewardRate = _rewardRate;
    }

    function stake(uint256 amount) external {
        require(amount > 0, "Cannot stake 0");
        guardToken.transferFrom(msg.sender, address(this), amount);
        stakes[msg.sender].amount += amount;
        stakes[msg.sender].lastStaked = block.timestamp;
        emit Staked(msg.sender, amount);
    }

    function unstake(uint256 amount) external {
        require(stakes[msg.sender].amount >= amount, "Not enough staked");
        stakes[msg.sender].amount -= amount;
        guardToken.transfer(msg.sender, amount);
        emit Unstaked(msg.sender, amount);
    }

    // Add reward calculation and claim logic as needed
}
