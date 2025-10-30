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

# Default: Show help
default:
    @just --list

# Gossip: Tell me where we left off and what's next
gossip:
    @echo "╔════════════════════════════════════════════════════════════════╗"
    @echo "║           💬 What's Up? Where Did We Leave Off?               ║"
    @echo "╚════════════════════════════════════════════════════════════════╝"
    @echo ""
    @just --quiet _status-git
    @echo ""
    @just --quiet _status-local
    @echo ""
    @just --quiet _status-production
    @echo ""
    @just --quiet _status-suggestions

# Start developing (your main task: write backend code)
dev:
    @echo "🚀 Starting development environment..."
    @echo ""
    @just --quiet _check-infra-status
    @echo ""
    @just --quiet _claim-port-8002
    @echo ""
    @echo "✅ Infrastructure ready. Starting backend with hot reload..."
    @echo ""
    @echo "🌐 Access your services via Caddy (hostnames, not ports):"
    @echo "   Frontend:       http://hey.local  or  http://www.hey.local"
    @echo "   Backend API:    http://api.hey.local"
    @echo "   Temporal UI:    http://temporal.hey.local"
    @echo "   Neo4j Browser:  http://neo4j.hey.local"
    @echo "   Weaviate:       http://weaviate.hey.local"
    @echo "   Storage (S3):   http://storage.hey.local"
    @echo "   MinIO Console:  http://minio-console.hey.local (dev tool)"
    @echo ""
    @echo "💡 Your focus: src/workflow/ and src/activity/"
    @echo "💡 Your backend owns port 8002 (highest priority)"
    @echo ""
    @echo "📝 Using environment: .env.local"
    @echo ""
    #!/usr/bin/env bash
    set -a
    source .env.local
    set +a
    uv run uvicorn src.service.api:app --reload --host 0.0.0.0 --port 8002

# Demo mode (stable, clean environment for showing features)
demo:
    @echo "🎬 Starting DEMO mode..."
    @echo ""
    @just --quiet _check-infra-status
    @echo ""
    @just --quiet _claim-port-8002
    @echo ""
    @echo "✨ Demo environment ready!"
    @echo ""
    @echo "🌐 Show this to stakeholders (via Caddy hostnames):"
    @echo "   Frontend:  http://www.hey.local"
    @echo "   API:       http://api.hey.local"
    @echo ""
    @echo "📊 Backend logs will be clean and quiet..."
    @echo ""
    @echo "📝 Using environment: .env.local"
    @echo ""
    #!/usr/bin/env bash
    set -a
    source .env.local
    set +a
    uv run uvicorn src.service.api:app --host 0.0.0.0 --port 8002 --log-level warning

# =============================================================================
# 🚀 DEPLOYMENT (Git Commit = Deployment Trigger)
# =============================================================================

# Deploy new version (creates version tag, triggers Cloud Build)
deploy version message="Release {{version}}":
    @echo "🚀 Deploying version: {{version}}"
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
    @echo "✅ Version {{version}} committed and tagged"
    @echo "🔨 Cloud Build will build this version automatically"
    @echo ""
    @echo "📊 Monitor build: just build-status"
    @echo "🔍 When ready: just version-status {{version}}"
    @echo ""
    @echo "💡 This version is now a production-ready candidate"
    @echo "   Use 'just promote {{version}}' to flip traffic to it"

# Promote a version to production (flip traffic)
promote version:
    @echo "🎯 Promoting version {{version}} to production"
    @echo ""
    @just --quiet _cloud-run-update-traffic {{version}} 100
    @echo ""
    @echo "✅ Traffic flipped to {{version}}"
    @echo "🌐 Live at: https://api.hey.sh"
    @echo ""
    @echo "Verify: just status production"

# Promote to staging (for testing before production)
promote-staging version:
    @echo "🧪 Promoting version {{version}} to staging"
    @echo ""
    @just --quiet _cloud-run-staging-deploy {{version}}
    @echo ""
    @echo "✅ Staging updated to {{version}}"
    @echo "🌐 Test at: https://staging-api.hey.sh"
    @echo ""
    @echo "When ready: just promote {{version}}"

# Gradual rollout (canary deployment)
rollout version percent:
    @echo "🐤 Canary rollout: {{version}} at {{percent}}%"
    @just --quiet _cloud-run-split-traffic {{version}} {{percent}}
    @echo ""
    @echo "Monitor: just metrics production"
    @echo "Continue: just rollout {{version}} 100"
    @echo "Rollback: just rollback"

# Rollback to previous version
rollback:
    @echo "⏮️  Rolling back to previous version"
    @just --quiet _cloud-run-rollback
    @echo ""
    @echo "✅ Rolled back"
    @echo "Verify: just status production"

