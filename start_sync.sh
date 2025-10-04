#!/bin/bash
# Quick start script for ClickHouse to Datadog sync

echo "=================================================="
echo "ClickHouse to Datadog Sync - Quick Start"
echo "=================================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env with your credentials."
    exit 1
fi

echo "✓ Found .env file"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found!"
    exit 1
fi

echo "✓ Python 3 installed"

# Test sync once
echo ""
echo "Testing sync (one-time run)..."
echo "--------------------------------------------------"
python3 sync_clickhouse_to_datadog.py --once

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Test successful!"
    echo ""
    echo "Do you want to start continuous sync? (y/n)"
    read -r response
    
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo ""
        echo "Starting continuous sync..."
        echo "Press Ctrl+C to stop"
        echo "--------------------------------------------------"
        python3 sync_clickhouse_to_datadog.py
    else
        echo ""
        echo "To start sync later, run:"
        echo "  python3 sync_clickhouse_to_datadog.py"
        echo ""
        echo "To run in background:"
        echo "  nohup python3 sync_clickhouse_to_datadog.py > sync.log 2>&1 &"
    fi
else
    echo ""
    echo "❌ Test failed!"
    echo "Please check the error messages above."
    exit 1
fi

