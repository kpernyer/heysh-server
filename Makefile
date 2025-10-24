# Makefile for Document Workflow System
.PHONY: help test test-local test-staging test-load deploy-staging deploy-prod clean

# Variables
VERSION ?= $(shell git rev-parse --short HEAD)
DOCKER_REGISTRY ?= gcr.io/hey-sh-workflow
PYTHON := python3
PYTEST := $(PYTHON) -m pytest

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(GREEN)Document Workflow System - Available Commands:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Examples:$(NC)"
	@echo "  make test-local     # Run tests locally"
	@echo "  make deploy-staging # Deploy to staging"
	@echo "  make test-load      # Run load tests"

# ==============================================================================
# Local Development
# ==============================================================================

install: ## Install dependencies
	@echo "$(GREEN)Installing dependencies...$(NC)"
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

dev: ## Start local development environment
	@echo "$(GREEN)Starting local development environment...$(NC)"
	docker-compose -f docker-compose.test.yml up -d
	@echo "$(GREEN)Environment ready! Temporal UI: http://localhost:8088$(NC)"

dev-stop: ## Stop local development environment
	@echo "$(YELLOW)Stopping development environment...$(NC)"
	docker-compose -f docker-compose.test.yml down

dev-logs: ## Show development environment logs
	docker-compose -f docker-compose.test.yml logs -f

worker-local: ## Run worker locally
	@echo "$(GREEN)Starting local worker...$(NC)"
	WORKER_TYPES=general,storage,ai-processing \
	USE_MOCK_AI=true \
	TEMPORAL_ADDRESS=localhost:7233 \
	python -m worker.multiqueue_worker

# ==============================================================================
# Testing
# ==============================================================================

test: test-unit test-integration ## Run all tests

test-unit: ## Run unit tests
	@echo "$(GREEN)Running unit tests...$(NC)"
	$(PYTEST) test/unit/ -v --tb=short

test-integration: ## Run integration tests
	@echo "$(GREEN)Running integration tests...$(NC)"
	docker-compose -f docker-compose.test.yml up -d
	@sleep 10  # Wait for services
	$(PYTEST) test/test_workflows.py -v --tb=short
	docker-compose -f docker-compose.test.yml down

test-e2e: ## Run end-to-end tests
	@echo "$(GREEN)Running end-to-end tests...$(NC)"
	docker-compose -f docker-compose.test.yml up -d
	@sleep 10
	$(PYTEST) test/test_workflows.py::test_end_to_end_document_flow -v
	docker-compose -f docker-compose.test.yml down

test-load: ## Run load tests
	@echo "$(GREEN)Running load tests...$(NC)"
	docker-compose -f docker-compose.test.yml up -d
	@sleep 10
	python test/load_test.py 100 10  # 100 workflows, 10 concurrent
	docker-compose -f docker-compose.test.yml down

test-local: ## Run all tests locally with Docker
	@echo "$(GREEN)Running complete test suite...$(NC)"
	@bash test/run_tests.sh

test-coverage: ## Run tests with coverage report
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	$(PYTEST) test/ \
		--cov=workflow \
		--cov=activity \
		--cov-report=html:test-results/coverage \
		--cov-report=term

# ==============================================================================
# Docker & Build
# ==============================================================================

build: ## Build all Docker images
	@echo "$(GREEN)Building Docker images...$(NC)"
	docker build -t $(DOCKER_REGISTRY)/hey-sh-worker:$(VERSION) -f Dockerfile .
	docker build -t $(DOCKER_REGISTRY)/hey-sh-ai-worker:$(VERSION) -f deployments/Dockerfile.ai-worker .
	docker build -t $(DOCKER_REGISTRY)/hey-sh-storage-worker:$(VERSION) -f deployments/Dockerfile.storage-worker .

push: build ## Build and push Docker images
	@echo "$(GREEN)Pushing Docker images...$(NC)"
	docker push $(DOCKER_REGISTRY)/hey-sh-worker:$(VERSION)
	docker push $(DOCKER_REGISTRY)/hey-sh-ai-worker:$(VERSION)
	docker push $(DOCKER_REGISTRY)/hey-sh-storage-worker:$(VERSION)

