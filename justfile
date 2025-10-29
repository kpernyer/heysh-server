# Hey.sh Backend - Daily Workflow
#
# Philosophy:
# - Capture the 5-10 most important daily tasks
# - Local tools: bootstrap once, verify, forget
# - Production CI/CD: repeatable setup, never lose control
# - Code stays the same: local ↔ production (smart config)
# - Focus on backend code: workflows, activities
# - Everything else should "just work"

# =============================================================================
# 🎯 DAILY TASKS (Your Real Work)
# =============================================================================

# Default: Show what you can do
default:
    @just --list --unsorted

# Start developing (your main task: write backend code)
dev:
    @echo "🚀 Starting development environment..."
    @echo ""
    @just --quiet _check-infra-status
    @echo ""
    @echo "✅ Infrastructure ready. Starting backend with hot reload..."
    @echo ""
    @echo "🌐 Frontend:    http://hey.local (or https://www.hey.local)"
    @echo "🔧 Backend API: http://api.hey.local:8002"
    @echo "⏰ Temporal UI: http://temporal.hey.local:8090"
    @echo "🔗 Neo4j:      http://neo4j.hey.local:7474"
    @echo "🔍 Weaviate:   http://weaviate.hey.local:8082"
    @echo ""
    @echo "💡 Your focus: src/workflow/ and src/activity/"
    @echo ""
    uv run uvicorn src.service.api:app --reload --host 0.0.0.0 --port 8002

# Demo mode (stable, clean environment for showing features)
demo:
    @echo "🎬 Starting DEMO mode..."
    @echo ""
    @just --quiet _check-infra-status
    @echo ""
    @echo "✨ Demo environment ready!"
    @echo ""
    @echo "🌐 Show this to stakeholders:"
    @echo "   Frontend:  https://www.hey.local"
    @echo "   API:       https://api.hey.local"
    @echo ""
    @echo "📊 Backend logs will be clean and quiet..."
    @echo ""
    uv run uvicorn src.service.api:app --host 0.0.0.0 --port 8002 --log-level warning

# Deploy to production (ship to customers)
deploy version message="Release {{version}}":
    @echo "🚀 Deploying to production: {{version}}"
    @echo "📝 {{message}}"
    @echo ""
    @if git diff --quiet && git diff --cached --quiet; then \
        echo "❌ No changes to commit"; \
        exit 1; \
    fi
    @git add -A
    @git commit -m "{{message}}"
    @git tag -a {{version}} -m "{{message}}"
    @git push origin main
    @git push origin {{version}}
    @echo ""
    @echo "✅ Deployment triggered via Cloud Build"
    @echo "📊 Monitor: just logs production"
    @echo "🌐 Live at: https://api-blwol5d45q-ey.a.run.app"
    @echo ""
    @echo "☕ Deployment takes 5-10 minutes. Use 'just check production' to verify."

# Quick deploy (auto-version, for hotfixes)
deploy-quick message="Quick deploy":
    #!/usr/bin/env bash
    set -euo pipefail
    SHORT_SHA=$(git rev-parse --short HEAD)
    VERSION="v0.0.0-${SHORT_SHA}"
    echo "⚡ Quick deploy: ${VERSION}"
    just deploy "${VERSION}" "{{message}}"

# Global health check (everything working?)
check environment="local":
    @echo "🔍 Global Health Check: {{environment}}"
    @echo "========================================"
    @echo ""
    @if [ "{{environment}}" = "local" ]; then \
        just --quiet _check-local; \
    else \
        just --quiet _check-production; \
    fi

# Run tests (verify your code works)
test:
    @echo "🧪 Running tests..."
    @uv run pytest test/ -v --tb=short

# View logs (debug issues)
logs environment="local" service="backend":
    @if [ "{{environment}}" = "local" ]; then \
        just --quiet _logs-local {{service}}; \
    else \
        just --quiet _logs-production {{service}}; \
    fi

# Learn from production (metrics, behavior, usage)
learn:
    @echo "📊 Production Insights"
    @echo "======================"
    @echo ""
    @echo "Backend Health:"
    @curl -s https://api-blwol5d45q-ey.a.run.app/health | jq '.'
    @echo ""
    @echo "Recent Deployments:"
    @gcloud builds list --limit 3 --format="table(createTime.date(tz=LOCAL),substitutions.TAG_NAME,status)"
    @echo ""
    @echo "Cloud Run Metrics:"
    @gcloud run services describe api --region=europe-west3 --format="table(status.traffic[0].revisionName,status.traffic[0].percent,status.conditions[0].status)"
    @echo ""
    @echo "Worker Pods:"
    @kubectl get pods -n temporal-workers --no-headers 2>/dev/null | wc -l | xargs -I {} echo "  {} pods running"
    @echo ""
    @echo "🔗 Full metrics: https://console.cloud.google.com/run/detail/europe-west3/api"

