#!/usr/bin/env python3
"""
Blockchain Indexer
Polls the chain for PurchaseMade events and stores them in PostgreSQL.
Exposes Prometheus metrics for monitoring.
"""

import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from threading import Thread

import psycopg2
from psycopg2.extras import execute_values
from web3 import Web3
from prometheus_client import start_http_server, Counter, Gauge, Histogram

# Configuration
RPC_URL = os.getenv("RPC_URL", "http://localhost:8545")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://indexer:indexer_pass@localhost:5432/blockchain_data")
CONTRACT_INFO_PATH = os.getenv("CONTRACT_INFO_PATH", "/app/contract_info/contract_info.json")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "2"))
METRICS_PORT = int(os.getenv("METRICS_PORT", "8000"))

# Prometheus metrics
EVENTS_INDEXED = Counter("indexer_events_indexed_total", "Total number of events indexed")
BLOCKS_PROCESSED = Counter("indexer_blocks_processed_total", "Total number of blocks processed")
CURRENT_BLOCK = Gauge("indexer_current_block", "Current block number being processed")
CHAIN_HEAD = Gauge("indexer_chain_head", "Latest block number on the chain")
INDEXER_LAG = Gauge("indexer_lag_blocks", "Number of blocks behind chain head")
INDEX_DURATION = Histogram("indexer_index_duration_seconds", "Time spent indexing events")
DB_WRITE_DURATION = Histogram("indexer_db_write_duration_seconds", "Time spent writing to database")

# Event signature for PurchaseMade
# keccak256("PurchaseMade(address,uint256,uint256,uint256,uint256)")
PURCHASE_MADE_TOPIC = None  # Will be computed from ABI


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


def wait_for_db(max_retries: int = 30) -> psycopg2.extensions.connection:
    """Wait for database to be available and return connection."""
    print(f"Connecting to database...")
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(DATABASE_URL)
            print("Database connected!")
            return conn
        except Exception as e:
            print(f"Waiting for database... ({i + 1}/{max_retries}): {e}")
            time.sleep(2)
    raise Exception("Could not connect to database")


def get_last_indexed_block(conn) -> int:
    """Get the last indexed block from the database."""
    with conn.cursor() as cur:
        cur.execute("SELECT COALESCE(MAX(block_number), 0) FROM raw_logs")
        result = cur.fetchone()[0]
        return result


def store_raw_log(conn, log: dict, block_timestamp: int):
    """Store raw log in the database."""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO raw_logs (block_number, transaction_hash, log_index, contract_address, topics, data, block_timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (transaction_hash, log_index) DO NOTHING
        """, (
            log["blockNumber"],
            log["transactionHash"].hex(),
            log["logIndex"],
            log["address"],
            json.dumps([t.hex() for t in log["topics"]]),
            log["data"].hex() if log["data"] else "",
            datetime.fromtimestamp(block_timestamp),
        ))


def decode_purchase_event(w3: Web3, log: dict) -> dict:
    """Decode a PurchaseMade event from a log entry."""
    # Topics: [event_signature, indexed_buyer, indexed_product_id]
    # Data: [price, quantity, timestamp] (non-indexed)

    buyer = w3.to_checksum_address("0x" + log["topics"][1].hex()[-40:])
    product_id = int(log["topics"][2].hex(), 16)

    # Decode data (3 uint256 values = 96 bytes)
    data = log["data"].hex()
    price = int(data[2:66], 16)  # First 32 bytes
    quantity = int(data[66:130], 16)  # Second 32 bytes
    timestamp = int(data[130:194], 16)  # Third 32 bytes

    return {
        "buyer_address": buyer,
        "product_id": product_id,
        "price_wei": price,
        "quantity": quantity,
        "event_timestamp": timestamp,
        "block_number": log["blockNumber"],
        "transaction_hash": log["transactionHash"].hex(),
        "log_index": log["logIndex"],
    }


def store_purchase(conn, purchase: dict):
    """Store decoded purchase in the database."""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO purchases (
                buyer_address, product_id, price_wei, quantity,
                event_timestamp, block_number, transaction_hash, log_index
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (transaction_hash, log_index) DO NOTHING
        """, (
            purchase["buyer_address"],
            purchase["product_id"],
            purchase["price_wei"],
            purchase["quantity"],
            datetime.fromtimestamp(purchase["event_timestamp"]),
            purchase["block_number"],
            purchase["transaction_hash"],
            purchase["log_index"],
        ))


