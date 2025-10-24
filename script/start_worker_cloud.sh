#!/bin/bash
# Start Temporal worker with Temporal Cloud configuration

set -e

echo "🚀 Starting Temporal Worker (Temporal Cloud)"
echo "============================================="

# Load environment variables
set -a
source .env
set +a

# Verify Temporal Cloud settings
if [ -z "$TEMPORAL_API_KEY" ]; then
    echo "❌ Error: TEMPORAL_API_KEY not set in .env file"
    exit 1
fi

echo "📡 Temporal Address: $TEMPORAL_ADDRESS"
echo "📦 Namespace: $TEMPORAL_NAMESPACE"
echo "🔑 API Key: ${TEMPORAL_API_KEY:0:20}..."
echo "🔄 Task Queue: $TEMPORAL_TASK_QUEUE"
echo ""

# Start worker
.venv/bin/python worker/main.py
