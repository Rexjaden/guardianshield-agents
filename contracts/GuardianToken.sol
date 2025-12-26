// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title GuardianToken
 * @dev ERC-20 token for Guardian project with staged release logic.
 */
contract GuardianToken is ERC20, Ownable {
    uint256 public constant MAX_SUPPLY = 5_000_000_000 * 10**18;
    uint256 public constant INITIAL_STAGE_SUPPLY = 300_000_000 * 10**18;
    uint256 public totalMinted;

    event StageMint(address indexed to, uint256 amount, uint256 totalMinted);

    constructor(address initialSaleAddress) ERC20("Guardian Token", "GUARD") Ownable(msg.sender) {
        _mint(initialSaleAddress, INITIAL_STAGE_SUPPLY);
        totalMinted = INITIAL_STAGE_SUPPLY;
        emit StageMint(initialSaleAddress, INITIAL_STAGE_SUPPLY, totalMinted);
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
     * @dev Burn tokens from caller's balance.
     */
    function burn(uint256 amount) external {
        _burn(msg.sender, amount);
    }
}
