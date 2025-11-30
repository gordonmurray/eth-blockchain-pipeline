#!/usr/bin/env python3
"""
Contract Deployer
Compiles and deploys the PurchaseStore contract to the local devnet.
Outputs contract address and ABI to a JSON file for other services to use.
"""

import json
import os
import sys
import time
from pathlib import Path

from web3 import Web3
from solcx import compile_standard, install_solc

# Configuration
RPC_URL = os.getenv("RPC_URL", "http://localhost:8545")
CONTRACT_OUTPUT = os.getenv("CONTRACT_OUTPUT", "/app/output/contract_info.json")
SOLC_VERSION = "0.8.19"


def wait_for_rpc(w3: Web3, max_retries: int = 30, delay: int = 2) -> bool:
    """Wait for RPC endpoint to be available."""
    print(f"Waiting for RPC at {RPC_URL}...")
    for i in range(max_retries):
        try:
            block_number = w3.eth.block_number
            print(f"RPC is ready. Current block: {block_number}")
            return True
        except Exception as e:
            print(f"Attempt {i + 1}/{max_retries}: RPC not ready - {e}")
            time.sleep(delay)
    return False


def compile_contract(contract_path: Path) -> dict:
    """Compile the Solidity contract."""
    print(f"Installing solc version {SOLC_VERSION}...")
    install_solc(SOLC_VERSION)

    print(f"Compiling contract: {contract_path}")
    with open(contract_path, "r") as f:
        contract_source = f.read()

    compiled_sol = compile_standard(
        {
            "language": "Solidity",
            "sources": {"PurchaseStore.sol": {"content": contract_source}},
            "settings": {
                "outputSelection": {
                    "*": {
                        "*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]
                    }
                }
            },
        },
        solc_version=SOLC_VERSION,
    )

    return compiled_sol


def deploy_contract(w3: Web3, compiled_sol: dict) -> tuple[str, list]:
    """Deploy the contract and return address and ABI."""
    # Get bytecode and ABI
    bytecode = compiled_sol["contracts"]["PurchaseStore.sol"]["PurchaseStore"]["evm"]["bytecode"]["object"]
    abi = compiled_sol["contracts"]["PurchaseStore.sol"]["PurchaseStore"]["abi"]

    # Get the dev account (Geth dev mode pre-funds this account)
    accounts = w3.eth.accounts
    if not accounts:
        raise Exception("No accounts available. Is Geth running in dev mode?")

    deployer_account = accounts[0]
    print(f"Deployer account: {deployer_account}")
    print(f"Deployer balance: {w3.from_wei(w3.eth.get_balance(deployer_account), 'ether')} ETH")

    # Create contract instance
    PurchaseStore = w3.eth.contract(abi=abi, bytecode=bytecode)

    # Build transaction
    tx = PurchaseStore.constructor().build_transaction({
        "from": deployer_account,
        "nonce": w3.eth.get_transaction_count(deployer_account),
        "gas": 2000000,
        "gasPrice": w3.eth.gas_price,
    })

    # Send transaction (dev mode auto-signs)
    print("Sending deployment transaction...")
    tx_hash = w3.eth.send_transaction(tx)
    print(f"Transaction hash: {tx_hash.hex()}")

    # Wait for receipt
    print("Waiting for transaction receipt...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

    contract_address = tx_receipt["contractAddress"]
    print(f"Contract deployed at: {contract_address}")
    print(f"Gas used: {tx_receipt['gasUsed']}")

    return contract_address, abi


def fund_wallets(w3: Web3, num_wallets: int = 3) -> list[dict]:
    """Create and fund wallets for the simulator."""
    print(f"\nCreating and funding {num_wallets} wallets...")

    dev_account = w3.eth.accounts[0]
    wallets = []

    for i in range(num_wallets):
        # Create new account
        account = w3.eth.account.create()
        wallet_info = {
            "address": account.address,
            "private_key": account.key.hex(),
        }
        wallets.append(wallet_info)

        # Fund with 10 ETH
        tx_hash = w3.eth.send_transaction({
            "from": dev_account,
            "to": account.address,
            "value": w3.to_wei(10, "ether"),
            "gas": 21000,
            "gasPrice": w3.eth.gas_price,
        })
        w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"  Wallet {i + 1}: {account.address} funded with 10 ETH")

    return wallets


def save_contract_info(contract_address: str, abi: list, wallets: list, output_path: str):
    """Save contract info to JSON file."""
    # Create output directory if needed
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    contract_info = {
        "contract_address": contract_address,
        "abi": abi,
        "wallets": wallets,
        "deployed_at": int(time.time()),
    }

    with open(output_path, "w") as f:
        json.dump(contract_info, f, indent=2)

    print(f"\nContract info saved to: {output_path}")


def main():
    print("=" * 60)
    print("PurchaseStore Contract Deployer")
    print("=" * 60)

    # Connect to RPC
    w3 = Web3(Web3.HTTPProvider(RPC_URL))

    if not wait_for_rpc(w3):
        print("ERROR: Could not connect to RPC")
        sys.exit(1)

    # Find contract file
    contract_path = Path("/app/contracts/PurchaseStore.sol")
    if not contract_path.exists():
        # Try local path
        contract_path = Path("contracts/PurchaseStore.sol")
    if not contract_path.exists():
        print(f"ERROR: Contract file not found")
        sys.exit(1)

    # Compile
    compiled_sol = compile_contract(contract_path)

    # Deploy
    contract_address, abi = deploy_contract(w3, compiled_sol)

    # Create and fund wallets
    wallets = fund_wallets(w3, num_wallets=3)

    # Save contract info
    save_contract_info(contract_address, abi, wallets, CONTRACT_OUTPUT)

    print("\n" + "=" * 60)
    print("Deployment completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
