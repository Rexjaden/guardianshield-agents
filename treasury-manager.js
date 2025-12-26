/**
 * GuardianTreasury Web3 Integration
 * Interface for managing multi-signature treasury operations
 */

class GuardianTreasuryManager {
    constructor(web3Instance) {
        this.web3 = web3Instance;
        this.treasuryContract = null;
        this.treasuryAddress = '';
        
        // Treasury ABI for main functions
        this.treasuryABI = [
            "function treasurer() view returns (address)",
            "function isAuthorized(address) view returns (bool)",
            "function proposeTransaction(address to, uint256 value, bytes data, string description) returns (uint256)",
            "function confirmTransaction(uint256 txId)",
            "function cancelTransaction(uint256 txId)",
            "function getTransaction(uint256 txId) view returns (address, uint256, bytes, bool, uint256, uint256, string, bool, bool)",
            "function getPendingTransactions() view returns (uint256[])",
            "function getBalances(address[] tokens) view returns (uint256, uint256[])",
            "function withdrawETH(address to, uint256 amount, string description) returns (uint256)",
            "function withdrawToken(address token, address to, uint256 amount, string description) returns (uint256)",
            "function changeTreasurer(address newTreasurer)",
            "function pause()",
            "function unpause()",
            "function emergencyWithdrawETH(address to, uint256 amount)",
            "function emergencyWithdrawToken(address token, address to, uint256 amount)"
        ];
        
        this.init();
    }
    
    async init() {
        if (this.treasuryAddress && this.web3.signer) {
            this.treasuryContract = new ethers.Contract(
                this.treasuryAddress,
                this.treasuryABI,
                this.web3.signer
            );
        }
    }
    
    setTreasuryAddress(address) {
        this.treasuryAddress = address;
        this.init();
    }
    
    async checkAuthorization() {
        if (!this.treasuryContract || !this.web3.signer) {
            return false;
        }
        
        try {
            const userAddress = await this.web3.signer.getAddress();
            return await this.treasuryContract.isAuthorized(userAddress);
        } catch (error) {
            console.error('Authorization check failed:', error);
            return false;
        }
    }
    
    async getTreasuryInfo() {
        if (!this.treasuryContract) {
            return null;
        }
        
        try {
            const treasurer = await this.treasuryContract.treasurer();
            const owner = await this.treasuryContract.owner();
            const userAddress = await this.web3.signer.getAddress();
            const isAuthorized = await this.checkAuthorization();
            
            return {
                treasurer,
                owner,
                userAddress,
                isAuthorized,
                isOwner: userAddress.toLowerCase() === owner.toLowerCase(),
                isTreasurer: userAddress.toLowerCase() === treasurer.toLowerCase()
            };
        } catch (error) {
            console.error('Failed to get treasury info:', error);
            return null;
        }
    }
    
    async getTreasuryBalances(tokenAddresses = []) {
        if (!this.treasuryContract) {
            return null;
        }
        
        try {
            const balances = await this.treasuryContract.getBalances(tokenAddresses);
            return {
                eth: ethers.utils.formatEther(balances[0]),
                tokens: balances[1].map((balance, index) => ({
                    address: tokenAddresses[index],
                    balance: ethers.utils.formatEther(balance)
                }))
            };
        } catch (error) {
            console.error('Failed to get treasury balances:', error);
            return null;
        }
    }
    
    async getPendingTransactions() {
        if (!this.treasuryContract) {
            return [];
        }
        
        try {
            const pendingIds = await this.treasuryContract.getPendingTransactions();
            const transactions = [];
            
            for (const id of pendingIds) {
                const tx = await this.getTransactionDetails(id.toString());
                if (tx) {
                    transactions.push({ id: id.toString(), ...tx });
                }
            }
            
            return transactions;
        } catch (error) {
            console.error('Failed to get pending transactions:', error);
            return [];
        }
    }
    
    async getTransactionDetails(txId) {
        if (!this.treasuryContract) {
            return null;
        }
        
        try {
            const result = await this.treasuryContract.getTransaction(txId);
            return {
                to: result[0],
                value: ethers.utils.formatEther(result[1]),
                data: result[2],
                executed: result[3],
                confirmations: result[4].toString(),
                timestamp: new Date(result[5].toNumber() * 1000),
                description: result[6],
                ownerConfirmed: result[7],
                treasurerConfirmed: result[8]
            };
        } catch (error) {
            console.error('Failed to get transaction details:', error);
            return null;
        }
    }
    
    async proposeWithdrawal(to, amount, description, isToken = false, tokenAddress = null) {
        if (!this.treasuryContract) {
            throw new Error('Treasury contract not initialized');
        }
        
        try {
            this.web3.showNotification('Proposing withdrawal transaction...', 'info');
            
            let tx;
            if (isToken) {
                const tokenAmount = ethers.utils.parseEther(amount.toString());
                tx = await this.treasuryContract.withdrawToken(
                    tokenAddress,
                    to,
                    tokenAmount,
                    description
                );
            } else {
                const ethAmount = ethers.utils.parseEther(amount.toString());
                tx = await this.treasuryContract.withdrawETH(to, ethAmount, description);
            }
            
            this.web3.showNotification('Transaction proposed! Waiting for confirmation...', 'info');
            
            const receipt = await tx.wait();
            this.web3.showNotification('Withdrawal proposal created successfully!', 'success');
            
            return receipt;
        } catch (error) {
            console.error('Withdrawal proposal failed:', error);
            this.web3.showNotification('Failed to propose withdrawal: ' + error.message, 'error');
            throw error;
        }
    }
    
