#!/bin/bash

# Docker network management script
echo "🐳 Managing Docker networks..."

# Create hey-network if it doesn't exist
if ! docker network ls | grep -q hey-network; then
    echo "Creating hey-network..."
    docker network create hey-network
    echo "✅ hey-network created"
else
    echo "✅ hey-network already exists"
fi

# List all networks
echo "📋 Available Docker networks:"
docker network ls

# Show network details
echo "🔍 hey-network details:"
docker network inspect hey-network

echo "🐳 Docker network management completed"