# Quick deploy (auto-version for hotfixes)
hotfix message="Hotfix":
    #!/usr/bin/env bash
    set -euo pipefail
    SHORT_SHA=$(git rev-parse --short HEAD)
    TIMESTAMP=$(date +%Y%m%d-%H%M)
    VERSION="hotfix-${TIMESTAMP}-${SHORT_SHA}"
    echo "⚡ Creating hotfix: ${VERSION}"
    just deploy "${VERSION}" "{{message}}"

# Rebuild base Docker image (run when requirements.txt changes)
rebuild-base:
    @echo "🏗️  Rebuilding Python base image with dependencies"
    @echo "   This takes ~5 minutes but makes future deploys 6x faster!"
    @echo ""
    @gcloud builds submit --config cloudbuild_base.yaml .
    @echo ""
    @echo "✅ Base image rebuilt"
    @echo "📦 Next deployments will use cached dependencies"
    @echo "⚡ Expected deploy time: 2-4 minutes (down from 15 minutes)"

# =============================================================================
# 📊 MONITORING & STATUS (Inspect Production)
# =============================================================================

# Check status of environment
status environment="production":
    #!/usr/bin/env bash
    set -euo pipefail
    echo "🔍 Status Check: {{environment}}"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    if [ "{{environment}}" = "local" ]; then
        just --quiet _check-local
    elif [ "{{environment}}" = "staging" ]; then
        just --quiet _status-staging
    else
        just --quiet _status-production
    fi

# Get current production version info
version-info:
    @just --quiet _prod-version-info

# Check status of a specific version
version-status version:
    @just --quiet _version-status {{version}}

# List all deployed versions
versions:
    @just --quiet _list-versions

# Show build status
build-status:
    @just --quiet _build-status

# Show production metrics
metrics:
    @just --quiet _prod-metrics

# Global health check (everything working?)
check environment="local":
    #!/usr/bin/env bash
    set -euo pipefail

    echo "🔍 Global Health Check: {{environment}}"
    echo "========================================"
    echo ""
    if [ "{{environment}}" = "local" ]; then
        just --quiet _check-local
    else
        just --quiet _check-production
    fi

# Run tests (verify your code works)
test:
    @echo "🧪 Running tests..."
    @uv run pytest test/ -v --tb=short

# View logs (debug issues) - interactive menu or direct call
logs environment="" service="":
    #!/usr/bin/env bash
    set -euo pipefail

    # If both args provided, call directly
    if [ -n "{{environment}}" ] && [ -n "{{service}}" ]; then
        if [ "{{environment}}" = "local" ]; then
            just --quiet _logs-local {{service}}
        else
            just --quiet _logs-production {{service}}
        fi
        exit 0
    fi

    # Interactive menu
    echo "📋 Which logs do you want to see?"
    echo ""
    echo "Local:"
    echo "  1. Backend API (just dev output)"
    echo "  2. Temporal (workflow engine)"
    echo "  3. Neo4j (graph database)"
    echo "  4. Weaviate (vector search)"
    echo "  5. Caddy (reverse proxy)"
    echo "  6. All services (docker-compose logs)"
    echo ""
    echo "Production:"
    echo "  7. Backend (Cloud Run)"
    echo "  8. Workers (GKE)"
    echo "  9. Builds (Cloud Build)"
    echo ""
    echo -n "Choose [1-9]: "
    read -r choice

    case $choice in
        1)
            just --quiet _logs-local backend
            ;;
        2)
            just --quiet _logs-local temporal
            ;;
        3)
            just --quiet _logs-local neo4j
            ;;
        4)
            just --quiet _logs-local weaviate
            ;;
        5)
            just --quiet _logs-local caddy
            ;;
        6)
            just --quiet _logs-local all
            ;;
        7)
            just --quiet _logs-production backend
            ;;
        8)
            just --quiet _logs-production workers
            ;;
        9)
            just --quiet _logs-production builds
            ;;
        *)
            echo "❌ Invalid choice: $choice"
            exit 1
            ;;
    esac

# Learn from production (metrics, behavior, usage)
learn:
    @echo "📊 Production Insights"
    @echo "======================"
    @echo ""
    @just --quiet _prod-insights