    async confirmTransaction(txId) {
        if (!this.treasuryContract) {
            throw new Error('Treasury contract not initialized');
        }
        
        try {
            this.web3.showNotification('Confirming transaction...', 'info');
            
            const tx = await this.treasuryContract.confirmTransaction(txId);
            
            this.web3.showNotification('Transaction sent! Waiting for confirmation...', 'info');
            
            const receipt = await tx.wait();
            this.web3.showNotification('Transaction confirmed successfully!', 'success');
            
            return receipt;
        } catch (error) {
            console.error('Transaction confirmation failed:', error);
            this.web3.showNotification('Failed to confirm transaction: ' + error.message, 'error');
            throw error;
        }
    }
    
    async cancelTransaction(txId) {
        if (!this.treasuryContract) {
            throw new Error('Treasury contract not initialized');
        }
        
        try {
            this.web3.showNotification('Cancelling transaction...', 'info');
            
            const tx = await this.treasuryContract.cancelTransaction(txId);
            
            this.web3.showNotification('Transaction sent! Waiting for confirmation...', 'info');
            
            const receipt = await tx.wait();
            this.web3.showNotification('Transaction cancelled successfully!', 'success');
            
            return receipt;
        } catch (error) {
            console.error('Transaction cancellation failed:', error);
            this.web3.showNotification('Failed to cancel transaction: ' + error.message, 'error');
            throw error;
        }
    }
    
    async changeTreasurer(newTreasurerAddress) {
        if (!this.treasuryContract) {
            throw new Error('Treasury contract not initialized');
        }
        
        try {
            this.web3.showNotification('Changing treasurer...', 'info');
            
            const tx = await this.treasuryContract.changeTreasurer(newTreasurerAddress);
            
            this.web3.showNotification('Transaction sent! Waiting for confirmation...', 'info');
            
            const receipt = await tx.wait();
            this.web3.showNotification('Treasurer changed successfully!', 'success');
            
            return receipt;
        } catch (error) {
            console.error('Treasurer change failed:', error);
            this.web3.showNotification('Failed to change treasurer: ' + error.message, 'error');
            throw error;
        }
    }
    
    async emergencyWithdraw(to, amount, isToken = false, tokenAddress = null) {
        if (!this.treasuryContract) {
            throw new Error('Treasury contract not initialized');
        }
        
        try {
            this.web3.showNotification('Processing emergency withdrawal...', 'info');
            
            let tx;
            if (isToken) {
                const tokenAmount = ethers.utils.parseEther(amount.toString());
                tx = await this.treasuryContract.emergencyWithdrawToken(tokenAddress, to, tokenAmount);
            } else {
                const ethAmount = ethers.utils.parseEther(amount.toString());
                tx = await this.treasuryContract.emergencyWithdrawETH(to, ethAmount);
            }
            
            this.web3.showNotification('Transaction sent! Waiting for confirmation...', 'info');
            
            const receipt = await tx.wait();
            this.web3.showNotification('Emergency withdrawal completed!', 'success');
            
            return receipt;
        } catch (error) {
            console.error('Emergency withdrawal failed:', error);
            this.web3.showNotification('Failed to process emergency withdrawal: ' + error.message, 'error');
            throw error;
        }
    }
    
    async pauseTreasury() {
        if (!this.treasuryContract) {
            throw new Error('Treasury contract not initialized');
        }
        
        try {
            const tx = await this.treasuryContract.pause();
            const receipt = await tx.wait();
            this.web3.showNotification('Treasury paused successfully!', 'success');
            return receipt;
        } catch (error) {
            console.error('Treasury pause failed:', error);
            this.web3.showNotification('Failed to pause treasury: ' + error.message, 'error');
            throw error;
        }
    }
    
    async unpauseTreasury() {
        if (!this.treasuryContract) {
            throw new Error('Treasury contract not initialized');
        }
        
        try {
            const tx = await this.treasuryContract.unpause();
            const receipt = await tx.wait();
            this.web3.showNotification('Treasury unpaused successfully!', 'success');
            return receipt;
        } catch (error) {
            console.error('Treasury unpause failed:', error);
            this.web3.showNotification('Failed to unpause treasury: ' + error.message, 'error');
            throw error;
        }
    }
}

// Initialize treasury manager when Web3 is ready
let guardianTreasuryManager;

document.addEventListener('DOMContentLoaded', () => {
    // Wait for guardianWeb3 to be initialized
    const initTreasury = () => {
        if (typeof guardianWeb3 !== 'undefined') {
            guardianTreasuryManager = new GuardianTreasuryManager(guardianWeb3);
        } else {
            setTimeout(initTreasury, 100);
        }
    };
    
    initTreasury();
});