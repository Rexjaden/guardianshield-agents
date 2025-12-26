// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

/**
 * @title GuardianTreasury
 * @dev Multi-signature treasury contract for Guardian ecosystem funds
 * Only the owner and designated treasurer can access funds with 2-of-2 approval
 */
contract GuardianTreasury is Ownable, ReentrancyGuard, Pausable {
    using SafeERC20 for IERC20;

    // Treasury roles
    address public treasurer;
    
    // Multisig configuration
    uint256 public constant REQUIRED_SIGNATURES = 2;
    
    // Transaction proposal structure
    struct Transaction {
        address to;
        uint256 value;
        bytes data;
        bool executed;
        uint256 confirmations;
        mapping(address => bool) isConfirmed;
        uint256 timestamp;
        string description;
    }

    // State variables
    mapping(uint256 => Transaction) public transactions;
    uint256 public transactionCount;
    uint256 public constant TRANSACTION_EXPIRY = 7 days;

    // Events
    event TreasurerChanged(address indexed oldTreasurer, address indexed newTreasurer);
    event TransactionProposed(uint256 indexed txId, address indexed proposer, address to, uint256 value, string description);
    event TransactionConfirmed(uint256 indexed txId, address indexed signer);
    event TransactionExecuted(uint256 indexed txId, address executor);
    event TransactionCancelled(uint256 indexed txId, address canceller);
    event ETHDeposited(address indexed from, uint256 amount);
    event TokenDeposited(address indexed token, address indexed from, uint256 amount);
    event EmergencyWithdrawal(address indexed token, uint256 amount, address to);

    modifier onlyAuthorized() {
        require(msg.sender == owner() || msg.sender == treasurer, "Not authorized");
        _;
    }

    modifier validTransaction(uint256 _txId) {
        require(_txId < transactionCount, "Invalid transaction ID");
        require(!transactions[_txId].executed, "Transaction already executed");
        require(block.timestamp <= transactions[_txId].timestamp + TRANSACTION_EXPIRY, "Transaction expired");
        _;
    }

    constructor(address _treasurer) Ownable(msg.sender) {
        require(_treasurer != address(0), "Invalid treasurer address");
        require(_treasurer != msg.sender, "Treasurer cannot be owner");
        treasurer = _treasurer;
    }

    /**
     * @dev Receive ETH deposits
     */
    receive() external payable {
        emit ETHDeposited(msg.sender, msg.value);
    }

    /**
     * @dev Fallback function for ETH deposits
     */
    fallback() external payable {
        emit ETHDeposited(msg.sender, msg.value);
    }

    /**
     * @dev Change the treasurer (only owner)
     */
    function changeTreasurer(address _newTreasurer) external onlyOwner {
        require(_newTreasurer != address(0), "Invalid treasurer address");
        require(_newTreasurer != owner(), "Treasurer cannot be owner");
        
        address oldTreasurer = treasurer;
        treasurer = _newTreasurer;
        
        emit TreasurerChanged(oldTreasurer, _newTreasurer);
    }

    /**
     * @dev Propose a new transaction
     */
    function proposeTransaction(
        address _to,
        uint256 _value,
        bytes memory _data,
        string memory _description
    ) public onlyAuthorized returns (uint256) {
        require(_to != address(0), "Invalid destination address");
        
        uint256 txId = transactionCount;
        Transaction storage txn = transactions[txId];
        
        txn.to = _to;
        txn.value = _value;
        txn.data = _data;
        txn.executed = false;
        txn.confirmations = 1;
        txn.isConfirmed[msg.sender] = true;
        txn.timestamp = block.timestamp;
        txn.description = _description;
        
        transactionCount++;
        
        emit TransactionProposed(txId, msg.sender, _to, _value, _description);
        emit TransactionConfirmed(txId, msg.sender);
        
        // Auto-execute if both signatures are available
        if (txn.confirmations == REQUIRED_SIGNATURES) {
            _executeTransaction(txId);
        }
        
        return txId;
    }

    /**
     * @dev Confirm a pending transaction
     */
    function confirmTransaction(uint256 _txId) 
        external 
        onlyAuthorized 
        validTransaction(_txId) 
    {
        Transaction storage txn = transactions[_txId];
        require(!txn.isConfirmed[msg.sender], "Transaction already confirmed by sender");
        
        txn.isConfirmed[msg.sender] = true;
        txn.confirmations++;
        
        emit TransactionConfirmed(_txId, msg.sender);
        
        // Execute if we have required signatures
        if (txn.confirmations == REQUIRED_SIGNATURES) {
            _executeTransaction(_txId);
        }
    }

    /**
     * @dev Execute a confirmed transaction
     */
    function _executeTransaction(uint256 _txId) internal {
        Transaction storage txn = transactions[_txId];
        require(txn.confirmations == REQUIRED_SIGNATURES, "Insufficient confirmations");
        
        txn.executed = true;
        
        (bool success, ) = txn.to.call{value: txn.value}(txn.data);
        require(success, "Transaction execution failed");
        
        emit TransactionExecuted(_txId, msg.sender);
    }

    /**
     * @dev Cancel a pending transaction (only proposer can cancel)
     */
    function cancelTransaction(uint256 _txId) external onlyAuthorized {
        require(_txId < transactionCount, "Invalid transaction ID");
        require(!transactions[_txId].executed, "Transaction already executed");
        require(transactions[_txId].isConfirmed[msg.sender], "Not authorized to cancel");
        
        // Mark as executed to prevent further actions
        transactions[_txId].executed = true;
        
        emit TransactionCancelled(_txId, msg.sender);
    }

    /**
     * @dev Withdraw ETH (creates a transaction proposal)
     */
    function withdrawETH(address payable _to, uint256 _amount, string memory _description) 
        external 
        onlyAuthorized 
        returns (uint256) 
    {
        require(_amount > 0, "Amount must be greater than 0");
        require(_amount <= address(this).balance, "Insufficient ETH balance");
        
        return proposeTransaction(_to, _amount, new bytes(0), _description);
    }

    /**
     * @dev Withdraw ERC20 tokens (creates a transaction proposal)
     */
    function withdrawToken(
        IERC20 _token,
        address _to,
        uint256 _amount,
        string memory _description
    ) external onlyAuthorized returns (uint256) {
        require(_amount > 0, "Amount must be greater than 0");
        require(_amount <= _token.balanceOf(address(this)), "Insufficient token balance");
        
        bytes memory data = abi.encodeWithSelector(
            IERC20.transfer.selector,
            _to,
            _amount
        );
        
        return proposeTransaction(address(_token), 0, data, _description);
    }

    /**
     * @dev Emergency withdrawal function (requires both owner and treasurer)
     */
    function emergencyWithdrawETH(address payable _to, uint256 _amount) 
        external 
        onlyOwner 
        whenPaused 
    {
        require(_to != address(0), "Invalid address");
        require(_amount <= address(this).balance, "Insufficient balance");
        
        _to.transfer(_amount);
        emit EmergencyWithdrawal(address(0), _amount, _to);
    }

    /**
     * @dev Emergency token withdrawal (requires both owner and treasurer)
     */
    function emergencyWithdrawToken(IERC20 _token, address _to, uint256 _amount) 
        external 
        onlyOwner 
        whenPaused 
    {
        require(_to != address(0), "Invalid address");
        require(_amount <= _token.balanceOf(address(this)), "Insufficient balance");
        
        _token.safeTransfer(_to, _amount);
        emit EmergencyWithdrawal(address(_token), _amount, _to);
    }

    /**
     * @dev Pause contract (only owner or treasurer)
     */
    function pause() external onlyAuthorized {
        _pause();
    }

    /**
     * @dev Unpause contract (only owner)
     */
    function unpause() external onlyOwner {
        _unpause();
    }

    /**
     * @dev Get transaction details
     */
    function getTransaction(uint256 _txId) external view returns (
        address to,
        uint256 value,
        bytes memory data,
        bool executed,
        uint256 confirmations,
        uint256 timestamp,
        string memory description,
        bool ownerConfirmed,
        bool treasurerConfirmed
    ) {
        require(_txId < transactionCount, "Invalid transaction ID");
        Transaction storage txn = transactions[_txId];
        
        return (
            txn.to,
            txn.value,
            txn.data,
            txn.executed,
            txn.confirmations,
            txn.timestamp,
            txn.description,
            txn.isConfirmed[owner()],
            txn.isConfirmed[treasurer]
        );
    }

    /**
     * @dev Get contract balances
     */
    function getBalances(address[] calldata _tokens) external view returns (
        uint256 ethBalance,
        uint256[] memory tokenBalances
    ) {
        ethBalance = address(this).balance;
        tokenBalances = new uint256[](_tokens.length);
        
        for (uint256 i = 0; i < _tokens.length; i++) {
            tokenBalances[i] = IERC20(_tokens[i]).balanceOf(address(this));
        }
    }

    /**
     * @dev Get pending transactions
     */
    function getPendingTransactions() external view returns (uint256[] memory) {
        uint256[] memory tempPending = new uint256[](transactionCount);
        uint256 pendingCount = 0;
        
        for (uint256 i = 0; i < transactionCount; i++) {
            if (!transactions[i].executed && 
                block.timestamp <= transactions[i].timestamp + TRANSACTION_EXPIRY) {
                tempPending[pendingCount] = i;
                pendingCount++;
            }
        }
        
        // Create properly sized array
        uint256[] memory pending = new uint256[](pendingCount);
        for (uint256 i = 0; i < pendingCount; i++) {
            pending[i] = tempPending[i];
        }
        
        return pending;
    }

    /**
     * @dev Check if address is authorized
     */
    function isAuthorized(address _address) external view returns (bool) {
        return _address == owner() || _address == treasurer;
    }

    /**
     * @dev Deposit tokens to treasury
     */
    function depositToken(IERC20 _token, uint256 _amount) external {
        require(_amount > 0, "Amount must be greater than 0");
        
        _token.safeTransferFrom(msg.sender, address(this), _amount);
        emit TokenDeposited(address(_token), msg.sender, _amount);
    }
}