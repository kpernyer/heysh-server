# Hey.sh Server - Local Development Justfile

# =============================================================================
# SETUP COMMANDS
# =============================================================================

# Install dependencies
install:
    @echo "📦 Installing dependencies..."
    @uv sync
    @echo "✅ Dependencies installed"

# Build the project
build:
    @echo "🔨 Building project..."
    @uv build
    @echo "✅ Project built"

# =============================================================================
# LOCAL DEVELOPMENT COMMANDS
# =============================================================================

# Main development command - brings up everything you need
dev: install build
    @echo "🚀 Starting Hey.sh Local Development Environment"
    @echo ""
    @just up-infra
    @echo ""
    @just verify
    @echo ""
    @echo "✅ Development environment ready!"
    @echo "🌐 Frontend: http://hey.local"
    @echo "🔧 API Server: http://api.hey.local (with hot reload)"
    @echo "⏰ Temporal UI: http://temporal.hey.local"
    @echo "🔗 Neo4j Browser: http://neo4j.hey.local"
    @echo "🔍 Weaviate: http://weaviate.hey.local"
    @echo "🗄️ Database: http://db.hey.local"
    @echo "🔴 Redis: http://redis.hey.local"
    @echo "📦 MinIO: http://supabase.hey.local"
    @echo ""
    @echo "Starting API server with hot reload..."
    @uv run uvicorn src.service.api:app --reload --host 0.0.0.0 --port 8002

# HTTPS development command - brings up everything with HTTPS
dev-https: install build
    @echo "🔐 Starting Hey.sh HTTPS Local Development Environment"
    @echo ""
    @just up-infra
    @echo ""
    @just verify
    @echo ""
    @echo "✅ HTTPS Development environment ready!"
    @echo "🌐 Frontend: https://www.hey.local"
    @echo "🔧 API Server: https://api.hey.local (with hot reload)"
    @echo "⏰ Temporal UI: https://temporal.hey.local"
    @echo "🔗 Neo4j Browser: https://neo4j.hey.local"
    @echo "🔍 Weaviate: https://weaviate.hey.local"
    @echo "🗄️ Database: https://db.hey.local"
    @echo "🔴 Redis: https://redis.hey.local"
    @echo "📦 MinIO: https://supabase.hey.local"
    @echo ""
    @echo "Starting API server with hot reload..."
    @uv run uvicorn src.service.api:app --reload --host 0.0.0.0 --port 8002

# Bring up infrastructure services (Temporal, Neo4j, Weaviate, etc.)
up-infra:
    @echo "🐳 Starting infrastructure services..."
    @docker-compose -f docker/docker-compose.yml up -d
    @echo "⏳ Waiting for services to be ready..."
    @sleep 10
    @echo "✅ Infrastructure services started"

# Verify all services are running
verify:
    @echo "🔍 Verifying services..."
    @echo ""
    @echo "📊 Service Status:"
    @echo "=================="
    @if curl -s http://localhost:8002/health >/dev/null 2>&1; then \
        echo "✅ API Server: http://localhost:8002"; \
    else \
        echo "❌ API Server: Not running"; \
    fi
    @if nc -z localhost 7233 2>/dev/null; then \
        echo "✅ Temporal: localhost:7233 (gRPC)"; \
    else \
        echo "❌ Temporal: Not running"; \
    fi
    @if curl -s http://localhost:7474 >/dev/null 2>&1; then \
        echo "✅ Neo4j: http://localhost:7474"; \
    else \
        echo "❌ Neo4j: Not running"; \
    fi
    @if curl -s http://localhost:8082 >/dev/null 2>&1; then \
        echo "✅ Weaviate: http://localhost:8082"; \
    else \
        echo "❌ Weaviate: Not running"; \
    fi
    @if curl -s http://localhost:8090 >/dev/null 2>&1; then \
        echo "✅ Temporal UI: http://localhost:8090"; \
    else \
        echo "❌ Temporal UI: Not running"; \
    fi
    @if curl -s http://localhost:80 >/dev/null 2>&1; then \
        echo "✅ Caddy: http://localhost:80"; \
    else \
        echo "❌ Caddy: Not running"; \
    fi
    @echo ""

# Clean shutdown and restart
reboot:
    @echo "🔄 Rebooting development environment..."
    @just clean
    @just dev

# Clean shutdown of all services
clean:
    @echo "🧹 Cleaning up development environment..."
    @docker-compose -f docker/docker-compose.yml down
    @docker-compose -f docker/docker-compose.yml down -v 2>/dev/null || true
    @echo "✅ Cleanup complete"

# =============================================================================
# DEVELOPMENT TOOLS
# =============================================================================

# Start workers for development
workers:
    @echo "👷 Starting Temporal workers..."
    @uv run python -m src.worker.multiqueue_worker

# Start Caddy for production hostnames (standalone)
caddy-prod:
    @echo "🌐 Starting Caddy for production hostnames..."
    @caddy run --config docker/Caddyfile.production

# Start Caddy with HTTPS for local development
caddy-https:
    @echo "🔐 Starting Caddy with HTTPS for local development..."
    @caddy run --config docker/Caddyfile.https

# Bootstrap installation of all external dependencies
bootstrap:
    @echo "🚀 Bootstrapping Hey.sh development environment..."
    @./script/bootstrap-install.sh

