#!/bin/bash
# Quick database query helper

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Default query
QUERY="${1:-SELECT * FROM get_recent_purchases(10);}"

echo "Running query: $QUERY"
echo ""

docker compose exec -T postgres psql -U indexer -d blockchain_data -c "$QUERY"
