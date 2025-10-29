#!/bin/bash
# Setup HTTPS Local Development Environment
# This script sets up SSL certificates and configures HTTPS for local development

set -e

echo "🔐 Setting up HTTPS Local Development Environment"
echo "=================================================="

# Check if mkcert is installed
if ! command -v mkcert >/dev/null 2>&1; then
    echo "❌ mkcert is not installed!"
    echo ""
    echo "Please install mkcert first:"
    echo "  macOS: brew install mkcert"
    echo "  Linux: https://github.com/FiloSottile/mkcert#installation"
    echo "  Windows: https://github.com/FiloSottile/mkcert#installation"
    echo ""
    exit 1
fi

echo "✅ mkcert is installed"

# Install CA certificate
echo "📜 Installing CA certificate..."
mkcert -install
echo "✅ CA certificate installed"

# Generate certificates for all hey.local domains
echo "🔑 Generating SSL certificates for hey.local domains..."
mkcert hey.local www.hey.local api.hey.local temporal.hey.local neo4j.hey.local weaviate.hey.local db.hey.local redis.hey.local minio.hey.local supabase.hey.local monitoring.hey.local grafana.hey.local alertmanager.hey.local jaeger.hey.local loki.hey.local

echo "✅ SSL certificates generated!"
echo ""

# Show certificate files
echo "📁 Certificate files created:"
ls -la hey.local+*.pem hey.local+*-key.pem 2>/dev/null || echo "   (certificate files not found in current directory)"

echo ""
echo "🔧 Next Steps:"
echo "=============="
echo "1. Start your infrastructure:"
echo "   just up-infra"
echo ""
echo "2. Start Caddy with HTTPS:"
echo "   just caddy-https"
echo ""
echo "3. Start your backend API:"
echo "   just start-api"
echo ""
echo "4. Start your frontend (in another terminal):"
echo "   cd /Users/kpernyer/repo/hey-sh-workflow"
echo "   npm run dev"
echo ""
echo "5. Access your application:"
echo "   Frontend: https://www.hey.local"
echo "   API: https://api.hey.local"
echo "   Temporal UI: https://temporal.hey.local"
echo ""
echo "🎉 HTTPS Local Development Environment is ready!"
