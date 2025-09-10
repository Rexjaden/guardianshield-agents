"""
web3_utils.py: Utilities for interacting with smart contracts using web3.py
"""
from web3 import Web3
import os

class Web3Utils:
    def __init__(self, rpc_url=None):
        self.rpc_url = rpc_url or os.getenv("WEB3_RPC_URL", "http://localhost:8545")
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))

    def get_contract(self, address, abi):
        return self.web3.eth.contract(address=address, abi=abi)

    def call_function(self, contract, function_name, *args, **kwargs):
        func = getattr(contract.functions, function_name)
        return func(*args, **kwargs).call()

    def send_transaction(self, contract, function_name, private_key, *args, **kwargs):
        func = getattr(contract.functions, function_name)
        tx = func(*args, **kwargs).build_transaction({
            'from': self.web3.eth.default_account,
            'nonce': self.web3.eth.get_transaction_count(self.web3.eth.default_account)
        })
        signed_tx = self.web3.eth.account.sign_transaction(tx, private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return tx_hash.hex()