# Setup SSL certificates for local development
setup-ssl:
    @echo "🔐 Setting up SSL certificates for local development..."
    @if ! command -v mkcert >/dev/null 2>&1; then \
        echo "❌ mkcert is not installed. Please run 'just bootstrap' first"; \
        exit 1; \
    fi
    @echo "📜 Installing CA certificate..."
    @mkcert -install
    @echo "🔑 Generating certificates for hey.local domains..."
    @mkcert hey.local www.hey.local api.hey.local temporal.hey.local neo4j.hey.local weaviate.hey.local db.hey.local redis.hey.local minio.hey.local supabase.hey.local monitoring.hey.local grafana.hey.local alertmanager.hey.local jaeger.hey.local loki.hey.local
    @echo "✅ SSL certificates generated!"
    @echo "🔐 Certificates are in: hey.local+13.pem and hey.local+13-key.pem"
    @echo "📝 Add these to your Caddyfile.https if needed"

# Start monitoring services
monitoring:
    @echo "📊 Starting monitoring services..."
    @docker-compose -f docker/docker-compose.monitoring.yml up -d
    @echo "✅ Monitoring services started!"
    @echo "📊 Prometheus: http://monitoring.hey.local"
    @echo "📈 Grafana: http://grafana.hey.local"
    @echo "🚨 Alertmanager: http://alertmanager.hey.local"
    @echo "🔍 Jaeger: http://jaeger.hey.local"
    @echo "📝 Loki: http://loki.hey.local"

# Stop monitoring services
monitoring-stop:
    @echo "📊 Stopping monitoring services..."
    @docker-compose -f docker/docker-compose.monitoring.yml down
    @echo "✅ Monitoring services stopped!"

# =============================================================================
# TESTING
# =============================================================================

# Run tests
test:
    @echo "🧪 Running tests..."
    @uv run pytest test/ -v

# Run tests with coverage
test-coverage:
    @echo "🧪 Running tests with coverage..."
    @uv run pytest test/ --cov=src --cov-report=html --cov-report=term

# Run API endpoint tests
test-api:
    @echo "🧪 Running API endpoint tests..."
    @uv run pytest test/test_api_endpoints.py -v

# Run user endpoint tests
test-users:
    @echo "🧪 Running user endpoint tests..."
    @uv run pytest test/test_user_endpoints.py -v

# Run membership endpoint tests
test-membership:
    @echo "🧪 Running membership endpoint tests..."
    @uv run pytest test/test_membership_endpoints.py -v

# Run comprehensive test suite
test-all:
    @echo "🧪 Running comprehensive test suite..."
    @uv run python test/run_tests.py

# =============================================================================
# CODE QUALITY
# =============================================================================

# Format code
format:
    @echo "🎨 Formatting code..."
    @uv run ruff format src/ test/

# Lint code
lint:
    @echo "🔍 Linting code..."
    @uv run ruff check src/ test/

# Type check
type-check:
    @echo "🔍 Type checking..."
    @uv run mypy src/

# =============================================================================
# UTILITIES
# =============================================================================

# Show service status
status:
    @just verify

# Show logs
logs:
    @echo "📋 Showing service logs..."
    @docker-compose -f docker/docker-compose.yml logs -f

# Show help
help:
    @echo "Hey.sh Server - Local Development Commands"
    @echo ""
    @echo "🔧 Setup:"
    @echo "  bootstrap             - Install all external dependencies (Docker, mkcert, just, uv, etc.)"
    @echo "  install               - Install Python dependencies"
    @echo "  build                 - Build the project"
    @echo ""
    @echo "🚀 Development:"
    @echo "  dev                    - Start full development environment (HTTP)"
    @echo "  dev-https              - Start full development environment (HTTPS)"
    @echo "  up-infra              - Start infrastructure services only"
    @echo "  verify                - Check if all services are running"
    @echo "  reboot                - Clean restart everything"
    @echo "  clean                 - Stop and clean up all services"
    @echo ""
    @echo "🔧 Development Tools:"
    @echo "  bootstrap             - Install all external dependencies (Docker, mkcert, just, uv, etc.)"
    @echo "  workers               - Start Temporal workers"
    @echo "  caddy-prod            - Start Caddy for production hostnames"
    @echo "  caddy-https            - Start Caddy with HTTPS for local development"
    @echo "  setup-ssl             - Setup SSL certificates for local development"
    @echo ""
    @echo "📊 Monitoring:"
    @echo "  monitoring            - Start monitoring services"
    @echo "  monitoring-stop       - Stop monitoring services"
    @echo ""
    @echo "🧪 Testing:"
    @echo "  test                  - Run tests"
    @echo "  test-coverage         - Run tests with coverage"
    @echo "  test-api              - Run API endpoint tests"
    @echo "  test-users            - Run user endpoint tests"
    @echo "  test-membership       - Run membership endpoint tests"
    @echo "  test-all              - Run comprehensive test suite"
    @echo ""
    @echo "🎨 Code Quality:"
    @echo "  format                - Format code"
    @echo "  lint                  - Lint code"
    @echo "  type-check            - Type check code"
    @echo ""
    @echo "📊 Utilities:"
    @echo "  status                - Show service status"
    @echo "  logs                  - Show service logs"
    @echo "  help                  - Show this help"