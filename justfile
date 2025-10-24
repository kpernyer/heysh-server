# Hey.sh Server - Python Backend Justfile

# Environment setup
setup:
    @echo "🚀 Setting up Hey.sh Server environment..."
    @uv venv
    @uv pip install -r requirements.txt
    @echo "✅ Environment setup complete"

# Development commands
dev:
    @echo "🔧 Starting development environment..."
    @just start-temporal &
    @just start-workers &
    @just start-api

# Main development command
start:
    @echo "🚀 Starting Hey.sh Server..."
    @echo "🌐 API Server: http://localhost:8002"
    @echo "🔧 Hot reload enabled for code changes"
    @uv run uvicorn service.main:app --reload --host 0.0.0.0 --port 8002

# Temporal commands
start-temporal:
    @echo "🕐 Starting Temporal server..."
    @if temporal workflow list --limit 1 >/dev/null 2>&1; then \
        echo "✅ Temporal is already running!"; \
        echo "🌐 Temporal UI: http://temporal.hey.sh"; \
    else \
        echo "Starting Temporal Server..."; \
        temporal server start-dev --ui-port $(python3 scripts/get_config.py temporal_ui port); \
    fi

start-workers:
    @echo "👷 Starting Temporal workers..."
    @uv run python worker/main.py

start-domain-bootstrap-worker:
    @echo "🏗️  Starting Domain Bootstrap Worker..."
    @echo "📋 Task Queue: hey-sh-workflows"
    @echo "🔧 Activities: domain research, analysis, config generation, notifications"
    @echo "📋 Workflows: StandaloneDomainBootstrapWorkflow"
    @uv run python standalone_worker.py

# API server
start-api:
    @echo "🌐 Starting FastAPI server..."
    @uv run uvicorn service.main:app --reload --host 0.0.0.0 --port $(python3 scripts/get_config.py backend port)

# Testing commands
test:
    @echo "🧪 Running all tests..."
    @uv run pytest test/ -v

test-workflow:
    @echo "🧪 Testing workflows..."
    @uv run python test_standalone_bootstrap.py

test-domain-bootstrap:
    @echo "🧪 Testing domain bootstrap..."
    @uv run python test_domain_bootstrap.py

# Domain bootstrap workflow
test-domain-bootstrap-real:
    @echo "🚀 Testing Real Domain Bootstrap Workflow..."
    @uv run python test_standalone_bootstrap.py

approve-domain-bootstrap WORKFLOW_ID:
    @echo "🎯 Approving Domain Bootstrap Workflow..."
    @uv run python approve_domain_bootstrap.py $(WORKFLOW_ID)

# Code quality
lint:
    @echo "🔍 Running linting..."
    @uv run ruff check . --fix
    @uv run black . --check

lint-fix:
    @echo "🔍 Running linting with fixes..."
    @uv run ruff check . --fix
    @uv run black .

type-check:
    @echo "🔍 Running type checking..."
    @uv run mypy .

format:
    @echo "🎨 Formatting code..."
    @uv run black .
    @uv run ruff check . --fix

# Security
security:
    @echo "🔒 Running security checks..."
    @uv run bandit -r . -f json -o security-report.json
    @uv run safety check

# Docker commands
build:
    @echo "🐳 Building Docker image..."
    @docker build -t heysh-server .

run-docker:
    @echo "🐳 Running Docker container..."
    @docker run -p 8000:8000 heysh-server

# Deployment
deploy-staging:
    @echo "🚀 Deploying to staging..."
    @echo "TODO: Implement staging deployment"

deploy-prod:
    @echo "🚀 Deploying to production..."
    @echo "TODO: Implement production deployment"

# Database commands
migrate:
    @echo "🗄️  Running database migrations..."
    @uv run python scripts/migrate.py

seed:
    @echo "🌱 Seeding database..."
    @uv run python scripts/seed.py

# Monitoring
health:
    @echo "🏥 Checking service health..."
    @uv run python scripts/health_check.py

