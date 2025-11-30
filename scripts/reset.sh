#!/bin/bash
# Reset all data and restart fresh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "=============================================="
echo "Resetting Blockchain Purchase System"
echo "=============================================="
echo ""
echo "WARNING: This will delete all blockchain data,"
echo "         database data, and monitoring data!"
echo ""

read -p "Are you sure? (y/N) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Stopping services..."
    docker compose down -v

    echo "Removing any orphan volumes..."
    docker volume prune -f

    echo ""
    echo "Reset complete. Run ./scripts/start.sh to start fresh."
else
    echo "Reset cancelled."
fi
