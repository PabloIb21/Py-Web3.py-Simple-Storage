import os
import json
from web3 import Web3
from solcx import compile_standard, install_solc
from dotenv import load_dotenv

load_dotenv()

with open("./SimpleStorage.sol", "r") as file:
  simple_storage_file = file.read()

print("Installing...")
install_solc("0.6.0")

# Solidity source code
compiled_sol = compile_standard(
  {
    "language": "Solidity",
    "sources": {"SimpleStorage.sol": {"content": simple_storage_file}},
    "settings": {
      "outputSelection": {
        "*": {
          "*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]
        }
      }
    }
  }, 
  solc_version="0.6.0"
)

with open("compiled_code.json", "w") as file:
  json.dump(compiled_sol, file)

# Get bytecode
bytecode = compiled_sol["contracts"]["SimpleStorage.sol"]["SimpleStorage"]["evm"]["bytecode"]["object"]

# Get abi
abi = compiled_sol["contracts"]["SimpleStorage.sol"]["SimpleStorage"]["abi"]

# For connecting to ganache
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))
chain_id = 1337
my_address = "0xF7F9348F3505896Fb6eB9842544F9d69Fbe14821"
private_key = os.getenv("private_key")


# Create the contract in Python
SimpleStorage = w3.eth.contract(abi=abi, bytecode=bytecode)

# Get the latest transaction
nonce = w3.eth.getTransactionCount(my_address)

# Submit the transaction that deploys the contract
tx = SimpleStorage.constructor().buildTransaction(
  {
    "chainId": chain_id, 
    "from": my_address,
    "gasPrice": w3.eth.gas_price,
    "nonce": nonce
  }
)

# Sign the transaction
signed_tx = w3.eth.account.sign_transaction(tx, private_key)
print("Deploying Contract!")

# Send this signed transaction
tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

# Wait for the transaction to be mined, and get the transaction receipt
print("Waiting for transaction to finish...")

tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"Contract deployed to: {tx_receipt.contractAddress}")

# Working with deployed contracts
simple_storage = w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)
print(f"Initial Stored Value: {simple_storage.functions.retrieve().call()}")

store_transaction = simple_storage.functions.store(15).buildTransaction(
  {
    "chainId": chain_id,
    "gasPrice": w3.eth.gas_price,
    "from": my_address,
    "nonce": nonce + 1,
  }
)
signed_store_tx = w3.eth.account.sign_transaction(
  store_transaction, private_key=private_key
)
store_tx_hash = w3.eth.send_raw_transaction(signed_store_tx.rawTransaction)
print("Updating stored value...")
store_tx_receipt = w3.eth.wait_for_transaction_receipt(store_tx_hash)

print(simple_storage.functions.retrieve().call())
