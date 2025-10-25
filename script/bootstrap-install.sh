#!/bin/bash
# Bootstrap Installation Script for Hey.sh Development Environment
# This script installs all external dependencies required for local development

set -e

echo "🚀 Hey.sh Development Environment Bootstrap"
echo "=========================================="
echo ""

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is designed for macOS. Please install dependencies manually:"
    echo "   - Docker Desktop"
    echo "   - mkcert: https://github.com/FiloSottile/mkcert#installation"
    echo "   - just: https://github.com/casey/just#installation"
    echo "   - uv: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

echo "📋 Installing external dependencies..."
echo ""

# Check if Homebrew is installed
if ! command -v brew >/dev/null 2>&1; then
    echo "❌ Homebrew is not installed!"
    echo "Please install Homebrew first: https://brew.sh/"
    echo ""
    echo "Run this command to install Homebrew:"
    echo '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    exit 1
fi

echo "✅ Homebrew is installed"

# Update Homebrew
echo "🔄 Updating Homebrew..."
brew update

# Install Docker Desktop (if not already installed)
echo "🐳 Checking Docker Desktop..."
if ! command -v docker >/dev/null 2>&1; then
    echo "📦 Installing Docker Desktop..."
    brew install --cask docker
    echo "✅ Docker Desktop installed"
    echo "⚠️  Please start Docker Desktop from Applications folder"
else
    echo "✅ Docker Desktop is already installed"
fi

# Install mkcert for SSL certificates
echo "🔐 Installing mkcert for SSL certificates..."
if ! command -v mkcert >/dev/null 2>&1; then
    brew install mkcert
    echo "✅ mkcert installed"
else
    echo "✅ mkcert is already installed"
fi

# Install just command runner
echo "⚡ Installing just command runner..."
if ! command -v just >/dev/null 2>&1; then
    brew install just
    echo "✅ just installed"
else
    echo "✅ just is already installed"
fi

# Install uv Python package manager
echo "🐍 Installing uv Python package manager..."
if ! command -v uv >/dev/null 2>&1; then
    brew install uv
    echo "✅ uv installed"
else
    echo "✅ uv is already installed"
fi

# Install curl (usually pre-installed, but just in case)
echo "🌐 Checking curl..."
if ! command -v curl >/dev/null 2>&1; then
    brew install curl
    echo "✅ curl installed"
else
    echo "✅ curl is already installed"
fi

# Install netcat (nc) for port checking
echo "🔌 Checking netcat..."
if ! command -v nc >/dev/null 2>&1; then
    brew install netcat
    echo "✅ netcat installed"
else
    echo "✅ netcat is already installed"
fi

# Install jq for JSON processing (useful for API testing)
echo "📄 Checking jq..."
if ! command -v jq >/dev/null 2>&1; then
    brew install jq
    echo "✅ jq installed"
else
    echo "✅ jq is already installed"
fi

echo ""
echo "🎉 Bootstrap installation complete!"
echo ""
echo "📋 Next Steps:"
echo "=============="
echo "1. Start Docker Desktop (if not already running)"
echo "2. Generate SSL certificates:"
echo "   sudo mkcert -install"
echo "   mkcert hey.local www.hey.local api.hey.local temporal.hey.local neo4j.hey.local weaviate.hey.local db.hey.local redis.hey.local minio.hey.local supabase.hey.local monitoring.hey.local grafana.hey.local alertmanager.hey.local jaeger.hey.local loki.hey.local"
echo ""
echo "3. Start development environment:"
echo "   just dev-https"
echo ""
echo "4. Or start services manually:"
echo "   just up-infra"
echo "   just caddy-https"
echo "   HEY_HTTPS=true uv run uvicorn src.service.api:app --reload --host 0.0.0.0 --port 8002"
echo ""
echo "🌐 Access your application:"
echo "   Frontend: https://www.hey.local"
echo "   API: https://api.hey.local"
echo "   Temporal UI: https://temporal.hey.local"
echo ""
echo "✅ Ready for HTTPS development!"
