// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Guard Token (GAR) - UUPS Upgradeable
/// @notice Max supply, owner-only mint, capped sale, dual-approval burn & withdrawals, Chainlink pricing, upgradeable

import "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";
import "@openzeppelin/contracts-upgradeable/token/ERC20/ERC20Upgradeable.sol";
import "@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable.sol";

interface AggregatorV3Interface {
    function latestRoundData()
        external
        view
        returns (
            uint80 roundId,
            int256 answer,
            uint256 startedAt,
            uint256 updatedAt,
            uint80 answeredInRound
        );
}

contract GuardToken is Initializable, ERC20Upgradeable, OwnableUpgradeable, UUPSUpgradeable {
    // ===== Constants =====
    uint256 public constant MAX_SUPPLY = 5_000_000_000 * 10**18; // 5B GAR
    uint256 public constant INITIAL_SUPPLY = 300_000_000 * 10**18; // 300M GAR
    uint256 public constant MAX_PURCHASE_PER_ADDRESS = 100_000_000 * 10**18; // 100M GAR

    // Token price in USD terms: 0.005 USD per GAR
    uint256 public constant TOKEN_PRICE_USD_8 = 500_000; // 0.005 USD with 8 decimals

    // ===== Branding =====
    string public logoURI;

    // ===== Roles =====
    address public treasurer;

    // ===== Sale state =====
    bool public saleActive;
    mapping(address => uint256) public purchasedFromSale;

    // ===== Chainlink price feed (ETH/USD) =====
    AggregatorV3Interface public priceFeed;

    // ===== Dual-approval ETH withdrawal =====
    struct WithdrawalRequest {
        uint256 amount;
        bool ownerApproved;
        bool treasurerApproved;
        bool executed;
    }

    uint256 public nextWithdrawalId;
    mapping(uint256 => WithdrawalRequest) public withdrawals;

    // ===== Dual-approval burn =====
    struct BurnRequest {
        address account;
        uint256 amount;
        bool ownerApproved;
        bool treasurerApproved;
        bool executed;
    }

    uint256 public nextBurnId;
    mapping(uint256 => BurnRequest) public burnRequests;

    // ===== Events =====
    event TreasurerSet(address indexed treasurer);
    event SaleStatusChanged(bool active);

    event WithdrawalRequested(uint256 indexed id, uint256 amount);
    event WithdrawalApproved(uint256 indexed id, address indexed approver);
    event WithdrawalExecuted(uint256 indexed id, uint256 amount, address indexed to);

    event BurnRequested(uint256 indexed id, address indexed account, uint256 amount);
    event BurnApproved(uint256 indexed id, address indexed approver);
    event BurnExecuted(uint256 indexed id, address indexed account, uint256 amount);

    // ===== Initializer (replaces constructor) =====
    function initialize(address _priceFeed, string memory _logoURI) public initializer {
        __ERC20_init("Guard Token", "GAR");
        __Ownable_init(msg.sender);
        __UUPSUpgradeable_init();

        priceFeed = AggregatorV3Interface(_priceFeed);
        logoURI = _logoURI;

        _mint(msg.sender, INITIAL_SUPPLY);
        saleActive = true;
    }

    // ===== Upgrade authorization (UUPS) =====
    function _authorizeUpgrade(address newImplementation) internal override onlyOwner {}

    // ===== Supply enforcement =====
    function _beforeTokenTransfer(address from, address to, uint256 amount) internal virtual {
        // Only check on minting (from == address(0))
        if (from == address(0)) {
            require(totalSupply() + amount <= MAX_SUPPLY, "Exceeds max supply");
        }
    }

    // ===== Ownership non-transferable =====
    function transferOwnership(address) public pure override {
        revert("Ownership non-transferable");
    }

    function renounceOwnership() public pure override {
        revert("Ownership non-renounceable");
    }

    // ===== Owner-only minting =====
    function ownerMint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }

    // ===== Chainlink price feed helpers =====
    function getLatestEthUsdPrice() public view returns (int256 price) {
        (, int256 answer, , , ) = priceFeed.latestRoundData();
        return answer;
    }

    function _tokensForEth(uint256 ethAmount) internal view returns (uint256) {
        int256 ethUsdPrice = getLatestEthUsdPrice();
        require(ethUsdPrice > 0, "Invalid price");

        uint256 ethUsdValue = (ethAmount * uint256(ethUsdPrice)) / 1e18;
        uint256 tokens = (ethUsdValue * 1e18) / TOKEN_PRICE_USD_8;
        return tokens;
    }

    // ===== Token sale =====
    function buyTokens() external payable {
        require(saleActive, "Sale not active");
        require(msg.value > 0, "No ETH sent");

        uint256 tokensToBuy = _tokensForEth(msg.value);
        require(tokensToBuy > 0, "Too little ETH");

        uint256 newTotalPurchased = purchasedFromSale[msg.sender] + tokensToBuy;
        require(newTotalPurchased <= MAX_PURCHASE_PER_ADDRESS, "Exceeds max purchase");

        _mint(msg.sender, tokensToBuy);
        purchasedFromSale[msg.sender] = newTotalPurchased;
    }

    function setSaleActive(bool _active) external onlyOwner {
        saleActive = _active;
        emit SaleStatusChanged(_active);
    }

    // ===== Treasurer =====
    function setTreasurer(address _treasurer) external onlyOwner {
        require(_treasurer != address(0), "Zero treasurer");
        treasurer = _treasurer;
        emit TreasurerSet(_treasurer);
    }

    modifier onlyTreasurer() {
        require(msg.sender == treasurer, "Not treasurer");
        _;
    }

    // ===== Dual-approval ETH withdrawal =====
    function createWithdrawalRequest(uint256 amount) external onlyOwner {
        require(amount > 0, "Amount zero");
        require(address(this).balance >= amount, "Insufficient balance");

        uint256 id = nextWithdrawalId;
        withdrawals[id] = WithdrawalRequest({
            amount: amount,
            ownerApproved: false,
            treasurerApproved: false,
            executed: false
        });

        nextWithdrawalId = id + 1;
        emit WithdrawalRequested(id, amount);
    }

    function approveWithdrawalAsOwner(uint256 id) external onlyOwner {
        WithdrawalRequest storage w = withdrawals[id];
        require(!w.executed, "Executed");
        w.ownerApproved = true;
        emit WithdrawalApproved(id, msg.sender);
    }

    function approveWithdrawalAsTreasurer(uint256 id) external onlyTreasurer {
        WithdrawalRequest storage w = withdrawals[id];
        require(!w.executed, "Executed");
        w.treasurerApproved = true;
        emit WithdrawalApproved(id, msg.sender);
    }

    function executeWithdrawal(uint256 id) external {
        WithdrawalRequest storage w = withdrawals[id];
        require(!w.executed, "Executed");
        require(w.ownerApproved && w.treasurerApproved, "Not approved");
        require(address(this).balance >= w.amount, "Insufficient balance");

        w.executed = true;
        (bool success, ) = owner().call{value: w.amount}("");
        require(success, "ETH transfer failed");

        emit WithdrawalExecuted(id, w.amount, owner());
    }

    // ===== Dual-approval burn =====
    function createBurnRequest(address account, uint256 amount) external onlyOwner {
        require(account != address(0), "Invalid account");
        require(balanceOf(account) >= amount, "Insufficient balance");

        uint256 id = nextBurnId;
        burnRequests[id] = BurnRequest({
            account: account,
            amount: amount,
            ownerApproved: false,
            treasurerApproved: false,
            executed: false
        });

        nextBurnId = id + 1;
        emit BurnRequested(id, account, amount);
    }

    function approveBurnAsOwner(uint256 id) external onlyOwner {
        BurnRequest storage b = burnRequests[id];
        require(!b.executed, "Executed");
        b.ownerApproved = true;
        emit BurnApproved(id, msg.sender);
    }

    function approveBurnAsTreasurer(uint256 id) external onlyTreasurer {
        BurnRequest storage b = burnRequests[id];
        require(!b.executed, "Executed");
        b.treasurerApproved = true;
        emit BurnApproved(id, msg.sender);
    }

    function executeBurn(uint256 id) external {
        BurnRequest storage b = burnRequests[id];
        require(!b.executed, "Executed");
        require(b.ownerApproved && b.treasurerApproved, "Not approved");
        require(balanceOf(b.account) >= b.amount, "Balance changed");

        b.executed = true;
        _burn(b.account, b.amount);

        emit BurnExecuted(id, b.account, b.amount);
    }

    // ===== Receive ETH =====
    receive() external payable {}

    // ===== Storage gap =====
    uint256[50] private __gap;
}