def index_events(w3: Web3, conn, contract_address: str, event_signature: str, from_block: int, to_block: int):
    """Index events from a range of blocks."""
    if from_block > to_block:
        return 0

    with INDEX_DURATION.time():
        # Get logs
        logs = w3.eth.get_logs({
            "address": contract_address,
            "topics": [event_signature],
            "fromBlock": from_block,
            "toBlock": to_block,
        })

    if not logs:
        return 0

    print(f"Found {len(logs)} events in blocks {from_block}-{to_block}")

    with DB_WRITE_DURATION.time():
        for log in logs:
            # Get block timestamp
            block = w3.eth.get_block(log["blockNumber"])
            block_timestamp = block["timestamp"]

            # Store raw log
            store_raw_log(conn, log, block_timestamp)

            # Decode and store purchase
            purchase = decode_purchase_event(w3, log)
            store_purchase(conn, purchase)

            EVENTS_INDEXED.inc()

        conn.commit()

    return len(logs)


def run_indexer():
    """Main indexer loop."""
    print("=" * 60)
    print("Blockchain Indexer Starting")
    print("=" * 60)

    # Start metrics server
    print(f"Starting metrics server on port {METRICS_PORT}")
    start_http_server(METRICS_PORT)

    # Connect to Web3
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not wait_for_rpc(w3):
        print("ERROR: Could not connect to RPC")
        sys.exit(1)

    # Connect to database
    conn = wait_for_db()

    # Load contract info
    contract_info = load_contract_info(CONTRACT_INFO_PATH)
    contract_address = Web3.to_checksum_address(contract_info["contract_address"])
    abi = contract_info["abi"]

    print(f"Contract address: {contract_address}")

    # Compute event signature
    contract = w3.eth.contract(address=contract_address, abi=abi)
    event_signature = w3.keccak(text="PurchaseMade(address,uint256,uint256,uint256,uint256)").hex()
    print(f"Event signature: {event_signature}")

    # Get starting block
    last_indexed = get_last_indexed_block(conn)
    current_block = last_indexed + 1 if last_indexed > 0 else 0

    print(f"Starting from block: {current_block}")
    print("\n" + "=" * 60)
    print("Indexer running...")
    print("=" * 60 + "\n")

    while True:
        try:
            # Get chain head
            chain_head = w3.eth.block_number
            CHAIN_HEAD.set(chain_head)

            # Calculate lag
            lag = chain_head - current_block
            INDEXER_LAG.set(lag)

            if current_block <= chain_head:
                # Index in batches of 100 blocks
                to_block = min(current_block + 100, chain_head)

                events_found = index_events(
                    w3, conn, contract_address, event_signature,
                    current_block, to_block
                )

                blocks_processed = to_block - current_block + 1
                BLOCKS_PROCESSED.inc(blocks_processed)
                CURRENT_BLOCK.set(to_block)

                if events_found > 0:
                    print(f"Indexed {events_found} events | Blocks: {current_block}-{to_block} | Lag: {chain_head - to_block}")

                current_block = to_block + 1

            time.sleep(POLL_INTERVAL)

        except Exception as e:
            print(f"ERROR: {e}")
            # Reconnect to database if needed
            try:
                conn.close()
            except:
                pass
            try:
                conn = wait_for_db()
            except:
                pass
            time.sleep(5)


if __name__ == "__main__":
    run_indexer()