# Check SSL certificate and domain status
domain:
    #!/usr/bin/env bash
    set -euo pipefail

    echo "🔐 SSL Certificate & Domain Status"
    echo "==================================="
    echo ""

    echo "1️⃣  Static IP:"
    IP=$(gcloud compute addresses describe api-hey-sh-ip --global --format="value(address)" 2>/dev/null || echo "Not found")
    echo "   IP: $IP"
    echo ""

    echo "2️⃣  DNS Status (api.hey.sh → $IP):"
    CURRENT_IP=$(dig +short api.hey.sh 2>/dev/null | head -1 || echo "")
    if [ "$CURRENT_IP" = "$IP" ]; then
        echo "   ✅ DNS configured correctly"
    elif [ -z "$CURRENT_IP" ]; then
        echo "   ❌ DNS not set"
    else
        echo "   ❌ DNS points to $CURRENT_IP (expected $IP)"
    fi
    echo ""

    echo "3️⃣  SSL Certificate:"
    STATUS=$(gcloud compute ssl-certificates describe api-hey-sh-cert --global --format="value(managed.status)" 2>/dev/null || echo "Not found")
    echo "   Status: $STATUS"
    if [ "$STATUS" = "ACTIVE" ]; then
        echo "   ✅ Certificate is active and ready"
    elif [ "$STATUS" = "PROVISIONING" ]; then
        echo "   ⏳ Certificate provisioning (wait 10-20 min after DNS propagates)"
    else
        echo "   ❌ Certificate not ready"
    fi
    echo ""

    echo "4️⃣  Load Balancer:"
    LB=$(gcloud compute forwarding-rules describe api-https-rule --global --format="value(IPAddress)" 2>/dev/null || echo "Not found")
    if [ "$LB" != "Not found" ]; then
        echo "   ✅ Load balancer configured ($LB)"
    else
        echo "   ❌ Load balancer not found"
    fi
    echo ""

    echo "5️⃣  HTTPS Endpoint:"
    if curl -s --connect-timeout 5 https://api.hey.sh/health >/dev/null 2>&1; then
        echo "   ✅ https://api.hey.sh is responding"
    else
        echo "   ❌ https://api.hey.sh not accessible yet"
    fi
    echo ""

    echo "Next steps:"
    if [ "$STATUS" != "ACTIVE" ]; then
        echo "  • Wait for DNS to propagate (dig api.hey.sh)"
        echo "  • Wait for SSL certificate to provision (10-20 min)"
        echo "  • Run: just domain (to check again)"
    else
        echo "  • ✅ Everything is ready! https://api.hey.sh should work"
    fi

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

# Check local infrastructure status (Caddy is priority #1)
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
    @if ! docker ps --filter "name=docker-caddy" | grep -q "Up"; then \
        echo "⚠️  Caddy not running. Caddy is CRITICAL for hostname-based development!"; \
        echo "   Starting Caddy..."; \
        docker-compose -f docker/docker-compose.yml up -d caddy; \
        sleep 2; \
    fi
    @if ! docker ps --filter "name=docker-caddy" | grep -q "Up"; then \
        echo "❌ Caddy failed to start. Check docker-compose.yml"; \
        exit 1; \
    fi
    @echo "✅ Infrastructure is running (Caddy + services)"

# Claim port 8002 (your port - highest priority)
_claim-port-8002:
    #!/usr/bin/env bash
    set -euo pipefail

    # Check if port 8002 is in use
    if lsof -ti:8002 >/dev/null 2>&1; then
        echo "🔧 Port 8002 occupied by earlier backend process"
        PID=$(lsof -ti:8002)
        PROCESS=$(ps -p $PID -o comm= 2>/dev/null || echo "unknown")
        echo "   Process: $PROCESS (PID: $PID)"
        echo "   Philosophy: Port 8002 is YOURS! Killing old process..."
        kill -9 $PID 2>/dev/null || true
        sleep 1
        echo "   ✅ Port 8002 is now free"
    fi

# Local health check
_check-local:
    #!/usr/bin/env bash
    set -euo pipefail

    echo "🌐 Caddy (Hostname Routing) - PRIORITY #1:"
    if docker ps --filter "name=docker-caddy" | grep -q "Up"; then
        echo "  ✅ Caddy is running (port 80/443)"
        echo "     Hostnames: *.hey.local → services"
    else
        echo "  ❌ Caddy not running - CRITICAL!"
        echo "     Run: just fix"
        echo "     Caddy provides hostname-based routing"
    fi
    echo ""

    echo "🔧 Backend API:"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://api.hey.local/health 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        STATUS=$(curl -s http://api.hey.local/health | jq -r .status 2>/dev/null || echo "healthy")
        echo "  ✅ http://api.hey.local - $STATUS"
        echo "     (via Caddy → localhost:8002)"
    elif [ "$HTTP_CODE" = "502" ]; then
        echo "  ⚠️  Not running (Caddy is ready, backend on port 8002 not started)"
        echo "     Start with: just dev"
    else
        echo "  ❌ Error (HTTP $HTTP_CODE)"
        echo "     Check: just fix"
    fi
    echo ""

    echo "📦 Infrastructure Services:"
    if docker ps >/dev/null 2>&1; then
        if docker ps --filter "name=temporal" | grep -q temporal; then
            echo "  ✅ Temporal + Temporal UI → http://temporal.hey.local"
        fi
        if docker ps --filter "name=neo4j" | grep -q neo4j; then
            echo "  ✅ Neo4j → http://neo4j.hey.local"
        fi
        if docker ps --filter "name=weaviate" | grep -q weaviate; then
            echo "  ✅ Weaviate → http://weaviate.hey.local"
        fi
        if docker ps --filter "name=postgres" | grep -q postgres; then
            echo "  ✅ PostgreSQL → db.hey.local:5432"
        fi
        if docker ps --filter "name=redis" | grep -q redis; then
            echo "  ✅ Redis → redis.hey.local:6379"
        fi
        if docker ps --filter "name=minio" | grep -q minio; then
            echo "  ✅ Storage (MinIO) → http://storage.hey.local"
            echo "     Console: http://minio-console.hey.local"
        fi
    else
        echo "  ❌ Docker is not running"
        echo "     Run: just bootstrap"
    fi
    echo ""

    echo "Summary:"
    echo "  • Caddy MUST be running (provides hostnames)"
    echo "  • Backend: http://api.hey.local (your port 8002)"
    echo "  • All services accessible via *.hey.local hostnames"
    echo ""
    echo "  Abstracted Services (same code, different backends):"
    echo "  • Database: db.hey.local (Postgres locally, Supabase in prod)"
    echo "  • Storage: http://storage.hey.local (MinIO locally, Supabase in prod)"
    echo ""
    echo "  • If ❌ appears, run: just fix"
    echo "  • Philosophy: Hostnames not ports, abstract implementation!"

