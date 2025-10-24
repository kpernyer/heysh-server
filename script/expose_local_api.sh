#!/bin/bash
# Expose local backend to Lovable using ngrok
# Usage: ./script/expose_local_api.sh

set -e

echo "🌐 Exposing local backend to the internet..."
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "📦 ngrok not found. Installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install ngrok
    else
        echo "Please install ngrok: https://ngrok.com/download"
        exit 1
    fi
fi

# Check if backend is running
if ! curl -s http://localhost:8001/health > /dev/null; then
    echo "❌ Backend not running on port 8001"
    echo "   Start it with: cd backend && just dev"
    exit 1
fi

echo "✅ Backend is running"
echo ""
echo "🚀 Starting ngrok tunnel..."
echo "   Local:  http://localhost:8001"
echo "   Public: (see below)"
echo ""
echo "💡 Use the public URL in Lovable for API calls"
echo "   Example: https://abc123.ngrok.io/api/v1/documents"
echo ""

# Start ngrok
ngrok http 8001