# =============================================================================
# 🔧 SETUP & MAINTENANCE (Run once, forget)
# =============================================================================

# Bootstrap everything (local environment)
bootstrap:
    @echo "🚀 Bootstrapping local environment..."
    @echo ""
    @echo "This will install:"
    @echo "  • Docker & Docker Compose"
    @echo "  • uv (Python package manager)"
    @echo "  • mkcert (local HTTPS)"
    @echo "  • Infrastructure services"
    @echo ""
    @./script/bootstrap-install.sh
    @echo ""
    @echo "Installing Python dependencies..."
    @uv sync
    @echo ""
    @echo "Starting infrastructure services..."
    @docker-compose -f docker/docker-compose.yml up -d
    @echo ""
    @echo "Waiting for services to be ready..."
    @sleep 15
    @echo ""
    @echo "✅ Bootstrap complete!"
    @echo ""
    @echo "Next steps:"
    @echo "  1. Run: just check"
    @echo "  2. Run: just dev"

# Bootstrap production CI/CD (repeatable setup)
bootstrap-production:
    @echo "☁️  Bootstrapping production CI/CD"
    @echo "===================================="
    @echo ""
    @echo "This documents and verifies your production setup."
    @echo "Run this to ensure CI/CD is configured correctly."
    @echo ""
    @just --quiet _bootstrap-production-check

# Fix broken infrastructure (when things go wrong)
fix:
    @echo "🔧 Fixing infrastructure..."
    @echo ""
    @echo "Stopping all services..."
    @docker-compose -f docker/docker-compose.yml down -v 2>/dev/null || true
    @echo "Removing stale containers..."
    @docker system prune -f
    @echo "Restarting services..."
    @docker-compose -f docker/docker-compose.yml up -d
    @echo "Waiting for services..."
    @sleep 15
    @echo ""
    @echo "✅ Infrastructure reset"
    @echo ""
    @echo "Run: just check"

# =============================================================================
# 🧰 UTILITIES (Helpers)
# =============================================================================

# Quick test (just API endpoints)
test-quick:
    @echo "⚡ Quick API test..."
    @uv run pytest test/test_topic_api_endpoints.py -v --tb=line

# Format code
fmt:
    @echo "🎨 Formatting code..."
    @uv run ruff format src/ test/

# Lint code
lint:
    @echo "🔍 Linting code..."
    @uv run ruff check src/ test/

# Clean everything (nuclear option)
clean:
    @echo "🧹 Cleaning everything..."
    @docker-compose -f docker/docker-compose.yml down -v 2>/dev/null || true
    @docker system prune -af
    @rm -rf .pytest_cache __pycache__ .ruff_cache
    @echo "✅ Cleaned"

# Database migration (when schema changes)
migrate-db:
    @echo "🗄️  Running database migration..."
    @echo ""
    @echo "⚠️  This will rename domains → topics in Supabase"
    @echo ""
    @echo "Please run this SQL in Supabase Dashboard:"
    @echo "  1. Go to: https://supabase.com/dashboard"
    @echo "  2. SQL Editor → New Query"
    @echo "  3. Copy: migrations/001_rename_domain_to_topic_up.sql"
    @echo "  4. Run it"
    @echo ""
    @echo "Then verify with: just check production"

# Start workers (for testing workflows locally)
workers:
    @echo "👷 Starting Temporal workers..."
    @uv run python -m src.worker.multiqueue_worker

# =============================================================================
# 🔒 INTERNAL HELPERS (Don't call directly)
# =============================================================================

# Check local infrastructure status
_check-infra-status:
    @if ! docker ps >/dev/null 2>&1; then \
        echo "❌ Docker is not running"; \
        echo "   Run: open -a Docker (or start Docker Desktop)"; \
        exit 1; \
    fi
    @if ! docker-compose -f docker/docker-compose.yml ps | grep -q "Up"; then \
        echo "🐳 Infrastructure not running. Starting..."; \
        docker-compose -f docker/docker-compose.yml up -d; \
        echo "⏳ Waiting for services..."; \
        sleep 15; \
    fi
    @echo "✅ Infrastructure is running"