# Production health check
_check-production:
    #!/usr/bin/env bash
    set -euo pipefail

    echo "🌐 Backend API:"
    if curl -s https://api.hey.sh/health >/dev/null 2>&1; then
        HEALTH=$(curl -s https://api.hey.sh/health | jq -r .status)
        VERSION=$(curl -s https://api.hey.sh/api/v1/info | jq -r .version)
        echo "  ✅ https://api.hey.sh - $HEALTH (v$VERSION)"
        curl -s https://api.hey.sh/api/v2/config/features >/dev/null 2>&1 && echo "  ✅ API v2 - Working"
    else
        echo "  ❌ Backend not responding"
        echo "     Check: just status production"
    fi
    echo ""
    just --quiet _check-production-infra

# Production infrastructure check (wrapped gcloud commands)
_check-production-infra:
    #!/usr/bin/env bash
    set -euo pipefail

    echo "🐳 Docker Images:"
    LATEST=$(gcloud artifacts docker tags list europe-west3-docker.pkg.dev/hey-sh-production/hey-sh-backend/service --limit=1 --format="value(tag)" 2>/dev/null | head -1)
    if [ -n "$LATEST" ]; then
        echo "  ✅ Latest image: $LATEST"
    else
        echo "  ❌ No images found"
    fi
    echo ""
    echo "📊 Recent Deployments:"
    gcloud builds list --limit 3 --format="table(createTime.date(tz=LOCAL),substitutions.TAG_NAME,status)" 2>/dev/null || echo "  ⚠️  Cannot fetch (run: gcloud auth login)"
    echo ""
    echo "Summary:"
    echo "  • API should show ✅ at https://api.hey.sh"
    echo "  • Latest deployment should be SUCCESS"
    echo ""
    echo "Details: just status production"

# Local logs
_logs-local service:
    #!/usr/bin/env bash
    set -euo pipefail

    if [ "{{service}}" = "backend" ]; then
        echo "📋 Backend logs (Ctrl+C to stop):"
        echo "   Start backend with: just dev"
        echo ""
        echo "💡 Backend runs on your host machine (not in Docker)"
        echo "   Check your terminal where you ran 'just dev'"
    elif [ "{{service}}" = "temporal" ]; then
        echo "📋 Temporal logs:"
        docker logs -f $(docker ps -q -f name=temporal) 2>/dev/null || echo "❌ Temporal not running"
    elif [ "{{service}}" = "neo4j" ]; then
        echo "📋 Neo4j logs:"
        docker logs -f $(docker ps -q -f name=neo4j) 2>/dev/null || echo "❌ Neo4j not running"
    elif [ "{{service}}" = "weaviate" ]; then
        echo "📋 Weaviate logs:"
        docker logs -f $(docker ps -q -f name=weaviate) 2>/dev/null || echo "❌ Weaviate not running"
    elif [ "{{service}}" = "caddy" ]; then
        echo "📋 Caddy logs (reverse proxy):"
        docker logs -f $(docker ps -q -f name=caddy) 2>/dev/null || echo "❌ Caddy not running"
    elif [ "{{service}}" = "all" ]; then
        echo "📋 All services logs (Ctrl+C to stop):"
        docker-compose -f docker/docker-compose.yml logs -f
    else
        echo "❌ Unknown service: {{service}}"
        echo "Available: backend, temporal, neo4j, weaviate, caddy, all"
        exit 1
    fi

# Production logs
_logs-production service:
    #!/usr/bin/env bash
    set -euo pipefail

    if [ "{{service}}" = "backend" ]; then
        echo "📋 Backend logs (Cloud Run):"
        gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=api" --limit=50 --format="table(timestamp,severity,textPayload)"
    elif [ "{{service}}" = "workers" ]; then
        echo "📋 Worker logs (GKE):"
        kubectl logs -n temporal-workers -l app=temporal-worker --tail=50 -f
    elif [ "{{service}}" = "builds" ]; then
        echo "📋 Cloud Build logs:"
        BUILD_ID=$(gcloud builds list --limit=1 --format="value(id)")
        gcloud builds log $BUILD_ID
    else
        echo "Available services: backend, workers, builds"
        echo "Example: just logs production backend"
    fi

# Git status for daily dashboard
_status-git:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "📝 Git Status"
    echo "════════════════════════════════════════════════════════════════"
    BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
    UNCOMMITTED=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
    UNPUSHED=$(git log @{u}.. --oneline 2>/dev/null | wc -l | tr -d ' ')
    LAST_COMMIT=$(git log -1 --pretty=format:"%h - %s" 2>/dev/null || echo "No commits")
    echo "  Branch: $BRANCH"
    if [ "$UNCOMMITTED" -gt 0 ]; then
        echo "  ⚠️  $UNCOMMITTED uncommitted changes"
        git status --short | head -5 | sed 's/^/     /'
        if [ "$UNCOMMITTED" -gt 5 ]; then
            echo "     ... and $((UNCOMMITTED - 5)) more"
        fi
    else
        echo "  ✅ Working directory clean"
    fi
    if [ "$UNPUSHED" -gt 0 ]; then
        echo "  ⚠️  $UNPUSHED unpushed commits"
    else
        echo "  ✅ All commits pushed"
    fi
    echo "  Last commit: $LAST_COMMIT"
    echo ""
    echo "  Recent commits:"
    git log --oneline --decorate -5 2>/dev/null | sed 's/^/     /' || echo "     No commits"

# Local environment status for dashboard
_status-local:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "🏠 Local Environment"
    echo "════════════════════════════════════════════════════════════════"
    # Check Caddy FIRST (priority #1)
    if docker ps --filter "name=docker-caddy" 2>/dev/null | grep -q "Up"; then
        echo "  ✅ Caddy: http://api.hey.local (hostname routing)"
    else
        echo "  ❌ Caddy not running - CRITICAL!"
        echo "     → Run: just dev (will start Caddy)"
        echo "     → Caddy provides *.hey.local hostnames"
    fi
    echo ""
    # Check backend via Caddy hostname (not port)
    if curl -s http://api.hey.local/health >/dev/null 2>&1; then
        STATUS=$(curl -s http://api.hey.local/health | jq -r .status 2>/dev/null || echo "unknown")
        echo "  ✅ Backend API: http://api.hey.local ($STATUS)"
        echo "     Your service on port 8002 (via Caddy)"
    else
        echo "  ⚠️  Backend API not running"
        echo "     → Run: just dev"
    fi
    echo ""
    # Show infrastructure services
    if ! docker ps >/dev/null 2>&1; then
        echo "  ❌ Docker not running"
        echo "     → Run: open -a Docker"
    else
        CONTAINERS=$(docker ps --filter "name=temporal" --filter "name=neo4j" --filter "name=weaviate" 2>/dev/null | wc -l | tr -d ' ')
        CONTAINERS=$((CONTAINERS - 1))
        if [ "$CONTAINERS" -gt 0 ]; then
            echo "  ✅ Infrastructure: $CONTAINERS services"
            echo "     Access via: http://temporal.hey.local"
            echo "                http://neo4j.hey.local"
            echo "                http://weaviate.hey.local"
        else
            echo "  ⚠️  No services running"
            echo "     → Run: just dev"
        fi
    fi

# Production status for dashboard
_status-production:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "☁️  Production Environment"
    echo "════════════════════════════════════════════════════════════════"
    if ! command -v gcloud >/dev/null 2>&1; then
        echo "  ⚠️  gcloud not installed (production checks disabled)"
        echo "     → Install: brew install google-cloud-sdk"
    else
        PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
        if [ -z "$PROJECT" ]; then
            echo "  ⚠️  No GCP project configured"
            echo "     → Run: gcloud config set project YOUR_PROJECT_ID"
        else
            echo "  📊 Project: $PROJECT"
            echo "  🌐 Domain: https://api.hey.sh"
            echo ""
            if curl -s https://api.hey.sh/health >/dev/null 2>&1; then
                HEALTH=$(curl -s https://api.hey.sh/health | jq -r .status 2>/dev/null || echo "unknown")
                VERSION=$(curl -s https://api.hey.sh/api/v1/info | jq -r .version 2>/dev/null || echo "unknown")
                GITSHA=$(curl -s https://api.hey.sh/api/v1/info | jq -r .git_sha 2>/dev/null || echo "unknown")
                echo "  ✅ Backend API: $HEALTH"
                echo "     Version: $VERSION ($GITSHA)"
            else
                echo "  ❌ Backend API not responding"
            fi
            echo ""
            echo "  Recent Deployments:"
            gcloud builds list --limit 3 --format="table[no-heading](createTime.date(tz=LOCAL),substitutions.TAG_NAME,status)" 2>/dev/null | sed 's/^/     /' || echo "     Cannot fetch (not authenticated)"
        fi
    fi

# Suggest next steps based on current state
_status-suggestions:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "🤔 So... What Should We Work On Next?"
    echo "════════════════════════════════════════════════════════════════"

    UNCOMMITTED=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
    BACKEND_RUNNING=$(curl -s http://localhost:8002/health >/dev/null 2>&1 && echo "yes" || echo "no")
    DOCKER_RUNNING=$(docker ps >/dev/null 2>&1 && echo "yes" || echo "no")
    LAST_COMMIT=$(git log -1 --pretty=format:"%s" 2>/dev/null || echo "No commits yet")

    # Conversational status based on current state
    if [ "$DOCKER_RUNNING" = "no" ]; then
        echo "  🐳 Docker's not running. Let's get that started:"
        echo "     1. Open Docker Desktop"
        echo "     2. Run: just dev"
    elif [ "$BACKEND_RUNNING" = "no" ]; then
        echo "  💤 Backend's asleep. Wake it up:"
        echo "     → just dev"
    elif [ "$UNCOMMITTED" -gt 0 ]; then
        echo "  📝 You've got $UNCOMMITTED uncommitted changes in progress."
        echo "  Last commit was: $LAST_COMMIT"
        echo ""
        echo "  Looks like you were working on something. Here's what you can do:"
        echo "     1. Keep coding → just dev (if not already running)"
        echo "     2. Test your changes → just test"
        echo "     3. Ship it → just deploy v1.x.x \"Your message\""
    else
        echo "  ✨ Everything's clean. Last thing you did:"
        echo "     \"$LAST_COMMIT\""
        echo ""
        echo "  What's next? Maybe:"
        echo "     • Continue building → just dev"
        echo "     • Show off to someone → just demo"
        echo "     • Check if production's happy → just check production"
        echo "     • See what users are doing → just learn"
    fi

    echo ""
    echo "  💡 Quick reminders:"
    echo "     just dev       Start your dev server (hostnames, not ports!)"
    echo "     just gossip    Come back here when you forget where you are"
    echo "     just test      Run those tests"
    echo "     just deploy    Ship to production"
    echo ""
    echo "  🌐 Services via Caddy:"
    echo "     http://api.hey.local        Your backend"
    echo "     http://temporal.hey.local   Temporal workflows"
    echo "     http://neo4j.hey.local      Graph database"
    echo "     http://weaviate.hey.local   Vector search"

# Check production CI/CD setup
_bootstrap-production-check:
    #!/usr/bin/env bash
    set -euo pipefail

    echo "1️⃣  GCP Project:"
    PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
    if [ -n "$PROJECT" ]; then
        echo "  ✅ Project: $PROJECT"
    else
        echo "  ❌ No project configured"
        echo "     Run: gcloud config set project YOUR_PROJECT_ID"
        exit 1
    fi

    echo ""
    echo "2️⃣  Cloud Build Triggers:"
    TRIGGERS=$(gcloud builds triggers list --format="value(name)" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$TRIGGERS" -gt 0 ]; then
        echo "  ✅ $TRIGGERS triggers configured:"
        gcloud builds triggers list --format="table(name,filename,triggerTemplate.tagName)" 2>/dev/null || true
    else
        echo "  ❌ No triggers found"
        echo "     Setup guide: docs/PRODUCTION_BOOTSTRAP.md"
    fi

    echo ""
    echo "3️⃣  Artifact Registry:"
    if gcloud artifacts repositories describe hey-sh-backend --location=europe-west3 >/dev/null 2>&1; then
        echo "  ✅ Repository: hey-sh-backend"
    else
        echo "  ❌ Repository not found"
        echo "     Create: gcloud artifacts repositories create hey-sh-backend --repository-format=docker --location=europe-west3"
    fi

    echo ""
    echo "4️⃣  Cloud Run Service:"
    if gcloud run services describe api --region=europe-west3 >/dev/null 2>&1; then
        echo "  ✅ Service: api"
        URL=$(gcloud run services describe api --region=europe-west3 --format="value(status.url)" 2>/dev/null || echo "")
        echo "     URL: $URL"
    else
        echo "  ❌ Service not found"
    fi

    echo ""
    echo "5️⃣  GKE Cluster:"
    if gcloud container clusters describe production-hey-sh-cluster --region=europe-west3 >/dev/null 2>&1; then
        echo "  ✅ Cluster: production-hey-sh-cluster"
    else
        echo "  ❌ Cluster not found"
        echo "     Check: infra/terraform/"
    fi

    echo ""
    echo "6️⃣  Secrets (Secret Manager):"
    SECRETS=$(gcloud secrets list --format="value(name)" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$SECRETS" -gt 0 ]; then
        echo "  ✅ $SECRETS secrets configured"
    else
        echo "  ⚠️  No secrets found"
    fi

    echo ""
    echo "📖 Documentation:"
    echo "   • cloudbuild_deploy.yaml - Main deployment pipeline"
    echo "   • infra/terraform/ - Infrastructure as code"
    echo "   • DEPLOYMENT_WORKFLOW.md - Complete guide"
    echo ""
    echo "✅ If all show ✅, your CI/CD is configured correctly"
    echo "❌ If any show ❌, see docs/PRODUCTION_BOOTSTRAP.md for setup"

# =============================================================================
# 🔧 NEW DEPLOYMENT IMPLEMENTATION (Wrapped gcloud commands)
# =============================================================================

# Cloud Run: Update traffic to a specific version
_cloud-run-update-traffic version percent:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "Updating Cloud Run traffic..."
    gcloud run services update-traffic api \
        --region=europe-west3 \
        --to-revisions=api-{{version}}={{percent}}
    echo ""
    echo "Traffic updated. Verifying..."
    gcloud run services describe api \
        --region=europe-west3 \
        --format="table(status.traffic[].revisionName,status.traffic[].percent)"

# Cloud Run: Split traffic between versions (canary)
_cloud-run-split-traffic version percent:
    #!/usr/bin/env bash
    set -euo pipefail
    # Get current serving revision
    CURRENT=$(gcloud run services describe api \
        --region=europe-west3 \
        --format="value(status.traffic[0].revisionName)" | head -1)
    REMAINING=$((100 - {{percent}}))

    echo "Splitting traffic: {{version}}={{percent}}%, $CURRENT=$REMAINING%"
    gcloud run services update-traffic api \
        --region=europe-west3 \
        --to-revisions=api-{{version}}={{percent}},$CURRENT=$REMAINING

# Cloud Run: Rollback to previous revision
_cloud-run-rollback:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "Getting previous revision..."
    PREVIOUS=$(gcloud run revisions list \
        --service=api \
        --region=europe-west3 \
        --format="value(metadata.name)" \
        --limit=2 | tail -1)

    echo "Rolling back to: $PREVIOUS"
    gcloud run services update-traffic api \
        --region=europe-west3 \
        --to-revisions=$PREVIOUS=100

# Cloud Run: Deploy to staging
_cloud-run-staging-deploy version:
    #!/usr/bin/env bash
    set -euo pipefail
    # Note: Assumes staging service exists
    # Create with: gcloud run services create api-staging --image=... --region=europe-west3
    echo "Deploying {{version}} to staging..."
    IMAGE="europe-west3-docker.pkg.dev/hey-sh-production/hey-sh-backend/service:{{version}}"
    gcloud run services update api-staging \
        --region=europe-west3 \
        --image=$IMAGE

# Get production version info
_prod-version-info:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "🏷️  Production Version Info"
    echo "════════════════════════════════════════════════════════════════"

    # Get from api.hey.sh
    if curl -s https://api.hey.sh/api/v1/info >/dev/null 2>&1; then
        INFO=$(curl -s https://api.hey.sh/api/v1/info)
        VERSION=$(echo "$INFO" | jq -r .version)
        GITSHA=$(echo "$INFO" | jq -r .git_sha)
        BUILT=$(echo "$INFO" | jq -r .built_at)
        ENV=$(echo "$INFO" | jq -r .environment)

        echo "  Version: $VERSION"
        echo "  Git SHA: $GITSHA"
        echo "  Built: $BUILT"
        echo "  Environment: $ENV"
    else
        echo "  ❌ Cannot reach api.hey.sh"
    fi

    echo ""
    # Get Cloud Run serving info
    echo "  Traffic Distribution:"
    gcloud run services describe api \
        --region=europe-west3 \
        --format="table[no-heading](status.traffic[].revisionName,status.traffic[].percent)" \
        | sed 's/^/    /'

# Check status of specific version
_version-status version:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "🔍 Version Status: {{version}}"
    echo "════════════════════════════════════════════════════════════════"

    # Check if image exists
    IMAGE="europe-west3-docker.pkg.dev/hey-sh-production/hey-sh-backend/service:{{version}}"
    if gcloud container images describe "$IMAGE" >/dev/null 2>&1; then
        echo "  ✅ Image exists: {{version}}"
        DIGEST=$(gcloud container images describe "$IMAGE" --format="value(image_summary.digest)")
        echo "     Digest: $DIGEST"
    else
        echo "  ❌ Image not found: {{version}}"
        echo "     Build may still be in progress"
        exit 1
    fi

    echo ""
    # Check if deployed
    DEPLOYED=$(gcloud run revisions list \
        --service=api \
        --region=europe-west3 \
        --format="value(metadata.name)" \
        | grep "{{version}}" || echo "")

    if [ -n "$DEPLOYED" ]; then
        echo "  ✅ Deployed as revision: $DEPLOYED"
        TRAFFIC=$(gcloud run services describe api \
            --region=europe-west3 \
            --format="value(status.traffic[?revisionName='$DEPLOYED'].percent)" | head -1)
        if [ -n "$TRAFFIC" ]; then
            echo "     Serving: $TRAFFIC% of traffic"
        else
            echo "     Serving: 0% of traffic (revision exists but not serving)"
        fi
    else
        echo "  ⏸️  Not deployed to Cloud Run yet"
        echo "     Use: just promote {{version}}"
    fi

# List all deployed versions
_list-versions:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "📦 Deployed Versions"
    echo "════════════════════════════════════════════════════════════════"

    echo "Available images:"
    gcloud artifacts docker tags list \
        europe-west3-docker.pkg.dev/hey-sh-production/hey-sh-backend/service \
        --limit=10 \
        --format="table(tag,timestamp.date(tz=LOCAL))" \
        | sed 's/^/  /'

    echo ""
    echo "Cloud Run revisions:"
    gcloud run revisions list \
        --service=api \
        --region=europe-west3 \
        --limit=10 \
        --format="table(metadata.name,metadata.creationTimestamp.date(tz=LOCAL),status.conditions[0].status)" \
        | sed 's/^/  /'

# Show build status
_build-status:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "🔨 Build Status"
    echo "════════════════════════════════════════════════════════════════"

    echo "Recent builds:"
    gcloud builds list \
        --limit=5 \
        --format="table(id,createTime.date(tz=LOCAL),substitutions.TAG_NAME,status,logUrl)"

    echo ""
    # Check if any builds are currently running
    RUNNING=$(gcloud builds list \
        --filter="status=WORKING OR status=QUEUED" \
        --format="value(id)" | wc -l | tr -d ' ')

    if [ "$RUNNING" -gt 0 ]; then
        echo "⏳ $RUNNING build(s) in progress"
        echo "   Monitor: gcloud builds log \$(gcloud builds list --limit=1 --format='value(id)') --stream"
    else
        echo "✅ No builds currently running"
    fi

# Show production metrics
_prod-metrics:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "📊 Production Metrics"
    echo "════════════════════════════════════════════════════════════════"

    # Cloud Run metrics
    echo "Cloud Run Service:"
    gcloud run services describe api \
        --region=europe-west3 \
        --format="yaml(status.traffic,status.conditions)" \
        | grep -E "revisionName|percent|type|status" \
        | sed 's/^/  /'

    echo ""
    echo "Request count (last hour):"
    echo "  (Use Cloud Console for detailed metrics)"
    echo "  🔗 https://console.cloud.google.com/run/detail/europe-west3/api/metrics"

# Production insights
_prod-insights:
    #!/usr/bin/env bash
    set -euo pipefail

    echo "Backend Health:"
    if curl -s https://api.hey.sh/health >/dev/null 2>&1; then
        curl -s https://api.hey.sh/health | jq '.'
    else
        echo "  ❌ Not reachable"
    fi

    echo ""
    echo "API Version:"
    if curl -s https://api.hey.sh/api/v1/info >/dev/null 2>&1; then
        curl -s https://api.hey.sh/api/v1/info | jq '.'
    else
        echo "  ❌ Cannot fetch version info"
    fi

    echo ""
    echo "Recent Deployments:"
    gcloud builds list --limit 3 --format="table(createTime.date(tz=LOCAL),substitutions.TAG_NAME,status)"

    echo ""
    echo "Traffic Distribution:"
    gcloud run services describe api \
        --region=europe-west3 \
        --format="table(status.traffic[].revisionName,status.traffic[].percent)"

    echo ""
    echo "🔗 Full metrics: https://console.cloud.google.com/run/detail/europe-west3/api"
    echo "🔗 Logs: https://console.cloud.google.com/logs"

# Staging status
_status-staging:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "🧪 Staging Environment"
    echo "════════════════════════════════════════════════════════════════"

    # Check if staging service exists
    if gcloud run services describe api-staging --region=europe-west3 >/dev/null 2>&1; then
        echo "  ✅ Staging service exists"
        URL=$(gcloud run services describe api-staging --region=europe-west3 --format="value(status.url)")
        echo "     URL: $URL"

        # Get version info
        IMAGE=$(gcloud run services describe api-staging --region=europe-west3 --format="value(spec.template.spec.containers[0].image)")
        VERSION=$(echo "$IMAGE" | grep -oE '[^:]+$')
        echo "     Version: $VERSION"
    else
        echo "  ⚠️  Staging service not created yet"
        echo "     Create with: gcloud run deploy api-staging --image=europe-west3-docker.pkg.dev/hey-sh-production/hey-sh-backend/service:latest --region=europe-west3"
    fi