logs:
    @echo "📋 Viewing logs..."
    @tail -f logs/app.log

# Cleanup
clean:
    @echo "🧹 Cleaning up..."
    @rm -rf __pycache__/
    @rm -rf .pytest_cache/
    @rm -rf htmlcov/
    @find . -name "*.pyc" -delete

# Port and URL management
ports:
    @echo "🌐 Hey.sh Server Ports & URLs:"
    @echo "  API Server (Dev):      http://localhost:8002"
    @echo "  API Server (Staging):  http://localhost:8001"
    @echo "  API Server (Prod):     https://api.hey.sh"
    @echo ""
    @echo "🔧 Backend Services:"
    @echo "  Temporal Server:       localhost:7235"
    @echo "  Temporal UI:           http://localhost:8082"
    @echo "  PostgreSQL:            localhost:5434"
    @echo "  Redis:                 localhost:6381"
    @echo "  Weaviate:              http://localhost:8081"
    @echo "  Neo4j:                 http://localhost:7474"
    @echo ""
    @echo "🌐 Frontend (heysh-workflow):"
    @echo "  Frontend:              http://localhost:5173"

# Status checking
status:
    @echo "🔍 Hey.sh Server Status:"
    @echo ""
    @echo "🌐 API Server Status:"
    @if curl -s http://localhost:8002/health > /dev/null 2>&1; then \
        echo "  ✅ API Server: Running on http://localhost:8002"; \
    else \
        echo "  ❌ API Server: Not running - run 'just start'"; \
    fi
    @echo ""
    @echo "🔧 Backend Services:"
    @if curl -s http://localhost:8082 > /dev/null 2>&1; then \
        echo "  ✅ Temporal UI: Running on http://localhost:8082"; \
    else \
        echo "  ❌ Temporal UI: Not running - run 'just start-temporal'"; \
    fi
    @if temporal workflow list --limit 1 >/dev/null 2>&1; then \
        echo "  ✅ Temporal Server: Running on localhost:7235"; \
    else \
        echo "  ❌ Temporal Server: Not running - run 'just start-temporal'"; \
    fi
    @if curl -s http://localhost:8081/v1/.well-known/ready > /dev/null 2>&1; then \
        echo "  ✅ Weaviate: Running on http://localhost:8081"; \
    else \
        echo "  ❌ Weaviate: Not running"; \
    fi
    @if curl -s http://localhost:7474 > /dev/null 2>&1; then \
        echo "  ✅ Neo4j: Running on http://localhost:7474"; \
    else \
        echo "  ❌ Neo4j: Not running"; \
    fi

# Help
help:
    @echo "Hey.sh Server Commands:"
    @echo ""
    @echo "🚀 Development:"
    @echo "  start                    - Start API server with hot reload (main command)"
    @echo "  dev                      - Start full development environment"
    @echo "  setup                    - Setup development environment"
    @echo ""
    @echo "🌐 Server Management:"
    @echo "  start-temporal           - Start Temporal server"
    @echo "  start-workers            - Start Temporal workers"
    @echo "  start-api                - Start FastAPI server"
    @echo "  ports                    - Show all ports and URLs"
    @echo "  status                   - Check service status"
    @echo ""
    @echo "🧪 Testing:"
    @echo "  test                     - Run all tests"
    @echo "  test-workflow            - Test workflows"
    @echo "  test-domain-bootstrap    - Test domain bootstrap"
    @echo ""
    @echo "🔧 Code Quality:"
    @echo "  lint                     - Run linting"
    @echo "  type-check              - Run type checking"
    @echo "  format                   - Format code"
    @echo "  security                - Run security checks"
    @echo ""
    @echo "🚀 Deployment:"
    @echo "  build                   - Build Docker image"
    @echo "  deploy-staging           - Deploy to staging"
    @echo "  deploy-prod              - Deploy to production"
    @echo ""
    @echo "🧹 Utilities:"
    @echo "  health                   - Check service health"
    @echo "  clean                    - Clean up files"
    @echo "  help                     - Show this help"