# Local health check
_check-local:
    @echo "📦 Docker:"
    @if docker ps >/dev/null 2>&1; then \
        echo "  ✅ Docker is running"; \
        docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(temporal|neo4j|weaviate|postgres|redis)" || echo "  ⚠️  No services running"; \
    else \
        echo "  ❌ Docker is not running"; \
        echo "     Run: just bootstrap"; \
    fi
    @echo ""
    @echo "🔧 Backend API:"
    @if curl -s http://localhost:8002/health >/dev/null 2>&1; then \
        echo "  ✅ http://localhost:8002 - $(curl -s http://localhost:8002/health | jq -r .status)"; \
    else \
        echo "  ⚠️  Not running. Start with: just dev"; \
    fi
    @echo ""
    @echo "⏰ Temporal:"
    @if nc -z localhost 7233 2>/dev/null; then \
        echo "  ✅ localhost:7233 (gRPC) - Running"; \
        if curl -s http://localhost:8090 >/dev/null 2>&1; then \
            echo "  ✅ http://localhost:8090 (UI) - Running"; \
        fi; \
    else \
        echo "  ❌ Not running"; \
        echo "     Run: just fix"; \
    fi
    @echo ""
    @echo "🔗 Neo4j:"
    @if curl -s http://localhost:7474 >/dev/null 2>&1; then \
        echo "  ✅ http://localhost:7474 - Running"; \
    else \
        echo "  ❌ Not running"; \
        echo "     Run: just fix"; \
    fi
    @echo ""
    @echo "🔍 Weaviate:"
    @if curl -s http://localhost:8082/v1/.well-known/ready >/dev/null 2>&1; then \
        echo "  ✅ http://localhost:8082 - Ready"; \
    else \
        echo "  ❌ Not running"; \
        echo "     Run: just fix"; \
    fi
    @echo ""
    @echo "🗄️  Database:"
    @if nc -z localhost 54322 2>/dev/null; then \
        echo "  ✅ localhost:54322 - Running"; \
    else \
        echo "  ⚠️  Not running (using remote Supabase)"; \
    fi
    @echo ""
    @echo "Summary:"
    @echo "  • All services should show ✅"
    @echo "  • If ❌ appears, run: just fix"
    @echo "  • If still broken, run: just bootstrap"

