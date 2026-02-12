import json
import os
from web3 import Web3
from web3.middleware import geth_poa_middleware
import time

# ---------------- تنظیمات ----------------
NETWORK_FILE = "networks.json"
CHAIN_ID = 46630

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
if not PRIVATE_KEY:
    raise ValueError("PRIVATE_KEY not set in secrets!")

# ---------------- لود شبکه ----------------
with open(NETWORK_FILE) as f:
    networks = json.load(f)

network = next((n for n in networks if int(n["chain_id"]) == CHAIN_ID), None)
if not network:
    raise ValueError("Network not found!")

w3 = Web3(Web3.HTTPProvider(network["rpc_url"]))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)  # برای Arbitrum Orbit

if not w3.is_connected():
    raise ConnectionError("Cannot connect to RPC!")

account = w3.eth.account.from_key(PRIVATE_KEY)
print(f"Sender: {account.address}")
print(f"Balance: {w3.from_wei(w3.eth.get_balance(account.address), 'ether')} ETH")

# ---------------- پارامترهای تراکنش GM ----------------
contract_address = "0xC21dF1Bb620ebe7f5aE0144df50DE28ce0D47ae7"
gm_data = "0x84a3bb6b0000000000000000000000000000000000000000000000000000000000000000"  # gm() با arg 0

tx = {
    "chainId": CHAIN_ID,
    "to": w3.to_checksum_address(contract_address),
    "data": gm_data,
    "value": 0x1a6016b2d000,  # ~0.000000006 ETH (برای تست)
    "nonce": w3.eth.get_transaction_count(account.address, "pending"),
    "maxFeePerGas": w3.to_wei(0.1, "gwei"),      # کم برای testnet
    "maxPriorityFeePerGas": w3.to_wei(0.01, "gwei"),
    "gas": 300000,  # کافی برای call ساده
}

# ---------------- ارسال با retry ----------------
max_retries = 3
for attempt in range(max_retries):
    try:
        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        print(f"GM Transaction sent! Hash: {w3.to_hex(tx_hash)}")
        print(f"Explorer: {network['explorer_url']}/tx/{w3.to_hex(tx_hash)}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        if receipt.status == 1:
            print("GM Claim Successful! 🎉")
        else:
            print("Transaction failed!")
        break
    except Exception as e:
        print(f"Attempt {attempt + 1} failed: {e}")
        if attempt < max_retries - 1:
            time.sleep(30)
        else:
            print("All attempts failed!")
