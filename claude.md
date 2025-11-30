Blockchain Purchase System – Learning & Build Guide

This document defines the purpose, learning objectives, architecture, milestones, and workflows for building a local blockchain infrastructure lab that simulates a small purchase system on a testnet/devnet.
The project is intentionally structured to mirror data engineering, SRE/infra, and FinOps patterns you already know — but applied to blockchain.

1. Purpose of This Project

Create a hands-on learning environment that teaches:

How blockchain infrastructure actually works
Running a full node, exposing RPC/WebSocket interfaces, handling transactions, watching logs/events, indexing data.

How a blockchain node behaves operationally
Syncing, block production, storage needs, monitoring, reliability, cost considerations.

How to build a data pipeline on top of blockchain
Treating transaction events the same way you’d treat Kafka → Flink → Iceberg → BI.

How to simulate real business activity
Using dummy “store purchase” transactions to create meaningful, relatable data.

How to think like an infra engineer at Infura, Alchemy, QuickNode, The Graph, Etherscan, or Dune Analytics.

The final result should be a GitHub-ready learning lab that demonstrates blockchain infra + data engineering + observability + operations.

2. Project Summary (High-Level)

You will build:

A local blockchain devnet using Docker Compose
(execution client + RPC + devnet config)

A simple smart contract emitting structured PurchaseMade events
(represents “raw data” similar to rows in a table)

A purchase simulator
Python script generating transactions from 2–3 wallets.

An indexer service
Polls the chain for PurchaseMade events and stores them.

A Postgres database
Holds raw events and curated purchase tables.

Prometheus + Grafana
Observes node health, RPC performance, and indexer lag.

(Optional) Block explorer (Blockscout)
Provides a UI to browse blocks, transactions, and events.

This mirrors a minimal “mini-Infura + mini-Dune + mini-Etherscan” stack.

3. Why This Project Works (Analogy to Data Engineering)
Equivalent Concepts
Data Engineering World	Blockchain World Equivalent
Kafka topic	Blockchain blocks & transactions
Producer sending messages	Wallet submitting transactions
Event schema	Smart contract events (logs)
ETL job / Flink job	Indexer reading logs via RPC
Data warehouse (Iceberg/Postgres)	Postgres storing decoded events
Metrics/observability	Node metrics + RPC latency + lag
BI dashboards	Grafana/Superset dashboards

By the end, you will have built a genuine streaming → storage → analytics pipeline, just with blockchain as the data source.

4. Core Learning Goals
Infrastructure

Run and manage an Ethereum client locally.

Understand RPC endpoints and WebSocket subscriptions.

Understand block production, state, and logs.

Data Engineering

Map blockchain logs to structured data.

Build a small indexing pipeline.

Store raw/clean tables and analyze them.

SRE / Operations

Monitor block height, node health, event throughput.

Observe lag, RPC errors, container resource usage.

Document recovery steps and typical failure modes.

FinOps

Understand storage/CPU/network costs if this ran on AWS.

Compare pruned vs full node size implications.

Understand IO profiles for blockchain nodes.

5. Architecture Overview (No Code)
Services (All via Docker Compose)

Execution Client (geth/erigon)

Provides JSON-RPC and WS endpoints.

Stores the chain data.

Produces events.

Postgres

Raw blockchain logs (JSON)

Purchase tables (structured)

Indexer (Python or similar)

Polls eth_getLogs for the PurchaseMade event signature.

Writes into Postgres.

Purchase Simulator

Holds 2–3 wallets.

Randomly selects products/quantities.

Sends signed purchase transactions.

Prometheus + Node Metrics

Scrapes blockchain node, indexer, and host stats.

Grafana

Visualizes:

Block height/lag

RPC latency

CPU/disk

Events per second

(Optional) Blockscout

Visual interface over your chain.

6. Data Model (Events)

Single smart contract event schema:

PurchaseMade(
  buyer_address,
  product_id,
  price,
  quantity,
  timestamp
)


This is your raw data equivalent to a Kafka “purchase events” stream.

Postgres Tables You’ll Store

raw_logs (raw JSON)

purchases (decoded structured table)

Optional aggregates: daily_product_sales, buyers_summary

7. Project Milestones
Phase 1 – Local Devnet Infra

Goal: Start a local chain + RPC endpoint.

Spin up execution client container.

Confirm access to RPC:

get block number

get gas price

Success criteria:
You can query the chain via curl or a JSON-RPC client.

Phase 2 – Contract Deployment

Goal: Deploy a minimal smart contract that emits PurchaseMade.

Deploy contract to local devnet.

Store contract address and ABI.

Verify you can call purchase() manually (1 transaction).

Success criteria:
You see the event emitted in the transaction receipt.

Phase 3 – Purchase Simulator

Goal: Create steady, realistic purchase events.

2–3 wallets

Random purchases every few seconds

Runs as a container in the compose stack

Success criteria:
Blockscout shows transactions increasing.
RPC logs show activity.

Phase 4 – Indexer

Goal: Build an ingestion pipeline.

Connect to RPC

Query eth_getLogs from last processed block

Decode into structured rows

Insert into Postgres

Success criteria:
Your Postgres tables fill up with purchase rows.

Phase 5 – Analytics

Goal: Treat the data like a true dataset.

Query purchases per product

Query purchases per wallet

Produce time-series views

Optional: Use Superset or Evidence

Success criteria:
You can perform analytics on the purchase activity.

Phase 6 – Observability

Goal: Monitor the system.

Prometheus scraping node metrics

Grafana dashboards for:

block lag

peer count

CPU/disk

event rate

indexer lag

Success criteria:
You can visually confirm health of the chain & data pipeline.

Phase 7 – Production Thinking (Documentation Only)

Goal: Map learnings to real-world infra roles.

Document what would change on AWS:

EC2 + gp3 profiles

S3 snapshots

Terraform module layout

NLB for RPC traffic

KMS for validator keys (if doing staking)

Document cost considerations:

storage growth

instance type

snapshot frequency

monitoring cost (CloudWatch or Prometheus)

Success criteria:
Repo includes a “Production Notes” doc showing you understand operational tradeoffs.

8. Suggested Repo Structure
.
├── Claude.md
├── docs/
│   ├── architecture-overview.md
│   ├── data-model.md
│   ├── ops-and-finops-notes.md
│   ├── analytics-examples.md
├── docker/
│   ├── compose-base.md
│   ├── service-descriptions.md
└── infra-notes/
    ├── terraform-outline.md
    ├── aws-sizing.md

9. End State / What You Can Officially Claim You’ve Learned

Ran an Ethereum-based devnet with full RPC endpoints.

Understood block structure, transactions, logs, and state.

Built a small indexing architecture (RPC → indexer → Postgres).

Deployed smart contracts and generated real transactions.

Implemented observability (Prometheus + Grafana).

Modeled cost and reliability concerns.

Understood how data engineering patterns map directly to blockchain.

This is enough to sit in a blockchain infra/SRE/Data role with confidence.
