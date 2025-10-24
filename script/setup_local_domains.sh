#!/bin/bash
# Setup script for local development with real hostnames
# Usage: ./script/setup_local_domains.sh

set -e

echo "🌐 Setting up local development domains for hey.sh"
echo ""

# Check if Caddy is installed
if ! command -v caddy &> /dev/null; then
    echo "📦 Caddy not found. Installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install caddy
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
        curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
        curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
        sudo apt update
        sudo apt install caddy
    else
        echo "❌ Unsupported OS. Please install Caddy manually: https://caddyserver.com/docs/install"
        exit 1
    fi
    echo "✅ Caddy installed"
fi

# Add entries to /etc/hosts
echo ""
echo "🔧 Adding entries to /etc/hosts..."
echo "   (This requires sudo access)"

HOSTS_ENTRIES="
# Hey.sh local development
127.0.0.1  app.hey.local
127.0.0.1  api.hey.local
127.0.0.1  temporal.hey.local
127.0.0.1  neo4j.hey.local
127.0.0.1  weaviate.hey.local
"

# Check if entries already exist
if grep -q "app.hey.local" /etc/hosts; then
    echo "⚠️  Entries already exist in /etc/hosts"
else
    echo "$HOSTS_ENTRIES" | sudo tee -a /etc/hosts > /dev/null
    echo "✅ Added entries to /etc/hosts"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Start your services (already running)"
echo "   2. Start Caddy: cd backend && caddy run --config docker/Caddyfile"
echo "   3. Access services:"
echo "      - Frontend:   http://app.hey.local"
echo "      - API:        http://api.hey.local"
echo "      - Temporal:   http://temporal.hey.local"
echo "      - Neo4j:      http://neo4j.hey.local"
echo "      - Weaviate:   http://weaviate.hey.local"
echo ""
echo "💡 Tip: Add 'caddy run --config docker/Caddyfile' to your startup"
