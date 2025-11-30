#!/usr/bin/env python3
"""
Purchase Simulator
Generates random purchase transactions from multiple wallets.
"""

import json
import os
import random
import sys
import time
from pathlib import Path

from web3 import Web3

# Configuration
RPC_URL = os.getenv("RPC_URL", "http://localhost:8545")
CONTRACT_INFO_PATH = os.getenv("CONTRACT_INFO_PATH", "/app/contract_info/contract_info.json")
PURCHASE_INTERVAL_MIN = int(os.getenv("PURCHASE_INTERVAL_MIN", "2"))
PURCHASE_INTERVAL_MAX = int(os.getenv("PURCHASE_INTERVAL_MAX", "5"))

# Product catalog (must match contract)
PRODUCTS = {
    1: {"name": "Coffee", "price_eth": 0.001},
    2: {"name": "Sandwich", "price_eth": 0.005},
    3: {"name": "Pizza", "price_eth": 0.01},
    4: {"name": "Burger", "price_eth": 0.008},
    5: {"name": "Salad", "price_eth": 0.006},
}


def load_contract_info(path: str) -> dict:
    """Load contract info from JSON file."""
    print(f"Loading contract info from: {path}")
    max_retries = 30
    for i in range(max_retries):
        if Path(path).exists():
            with open(path, "r") as f:
                return json.load(f)
        print(f"Waiting for contract info file... ({i + 1}/{max_retries})")
        time.sleep(2)
    raise FileNotFoundError(f"Contract info not found at {path}")


def wait_for_rpc(w3: Web3, max_retries: int = 30) -> bool:
    """Wait for RPC endpoint to be available."""
    print(f"Connecting to RPC: {RPC_URL}")
    for i in range(max_retries):
        try:
            w3.eth.block_number
            print("RPC connected!")
            return True
        except Exception as e:
            print(f"Waiting for RPC... ({i + 1}/{max_retries})")
            time.sleep(2)
    return False


def make_purchase(w3: Web3, contract, wallet: dict, product_id: int, quantity: int):
    """Execute a purchase transaction."""
    product = PRODUCTS[product_id]
    price_wei = w3.to_wei(product["price_eth"] * quantity, "ether")

    # Build transaction
    tx = contract.functions.purchase(product_id, quantity).build_transaction({
        "from": wallet["address"],
        "value": price_wei,
        "nonce": w3.eth.get_transaction_count(wallet["address"]),
        "gas": 100000,
        "gasPrice": w3.eth.gas_price,
    })

    # Sign and send
    signed_tx = w3.eth.account.sign_transaction(tx, wallet["private_key"])
    # Handle both old and new web3.py API
    raw_tx = getattr(signed_tx, 'rawTransaction', None) or signed_tx.raw_transaction
    tx_hash = w3.eth.send_raw_transaction(raw_tx)

    # Wait for receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)

    return tx_hash.hex(), receipt


def run_simulator():
    """Main simulator loop."""
    print("=" * 60)
    print("Purchase Simulator Starting")
    print("=" * 60)

    # Connect to Web3
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not wait_for_rpc(w3):
        print("ERROR: Could not connect to RPC")
        sys.exit(1)

    # Load contract info
    contract_info = load_contract_info(CONTRACT_INFO_PATH)
    contract_address = contract_info["contract_address"]
    abi = contract_info["abi"]
    wallets = contract_info["wallets"]

    print(f"Contract address: {contract_address}")
    print(f"Number of wallets: {len(wallets)}")

    # Create contract instance
    contract = w3.eth.contract(address=contract_address, abi=abi)

    # Print wallet balances
    print("\nWallet balances:")
    for i, wallet in enumerate(wallets):
        balance = w3.eth.get_balance(wallet["address"])
        print(f"  Wallet {i + 1}: {wallet['address'][:10]}... - {w3.from_wei(balance, 'ether'):.4f} ETH")

    print("\n" + "=" * 60)
    print("Starting purchase simulation...")
    print("=" * 60 + "\n")

    purchase_count = 0

    while True:
        try:
            # Random selection
            wallet = random.choice(wallets)
            product_id = random.randint(1, 5)
            quantity = random.randint(1, 3)
            product = PRODUCTS[product_id]

            print(f"[Purchase #{purchase_count + 1}]")
            print(f"  Wallet: {wallet['address'][:10]}...")
            print(f"  Product: {product['name']} (ID: {product_id})")
            print(f"  Quantity: {quantity}")
            print(f"  Total: {product['price_eth'] * quantity:.4f} ETH")

            # Execute purchase
            tx_hash, receipt = make_purchase(w3, contract, wallet, product_id, quantity)

            print(f"  TX Hash: {tx_hash[:20]}...")
            print(f"  Block: {receipt['blockNumber']}")
            print(f"  Gas Used: {receipt['gasUsed']}")
            print(f"  Status: {'Success' if receipt['status'] == 1 else 'Failed'}")
            print()

            purchase_count += 1

            # Random delay
            delay = random.uniform(PURCHASE_INTERVAL_MIN, PURCHASE_INTERVAL_MAX)
            time.sleep(delay)

        except Exception as e:
            print(f"ERROR: {e}")
            time.sleep(5)


if __name__ == "__main__":
    run_simulator()
