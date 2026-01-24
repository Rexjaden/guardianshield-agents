import os

def create_contracts_script():
    try:
        with open('contracts/GuardianTokenSale.sol', 'r', encoding='utf-8') as f:
            sale_content = f.read()
        
        with open('contracts/ChainlinkPriceOracle.sol', 'r', encoding='utf-8') as f:
            oracle_content = f.read()
            
        with open('contracts/GuardianShieldToken.sol', 'r', encoding='utf-8') as f:
            token_content = f.read()
            
    except Exception as e:
        print(f"Error reading contract files: {e}")
        return

    script_content = f"""#!/bin/bash
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
{sale_content}
SOLIDITY_EOF

# 2. ChainlinkPriceOracle.sol (The Pricing Logic)
echo "📄 Extracting ChainlinkPriceOracle.sol..."
cat << 'SOLIDITY_EOF' > $WORK_DIR/ChainlinkPriceOracle.sol
{oracle_content}
SOLIDITY_EOF

# 3. GuardianShieldToken.sol (The Token Itself - Example)
echo "📄 Extracting GuardianShieldToken.sol..."
cat << 'SOLIDITY_EOF' > $WORK_DIR/GuardianShieldToken.sol
{token_content}
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
"""

    with open('GET_CONTRACTS_PACKAGE.sh', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("GET_CONTRACTS_PACKAGE.sh created successfully.")

if __name__ == "__main__":
    create_contracts_script()
