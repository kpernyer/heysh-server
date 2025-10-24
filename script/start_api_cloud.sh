#!/bin/bash
# Start FastAPI server with Temporal Cloud configuration

set -e

echo "🚀 Starting Hey.sh Backend API (Temporal Cloud)"
echo "================================================"

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
echo "🌐 Starting API on http://localhost:8001"
echo ""

# Start API
.venv/bin/uvicorn service.api:app --reload --port 8001
