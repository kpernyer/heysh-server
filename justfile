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
            if curl -s https://api-blwol5d45q-ey.a.run.app/health >/dev/null 2>&1; then
                HEALTH=$(curl -s https://api-blwol5d45q-ey.a.run.app/health | jq -r .status 2>/dev/null || echo "unknown")
                echo "  ✅ Backend API: https://api-blwol5d45q-ey.a.run.app ($HEALTH)"
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
