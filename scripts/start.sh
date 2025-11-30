#!/bin/bash
# Start the blockchain infrastructure stack

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "=============================================="
echo "Starting Blockchain Purchase System"
echo "=============================================="

# Build and start all services
docker compose up -d --build

echo ""
echo "=============================================="
echo "Services Starting..."
echo "=============================================="
echo ""
echo "Wait a few seconds for all services to initialize."
echo ""
echo "Available endpoints:"
echo "  - Geth RPC:     http://localhost:8545"
echo "  - Geth WS:      ws://localhost:8546"
echo "  - PostgreSQL:   localhost:5432 (user: indexer, pass: indexer_pass)"
echo "  - Prometheus:   http://localhost:9090"
echo "  - Grafana:      http://localhost:3000 (admin/admin)"
echo "  - Indexer:      http://localhost:8000/metrics"
echo ""
echo "Useful commands:"
echo "  - View logs:    docker compose logs -f"
echo "  - Stop:         docker compose down"
echo "  - Clean reset:  docker compose down -v"
echo ""