# Production health check
_check-production:
    @echo "🌐 Backend API (Cloud Run):"
    @if curl -s https://api-blwol5d45q-ey.a.run.app/health >/dev/null 2>&1; then \
        HEALTH=$$(curl -s https://api-blwol5d45q-ey.a.run.app/health | jq -r .status); \
        echo "  ✅ https://api-blwol5d45q-ey.a.run.app - $$HEALTH"; \
        curl -s https://api-blwol5d45q-ey.a.run.app/api/v1/topics 2>&1 | grep -q "Missing authorization" && echo "  ✅ /api/v1/topics - Requires auth (working)"; \
    else \
        echo "  ❌ Backend not responding"; \
        echo "     Check: gcloud run services describe api --region=europe-west3"; \
    fi
    @echo ""
    @echo "🐳 Docker Images (Artifact Registry):"
    @LATEST=$$(gcloud artifacts docker tags list europe-west3-docker.pkg.dev/hey-sh-production/hey-sh-backend/service --limit=1 --format="value(tag)" 2>/dev/null | head -1); \
    if [ -n "$$LATEST" ]; then \
        echo "  ✅ Latest image: $$LATEST"; \
    else \
        echo "  ❌ No images found"; \
    fi
    @echo ""
    @echo "👷 Workers (GKE):"
    @PODS=$$(kubectl get pods -n temporal-workers --no-headers 2>/dev/null | wc -l | tr -d ' '); \
    if [ "$$PODS" -gt 0 ]; then \
        echo "  ✅ $$PODS pods running"; \
        kubectl get pods -n temporal-workers --no-headers 2>/dev/null | awk '{print "     " $$1 " - " $$3}'; \
    else \
        echo "  ⚠️  No worker pods found"; \
        echo "     Check: kubectl get pods -n temporal-workers"; \
    fi
    @echo ""
    @echo "📊 Recent Deployments:"
    @gcloud builds list --limit 3 --format="table(createTime.date(tz=LOCAL),substitutions.TAG_NAME,status)" 2>/dev/null || echo "  ⚠️  Cannot fetch (run: gcloud auth login)"
    @echo ""
    @echo "Summary:"
    @echo "  • Backend should show ✅ healthy"
    @echo "  • Workers should show running pods"
    @echo "  • Latest deployment should be SUCCESS"
    @echo ""
    @echo "Full logs: just logs production"

# Local logs
_logs-local service:
    @if [ "{{service}}" = "backend" ]; then \
        echo "📋 Backend logs (Ctrl+C to stop):"; \
        echo "   Start backend with: just dev"; \
    elif [ "{{service}}" = "temporal" ]; then \
        echo "📋 Temporal logs:"; \
        docker logs -f $$(docker ps -q -f name=temporal) 2>/dev/null || echo "Temporal not running"; \
    elif [ "{{service}}" = "neo4j" ]; then \
        echo "📋 Neo4j logs:"; \
        docker logs -f $$(docker ps -q -f name=neo4j) 2>/dev/null || echo "Neo4j not running"; \
    else \
        echo "📋 All services logs:"; \
        docker-compose -f docker/docker-compose.yml logs -f; \
    fi

# Production logs
_logs-production service:
    @if [ "{{service}}" = "backend" ]; then \
        echo "📋 Backend logs (Cloud Run):"; \
        gcloud run logs read api --region=europe-west3 --limit=50; \
    elif [ "{{service}}" = "workers" ]; then \
        echo "📋 Worker logs (GKE):"; \
        kubectl logs -n temporal-workers -l app=temporal-worker --tail=50 -f; \
    elif [ "{{service}}" = "builds" ]; then \
        echo "📋 Cloud Build logs:"; \
        BUILD_ID=$$(gcloud builds list --limit=1 --format="value(id)"); \
        gcloud builds log $$BUILD_ID; \
    else \
        echo "Available services: backend, workers, builds"; \
        echo "Example: just logs production backend"; \
    fi

# Check production CI/CD setup
_bootstrap-production-check:
    @echo "1️⃣  GCP Project:"
    @PROJECT=$$(gcloud config get-value project 2>/dev/null); \
    if [ -n "$$PROJECT" ]; then \
        echo "  ✅ Project: $$PROJECT"; \
    else \
        echo "  ❌ No project configured"; \
        echo "     Run: gcloud config set project YOUR_PROJECT_ID"; \
        exit 1; \
    fi
    @echo ""
    @echo "2️⃣  Cloud Build Triggers:"
    @TRIGGERS=$$(gcloud builds triggers list --format="value(name)" 2>/dev/null | wc -l); \
    if [ $$TRIGGERS -gt 0 ]; then \
        echo "  ✅ $$TRIGGERS triggers configured:"; \
        gcloud builds triggers list --format="table(name,filename,triggerTemplate.tagName)" 2>/dev/null || true; \
    else \
        echo "  ❌ No triggers found"; \
        echo "     Setup guide: docs/PRODUCTION_BOOTSTRAP.md"; \
    fi
    @echo ""
    @echo "3️⃣  Artifact Registry:"
    @if gcloud artifacts repositories describe hey-sh-backend --location=europe-west3 >/dev/null 2>&1; then \
        echo "  ✅ Repository: hey-sh-backend"; \
    else \
        echo "  ❌ Repository not found"; \
        echo "     Create: gcloud artifacts repositories create hey-sh-backend --repository-format=docker --location=europe-west3"; \
    fi
    @echo ""
    @echo "4️⃣  Cloud Run Service:"
    @if gcloud run services describe api --region=europe-west3 >/dev/null 2>&1; then \
        echo "  ✅ Service: api"; \
        URL=$$(gcloud run services describe api --region=europe-west3 --format="value(status.url)" 2>/dev/null); \
        echo "     URL: $$URL"; \
    else \
        echo "  ❌ Service not found"; \
    fi
    @echo ""
    @echo "5️⃣  GKE Cluster:"
    @if gcloud container clusters describe production-hey-sh-cluster --region=europe-west3 >/dev/null 2>&1; then \
        echo "  ✅ Cluster: production-hey-sh-cluster"; \
    else \
        echo "  ❌ Cluster not found"; \
        echo "     Check: infra/terraform/"; \
    fi
    @echo ""
    @echo "6️⃣  Secrets (Secret Manager):"
    @SECRETS=$$(gcloud secrets list --format="value(name)" 2>/dev/null | wc -l); \
    if [ $$SECRETS -gt 0 ]; then \
        echo "  ✅ $$SECRETS secrets configured"; \
    else \
        echo "  ⚠️  No secrets found"; \
    fi
    @echo ""
    @echo "📖 Documentation:"
    @echo "   • cloudbuild_deploy.yaml - Main deployment pipeline"
    @echo "   • infra/terraform/ - Infrastructure as code"
    @echo "   • DEPLOYMENT_WORKFLOW.md - Complete guide"
    @echo ""
    @echo "✅ If all show ✅, your CI/CD is configured correctly"
    @echo "❌ If any show ❌, see docs/PRODUCTION_BOOTSTRAP.md for setup"
