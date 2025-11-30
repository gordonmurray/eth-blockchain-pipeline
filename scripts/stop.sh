#!/bin/bash
# Stop the blockchain infrastructure stack

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "Stopping Blockchain Purchase System..."

docker compose down

echo "All services stopped."