# ==============================================================================
# Deployment
# ==============================================================================

deploy-staging: ## Deploy to staging environment
	@echo "$(GREEN)Deploying to staging...$(NC)"
	@bash deployments/staging/deploy-staging.sh

deploy-prod: ## Deploy to production (requires confirmation)
	@echo "$(RED)⚠️  WARNING: Deploying to PRODUCTION$(NC)"
	@read -p "Are you sure? (type 'yes' to confirm): " confirm && \
	if [ "$$confirm" = "yes" ]; then \
		echo "$(GREEN)Deploying to production...$(NC)"; \
		bash deployments/prod/deploy-prod.sh; \
	else \
		echo "$(YELLOW)Deployment cancelled$(NC)"; \
	fi

rollback: ## Rollback deployment
	@echo "$(YELLOW)Rolling back deployment...$(NC)"
	kubectl rollout undo deployment/general-worker -n temporal-workers
	kubectl rollout undo deployment/storage-worker -n temporal-workers
	kubectl rollout undo deployment/ai-processing-worker -n temporal-workers

# ==============================================================================
# Monitoring & Debugging
# ==============================================================================

logs-ai: ## Show AI worker logs
	kubectl logs -n temporal-workers -l worker-type=ai-processing -f

logs-storage: ## Show storage worker logs
	kubectl logs -n temporal-workers -l worker-type=storage -f

logs-general: ## Show general worker logs
	kubectl logs -n temporal-workers -l worker-type=general -f

status: ## Show deployment status
	@echo "$(GREEN)Deployment Status:$(NC)"
	kubectl get deployments -n temporal-workers
	@echo ""
	@echo "$(GREEN)Pod Status:$(NC)"
	kubectl get pods -n temporal-workers
	@echo ""
	@echo "$(GREEN)HPA Status:$(NC)"
	kubectl get hpa -n temporal-workers

metrics: ## Show worker metrics
	kubectl top pods -n temporal-workers

temporal-ui: ## Open Temporal Web UI
	@echo "$(GREEN)Opening Temporal Web UI...$(NC)"
	kubectl port-forward -n temporal-system svc/temporal-web 8088:8088

# ==============================================================================
# Database Management
# ==============================================================================

db-migrate: ## Run database migrations
	@echo "$(GREEN)Running database migrations...$(NC)"
	python -m alembic upgrade head

db-seed: ## Seed database with test data
	@echo "$(GREEN)Seeding database...$(NC)"
	python scripts/seed_database.py

neo4j-shell: ## Open Neo4j shell
	docker-compose -f docker-compose.test.yml exec neo4j cypher-shell -u neo4j -p testpassword

# ==============================================================================
# Cleanup
# ==============================================================================

clean: ## Clean up all resources
	@echo "$(YELLOW)Cleaning up...$(NC)"
	docker-compose -f docker-compose.test.yml down -v
	rm -rf test-results/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

clean-staging: ## Clean up staging environment
	@echo "$(YELLOW)Cleaning up staging environment...$(NC)"
	kubectl delete namespace temporal-workers --ignore-not-found
	kubectl delete namespace databases --ignore-not-found

# ==============================================================================
# Utilities
# ==============================================================================

format: ## Format code with black and isort
	@echo "$(GREEN)Formatting code...$(NC)"
	black workflow/ activity/ test/
	isort workflow/ activity/ test/

lint: ## Lint code with flake8 and mypy
	@echo "$(GREEN)Linting code...$(NC)"
	flake8 workflow/ activity/ test/
	mypy workflow/ activity/

validate-yaml: ## Validate Kubernetes YAML files
	@echo "$(GREEN)Validating YAML files...$(NC)"
	yamllint deployments/k8s/

workflow-test: ## Test a specific workflow
	@echo "$(GREEN)Testing workflow: $(WORKFLOW)$(NC)"
	python scripts/test_workflow.py $(WORKFLOW)

.DEFAULT_GOAL := help
